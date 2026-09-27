from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.assessments.urls")),
    path("api/v1/nutricion/", include("apps.nutrition.urls")),
    # Simulador de frontend -- NO es la interfaz final, es una página estática
    # de un solo archivo para probar la interacción con la API (login +
    # flujo médico) antes de construir el frontend real. Requiere login de
    # médico, igual que la API. Ver apps/reports/templates/simulador.html.
    path("simulador/", TemplateView.as_view(template_name="simulador.html"), name="simulador"),
]
