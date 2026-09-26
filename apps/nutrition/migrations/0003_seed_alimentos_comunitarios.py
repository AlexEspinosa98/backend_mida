from django.db import migrations

# Alimentos cercanos y accesibles para las comunidades del Caribe
# colombiano y la Sierra Nevada de Santa Marta (contexto Kogui/Arhuaco de
# apps/who_standards/local_patterns.py) -- se agregan aparte de
# 0002_seed_alimentos.py (ya aplicada) en vez de editarla, siguiendo el
# mismo patrón de esa migración. Todos son fuentes altas en carbohidratos,
# de bajo costo y fácil acceso local, para que el plan nutricional
# generado (apps/nutrition/plan.py) pueda sugerir opciones que la familia
# realmente encuentre y pueda comprar o cultivar cerca.
ALIMENTOS_SEMILLA = [
    # (nombre, grupo, edad_minima_meses, notas)
    ("Ñame", "cereal", 6, "Cocinar bien y cortar en trozos pequeños."),
    ("Malanga (mafafa)", "cereal", 6, "Cocinar bien y cortar en trozos pequeños."),
    ("Batata", "cereal", 6, ""),
    ("Guineo (banano verde)", "cereal", 6, "Cocinar bien antes de servir."),
    ("Bore", "cereal", 8, "Cocinar bien y cortar en trozos pequeños."),
    ("Mazorca (maíz)", "cereal", 8, "Desgranar y cocinar bien para menores de 12 meses."),
]


def sembrar_alimentos(apps, schema_editor):
    Alimento = apps.get_model("nutrition", "Alimento")
    for nombre, grupo, edad_minima_meses, notas in ALIMENTOS_SEMILLA:
        Alimento.objects.get_or_create(
            nombre=nombre,
            grupo=grupo,
            defaults={
                "edad_minima_meses": edad_minima_meses,
                "notas": notas,
                "disponible": True,
            },
        )


def eliminar_alimentos_semilla(apps, schema_editor):
    Alimento = apps.get_model("nutrition", "Alimento")
    nombres = [nombre for nombre, _, _, _ in ALIMENTOS_SEMILLA]
    Alimento.objects.filter(nombre__in=nombres).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("nutrition", "0002_seed_alimentos"),
    ]

    operations = [
        migrations.RunPython(sembrar_alimentos, eliminar_alimentos_semilla),
    ]
