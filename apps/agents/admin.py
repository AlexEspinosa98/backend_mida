from django.contrib import admin

from .models import PromptSistema


@admin.register(PromptSistema)
class PromptSistemaAdmin(admin.ModelAdmin):
    list_display = ("clave", "orden", "activo", "actualizado_en")
    list_editable = ("orden", "activo")
    ordering = ("orden", "clave")
    fields = ("clave", "contenido", "orden", "activo", "actualizado_en")
    readonly_fields = ("actualizado_en",)

    def has_add_permission(self, request):
        # Las 3 claves (sintesis_clinica, sintesis_familiar, tips_nutricion)
        # ya vienen sembradas por la migración -- no tiene sentido crear
        # una fila con una clave que ningún nodo consulta.
        return False

    def has_delete_permission(self, request, obj=None):
        # Borrar una fila no la "apaga" (el nodo usaría el texto por
        # defecto de todas formas), pero sí pierde el historial editado --
        # mejor que el admin la desactive con `activo` en vez de borrarla.
        return False
