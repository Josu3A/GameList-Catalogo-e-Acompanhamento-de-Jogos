"""Backfill de `data_lancamento`/`rawg_id` pros jogos já cadastrados no
catálogo (a maioria vinda da Steam, que só tem o ano em `ano_lancamento`).

Busca cada Game que ainda não tenha os dois campos preenchidos por título na
RAWG (busca exata — `catalog.rawg.buscar_por_titulo`) e aplica o mesmo
backfill "só campos vazios" do carrossel de próximos lançamentos
(`catalog.rawg.aplicar_backfill`) — nunca sobrescreve um valor já preenchido
manualmente pelo admin. Idempotente: pode rodar mais de uma vez sem efeito
colateral nos jogos já completos.

Uso:
    python manage.py sync_rawg_dates                # todos que faltam
    python manage.py sync_rawg_dates --limit 20      # só os 20 primeiros
    python manage.py sync_rawg_dates --delay 1       # segundos entre chamadas (padrão 0.5)
    python manage.py sync_rawg_dates --dry-run       # não grava; só mostra
"""
import time

import requests
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db import IntegrityError
from django.db.models import Q

from catalog import rawg
from catalog.models import Game


class Command(BaseCommand):
    help = 'Backfill de data_lancamento/rawg_id pros jogos já cadastrados, via busca por título na RAWG.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit', type=int, default=None,
            help='Processa só os N primeiros jogos (útil para testar).',
        )
        parser.add_argument(
            '--delay', type=float, default=0.5,
            help='Segundos de espera entre chamadas à RAWG (padrão 0.5).',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Não grava nada; só mostra o que seria feito.',
        )

    def handle(self, *args, **options):
        if not settings.RAWG_API_KEY:
            raise CommandError('RAWG_API_KEY não configurada (ver .env.example).')

        limit = options['limit']
        delay = options['delay']
        dry = options['dry_run']

        qs = Game.objects.filter(
            Q(rawg_id__isnull=True) | Q(data_lancamento__isnull=True),
        ).order_by('titulo')
        jogos = list(qs[:limit] if limit else qs)
        total = len(jogos)
        self.stdout.write(f'Verificando {total} jogo(s) com rawg_id/data_lancamento incompletos...')

        atualizados = sem_match = falhas = 0
        for i, game in enumerate(jogos, start=1):
            try:
                dados = rawg.buscar_por_titulo(game.titulo)
            except requests.RequestException as exc:
                falhas += 1
                self.stderr.write(self.style.WARNING(f'[{i}/{total}] "{game.titulo}": erro de rede ({exc})'))
                self._sleep(delay, i, total)
                continue

            if not dados:
                sem_match += 1
                self.stdout.write(f'[{i}/{total}] "{game.titulo}": sem match na RAWG (pulado)')
                self._sleep(delay, i, total)
                continue

            if dry:
                self.stdout.write(
                    f'[{i}/{total}] "{game.titulo}": ATUALIZARIA — '
                    f'rawg_id={dados["rawg_id"]}, data_lancamento={dados["data_lancamento"]}'
                )
            else:
                try:
                    mudou = rawg.aplicar_backfill(game, dados['rawg_id'], dados['data_lancamento'])
                except IntegrityError as exc:
                    falhas += 1
                    self.stderr.write(self.style.ERROR(f'[{i}/{total}] "{game.titulo}": falhou ao salvar ({exc})'))
                    self._sleep(delay, i, total)
                    continue

                if mudou:
                    atualizados += 1
                    self.stdout.write(
                        f'[{i}/{total}] "{game.titulo}": atualizado — '
                        f'rawg_id={game.rawg_id}, data_lancamento={game.data_lancamento}'
                    )
                else:
                    sem_match += 1
                    self.stdout.write(f'[{i}/{total}] "{game.titulo}": já estava completo (nada a fazer)')

            self._sleep(delay, i, total)

        resumo = (
            f'Concluído: {atualizados} atualizado(s), {sem_match} sem novidade, '
            f'{falhas} falha(s) — de {total} jogo(s).'
        )
        self.stdout.write(self.style.SUCCESS(('DRY-RUN — ' if dry else '') + resumo))

    def _sleep(self, delay, i, total):
        """Espaça as chamadas à RAWG (não dorme depois da última)."""
        if delay and i < total:
            time.sleep(delay)
