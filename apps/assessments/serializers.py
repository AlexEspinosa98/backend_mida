from decimal import Decimal

from rest_framework import serializers

from apps.patients.models import Paciente
from apps.patients.serializers import PacienteSerializer

from .choices import TriEstado
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


class AliasChoiceField(serializers.ChoiceField):
    """ChoiceField que además acepta alias de entrada (sin distinguir mayúsculas),
    normalizados al valor canónico antes de validar -- para no obligar al frontend
    a traducir a mano valores como "masculino" -> "M" o "pie" -> "de_pie"."""

    def __init__(self, *args, alias_map=None, **kwargs):
        self.alias_map = {k.lower(): v for k, v in (alias_map or {}).items()}
        super().__init__(*args, **kwargs)

    def to_internal_value(self, data):
        if isinstance(data, str):
            data = self.alias_map.get(data.lower(), data)
        return super().to_internal_value(data)


class PacienteInputSerializer(serializers.Serializer):
    """Identidad del paciente. Todo es opcional: si se omite, el servicio crea
    un registro mínimo para poder persistir el historial de todas formas."""

    id = serializers.UUIDField(required=False)
    nombres = serializers.CharField(max_length=150, required=False, allow_blank=True)
    apellidos = serializers.CharField(max_length=150, required=False, allow_blank=True)
    documento_identidad = serializers.CharField(max_length=50, required=False, allow_null=True)
    fecha_nacimiento = serializers.DateField(required=False)
    etnia = AliasChoiceField(
        choices=Paciente.Etnia.choices,
        required=False,
        default=Paciente.Etnia.NINGUNA,
        alias_map={"kaggaba": Paciente.Etnia.KOGUI},  # autónimo del mismo pueblo (HU-2)
    )

    # Datos culturales y territoriales (HU-2), todos opcionales.
    comunidad_asentamiento = serializers.CharField(
        max_length=150, required=False, allow_blank=True
    )
    municipio = serializers.CharField(max_length=150, required=False, allow_blank=True)
    departamento = serializers.CharField(max_length=150, required=False, allow_blank=True)
    cuidador_principal = serializers.CharField(max_length=150, required=False, allow_blank=True)
    lengua_principal = serializers.CharField(max_length=100, required=False, allow_blank=True)
    requiere_mediacion_cultural = serializers.BooleanField(required=False, default=False)


class CalidadMedicionInputSerializer(serializers.Serializer):
    """HU-4."""

    balanza_calibrada = serializers.ChoiceField(choices=TriEstado.choices, required=False)
    instrumentos_validados = serializers.ChoiceField(choices=TriEstado.choices, required=False)
    medicion_repetida = serializers.ChoiceField(choices=TriEstado.choices, required=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)


class SignosClinicosInputSerializer(serializers.Serializer):
    """HU-5."""

    fatiga = serializers.BooleanField(required=False, default=False)
    decaimiento = serializers.BooleanField(required=False, default=False)
    fiebre = serializers.BooleanField(required=False, default=False)
    diarrea = serializers.BooleanField(required=False, default=False)
    vomito = serializers.BooleanField(required=False, default=False)
    perdida_peso_reciente = serializers.BooleanField(required=False, default=False)
    rechazo_alimento = serializers.BooleanField(required=False, default=False)
    deshidratacion = serializers.BooleanField(required=False, default=False)
    dificultad_respiratoria = serializers.BooleanField(required=False, default=False)
    observaciones = serializers.CharField(required=False, allow_blank=True)


class HabitosAlimentariosInputSerializer(serializers.Serializer):
    """HU-6."""

    numero_comidas_dia = serializers.IntegerField(required=False, min_value=0, max_value=20)
    alimentos_frecuentes = serializers.CharField(required=False, allow_blank=True)
    alimentos_escasos = serializers.CharField(required=False, allow_blank=True)
    cambios_recientes_alimentacion = serializers.CharField(required=False, allow_blank=True)
    restricciones_culturales_familiares = serializers.CharField(required=False, allow_blank=True)
    acceso_agua_segura = serializers.ChoiceField(choices=TriEstado.choices, required=False)


class ActividadFisicaInputSerializer(serializers.Serializer):
    """HU-7."""

    nivel_actividad = serializers.ChoiceField(choices=ActividadFisica.NivelActividad.choices)
    actividades_diarias = serializers.CharField(required=False, allow_blank=True)
    limitaciones = serializers.CharField(required=False, allow_blank=True)


class ContextoFamiliarInputSerializer(serializers.Serializer):
    """HU-8."""

    antecedentes_familiares_baja_talla = serializers.ChoiceField(
        choices=TriEstado.choices, required=False
    )
    hermanos_baja_talla = serializers.ChoiceField(choices=TriEstado.choices, required=False)
    inseguridad_alimentaria_reportada = serializers.ChoiceField(
        choices=TriEstado.choices, required=False
    )
    dificultad_acceso_salud = serializers.ChoiceField(choices=TriEstado.choices, required=False)
    observaciones_familia = serializers.CharField(required=False, allow_blank=True)
    observaciones_autoridad_tradicional = serializers.CharField(required=False, allow_blank=True)


