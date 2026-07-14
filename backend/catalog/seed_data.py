"""Snapshot offline do catálogo de jogos famosos da Steam + aplicação no banco.

O snapshot (`data/steam_top_games.json`) é gerado a partir do que a Storefront da
Steam devolveu (ver o comando `seed_steam_top`), e fica versionado para o seed
rodar **sem rede** na inicialização do banco.

`apply_games` insere/atualiza os jogos casando por `steam_appid` e resolve as
taxonomias (gênero/plataforma/dev/publisher) por `get_or_create` — o mesmo padrão
do `seed_demo`/`steam-preview`. É idempotente.
"""
import json
from pathlib import Path

from django.db import transaction

from .models import Developer, Game, Genre, Platform, Publisher

TOP_GAMES_PATH = Path(__file__).resolve().parent / 'data' / 'steam_top_games.json'


def load_top_games():
    """Lê o snapshot dos jogos famosos (lista de dicts). Vazio se não existir."""
    if not TOP_GAMES_PATH.exists():
        return []
    with TOP_GAMES_PATH.open(encoding='utf-8') as fh:
        return json.load(fh)


def _taxonomia(model, nomes):
    return [model.objects.get_or_create(nome=n)[0] for n in nomes or []]


@transaction.atomic
def apply_game(dados, *, update=True):
    """Cria/atualiza um jogo (publicado) e liga as taxonomias resolvidas.

    Casa por `steam_appid`. Com `update=False`, não mexe num jogo já existente
    (só cria os que faltam). Retorna `(game, created)`.
    """
    appid = dados['steam_appid']
    if not update and Game.objects.filter(steam_appid=appid).exists():
        return Game.objects.get(steam_appid=appid), False

    game, created = Game.objects.update_or_create(
        steam_appid=appid,
        defaults={
            'titulo': dados['titulo'],
            'sinopse': dados.get('sinopse') or '',
            'ano_lancamento': dados.get('ano_lancamento'),
            'capa_url': dados.get('capa_url'),
            'banner_url': dados.get('banner_url'),
            'status_publicacao': Game.StatusPublicacao.PUBLICADO,
        },
    )
    game.genres.set(_taxonomia(Genre, dados.get('genres')))
    game.platforms.set(_taxonomia(Platform, dados.get('platforms')))
    game.developers.set(_taxonomia(Developer, dados.get('developers')))
    game.publishers.set(_taxonomia(Publisher, dados.get('publishers')))
    return game, created


def apply_games(lista, *, update=True, on_event=None):
    """Aplica uma lista de dicts de jogos. Retorna dict com as contagens.

    `on_event(game, evento)` é chamado por jogo com evento em
    {'criado','atualizado','pulado'} — útil para log de progresso.
    """
    contagens = {'criados': 0, 'atualizados': 0, 'pulados': 0}
    for dados in lista:
        game, created = apply_game(dados, update=update)
        if created:
            contagens['criados'] += 1
            evento = 'criado'
        elif update:
            contagens['atualizados'] += 1
            evento = 'atualizado'
        else:
            contagens['pulados'] += 1
            evento = 'pulado'
        if on_event:
            on_event(game, evento)
    return contagens
