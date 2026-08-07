"""Construye la "Conclusión" detallada de cada indicador para el reporte
técnico -- texto DETERMINÍSTICO (no generado por LLM), a partir de los
mismos datos ya calculados (glosario + resultado OMS + resultado
comunitario si aplica). Se decidió construir esto en Python en vez de
pedírselo al LLM porque, al probar el ajuste biocultural con el modelo
local, el LLM llegó a invertir cuál de las dos comparaciones (OMS vs.
comunidad) decía qué -- ver README.md, sección de advertencias."""

from __future__ import annotations

from apps.who_standards.glossary import GLOSARIO_INDICADORES

_NOMBRES_INDICADOR = {
    "TE": "la talla para la edad",
    "PT": "el peso para la talla",
    "PE": "el peso para la edad",
    "IMCE": "el IMC para la edad",
    "PCE": "el perímetro cefálico para la edad",
    "PBE": "el perímetro braquial para la edad",
}


def _interpretacion_glosario(g: dict, nivel_alerta: str, valor_z: float | None) -> str:
    if not g or valor_z is None:
        return ""
    if nivel_alerta == "normal":
        return ""
    if valor_z is not None and valor_z < 0:
        return g.get("significado_bajo", "")
    return g.get("significado_alto", "")


def construir_conclusion(indicador: str, resultado: dict) -> str:
    """resultado: dict con valor_z, clasificacion, nivel_alerta, detalle
    (que puede traer detalle["comunitario"])."""

    nombre = _NOMBRES_INDICADOR.get(indicador, indicador)
    g = GLOSARIO_INDICADORES.get(indicador, {})

    valor_z = resultado.get("valor_z")
    clasificacion = resultado.get("clasificacion", "")
    nivel_alerta = resultado.get("nivel_alerta", "normal")
    detalle = resultado.get("detalle", {}) or {}
    comunitario = detalle.get("comunitario")

    if nivel_alerta == "no_aplica":
        return detalle.get("motivo", "Este indicador no aplica para esta evaluación.")

    if valor_z is None:
        partes = [f"Para {nombre}, la clasificación es \"{clasificacion}\"."]
    else:
        partes = [
            f"Frente al patrón de la OMS, {nombre} se clasifica como \"{clasificacion}\" "
            f"(z = {valor_z:.2f})."
        ]
        interpretacion_oms = _interpretacion_glosario(g, nivel_alerta, valor_z)
        if interpretacion_oms:
            partes.append(interpretacion_oms)

    if comunitario:
        etnia_legible = comunitario["etnia"].capitalize()
        partes.append(
            f"Frente al patrón de crecimiento de la comunidad {etnia_legible}, el mismo "
            f"valor se clasifica como \"{comunitario['clasificacion']}\" "
            f"(z aproximado = {comunitario['valor_z']:.2f})."
        )
        coinciden = (nivel_alerta == "normal") == (comunitario["nivel_alerta"] == "normal")
        if coinciden:
            partes.append(
                "Las dos comparaciones coinciden, lo que refuerza esta interpretación."
            )
        else:
            if nivel_alerta != "normal" and comunitario["nivel_alerta"] == "normal":
                partes.append(
                    f"Esta diferencia es consistente con que {nombre} sea, para esta "
                    "comunidad, un rasgo de crecimiento poblacional saludable y no "
                    "necesariamente un signo de riesgo nutricional -- se recomienda "
                    "interpretar este hallazgo junto con el IMC, el peso-para-talla y el "
                    "perímetro braquial (ver 'Sugerencias de proceso')."
                )
            else:
                partes.append(
                    "Las dos comparaciones no coinciden -- se recomienda que el "
                    "profesional de salud revise este hallazgo con atención, considerando "
                    "ambas referencias."
                )

    return " ".join(partes)
