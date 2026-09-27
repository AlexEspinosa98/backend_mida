from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import EsMedico, EsSuperadmin
from apps.patients.models import Paciente

from .models import Alimento
from .plan import EDAD_MINIMA_ALIMENTACION_COMPLEMENTARIA_MESES, catalogo_disponible
from .serializers import AlimentoSerializer


class CatalogoDisponibleView(APIView):
    """GET /api/v1/nutricion/catalogo/?edad_meses=24&etnia=kogui

    Endpoint de SOLO LECTURA -- no crea ni modifica ningún alimento (para eso
    ver AlimentoViewSet más abajo). Sirve para previsualizar qué catálogo
    efectivo vería un paciente con esa edad y etnia (catálogo general +
    alimentos propios de su comunidad, menos los excluidos para ella) sin
    tener que generar una evaluación completa -- pensado para el simulador de
    frontend (ver /simulador/), que ahora requiere login de médico (ya no hay
    acceso libre de comunidad)."""

    permission_classes = [EsMedico]

    def get(self, request):
        try:
            edad_meses = float(request.query_params.get("edad_meses", 24))
        except ValueError:
            return Response({"detail": "edad_meses debe ser un número."}, status=400)

        etnia = request.query_params.get("etnia") or None
        if etnia and etnia not in dict(Paciente.Etnia.choices):
            return Response({"detail": f"etnia inválida: {etnia}"}, status=400)

        if edad_meses < EDAD_MINIMA_ALIMENTACION_COMPLEMENTARIA_MESES:
            return Response(
                {
                    "aplica": False,
                    "motivo_no_aplica": (
                        "Antes de los 6 meses, la OMS recomienda lactancia materna "
                        "exclusiva -- no aplica un catálogo de alimentación "
                        "complementaria a esta edad."
                    ),
                    "catalogo": {},
                }
            )

        return Response({"aplica": True, "motivo_no_aplica": None, "catalogo": catalogo_disponible(edad_meses, etnia)})


class AlimentoViewSet(viewsets.ModelViewSet):
    """CRUD del catálogo de alimentos -- /api/v1/nutricion/alimentos/.

    Antes esto solo se podía hacer desde /admin/nutrition/alimento/ (que
    sigue existiendo y funcionando igual); esto le da al frontend su propia
    pantalla de gestión de catálogo, sin depender del admin de Django.

    Ver/leer (list, retrieve) es de cualquier médico -- necesitan poder
    consultar el catálogo. Crear/editar/borrar un alimento es exclusivo de
    superadmin: es una decisión de catálogo/nutrición, no un acto clínico
    puntual sobre un paciente, mismo criterio que ya separa EsMedico de
    EsSuperadmin en el resto de la API."""

    queryset = Alimento.objects.all().order_by("grupo", "nombre")
    serializer_class = AlimentoSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [EsMedico()]
        return [EsSuperadmin()]

    def get_queryset(self):
        qs = super().get_queryset()
        params = self.request.query_params
        if params.get("grupo"):
            qs = qs.filter(grupo=params["grupo"])
        if params.get("region_especifica"):
            qs = qs.filter(region_especifica=params["region_especifica"])
        if params.get("disponible") not in (None, ""):
            disponible = params["disponible"].strip().lower() in ("1", "true", "si", "yes")
            qs = qs.filter(disponible=disponible)
        if params.get("nombre"):
            qs = qs.filter(nombre__icontains=params["nombre"])
        return qs
