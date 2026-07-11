import django_filters
from django.db.models import RestrictedError
from rest_framework import status, viewsets
from rest_framework.response import Response

from accounts.permissions import IsAdminOrReadOnly

from .models import Developer, Game, Genre, Platform, Publisher
from .serializers import (
    DeveloperSerializer,
    GameSerializer,
    GenreSerializer,
    PlatformSerializer,
    PublisherSerializer,
)


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
