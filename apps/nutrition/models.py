from django.db import models

from apps.patients.models import Paciente

# Comunidades a las que un alimento puede restringirse (ver `region_especifica`
# abajo). Se reutiliza Paciente.Etnia como única fuente de verdad -- se
# excluye NINGUNA porque no es una comunidad, es "sin etnia registrada".
REGIONES_ESPECIFICAS_CHOICES = [
    choice for choice in Paciente.Etnia.choices if choice[0] != Paciente.Etnia.NINGUNA
]

# (singular, plural) de cada unidad casera -- Alimento.UnidadCasera.choices solo
# tiene el singular (para el <select> del admin), la pluralización real para el
# texto del reporte vive acá.
_UNIDAD_CASERA_TEXTO = {
    "cucharada": ("cucharada", "cucharadas"),
    "punado": ("puñado", "puñados"),
    "pizca": ("pizca", "pizcas"),
    "vaso_agua": ("vaso de agua", "vasos de agua"),
    "chorro": ("chorro", "chorros"),
    "unidad": ("unidad", "unidades"),
}


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
    # TextField, no CharField: notas reales llegan a >400 caracteres (ej. advertencias de
    # seguridad clínica sobre preparación/edad mínima para alimentos comunitarios como la
    # chicha fermentada, migración 0007) -- un CharField(200) truncaba contenido de seguridad,
    # nunca solo el ejemplo corto del help_text de abajo.
    notas = models.TextField(
        blank=True,
        default="",
        help_text="Ej. 'picar en trozos pequeños para evitar atragantamiento'.",
    )
    region_especifica = models.CharField(
        max_length=10,
        choices=REGIONES_ESPECIFICAS_CHOICES,
        blank=True,
        default="",
        help_text=(
            "Dejar vacío = disponible para cualquier paciente (catálogo general). Si se "
            "marca una comunidad (ej. Kogui), este alimento SOLO se ofrece además en el "
            "plan de pacientes de esa etnia -- no reemplaza el catálogo general, que se "
            "sigue ofreciendo a todos los pacientes tengan o no una etnia registrada."
        ),
    )
    excluido_para_region = models.CharField(
        max_length=10,
        choices=REGIONES_ESPECIFICAS_CHOICES,
        blank=True,
        default="",
        help_text=(
            "Si se marca una comunidad, este alimento (aunque esté en el catálogo "
            "general) NO se ofrece a pacientes de esa etnia -- para alimentos que, pese "
            "a estar disponibles en general, no son culturalmente apropiados o accesibles "
            "para esa comunidad en particular. Use junto con `region_especifica` en el "
            "alimento de reemplazo correspondiente."
        ),
    )
    porcion_referencia_g = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Tamaño de una porción de referencia para un niño pequeño, en gramos (o mL para líquidos). Se usa para calcular el aporte calórico del plan -- se sigue guardando aunque el reporte muestre la medida casera (ver campos de abajo), porque el cálculo de calorías/proteína del plan necesita gramos.",
    )

    class UnidadCasera(models.TextChoices):
        CUCHARADA = "cucharada", "Cucharada"
        PUNADO = "punado", "Puñado"
        PIZCA = "pizca", "Pizca"
        VASO_AGUA = "vaso_agua", "Vaso de agua"
        CHORRO = "chorro", "Chorro"
        UNIDAD = "unidad", "Unidad / tamaño (ej. \"1 arepa pequeña\")"

    # Medida casera para mostrar en el plan/PDF en vez de (o junto a) los gramos --
    # pedido por Ines + nutricionista para adaptar el plan a alimentos de la
    # comunidad Kogui. Todos opcionales: mientras no se llenen, el reporte sigue
    # mostrando solo gramos (comportamiento de hoy) -- el nutricionista los va
    # completando alimento por alimento desde /admin/.
    unidad_casera = models.CharField(max_length=15, choices=UnidadCasera.choices, blank=True, default="")
    cantidad_casera = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Ej. 2 (para \"2 cucharadas\"). Si se deja vacío con una unidad seleccionada, se asume 1.",
    )
    descripcion_casera = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text=(
            "Texto libre que reemplaza cantidad+unidad para casos que no encajan en el "
            "patrón simple (ej. \"1 arepa pequeña\", \"medio plátano\"). Si se llena, tiene "
            "prioridad sobre unidad_casera/cantidad_casera."
        ),
    )

    calorias_kcal_100g = models.DecimalField(
        max_digits=5,
        decimal_places=1,
        null=True,
        blank=True,
        help_text="Energía por cada 100g/100mL de este alimento, en kcal -- valor de referencia aproximado (tabla de composición de alimentos estándar), no un análisis de laboratorio de este alimento en particular.",
    )
    proteina_g_100g = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    carbohidratos_g_100g = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    grasa_g_100g = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["grupo", "nombre"]
        constraints = [
            models.UniqueConstraint(fields=["nombre", "grupo"], name="unique_alimento_por_grupo")
        ]

    def __str__(self):
        return f"{self.nombre} ({self.get_grupo_display()})"

    @property
    def calorias_por_porcion(self) -> float | None:
        if self.calorias_kcal_100g is None or not self.porcion_referencia_g:
            return None
        return round(float(self.calorias_kcal_100g) * self.porcion_referencia_g / 100, 1)

    @property
    def porcion_texto(self) -> str | None:
        """Texto de porción para mostrar en el plan/PDF: medida casera + gramos
        entre paréntesis cuando hay medida casera cargada (ej. "2 cucharadas
        (≈ 30 g)"); solo gramos si no se ha cargado ninguna medida casera aún
        (comportamiento de hoy, sin romper nada mientras el nutricionista va
        completando el catálogo)."""
        texto_casero = None
        if self.descripcion_casera:
            texto_casero = self.descripcion_casera
        elif self.unidad_casera:
            singular, plural = _UNIDAD_CASERA_TEXTO[self.unidad_casera]
            cantidad = self.cantidad_casera
            if cantidad is None or cantidad == 1:
                texto_casero = f"1 {singular}"
            else:
                texto_casero = f"{cantidad:g} {plural}"

        if not self.porcion_referencia_g:
            return texto_casero

        gramos_texto = f"{self.porcion_referencia_g} g"
        if texto_casero:
            return f"{texto_casero} (≈ {gramos_texto})"
        return gramos_texto
