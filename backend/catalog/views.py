import django_filters
import requests
from django.core.cache import cache
from django.db.models import Case, CharField, DateField, F, RestrictedError, Value, When
from django.db.models.functions import Cast, Concat
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.permissions import IsAdminOrReadOnly

from . import rawg, steam
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
    ordering_fields = ('titulo', 'ano_lancamento', 'created_at', 'data_ordenacao')

    def get_queryset(self):
        # data_ordenacao: data_lancamento (RAWG/manual) quando tiver; senão
        # 1º de janeiro do ano_lancamento (Steam) como aproximação — mesma
        # ideia do fallback usado na página do jogo. Vira 1 coluna ordenável.
        ano_como_data = Cast(
            Concat(Cast(F('ano_lancamento'), output_field=CharField()), Value('-01-01')),
            output_field=DateField(),
        )
        qs = Game.objects.prefetch_related(
            'genres', 'platforms', 'developers', 'publishers',
        ).annotate(
            data_ordenacao=Case(
                When(data_lancamento__isnull=False, then=F('data_lancamento')),
                When(ano_lancamento__isnull=False, then=ano_como_data),
                output_field=DateField(),
            ),
        )
        user = self.request.user
        if not (user.is_authenticated and user.is_admin):
            qs = qs.filter(status_publicacao=Game.StatusPublicacao.PUBLICADO)
        return qs

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)
        # OrderingFilter já aplicou .order_by('data_ordenacao'/'-data_ordenacao')
        # como string simples, o que no Postgres deixa os NULLs (sem
        # data_lancamento NEM ano_lancamento) no topo do "Mais recentes" — bem
        # contraintuitivo. Reordena com nulls_last pras duas direções.
        ordering = self.request.query_params.get('ordering')
        if ordering == 'data_ordenacao':
            queryset = queryset.order_by(F('data_ordenacao').asc(nulls_last=True))
        elif ordering == '-data_ordenacao':
            queryset = queryset.order_by(F('data_ordenacao').desc(nulls_last=True))
        return queryset

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

        # Complementa com a data precisa da RAWG (busca exata pelo título da
        # Steam). Best-effort: sem chave, sem match ou com erro de rede, o
        # admin só não recebe data_lancamento/rawg_id pré-preenchidos — não
        # bloqueia o autofill da Steam.
        try:
            rawg_dados = rawg.buscar_por_titulo(dados['titulo'])
        except requests.RequestException:
            rawg_dados = None

        existing = Game.objects.filter(steam_appid=appid).first()
        return Response({
            'titulo': dados['titulo'],
            'sinopse': dados['sinopse'],
            'ano_lancamento': dados['ano_lancamento'],
            'data_lancamento': rawg_dados['data_lancamento'] if rawg_dados else None,
            'banner_url': dados['banner_url'],
            'capa_url': dados['capa_url'],
            'steam_appid': dados['steam_appid'],
            'rawg_id': rawg_dados['rawg_id'] if rawg_dados else None,
            'genres': _resolve_taxonomy(Genre, dados['genres']),
            'platforms': _resolve_taxonomy(Platform, dados['platforms']),
            'developers': _resolve_taxonomy(Developer, dados['developers']),
            'publishers': _resolve_taxonomy(Publisher, dados['publishers']),
            'existing_game_id': existing.id if existing else None,
        })

    @action(detail=False, methods=['get'], url_path='proximos-lancamentos')
    def proximos_lancamentos(self, request):
        """Carrossel de "Próximos Lançamentos" da Home — feed ao vivo da RAWG
        (leitura pública). Dados por RAWG.io.

        A lista da RAWG fica cacheada (~12h) pra respeitar o rate limit, mas o
        casamento com o catálogo local roda a cada request (é só um
        SELECT/UPDATE local) pra manter `game_id`/backfill sempre atuais.
        """
        try:
            proximos = cache.get_or_set(
                'rawg_proximos_lancamentos',
                rawg.buscar_proximos_lancamentos,
                60 * 60 * 12,
            )
        except requests.RequestException:
            return Response([])

        resultados = []
        for item in proximos:
            game = rawg.casar_com_catalogo(
                item['rawg_id'], item['nome'], item['data_lancamento'],
            )
            resultados.append({
                'rawg_id': item['rawg_id'],
                'nome': item['nome'],
                'data_lancamento': item['data_lancamento'],
                'capa_url': item['capa_url'],
                'plataformas': item['plataformas'],
                'game_id': game.id if game else None,
            })
        return Response(resultados)


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
