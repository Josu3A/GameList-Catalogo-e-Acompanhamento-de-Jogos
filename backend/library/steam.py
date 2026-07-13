"""Sincronização com a Steam Web API (biblioteca e conquistas do usuário).

Estas chamadas exigem `STEAM_API_KEY` (só no backend) e um perfil Steam público.
O casamento de jogos é sempre por `steam_appid`, nunca por nome (CONTEXTO §6.4).
"""
import requests
from django.conf import settings

_TIMEOUT = 15


def get_owned_games(steam_id):
    """Jogos possuídos + tempo jogado. Lista de {appid, name, playtime_forever(min)}.

    Perfil privado devolve resposta vazia → retornamos [].
    """
    resp = requests.get(
        'https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/',
        params={
            'key': settings.STEAM_API_KEY,
            'steamid': steam_id,
            'include_appinfo': 1,
            'include_played_free_games': 1,
            'format': 'json',
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get('response', {}).get('games', [])


def get_schema_for_game(appid):
    """Esquema de conquistas de um jogo. Lista de dicts prontos p/ Achievement."""
    resp = requests.get(
        'https://api.steampowered.com/ISteamUserStats/GetSchemaForGame/v2/',
        params={'key': settings.STEAM_API_KEY, 'appid': appid},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    stats = resp.json().get('game', {}).get('availableGameStats', {})
    return [
        {
            'steam_apiname': a.get('name', ''),
            'nome': a.get('displayName') or a.get('name', ''),
            'descricao': a.get('description') or None,
            'icon_url': a.get('icon') or None,
        }
        for a in stats.get('achievements', [])
        if a.get('name')
    ]


def get_player_achievements(steam_id, appid):
    """Conquistas do usuário no jogo. Lista de {apiname, achieved, unlocktime}.

    Perfil privado / jogo sem stats → success=false → retornamos [].
    """
    resp = requests.get(
        'https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/',
        params={
            'key': settings.STEAM_API_KEY,
            'steamid': steam_id,
            'appid': appid,
            'l': 'portuguese',
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    stats = resp.json().get('playerstats', {})
    if not stats.get('success'):
        return []
    return [
        {
            'apiname': a.get('apiname', ''),
            'achieved': bool(a.get('achieved')),
            'unlocktime': a.get('unlocktime') or 0,
        }
        for a in stats.get('achievements', [])
    ]
