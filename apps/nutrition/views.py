from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import EsMedico
from apps.patients.models import Paciente

from .plan import EDAD_MINIMA_ALIMENTACION_COMPLEMENTARIA_MESES, catalogo_disponible


class CatalogoDisponibleView(APIView):
    """GET /api/v1/nutricion/catalogo/?edad_meses=24&etnia=kogui

    Endpoint de SOLO LECTURA -- no crea ni modifica ningún alimento (eso
    sigue siendo exclusivo de /admin/nutrition/alimento/). Sirve para
    previsualizar qué catálogo efectivo vería un paciente con esa edad y
    etnia (catálogo general + alimentos propios de su comunidad, menos los
    excluidos para ella) sin tener que generar una evaluación completa --
    pensado para el simulador de frontend (ver /simulador/), que ahora
    requiere login de médico (ya no hay acceso libre de comunidad)."""

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