class EvaluacionInputSerializer(serializers.Serializer):
    """Payload de entrada de POST /api/v1/evaluaciones/.

    Campos mínimos pedidos: edad (edad_meses), peso_kg, talla_cm, sexo,
    edema_bilateral (opcional). Se añaden perimetro_cefalico_cm y
    perimetro_braquial_cm (opcionales) porque la ficha técnica OMS los
    requiere para PC/E y PB/E.

    Todo lo demás (codigo_caso, fecha_reporte, objetivo_reporte,
    notas_administrativas, cintura/cadera, y los cinco bloques anidados) es la
    ampliación del formulario completo (HU-1 a HU-8, ver docs/USER_STORIES.md)
    -- opcional, no rompe a un médico que solo manda lo mínimo de hoy.
    """

    paciente = PacienteInputSerializer(required=False)
    sexo = AliasChoiceField(
        choices=Paciente.Sexo.choices,
        alias_map={"masculino": Paciente.Sexo.MASCULINO, "femenino": Paciente.Sexo.FEMENINO},
    )
    fecha_evaluacion = serializers.DateField(required=False)

    codigo_caso = serializers.CharField(max_length=80, required=False, allow_blank=True)
    fecha_reporte = serializers.DateField(required=False)
    objetivo_reporte = serializers.CharField(max_length=200, required=False, allow_blank=True)
    notas_administrativas = serializers.CharField(required=False, allow_blank=True)

    def validate_codigo_caso(self, value):
        # Sin esto, un código repetido (ej. un reintento del frontend con el mismo
        # payload tras un timeout, sin saber que la evaluación original sí se creó)
        # reventaba como un IntegrityError sin capturar -> 500 -- acá se convierte
        # en un 400 claro, e incluye el id de la evaluación existente para que el
        # frontend pueda recuperarla en vez de perder el resultado.
        existente = Evaluacion.objects.filter(codigo_caso=value).first() if value else None
        if existente:
            raise serializers.ValidationError(
                f'Ya existe un caso con el código "{value}" (evaluación {existente.id}, '
                f"estado: {existente.estado}) -- si esto es un reintento, consulta "
                f"GET /api/v1/evaluaciones/{existente.id}/ en vez de repetir el POST, "
                "o genera un código de caso nuevo."
            )
        return value

    edad_meses = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0"), max_value=Decimal("60")
    )
    peso_kg = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("0.5"), max_value=Decimal("60")
    )
    talla_cm = serializers.DecimalField(
        max_digits=5, decimal_places=2, min_value=Decimal("20"), max_value=Decimal("140")
    )
    tipo_medicion_talla = AliasChoiceField(
        choices=Evaluacion.TipoMedicionTalla.choices,
        alias_map={
            "pie": Evaluacion.TipoMedicionTalla.DE_PIE,
            "estatura": Evaluacion.TipoMedicionTalla.DE_PIE,
            "longitud": Evaluacion.TipoMedicionTalla.ACOSTADO,
        },
    )
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
    perimetro_cintura_cm = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )
    perimetro_cadera_cm = serializers.DecimalField(
        max_digits=5, decimal_places=2, required=False, allow_null=True
    )
    edema_bilateral = serializers.BooleanField(required=False, default=False)

    calidad_medicion = CalidadMedicionInputSerializer(required=False)
    signos_clinicos = SignosClinicosInputSerializer(required=False)
    habitos_alimentarios = HabitosAlimentariosInputSerializer(required=False)
    actividad_fisica = ActividadFisicaInputSerializer(required=False)
    contexto_familiar = ContextoFamiliarInputSerializer(required=False)


class ResultadoIndicadorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResultadoIndicador
        fields = ["indicador", "valor_z", "clasificacion", "nivel_alerta", "es_bypass", "detalle"]


class ReporteGeneradoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReporteGenerado
        fields = [
            "resumen_clinico",
            "resumen_familiar",
            "plan_nutricional",
            "tips_nutricionales",
            "fecha_reporte",
            "objetivo_reporte",
            "generado_en",
        ]


class CalidadMedicionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalidadMedicion
        fields = [
            "balanza_calibrada",
            "instrumentos_validados",
            "medicion_repetida",
            "observaciones",
        ]


class SignosClinicosSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignosClinicos
        fields = [
            "fatiga",
            "decaimiento",
            "fiebre",
            "diarrea",
            "vomito",
            "perdida_peso_reciente",
            "rechazo_alimento",
            "deshidratacion",
            "dificultad_respiratoria",
            "observaciones",
        ]


