from django.db import migrations

# Valores de referencia APROXIMADOS (kcal y macronutrientes por 100g/100mL,
# más una porción típica en gramos para un niño pequeño) -- basados en
# tablas de composición de alimentos estándar (equivalentes a USDA
# FoodData Central / ICBF Tabla de Composición de Alimentos Colombianos),
# NO en un análisis de laboratorio de cada alimento puntual. Sirven para
# calcular un estimado del aporte calórico del plan (ver
# apps/nutrition/plan.py), no como dato clínico exacto -- deben ser
# validados/ajustados por un profesional de nutrición antes de un uso
# clínico real. Clave: (nombre, grupo) tal como se sembraron en
# 0002_seed_alimentos.py y 0003_seed_alimentos_comunitarios.py.
#
# (porcion_g, kcal_100g, proteina_g_100g, carbohidratos_g_100g, grasa_g_100g)
DATOS_NUTRICIONALES = {
    # Frutas
    ("Banano", "fruta"): (60, 89, 1.1, 23.0, 0.3),
    ("Guayaba", "fruta"): (60, 68, 2.6, 14.3, 1.0),
    ("Papaya", "fruta"): (80, 43, 0.5, 10.8, 0.3),
    ("Mango", "fruta"): (60, 60, 0.8, 15.0, 0.4),
    ("Naranja", "fruta"): (80, 47, 0.9, 11.8, 0.1),
    ("Mandarina", "fruta"): (70, 53, 0.8, 13.3, 0.3),
    ("Manzana", "fruta"): (60, 52, 0.3, 13.8, 0.2),
    ("Pera", "fruta"): (60, 57, 0.4, 15.2, 0.1),
    ("Melón", "fruta"): (80, 34, 0.8, 8.2, 0.2),
    ("Patilla", "fruta"): (80, 30, 0.6, 7.6, 0.2),
    ("Piña", "fruta"): (70, 50, 0.5, 13.1, 0.1),
    ("Maracuyá", "fruta"): (50, 97, 2.2, 23.4, 0.7),
    # Verduras
    ("Zanahoria", "verdura"): (40, 41, 0.9, 9.6, 0.2),
    ("Ahuyama", "verdura"): (50, 26, 1.0, 6.5, 0.1),
    ("Espinaca", "verdura"): (30, 23, 2.9, 3.6, 0.4),
    ("Acelga", "verdura"): (30, 19, 1.8, 3.7, 0.2),
    ("Habichuela", "verdura"): (40, 31, 1.8, 7.0, 0.1),
    ("Tomate", "verdura"): (40, 18, 0.9, 3.9, 0.2),
    ("Pepino", "verdura"): (40, 15, 0.7, 3.6, 0.1),
    ("Brócoli", "verdura"): (40, 34, 2.8, 6.6, 0.4),
    ("Calabacín", "verdura"): (40, 17, 1.2, 3.1, 0.3),
    # Proteína
    ("Pollo", "proteina"): (30, 165, 31.0, 0.0, 3.6),
    ("Huevo", "proteina"): (50, 143, 12.6, 0.7, 9.5),
    ("Carne de res", "proteina"): (30, 217, 26.0, 0.0, 12.0),
    ("Pescado", "proteina"): (30, 128, 26.0, 0.0, 2.7),
    ("Lenteja", "proteina"): (60, 116, 9.0, 20.1, 0.4),
    ("Fríjol", "proteina"): (60, 127, 8.7, 22.8, 0.5),
    ("Garbanzo", "proteina"): (60, 164, 8.9, 27.4, 2.6),
    # Cereal / tubérculo
    ("Arroz", "cereal"): (60, 130, 2.7, 28.2, 0.3),
    ("Papa", "cereal"): (80, 87, 1.9, 20.1, 0.1),
    ("Yuca", "cereal"): (80, 160, 1.4, 38.1, 0.3),
    ("Plátano", "cereal"): (80, 122, 1.3, 31.9, 0.4),
    ("Avena", "cereal"): (100, 71, 2.5, 12.0, 1.5),
    ("Pasta", "cereal"): (60, 131, 5.0, 25.0, 1.1),
    ("Arepa de maíz", "cereal"): (50, 177, 3.7, 37.0, 1.4),
    ("Ñame", "cereal"): (80, 118, 1.5, 27.9, 0.2),
    ("Malanga (mafafa)", "cereal"): (80, 112, 1.5, 26.5, 0.1),
    ("Batata", "cereal"): (80, 90, 2.0, 20.7, 0.1),
    ("Guineo (banano verde)", "cereal"): (80, 122, 1.3, 31.9, 0.4),
    ("Bore", "cereal"): (80, 112, 1.5, 26.0, 0.1),
    ("Mazorca (maíz)", "cereal"): (70, 96, 3.4, 21.0, 1.5),
    # Lácteo
    ("Leche entera", "lacteo"): (150, 61, 3.2, 4.8, 3.3),
    ("Yogur natural", "lacteo"): (100, 61, 3.5, 4.7, 3.3),
    ("Queso campesino", "lacteo"): (20, 264, 18.0, 3.5, 20.0),
    ("Kumis", "lacteo"): (150, 62, 3.3, 4.7, 3.3),
}


def sembrar_datos_nutricionales(apps, schema_editor):
    Alimento = apps.get_model("nutrition", "Alimento")
    for (nombre, grupo), (porcion_g, kcal, proteina, carbohidratos, grasa) in DATOS_NUTRICIONALES.items():
        Alimento.objects.filter(nombre=nombre, grupo=grupo).update(
            porcion_referencia_g=porcion_g,
            calorias_kcal_100g=kcal,
            proteina_g_100g=proteina,
            carbohidratos_g_100g=carbohidratos,
            grasa_g_100g=grasa,
        )


def limpiar_datos_nutricionales(apps, schema_editor):
    Alimento = apps.get_model("nutrition", "Alimento")
    for nombre, grupo in DATOS_NUTRICIONALES:
        Alimento.objects.filter(nombre=nombre, grupo=grupo).update(
            porcion_referencia_g=None,
            calorias_kcal_100g=None,
            proteina_g_100g=None,
            carbohidratos_g_100g=None,
            grasa_g_100g=None,
        )


class Migration(migrations.Migration):
    dependencies = [
        ("nutrition", "0004_alimento_calorias_kcal_100g_and_more"),
    ]

    operations = [
        migrations.RunPython(sembrar_datos_nutricionales, limpiar_datos_nutricionales),
    ]
