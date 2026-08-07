from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.patients.models import Paciente

from .models import Evaluacion
from .serializers import EvaluacionInputSerializer, EvaluacionSerializer
from .services import ejecutar_evaluacion


class EvaluacionCreateView(APIView):
    """POST /api/v1/evaluaciones/

    Recibe las mediciones antropométricas de un niño (0-5 años), ejecuta
    el pipeline multiagente (LangGraph) que calcula los 6 indicadores OMS,
    persiste el resultado y devuelve el reporte estructurado en JSON."""

    def post(self, request):
        entrada = EvaluacionInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        evaluacion = ejecutar_evaluacion(entrada.validated_data)

        salida = EvaluacionSerializer(evaluacion, context={"request": request})
        codigo = status.HTTP_201_CREATED if evaluacion.estado == Evaluacion.Estado.COMPLETADA else status.HTTP_422_UNPROCESSABLE_ENTITY
        return Response(salida.data, status=codigo)


class EvaluacionDetailView(RetrieveAPIView):
    """GET /api/v1/evaluaciones/{id}/"""

    queryset = Evaluacion.objects.select_related("paciente", "reporte").prefetch_related("resultados")
    serializer_class = EvaluacionSerializer
    lookup_field = "id"


class EvaluacionReporteView(APIView):
    """GET /api/v1/evaluaciones/{id}/reporte/ — genera (primera vez) o sirve
    el PDF cacheado del reporte clínico."""

    def get(self, request, id):
        try:
            evaluacion = Evaluacion.objects.select_related("paciente", "reporte").prefetch_related(
                "resultados"
            ).get(id=id)
        except Evaluacion.DoesNotExist as exc:
            raise Http404 from exc

        if evaluacion.estado != Evaluacion.Estado.COMPLETADA:
            return Response(
                {"detail": "La evaluación no se completó correctamente; no hay reporte disponible."},
                status=status.HTTP_409_CONFLICT,
            )

        from apps.reports.pdf import obtener_o_generar_pdf

        pdf_file = obtener_o_generar_pdf(evaluacion)
        return FileResponse(
            pdf_file.open("rb"),
            content_type="application/pdf",
            filename=f"reporte_mida_{evaluacion.id}.pdf",
        )


class PacienteEvaluacionesListView(ListAPIView):
    """GET /api/v1/pacientes/{paciente_id}/evaluaciones/ — historial longitudinal."""

    serializer_class = EvaluacionSerializer

    def get_queryset(self):
        paciente_id = self.kwargs["paciente_id"]
        get_object_or_404(Paciente, id=paciente_id)
        return (
            Evaluacion.objects.filter(paciente_id=paciente_id)
            .select_related("paciente", "reporte")
            .prefetch_related("resultados")
        )
