"""Sugerencias clínicas DETERMINÍSTICAS (no generadas por LLM) sobre qué
hacer a continuación, según el nivel de alerta encontrado.

Alcance deliberadamente limitado a ACCIONES DE PROCESO (remitir, repetir
control, vigilar signos de alarma) -- nunca tratamiento, dosis, ni
recomendaciones nutricionales específicas (ese módulo aún no existe en
MIDA). El LLM del nodo de síntesis recibe esta lista como INSUMO para
redactarla en prosa; no debe inventar sugerencias adicionales.

Pure Python -- no Django imports.
"""
from __future__ import annotations

_ORDEN_SEVERIDAD = {"no_aplica": -1, "normal": 0, "moderado": 1, "severo": 2, "critico": 3}

_ACCIONES_POR_NIVEL: dict[str, list[str]] = {
    "critico": [
        "Remisión médica INMEDIATA / urgente -- no esperar a estudios adicionales.",
        "Vigilar signos de peligro mientras se accede a atención médica (letargia, "
        "rechazo a la vía oral, dificultad respiratoria, fiebre).",
        "Notificar al cuidador la urgencia de la remisión de forma clara y directa.",
    ],
    "severo": [
        "Remisión prioritaria a pediatría/nutrición en las próximas 48-72 horas.",
        "Repetir la evaluación antropométrica en el control de seguimiento que "
        "indique el profesional tratante.",
        "Vigilar signos de alarma hasta la consulta de remisión.",
    ],
    "moderado": [
        "Seguimiento cercano: repetir control antropométrico en 2-4 semanas.",
        "Considerar remisión a consulta de crecimiento y desarrollo si no hay "
        "mejoría en el próximo control.",
    ],
    "normal": [
        "Continuar controles de crecimiento según el calendario habitual.",
        "No se requiere intervención adicional a partir de este tamizaje.",
    ],
}

_NOTA_EDEMA = (
    "El edema bilateral es, por sí solo, un signo de desnutrición aguda severa "
    "(independientemente del z-score de peso-para-talla) -- amerita manejo como "
    "una emergencia nutricional."
)

_NOTA_PCE_INDEPENDIENTE = (
    "El hallazgo en perímetro cefálico no se explica por desnutrición reciente y "
    "debe evaluarse de forma independiente de los demás indicadores -- considerar "
    "remisión para valoración del desarrollo neurológico."
)

_NOTA_AJUSTE_BIOCULTURAL = (
    "{indicador} muestra un hallazgo frente al estándar OMS ({clasificacion_oms}) que el "
    "patrón de crecimiento local de la comunidad {etnia} no confirma (comparación "
    "comunitaria: Normal) -- esto es consistente con un patrón poblacional saludable "
    "documentado para esta etnia, no necesariamente con un problema nutricional. Se "
    "recomienda priorizar IMC, peso-para-talla y perímetro braquial (no afectados por "
    "este sesgo poblacional) para la valoración de riesgo nutricional real, y no basar "
    "la urgencia de remisión únicamente en este hallazgo."
)

# Misma lógica, en lenguaje simple para el reporte familiar (sin jerga
# clínica) -- también texto fijo, no generado por IA.
_ACCIONES_FAMILIARES_POR_NIVEL: dict[str, list[str]] = {
    "critico": [
        "Es urgente llevar a su hijo/a a un centro de salud HOY, sin esperar.",
        "Mientras busca atención, esté atento/a a señales de alarma: decaimiento "
        "extremo, no querer comer ni beber, o dificultad para respirar -- si "
        "aparecen, busque ayuda de inmediato.",
    ],
    "severo": [
        "Es importante llevar a su hijo/a a una consulta médica en los próximos "
        "2-3 días.",
        "El profesional de salud le indicará cuándo volver a medir a su hijo/a.",
    ],
    "moderado": [
        "Le recomendamos volver a control de crecimiento en las próximas "
        "2 a 4 semanas.",
        "Si nota que su hijo/a no mejora, consulte antes de esa fecha.",
    ],
    "normal": [
        "Continúe llevando a su hijo/a a los controles de crecimiento habituales.",
        "Por ahora no se necesita ninguna acción adicional.",
    ],
}

_NOTA_EDEMA_FAMILIAR = (
    "Se detectó hinchazón en ambas piernas o pies (edema), lo cual por sí solo "
    "es un signo de alerta importante, sin importar los demás resultados."
)

_NOTA_PCE_FAMILIAR = (
    "El resultado del perímetro de la cabeza debe revisarlo un profesional de "
    "salud aparte de los demás resultados."
)

_NOTA_AJUSTE_BIOCULTURAL_FAMILIAR = (
    "La {indicador_minuscula} de su hijo/a se comparó también con el patrón de "
    "crecimiento típico de niños de la comunidad {etnia}, y en esa comparación está "
    "dentro de lo esperado -- es decir, puede tratarse simplemente de un rasgo normal "
    "de crecimiento de su comunidad, no necesariamente un problema de nutrición. Aun "
    "así, coménteselo al profesional de salud para que lo revise junto con los demás "
    "resultados."
)


