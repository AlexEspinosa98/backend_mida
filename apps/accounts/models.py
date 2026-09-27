from django.conf import settings
from django.db import models


class PerfilUsuario(models.Model):
    """Rol de un usuario dentro de la app -- no confundir con is_staff/is_superuser de Django,
    que solo controlan acceso a /admin/. Un usuario SIN fila aquí (todo lo que existe hoy:
    superusers creados con `createsuperuser`) se trata como superadmin -- así el primer usuario
    del sistema nunca queda bloqueado por no tener perfil, y el rollout de roles no requiere
    migrar datos (mismo patrón ya usado en otros backends de este mismo servidor)."""

    class Rol(models.TextChoices):
        SUPERADMIN = "superadmin", "Superadministrador"
        MEDICO = "medico", "Médico"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="perfil")
    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.MEDICO)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user} · {self.get_rol_display()}"
