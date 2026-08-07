from django.db import migrations

# Catálogo inicial (contexto colombiano) para que el plan nutricional no
# arranque vacío -- el administrador lo edita libremente después desde
# /admin/nutrition/alimento/ (agregar, quitar, marcar no disponible, etc.).
ALIMENTOS_SEMILLA = [
    # (nombre, grupo, edad_minima_meses, notas)
    ("Banano", "fruta", 6, ""),
    ("Guayaba", "fruta", 6, ""),
    ("Papaya", "fruta", 6, ""),
    ("Mango", "fruta", 6, ""),
    ("Naranja", "fruta", 6, ""),
    ("Mandarina", "fruta", 8, ""),
    ("Manzana", "fruta", 6, "Rallar o cocinar para niños menores de 12 meses."),
    ("Pera", "fruta", 6, "Rallar o cocinar para niños menores de 12 meses."),
    ("Melón", "fruta", 6, ""),
    ("Patilla", "fruta", 6, ""),
    ("Piña", "fruta", 8, ""),
    ("Maracuyá", "fruta", 8, ""),
    ("Zanahoria", "verdura", 6, "Cocinar bien y cortar en trozos pequeños."),
    ("Ahuyama", "verdura", 6, ""),
    ("Espinaca", "verdura", 6, ""),
    ("Acelga", "verdura", 6, ""),
    ("Habichuela", "verdura", 8, "Cocinar bien y cortar en trozos pequeños."),
    ("Tomate", "verdura", 6, ""),
    ("Pepino", "verdura", 10, ""),
    ("Brócoli", "verdura", 8, "Cocinar bien y cortar en trozos pequeños."),
    ("Calabacín", "verdura", 6, ""),
    ("Pollo", "proteina", 6, ""),
    ("Huevo", "proteina", 6, ""),
    ("Carne de res", "proteina", 6, "Picar finamente o moler."),
    ("Pescado", "proteina", 6, "Revisar cuidadosamente que no tenga espinas."),
    ("Lenteja", "proteina", 6, "Cocinar bien, en puré para menores de 12 meses."),
    ("Fríjol", "proteina", 8, "Cocinar bien, en puré para menores de 12 meses."),
    ("Garbanzo", "proteina", 8, "Cocinar bien, en puré para menores de 12 meses."),
    ("Arroz", "cereal", 6, ""),
    ("Papa", "cereal", 6, ""),
    ("Yuca", "cereal", 6, ""),
    ("Plátano", "cereal", 6, ""),
    ("Avena", "cereal", 6, ""),
    ("Pasta", "cereal", 8, ""),
    ("Arepa de maíz", "cereal", 8, ""),
    ("Leche entera", "lacteo", 12, "Antes de los 12 meses, la leche materna o fórmula sigue siendo la principal fuente láctea."),
    ("Yogur natural", "lacteo", 8, "Sin azúcar añadida."),
    ("Queso campesino", "lacteo", 8, ""),
    ("Kumis", "lacteo", 10, ""),
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
        ("nutrition", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sembrar_alimentos, eliminar_alimentos_semilla),
    ]
