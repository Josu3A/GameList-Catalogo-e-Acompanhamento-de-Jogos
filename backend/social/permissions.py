"""Permissões da camada social (padrão de accounts/permissions.py).

Amizade é assunto só dos dois envolvidos; lista customizada só o dono altera
(FRONTEND_TELAS §3.1 e §3.3).
"""
from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsFriendshipParticipant(BasePermission):
    message = 'Você não participa desta amizade.'

    def has_object_permission(self, request, view, obj):
        return request.user.id in (obj.user_id, obj.friend_id)


class IsListOwnerOrReadOnly(BasePermission):
    message = 'Apenas o dono pode alterar esta lista.'

    def has_object_permission(self, request, view, obj):
        # A visibilidade de leitura já é garantida pelo queryset da view;
        # aqui barramos qualquer escrita de quem não é o dono.
        if request.method in SAFE_METHODS:
            return True
        return obj.user_id == request.user.id
