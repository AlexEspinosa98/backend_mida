import uuid

from django.db import models

from .choices import TriEstado


class Evaluacion(models.Model):
    class Estado(models.TextChoices):
        PENDIENTE = "pendiente", "Pendiente"
        PROCESANDO = "procesando", "Procesando"
        COMPLETADA = "completada", "Completada"
        ERROR = "error", "Error"

    class TipoMedicionTalla(models.TextChoices):
        ACOSTADO = "acostado", "Longitud (acostado)"
        DE_PIE = "de_pie", "Estatura (de pie)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    paciente = models.ForeignKey(
        "patients.Paciente", related_name="evaluaciones", on_delete=models.PROTECT
    )

    # Código de caso propio (HU-1) -- generado por el servicio si no se manda uno
    # explícito, para referenciar el caso en comunicaciones externas sin exponer el
    # UUID interno. blank=True + UniqueConstraint condicional (igual que
    # Paciente.documento_identidad) porque las filas creadas antes de esta columna
    # quedan en blanco y no deben chocar entre sí contra un unique=True estricto.
    codigo_caso = models.CharField(max_length=40, blank=True, default="")
    notas_administrativas = models.TextField(blank=True, default="")

    fecha_evaluacion = models.DateField()

    # Edad derivada de paciente.fecha_nacimiento y fecha_evaluacion al crear la evaluación.
    edad_dias = models.PositiveIntegerField()
    edad_meses_decimal = models.DecimalField(max_digits=5, decimal_places=2)

    peso_kg = models.DecimalField(max_digits=5, decimal_places=2)
    talla_cm = models.DecimalField(max_digits=5, decimal_places=2)
    tipo_medicion_talla = models.CharField(max_length=10, choices=TipoMedicionTalla.choices)
    perimetro_cefalico_cm = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    perimetro_braquial_cm = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    # Cintura/cadera (HU-3): dato clínico de contexto, no alimentan ningún indicador OMS de
    # los 6 ya calculados -- no hay tabla LMS oficial de cintura/cadera para 0-5 años.
    perimetro_cintura_cm = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    perimetro_cadera_cm = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    edema_bilateral = models.BooleanField(default=False)

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    alerta_critica = models.BooleanField(default=False)
    error_detalle = models.TextField(blank=True, default="")

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["codigo_caso"],
                condition=models.Q(codigo_caso__gt=""),
                name="unique_codigo_caso_si_existe",
            )
        ]

    def __str__(self):
        return f"Evaluación {self.id} — {self.paciente_id} ({self.fecha_evaluacion})"


class ResultadoIndicador(models.Model):
    class Indicador(models.TextChoices):
        TALLA_EDAD = "TE", "Talla para la Edad"
        PESO_TALLA = "PT", "Peso para la Talla"
        PESO_EDAD = "PE", "Peso para la Edad"
        IMC_EDAD = "IMCE", "IMC para la Edad"
        PC_EDAD = "PCE", "Perímetro Cefálico para la Edad"
        PB_EDAD = "PBE", "Perímetro Braquial para la Edad"

    class NivelAlerta(models.TextChoices):
        NORMAL = "normal", "Normal"
        MODERADO = "moderado", "Moderado"
        SEVERO = "severo", "Severo"
        CRITICO = "critico", "Crítico"
        NO_APLICA = "no_aplica", "No aplica"

    evaluacion = models.ForeignKey(
        Evaluacion, related_name="resultados", on_delete=models.CASCADE
    )
    indicador = models.CharField(max_length=6, choices=Indicador.choices)
    valor_z = models.DecimalField(max_digits=6, decimal_places=3, null=True, blank=True)
    clasificacion = models.CharField(max_length=120)
    nivel_alerta = models.CharField(max_length=10, choices=NivelAlerta.choices)
    es_bypass = models.BooleanField(default=False)
    detalle = models.JSONField(default=dict, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["evaluacion", "indicador"], name="unique_indicador_por_evaluacion"
            )
        ]
        ordering = ["indicador"]

    def __str__(self):
        return f"{self.indicador} = {self.valor_z} ({self.clasificacion})"


class ReporteGenerado(models.Model):
    evaluacion = models.OneToOneField(
        Evaluacion, related_name="reporte", on_delete=models.CASCADE
    )
    resumen_clinico = models.TextField()
    resumen_familiar = models.TextField(blank=True, default="")
    plan_nutricional = models.JSONField(default=dict, blank=True)
    tips_nutricionales = models.TextField(blank=True, default="")
    pdf_file = models.FileField(upload_to="reportes/%Y/%m/", null=True, blank=True)
    pdf_file_familiar = models.FileField(
        upload_to="reportes_familiares/%Y/%m/", null=True, blank=True
    )
    # Fecha/objetivo del reporte (HU-1) -- puede diferir de fecha_evaluacion (la de la
    # medición física); objetivo_reporte se le pasa al LLM como contexto adicional al
    # redactar, sin que invente uno que no se le dio.
    fecha_reporte = models.DateField(null=True, blank=True)
    objetivo_reporte = models.CharField(max_length=200, blank=True, default="")
    generado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reporte de {self.evaluacion_id}"


