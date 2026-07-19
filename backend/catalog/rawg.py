"""Integração com a RAWG API para o carrossel de "Próximos Lançamentos" da Home
e para o backfill de `data_lancamento`/`rawg_id` do catálogo.

Diferente da Steam (`catalog.steam`), aqui os dados são consumidos ao vivo
(cacheados na view) e não alimentam o catálogo diretamente — servem para
exibição e, quando casam com um Game já existente, para um backfill leve.
"""
import datetime

import requests
from django.conf import settings

from .models import Game

GAMES_URL = 'https://api.rawg.io/api/games'

_TIMEOUT = 10

# Janela de busca do carrossel: hoje até hoje + ~6 meses.
_JANELA_DIAS = 182


def _normalizar_item(item):
    """Normaliza um item bruto da RAWG, ou None se ainda não tem data definida
    (`tba=true` ou `released` nulo)."""
    if item.get('tba') or not item.get('released'):
        return None
    return {
        'rawg_id': item['id'],
        'nome': item.get('name') or '',
        'data_lancamento': datetime.date.fromisoformat(item['released']),
        'capa_url': item.get('background_image'),
        'plataformas': [
            p['platform']['name']
            for p in item.get('platforms', []) or []
            if p.get('platform', {}).get('name')
        ],
    }


def buscar_proximos_lancamentos():
    """Busca na RAWG os jogos com lançamento previsto pros próximos ~6 meses.

    Retorna uma lista de dicts normalizados — {rawg_id, nome, data_lancamento
    (date), capa_url, plataformas} — ordenada por data_lancamento.

    Sem `settings.RAWG_API_KEY`, retorna [] sem chamar a API. Erros de rede
    propagam como `requests.RequestException` (tratados na view).
    """
    if not settings.RAWG_API_KEY:
        return []

    hoje = datetime.date.today()
    fim = hoje + datetime.timedelta(days=_JANELA_DIAS)
    resp = requests.get(
        GAMES_URL,
        params={
            'dates': f'{hoje.isoformat()},{fim.isoformat()}',
            'ordering': 'released',
            'page_size': 20,
            'key': settings.RAWG_API_KEY,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()

    resultados = [
        normalizado
        for item in resp.json().get('results', [])
        if (normalizado := _normalizar_item(item)) is not None
    ]
    resultados.sort(key=lambda r: r['data_lancamento'])
    return resultados


def buscar_por_titulo(nome):
    """Busca na RAWG o jogo cujo título bate exatamente com `nome`.

    Importante: o parâmetro `search_exact` da própria RAWG NÃO é um filtro de
    igualdade estrita apesar do nome — na prática ele ainda devolve
    correspondências parciais/soltas (ex.: buscar "Rust" com search_exact
    devolve "Rusted Will" como primeiro resultado). Por isso fazemos uma busca
    normal (`search`, sem `search_exact`) e conferimos a igualdade exata
    (case-insensitive) do lado de cá contra o campo `name` de cada resultado —
    mesmo espírito de `casar_com_catalogo`, sem fuzzy matching. Se nenhum dos
    resultados bater exatamente, retorna None (não arrisca casar errado).

    Usada pro backfill de jogos já cadastrados (comando `sync_rawg_dates`) e
    pelo autofill da Steam.

    Retorna o mesmo dict normalizado de `buscar_proximos_lancamentos`, ou None
    sem `RAWG_API_KEY`, sem match exato, ou se o match ainda não tiver data
    definida (`tba`/`released` nulo).
    """
    if not settings.RAWG_API_KEY:
        return None

    resp = requests.get(
        GAMES_URL,
        params={
            'search': nome,
            'page_size': 10,
            'key': settings.RAWG_API_KEY,
        },
        timeout=_TIMEOUT,
    )
    resp.raise_for_status()

    nome_norm = nome.strip().lower()
    item = next(
        (
            r for r in resp.json().get('results', [])
            if (r.get('name') or '').strip().lower() == nome_norm
        ),
        None,
    )
    return _normalizar_item(item) if item else None


def aplicar_backfill(game, rawg_id, data_lancamento):
    """Preenche `rawg_id`/`data_lancamento` de `game`, só nos campos que ainda
    estavam vazios — nunca sobrescreve um valor já preenchido manualmente
    pelo admin. Salva e retorna True se algo mudou, False caso contrário."""
    campos = []
    if game.rawg_id is None and rawg_id is not None:
        game.rawg_id = rawg_id
        campos.append('rawg_id')
    if game.data_lancamento is None and data_lancamento is not None:
        game.data_lancamento = data_lancamento
        campos.append('data_lancamento')
    if campos:
        game.save(update_fields=campos)
    return bool(campos)


def casar_com_catalogo(rawg_id, nome, data_lancamento=None):
    """Tenta casar um resultado da RAWG com um Game já cadastrado no catálogo.

    Tenta primeiro por `rawg_id`; se não achar, por título exato
    (case-insensitive — sem fuzzy matching, foge do escopo). Ao casar por
    título, aplica `aplicar_backfill`. Retorna o Game casado ou None.
    """
    game = Game.objects.filter(rawg_id=rawg_id).first()
    if game:
        return game

    game = Game.objects.filter(titulo__iexact=nome).first()
    if not game:
        return None

    aplicar_backfill(game, rawg_id, data_lancamento)
    return game
