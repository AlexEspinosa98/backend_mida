"""Generador DETERMINÍSTICO del plan de alimentación semanal.

Decisión de diseño clave: la SELECCIÓN de qué alimento va en cada comida
es puramente por rotación sobre el catálogo editable (`Alimento`, filtrado
por disponible=True y edad_minima_meses) -- nunca por el LLM. El LLM (ver
apps/agents/nodes/nutrition.py) solo redacta una introducción y consejos
generales SOBRE el plan ya armado aquí.

Esto es intencional: a lo largo de este proyecto, cada vez que se le pidió
al LLM local (3B) que seleccionara/combinara datos estructurados él mismo
(no solo redactar prosa sobre datos ya dados), cometió errores reales
(ver README.md). Elegir qué alimentos son seguros para la edad de un niño
no es un lugar para repetir ese riesgo -- por eso es 100% código, testeado,
y escala automáticamente según lo que el administrador agregue/quite en
/admin/nutrition/alimento/, sin tocar este archivo."""

from __future__ import annotations

from .models import Alimento

DIAS_SEMANA = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]

# Qué grupos de alimentos componen cada comida del día. Ajustar esta
# estructura (no el algoritmo de rotación) si se quiere cambiar el
# número de comidas o su composición.
COMPOSICION_COMIDAS: dict[str, list[str]] = {
    "Desayuno": ["cereal", "fruta", "lacteo"],
    "Almuerzo": ["proteina", "cereal", "verdura"],
    "Merienda": ["fruta", "lacteo"],
    "Cena": ["proteina", "verdura", "cereal"],
}

EDAD_MINIMA_ALIMENTACION_COMPLEMENTARIA_MESES = 6


def _alimentos_disponibles_por_grupo(edad_meses: float) -> dict[str, list[Alimento]]:
    disponibles: dict[str, list[Alimento]] = {}
    for grupo, _ in Alimento.Grupo.choices:
        disponibles[grupo] = list(
            Alimento.objects.filter(
                grupo=grupo, disponible=True, edad_minima_meses__lte=edad_meses
            ).order_by("nombre")
        )
    return disponibles


def generar_plan_semanal(edad_meses: float) -> dict:
    """Devuelve un dict JSON-serializable (para persistir en
    ReporteGenerado.plan_nutricional):

    {
      "aplica": bool,
      "motivo_no_aplica": str | None,
      "grupos_sin_opciones": [str],   # grupos sin ningún alimento disponible para esta edad
      "dias": [
        {"dia": "Lunes", "comidas": {"Desayuno": [{"nombre":..., "notas":...}, ...], ...}},
        ...
      ],
    }
    """
    if edad_meses < EDAD_MINIMA_ALIMENTACION_COMPLEMENTARIA_MESES:
        return {
            "aplica": False,
            "motivo_no_aplica": (
                "Antes de los 6 meses, la OMS recomienda lactancia materna exclusiva "
                "(o la fórmula indicada por el profesional de salud tratante) -- no "
                "aplica un plan de alimentación complementaria a esta edad."
            ),
            "grupos_sin_opciones": [],
            "dias": [],
        }

    disponibles = _alimentos_disponibles_por_grupo(edad_meses)
    grupos_sin_opciones = [g for g, items in disponibles.items() if not items]

    # Cursor independiente por (comida, grupo) -- no solo por grupo. Si se
    # usara un único cursor por grupo compartido entre comidas del mismo
    # día (ej. "fruta" aparece en Desayuno Y Merienda), un número par de
    # alimentos disponibles hace que cada comida quede pegada siempre al
    # mismo alimento (el cursor avanza de a 2 por día y nunca cambia de
    # paridad) -- separar el cursor por comida evita ese problema y da
    # variedad real dentro de cada comida a lo largo de la semana.
    cursores = {
        (comida, grupo): 0 for comida, grupos in COMPOSICION_COMIDAS.items() for grupo in grupos
    }

    def siguiente(comida: str, grupo: str) -> dict | None:
        items = disponibles[grupo]
        if not items:
            return None
        clave = (comida, grupo)
        alimento = items[cursores[clave] % len(items)]
        cursores[clave] += 1
        return {"nombre": alimento.nombre, "notas": alimento.notas}

    dias = []
    for dia in DIAS_SEMANA:
        comidas = {}
        for comida, grupos in COMPOSICION_COMIDAS.items():
            elegidos = [siguiente(comida, grupo) for grupo in grupos]
            comidas[comida] = [a for a in elegidos if a is not None]
        dias.append({"dia": dia, "comidas": comidas})

    return {
        "aplica": True,
        "motivo_no_aplica": None,
        "grupos_sin_opciones": grupos_sin_opciones,
        "dias": dias,
    }


def resumen_disponibilidad(edad_meses: float) -> dict[str, list[str]]:
    """Lista simple de nombres disponibles por grupo (para dar contexto
    al LLM al redactar los consejos -- nunca para que elija comidas)."""
    disponibles = _alimentos_disponibles_por_grupo(edad_meses)
    return {grupo: [a.nombre for a in items] for grupo, items in disponibles.items()}
