from rest_framework.routers import DefaultRouter

from django.urls import path

from .views import AlimentoViewSet, CatalogoDisponibleView

router = DefaultRouter()
router.register("alimentos", AlimentoViewSet, basename="alimento")

urlpatterns = [
    path("catalogo/", CatalogoDisponibleView.as_view(), name="nutricion-catalogo"),
] + router.urls
