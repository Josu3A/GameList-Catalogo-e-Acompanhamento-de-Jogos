"""Permissões de papel (CONTEXTO_PROJETO §4): admin gerencia o catálogo,
usuário comum só lê. A regra usa tipo_usuario explicitamente para ficar
clara no domínio, em vez de depender de is_staff do Django."""
from rest_framework.permissions import SAFE_METHODS, BasePermission


def _eh_admin(user):
    return bool(user and user.is_authenticated and user.tipo_usuario == 'admin')


class IsAdmin(BasePermission):
    message = 'Apenas administradores podem executar esta ação.'

    def has_permission(self, request, view):
        return _eh_admin(request.user)


class IsAdminOrReadOnly(BasePermission):
    message = 'Apenas administradores podem alterar o catálogo.'

    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or _eh_admin(request.user)
