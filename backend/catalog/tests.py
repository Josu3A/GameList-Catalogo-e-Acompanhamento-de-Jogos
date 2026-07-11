"""Critérios de aceitação do catálogo (CONTEXTO_PROJETO §4):
só admin faz CRUD em games; usuário comum tem leitura (apenas publicados)."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from library.models import UserGame

from .models import Game, Genre

User = get_user_model()


class CatalogPermissionsTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = User.objects.create_superuser(
            email='admin@example.com', nome='Admin', password='senha-forte-123',
        )
        cls.comum = User.objects.create_user(
            email='comum@example.com', nome='Comum', password='senha-forte-123',
        )
        cls.genero = Genre.objects.create(nome='RPG')
        cls.publicado = Game.objects.create(
            titulo='Hades', status_publicacao=Game.StatusPublicacao.PUBLICADO,
        )
        cls.rascunho = Game.objects.create(
            titulo='Silksong', status_publicacao=Game.StatusPublicacao.RASCUNHO,
        )

    def test_anonimo_ve_apenas_jogos_publicados(self):
        resp = self.client.get('/api/games/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        titulos = [g['titulo'] for g in resp.data['results']]
        self.assertEqual(titulos, ['Hades'])

    def test_comum_nao_ve_rascunho_nem_no_detalhe(self):
        self.client.force_authenticate(self.comum)
        resp = self.client.get(f'/api/games/{self.rascunho.id}/')
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_ve_rascunhos(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get('/api/games/')
        titulos = {g['titulo'] for g in resp.data['results']}
        self.assertIn('Silksong', titulos)

    def test_anonimo_nao_cria_jogo(self):
        resp = self.client.post('/api/games/', {'titulo': 'Hack'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_comum_nao_cria_edita_nem_remove_jogo(self):
        self.client.force_authenticate(self.comum)
        post = self.client.post('/api/games/', {'titulo': 'Novo'})
        patch = self.client.patch(
            f'/api/games/{self.publicado.id}/', {'titulo': 'Alterado'},
        )
        delete = self.client.delete(f'/api/games/{self.publicado.id}/')
        self.assertEqual(post.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(patch.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(delete.status_code, status.HTTP_403_FORBIDDEN)
        self.publicado.refresh_from_db()
        self.assertEqual(self.publicado.titulo, 'Hades')

    def test_admin_faz_crud_completo(self):
        self.client.force_authenticate(self.admin)

        post = self.client.post('/api/games/', {
            'titulo': 'Elden Ring',
            'ano_lancamento': 2022,
            'status_publicacao': 'publicado',
            'genre_ids': [self.genero.id],
        })
        self.assertEqual(post.status_code, status.HTTP_201_CREATED)
        game_id = post.data['id']
        self.assertEqual(post.data['genres'][0]['nome'], 'RPG')

        patch = self.client.patch(f'/api/games/{game_id}/', {'ano_lancamento': 2023})
        self.assertEqual(patch.status_code, status.HTTP_200_OK)
        self.assertEqual(patch.data['ano_lancamento'], 2023)

        delete = self.client.delete(f'/api/games/{game_id}/')
        self.assertEqual(delete.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Game.objects.filter(id=game_id).exists())

    def test_jogo_presente_em_listas_nao_pode_ser_removido(self):
        UserGame.objects.create(
            user=self.comum, game=self.publicado, status=UserGame.Status.JOGANDO,
        )
        self.client.force_authenticate(self.admin)
        resp = self.client.delete(f'/api/games/{self.publicado.id}/')
        self.assertEqual(resp.status_code, status.HTTP_409_CONFLICT)
        self.assertTrue(Game.objects.filter(id=self.publicado.id).exists())
