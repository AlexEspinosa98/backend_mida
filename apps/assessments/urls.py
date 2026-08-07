from django.urls import path

from .views import EvaluacionCreateView, EvaluacionDetailView, EvaluacionReporteView, PacienteEvaluacionesListView

urlpatterns = [
    path("evaluaciones/", EvaluacionCreateView.as_view(), name="evaluacion-create"),
    path("evaluaciones/<uuid:id>/", EvaluacionDetailView.as_view(), name="evaluacion-detail"),
    path("evaluaciones/<uuid:id>/reporte/", EvaluacionReporteView.as_view(), name="evaluacion-reporte"),
    path(
        "pacientes/<uuid:paciente_id>/evaluaciones/",
        PacienteEvaluacionesListView.as_view(),
        name="paciente-evaluaciones",
    ),
]
