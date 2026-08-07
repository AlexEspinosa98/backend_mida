from pathlib import Path

from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from weasyprint import CSS, HTML

from apps.agents.clinical_actions import sugerencias_clinicas, sugerencias_familiares
from apps.who_standards.glossary import (
    EXPLICACION_DESVIACION_ESTANDAR,
    EXPLICACION_ESTANDAR_OMS,
    GLOSARIO_INDICADORES,
    LEYENDA_COLORES,
)
from apps.who_standards.local_patterns import EXPLICACION_METODOLOGIA as EXPLICACION_PATRON_LOCAL

from .charts import generar_grafico_indicador

_CSS_PATH = Path(__file__).parent / "static" / "reports" / "report_pdf.css"
_CSS_FAMILIAR_PATH = Path(__file__).parent / "static" / "reports" / "report_familiar_pdf.css"

_ORDEN_INDICADORES = ["TE", "PT", "PE", "IMCE", "PCE", "PBE"]

_SEMAFORO = {
    "normal": {"color": "verde", "texto": "Dentro de lo esperado"},
    "moderado": {"color": "amarillo", "texto": "Requiere atención"},
    "severo": {"color": "rojo", "texto": "Requiere atención prioritaria"},
    "critico": {"color": "rojo", "texto": "Requiere atención urgente"},
    "no_aplica": {"color": "gris", "texto": "No evaluado"},
}


def _resultados_ordenados(evaluacion):
    resultados = {r.indicador: r for r in evaluacion.resultados.all()}
    return [resultados[i] for i in _ORDEN_INDICADORES if i in resultados]


def _reconstruir_hallazgos(evaluacion, resultados_ordenados) -> dict:
    """Las sugerencias clínicas son puramente determinísticas (mismas reglas
    de apps.agents.clinical_actions) -- se recalculan aquí a partir de los
    ResultadoIndicador ya persistidos, en vez de guardarlas duplicadas en la
    base de datos."""
    resultados_dict = [
        {
            "indicador": r.indicador,
            "nivel_alerta": r.nivel_alerta,
            "clasificacion": r.clasificacion,
            "detalle": r.detalle,
        }
        for r in resultados_ordenados
    ]
    hallazgos = {
        "resultados": resultados_dict,
        "alerta_critica": evaluacion.alerta_critica,
        "edema_bilateral": evaluacion.edema_bilateral,
    }
    hallazgos["sugerencias"] = sugerencias_clinicas(hallazgos)
    hallazgos["sugerencias_familiares"] = sugerencias_familiares(hallazgos)
    return hallazgos


def _imc_calculado(evaluacion) -> float:
    talla_m = float(evaluacion.talla_cm) / 100.0
    return float(evaluacion.peso_kg) / (talla_m**2)


def generar_pdf_evaluacion(evaluacion) -> bytes:
    resultados_ordenados = _resultados_ordenados(evaluacion)
    hallazgos = _reconstruir_hallazgos(evaluacion, resultados_ordenados)

    items = [
        {
            "resultado": r,
            "grafico": generar_grafico_indicador(evaluacion.paciente.sexo, r.indicador, r),
            "glosario": GLOSARIO_INDICADORES.get(r.indicador),
        }
        for r in resultados_ordenados
    ]

    contexto = {
        "evaluacion": evaluacion,
        "paciente": evaluacion.paciente,
        "items": items,
        "imc_calculado": _imc_calculado(evaluacion),
        "resumen_clinico": getattr(evaluacion.reporte, "resumen_clinico", ""),
        "alerta_critica": evaluacion.alerta_critica,
        "sugerencias": hallazgos["sugerencias"],
        "explicacion_estandar_oms": EXPLICACION_ESTANDAR_OMS,
        "explicacion_desviacion": EXPLICACION_DESVIACION_ESTANDAR,
        "leyenda_colores": LEYENDA_COLORES,
        "explicacion_patron_local": (
            EXPLICACION_PATRON_LOCAL if evaluacion.paciente.etnia != "ninguna" else None
        ),
    }
    html_str = render_to_string("reports/report_pdf.html", contexto)

    return HTML(string=html_str).write_pdf(stylesheets=[CSS(filename=str(_CSS_PATH))])


def generar_pdf_familiar_evaluacion(evaluacion) -> bytes:
    resultados_ordenados = _resultados_ordenados(evaluacion)
    hallazgos = _reconstruir_hallazgos(evaluacion, resultados_ordenados)

    items = [
        {
            "resultado": r,
            "semaforo": _SEMAFORO.get(r.nivel_alerta, _SEMAFORO["no_aplica"]),
            "nombre": GLOSARIO_INDICADORES.get(r.indicador, {}).get("nombre", r.indicador),
        }
        for r in resultados_ordenados
    ]

    contexto = {
        "evaluacion": evaluacion,
        "paciente": evaluacion.paciente,
        "items": items,
        "resumen_familiar": getattr(evaluacion.reporte, "resumen_familiar", ""),
        "alerta_critica": evaluacion.alerta_critica,
        "sugerencias": hallazgos["sugerencias_familiares"],
        "explicacion_estandar_oms": EXPLICACION_ESTANDAR_OMS,
    }
    html_str = render_to_string("reports/report_familiar_pdf.html", contexto)

    return HTML(string=html_str).write_pdf(stylesheets=[CSS(filename=str(_CSS_FAMILIAR_PATH))])


def obtener_o_generar_pdf(evaluacion):
    reporte = evaluacion.reporte
    if not reporte.pdf_file:
        pdf_bytes = generar_pdf_evaluacion(evaluacion)
        reporte.pdf_file.save(
            f"reporte_mida_{evaluacion.id}.pdf", ContentFile(pdf_bytes), save=True
        )
    return reporte.pdf_file


def obtener_o_generar_pdf_familiar(evaluacion):
    reporte = evaluacion.reporte
    if not reporte.pdf_file_familiar:
        pdf_bytes = generar_pdf_familiar_evaluacion(evaluacion)
        reporte.pdf_file_familiar.save(
            f"reporte_familiar_mida_{evaluacion.id}.pdf", ContentFile(pdf_bytes), save=True
        )
    return reporte.pdf_file_familiar
