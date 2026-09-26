from django.urls import path

from .views import CatalogoDisponibleView

urlpatterns = [
    path("catalogo/", CatalogoDisponibleView.as_view(), name="nutricion-catalogo"),
]
