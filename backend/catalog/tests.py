"""Critérios de aceitação do catálogo (CONTEXTO_PROJETO §4):
só admin faz CRUD em games; usuário comum tem leitura (apenas publicados)."""
from datetime import date
from io import StringIO
from unittest.mock import Mock, patch

import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase

from library.models import UserGame

from . import rawg
from .models import Developer, Game, Genre, Platform, Publisher

User = get_user_model()

FAKE_APPDETAILS = {
    'titulo': 'Hades',
    'sinopse': 'Rogue-like da Supergiant.',
    'ano_lancamento': 2020,
    'banner_url': 'https://cdn/header.jpg',
    'capa_url': 'https://cdn/capsule.jpg',
    'steam_appid': 1145360,
    'genres': ['Ação', 'RPG'],
    'platforms': ['Windows', 'macOS'],
    'developers': ['Supergiant Games'],
    'publishers': ['Supergiant Games'],
}


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


class OrdenacaoPorDataTests(APITestCase):
    """Ordenação por data_ordenacao: usa data_lancamento (RAWG/manual) quando
    tiver; senão cai pro 1º de janeiro do ano_lancamento (Steam)."""

    @classmethod
    def setUpTestData(cls):
        # Só data_lancamento (mais recente de todos).
        cls.com_data = Game.objects.create(
            titulo='Com Data', status_publicacao=Game.StatusPublicacao.PUBLICADO,
            ano_lancamento=2010, data_lancamento=date(2024, 6, 1),
        )
        # Só ano_lancamento — cai pro 1º de janeiro (2015-01-01).
        cls.so_ano = Game.objects.create(
            titulo='Só Ano', status_publicacao=Game.StatusPublicacao.PUBLICADO,
            ano_lancamento=2015,
        )
        # Nenhum dos dois.
        cls.sem_nenhum = Game.objects.create(
            titulo='Sem Nenhum', status_publicacao=Game.StatusPublicacao.PUBLICADO,
        )

    def test_mais_recentes_usa_data_lancamento_com_fallback_pro_ano(self):
        resp = self.client.get('/api/games/', {'ordering': '-data_ordenacao'})
        titulos = [g['titulo'] for g in resp.data['results']]
        # com_data (2024) antes de so_ano (2015-01-01); sem_nenhum (NULL) por
        # último nas duas direções — nunca aparenta ser "mais recente".
        self.assertEqual(titulos, ['Com Data', 'Só Ano', 'Sem Nenhum'])

    def test_mais_antigos_ordena_em_data_ordenacao_crescente_com_nulls_last(self):
        resp = self.client.get('/api/games/', {'ordering': 'data_ordenacao'})
        titulos = [g['titulo'] for g in resp.data['results']]
        self.assertEqual(titulos, ['Só Ano', 'Com Data', 'Sem Nenhum'])


