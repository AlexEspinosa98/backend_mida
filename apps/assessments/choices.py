from django.db import models


class TriEstado(models.TextChoices):
    """Patrón compartido "Sí / No / No reportado" de varios campos del formulario
    ampliado (calidad de medición, antecedentes familiares, inseguridad
    alimentaria...) -- un mismo TextChoices para no repetir la lógica."""

    SI = "si", "Sí"
    NO = "no", "No"
    NO_REPORTADO = "no_reportado", "No reportado"
