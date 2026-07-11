"""Catálogo central de jogos (ESQUEMA_DADOS §1.2, §2 e §3.1)."""
from django.db import models


class Genre(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'genres'
        ordering = ['nome']
        verbose_name = 'gênero'

    def __str__(self):
        return self.nome


class Platform(models.Model):
    nome = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'platforms'
        ordering = ['nome']
        verbose_name = 'plataforma'

    def __str__(self):
        return self.nome


class Developer(models.Model):
    nome = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = 'developers'
        ordering = ['nome']
        verbose_name = 'desenvolvedora'

    def __str__(self):
        return self.nome


class Publisher(models.Model):
    nome = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = 'publishers'
        ordering = ['nome']
        verbose_name = 'publicadora'

    def __str__(self):
        return self.nome


class Game(models.Model):
    class StatusPublicacao(models.TextChoices):
        RASCUNHO = 'rascunho', 'Rascunho'
        PUBLICADO = 'publicado', 'Publicado'

    titulo = models.CharField(max_length=200)
    capa_url = models.URLField(max_length=500, blank=True, null=True)
    banner_url = models.URLField(max_length=500, blank=True, null=True)
    ano_lancamento = models.IntegerField(blank=True, null=True)
    sinopse = models.TextField(blank=True, null=True)
    status_publicacao = models.CharField(
        max_length=20,
        choices=StatusPublicacao.choices,
        default=StatusPublicacao.RASCUNHO,
    )
    steam_appid = models.IntegerField(unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Junções N:N do catálogo (game_genres etc.). O Django cria as tabelas com
    # coluna id própria + UNIQUE(game_id, X_id), em vez de PK composta — a
    # divergência com db/schema.sql está registrada no LOG.md.
    genres = models.ManyToManyField(
        Genre, db_table='game_genres', related_name='games', blank=True,
    )
    platforms = models.ManyToManyField(
        Platform, db_table='game_platforms', related_name='games', blank=True,
    )
    developers = models.ManyToManyField(
        Developer, db_table='game_developers', related_name='games', blank=True,
    )
    publishers = models.ManyToManyField(
        Publisher, db_table='game_publishers', related_name='games', blank=True,
    )

    class Meta:
        db_table = 'games'
        ordering = ['titulo']
        verbose_name = 'jogo'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(status_publicacao__in=('rascunho', 'publicado')),
                name='ck_games_status_publicacao',
            ),
        ]

    def __str__(self):
        return self.titulo


class Achievement(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, related_name='achievements')
    steam_apiname = models.CharField(max_length=200)
    nome = models.CharField(max_length=200)
    descricao = models.TextField(blank=True, null=True)
    icon_url = models.URLField(max_length=500, blank=True, null=True)

    class Meta:
        db_table = 'achievements'
        verbose_name = 'conquista'
        constraints = [
            models.UniqueConstraint(
                fields=['game', 'steam_apiname'], name='uq_game_achievement',
            ),
        ]

    def __str__(self):
        return f'{self.game} — {self.nome}'
