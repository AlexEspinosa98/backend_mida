from django.contrib import admin

from .models import Alimento


@admin.register(Alimento)
class AlimentoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "grupo", "edad_minima_meses", "disponible")
    list_filter = ("grupo", "disponible")
    search_fields = ("nombre",)
    list_editable = ("disponible",)
    ordering = ("grupo", "nombre")
