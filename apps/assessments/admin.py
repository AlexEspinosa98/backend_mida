from django.contrib import admin

from .models import Evaluacion, ReporteGenerado, ResultadoIndicador


class ResultadoIndicadorInline(admin.TabularInline):
    model = ResultadoIndicador
    extra = 0
    readonly_fields = ("indicador", "valor_z", "clasificacion", "nivel_alerta", "es_bypass")
    can_delete = False


class ReporteGeneradoInline(admin.StackedInline):
    model = ReporteGenerado
    extra = 0
    readonly_fields = ("resumen_clinico", "pdf_file", "generado_en")
    can_delete = False


@admin.register(Evaluacion)
class EvaluacionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "paciente",
        "fecha_evaluacion",
        "edad_meses_decimal",
        "estado",
        "alerta_critica",
        "creado_en",
    )
    list_filter = ("estado", "alerta_critica")
    search_fields = ("paciente__nombres", "paciente__apellidos", "paciente__documento_identidad")
    inlines = [ResultadoIndicadorInline, ReporteGeneradoInline]
