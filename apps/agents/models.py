from django.db import models


class PromptSistema(models.Model):
    """System prompt de cada nodo del grafo que usa un LLM (ver
    apps/agents/nodes/) -- editable desde /admin/ sin tocar código ni
    redesplegar. `obtener_texto()` en apps/agents/prompts.py lee estos
    registros; si no existe uno para una `clave` dada (BD sin sembrar,
    fila borrada, o `activo=False`), se usa el texto por defecto fijado
    en código como respaldo -- el sistema nunca queda sin system prompt.
    """

    class Clave(models.TextChoices):
        SINTESIS_CLINICA = "sintesis_clinica", "Síntesis clínica (reporte técnico)"
        SINTESIS_FAMILIAR = "sintesis_familiar", "Síntesis familiar (reporte para la familia)"
        TIPS_NUTRICION = "tips_nutricion", "Consejos del plan de alimentación"

    clave = models.CharField(
        max_length=30,
        choices=Clave.choices,
        unique=True,
        help_text="Qué nodo del asistente usa este system prompt -- no se puede repetir.",
    )
    contenido = models.TextField(
        help_text="Texto completo del system prompt enviado al LLM antes del mensaje del usuario."
    )
    orden = models.PositiveSmallIntegerField(
        default=0,
        help_text="Orden en que se muestra este prompt en /admin/ -- se puede reordenar sin afectar el funcionamiento del asistente.",
    )
    activo = models.BooleanField(
        default=True,
        help_text="Si está desmarcado, el nodo correspondiente usa el texto por defecto de respaldo en vez de este.",
    )
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["orden", "clave"]
        verbose_name = "Prompt del sistema"
        verbose_name_plural = "Prompts del sistema"

    def __str__(self):
        return self.get_clave_display()
