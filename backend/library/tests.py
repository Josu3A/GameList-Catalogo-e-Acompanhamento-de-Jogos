"""Critérios de aceitação da lista pessoal e do perfil (CONTEXTO_PROJETO §4)."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Game

from .models import UserGame

User = get_user_model()


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
