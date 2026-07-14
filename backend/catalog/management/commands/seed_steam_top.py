"""Popula o catálogo com ~100 jogos famosos da Steam, via Storefront API.

Cada AppID é buscado na loja da Steam (o MESMO autofill do botão "Buscar da
Steam" — `catalog.steam.fetch_appdetails`), as taxonomias (gênero/plataforma/
desenvolvedora/publicadora) são resolvidas por `get_or_create` e o jogo é criado
já como **publicado**. Idempotente: casa por `steam_appid`, então pode rodar
mais de uma vez sem duplicar.

Uso:
    python manage.py seed_steam_top                 # cria os que faltam
    python manage.py seed_steam_top --limit 10      # só os 10 primeiros
    python manage.py seed_steam_top --delay 2       # 2s entre chamadas à Steam
    python manage.py seed_steam_top --update        # atualiza jogos já existentes
    python manage.py seed_steam_top --dry-run       # não grava; só mostra

Observações:
- A Storefront é pública (sem chave), mas tem limite de taxa — por isso o
  `--delay` entre chamadas (padrão 1s) e as retentativas com espera.
- O título e as artes vêm da própria Steam; o nome no comentário de cada AppID
  é só referência humana. AppIDs não encontrados são contados e pulados.
"""
import time

import requests
from django.core.management.base import BaseCommand

from catalog import seed_data, steam
from catalog.models import Game

# 100 AppIDs de jogos famosos da Steam (lista deduplicada). O comentário é só
# referência; o dado gravado vem da resposta da Steam.
TOP_STEAM_APPIDS = [
    730,      # Counter-Strike 2
    570,      # Dota 2
    440,      # Team Fortress 2
    620,      # Portal 2
    400,      # Portal
    220,      # Half-Life 2
    546560,   # Half-Life: Alyx
    550,      # Left 4 Dead 2
    500,      # Left 4 Dead
    4000,     # Garry's Mod
    240,      # Counter-Strike: Source
    10,       # Counter-Strike
    578080,   # PUBG: BATTLEGROUNDS
    1172470,  # Apex Legends
    1085660,  # Destiny 2
    359550,   # Tom Clancy's Rainbow Six Siege
    252490,   # Rust
    230410,   # Warframe
    238960,   # Path of Exile
    236390,   # War Thunder
    291550,   # Brawlhalla
    218620,   # PAYDAY 2
    444090,   # Paladins
    381210,   # Dead by Daylight
    739630,   # Phasmophobia
    1966720,  # Lethal Company
    632360,   # Risk of Rain 2
    322330,   # Don't Starve Together
    105600,   # Terraria
    892970,   # Valheim
    526870,   # Satisfactory
    251570,   # 7 Days to Die
    346110,   # ARK: Survival Evolved
    264710,   # Subnautica
    848450,   # Subnautica: Below Zero
    275850,   # No Man's Sky
    227300,   # Euro Truck Simulator 2
    270880,   # American Truck Simulator
    431960,   # Wallpaper Engine
    620980,   # Beat Saber
    413150,   # Stardew Valley
    1245620,  # Elden Ring
    1091500,  # Cyberpunk 2077
    292030,   # The Witcher 3: Wild Hunt
    1174180,  # Red Dead Redemption 2
    271590,   # Grand Theft Auto V
    1086940,  # Baldur's Gate 3
    990080,   # Hogwarts Legacy
    377160,   # Fallout 4
    22380,    # Fallout: New Vegas
    22370,    # Fallout 3: Game of the Year Edition
    489830,   # The Elder Scrolls V: Skyrim Special Edition
    72850,    # The Elder Scrolls V: Skyrim
    1817070,  # Marvel's Spider-Man Remastered
    1817190,  # Marvel's Spider-Man: Miles Morales
    1888930,  # The Last of Us Part I
    582010,   # Monster Hunter: World
    1446780,  # Monster Hunter Rise
    601150,   # Devil May Cry 5
    782330,   # DOOM Eternal
    379720,   # DOOM (2016)
    1030840,  # Mafia: Definitive Edition
    435150,   # Divinity: Original Sin 2
    552520,   # Far Cry 5
    289070,   # Sid Meier's Civilization VI
    8930,     # Sid Meier's Civilization V
    294100,   # RimWorld
    255710,   # Cities: Skylines
    236850,   # Europa Universalis IV
    281990,   # Stellaris
    394360,   # Hearts of Iron IV
    203770,   # Crusader Kings II
    1158310,  # Crusader Kings III
    261550,   # Mount & Blade II: Bannerlord
    48700,    # Mount & Blade: Warband
    1145360,  # Hades
    367520,   # Hollow Knight
    504230,   # Celeste
    391540,   # Undertale
    268910,   # Cuphead
    646570,   # Slay the Spire
    588650,   # Dead Cells
    262060,   # Darkest Dungeon
    311690,   # Enter the Gungeon
    1426210,  # It Takes Two
    1237970,  # Titanfall 2
    250900,   # The Binding of Isaac: Rebirth
    233860,   # Kenshi
    244210,   # Assetto Corsa
    1293830,  # Forza Horizon 4
    1551360,  # Forza Horizon 5
    322170,   # Geometry Dash
    976730,   # Halo: The Master Chief Collection
    1240440,  # Halo Infinite
    361420,   # ASTRONEER
    632470,   # Disco Elysium - The Final Cut
    1794680,  # Vampire Survivors
    1057090,  # Ori and the Will of the Wisps
    387290,   # Ori and the Blind Forest: Definitive Edition
    570940,   # DARK SOULS: REMASTERED
]


