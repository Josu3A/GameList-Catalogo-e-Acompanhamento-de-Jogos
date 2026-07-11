from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
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
        fields = ('id', 'nome', 'email', 'password', 'bio', 'avatar_url', 'perfil_publico')
        read_only_fields = ('id',)

    def validate_password(self, value):
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
