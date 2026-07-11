"""Popula o banco com os dados de demonstração de db/seed.sql — agora com
senhas reais (hash do Django). Idempotente: pode rodar mais de uma vez.

Uso: python manage.py seed_demo
Senha de todos os usuários de demonstração: senha123
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from catalog.models import Developer, Game, Genre, Platform, Publisher
from library.models import UserGame
from social.models import Friendship, Notification, ReviewLike

User = get_user_model()

SENHA_DEMO = 'senha123'

USUARIOS = [
    # (nome, email, tipo, bio)
    ('Administrador', 'admin@gamelist.dev', 'admin', 'Curador do catálogo.'),
    ('Ana Souza', 'ana@gamelist.dev', 'comum', 'Caçadora de platinas e fã de indies.'),
    ('Bruno Lima', 'bruno@gamelist.dev', 'comum', 'Backlog eterno, mas um dia eu zero tudo.'),
]

GENEROS = ['Ação', 'RPG', 'Aventura', 'Indie', 'Simulação', 'Roguelike',
           'Plataforma', 'Metroidvania']

PLATAFORMAS = ['PC', 'PlayStation 5', 'PlayStation 4', 'Xbox Series X|S',
               'Xbox One', 'Nintendo Switch']

DEVELOPERS = ['FromSoftware', 'Supergiant Games', 'ConcernedApe', 'Team Cherry',
              'Extremely OK Games']

PUBLISHERS = ['Bandai Namco Entertainment', 'Supergiant Games', 'ConcernedApe',
              'Team Cherry', 'Extremely OK Games']

JOGOS = [
    # (titulo, ano, sinopse, steam_appid, generos, plataformas, devs, pubs)
    ('Elden Ring', 2022,
     'RPG de ação em mundo aberto nas Terras Intermédias, criado por Hidetaka '
     'Miyazaki e George R. R. Martin.',
     1245620,
     ['Ação', 'RPG'],
     ['PC', 'PlayStation 5', 'PlayStation 4', 'Xbox Series X|S', 'Xbox One'],
     ['FromSoftware'], ['Bandai Namco Entertainment']),
    ('Hades', 2020,
     'Roguelike de ação em que Zagreus tenta escapar do submundo grego, '
     'desafiando o próprio pai, Hades.',
     1145360,
     ['Ação', 'Indie', 'Roguelike'],
     ['PC', 'PlayStation 5', 'Xbox Series X|S', 'Nintendo Switch'],
     ['Supergiant Games'], ['Supergiant Games']),
    ('Stardew Valley', 2016,
     'Simulador de fazenda: herde um terreno, cultive, crie animais e faça '
     'parte da comunidade de Vale do Orvalho.',
     413150,
     ['Indie', 'Simulação'],
     ['PC', 'PlayStation 4', 'Xbox One', 'Nintendo Switch'],
     ['ConcernedApe'], ['ConcernedApe']),
    ('Hollow Knight', 2017,
     'Metroidvania sombrio no reino subterrâneo de Hallownest, habitado por '
     'insetos e segredos.',
     367520,
     ['Aventura', 'Indie', 'Metroidvania'],
     ['PC', 'PlayStation 4', 'Xbox One', 'Nintendo Switch'],
     ['Team Cherry'], ['Team Cherry']),
    ('Celeste', 2018,
     'Plataforma de precisão: ajude Madeline a escalar a montanha Celeste e '
     'enfrentar seus próprios demônios.',
     504230,
     ['Indie', 'Plataforma'],
     ['PC', 'PlayStation 4', 'Xbox One', 'Nintendo Switch'],
     ['Extremely OK Games'], ['Extremely OK Games']),
]

LISTAS_PESSOAIS = [
    # (email, steam_appid, campos)
    ('ana@gamelist.dev', 1145360, dict(
        status='completo', nota='9.5', horas_jogadas='112.0', platinado=True,
        data_inicio=date(2026, 1, 10), data_fim=date(2026, 3, 2),
        review='Roguelike perfeito: cada tentativa avança a história. '
               'A platina é trabalhosa mas justa.',
        fonte='manual')),
    ('ana@gamelist.dev', 367520, dict(
        status='jogando', horas_jogadas='21.5',
        data_inicio=date(2026, 6, 1), fonte='manual')),
    ('ana@gamelist.dev', 1245620, dict(status='quero_jogar', fonte='manual')),
    ('bruno@gamelist.dev', 413150, dict(
        status='pausado', nota='8.0', horas_jogadas='64.3',
        data_inicio=date(2025, 11, 20), fonte='steam_sync')),
    ('bruno@gamelist.dev', 504230, dict(
        status='abandonado', nota='6.5', horas_jogadas='4.2',
        data_inicio=date(2026, 2, 5),
        review='Jogo lindo, mas meus dedos não acompanham o capítulo 5.',
        fonte='manual')),
    ('bruno@gamelist.dev', 1245620, dict(
        status='completo', nota='10.0', horas_jogadas='98.0',
        data_inicio=date(2026, 3, 10), data_fim=date(2026, 5, 28),
        fonte='manual')),
]


class Command(BaseCommand):
    help = 'Popula o banco com os dados de demonstração (porta de db/seed.sql).'

    @transaction.atomic
    def handle(self, *args, **options):
        # Usuários -----------------------------------------------------------
        users = {}
        for nome, email, tipo, bio in USUARIOS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'nome': nome, 'tipo_usuario': tipo, 'bio': bio},
            )
            if created:
                user.set_password(SENHA_DEMO)
                user.save()
            users[email] = user

        # Catálogo de referência ----------------------------------------------
        genres = {n: Genre.objects.get_or_create(nome=n)[0] for n in GENEROS}
        platforms = {n: Platform.objects.get_or_create(nome=n)[0] for n in PLATAFORMAS}
        developers = {n: Developer.objects.get_or_create(nome=n)[0] for n in DEVELOPERS}
        publishers = {n: Publisher.objects.get_or_create(nome=n)[0] for n in PUBLISHERS}

        # Jogos publicados + junções -----------------------------------------
        games = {}
        for titulo, ano, sinopse, appid, gs, ps, ds, pbs in JOGOS:
            game, _ = Game.objects.get_or_create(
                steam_appid=appid,
                defaults={
                    'titulo': titulo,
                    'ano_lancamento': ano,
                    'sinopse': sinopse,
                    'status_publicacao': Game.StatusPublicacao.PUBLICADO,
                },
            )
            game.genres.set([genres[n] for n in gs])
            game.platforms.set([platforms[n] for n in ps])
            game.developers.set([developers[n] for n in ds])
            game.publishers.set([publishers[n] for n in pbs])
            games[appid] = game

        # Listas pessoais (cobrem os 5 status + platina + steam_sync) --------
        for email, appid, campos in LISTAS_PESSOAIS:
            UserGame.objects.update_or_create(
                user=users[email], game=games[appid], defaults=campos,
            )

        # Extensões: curtida, amizade e notificações --------------------------
        ana, bruno = users['ana@gamelist.dev'], users['bruno@gamelist.dev']
        review_hades = UserGame.objects.get(user=ana, game=games[1145360])

        ReviewLike.objects.get_or_create(user_game=review_hades, user=bruno)

        amizade, _ = Friendship.objects.get_or_create(
            user=ana, friend=bruno, defaults={'status': Friendship.Status.ACEITO},
        )

        notificacoes = [
            dict(user=bruno, actor=ana, tipo='pedido_amizade',
                 friendship=amizade, lida=True),
            dict(user=ana, actor=bruno, tipo='amizade_aceita',
                 friendship=amizade, lida=False),
            dict(user=ana, actor=bruno, tipo='review_curtida',
                 user_game=review_hades, lida=False),
        ]
        for n in notificacoes:
            Notification.objects.get_or_create(
                user=n['user'], tipo=n['tipo'],
                friendship=n.get('friendship'), user_game=n.get('user_game'),
                defaults={'actor': n['actor'], 'lida': n['lida']},
            )

        self.stdout.write(self.style.SUCCESS(
            'Seed concluído: 3 usuários (senha "%s"), %d jogos, listas pessoais '
            'e dados das extensões.' % (SENHA_DEMO, len(games)),
        ))
