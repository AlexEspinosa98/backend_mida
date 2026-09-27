from rest_framework import serializers

from .models import Alimento


class AlimentoSerializer(serializers.ModelSerializer):
    """CRUD del catálogo (GET/POST/PATCH/DELETE en /api/v1/nutricion/alimentos/).
    Antes solo se podía gestionar desde /admin/nutrition/alimento/ -- esto le da
    al frontend su propia pantalla, sin tener que mandar a nadie al admin."""

    porcion_texto = serializers.ReadOnlyField()
    calorias_por_porcion = serializers.ReadOnlyField()

    class Meta:
        model = Alimento
        fields = [
            "id",
            "nombre",
            "grupo",
            "edad_minima_meses",
            "disponible",
            "notas",
            "region_especifica",
            "excluido_para_region",
            "porcion_referencia_g",
            "unidad_casera",
            "cantidad_casera",
            "descripcion_casera",
            "porcion_texto",
            "calorias_kcal_100g",
            "proteina_g_100g",
            "carbohidratos_g_100g",
            "grasa_g_100g",
            "calorias_por_porcion",
            "creado_en",
            "actualizado_en",
        ]
        read_only_fields = ["id", "creado_en", "actualizado_en"]
