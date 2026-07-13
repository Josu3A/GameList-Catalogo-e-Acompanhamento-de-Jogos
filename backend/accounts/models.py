"""Usuário customizado — tabela `users` do esquema (ESQUEMA_DADOS §1.1)."""
import os
import uuid

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.validators import FileExtensionValidator
from django.db import models

# Extensões de imagem aceitas no upload de avatar.
AVATAR_ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif']


def avatar_upload_to(instance, filename):
    """Nome de arquivo único (uuid) preservando a extensão.

    O nome original do usuário não é reaproveitado: o caminho gravado fica
    opaco (`avatars/<uuid>.<ext>`) — o usuário nunca vê o caminho, só a foto.
    """
    ext = os.path.splitext(filename)[1].lower() or '.jpg'
    return f'avatars/{uuid.uuid4().hex}{ext}'


class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, email, nome, password=None, **extra_fields):
        if not email:
            raise ValueError('O e-mail é obrigatório.')
        user = self.model(email=self.normalize_email(email), nome=nome, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, nome, password=None, **extra_fields):
        extra_fields['tipo_usuario'] = User.TipoUsuario.ADMIN
        return self.create_user(email, nome, password, **extra_fields)


class User(AbstractBaseUser):
    class TipoUsuario(models.TextChoices):
        COMUM = 'comum', 'Comum'
        ADMIN = 'admin', 'Administrador'

    nome = models.CharField(max_length=100)
    email = models.EmailField(max_length=255, unique=True)
    # O hash gerado pelo Django é gravado na coluna senha_hash do esquema.
    password = models.CharField('senha', max_length=255, db_column='senha_hash')
    tipo_usuario = models.CharField(
        max_length=20,
        choices=TipoUsuario.choices,
        default=TipoUsuario.COMUM,
    )
    bio = models.TextField(blank=True, null=True)
    # Avatar por upload. A coluna `avatar_url` (VARCHAR 500 do esquema) passa a
    # guardar o CAMINHO relativo do arquivo (ex.: avatars/<uuid>.jpg); a API o
    # serializa como URL de mídia. O usuário vê a foto, nunca o caminho.
    avatar_url = models.ImageField(
        'avatar',
        upload_to=avatar_upload_to,
        max_length=500,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(AVATAR_ALLOWED_EXTENSIONS)],
    )
    perfil_publico = models.BooleanField(default=True)
    steam_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nome']

    class Meta:
        db_table = 'users'
        verbose_name = 'usuário'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(tipo_usuario__in=('comum', 'admin')),
                name='ck_users_tipo_usuario',
            ),
        ]

    def __str__(self):
        return f'{self.nome} <{self.email}>'

    def get_full_name(self):
        return self.nome

    def get_short_name(self):
        return self.nome

    # O papel (comum/admin) vem de tipo_usuario; o Django Admin e o sistema de
    # permissões enxergam admin como staff/superuser.

    @property
    def is_admin(self):
        return self.tipo_usuario == self.TipoUsuario.ADMIN

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def is_superuser(self):
        return self.is_admin

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return self.is_admin
