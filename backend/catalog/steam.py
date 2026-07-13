"""Autopreenchimento do catálogo via Storefront API da Steam.

A Storefront (`store.steampowered.com/api/appdetails`) é pública e não exige
chave. Mapeamos os campos da loja para os campos de `Game` e as listas
(gêneros/plataformas/devs/publishers) para as taxonomias normalizadas.
"""
import re

import requests

APPDETAILS_URL = 'https://store.steampowered.com/api/appdetails'

# CDN das artes da biblioteca Steam. Ao contrário do capsule/header devolvidos
# pela Storefront (horizontais), estas capas são montadas a partir do appid:
#   - library_600x900: capa vertical (a "Capa" 600x900 da biblioteca);
#   - library_hero: fundo largo (~1920x620, a "Capa horizontal"/fundo).
STEAM_CDN = 'https://steamcdn-a.akamaihd.net/steam/apps'

# nomes de exibição das plataformas retornadas como {windows, mac, linux}
_PLATFORM_LABELS = {'windows': 'Windows', 'mac': 'macOS', 'linux': 'Linux'}

_TIMEOUT = 10


def library_cover_url(appid):
    """Capa vertical (600x900) da biblioteca Steam, ou None sem appid."""
    return f'{STEAM_CDN}/{appid}/library_600x900.jpg' if appid else None


def library_hero_url(appid):
    """Fundo largo (~1920x620) da biblioteca Steam, ou None sem appid."""
    return f'{STEAM_CDN}/{appid}/library_hero.jpg' if appid else None


def _parse_year(release_date):
    """Extrai o ano (int) de um `release_date.date` da Steam, ou None."""
    if not release_date:
        return None
    match = re.search(r'(\d{4})', release_date.get('date', '') or '')
    return int(match.group(1)) if match else None


def fetch_appdetails(appid, lang='portuguese'):
    """Busca e mapeia os detalhes de um appid. Retorna dict ou None (não achado).

    Erros de rede propagam como `requests.RequestException` (tratados na view).
    """
    resp = requests.get(
        APPDETAILS_URL,
        params={'appids': appid, 'l': lang},
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()
    entry = resp.json().get(str(appid))
    if not entry or not entry.get('success'):
        return None
    data = entry.get('data', {})
    if data.get('type') and data.get('type') != 'game':
        # DLC/vídeo/etc. também têm appid; ainda assim mapeamos o que der.
        pass

    platforms = [
        label
        for key, label in _PLATFORM_LABELS.items()
        if data.get('platforms', {}).get(key)
    ]
    return {
        'titulo': data.get('name') or '',
        'sinopse': data.get('short_description') or '',
        'ano_lancamento': _parse_year(data.get('release_date')),
        'banner_url': library_hero_url(appid) or data.get('header_image') or None,
        'capa_url': library_cover_url(appid) or data.get('capsule_image') or None,
        'steam_appid': int(appid),
        'genres': [g['description'] for g in data.get('genres', []) if g.get('description')],
        'platforms': platforms,
        'developers': [d for d in data.get('developers', []) if d],
        'publishers': [p for p in data.get('publishers', []) if p],
    }
