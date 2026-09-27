from rest_framework.routers import DefaultRouter

from django.urls import path

from .views import LoginView, UsuarioAdminViewSet

router = DefaultRouter()
router.register("usuarios", UsuarioAdminViewSet, basename="usuario-admin")

urlpatterns = [
    path("auth/login/", LoginView.as_view(), name="auth-login"),
] + router.urls
