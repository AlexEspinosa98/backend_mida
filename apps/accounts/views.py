from django.contrib.auth import authenticate, get_user_model
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import PerfilUsuario
from .permissions import EsSuperadmin, rol_de
from .serializers import CambiarPasswordSerializer, LoginSerializer, UsuarioAdminSerializer

Usuario = get_user_model()


class LoginView(APIView):
    """POST /api/v1/auth/login/ -- único punto de entrada, tanto para médicos como para
    superadmin (el rol viene en la respuesta, el frontend decide qué mostrar según eso)."""

    permission_classes = [AllowAny]

    def post(self, request):
        entrada = LoginSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        usuario = authenticate(
            username=entrada.validated_data["username"], password=entrada.validated_data["password"]
        )
        if usuario is None:
            raise AuthenticationFailed("Usuario o contraseña incorrectos.")
        if not usuario.is_active:
            raise AuthenticationFailed("Este usuario está inactivo.")

        token, _ = Token.objects.get_or_create(user=usuario)
        return Response(
            {
                "token": token.key,
                "username": usuario.username,
                "nombre": usuario.get_full_name() or usuario.username,
                "rol": rol_de(usuario),
            }
        )


class UsuarioAdminViewSet(viewsets.ModelViewSet):
    """CRUD de usuarios (crear médicos, editar, cambiar contraseña) -- exclusivo de superadmin.
    Es lo único que un superadmin hace en este sistema: no tiene acceso a evaluaciones/reportes
    salvo que además tenga rol médico (no es el caso por defecto)."""

    queryset = Usuario.objects.select_related("perfil").order_by("username")
    serializer_class = UsuarioAdminSerializer
    permission_classes = [EsSuperadmin]

    def perform_destroy(self, instance):
        # No se borra el usuario (perdería la trazabilidad de qué médico generó qué reporte) --
        # se desactiva, mismo efecto práctico (no puede loguearse) sin romper el historial.
        instance.is_active = False
        instance.save(update_fields=["is_active"])

    @action(detail=True, methods=["post"], url_path="cambiar-password")
    def cambiar_password(self, request, pk=None):
        usuario = self.get_object()
        entrada = CambiarPasswordSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)
        usuario.set_password(entrada.validated_data["password"])
        usuario.save(update_fields=["password"])
        # Invalida cualquier sesión (token) previa de ese usuario -- una contraseña se cambia
        # normalmente porque se sospecha que la anterior quedó expuesta; dejar el token viejo
        # vivo anularía el propósito del cambio.
        Token.objects.filter(user=usuario).delete()
        return Response({"detail": "Contraseña actualizada."}, status=status.HTTP_200_OK)
