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


def _nivel_maximo(hallazgos: dict) -> str:
    peor = "normal"
    for r in hallazgos.get("resultados", []):
        nivel = r.get("nivel_alerta", "normal")
        if _ORDEN_SEVERIDAD.get(nivel, 0) > _ORDEN_SEVERIDAD.get(peor, 0):
            peor = nivel
    if hallazgos.get("alerta_critica"):
        peor = "critico"
    return peor


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

    return acciones


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

    return acciones
