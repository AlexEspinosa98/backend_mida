from rest_framework.permissions import BasePermission

from .models import PerfilUsuario


def rol_de(user):
    if user.is_superuser:
        return PerfilUsuario.Rol.SUPERADMIN
    return getattr(getattr(user, "perfil", None), "rol", None)


class EsSuperadmin(BasePermission):
    message = "Requiere rol superadmin."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated) and rol_de(user) == PerfilUsuario.Rol.SUPERADMIN


class EsMedico(BasePermission):
    """Un superadmin también puede hacer todo lo que un médico -- nunca al revés."""

    message = "Requiere rol médico."

    def has_permission(self, request, view):
        user = request.user
        if not (user and user.is_authenticated):
            return False
        rol = rol_de(user)
        return rol in (PerfilUsuario.Rol.MEDICO, PerfilUsuario.Rol.SUPERADMIN)
