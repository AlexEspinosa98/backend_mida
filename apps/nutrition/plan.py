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

from django.db.models import Q

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


def _alimentos_disponibles_por_grupo(
    edad_meses: float, etnia: str | None = None
) -> dict[str, list[Alimento]]:
    """Catálogo general (region_especifica="") + alimentos propios de la
    comunidad del paciente cuando aplica -- ADITIVO por defecto, nunca
    quita nada del catálogo general (mismo criterio que la comparación
    OMS+comunidad en apps/who_standards/local_patterns.py: la comunidad se
    suma). La única excepción puntual es `excluido_para_region`: un
    alimento general puede marcarse como no apropiado/accesible para una
    comunidad específica (ej. Kumis para pacientes Kogui, que no tienen
    tradición de fermento lácteo de vaca) y así no se le ofrece a esa
    comunidad aunque siga disponible para el resto."""
    filtro_region = Q(region_especifica="")
    if etnia and etnia != "ninguna":
        filtro_region |= Q(region_especifica=etnia)

    disponibles: dict[str, list[Alimento]] = {}
    for grupo, _ in Alimento.Grupo.choices:
        queryset = Alimento.objects.filter(
            filtro_region, grupo=grupo, disponible=True, edad_minima_meses__lte=edad_meses
        )
        if etnia and etnia != "ninguna":
            queryset = queryset.exclude(excluido_para_region=etnia)
        disponibles[grupo] = list(queryset.order_by("nombre"))
    return disponibles


def _info_nutricional_porcion(alimento: Alimento) -> dict:
    """Aporte nutricional de UNA porción de referencia de este alimento
    (escalado desde los valores por 100g/100mL). Devuelve None en cada
    campo que no se pueda calcular por falta de dato -- ver
    _totales_nutricionales, que usa esos None para marcar el total del
    día como incompleto en vez de subestimarlo en silencio."""
    porcion_g = alimento.porcion_referencia_g
    factor = (porcion_g / 100) if porcion_g else None

    def _escalar(valor):
        if valor is None or factor is None:
            return None
        return round(float(valor) * factor, 1)

    return {
        "porcion_g": porcion_g,
        "porcion_texto": alimento.porcion_texto,
        "calorias_kcal": _escalar(alimento.calorias_kcal_100g),
        "proteina_g": _escalar(alimento.proteina_g_100g),
        "carbohidratos_g": _escalar(alimento.carbohidratos_g_100g),
        "grasa_g": _escalar(alimento.grasa_g_100g),
    }


_CAMPOS_NUTRICIONALES = ["calorias_kcal", "proteina_g", "carbohidratos_g", "grasa_g"]


def _totales_nutricionales(comidas: dict[str, list[dict]]) -> dict:
    """Suma el aporte nutricional de todos los alimentos del día.
    `datos_completos=False` señala que al menos un alimento del día no
    tenía información nutricional registrada -- el total es, entonces,
    un PISO (subestimado), no una cifra completa, y así debe mostrarse."""
    totales = {campo: 0.0 for campo in _CAMPOS_NUTRICIONALES}
    datos_completos = True
    for alimentos in comidas.values():
        for alimento in alimentos:
            for campo in _CAMPOS_NUTRICIONALES:
                valor = alimento.get(campo)
                if valor is None:
                    datos_completos = False
                else:
                    totales[campo] += valor
    return {
        **{campo: round(valor, 1) for campo, valor in totales.items()},
        "datos_completos": datos_completos,
    }


def _promedio_semanal(dias: list[dict]) -> dict:
    n = len(dias) or 1
    promedio = {
        campo: round(sum(d["totales_nutricionales"][campo] for d in dias) / n, 1)
        for campo in _CAMPOS_NUTRICIONALES
    }
    promedio["datos_completos"] = all(d["totales_nutricionales"]["datos_completos"] for d in dias)
    return promedio


