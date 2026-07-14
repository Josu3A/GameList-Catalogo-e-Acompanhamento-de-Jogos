"""Critérios de aceitação da lista pessoal e do perfil (CONTEXTO_PROJETO §4)."""
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Achievement, Game

from .models import UserAchievement, UserGame

User = get_user_model()

STEAM_ID = '76561198000000009'


class MinhaListaTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
        )
        cls.bruno = User.objects.create_user(
            email='bruno@example.com', nome='Bruno', password='senha-forte-123',
        )
        cls.hades = Game.objects.create(
            titulo='Hades', status_publicacao=Game.StatusPublicacao.PUBLICADO,
        )
        cls.celeste = Game.objects.create(
            titulo='Celeste', status_publicacao=Game.StatusPublicacao.PUBLICADO,
        )
        cls.rascunho = Game.objects.create(
            titulo='Silksong', status_publicacao=Game.StatusPublicacao.RASCUNHO,
        )

    def test_anonimo_nao_acessa_a_lista(self):
        resp = self.client.get('/api/my-games/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_comum_adiciona_jogo_e_muda_status(self):
        self.client.force_authenticate(self.ana)
        post = self.client.post('/api/my-games/', {
            'game_id': self.hades.id, 'status': 'jogando',
        })
        self.assertEqual(post.status_code, status.HTTP_201_CREATED)
        self.assertEqual(post.data['game']['titulo'], 'Hades')

        patch = self.client.patch(f"/api/my-games/{post.data['id']}/", {
            'status': 'completo', 'platinado': True, 'nota': '9.5',
        })
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertEqual(patch.data['status'], 'completo')
        self.assertTrue(patch.data['platinado'])

    def test_jogo_rascunho_nao_entra_na_lista(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/my-games/', {
            'game_id': self.rascunho.id, 'status': 'quero_jogar',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_jogo_duplicado_na_lista_e_rejeitado(self):
        UserGame.objects.create(
            user=self.ana, game=self.hades, status=UserGame.Status.JOGANDO,
        )
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/my-games/', {
            'game_id': self.hades.id, 'status': 'completo',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_nota_fora_da_escala_e_rejeitada(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/my-games/', {
            'game_id': self.hades.id, 'status': 'completo', 'nota': '11',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_nao_edita_lista_de_outro(self):
        do_bruno = UserGame.objects.create(
            user=self.bruno, game=self.celeste, status=UserGame.Status.JOGANDO,
        )
        self.client.force_authenticate(self.ana)
        patch = self.client.patch(f'/api/my-games/{do_bruno.id}/', {
            'status': 'abandonado',
        })
        # o queryset é filtrado pelo dono, então o item do Bruno nem existe p/ Ana
        self.assertEqual(patch.status_code, status.HTTP_404_NOT_FOUND)
        do_bruno.refresh_from_db()
        self.assertEqual(do_bruno.status, UserGame.Status.JOGANDO)

    def test_lista_so_mostra_os_proprios_jogos(self):
        UserGame.objects.create(
            user=self.ana, game=self.hades, status=UserGame.Status.JOGANDO,
        )
        UserGame.objects.create(
            user=self.bruno, game=self.celeste, status=UserGame.Status.JOGANDO,
        )
        self.client.force_authenticate(self.ana)
        resp = self.client.get('/api/my-games/')
        titulos = [item['game']['titulo'] for item in resp.data['results']]
        self.assertEqual(titulos, ['Hades'])


class PerfilPublicoTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
        )
        cls.recluso = User.objects.create_user(
            email='recluso@example.com', nome='Recluso',
            password='senha-forte-123', perfil_publico=False,
        )
        cls.hades = Game.objects.create(
            titulo='Hades', status_publicacao=Game.StatusPublicacao.PUBLICADO,
        )
        cls.celeste = Game.objects.create(
            titulo='Celeste', status_publicacao=Game.StatusPublicacao.PUBLICADO,
        )
        UserGame.objects.create(
            user=cls.ana, game=cls.hades, status=UserGame.Status.COMPLETO,
            platinado=True, nota='9.5',
        )
        UserGame.objects.create(
            user=cls.ana, game=cls.celeste, status=UserGame.Status.JOGANDO,
        )

    def test_perfil_publico_destaca_platinas(self):
        resp = self.client.get(f'/api/profiles/{self.ana.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['jogos']), 2)
        platinas = resp.data['platinas']
        self.assertEqual(len(platinas), 1)
        self.assertEqual(platinas[0]['game']['titulo'], 'Hades')

    def test_perfil_privado_nao_e_visivel_para_terceiros(self):
        anonimo = self.client.get(f'/api/profiles/{self.recluso.id}/')
        self.assertEqual(anonimo.status_code, status.HTTP_404_NOT_FOUND)

        self.client.force_authenticate(self.ana)
        outro_usuario = self.client.get(f'/api/profiles/{self.recluso.id}/')
        self.assertEqual(outro_usuario.status_code, status.HTTP_404_NOT_FOUND)

    def test_perfil_privado_e_visivel_para_o_dono(self):
        self.client.force_authenticate(self.recluso)
        resp = self.client.get(f'/api/profiles/{self.recluso.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)


@override_settings(STEAM_API_KEY='chave-de-teste')
class SteamSyncTests(APITestCase):
    """Sync de biblioteca e conquistas (casamento por steam_appid)."""

    def setUp(self):
        self.ana = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
            steam_id=STEAM_ID,
        )
        self.hades = Game.objects.create(
            titulo='Hades', steam_appid=1145360,
            status_publicacao=Game.StatusPublicacao.PUBLICADO,
        )

    def test_sync_exige_steam_vinculada(self):
        self.ana.steam_id = None
        self.ana.save(update_fields=['steam_id'])
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/my-games/steam-sync/')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(STEAM_API_KEY='')
    def test_sync_sem_chave_no_servidor(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/my-games/steam-sync/')
        self.assertEqual(resp.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)

    @patch('library.views.steam.get_owned_games')
    def test_sync_cria_casando_por_appid_e_ignora_fora_do_catalogo(self, owned):
        owned.return_value = [
            {'appid': 1145360, 'name': 'Hades', 'playtime_forever': 120},
            {'appid': 999999, 'name': 'Desconhecido', 'playtime_forever': 0},
        ]
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/my-games/steam-sync/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {
            'criados': 1, 'atualizados': 0, 'ignorados_sem_catalogo': 1,
        })
        ug = UserGame.objects.get(user=self.ana, game=self.hades)
        self.assertEqual(ug.fonte, UserGame.Fonte.STEAM_SYNC)
        self.assertEqual(float(ug.horas_jogadas), 2.0)

        # Segunda passada só atualiza as horas (fonte steam_sync).
        owned.return_value[0]['playtime_forever'] = 180
        resp2 = self.client.post('/api/my-games/steam-sync/')
        self.assertEqual(resp2.data['atualizados'], 1)
        ug.refresh_from_db()
        self.assertEqual(float(ug.horas_jogadas), 3.0)

    @patch('library.views.steam.get_player_achievements')
    @patch('library.views.steam.get_schema_for_game')
    def test_achievements_100_pct_sugere_platinado(self, schema, player):
        UserGame.objects.create(
            user=self.ana, game=self.hades, status=UserGame.Status.COMPLETO,
        )
        schema.return_value = [
            {'steam_apiname': 'A', 'nome': 'Conquista A', 'descricao': None, 'icon_url': None},
            {'steam_apiname': 'B', 'nome': 'Conquista B', 'descricao': None, 'icon_url': None},
        ]
        player.return_value = [
            {'apiname': 'A', 'achieved': True, 'unlocktime': 1600000000},
            {'apiname': 'B', 'achieved': True, 'unlocktime': 0},
        ]
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/my-games/steam-achievements/', {
            'game_id': self.hades.id,
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, {
            'total': 2, 'desbloqueadas': 2, 'percent': 100, 'platinado': True,
        })
        self.assertEqual(Achievement.objects.filter(game=self.hades).count(), 2)
        self.assertEqual(UserAchievement.objects.filter(user=self.ana).count(), 2)
        ug = UserGame.objects.get(user=self.ana, game=self.hades)
        self.assertTrue(ug.platinado)

    def test_achievements_jogo_fora_da_lista_404(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/my-games/steam-achievements/', {
            'game_id': self.hades.id,
        })
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


class SeedDemoTests(TestCase):
    """O seed inicializa o banco com o catálogo dos 100 jogos (offline) + demo."""

    def test_seed_demo_popula_catalogo_offline_e_dados_demo(self):
        call_command('seed_demo', stdout=StringIO(), stderr=StringIO())

        # 100 jogos do snapshot versionado, todos publicados (sem acessar a rede).
        self.assertEqual(Game.objects.count(), 100)
        self.assertEqual(
            Game.objects.filter(status_publicacao=Game.StatusPublicacao.PUBLICADO).count(),
            100,
        )
        # Um jogo-chave da demo existe e tem taxonomia ligada.
        elden = Game.objects.get(steam_appid=1245620)
        self.assertTrue(elden.genres.exists())

        # Usuários + listas pessoais + a platina da Ana (Hades).
        self.assertEqual(User.objects.count(), 3)
        self.assertTrue(UserGame.objects.filter(platinado=True).exists())

    def test_seed_demo_idempotente(self):
        call_command('seed_demo', stdout=StringIO(), stderr=StringIO())
        call_command('seed_demo', stdout=StringIO(), stderr=StringIO())
        self.assertEqual(Game.objects.count(), 100)
        self.assertEqual(User.objects.count(), 3)
