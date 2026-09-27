from django.contrib import admin

from .models import (
    ActividadFisica,
    CalidadMedicion,
    ContextoFamiliarTerritorial,
    Evaluacion,
    HabitosAlimentarios,
    ReporteGenerado,
    ResultadoIndicador,
    SignosClinicos,
)


class ResultadoIndicadorInline(admin.TabularInline):
    model = ResultadoIndicador
    extra = 0
    readonly_fields = ("indicador", "valor_z", "clasificacion", "nivel_alerta", "es_bypass")
    can_delete = False


class ReporteGeneradoInline(admin.StackedInline):
    model = ReporteGenerado
    extra = 0
    readonly_fields = (
        "resumen_clinico",
        "resumen_familiar",
        "plan_nutricional",
        "tips_nutricionales",
        "fecha_reporte",
        "objetivo_reporte",
        "pdf_file",
        "pdf_file_familiar",
        "generado_en",
    )
    can_delete = False


class CalidadMedicionInline(admin.StackedInline):
    model = CalidadMedicion
    extra = 0
    can_delete = False


class SignosClinicosInline(admin.StackedInline):
    model = SignosClinicos
    extra = 0
    can_delete = False


class HabitosAlimentariosInline(admin.StackedInline):
    model = HabitosAlimentarios
    extra = 0
    can_delete = False


class ActividadFisicaInline(admin.StackedInline):
    model = ActividadFisica
    extra = 0
    can_delete = False


class ContextoFamiliarTerritorialInline(admin.StackedInline):
    model = ContextoFamiliarTerritorial
    extra = 0
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
    search_fields = (
        "paciente__nombres",
        "paciente__apellidos",
        "paciente__documento_identidad",
        "codigo_caso",
    )
    inlines = [
        ResultadoIndicadorInline,
        ReporteGeneradoInline,
        CalidadMedicionInline,
        SignosClinicosInline,
        HabitosAlimentariosInline,
        ActividadFisicaInline,
        ContextoFamiliarTerritorialInline,
    ]
