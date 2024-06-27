from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Permite apenas o dono do post editar ou deletar
        return obj.author == request.user