class HabitosAlimentariosSerializer(serializers.ModelSerializer):
    class Meta:
        model = HabitosAlimentarios
        fields = [
            "numero_comidas_dia",
            "alimentos_frecuentes",
            "alimentos_escasos",
            "cambios_recientes_alimentacion",
            "restricciones_culturales_familiares",
            "acceso_agua_segura",
        ]


class ActividadFisicaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ActividadFisica
        fields = ["nivel_actividad", "actividades_diarias", "limitaciones"]


class ContextoFamiliarTerritorialSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContextoFamiliarTerritorial
        fields = [
            "antecedentes_familiares_baja_talla",
            "hermanos_baja_talla",
            "inseguridad_alimentaria_reportada",
            "dificultad_acceso_salud",
            "observaciones_familia",
            "observaciones_autoridad_tradicional",
        ]


class EvaluacionSerializer(serializers.ModelSerializer):
    paciente = PacienteSerializer(read_only=True)
    resultados = ResultadoIndicadorSerializer(many=True, read_only=True)
    reporte = ReporteGeneradoSerializer(read_only=True)
    reporte_pdf_url = serializers.SerializerMethodField()
    reporte_familiar_pdf_url = serializers.SerializerMethodField()
    calidad_medicion = CalidadMedicionSerializer(read_only=True)
    signos_clinicos = SignosClinicosSerializer(read_only=True)
    habitos_alimentarios = HabitosAlimentariosSerializer(read_only=True)
    actividad_fisica = ActividadFisicaSerializer(read_only=True)
    contexto_familiar = ContextoFamiliarTerritorialSerializer(read_only=True)

    class Meta:
        model = Evaluacion
        fields = [
            "id",
            "codigo_caso",
            "notas_administrativas",
            "paciente",
            "fecha_evaluacion",
            "edad_dias",
            "edad_meses_decimal",
            "peso_kg",
            "talla_cm",
            "tipo_medicion_talla",
            "perimetro_cefalico_cm",
            "perimetro_braquial_cm",
            "perimetro_cintura_cm",
            "perimetro_cadera_cm",
            "edema_bilateral",
            "estado",
            "alerta_critica",
            "resultados",
            "reporte",
            "reporte_pdf_url",
            "reporte_familiar_pdf_url",
            "calidad_medicion",
            "signos_clinicos",
            "habitos_alimentarios",
            "actividad_fisica",
            "contexto_familiar",
            "creado_en",
        ]

    def get_reporte_pdf_url(self, obj):
        return self._url_absoluta(f"/api/v1/evaluaciones/{obj.id}/reporte/")

    def get_reporte_familiar_pdf_url(self, obj):
        return self._url_absoluta(f"/api/v1/evaluaciones/{obj.id}/reporte-familiar/")

    def _url_absoluta(self, ruta):
        # build_absolute_uri(ruta) con una ruta que empieza en "/" la trata como ya relativa a
        # la raíz del sitio -- NUNCA le antepone SCRIPT_NAME, ni con FORCE_SCRIPT_NAME fijado.
        # Detrás de un nginx que monta esta app en un prefijo (ver DJANGO_FORCE_SCRIPT_NAME,
        # ej. /api/mida), había que anteponerlo a mano o el link quedaba roto en producción
        # (404: el prefijo nunca llegaba a la URL devuelta por la API).
        from django.urls import get_script_prefix

        request = self.context.get("request")
        if not request:
            return None
        return request.build_absolute_uri(get_script_prefix().rstrip("/") + ruta)


_ORDEN_NIVEL_ALERTA = {"no_aplica": -1, "normal": 0, "moderado": 1, "severo": 2, "critico": 3}


class EvaluacionResumenSerializer(EvaluacionSerializer):
    """Una fila del dashboard de reportes (GET /api/v1/evaluaciones/) -- a
    propósito más liviana que EvaluacionSerializer: sin los cinco bloques
    anidados del formulario completo ni el detalle de cada indicador, solo lo
    que se necesita para listar y decidir en qué caso entrar."""

    paciente_nombre = serializers.CharField(source="paciente.nombre_completo", read_only=True)
    paciente_etnia = serializers.CharField(source="paciente.etnia", read_only=True)
    nivel_alerta_maximo = serializers.SerializerMethodField()

    class Meta(EvaluacionSerializer.Meta):
        fields = [
            "id",
            "codigo_caso",
            "paciente_nombre",
            "paciente_etnia",
            "fecha_evaluacion",
            "estado",
            "alerta_critica",
            "nivel_alerta_maximo",
            "reporte_pdf_url",
            "reporte_familiar_pdf_url",
            "creado_en",
        ]

    def get_nivel_alerta_maximo(self, obj):
        niveles = [r.nivel_alerta for r in obj.resultados.all()]
        if not niveles:
            return None
        return max(niveles, key=lambda n: _ORDEN_NIVEL_ALERTA.get(n, -1))
