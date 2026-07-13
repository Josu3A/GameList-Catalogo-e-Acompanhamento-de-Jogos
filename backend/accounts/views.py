import uuid

import requests
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.core.files.base import ContentFile
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import steam
from .models import User
from .serializers import LoginSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request,
            username=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
        )
        if user is None:
            return Response(
                {'detail': 'Credenciais inválidas.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        login(request, user)
        return Response(UserSerializer(user, context={'request': request}).data)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        logout(request)
        return Response({'detail': 'Sessão encerrada.'})


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user, context={'request': request}).data)

    def patch(self, request):
        # Edição do próprio perfil (nome, email, bio, avatar_url, perfil_publico).
        # avatar_url chega como arquivo (multipart) no upload, ou null para limpar.
        # tipo_usuario/steam_id são read_only no UserSerializer — não podem ser alterados aqui.
        serializer = UserSerializer(
            request.user, data=request.data, partial=True,
            context={'request': request},
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


@ensure_csrf_cookie
def csrf_view(request):
    """Define o cookie csrftoken para o frontend poder enviar X-CSRFToken."""
    return JsonResponse({'detail': 'Cookie CSRF definido.'})


# --- Integração Steam (OpenID 2.0) ------------------------------------------
# Decisão do projeto: a Steam só VINCULA a uma conta já existente (nunca cria
# conta). O botão de login por Steam loga quem já vinculou; SteamID desconhecido
# volta ao login com aviso. Ver LOG.md / CONTEXTO_PROJETO §6.

def _frontend_redirect(path):
    return redirect(f'{settings.FRONTEND_URL}{path}')


def _save_steam_avatar(user, url):
    """Baixa o avatar da Steam e o guarda como arquivo local (best-effort).

    O avatar_url é um ImageField: guardamos o arquivo em vez da URL externa,
    mantendo todos os avatares como mídia local. Falha de rede é silenciosa.
    """
    try:
        resp = requests.get(url, timeout=10)
    except requests.RequestException:
        return
    if not resp.ok or not resp.content:
        return
    user.avatar_url.save(f'{uuid.uuid4().hex}.jpg', ContentFile(resp.content), save=False)


def steam_login(request):
    """Redireciona o usuário ao provedor OpenID da Steam."""
    return_to = request.build_absolute_uri(reverse('auth-steam-callback'))
    realm = request.build_absolute_uri('/')
    return redirect(steam.build_login_url(return_to, realm))


def steam_callback(request):
    """Callback do OpenID: valida a resposta e vincula/loga conforme a sessão."""
    steam_id = steam.verify_response(request.GET)
    if not steam_id:
        return _frontend_redirect('/login?steam=error')

    if request.user.is_authenticated:
        # Vincular à conta logada.
        if User.objects.filter(steam_id=steam_id).exclude(pk=request.user.pk).exists():
            return _frontend_redirect('/settings/profile?steam=taken')
        user = request.user
        user.steam_id = steam_id
        if not user.avatar_url:
            summary = steam.get_player_summary(steam_id)
            avatar_src = summary.get('avatar_url') if summary else None
            if avatar_src:
                _save_steam_avatar(user, avatar_src)
        user.save(update_fields=['steam_id', 'avatar_url', 'updated_at'])
        return _frontend_redirect('/settings/profile?steam=linked')

    # Anônimo: loga se o SteamID já estiver vinculado a alguém; senão, avisa.
    user = User.objects.filter(steam_id=steam_id).first()
    if user is None:
        return _frontend_redirect('/login?steam=nolink')
    login(request, user)
    return _frontend_redirect('/?steam=login')


class SteamDisconnectView(APIView):
    """Desvincula a Steam da conta do usuário logado."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.steam_id = None
        request.user.save(update_fields=['steam_id', 'updated_at'])
        return Response(UserSerializer(request.user, context={'request': request}).data)
