"""Popula o banco com os dados de demonstração — agora com senhas reais (hash do
Django) e com o **catálogo completo** dos ~100 jogos famosos da Steam, carregado
do snapshot offline (`catalog/seed_data.py`, sem acessar a rede). Idempotente.

Uso: python manage.py seed_demo
Senha de todos os usuários de demonstração: senha123
"""
from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from catalog import seed_data
from catalog.models import Game
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

        # Catálogo: 100 jogos famosos da Steam, do snapshot offline -----------
        jogos_snapshot = seed_data.load_top_games()
        if not jogos_snapshot:
            raise CommandError(
                'Snapshot do catálogo ausente (catalog/data/steam_top_games.json). '
                'Gere-o com "python manage.py seed_steam_top" antes de semear.'
            )
        contagens = seed_data.apply_games(jogos_snapshot, update=False)
        total_jogos = Game.objects.count()

        # Lookup por appid dos jogos citados nas listas/extensões da demo.
        appids_demo = {appid for _, appid, _ in LISTAS_PESSOAIS}
        games = {appid: Game.objects.get(steam_appid=appid) for appid in appids_demo}

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
            'Seed concluído: 3 usuários (senha "%s"), %d jogos no catálogo '
            '(%d novos), listas pessoais e dados das extensões.'
            % (SENHA_DEMO, total_jogos, contagens['criados']),
        ))
