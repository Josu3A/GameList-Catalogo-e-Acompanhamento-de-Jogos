from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, Exists, F, OuterRef, Prefetch, Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from library.models import UserGame

from .models import Friendship, List, ListItem, Notification, ReviewLike
from .permissions import IsFriendshipParticipant, IsListOwnerOrReadOnly
from .serializers import (
    FriendshipSerializer,
    ListDetailSerializer,
    ListItemSerializer,
    ListSerializer,
    NotificationSerializer,
    ReviewSerializer,
    UserSearchSerializer,
)

User = get_user_model()


# --- Notificações (respeitam o CHECK de referência exatamente-uma, §4.4) -----

def _notificar_pedido(friendship):
    Notification.objects.create(
        user=friendship.friend, actor=friendship.user,
        tipo=Notification.Tipo.PEDIDO_AMIZADE, friendship=friendship,
    )


def _notificar_aceite(friendship):
    Notification.objects.create(
        user=friendship.user, actor=friendship.friend,
        tipo=Notification.Tipo.AMIZADE_ACEITA, friendship=friendship,
    )


def _notificar_curtida(review_like):
    Notification.objects.create(
        user=review_like.user_game.user, actor=review_like.user,
        tipo=Notification.Tipo.REVIEW_CURTIDA, user_game=review_like.user_game,
    )


# --- Amigos -----------------------------------------------------------------

