from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import EsMedico
from apps.patients.models import Paciente

from .models import Evaluacion
from .serializers import EvaluacionInputSerializer, EvaluacionSerializer
from .services import ejecutar_evaluacion


class EvaluacionCreateView(APIView):
    """POST /api/v1/evaluaciones/

    Recibe las mediciones antropométricas de un niño (0-5 años), ejecuta
    el pipeline multiagente (LangGraph) que calcula los 6 indicadores OMS,
    persiste el resultado y devuelve el reporte estructurado en JSON."""

    permission_classes = [EsMedico]

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
    permission_classes = [EsMedico]


class _EvaluacionReporteBaseView(APIView):
    """Base común para las vistas de descarga de PDF (técnico y familiar)."""

    permission_classes = [EsMedico]
    nombre_archivo = "reporte_mida_{id}.pdf"

    def _obtener_evaluacion(self, id):
        try:
            return (
                Evaluacion.objects.select_related("paciente", "reporte")
                .prefetch_related("resultados")
                .get(id=id)
            )
        except Evaluacion.DoesNotExist as exc:
            raise Http404 from exc

    def _generar_pdf(self, evaluacion):
        raise NotImplementedError

    def get(self, request, id):
        evaluacion = self._obtener_evaluacion(id)

        if evaluacion.estado != Evaluacion.Estado.COMPLETADA:
            return Response(
                {"detail": "La evaluación no se completó correctamente; no hay reporte disponible."},
                status=status.HTTP_409_CONFLICT,
            )

        pdf_file = self._generar_pdf(evaluacion)
        return FileResponse(
            pdf_file.open("rb"),
            content_type="application/pdf",
            filename=self.nombre_archivo.format(id=evaluacion.id),
        )


class EvaluacionReporteView(_EvaluacionReporteBaseView):
    """GET /api/v1/evaluaciones/{id}/reporte/ — reporte técnico para el
    médico (genera la primera vez, sirve la versión cacheada después)."""

    nombre_archivo = "reporte_mida_{id}.pdf"

    def _generar_pdf(self, evaluacion):
        from apps.reports.pdf import obtener_o_generar_pdf

        return obtener_o_generar_pdf(evaluacion)


class EvaluacionReporteFamiliarView(_EvaluacionReporteBaseView):
    """GET /api/v1/evaluaciones/{id}/reporte-familiar/ — reporte en lenguaje
    sencillo para la familia/cuidador (genera la primera vez, cachea)."""

    nombre_archivo = "reporte_familiar_mida_{id}.pdf"

    def _generar_pdf(self, evaluacion):
        from apps.reports.pdf import obtener_o_generar_pdf_familiar

        return obtener_o_generar_pdf_familiar(evaluacion)


class PacienteEvaluacionesListView(ListAPIView):
    """GET /api/v1/pacientes/{paciente_id}/evaluaciones/ — historial longitudinal."""

    serializer_class = EvaluacionSerializer
    permission_classes = [EsMedico]

    def get_queryset(self):
        paciente_id = self.kwargs["paciente_id"]
        get_object_or_404(Paciente, id=paciente_id)
        return (
            Evaluacion.objects.filter(paciente_id=paciente_id)
            .select_related("paciente", "reporte")
            .prefetch_related("resultados")
        )
