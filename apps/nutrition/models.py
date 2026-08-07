from django.db import models


class Alimento(models.Model):
    """Catálogo de alimentos que el administrador puede agregar/quitar
    desde /admin/ -- el plan nutricional semanal se genera SIEMPRE a
    partir de lo que esté marcado `disponible=True` aquí, así que crece o
    se reduce sin tocar código (ver apps/nutrition/plan.py)."""

    class Grupo(models.TextChoices):
        FRUTA = "fruta", "Fruta"
        VERDURA = "verdura", "Verdura"
        PROTEINA = "proteina", "Proteína (carne, huevo, leguminosa)"
        CEREAL = "cereal", "Cereal / tubérculo"
        LACTEO = "lacteo", "Lácteo"

    nombre = models.CharField(max_length=100)
    grupo = models.CharField(max_length=10, choices=Grupo.choices)
    edad_minima_meses = models.PositiveSmallIntegerField(
        default=6,
        help_text="Edad mínima recomendada para introducir este alimento (OMS: alimentación complementaria desde los 6 meses).",
    )
    disponible = models.BooleanField(
        default=True,
        help_text="Si está desmarcado, este alimento no se usa en los planes nutricionales generados.",
    )
    notas = models.CharField(
        max_length=200,
        blank=True,
        default="",
        help_text="Ej. 'picar en trozos pequeños para evitar atragantamiento'.",
    )
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["grupo", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["nombre", "grupo"], name="unique_alimento_por_grupo")
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_grupo_display()})"
