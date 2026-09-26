from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.assessments.urls")),
    path("api/v1/nutricion/", include("apps.nutrition.urls")),
    # Simulador de frontend -- NO es la interfaz final, es una página estática
    # de un solo archivo para probar la interacción con la API (flujo médico +
    # previsualización del catálogo por comunidad) antes de construir el
    # frontend real. Ver apps/reports/templates/simulador.html.
    path("simulador/", TemplateView.as_view(template_name="simulador.html"), name="simulador"),
]
