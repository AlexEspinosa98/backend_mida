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
            "creado_en",
        ]
        read_only_fields = ["id", "creado_en"]
