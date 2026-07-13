import django_filters
import requests
from django.db.models import RestrictedError
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminOrReadOnly

from . import steam
from .models import Developer, Game, Genre, Platform, Publisher
from .serializers import (
    DeveloperSerializer,
    GameSerializer,
    GenreSerializer,
    PlatformSerializer,
    PublisherSerializer,
)


def _resolve_taxonomy(model, nomes):
    """get_or_create de cada nome; devolve [{'id', 'nome'}] (padrão do seed_demo)."""
    resolved = []
    for nome in nomes:
        obj, _ = model.objects.get_or_create(nome=nome)
        resolved.append({'id': obj.id, 'nome': obj.nome})
    return resolved


class GameFilter(django_filters.FilterSet):
    genero = django_filters.NumberFilter(field_name='genres__id')
    plataforma = django_filters.NumberFilter(field_name='platforms__id')
    desenvolvedora = django_filters.NumberFilter(field_name='developers__id')
    ano = django_filters.NumberFilter(field_name='ano_lancamento')

    class Meta:
        model = Game
        fields = ('genero', 'plataforma', 'desenvolvedora', 'ano', 'status_publicacao')


class GameViewSet(viewsets.ModelViewSet):
    """Catálogo de jogos: leitura pública (só publicados para não-admin);
    escrita restrita a administradores (CONTEXTO_PROJETO §4)."""

    serializer_class = GameSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = GameFilter
    search_fields = ('titulo',)
    ordering_fields = ('titulo', 'ano_lancamento', 'created_at')

    def get_queryset(self):
        qs = Game.objects.prefetch_related(
            'genres', 'platforms', 'developers', 'publishers',
        )
        user = self.request.user
        if not (user.is_authenticated and user.is_admin):
            qs = qs.filter(status_publicacao=Game.StatusPublicacao.PUBLICADO)
        return qs

    def destroy(self, request, *args, **kwargs):
        try:
            return super().destroy(request, *args, **kwargs)
        except RestrictedError:
            # user_games.game_id é ON DELETE RESTRICT (preserva histórico)
            return Response(
                {'detail': 'Este jogo está na lista de usuários e não pode ser removido.'},
                status=status.HTTP_409_CONFLICT,
            )

    @action(detail=False, methods=['post'], url_path='steam-preview')
    def steam_preview(self, request):
        """Autopreenche os campos de um jogo pela Storefront da Steam (só admin).

        POST {appid}: busca na loja, resolve as taxonomias (get_or_create) e
        devolve os campos + taxonomias como [{id, nome}] para prefill do form.
        Não cria o Game — o admin revisa e salva pelo fluxo normal. Se já houver
        jogo com aquele steam_appid, devolve `existing_game_id`.
        """
        try:
            appid = int(request.data.get('appid'))
            if appid <= 0:
                raise ValueError
        except (TypeError, ValueError):
            return Response(
                {'detail': 'Informe um Steam AppID válido.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            dados = steam.fetch_appdetails(appid)
        except requests.RequestException:
            return Response(
                {'detail': 'Não foi possível consultar a Steam. Tente novamente.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )
        if dados is None:
            return Response(
                {'detail': f'Nenhum app encontrado na Steam para o AppID {appid}.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        existing = Game.objects.filter(steam_appid=appid).first()
        return Response({
            'titulo': dados['titulo'],
            'sinopse': dados['sinopse'],
            'ano_lancamento': dados['ano_lancamento'],
            'banner_url': dados['banner_url'],
            'capa_url': dados['capa_url'],
            'steam_appid': dados['steam_appid'],
            'genres': _resolve_taxonomy(Genre, dados['genres']),
            'platforms': _resolve_taxonomy(Platform, dados['platforms']),
            'developers': _resolve_taxonomy(Developer, dados['developers']),
            'publishers': _resolve_taxonomy(Publisher, dados['publishers']),
            'existing_game_id': existing.id if existing else None,
        })


class GenreViewSet(viewsets.ModelViewSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ('nome',)


class PlatformViewSet(viewsets.ModelViewSet):
    queryset = Platform.objects.all()
    serializer_class = PlatformSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ('nome',)


class DeveloperViewSet(viewsets.ModelViewSet):
    queryset = Developer.objects.all()
    serializer_class = DeveloperSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ('nome',)


class PublisherViewSet(viewsets.ModelViewSet):
    queryset = Publisher.objects.all()
    serializer_class = PublisherSerializer
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ('nome',)
