"""Critérios de aceitação de autenticação (CONTEXTO_PROJETO §4):
login inválido é rejeitado; áreas restritas exigem autenticação."""
import io
import os
import shutil
import tempfile
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


def _png(size=(8, 8)):
    """Gera um PNG válido pequeno em memória para os testes de upload."""
    buf = io.BytesIO()
    Image.new('RGB', size, (90, 140, 200)).save(buf, format='PNG')
    return buf.getvalue()

STEAM_ID = '76561198000000001'
OTHER_STEAM_ID = '76561198000000002'


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

    def test_patch_me_edita_o_proprio_perfil(self):
        self.client.force_authenticate(self.user)
        resp = self.client.patch('/api/auth/me/', {
            'nome': 'Ana Editada',
            'bio': 'Curto RPGs.',
            'perfil_publico': False,
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nome, 'Ana Editada')
        self.assertEqual(self.user.bio, 'Curto RPGs.')
        self.assertFalse(self.user.perfil_publico)

    def test_patch_me_nao_altera_tipo_usuario(self):
        self.client.force_authenticate(self.user)
        resp = self.client.patch('/api/auth/me/', {'tipo_usuario': 'admin'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.tipo_usuario, User.TipoUsuario.COMUM)

    def test_patch_me_exige_autenticacao(self):
        resp = self.client.patch('/api/auth/me/', {'nome': 'X'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


_MEDIA_TMP = tempfile.mkdtemp(prefix='gamelist-avatars-test-')


@override_settings(MEDIA_ROOT=_MEDIA_TMP)
class AvatarUploadTests(APITestCase):
    """Avatar por upload (não URL): arquivo salvo em mídia, com limites de tamanho/tipo."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
        )
        self.client.force_authenticate(self.user)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(_MEDIA_TMP, ignore_errors=True)
        super().tearDownClass()

    def test_upload_valido_salva_arquivo_e_devolve_url_de_midia(self):
        img = SimpleUploadedFile('foto.png', _png(), content_type='image/png')
        resp = self.client.patch('/api/auth/me/', {'avatar_url': img}, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # A resposta traz uma URL de mídia (não o caminho no banco).
        self.assertIn('/media/avatars/', resp.data['avatar_url'])
        self.user.refresh_from_db()
        # No banco fica só o caminho relativo do arquivo.
        self.assertTrue(self.user.avatar_url.name.startswith('avatars/'))
        self.assertTrue(os.path.exists(self.user.avatar_url.path))

    def test_upload_de_nao_imagem_e_rejeitado(self):
        arq = SimpleUploadedFile('a.txt', b'isto nao e imagem', content_type='text/plain')
        resp = self.client.patch('/api/auth/me/', {'avatar_url': arq}, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('avatar_url', resp.data)

    def test_upload_acima_do_limite_e_rejeitado(self):
        # PNG de ruído ~3 MB (> 2 MB): passa na checagem de imagem e falha no tamanho.
        buf = io.BytesIO()
        Image.frombytes('RGB', (1000, 1000), os.urandom(1000 * 1000 * 3)).save(buf, format='PNG')
        grande = SimpleUploadedFile('grande.png', buf.getvalue(), content_type='image/png')
        resp = self.client.patch('/api/auth/me/', {'avatar_url': grande}, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_enviar_null_limpa_o_avatar(self):
        img = SimpleUploadedFile('foto.png', _png(), content_type='image/png')
        self.client.patch('/api/auth/me/', {'avatar_url': img}, format='multipart')
        resp = self.client.patch('/api/auth/me/', {'avatar_url': None}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data['avatar_url'])
        self.user.refresh_from_db()
        self.assertFalse(self.user.avatar_url)


class SteamAuthTests(APITestCase):
    """Login por Steam (OpenID) só VINCULA/loga — nunca cria conta."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='ana@example.com', nome='Ana', password='senha-forte-123',
        )

    @patch('accounts.views.steam.get_player_summary', return_value=None)
    @patch('accounts.views.steam.verify_response', return_value=STEAM_ID)
    def test_callback_logado_vincula_steam(self, _verify, _summary):
        self.client.force_login(self.user)
        resp = self.client.get('/api/auth/steam/callback/')
        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertIn('steam=linked', resp['Location'])
        self.user.refresh_from_db()
        self.assertEqual(self.user.steam_id, STEAM_ID)

    @patch('accounts.views.steam.verify_response', return_value=STEAM_ID)
    def test_callback_bloqueia_steam_de_outra_conta(self, _verify):
        User.objects.create_user(
            email='dono@example.com', nome='Dono', password='x', steam_id=STEAM_ID,
        )
        self.client.force_login(self.user)
        resp = self.client.get('/api/auth/steam/callback/')
        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertIn('steam=taken', resp['Location'])
        self.user.refresh_from_db()
        self.assertIsNone(self.user.steam_id)

    @patch('accounts.views.steam.verify_response', return_value=STEAM_ID)
    def test_callback_anonimo_loga_conta_vinculada(self, _verify):
        self.user.steam_id = STEAM_ID
        self.user.save(update_fields=['steam_id'])
        resp = self.client.get('/api/auth/steam/callback/')
        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertIn('steam=login', resp['Location'])
        # Sessão criada: /me passa a responder.
        me = self.client.get('/api/auth/me/')
        self.assertEqual(me.status_code, status.HTTP_200_OK)
        self.assertEqual(me.data['email'], 'ana@example.com')

    @patch('accounts.views.steam.verify_response', return_value=OTHER_STEAM_ID)
    def test_callback_anonimo_steam_desconhecida_nao_cria_conta(self, _verify):
        resp = self.client.get('/api/auth/steam/callback/')
        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertIn('steam=nolink', resp['Location'])
        self.assertFalse(User.objects.filter(steam_id=OTHER_STEAM_ID).exists())
        self.assertEqual(User.objects.count(), 1)

    @patch('accounts.views.steam.verify_response', return_value=None)
    def test_callback_resposta_invalida(self, _verify):
        resp = self.client.get('/api/auth/steam/callback/')
        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertIn('steam=error', resp['Location'])

    def test_disconnect_remove_steam_id(self):
        self.user.steam_id = STEAM_ID
        self.user.save(update_fields=['steam_id'])
        self.client.force_authenticate(self.user)
        resp = self.client.post('/api/auth/steam/disconnect/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.steam_id)

    def test_login_steam_redireciona_para_provedor(self):
        resp = self.client.get('/api/auth/steam/login/')
        self.assertEqual(resp.status_code, status.HTTP_302_FOUND)
        self.assertIn('steamcommunity.com/openid/login', resp['Location'])