class SteamPreviewTests(APITestCase):
    """Autofill do catálogo pela Storefront (só admin)."""

    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@example.com', nome='Admin', password='senha-forte-123',
        )
        self.comum = User.objects.create_user(
            email='comum@example.com', nome='Comum', password='senha-forte-123',
        )

    @patch('catalog.views.rawg.buscar_por_titulo', return_value=None)
    @patch('catalog.views.steam.fetch_appdetails', return_value=FAKE_APPDETAILS)
    def test_admin_recebe_campos_e_resolve_taxonomias(self, _fetch, _rawg):
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/games/steam-preview/', {'appid': 1145360})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['titulo'], 'Hades')
        self.assertEqual(resp.data['steam_appid'], 1145360)
        # get_or_create criou as taxonomias e devolveu IDs reais.
        self.assertTrue(Genre.objects.filter(nome='RPG').exists())
        self.assertTrue(Developer.objects.filter(nome='Supergiant Games').exists())
        self.assertTrue(Platform.objects.filter(nome='Windows').exists())
        self.assertTrue(Publisher.objects.filter(nome='Supergiant Games').exists())
        self.assertEqual({g['nome'] for g in resp.data['genres']}, {'Ação', 'RPG'})
        self.assertTrue(all('id' in g for g in resp.data['genres']))
        self.assertIsNone(resp.data['existing_game_id'])

    @patch('catalog.views.rawg.buscar_por_titulo', return_value=None)
    @patch('catalog.views.steam.fetch_appdetails', return_value=FAKE_APPDETAILS)
    def test_avisa_quando_jogo_ja_existe(self, _fetch, _rawg):
        jogo = Game.objects.create(titulo='Hades', steam_appid=1145360)
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/games/steam-preview/', {'appid': 1145360})
        self.assertEqual(resp.data['existing_game_id'], jogo.id)

    @patch('catalog.views.rawg.buscar_por_titulo')
    @patch('catalog.views.steam.fetch_appdetails', return_value=FAKE_APPDETAILS)
    def test_preview_inclui_data_lancamento_da_rawg_quando_casa(self, _fetch, mock_rawg):
        mock_rawg.return_value = {
            'rawg_id': 999,
            'nome': 'Hades',
            'data_lancamento': date(2020, 9, 17),
            'capa_url': 'https://img/hades.jpg',
            'plataformas': ['PC'],
        }
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/games/steam-preview/', {'appid': 1145360})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['data_lancamento'], date(2020, 9, 17))
        self.assertEqual(resp.data['rawg_id'], 999)
        mock_rawg.assert_called_once_with('Hades')

    @patch('catalog.views.rawg.buscar_por_titulo', side_effect=requests.RequestException('falhou'))
    @patch('catalog.views.steam.fetch_appdetails', return_value=FAKE_APPDETAILS)
    def test_preview_degrada_quando_rawg_falha(self, _fetch, _rawg):
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/games/steam-preview/', {'appid': 1145360})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIsNone(resp.data['data_lancamento'])
        self.assertIsNone(resp.data['rawg_id'])

    @patch('catalog.views.steam.fetch_appdetails', return_value=None)
    def test_appid_inexistente_404(self, _fetch):
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/games/steam-preview/', {'appid': 999999999})
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_appid_invalido_400(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.post('/api/games/steam-preview/', {'appid': 'abc'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_comum_nao_pode_importar(self):
        self.client.force_authenticate(self.comum)
        resp = self.client.post('/api/games/steam-preview/', {'appid': 1145360})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)


FAKE_RAWG_PAYLOAD = {
    'results': [
        {
            'id': 111,
            'name': 'Later Game',
            'released': '2026-12-01',
            'tba': False,
            'background_image': 'https://img/later.jpg',
            'platforms': [{'platform': {'name': 'PC'}}],
        },
        {
            'id': 222,
            'name': 'Sooner Game',
            'released': '2026-08-01',
            'tba': False,
            'background_image': 'https://img/sooner.jpg',
            'platforms': [{'platform': {'name': 'PS5'}}],
        },
        {
            'id': 333,
            'name': 'Anunciado sem data',
            'released': None,
            'tba': True,
            'background_image': None,
            'platforms': [],
        },
        {
            'id': 444,
            'name': 'Sem data ainda',
            'released': None,
            'tba': False,
            'background_image': None,
            'platforms': [],
        },
    ],
}


def _mock_rawg_response(payload):
    return Mock(json=lambda: payload, raise_for_status=lambda: None)


class RawgClientTests(TestCase):
    """Normalização do cliente RAWG (catalog/rawg.py), isolada da view."""

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_normaliza_ordena_por_data_e_filtra_tba_e_sem_data(self, mock_get):
        mock_get.return_value = _mock_rawg_response(FAKE_RAWG_PAYLOAD)
        resultados = rawg.buscar_proximos_lancamentos()

        self.assertEqual([r['nome'] for r in resultados], ['Sooner Game', 'Later Game'])
        self.assertEqual(resultados[0]['rawg_id'], 222)
        self.assertEqual(resultados[0]['data_lancamento'], date(2026, 8, 1))
        self.assertEqual(resultados[0]['capa_url'], 'https://img/sooner.jpg')
        self.assertEqual(resultados[0]['plataformas'], ['PS5'])

    @override_settings(RAWG_API_KEY='')
    def test_sem_chave_nao_chama_a_rawg(self):
        self.assertEqual(rawg.buscar_proximos_lancamentos(), [])

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_buscar_por_titulo_acha_o_resultado_com_nome_exato(self, mock_get):
        mock_get.return_value = _mock_rawg_response({'results': [FAKE_RAWG_PAYLOAD['results'][1]]})
        resultado = rawg.buscar_por_titulo('Sooner Game')

        self.assertEqual(resultado['rawg_id'], 222)
        self.assertEqual(resultado['data_lancamento'], date(2026, 8, 1))
        params = mock_get.call_args.kwargs['params']
        self.assertEqual(params['search'], 'Sooner Game')
        self.assertNotIn('search_exact', params)

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_buscar_por_titulo_ignora_resultados_parecidos_mas_nao_exatos(self, mock_get):
        # Regressão: a RAWG devolve correspondências soltas mesmo com
        # search_exact=true (ex.: buscar "Rust" trazia "Rusted Will" como
        # primeiro resultado) — por isso o filtro de igualdade é nosso, não
        # da API. Nenhum destes bate exatamente com "Rust".
        mock_get.return_value = _mock_rawg_response({
            'results': [
                {'id': 1, 'name': 'Rusted Will', 'released': '2020-01-01', 'tba': False,
                 'background_image': None, 'platforms': []},
                {'id': 2, 'name': 'Rust Belt', 'released': '2019-01-01', 'tba': False,
                 'background_image': None, 'platforms': []},
            ],
        })
        self.assertIsNone(rawg.buscar_por_titulo('Rust'))

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_buscar_por_titulo_acha_match_exato_que_nao_e_o_primeiro(self, mock_get):
        mock_get.return_value = _mock_rawg_response({
            'results': [
                {'id': 1, 'name': 'Rusted Will', 'released': '2020-01-01', 'tba': False,
                 'background_image': None, 'platforms': []},
                {'id': 2, 'name': 'Rust', 'released': '2013-12-11', 'tba': False,
                 'background_image': 'https://img/rust.jpg', 'platforms': []},
            ],
        })
        resultado = rawg.buscar_por_titulo('Rust')
        self.assertEqual(resultado['rawg_id'], 2)

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_buscar_por_titulo_sem_resultado_retorna_none(self, mock_get):
        mock_get.return_value = _mock_rawg_response({'results': []})
        self.assertIsNone(rawg.buscar_por_titulo('Jogo Inexistente'))

    @override_settings(RAWG_API_KEY='')
    def test_buscar_por_titulo_sem_chave_retorna_none(self):
        self.assertIsNone(rawg.buscar_por_titulo('Qualquer'))


class SyncRawgDatesCommandTests(TestCase):
    """Backfill em lote pros jogos já cadastrados (management command)."""

    def setUp(self):
        self.jogo = Game.objects.create(
            titulo='Sooner Game', status_publicacao=Game.StatusPublicacao.PUBLICADO,
        )

    def _run(self, *args):
        out = StringIO()
        call_command('sync_rawg_dates', *args, stdout=out, stderr=out)
        return out.getvalue()

    @override_settings(RAWG_API_KEY='')
    def test_sem_chave_aborta_com_erro(self):
        with self.assertRaises(CommandError):
            self._run()

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_faz_backfill_dos_jogos_incompletos(self, mock_get):
        mock_get.return_value = _mock_rawg_response(
            {'results': [FAKE_RAWG_PAYLOAD['results'][1]]},
        )
        self._run()

        self.jogo.refresh_from_db()
        self.assertEqual(self.jogo.rawg_id, 222)
        self.assertEqual(self.jogo.data_lancamento, date(2026, 8, 1))

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_dry_run_nao_grava(self, mock_get):
        mock_get.return_value = _mock_rawg_response(
            {'results': [FAKE_RAWG_PAYLOAD['results'][1]]},
        )
        self._run('--dry-run')

        self.jogo.refresh_from_db()
        self.assertIsNone(self.jogo.rawg_id)
        self.assertIsNone(self.jogo.data_lancamento)

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_nao_sobrescreve_data_ja_preenchida_manualmente(self, mock_get):
        data_manual = date(2026, 1, 1)
        self.jogo.data_lancamento = data_manual
        self.jogo.save(update_fields=['data_lancamento'])
        mock_get.return_value = _mock_rawg_response(
            {'results': [FAKE_RAWG_PAYLOAD['results'][1]]},
        )
        self._run()

        self.jogo.refresh_from_db()
        self.assertEqual(self.jogo.data_lancamento, data_manual)
        self.assertEqual(self.jogo.rawg_id, 222)

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_jogo_ja_completo_nao_e_processado(self, mock_get):
        self.jogo.rawg_id = 1
        self.jogo.data_lancamento = date(2020, 1, 1)
        self.jogo.save(update_fields=['rawg_id', 'data_lancamento'])

        self._run()

        mock_get.assert_not_called()

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get', side_effect=requests.RequestException('falhou'))
    def test_erro_de_rede_nao_derruba_o_comando(self, _mock_get):
        saida = self._run()
        self.assertIn('erro de rede', saida)
        self.jogo.refresh_from_db()
        self.assertIsNone(self.jogo.rawg_id)


class ProximosLancamentosEndpointTests(APITestCase):
    """GET /api/games/proximos-lancamentos/: leitura pública, feed cacheado
    da RAWG, casado (e opcionalmente enriquecido por backfill) com o
    catálogo local a cada request."""

    def setUp(self):
        cache.clear()

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_casa_por_titulo_e_faz_backfill(self, mock_get):
        mock_get.return_value = _mock_rawg_response(FAKE_RAWG_PAYLOAD)
        jogo = Game.objects.create(
            titulo='Sooner Game', status_publicacao=Game.StatusPublicacao.PUBLICADO,
        )

        resp = self.client.get('/api/games/proximos-lancamentos/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual([i['nome'] for i in resp.data], ['Sooner Game', 'Later Game'])

        item = next(i for i in resp.data if i['rawg_id'] == 222)
        self.assertEqual(item['game_id'], jogo.id)

        jogo.refresh_from_db()
        self.assertEqual(jogo.rawg_id, 222)
        self.assertEqual(jogo.data_lancamento, date(2026, 8, 1))

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_nao_casado_nao_tem_game_id(self, mock_get):
        mock_get.return_value = _mock_rawg_response(FAKE_RAWG_PAYLOAD)
        resp = self.client.get('/api/games/proximos-lancamentos/')
        item = next(i for i in resp.data if i['rawg_id'] == 111)
        self.assertIsNone(item['game_id'])

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get')
    def test_backfill_nao_sobrescreve_data_ja_preenchida_manualmente(self, mock_get):
        mock_get.return_value = _mock_rawg_response(FAKE_RAWG_PAYLOAD)
        data_manual = date(2026, 1, 1)
        jogo = Game.objects.create(
            titulo='Sooner Game',
            status_publicacao=Game.StatusPublicacao.PUBLICADO,
            data_lancamento=data_manual,
        )

        resp = self.client.get('/api/games/proximos-lancamentos/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

        jogo.refresh_from_db()
        # data preenchida manualmente é preservada...
        self.assertEqual(jogo.data_lancamento, data_manual)
        # ...mas o rawg_id (que estava vazio) ainda é preenchido.
        self.assertEqual(jogo.rawg_id, 222)

    @override_settings(RAWG_API_KEY='')
    def test_sem_chave_retorna_lista_vazia_sem_erro(self):
        resp = self.client.get('/api/games/proximos-lancamentos/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])

    @override_settings(RAWG_API_KEY='chave-de-teste')
    @patch('catalog.rawg.requests.get', side_effect=requests.RequestException('falhou'))
    def test_erro_de_rede_degrada_para_lista_vazia(self, _mock_get):
        resp = self.client.get('/api/games/proximos-lancamentos/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data, [])
