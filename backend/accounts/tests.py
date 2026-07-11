"""Critérios de aceitação de autenticação (CONTEXTO_PROJETO §4):
login inválido é rejeitado; áreas restritas exigem autenticação."""
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthApiTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
        )

    def test_register_cria_usuario_comum_mesmo_enviando_tipo_admin(self):
        resp = self.client.post('/api/auth/register/', {
            'nome': 'Novo Usuário',
            'email': 'novo@example.com',
            'password': 'senha-forte-123',
            'tipo_usuario': 'admin',  # deve ser ignorado
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        novo = User.objects.get(email='novo@example.com')
        self.assertEqual(novo.tipo_usuario, User.TipoUsuario.COMUM)

    def test_login_valido_cria_sessao(self):
        resp = self.client.post('/api/auth/login/', {
            'email': 'ana@example.com', 'password': 'senha-forte-123',
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data['email'], 'ana@example.com')

    def test_login_com_credenciais_invalidas_e_rejeitado(self):
        resp = self.client.post('/api/auth/login/', {
            'email': 'ana@example.com', 'password': 'senha-errada',
        })
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_area_restrita_exige_autenticacao(self):
        resp = self.client.get('/api/auth/me/')
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_logout_encerra_sessao(self):
        self.client.post('/api/auth/login/', {
            'email': 'ana@example.com', 'password': 'senha-forte-123',
        })
        resp = self.client.post('/api/auth/logout/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, status.HTTP_403_FORBIDDEN)