def generar_plan_semanal(edad_meses: float, etnia: str | None = None) -> dict:
    """Devuelve un dict JSON-serializable (para persistir en
    ReporteGenerado.plan_nutricional):

    {
      "aplica": bool,
      "motivo_no_aplica": str | None,
      "grupos_sin_opciones": [str],   # grupos sin ningún alimento disponible para esta edad
      "dias": [
        {
          "dia": "Lunes",
          "comidas": {"Desayuno": [{"nombre":..., "notas":..., "porcion_g":...,
                                     "calorias_kcal":..., "proteina_g":...,
                                     "carbohidratos_g":..., "grasa_g":...}, ...], ...},
          "totales_nutricionales": {"calorias_kcal":..., ..., "datos_completos": bool},
        },
        ...
      ],
      "promedio_diario": {"calorias_kcal":..., ..., "datos_completos": bool},
    }

    `etnia`: además del catálogo general, incluye los alimentos marcados
    con `region_especifica` igual a esta etnia (ver
    _alimentos_disponibles_por_grupo) -- p. ej. "kogui" o "arhuaco".
    Los campos nutricionales (porcion_g, calorias_kcal, etc.) vienen de
    valores de REFERENCIA aproximados cargados en el catálogo (ver
    apps/nutrition/migrations/0005_seed_datos_nutricionales.py) -- si un
    alimento no tiene esos datos cargados, sus campos vienen en None y
    `datos_completos` queda en False para ese día/promedio, en vez de
    subestimar el total en silencio.
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
            "promedio_diario": None,
        }

    disponibles = _alimentos_disponibles_por_grupo(edad_meses, etnia)
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
        entrada = {"nombre": alimento.nombre, "notas": alimento.notas}
        entrada.update(_info_nutricional_porcion(alimento))
        return entrada

    dias = []
    for dia in DIAS_SEMANA:
        comidas = {}
        for comida, grupos in COMPOSICION_COMIDAS.items():
            elegidos = [siguiente(comida, grupo) for grupo in grupos]
            comidas[comida] = [a for a in elegidos if a is not None]
        dias.append(
            {"dia": dia, "comidas": comidas, "totales_nutricionales": _totales_nutricionales(comidas)}
        )

    return {
        "aplica": True,
        "motivo_no_aplica": None,
        "grupos_sin_opciones": grupos_sin_opciones,
        "dias": dias,
        "promedio_diario": _promedio_semanal(dias),
    }


def resumen_disponibilidad(edad_meses: float, etnia: str | None = None) -> dict[str, list[str]]:
    """Lista simple de nombres disponibles por grupo (para dar contexto
    al LLM al redactar los consejos -- nunca para que elija comidas)."""
    disponibles = _alimentos_disponibles_por_grupo(edad_meses, etnia)
    return {grupo: [a.nombre for a in items] for grupo, items in disponibles.items()}


def catalogo_disponible(edad_meses: float, etnia: str | None = None) -> dict[str, list[dict]]:
    """Como _alimentos_disponibles_por_grupo pero serializado a dicts
    simples -- para un endpoint de solo lectura que permita previsualizar
    el efecto de `region_especifica`/`excluido_para_region` para una etnia
    dada, antes de generar un plan real (ver apps/nutrition/views.py)."""
    disponibles = _alimentos_disponibles_por_grupo(edad_meses, etnia)
    return {
        grupo: [
            {
                "nombre": alimento.nombre,
                "region_especifica": alimento.region_especifica,
                "porcion_g": alimento.porcion_referencia_g,
                "porcion_texto": alimento.porcion_texto,
                "calorias_kcal_100g": (
                    float(alimento.calorias_kcal_100g)
                    if alimento.calorias_kcal_100g is not None
                    else None
                ),
                "calorias_por_porcion": alimento.calorias_por_porcion,
            }
            for alimento in items
        ]
        for grupo, items in disponibles.items()
    }
