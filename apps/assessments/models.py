import uuid

from django.db import models


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
    edema_bilateral = models.BooleanField(default=False)

    estado = models.CharField(max_length=20, choices=Estado.choices, default=Estado.PENDIENTE)
    alerta_critica = models.BooleanField(default=False)
    error_detalle = models.TextField(blank=True, default="")

    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]

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
    pdf_file = models.FileField(upload_to="reportes/%Y/%m/", null=True, blank=True)
    pdf_file_familiar = models.FileField(
        upload_to="reportes_familiares/%Y/%m/", null=True, blank=True
    )
    generado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reporte de {self.evaluacion_id}"
