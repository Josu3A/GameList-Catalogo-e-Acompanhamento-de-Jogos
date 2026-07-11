"""Critérios da camada social (FRONTEND_TELAS §3): amigos, reviews+curtidas,
listas, notificações e enriquecimento do perfil."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

from catalog.models import Game
from library.models import UserGame

from .models import Friendship, List, ListItem, Notification, ReviewLike

User = get_user_model()


def _game(titulo):
    return Game.objects.create(
        titulo=titulo, status_publicacao=Game.StatusPublicacao.PUBLICADO,
    )


class AmigosTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
        )
        cls.bruno = User.objects.create_user(
            email='bruno@example.com', nome='Bruno', password='senha-forte-123',
        )
        cls.carla = User.objects.create_user(
            email='carla@example.com', nome='Carla', password='senha-forte-123',
        )

    def test_enviar_pedido_cria_notificacao(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/friendships/', {'friend_id': self.bruno.id})
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data['status'], 'pendente')
        self.assertTrue(Notification.objects.filter(
            user=self.bruno, actor=self.ana,
            tipo=Notification.Tipo.PEDIDO_AMIZADE,
        ).exists())

    def test_nao_pode_pedir_a_si_mesmo(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/friendships/', {'friend_id': self.ana.id})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pedido_duplicado_ou_invertido_bloqueado(self):
        Friendship.objects.create(user=self.ana, friend=self.bruno)
        self.client.force_authenticate(self.ana)
        dup = self.client.post('/api/friendships/', {'friend_id': self.bruno.id})
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)
        # Invertido: Bruno pedindo a Ana quando já existe Ana→Bruno.
        self.client.force_authenticate(self.bruno)
        inv = self.client.post('/api/friendships/', {'friend_id': self.ana.id})
        self.assertEqual(inv.status_code, status.HTTP_400_BAD_REQUEST)

    def test_aceitar_cria_notificacao_e_leitura_simetrica(self):
        fs = Friendship.objects.create(user=self.ana, friend=self.bruno)
        self.client.force_authenticate(self.bruno)
        resp = self.client.post(f'/api/friendships/{fs.id}/aceitar/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'aceito')
        self.assertTrue(Notification.objects.filter(
            user=self.ana, actor=self.bruno,
            tipo=Notification.Tipo.AMIZADE_ACEITA,
        ).exists())
        # Simetria: os dois veem a amizade em ?estado=amigos.
        self.client.force_authenticate(self.ana)
        vista_ana = self.client.get('/api/friendships/?estado=amigos')
        self.assertEqual(len(vista_ana.data['results']), 1)
        self.client.force_authenticate(self.bruno)
        vista_bruno = self.client.get('/api/friendships/?estado=amigos')
        self.assertEqual(len(vista_bruno.data['results']), 1)

    def test_so_o_destinatario_aceita(self):
        fs = Friendship.objects.create(user=self.ana, friend=self.bruno)
        self.client.force_authenticate(self.ana)  # a solicitante
        resp = self.client.post(f'/api/friendships/{fs.id}/aceitar/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_recusar_remove_a_linha(self):
        fs = Friendship.objects.create(user=self.ana, friend=self.bruno)
        self.client.force_authenticate(self.bruno)
        resp = self.client.delete(f'/api/friendships/{fs.id}/')
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Friendship.objects.filter(pk=fs.id).exists())

    def test_terceiro_nao_ve_nem_altera_amizade_alheia(self):
        fs = Friendship.objects.create(
            user=self.ana, friend=self.bruno, status=Friendship.Status.ACEITO,
        )
        self.client.force_authenticate(self.carla)
        listagem = self.client.get('/api/friendships/')
        self.assertEqual(len(listagem.data['results']), 0)
        remocao = self.client.delete(f'/api/friendships/{fs.id}/')
        self.assertEqual(remocao.status_code, status.HTTP_404_NOT_FOUND)


class ReviewsCurtidasTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
        )
        cls.bruno = User.objects.create_user(
            email='bruno@example.com', nome='Bruno', password='senha-forte-123',
        )
        cls.recluso = User.objects.create_user(
            email='recluso@example.com', nome='Recluso',
            password='senha-forte-123', perfil_publico=False,
        )
        cls.hades = _game('Hades')
        cls.celeste = _game('Celeste')
        cls.review_ana = UserGame.objects.create(
            user=cls.ana, game=cls.hades, status=UserGame.Status.COMPLETO,
            nota='9.0', review='Incrível.',
        )
        cls.review_recluso = UserGame.objects.create(
            user=cls.recluso, game=cls.celeste, status=UserGame.Status.COMPLETO,
            review='Só eu vejo.',
        )
        # Uma linha sem review não deve aparecer na listagem.
        UserGame.objects.create(
            user=cls.bruno, game=cls.hades, status=UserGame.Status.JOGANDO,
        )

    def test_listar_reviews_por_jogo(self):
        resp = self.client.get(f'/api/reviews/?game={self.hades.id}')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data['results']), 1)
        self.assertEqual(resp.data['results'][0]['review'], 'Incrível.')

    def test_review_de_perfil_privado_nao_aparece_para_terceiros(self):
        self.client.force_authenticate(self.bruno)
        resp = self.client.get('/api/reviews/')
        ids = [r['id'] for r in resp.data['results']]
        self.assertIn(self.review_ana.id, ids)
        self.assertNotIn(self.review_recluso.id, ids)
        # O próprio dono enxerga a review dele.
        self.client.force_authenticate(self.recluso)
        propria = self.client.get('/api/reviews/')
        self.assertIn(self.review_recluso.id, [r['id'] for r in propria.data['results']])

    def test_curtir_cria_notificacao_conta_e_flag(self):
        self.client.force_authenticate(self.bruno)
        resp = self.client.post(f'/api/reviews/{self.review_ana.id}/like/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['likes_count'], 1)
        self.assertTrue(resp.data['liked_by_me'])
        self.assertTrue(Notification.objects.filter(
            user=self.ana, actor=self.bruno,
            tipo=Notification.Tipo.REVIEW_CURTIDA, user_game=self.review_ana,
        ).exists())

    def test_descurtir_remove(self):
        ReviewLike.objects.create(user_game=self.review_ana, user=self.bruno)
        self.client.force_authenticate(self.bruno)
        resp = self.client.delete(f'/api/reviews/{self.review_ana.id}/like/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['likes_count'], 0)
        self.assertFalse(resp.data['liked_by_me'])

    def test_curtir_duas_vezes_e_idempotente(self):
        self.client.force_authenticate(self.bruno)
        self.client.post(f'/api/reviews/{self.review_ana.id}/like/')
        segunda = self.client.post(f'/api/reviews/{self.review_ana.id}/like/')
        self.assertEqual(segunda.data['likes_count'], 1)
        self.assertEqual(ReviewLike.objects.filter(user_game=self.review_ana).count(), 1)
        self.assertEqual(Notification.objects.filter(
            tipo=Notification.Tipo.REVIEW_CURTIDA,
        ).count(), 1)

    def test_curtir_a_propria_review_nao_notifica(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.post(f'/api/reviews/{self.review_ana.id}/like/')
        self.assertEqual(resp.data['likes_count'], 1)
        self.assertFalse(Notification.objects.filter(
            tipo=Notification.Tipo.REVIEW_CURTIDA,
        ).exists())


class ListasTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
        )
        cls.bruno = User.objects.create_user(
            email='bruno@example.com', nome='Bruno', password='senha-forte-123',
        )
        cls.hades = _game('Hades')
        cls.celeste = _game('Celeste')

    def test_criar_lista_e_nome_duplicado(self):
        self.client.force_authenticate(self.ana)
        criar = self.client.post('/api/lists/', {'nome': 'Top RPGs'})
        self.assertEqual(criar.status_code, status.HTTP_201_CREATED)
        dup = self.client.post('/api/lists/', {'nome': 'Top RPGs'})
        self.assertEqual(dup.status_code, status.HTTP_400_BAD_REQUEST)

    def test_adicionar_remover_e_reordenar_itens(self):
        lista = List.objects.create(user=self.ana, nome='Favoritos')
        self.client.force_authenticate(self.ana)
        self.client.post(f'/api/lists/{lista.id}/items/', {'game_id': self.hades.id})
        self.client.post(f'/api/lists/{lista.id}/items/', {'game_id': self.celeste.id})
        detalhe = self.client.get(f'/api/lists/{lista.id}/')
        self.assertEqual(detalhe.data['total_itens'], 2)

        reorder = self.client.patch(
            f'/api/lists/{lista.id}/reorder/',
            {'game_ids': [self.celeste.id, self.hades.id]}, format='json',
        )
        self.assertEqual(reorder.status_code, status.HTTP_200_OK)
        ordem_titulos = [item['game']['titulo'] for item in reorder.data['items']]
        self.assertEqual(ordem_titulos, ['Celeste', 'Hades'])

        remover = self.client.delete(f'/api/lists/{lista.id}/items/{self.hades.id}/')
        self.assertEqual(remover.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(ListItem.objects.filter(lista=lista, game=self.hades).exists())

    def test_item_duplicado_rejeitado(self):
        lista = List.objects.create(user=self.ana, nome='Favoritos')
        ListItem.objects.create(lista=lista, game=self.hades)
        self.client.force_authenticate(self.ana)
        resp = self.client.post(
            f'/api/lists/{lista.id}/items/', {'game_id': self.hades.id},
        )
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_so_o_dono_altera_a_lista(self):
        lista = List.objects.create(user=self.ana, nome='Favoritos', publica=True)
        self.client.force_authenticate(self.bruno)
        add = self.client.post(
            f'/api/lists/{lista.id}/items/', {'game_id': self.hades.id},
        )
        self.assertEqual(add.status_code, status.HTTP_403_FORBIDDEN)

    def test_listas_publicas_de_outro_visiveis_privadas_nao(self):
        List.objects.create(user=self.ana, nome='Pública', publica=True)
        List.objects.create(user=self.ana, nome='Privada', publica=False)
        self.client.force_authenticate(self.bruno)
        resp = self.client.get(f'/api/lists/?user={self.ana.id}')
        nomes = [item['nome'] for item in resp.data['results']]
        self.assertEqual(nomes, ['Pública'])

    def test_indice_mostra_apenas_as_minhas(self):
        List.objects.create(user=self.ana, nome='Da Ana')
        List.objects.create(user=self.bruno, nome='Do Bruno')
        self.client.force_authenticate(self.ana)
        resp = self.client.get('/api/lists/')
        nomes = [item['nome'] for item in resp.data['results']]
        self.assertEqual(nomes, ['Da Ana'])


class NotificacoesTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
        )
        cls.bruno = User.objects.create_user(
            email='bruno@example.com', nome='Bruno', password='senha-forte-123',
        )
        fs = Friendship.objects.create(user=cls.bruno, friend=cls.ana)
        cls.notif = Notification.objects.create(
            user=cls.ana, actor=cls.bruno,
            tipo=Notification.Tipo.PEDIDO_AMIZADE, friendship=fs,
        )

    def test_lista_apenas_as_proprias(self):
        self.client.force_authenticate(self.ana)
        minhas = self.client.get('/api/notifications/')
        self.assertEqual(len(minhas.data['results']), 1)
        self.client.force_authenticate(self.bruno)
        alheias = self.client.get('/api/notifications/')
        self.assertEqual(len(alheias.data['results']), 0)

    def test_contador_de_nao_lidas(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.get('/api/notifications/nao-lidas/')
        self.assertEqual(resp.data['count'], 1)

    def test_marcar_uma_como_lida(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.post(f'/api/notifications/{self.notif.id}/marcar-lida/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(resp.data['lida'])
        self.notif.refresh_from_db()
        self.assertTrue(self.notif.lida)

    def test_marcar_todas_como_lidas(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.post('/api/notifications/marcar-todas-lidas/')
        self.assertEqual(resp.data['atualizadas'], 1)
        contador = self.client.get('/api/notifications/nao-lidas/')
        self.assertEqual(contador.data['count'], 0)


class PerfilSocialTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.ana = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
        )
        cls.bruno = User.objects.create_user(
            email='bruno@example.com', nome='Bruno', password='senha-forte-123',
        )
        cls.carla = User.objects.create_user(
            email='carla@example.com', nome='Carla', password='senha-forte-123',
        )
        Friendship.objects.create(
            user=cls.ana, friend=cls.bruno, status=Friendship.Status.ACEITO,
        )
        List.objects.create(user=cls.ana, nome='Pública', publica=True)
        List.objects.create(user=cls.ana, nome='Privada', publica=False)

    def test_perfil_traz_amizade_e_listas_publicas(self):
        self.client.force_authenticate(self.bruno)
        resp = self.client.get(f'/api/profiles/{self.ana.id}/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['amizade'], 'amigos')
        nomes = [item['nome'] for item in resp.data['listas_publicas']]
        self.assertEqual(nomes, ['Pública'])

    def test_estados_de_pedido_pendente(self):
        Friendship.objects.create(user=self.carla, friend=self.ana)
        # Ana recebeu o pedido de Carla.
        self.client.force_authenticate(self.ana)
        vista_ana = self.client.get(f'/api/profiles/{self.carla.id}/')
        self.assertEqual(vista_ana.data['amizade'], 'pedido_recebido')
        # Carla enviou o pedido para Ana.
        self.client.force_authenticate(self.carla)
        vista_carla = self.client.get(f'/api/profiles/{self.ana.id}/')
        self.assertEqual(vista_carla.data['amizade'], 'pedido_enviado')

    def test_proprio_perfil_e_anonimo(self):
        self.client.force_authenticate(self.ana)
        propria = self.client.get(f'/api/profiles/{self.ana.id}/')
        self.assertEqual(propria.data['amizade'], 'eu')
        self.client.force_authenticate(user=None)
        anon = self.client.get(f'/api/profiles/{self.bruno.id}/')
        self.assertIsNone(anon.data['amizade'])