class FriendshipViewSet(viewsets.ModelViewSet):
    """Pedidos e amizades — sempre restritos aos dois envolvidos (§3.1)."""

    serializer_class = FriendshipSerializer
    permission_classes = [IsAuthenticated, IsFriendshipParticipant]

    def get_queryset(self):
        user = self.request.user
        qs = Friendship.objects.filter(
            Q(user=user) | Q(friend=user),
        ).select_related('user', 'friend')
        estado = self.request.query_params.get('estado')
        if estado == 'amigos':
            qs = qs.filter(status=Friendship.Status.ACEITO)
        elif estado == 'recebidos':
            qs = qs.filter(status=Friendship.Status.PENDENTE, friend=user)
        elif estado == 'enviados':
            qs = qs.filter(status=Friendship.Status.PENDENTE, user=user)
        return qs.order_by('-created_at')

    def perform_create(self, serializer):
        with transaction.atomic():
            friendship = serializer.save()  # status default = pendente
            _notificar_pedido(friendship)

    @action(detail=True, methods=['post'], url_path='aceitar')
    def aceitar(self, request, pk=None):
        friendship = self.get_object()
        if friendship.friend_id != request.user.id:
            return Response(
                {'detail': 'Apenas o destinatário pode aceitar o pedido.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if friendship.status != Friendship.Status.PENDENTE:
            return Response(
                {'detail': 'Este pedido não está pendente.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            friendship.status = Friendship.Status.ACEITO
            friendship.save(update_fields=['status'])
            _notificar_aceite(friendship)
        return Response(self.get_serializer(friendship).data)

    # destroy (DELETE) = recusar/cancelar (pendente) ou desfazer (aceito).
    # Qualquer um dos dois participantes pode remover a linha.


class UserSearchView(generics.ListAPIView):
    """Busca usuários por nome para enviar pedidos de amizade (§3.1).

    Só encontra perfis públicos (perfil privado não é descoberto, como no
    ProfileView) e nunca inclui o próprio usuário. Cada resultado traz o estado
    da amizade com quem busca, para o botão escolher entre adicionar/aguardar.
    """

    serializer_class = UserSearchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        termo = (self.request.query_params.get('q') or '').strip()
        if len(termo) < 2:
            return User.objects.none()
        return (
            User.objects
            .filter(perfil_publico=True, nome__icontains=termo)
            .exclude(pk=self.request.user.pk)
            .order_by('nome')
        )


# --- Reviews + curtidas -----------------------------------------------------

class ReviewViewSet(viewsets.ReadOnlyModelViewSet):
    """Leitura de reviews (linhas de user_games com review) + curtir/descurtir.

    Respeita a visibilidade: review de perfil privado não aparece p/ terceiros.
    """

    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        user = self.request.user
        qs = (
            UserGame.objects
            .exclude(review__isnull=True).exclude(review='')
            .select_related('user', 'game')
            .annotate(likes_count=Count('likes'))
        )
        if user.is_authenticated:
            qs = qs.filter(Q(user__perfil_publico=True) | Q(user=user))
            qs = qs.annotate(liked_by_me=Exists(
                ReviewLike.objects.filter(user_game=OuterRef('pk'), user=user),
            ))
        else:
            qs = qs.filter(user__perfil_publico=True)
        game = self.request.query_params.get('game')
        if game:
            qs = qs.filter(game_id=game)
        return qs.order_by('-created_at')

    @action(detail=True, methods=['post', 'delete'], url_path='like')
    def like(self, request, pk=None):
        review = self.get_object()  # 404 se não for visível/não tiver review
        if request.method == 'POST':
            with transaction.atomic():
                like = ReviewLike.objects.filter(
                    user_game=review, user=request.user,
                ).first()
                if like is None:
                    like = ReviewLike.objects.create(
                        user_game=review, user=request.user,
                    )
                    if review.user_id != request.user.id:
                        _notificar_curtida(like)
        else:  # DELETE — idempotente
            ReviewLike.objects.filter(
                user_game=review, user=request.user,
            ).delete()
        return Response(self.get_serializer(self.get_object()).data)


# --- Listas customizadas ----------------------------------------------------

class ListViewSet(viewsets.ModelViewSet):
    """CRUD de listas (só o dono altera); leitura das públicas (§3.3)."""

    permission_classes = [IsAuthenticatedOrReadOnly, IsListOwnerOrReadOnly]

    def get_serializer_class(self):
        return ListSerializer if self.action == 'list' else ListDetailSerializer

    def get_queryset(self):
        user = self.request.user
        itens = ListItem.objects.select_related('game').order_by(
            F('ordem').asc(nulls_last=True), 'added_at',
        )
        qs = (
            List.objects
            .annotate(total_itens=Count('items'))
            .prefetch_related(Prefetch('items', queryset=itens))
            .order_by('-updated_at')
        )
        # Visibilidade base: minhas listas + listas públicas de qualquer um.
        if user.is_authenticated:
            qs = qs.filter(Q(publica=True) | Q(user=user))
        else:
            qs = qs.filter(publica=True)

        outro = self.request.query_params.get('user')
        if outro:
            return qs.filter(user_id=outro)
        if self.action == 'list':
            # Índice sem filtro = as minhas listas (inclui as privadas).
            return qs.filter(user=user) if user.is_authenticated else qs.none()
        return qs

    @action(detail=True, methods=['post'], url_path='items')
    def add_item(self, request, pk=None):
        lista = self.get_object()  # POST não é SAFE → exige o dono
        serializer = ListItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if ListItem.objects.filter(
            lista=lista, game=serializer.validated_data['game'],
        ).exists():
            return Response(
                {'detail': 'Este jogo já está na lista.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer.save(lista=lista)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['delete'], url_path=r'items/(?P<game_id>[^/.]+)')
    def remove_item(self, request, pk=None, game_id=None):
        lista = self.get_object()  # DELETE não é SAFE → exige o dono
        deleted, _ = ListItem.objects.filter(lista=lista, game_id=game_id).delete()
        if not deleted:
            return Response(
                {'detail': 'Item não encontrado na lista.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['patch'], url_path='reorder')
    def reorder(self, request, pk=None):
        lista = self.get_object()  # PATCH não é SAFE → exige o dono
        game_ids = request.data.get('game_ids')
        if not isinstance(game_ids, list):
            return Response(
                {'detail': 'Envie game_ids como uma lista de IDs de jogos.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        with transaction.atomic():
            for ordem, game_id in enumerate(game_ids):
                ListItem.objects.filter(
                    lista=lista, game_id=game_id,
                ).update(ordem=ordem)
        return Response(self.get_serializer(self.get_object()).data)


# --- Notificações -----------------------------------------------------------

class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """As próprias notificações + badge de não lidas + marcar como lida (§3.4)."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return (
            Notification.objects
            .filter(user=self.request.user)
            .select_related('actor', 'friendship', 'user_game__game')
            .order_by('-created_at')
        )

    @action(detail=False, methods=['get'], url_path='nao-lidas')
    def nao_lidas(self, request):
        count = self.get_queryset().filter(lida=False).count()
        return Response({'count': count})

    @action(detail=True, methods=['post'], url_path='marcar-lida')
    def marcar_lida(self, request, pk=None):
        notif = self.get_object()
        if not notif.lida:
            notif.lida = True
            notif.save(update_fields=['lida'])
        return Response(self.get_serializer(notif).data)

    @action(detail=False, methods=['post'], url_path='marcar-todas-lidas')
    def marcar_todas_lidas(self, request):
        atualizadas = self.get_queryset().filter(lida=False).update(lida=True)
        return Response({'atualizadas': atualizadas})
