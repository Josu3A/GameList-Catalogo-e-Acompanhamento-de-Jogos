from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from catalog.models import Game
from library.models import UserGame
from library.serializers import GameSummarySerializer

from .models import Friendship, List, ListItem, Notification

User = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    """Resumo do usuário para aparecer em amizades/notificações/reviews."""

    class Meta:
        model = User
        fields = ('id', 'nome', 'avatar_url')


# --- Amigos -----------------------------------------------------------------

class FriendshipSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    solicitante = UserSummarySerializer(source='user', read_only=True)
    friend = UserSummarySerializer(read_only=True)
    friend_id = serializers.PrimaryKeyRelatedField(
        source='friend', queryset=User.objects.all(), write_only=True,
    )

    class Meta:
        model = Friendship
        fields = (
            'id', 'user', 'solicitante', 'friend', 'friend_id',
            'status', 'created_at',
        )
        read_only_fields = ('id', 'status', 'created_at')

    def validate(self, attrs):
        user = attrs['user']
        friend = attrs['friend']
        if user == friend:
            raise serializers.ValidationError(
                'Você não pode enviar um pedido de amizade para si mesmo.',
            )
        # Leitura simétrica: bloqueia pedido duplicado e o invertido (§3.1).
        existe = Friendship.objects.filter(
            Q(user=user, friend=friend) | Q(user=friend, friend=user),
        ).exists()
        if existe:
            raise serializers.ValidationError(
                'Já existe um pedido ou amizade entre vocês.',
            )
        return attrs


# --- Reviews + curtidas -----------------------------------------------------

class ReviewSerializer(serializers.ModelSerializer):
    """Leitura de review (linha de user_games com review preenchida).

    `likes_count`/`liked_by_me` vêm de annotate na view.
    """

    user = UserSummarySerializer(read_only=True)
    game = GameSummarySerializer(read_only=True)
    likes_count = serializers.IntegerField(read_only=True)
    liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = UserGame
        fields = (
            'id', 'user', 'game', 'review', 'nota',
            'likes_count', 'liked_by_me', 'created_at',
        )

    def get_liked_by_me(self, obj):
        return bool(getattr(obj, 'liked_by_me', False))


# --- Listas customizadas ----------------------------------------------------

class ListItemSerializer(serializers.ModelSerializer):
    game = GameSummarySerializer(read_only=True)
    game_id = serializers.PrimaryKeyRelatedField(
        source='game', queryset=Game.objects.all(), write_only=True,
    )

    class Meta:
        model = ListItem
        fields = ('game', 'game_id', 'ordem', 'added_at')
        read_only_fields = ('added_at',)


class ListSerializer(serializers.ModelSerializer):
    """Resumo de uma lista (para o índice e a aba do perfil)."""

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    total_itens = serializers.SerializerMethodField()

    class Meta:
        model = List
        fields = (
            'id', 'user', 'nome', 'descricao', 'publica',
            'total_itens', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
        validators = [
            UniqueTogetherValidator(
                queryset=List.objects.all(),
                fields=('user', 'nome'),
                message='Você já tem uma lista com esse nome.',
            ),
        ]

    def get_total_itens(self, obj):
        if hasattr(obj, 'total_itens'):
            return obj.total_itens
        return obj.items.count()


class ListDetailSerializer(ListSerializer):
    """Lista com os itens (ordenados pela view)."""

    items = ListItemSerializer(many=True, read_only=True)

    class Meta(ListSerializer.Meta):
        fields = ListSerializer.Meta.fields + ('items',)


# --- Notificações -----------------------------------------------------------

class NotificationSerializer(serializers.ModelSerializer):
    actor = UserSummarySerializer(read_only=True)
    referencia = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ('id', 'tipo', 'lida', 'actor', 'referencia', 'created_at')
        read_only_fields = fields

    def get_referencia(self, obj):
        if obj.friendship_id is not None:
            return {
                'friendship_id': obj.friendship_id,
                'status': obj.friendship.status,
            }
        if obj.user_game_id is not None:
            return {
                'user_game_id': obj.user_game_id,
                'game': obj.user_game.game.titulo,
            }
        return None