_NOMBRES_INDICADOR = {
    "TE": "Talla para la Edad",
    "PE": "Peso para la Edad",
}


def _tiene_ajuste_biocultural(r: dict) -> bool:
    """True cuando el hallazgo OMS de este indicador (moderado/severo, NO
    crítico -- un hallazgo crítico nunca se de-escala) es contradicho por
    una comparación comunitaria "Normal". Solo aplica a T/E y P/E, que son
    los dos indicadores donde el estudio local documenta el sesgo (ver
    apps/who_standards/local_patterns.py)."""
    comunitario = r.get("detalle", {}).get("comunitario")
    if not comunitario:
        return False
    if r.get("nivel_alerta") not in ("moderado", "severo"):
        return False
    return comunitario.get("nivel_alerta") == "normal"


def _nivel_efectivo(r: dict) -> str:
    """Nivel a usar para decidir la URGENCIA de las sugerencias -- igual
    al nivel_alerta OMS, salvo que exista un ajuste biocultural aplicable,
    en cuyo caso ese indicador no debe, por sí solo, escalar la urgencia
    de la remisión (la clasificación OMS original se sigue mostrando tal
    cual en el reporte, esto solo afecta qué acciones se sugieren)."""
    if _tiene_ajuste_biocultural(r):
        return "normal"
    return r.get("nivel_alerta", "normal")


def _nivel_maximo(hallazgos: dict) -> str:
    peor = "normal"
    for r in hallazgos.get("resultados", []):
        nivel = _nivel_efectivo(r)
        if _ORDEN_SEVERIDAD.get(nivel, 0) > _ORDEN_SEVERIDAD.get(peor, 0):
            peor = nivel
    if hallazgos.get("alerta_critica"):
        peor = "critico"
    return peor


def _notas_ajuste_biocultural(hallazgos: dict) -> list[str]:
    notas = []
    for r in hallazgos.get("resultados", []):
        if not _tiene_ajuste_biocultural(r):
            continue
        comunitario = r["detalle"]["comunitario"]
        notas.append(
            _NOTA_AJUSTE_BIOCULTURAL.format(
                indicador=_NOMBRES_INDICADOR.get(r["indicador"], r["indicador"]),
                clasificacion_oms=r["clasificacion"],
                etnia=comunitario["etnia"].capitalize(),
            )
        )
    return notas


def sugerencias_clinicas(hallazgos: dict) -> list[str]:
    """Devuelve una lista ordenada de acciones sugeridas (texto fijo, no
    generado por IA) según el hallazgo más severo del conjunto de
    resultados. El nodo de síntesis las recibe como hechos a narrar."""

    nivel = _nivel_maximo(hallazgos)
    acciones = list(_ACCIONES_POR_NIVEL.get(nivel, _ACCIONES_POR_NIVEL["normal"]))

    resultados_por_indicador = {r["indicador"]: r for r in hallazgos.get("resultados", [])}

    if hallazgos.get("edema_bilateral"):
        acciones.insert(0, _NOTA_EDEMA)

    pce = resultados_por_indicador.get("PCE")
    if pce and pce.get("nivel_alerta") in ("moderado", "severo", "critico"):
        acciones.append(_NOTA_PCE_INDEPENDIENTE)

    acciones.extend(_notas_ajuste_biocultural(hallazgos))

    return acciones


def _notas_ajuste_biocultural_familiares(hallazgos: dict) -> list[str]:
    notas = []
    for r in hallazgos.get("resultados", []):
        if not _tiene_ajuste_biocultural(r):
            continue
        comunitario = r["detalle"]["comunitario"]
        nombre = _NOMBRES_INDICADOR.get(r["indicador"], r["indicador"])
        notas.append(
            _NOTA_AJUSTE_BIOCULTURAL_FAMILIAR.format(
                indicador_minuscula=nombre.lower(),
                etnia=comunitario["etnia"].capitalize(),
            )
        )
    return notas


def sugerencias_familiares(hallazgos: dict) -> list[str]:
    """Misma decisión que sugerencias_clinicas(), en lenguaje simple para el
    reporte dirigido a la familia. Texto fijo, no generado por IA."""

    nivel = _nivel_maximo(hallazgos)
    acciones = list(_ACCIONES_FAMILIARES_POR_NIVEL.get(nivel, _ACCIONES_FAMILIARES_POR_NIVEL["normal"]))

    resultados_por_indicador = {r["indicador"]: r for r in hallazgos.get("resultados", [])}

    if hallazgos.get("edema_bilateral"):
        acciones.insert(0, _NOTA_EDEMA_FAMILIAR)

    pce = resultados_por_indicador.get("PCE")
    if pce and pce.get("nivel_alerta") in ("moderado", "severo", "critico"):
        acciones.append(_NOTA_PCE_FAMILIAR)

    acciones.extend(_notas_ajuste_biocultural_familiares(hallazgos))

    return acciones
