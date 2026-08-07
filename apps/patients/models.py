import uuid

from django.db import models


class Paciente(models.Model):
    class Sexo(models.TextChoices):
        MASCULINO = "M", "Masculino"
        FEMENINO = "F", "Femenino"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nombres = models.CharField(max_length=150)
    apellidos = models.CharField(max_length=150)
    documento_identidad = models.CharField(max_length=50, blank=True, null=True)
    fecha_nacimiento = models.DateField()
    sexo = models.CharField(max_length=1, choices=Sexo.choices)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-creado_en"]
        constraints = [
            models.UniqueConstraint(
                fields=["documento_identidad"],
                condition=models.Q(documento_identidad__isnull=False),
                name="unique_documento_identidad_si_existe",
            )
        ]

    def __str__(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"
