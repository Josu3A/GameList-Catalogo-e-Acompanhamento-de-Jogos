from django.contrib.auth.password_validation import validate_password
from django.core.validators import FileExtensionValidator
from rest_framework import serializers

from .models import AVATAR_ALLOWED_EXTENSIONS, User

# Limite de tamanho do avatar enviado por upload.
MAX_AVATAR_BYTES = 2 * 1024 * 1024  # 2 MB


def validate_avatar_size(uploaded):
    if uploaded.size > MAX_AVATAR_BYTES:
        raise serializers.ValidationError('A imagem do avatar deve ter no máximo 2 MB.')
    return uploaded


class UserSerializer(serializers.ModelSerializer):
    # Recebe o arquivo por upload (multipart); na leitura, devolve a URL de mídia
    # (absoluta quando o request está no contexto do serializer). Enviar null limpa o avatar.
    avatar_url = serializers.ImageField(
        required=False,
        allow_null=True,
        max_length=500,
        validators=[
            FileExtensionValidator(AVATAR_ALLOWED_EXTENSIONS),
            validate_avatar_size,
        ],
        error_messages={
            'invalid_image': 'Envie um arquivo de imagem válido (JPG, PNG, WEBP ou GIF).',
        },
    )

    class Meta:
        model = User
        fields = (
            'id', 'nome', 'email', 'tipo_usuario', 'bio', 'avatar_url',
            'perfil_publico', 'steam_id', 'created_at',
        )
        read_only_fields = ('id', 'tipo_usuario', 'steam_id', 'created_at')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True, style={'input_type': 'password'}, label='Senha',
    )

    class Meta:
        model = User
        # tipo_usuario fica de fora de propósito: registro público sempre cria
        # usuário comum; admins são promovidos via Django Admin/createsuperuser.
        # avatar_url também fica de fora: o avatar é enviado por upload depois,
        # na edição de perfil (PATCH /api/auth/me/), não no cadastro.
        fields = ('id', 'nome', 'email', 'password', 'bio', 'perfil_publico')
        read_only_fields = ('id',)

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
