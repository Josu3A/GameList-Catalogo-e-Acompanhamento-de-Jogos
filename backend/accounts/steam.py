"""Integração com a Steam — autenticação OpenID 2.0 e perfil do jogador.

O login por Steam usa **OpenID 2.0** (não precisa de chave): redirecionamos o
usuário ao provedor da Steam, que volta com o `claimed_id` contendo o SteamID64;
validamos essa resposta fazendo `check_authentication` de volta à Steam.

`get_player_summary` usa a **Steam Web API** (precisa de `STEAM_API_KEY`) para
puxar nome/avatar do perfil — é opcional e degrada para `None` sem chave.
"""
import re

import requests
from django.conf import settings

OPENID_ENDPOINT = 'https://steamcommunity.com/openid/login'
OPENID_NS = 'http://specs.openid.net/auth/2.0'
OPENID_IDENTIFIER_SELECT = 'http://specs.openid.net/auth/2.0/identifier_select'

# .../openid/id/<steamid64> — o SteamID64 tem 17 dígitos.
_CLAIMED_ID_RE = re.compile(r'^https://steamcommunity\.com/openid/id/(\d{17})$')

_TIMEOUT = 10


def build_login_url(return_to, realm):
    """Monta a URL de redirecionamento para o login OpenID da Steam.

    `return_to` é o endpoint de callback (para onde a Steam devolve o usuário);
    `realm` é a base do site que está pedindo a autenticação.
    """
    params = {
        'openid.ns': OPENID_NS,
        'openid.mode': 'checkid_setup',
        'openid.return_to': return_to,
        'openid.realm': realm,
        'openid.identity': OPENID_IDENTIFIER_SELECT,
        'openid.claimed_id': OPENID_IDENTIFIER_SELECT,
    }
    req = requests.Request('GET', OPENID_ENDPOINT, params=params).prepare()
    return req.url


def verify_response(params):
    """Valida a resposta OpenID da Steam e devolve o SteamID64 (str) ou None.

    `params` é o mapeamento dos parâmetros `openid.*` recebidos no callback.
    Reenviamos tudo com `mode=check_authentication`; a Steam responde
    `is_valid:true` quando a assinatura confere.
    """
    claimed_id = params.get('openid.claimed_id', '')
    match = _CLAIMED_ID_RE.match(claimed_id)
    if not match:
        return None

    data = {key: value for key, value in params.items() if key.startswith('openid.')}
    data['openid.mode'] = 'check_authentication'

    try:
        resp = requests.post(OPENID_ENDPOINT, data=data, timeout=_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException:
        return None

    if 'is_valid:true' not in resp.text:
        return None
    return match.group(1)


def get_player_summary(steam_id):
    """Nome e avatar do perfil Steam via Web API. Requer STEAM_API_KEY.

    Devolve `{'nome': ..., 'avatar_url': ...}` ou None (sem chave, erro de rede,
    ou perfil inexistente).
    """
    if not settings.STEAM_API_KEY:
        return None
    try:
        resp = requests.get(
            'https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/',
            params={'key': settings.STEAM_API_KEY, 'steamids': steam_id},
            timeout=_TIMEOUT,
        )
        resp.raise_for_status()
        players = resp.json().get('response', {}).get('players', [])
    except (requests.RequestException, ValueError):
        return None
    if not players:
        return None
    player = players[0]
    return {
        'nome': player.get('personaname'),
        'avatar_url': player.get('avatarfull') or player.get('avatar'),
    }
