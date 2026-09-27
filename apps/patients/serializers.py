from rest_framework import serializers

from .models import Paciente


class PacienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paciente
        fields = [
            "id",
            "nombres",
            "apellidos",
            "documento_identidad",
            "fecha_nacimiento",
            "sexo",
            "etnia",
            "comunidad_asentamiento",
            "municipio",
            "departamento",
            "cuidador_principal",
            "lengua_principal",
            "requiere_mediacion_cultural",
            "creado_en",
        ]
        read_only_fields = ["id", "creado_en"]
