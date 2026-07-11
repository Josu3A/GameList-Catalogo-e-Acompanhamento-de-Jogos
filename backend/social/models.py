"""Rede social e organização (ESQUEMA_DADOS §4) — extensões futuras.

Apenas os modelos, sem endpoints: o banco continua nascendo com as 18 tabelas
do esquema, e a API social será exposta quando a extensão for implementada.
"""
from django.conf import settings
from django.db import models


class Friendship(models.Model):
    class Status(models.TextChoices):
        PENDENTE = 'pendente', 'Pendente'
        ACEITO = 'aceito', 'Aceito'

    # user solicitou; friend recebeu (auto-relacionamento em users)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='friendships_enviadas',
    )
    friend = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='friendships_recebidas',
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDENTE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'friendships'
        verbose_name = 'amizade'
        constraints = [
            models.UniqueConstraint(fields=['user', 'friend'], name='uq_friendship'),
            models.CheckConstraint(
                condition=models.Q(status__in=('pendente', 'aceito')),
                name='ck_friendships_status',
            ),
            models.CheckConstraint(
                condition=~models.Q(user=models.F('friend')),
                name='ck_friendship_nao_reflexiva',
            ),
        ]

    def __str__(self):
        return f'{self.user.nome} → {self.friend.nome} ({self.status})'


class ReviewLike(models.Model):
    """Curtida em review. A review é a linha de user_games com review não-nulo."""

    pk = models.CompositePrimaryKey('user_game_id', 'user_id')
    user_game = models.ForeignKey(
        'library.UserGame', on_delete=models.CASCADE, related_name='likes',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='review_likes',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'review_likes'
        verbose_name = 'curtida de review'
        verbose_name_plural = 'curtidas de review'

    def __str__(self):
        return f'{self.user.nome} curtiu review #{self.user_game_id}'


class List(models.Model):
    """Listas/coleções customizadas do usuário (ex.: "Top 10 RPGs")."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lists',
    )
    nome = models.CharField(max_length=150)
    descricao = models.TextField(blank=True, null=True)
    publica = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'lists'
        verbose_name = 'lista customizada'
        constraints = [
            models.UniqueConstraint(fields=['user', 'nome'], name='uq_list_user_nome'),
        ]

    def __str__(self):
        return f'{self.nome} ({self.user.nome})'


class ListItem(models.Model):
    pk = models.CompositePrimaryKey('lista_id', 'game_id')
    lista = models.ForeignKey(
        List, on_delete=models.CASCADE, db_column='list_id', related_name='items',
    )
    game = models.ForeignKey(
        'catalog.Game', on_delete=models.RESTRICT, related_name='list_items',
    )
    ordem = models.IntegerField(blank=True, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'list_items'
        verbose_name = 'item de lista'
        verbose_name_plural = 'itens de lista'

    def __str__(self):
        return f'{self.game.titulo} em {self.lista.nome}'


class Notification(models.Model):
    class Tipo(models.TextChoices):
        PEDIDO_AMIZADE = 'pedido_amizade', 'Pedido de amizade'
        AMIZADE_ACEITA = 'amizade_aceita', 'Amizade aceita'
        REVIEW_CURTIDA = 'review_curtida', 'Review curtida'

    user = models.ForeignKey(  # destinatário
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='notifications',
    )
    actor = models.ForeignKey(  # quem gerou o evento
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='notifications_geradas',
    )
    tipo = models.CharField(max_length=20, choices=Tipo.choices)
    friendship = models.ForeignKey(
        Friendship, on_delete=models.CASCADE, blank=True, null=True,
        related_name='notifications',
    )
    user_game = models.ForeignKey(
        'library.UserGame', on_delete=models.CASCADE, blank=True, null=True,
        related_name='notifications',
    )
    lida = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'
        verbose_name = 'notificação'
        verbose_name_plural = 'notificações'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tipo__in=(
                    'pedido_amizade', 'amizade_aceita', 'review_curtida',
                )),
                name='ck_notifications_tipo',
            ),
            # Exatamente uma referência preenchida, conforme o tipo (§4.4)
            models.CheckConstraint(
                condition=(
                    models.Q(
                        tipo__in=('pedido_amizade', 'amizade_aceita'),
                        friendship__isnull=False,
                        user_game__isnull=True,
                    )
                    | models.Q(
                        tipo='review_curtida',
                        user_game__isnull=False,
                        friendship__isnull=True,
                    )
                ),
                name='ck_notifications_referencia',
            ),
        ]
        indexes = [
            models.Index(fields=['user', 'lida'], name='idx_notifications_user_lida'),
        ]

    def __str__(self):
        return f'{self.tipo} para {self.user.nome}'
