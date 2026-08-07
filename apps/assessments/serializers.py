from decimal import Decimal

from rest_framework import serializers

from apps.patients.models import Paciente
from apps.patients.serializers import PacienteSerializer

from .models import Evaluacion, ReporteGenerado, ResultadoIndicador


class PacienteInputSerializer(serializers.Serializer):
    """Identidad del paciente. Todo es opcional: si se omite, el servicio crea
    un registro mínimo para poder persistir el historial de todas formas."""

    id = serializers.UUIDField(required=False)
    nombres = serializers.CharField(max_length=150, required=False, allow_blank=True)
    apellidos = serializers.CharField(max_length=150, required=False, allow_blank=True)
    documento_identidad = serializers.CharField(max_length=50, required=False, allow_null=True)
    fecha_nacimiento = serializers.DateField(required=False)
    etnia = serializers.ChoiceField(
        choices=Paciente.Etnia.choices, required=False, default=Paciente.Etnia.NINGUNA
    )


class EvaluacionInputSerializer(serializers.Serializer):
    """Payload de entrada de POST /api/v1/evaluaciones/.

    Campos mínimos pedidos: edad (edad_meses), peso_kg, talla_cm, sexo,
    edema_bilateral (opcional). Se añaden perimetro_cefalico_cm y
    perimetro_braquial_cm (opcionales) porque la ficha técnica OMS los
    requiere para PC/E y PB/E.
    """

    paciente = PacienteInputSerializer(required=False)
    sexo = serializers.ChoiceField(choices=Paciente.Sexo.choices)
    fecha_evaluacion = serializers.DateField(required=False)

    edad_meses = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("60")
    )
    peso_kg = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0.5"), max_value=Decimal("60")
    )
    talla_cm = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("20"), max_value=Decimal("140")
    )
    tipo_medicion_talla = serializers.ChoiceField(choices=Evaluacion.TipoMedicionTalla.choices)
    perimetro_cefalico_cm = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal("20"),
        max_value=Decimal("60"),
    )
    perimetro_braquial_cm = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        required=False,
        allow_null=True,
        min_value=Decimal("5"),
        max_value=Decimal("30"),
    )
    edema_bilateral = serializers.BooleanField(required=False, default=False)


class ResultadoIndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadoIndicador
        fields = ["indicador", "valor_z", "clasificacion", "nivel_alerta", "es_bypass", "detalle"]


class ReporteGeneradoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporteGenerado
        fields = ["resumen_clinico", "resumen_familiar", "generado_en"]


class EvaluacionSerializer(serializers.ModelSerializer):
    paciente = PacienteSerializer(read_only=True)
    resultados = ResultadoIndicadorSerializer(many=True, read_only=True)
    reporte = ReporteGeneradoSerializer(read_only=True)
    reporte_pdf_url = serializers.SerializerMethodField()
    reporte_familiar_pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = Evaluacion
        fields = [
            "id",
            "paciente",
            "fecha_evaluacion",
            "edad_dias",
            "edad_meses_decimal",
            "peso_kg",
            "talla_cm",
            "tipo_medicion_talla",
            "perimetro_cefalico_cm",
            "perimetro_braquial_cm",
            "edema_bilateral",
            "estado",
            "alerta_critica",
            "resultados",
            "reporte",
            "reporte_pdf_url",
            "reporte_familiar_pdf_url",
            "creado_en",
        ]

    def get_reporte_pdf_url(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        return request.build_absolute_uri(f"/api/v1/evaluaciones/{obj.id}/reporte/")

    def get_reporte_familiar_pdf_url(self, obj):
        request = self.context.get("request")
        if not request:
            return None
        return request.build_absolute_uri(f"/api/v1/evaluaciones/{obj.id}/reporte-familiar/")
