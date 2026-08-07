from django.contrib import admin

from .models import Paciente


@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    list_display = (
        "nombre_completo",
        "documento_identidad",
        "fecha_nacimiento",
        "sexo",
        "etnia",
        "creado_en",
    )
    search_fields = ("nombres", "apellidos", "documento_identidad")
    list_filter = ("sexo", "etnia")
