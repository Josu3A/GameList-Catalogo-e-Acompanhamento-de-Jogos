"""Lista pessoal e conquistas do usuário (ESQUEMA_DADOS §1.3 e §3.2)."""
from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class UserGame(models.Model):
    class Status(models.TextChoices):
        JOGANDO = 'jogando', 'Jogando'
        COMPLETO = 'completo', 'Completo'
        QUERO_JOGAR = 'quero_jogar', 'Quero jogar'
        PAUSADO = 'pausado', 'Pausado'
        ABANDONADO = 'abandonado', 'Abandonado'

    class Fonte(models.TextChoices):
        MANUAL = 'manual', 'Manual'
        STEAM_SYNC = 'steam_sync', 'Sincronização Steam'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_games',
    )
    # RESTRICT: não se apaga do catálogo um jogo presente em listas (§6)
    game = models.ForeignKey(
        'catalog.Game', on_delete=models.RESTRICT, related_name='user_games',
    )
    status = models.CharField(max_length=20, choices=Status.choices)
    nota = models.DecimalField(
        max_digits=3, decimal_places=1, blank=True, null=True,
        validators=[MinValueValidator(0), MaxValueValidator(10)],
    )
    horas_jogadas = models.DecimalField(
        max_digits=7, decimal_places=1, default=0,
        validators=[MinValueValidator(0)],
    )
    platinado = models.BooleanField(default=False)
    data_inicio = models.DateField(blank=True, null=True)
    data_fim = models.DateField(blank=True, null=True)
    review = models.TextField(blank=True, null=True)
    fonte = models.CharField(
        max_length=20, choices=Fonte.choices, default=Fonte.MANUAL,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_games'
        ordering = ['-updated_at']
        verbose_name = 'jogo da lista pessoal'
        verbose_name_plural = 'jogos da lista pessoal'
        constraints = [
            models.UniqueConstraint(fields=['user', 'game'], name='uq_user_game'),
            models.CheckConstraint(
                condition=models.Q(status__in=(
                    'jogando', 'completo', 'quero_jogar', 'pausado', 'abandonado',
                )),
                name='ck_user_games_status',
            ),
            models.CheckConstraint(
                condition=models.Q(nota__gte=0) & models.Q(nota__lte=10),
                name='ck_user_games_nota',
            ),
            models.CheckConstraint(
                condition=models.Q(horas_jogadas__gte=0),
                name='ck_user_games_horas',
            ),
            models.CheckConstraint(
                condition=models.Q(fonte__in=('manual', 'steam_sync')),
                name='ck_user_games_fonte',
            ),
        ]
        indexes = [
            # Destaque de platinas no perfil (índice parcial — ESQUEMA_DADOS §5)
            models.Index(
                fields=['user'],
                name='idx_user_games_platinados',
                condition=models.Q(platinado=True),
            ),
        ]

    def __str__(self):
        return f'{self.user.nome} — {self.game.titulo} ({self.status})'


class UserAchievement(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='user_achievements',
    )
    achievement = models.ForeignKey(
        'catalog.Achievement', on_delete=models.CASCADE,
        related_name='user_achievements',
    )
    desbloqueada_em = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'user_achievements'
        verbose_name = 'conquista do usuário'
        verbose_name_plural = 'conquistas do usuário'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'achievement'], name='uq_user_achievement',
            ),
        ]

    def __str__(self):
        return f'{self.user.nome} — {self.achievement.nome}'
