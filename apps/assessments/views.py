from django.db import IntegrityError
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView, ListCreateAPIView, RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import EsMedico
from apps.patients.models import Paciente

from .models import Evaluacion
from .serializers import EvaluacionInputSerializer, EvaluacionResumenSerializer, EvaluacionSerializer
from .services import ejecutar_evaluacion


class EvaluacionPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class EvaluacionListCreateView(ListCreateAPIView):
    """GET /api/v1/evaluaciones/ — dashboard de reportes: listado paginado de
    todas las evaluaciones (no solo de un paciente puntual), con filtros por
    querystring: estado, alerta_critica (1/0), codigo_caso (contiene),
    paciente (contiene, busca en nombres y apellidos), fecha_desde/fecha_hasta
    (sobre fecha_evaluacion). Orden más reciente primero.

    POST /api/v1/evaluaciones/ — sin cambios: crea una evaluación (ver
    EvaluacionInputSerializer para el contrato completo)."""

    permission_classes = [EsMedico]
    serializer_class = EvaluacionResumenSerializer
    pagination_class = EvaluacionPagination

    def get_queryset(self):
        qs = (
            Evaluacion.objects.select_related("paciente", "reporte")
            .prefetch_related("resultados")
            .order_by("-creado_en")
        )
        params = self.request.query_params

        if params.get("estado"):
            qs = qs.filter(estado=params["estado"])
        if params.get("alerta_critica") not in (None, ""):
            es_critica = params["alerta_critica"].strip().lower() in ("1", "true", "si", "yes")
            qs = qs.filter(alerta_critica=es_critica)
        if params.get("codigo_caso"):
            qs = qs.filter(codigo_caso__icontains=params["codigo_caso"])
        if params.get("paciente"):
            q = params["paciente"]
            qs = qs.filter(Q(paciente__nombres__icontains=q) | Q(paciente__apellidos__icontains=q))
        if params.get("fecha_desde"):
            qs = qs.filter(fecha_evaluacion__gte=params["fecha_desde"])
        if params.get("fecha_hasta"):
            qs = qs.filter(fecha_evaluacion__lte=params["fecha_hasta"])

        return qs

    def create(self, request, *args, **kwargs):
        entrada = EvaluacionInputSerializer(data=request.data)
        entrada.is_valid(raise_exception=True)

        try:
            evaluacion = ejecutar_evaluacion(entrada.validated_data)
        except IntegrityError:
            # El serializer ya valida codigo_caso duplicado, pero esto cubre la
            # carrera entre dos POST casi simultáneos con el mismo código -- sin
            # esto, el segundo terminaba en un 500 sin capturar.
            return Response(
                {"codigo_caso": ["Ya existe un caso con ese código (creado justo ahora)."]},
                status=status.HTTP_409_CONFLICT,
            )

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
