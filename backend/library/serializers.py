from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from catalog.models import Game

from .models import UserGame


class GameSummarySerializer(serializers.ModelSerializer):
    """Resumo do jogo para aparecer dentro da lista pessoal/perfil."""

    class Meta:
        model = Game
        fields = ('id', 'titulo', 'capa_url', 'ano_lancamento')


class UserGameSerializer(serializers.ModelSerializer):
    # O dono é sempre o usuário autenticado — nunca vem do payload.
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    game = GameSummarySerializer(read_only=True)
    # Só jogos publicados podem entrar na lista.
    game_id = serializers.PrimaryKeyRelatedField(
        source='game',
        queryset=Game.objects.filter(status_publicacao=Game.StatusPublicacao.PUBLICADO),
        write_only=True,
    )

    class Meta:
        model = UserGame
        fields = (
            'id', 'user', 'game', 'game_id', 'status', 'nota', 'horas_jogadas',
            'platinado', 'data_inicio', 'data_fim', 'review', 'fonte',
            'created_at', 'updated_at',
        )
        # fonte=steam_sync só será gravada pelo job de sincronização (extensão)
        read_only_fields = ('id', 'fonte', 'created_at', 'updated_at')
        validators = [
            UniqueTogetherValidator(
                queryset=UserGame.objects.all(),
                fields=('user', 'game_id'),
                message='Este jogo já está na sua lista.',
            ),
        ]


class UserGamePublicSerializer(serializers.ModelSerializer):
    """Visão somente leitura da lista de alguém (perfil público)."""

    game = GameSummarySerializer(read_only=True)

    class Meta:
        model = UserGame
        fields = (
            'id', 'game', 'status', 'nota', 'horas_jogadas', 'platinado',
            'data_inicio', 'data_fim', 'review',
        )
