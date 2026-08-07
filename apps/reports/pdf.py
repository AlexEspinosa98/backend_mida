from pathlib import Path

from django.core.files.base import ContentFile
from django.template.loader import render_to_string
from weasyprint import CSS, HTML

from .charts import generar_grafico_indicador

_CSS_PATH = Path(__file__).parent / "static" / "reports" / "report_pdf.css"

_ORDEN_INDICADORES = ["TE", "PT", "PE", "IMCE", "PCE", "PBE"]


def generar_pdf_evaluacion(evaluacion) -> bytes:
    resultados = {r.indicador: r for r in evaluacion.resultados.all()}
    resultados_ordenados = [resultados[i] for i in _ORDEN_INDICADORES if i in resultados]

    items = [
        {
            "resultado": r,
            "grafico": generar_grafico_indicador(evaluacion.paciente.sexo, r.indicador, r),
        }
        for r in resultados_ordenados
    ]

    contexto = {
        "evaluacion": evaluacion,
        "paciente": evaluacion.paciente,
        "items": items,
        "resumen_clinico": getattr(evaluacion.reporte, "resumen_clinico", ""),
        "alerta_critica": evaluacion.alerta_critica,
    }
    html_str = render_to_string("reports/report_pdf.html", contexto)

    return HTML(string=html_str).write_pdf(stylesheets=[CSS(filename=str(_CSS_PATH))])


def obtener_o_generar_pdf(evaluacion):
    reporte = evaluacion.reporte
    if not reporte.pdf_file:
        pdf_bytes = generar_pdf_evaluacion(evaluacion)
        reporte.pdf_file.save(
            f"reporte_mida_{evaluacion.id}.pdf", ContentFile(pdf_bytes), save=True
        )
    return reporte.pdf_file
