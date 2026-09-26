from django.contrib import admin

from .models import Alimento


@admin.register(Alimento)
class AlimentoAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "grupo",
        "region_especifica",
        "excluido_para_region",
        "edad_minima_meses",
        "porcion_referencia_g",
        "calorias_kcal_100g",
        "disponible",
    )
    list_filter = ("grupo", "region_especifica", "excluido_para_region", "disponible")
    search_fields = ("nombre",)
    list_editable = ("disponible",)
    ordering = ("grupo", "nombre")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "nombre",
                    "grupo",
                    "region_especifica",
                    "excluido_para_region",
                    "disponible",
                    "notas",
                )
            },
        ),
        ("Edad", {"fields": ("edad_minima_meses",)}),
        (
            "Información nutricional (valores de referencia aproximados, por 100g/100mL)",
            {
                "fields": (
                    "porcion_referencia_g",
                    "calorias_kcal_100g",
                    "proteina_g_100g",
                    "carbohidratos_g_100g",
                    "grasa_g_100g",
                )
            },
        ),
    )
