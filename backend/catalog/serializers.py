from rest_framework import serializers

from .models import Developer, Game, Genre, Platform, Publisher


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('id', 'nome')


class PlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = Platform
        fields = ('id', 'nome')


class DeveloperSerializer(serializers.ModelSerializer):
    class Meta:
        model = Developer
        fields = ('id', 'nome')


class PublisherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Publisher
        fields = ('id', 'nome')


class GameSerializer(serializers.ModelSerializer):
    # Capas derivadas do appid (vertical/fundo) — só leitura; a edição continua
    # usando capa_url/banner_url brutos.
    capa_vertical_url = serializers.ReadOnlyField()
    banner_hero_url = serializers.ReadOnlyField()
    # Leitura aninhada (nomes) + escrita por lista de IDs (*_ids).
    genres = GenreSerializer(many=True, read_only=True)
    platforms = PlatformSerializer(many=True, read_only=True)
    developers = DeveloperSerializer(many=True, read_only=True)
    publishers = PublisherSerializer(many=True, read_only=True)

    genre_ids = serializers.PrimaryKeyRelatedField(
        source='genres', queryset=Genre.objects.all(),
        many=True, write_only=True, required=False,
    )
    platform_ids = serializers.PrimaryKeyRelatedField(
        source='platforms', queryset=Platform.objects.all(),
        many=True, write_only=True, required=False,
    )
    developer_ids = serializers.PrimaryKeyRelatedField(
        source='developers', queryset=Developer.objects.all(),
        many=True, write_only=True, required=False,
    )
    publisher_ids = serializers.PrimaryKeyRelatedField(
        source='publishers', queryset=Publisher.objects.all(),
        many=True, write_only=True, required=False,
    )

    class Meta:
        model = Game
        fields = (
            'id', 'titulo', 'capa_url', 'banner_url',
            'capa_vertical_url', 'banner_hero_url', 'ano_lancamento', 'sinopse',
            'status_publicacao', 'steam_appid',
            'genres', 'platforms', 'developers', 'publishers',
            'genre_ids', 'platform_ids', 'developer_ids', 'publisher_ids',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