class CalidadMedicion(models.Model):
    """HU-4 -- deja constancia de qué tan confiable es la medición física."""

    evaluacion = models.OneToOneField(
        Evaluacion, related_name="calidad_medicion", on_delete=models.CASCADE
    )
    balanza_calibrada = models.CharField(
        max_length=15, choices=TriEstado.choices, default=TriEstado.NO_REPORTADO
    )
    instrumentos_validados = models.CharField(
        max_length=15, choices=TriEstado.choices, default=TriEstado.NO_REPORTADO
    )
    medicion_repetida = models.CharField(
        max_length=15, choices=TriEstado.choices, default=TriEstado.NO_REPORTADO
    )
    observaciones = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Calidad de medición de {self.evaluacion_id}"


class SignosClinicos(models.Model):
    """HU-5 -- signos observados durante la visita. Solo aparece en el reporte
    técnico, nunca en el familiar (ver HU-13)."""

    evaluacion = models.OneToOneField(
        Evaluacion, related_name="signos_clinicos", on_delete=models.CASCADE
    )
    fatiga = models.BooleanField(default=False)
    decaimiento = models.BooleanField(default=False)
    fiebre = models.BooleanField(default=False)
    diarrea = models.BooleanField(default=False)
    vomito = models.BooleanField(default=False)
    perdida_peso_reciente = models.BooleanField(default=False)
    rechazo_alimento = models.BooleanField(default=False)
    deshidratacion = models.BooleanField(default=False)
    dificultad_respiratoria = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Signos clínicos de {self.evaluacion_id}"


class HabitosAlimentarios(models.Model):
    """HU-6 -- lo que la familia YA hace, no lo que debería hacer (eso lo genera
    el plan nutricional de apps.nutrition)."""

    evaluacion = models.OneToOneField(
        Evaluacion, related_name="habitos_alimentarios", on_delete=models.CASCADE
    )
    numero_comidas_dia = models.PositiveSmallIntegerField(null=True, blank=True)
    alimentos_frecuentes = models.TextField(blank=True, default="")
    alimentos_escasos = models.TextField(blank=True, default="")
    cambios_recientes_alimentacion = models.TextField(blank=True, default="")
    restricciones_culturales_familiares = models.TextField(blank=True, default="")
    acceso_agua_segura = models.CharField(
        max_length=15, choices=TriEstado.choices, default=TriEstado.NO_REPORTADO
    )

    def __str__(self):
        return f"Hábitos alimentarios de {self.evaluacion_id}"


class ActividadFisica(models.Model):
    """HU-7."""

    class NivelActividad(models.TextChoices):
        BAJO = "bajo", "Bajo"
        MODERADO = "moderado", "Moderado"
        ALTO = "alto", "Alto"

    evaluacion = models.OneToOneField(
        Evaluacion, related_name="actividad_fisica", on_delete=models.CASCADE
    )
    nivel_actividad = models.CharField(max_length=10, choices=NivelActividad.choices)
    actividades_diarias = models.TextField(blank=True, default="")
    limitaciones = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Actividad física de {self.evaluacion_id}"


class ContextoFamiliarTerritorial(models.Model):
    """HU-8."""

    evaluacion = models.OneToOneField(
        Evaluacion, related_name="contexto_familiar", on_delete=models.CASCADE
    )
    antecedentes_familiares_baja_talla = models.CharField(
        max_length=15, choices=TriEstado.choices, default=TriEstado.NO_REPORTADO
    )
    hermanos_baja_talla = models.CharField(
        max_length=15, choices=TriEstado.choices, default=TriEstado.NO_REPORTADO
    )
    inseguridad_alimentaria_reportada = models.CharField(
        max_length=15, choices=TriEstado.choices, default=TriEstado.NO_REPORTADO
    )
    dificultad_acceso_salud = models.CharField(
        max_length=15, choices=TriEstado.choices, default=TriEstado.NO_REPORTADO
    )
    observaciones_familia = models.TextField(blank=True, default="")
    observaciones_autoridad_tradicional = models.TextField(blank=True, default="")

    def __str__(self):
        return f"Contexto familiar/territorial de {self.evaluacion_id}"
