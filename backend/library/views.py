from datetime import datetime, timezone as dt_timezone

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.models import Achievement, Game
from social.models import Friendship, List
from social.serializers import ListSerializer

from . import steam
from .models import UserAchievement, UserGame
from .serializers import UserGamePublicSerializer, UserGameSerializer

User = get_user_model()


class UserGameViewSet(viewsets.ModelViewSet):
    """CRUD da lista pessoal — sempre restrito ao próprio usuário
    (CONTEXTO_PROJETO §4: ninguém edita a lista de outro)."""

    serializer_class = UserGameSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ('status', 'platinado')
    ordering_fields = ('updated_at', 'nota', 'horas_jogadas')

    def get_queryset(self):
        return UserGame.objects.filter(user=self.request.user).select_related('game')

    # --- Integração Steam ---------------------------------------------------
    # A Web API tem rate limit (CONTEXTO §6.4): a biblioteca é 1 chamada; as
    # conquistas são por jogo, sob demanda. Casamento sempre por steam_appid.

    def _guard_steam(self, request):
        """Valida pré-condições comuns; devolve um Response de erro ou None."""
        if not request.user.steam_id:
            return Response(
                {'detail': 'Vincule sua conta Steam antes de sincronizar.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not settings.STEAM_API_KEY:
            return Response(
                {'detail': 'Steam Web API Key não configurada no servidor.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return None

    @action(detail=False, methods=['post'], url_path='steam-sync')
    def steam_sync(self, request):
        """Importa os jogos possuídos + horas para a lista pessoal (steam_sync)."""
        erro = self._guard_steam(request)
        if erro:
            return erro
        try:
            owned = steam.get_owned_games(request.user.steam_id)
        except requests.RequestException:
            return Response(
                {'detail': 'Não foi possível consultar a Steam. Tente novamente.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # Casa cada appid possuído com um jogo publicado do catálogo.
        catalogo = {
            g.steam_appid: g
            for g in Game.objects.filter(
                steam_appid__in=[o['appid'] for o in owned],
                status_publicacao=Game.StatusPublicacao.PUBLICADO,
            )
        }
        criados = atualizados = ignorados = 0
        with transaction.atomic():
            for item in owned:
                game = catalogo.get(item['appid'])
                if game is None:
                    ignorados += 1
                    continue
                horas = round(item.get('playtime_forever', 0) / 60, 1)
                ug, created = UserGame.objects.get_or_create(
                    user=request.user, game=game,
                    defaults={
                        'status': (UserGame.Status.JOGANDO if horas > 0
                                   else UserGame.Status.QUERO_JOGAR),
                        'fonte': UserGame.Fonte.STEAM_SYNC,
                        'horas_jogadas': horas,
                    },
                )
                if created:
                    criados += 1
                elif ug.fonte == UserGame.Fonte.STEAM_SYNC:
                    # Não sobrescreve horas de entradas manuais.
                    ug.horas_jogadas = horas
                    ug.save(update_fields=['horas_jogadas', 'updated_at'])
                    atualizados += 1
        return Response({
            'criados': criados,
            'atualizados': atualizados,
            'ignorados_sem_catalogo': ignorados,
        })

    @action(detail=False, methods=['post'], url_path='steam-achievements')
    def steam_achievements(self, request):
        """Sincroniza as conquistas de um jogo da lista; sugere platinado a 100%."""
        erro = self._guard_steam(request)
        if erro:
            return erro
        try:
            game_id = int(request.data.get('game_id'))
        except (TypeError, ValueError):
            return Response({'detail': 'Informe o game_id.'},
                            status=status.HTTP_400_BAD_REQUEST)

        ug = (UserGame.objects.filter(user=request.user, game_id=game_id)
              .select_related('game').first())
        if ug is None:
            return Response({'detail': 'Este jogo não está na sua lista.'},
                            status=status.HTTP_404_NOT_FOUND)
        if not ug.game.steam_appid:
            return Response({'detail': 'Este jogo não tem Steam AppID.'},
                            status=status.HTTP_400_BAD_REQUEST)

        appid = ug.game.steam_appid
        try:
            schema = steam.get_schema_for_game(appid)
            player = steam.get_player_achievements(request.user.steam_id, appid)
        except requests.RequestException:
            return Response(
                {'detail': 'Não foi possível consultar a Steam. Tente novamente.'},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        with transaction.atomic():
            por_apiname = {}
            for a in schema:
                ach, _ = Achievement.objects.update_or_create(
                    game=ug.game, steam_apiname=a['steam_apiname'],
                    defaults={
                        'nome': a['nome'],
                        'descricao': a['descricao'],
                        'icon_url': a['icon_url'],
                    },
                )
                por_apiname[a['steam_apiname']] = ach

            desbloqueadas = 0
            for pa in player:
                if not pa['achieved']:
                    continue
                ach = por_apiname.get(pa['apiname'])
                if ach is None:
                    continue
                desbloqueada_em = (
                    datetime.fromtimestamp(pa['unlocktime'], tz=dt_timezone.utc)
                    if pa['unlocktime'] else None
                )
                UserAchievement.objects.update_or_create(
                    user=request.user, achievement=ach,
                    defaults={'desbloqueada_em': desbloqueada_em},
                )
                desbloqueadas += 1

            total = len(por_apiname)
            percent = round(desbloqueadas / total * 100) if total else 0
            platinado = total > 0 and desbloqueadas == total
            if platinado and not ug.platinado:
                ug.platinado = True
                ug.save(update_fields=['platinado', 'updated_at'])

        return Response({
            'total': total,
            'desbloqueadas': desbloqueadas,
            'percent': percent,
            'platinado': ug.platinado,
        })


class ProfileView(APIView):
    """Perfil público: dados do usuário, lista de jogos e platinas em destaque."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        if not user.perfil_publico and request.user != user:
            # Perfil privado não revela nem a própria existência
            raise Http404
        jogos = UserGame.objects.filter(user=user).select_related('game')
        listas_publicas = (
            List.objects.filter(user=user, publica=True)
            .annotate(total_itens=Count('items'))
            .order_by('-updated_at')
        )
        return Response({
            'id': user.id,
            'nome': user.nome,
            'bio': user.bio,
            # avatar_url é um ImageField: devolve a URL de mídia absoluta (ou None).
            'avatar_url': (
                request.build_absolute_uri(user.avatar_url.url)
                if user.avatar_url else None
            ),
            # Estado da amizade em relação a quem visita (alimenta o botão do perfil).
            'amizade': Friendship.estado_entre(request.user, user),
            'platinas': UserGamePublicSerializer(
                jogos.filter(platinado=True), many=True,
            ).data,
            'jogos': UserGamePublicSerializer(jogos, many=True).data,
            'listas_publicas': ListSerializer(listas_publicas, many=True).data,
        })
