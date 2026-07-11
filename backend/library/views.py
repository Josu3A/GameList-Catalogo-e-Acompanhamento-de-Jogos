from django.contrib.auth import get_user_model
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import UserGame
from .serializers import UserGamePublicSerializer, UserGameSerializer

User = get_user_model()


class UserGameViewSet(viewsets.ModelViewSet):
    """CRUD da lista pessoal — sempre restrito ao próprio usuário
    (CONTEXTO_PROJETO §4: ninguém edita a lista de outro)."""

    serializer_class = UserGameSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ('status', 'platinado')
    ordering_fields = ('updated_at', 'nota', 'horas_jogadas')

    def get_queryset(self):
        return UserGame.objects.filter(user=self.request.user).select_related('game')


class ProfileView(APIView):
    """Perfil público: dados do usuário, lista de jogos e platinas em destaque."""

    permission_classes = [permissions.AllowAny]

    def get(self, request, user_id):
        user = get_object_or_404(User, pk=user_id)
        if not user.perfil_publico and request.user != user:
            # Perfil privado não revela nem a própria existência
            raise Http404
        jogos = UserGame.objects.filter(user=user).select_related('game')
        return Response({
            'id': user.id,
            'nome': user.nome,
            'bio': user.bio,
            'avatar_url': user.avatar_url,
            'platinas': UserGamePublicSerializer(
                jogos.filter(platinado=True), many=True,
            ).data,
            'jogos': UserGamePublicSerializer(jogos, many=True).data,
        })