class Command(BaseCommand):
    help = 'Popula o catálogo com ~100 jogos famosos da Steam (Storefront API).'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit', type=int, default=None,
            help='Processa só os N primeiros AppIDs (útil para testar).',
        )
        parser.add_argument(
            '--delay', type=float, default=1.0,
            help='Segundos de espera entre chamadas à Steam (padrão 1.0).',
        )
        parser.add_argument(
            '--lang', default='portuguese',
            help='Idioma dos textos da Steam (padrão portuguese).',
        )
        parser.add_argument(
            '--update', action='store_true',
            help='Atualiza jogos já existentes (por padrão, pula os que já existem).',
        )
        parser.add_argument(
            '--offline', action='store_true',
            help='Semeia do snapshot versionado (catalog/data), sem acessar a Steam.',
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Não grava nada; só mostra o que seria feito.',
        )

    def handle(self, *args, **options):
        limit = options['limit']
        delay = options['delay']
        lang = options['lang']
        do_update = options['update']
        dry = options['dry_run']

        if options['offline']:
            return self._handle_offline(limit, do_update, dry)

        appids = TOP_STEAM_APPIDS[:limit] if limit else TOP_STEAM_APPIDS
        total = len(appids)
        criados = atualizados = pulados = falhas = 0

        self.stdout.write(
            f'Buscando {total} jogos na Steam '
            f'(delay={delay}s, lang={lang}, update={do_update}, dry_run={dry})...'
        )

        for i, appid in enumerate(appids, start=1):
            existing = Game.objects.filter(steam_appid=appid).first()
            if existing and not do_update:
                pulados += 1
                self.stdout.write(
                    f'[{i}/{total}] {appid}: já existe — "{existing.titulo}" (pulado)'
                )
                continue

            dados = self._fetch(appid, lang)
            if dados is None:
                falhas += 1
                self.stderr.write(
                    self.style.WARNING(f'[{i}/{total}] {appid}: não encontrado/erro (pulado)')
                )
                self._sleep(delay, i, total)
                continue

            if dry:
                acao = 'ATUALIZARIA' if existing else 'CRIARIA'
                self.stdout.write(
                    f'[{i}/{total}] {appid}: {acao} "{dados["titulo"]}" '
                    f'({dados["ano_lancamento"]}) — {len(dados["genres"])} gênero(s), '
                    f'{len(dados["platforms"])} plataforma(s)'
                )
            else:
                game, created = seed_data.apply_game(dados, update=True)
                if created:
                    criados += 1
                    self.stdout.write(f'[{i}/{total}] {appid}: criado — "{game.titulo}"')
                else:
                    atualizados += 1
                    self.stdout.write(f'[{i}/{total}] {appid}: atualizado — "{game.titulo}"')

            self._sleep(delay, i, total)

        resumo = (
            f'Concluído: {criados} criado(s), {atualizados} atualizado(s), '
            f'{pulados} já existente(s), {falhas} falha(s) — de {total} AppIDs.'
        )
        self.stdout.write(self.style.SUCCESS(('DRY-RUN — ' if dry else '') + resumo))

    # -- auxiliares ----------------------------------------------------------

    def _sleep(self, delay, i, total):
        """Espaça as chamadas à Steam (não dorme depois do último)."""
        if delay and i < total:
            time.sleep(delay)

    def _fetch(self, appid, lang, tentativas=3):
        """`fetch_appdetails` com retentativas (limite de taxa/erro de rede)."""
        for tentativa in range(1, tentativas + 1):
            try:
                return steam.fetch_appdetails(appid, lang=lang)
            except requests.RequestException as exc:
                if tentativa == tentativas:
                    self.stderr.write(f'    {appid}: falhou após {tentativas} tentativas ({exc})')
                    return None
                espera = 5 * tentativa
                self.stderr.write(
                    f'    {appid}: {exc} — nova tentativa em {espera}s '
                    f'({tentativa}/{tentativas})'
                )
                time.sleep(espera)
        return None

    def _handle_offline(self, limit, do_update, dry):
        """Semeia do snapshot versionado (catalog/data), sem acessar a Steam."""
        jogos = seed_data.load_top_games()
        if not jogos:
            self.stderr.write(self.style.ERROR(
                'Snapshot não encontrado (catalog/data/steam_top_games.json).'
            ))
            return
        jogos = jogos[:limit] if limit else jogos
        total = len(jogos)
        self.stdout.write(
            f'[offline] Semeando {total} jogos do snapshot '
            f'(update={do_update}, dry_run={dry})...'
        )
        if dry:
            for i, dados in enumerate(jogos, start=1):
                existe = Game.objects.filter(steam_appid=dados['steam_appid']).exists()
                acao = ('ATUALIZARIA' if do_update else 'MANTERIA') if existe else 'CRIARIA'
                self.stdout.write(f'[{i}/{total}] {dados["steam_appid"]}: {acao} "{dados["titulo"]}"')
            self.stdout.write(self.style.SUCCESS(f'DRY-RUN — {total} jogos no snapshot.'))
            return

        contagens = seed_data.apply_games(jogos, update=do_update)
        self.stdout.write(self.style.SUCCESS(
            '[offline] Concluído: {criados} criado(s), {atualizados} atualizado(s), '
            '{pulados} já existente(s).'.format(**contagens)
        ))
