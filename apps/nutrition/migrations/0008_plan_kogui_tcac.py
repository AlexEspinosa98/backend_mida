from django.db import migrations

# Esta migración incorpora el "Plan de alimentación para esta semana --
# Adaptado con alimentos propios de la comunidad Kogui" (documento de
# apoyo nutricional entregado, basado a su vez en la Tabla de Composición
# de Alimentos Colombianos -- TCAC/ICBF) al catálogo editable de
# apps/nutrition/plan.py, en dos partes:
#
# 1) CORRECCIONES_TCAC: reemplaza estimaciones aproximadas cargadas en
#    0005_seed_datos_nutricionales.py por los valores reales de la hoja
#    "TCAC" de la Tabla de Composición de Alimentos Colombianos (columnas
#    Energía kcal, Proteína g, Lípidos g, Carbohidratos totales g por
#    100g/100mL), para los alimentos que aparecen en el plan semanal
#    Kogui. Se prioriza el estado de preparación ("cocido/a, sin sal") que
#    coincide con cómo se consume en el plan; donde no hay ese estado en
#    la tabla, se usa "crudo/a" (mismo criterio que ya traía el catálogo).
# 2) NUEVOS_ALIMENTOS_PLAN_KOGUI: agrega alimentos que el plan Kogui usa
#    y que no estaban en el catálogo con esa identidad cultural concreta
#    (gallina criolla y pescado de río, distintos del pollo/pescado
#    genérico ya existente) y el aguacate (grasa saludable mencionada en
#    el plan), con datos también tomados de la TCAC.
#
# (nombre, grupo) -> (porcion_g, kcal_100g, proteina_g_100g, carbohidratos_g_100g, grasa_g_100g)
CORRECCIONES_TCAC = {
    # Fuente TCAC: "Yuca blanca, sin cáscara, cocida, sin sal" (B106)
    ("Yuca", "cereal"): (80, 157.0, 0.7, 36.6, 0.2),
    # Fuente TCAC: "Papa, variedad harinosa, criolla, con cáscara, cocida, sin sal" (P/162)
    ("Papa criolla", "cereal"): (70, 85.0, 1.4, 18.1, 0.0),
    # Fuente TCAC: "Malanga, sin cáscara, cruda" (P064) -- no hay estado cocido en la tabla
    ("Malanga (mafafa)", "cereal"): (80, 120.0, 1.5, 25.8, 0.3),
    # Fuente TCAC: "Batata, sin cáscara, crudo" (B021)
    ("Batata", "cereal"): (80, 99.0, 1.2, 21.9, 0.1),
    # Fuente TCAC: "Platano hartón, maduro, cocido, sin sal" (B088)
    ("Plátano", "cereal"): (80, 130.0, 0.8, 30.1, 0.2),
    # Fuente TCAC: "Plátano colí o guineo verde, crudo" (B084)
    ("Guineo (banano verde)", "cereal"): (80, 128.0, 1.3, 30.3, 0.1),
    # Fuente TCAC: "Maíz mute, cocido, sin sal" (A048) -- mazorca desgranada y cocida
    ("Mazorca (maíz)", "cereal"): (70, 98.0, 2.5, 21.0, 0.5),
    # Fuente TCAC: "Fríjol verde, cocido, con sal" (B045)
    ("Fríjol", "proteina"): (60, 147.0, 9.3, 25.5, 0.4),
    # Fuente TCAC: "Ahuyama, cocida, sin sal" (B005)
    ("Ahuyama", "verdura"): (50, 48.0, 0.7, 8.4, 0.7),
    # Fuente TCAC: "Huevo de gallina, cocido, sin sal" (J003)
    ("Huevo", "proteina"): (50, 145.0, 13.0, 0.0, 10.4),
    # Fuente TCAC: "Guayaba, madura, cruda" (C031)
    ("Guayaba", "fruta"): (60, 71.0, 0.9, 13.4, 0.3),
    # Fuente TCAC: "Mango común, crudo" (C051) -- variedad más cercana a la de la Sierra
    ("Mango", "fruta"): (60, 79.0, 0.6, 17.1, 0.0),
    # Fuente TCAC: promedio "Piña, cruda" (C0xx) / "Piña india, cruda" (P0xx)
    ("Piña", "fruta"): (70, 55.0, 0.55, 12.2, 0.15),
    # Fuente TCAC: "Banano común, crudo" (C010)
    ("Banano", "fruta"): (60, 101.0, 1.5, 22.3, 0.1),
    # Fuente TCAC: "Naranja, cruda" (C062)
    ("Naranja", "fruta"): (80, 41.0, 0.7, 8.8, 0.3),
    # Fuente TCAC: "Mandarina, cruda" (C050)
    ("Mandarina", "fruta"): (70, 54.0, 0.9, 11.4, 0.1),
}

# El plan Kogui incluye explícitamente mandarina como fruta propia de la
# comunidad -- 0007_reemplazos_culturales_kogui.py la había marcado
# excluido_para_region="kogui" (con lulo silvestre/guanábana del monte
# como reemplazo) antes de tener este documento de referencia. Se corrige
# aquí: la mandarina SÍ es parte del plan Kogui documentado, así que deja
# de excluirse (los reemplazos de 0007 quedan disponibles igual, como
# opciones adicionales, no exclusivas).
FRUTAS_YA_NO_EXCLUIDAS_KOGUI = [("Mandarina", "fruta")]

# (nombre, grupo, edad_minima_meses, notas, region_especifica, disponible,
#  porcion_g, kcal_100g, proteina_g_100g, carbohidratos_g_100g, grasa_g_100g)
NUEVOS_ALIMENTOS_PLAN_KOGUI = [
    (
        "Gallina criolla", "proteina", 8,
        "Ave de cría propia de la comunidad (distinta del pollo de granja) -- cocinar bien y "
        "deshilachar o picar finamente, retirando huesos y exceso de piel. Fuente TCAC: "
        "\"Gallina, entera, con piel, cruda\".",
        "kogui", True, 100, 256.0, 18.9, 0.0, 10.0,
    ),
    (
        "Pescado de río", "proteina", 8,
        "Bocachico, mojarra o trucha de río -- revisar muy bien que no queden espinas antes de "
        "servir. Fuente TCAC: \"Bocachico, entero, cocido, sin sal\" (valor representativo del "
        "grupo; mojarra y trucha son nutricionalmente similares).",
        "kogui", True, 80, 138.0, 20.1, 0.0, 6.4,
    ),
    (
        "Aguacate", "fruta", 8,
        "Grasa saludable -- ofrecer 2 a 3 veces por semana, en trozos pequeños o machacado. "
        "Fuente TCAC: promedio \"Aguacate hass, crudo\" / \"Aguacate lorena, crudo\".",
        "", True, 80, 200.0, 1.5, 11.8, 14.8,
    ),
]


def aplicar(apps, schema_editor):
    Alimento = apps.get_model("nutrition", "Alimento")

    for (nombre, grupo), (porcion_g, kcal, proteina, carbohidratos, grasa) in CORRECCIONES_TCAC.items():
        Alimento.objects.filter(nombre=nombre, grupo=grupo).update(
            porcion_referencia_g=porcion_g,
            calorias_kcal_100g=kcal,
            proteina_g_100g=proteina,
            carbohidratos_g_100g=carbohidratos,
            grasa_g_100g=grasa,
        )

    for nombre, grupo in FRUTAS_YA_NO_EXCLUIDAS_KOGUI:
        Alimento.objects.filter(nombre=nombre, grupo=grupo).update(excluido_para_region="")

    for (
        nombre, grupo, edad_minima_meses, notas, region_especifica, disponible,
        porcion_g, kcal, proteina, carbohidratos, grasa,
    ) in NUEVOS_ALIMENTOS_PLAN_KOGUI:
        Alimento.objects.get_or_create(
            nombre=nombre,
            grupo=grupo,
            defaults={
                "edad_minima_meses": edad_minima_meses,
                "notas": notas,
                "region_especifica": region_especifica,
                "disponible": disponible,
                "porcion_referencia_g": porcion_g,
                "calorias_kcal_100g": kcal,
                "proteina_g_100g": proteina,
                "carbohidratos_g_100g": carbohidratos,
                "grasa_g_100g": grasa,
            },
        )


def revertir(apps, schema_editor):
    Alimento = apps.get_model("nutrition", "Alimento")

    for nombre, grupo in FRUTAS_YA_NO_EXCLUIDAS_KOGUI:
        Alimento.objects.filter(nombre=nombre, grupo=grupo).update(excluido_para_region="kogui")

    nombres_nuevos = [n for n, *_ in NUEVOS_ALIMENTOS_PLAN_KOGUI]
    Alimento.objects.filter(nombre__in=nombres_nuevos).delete()

    # No se revierten las correcciones numéricas de CORRECCIONES_TCAC --
    # los valores previos eran estimaciones aproximadas, no un estado
    # intencional a restaurar.


class Migration(migrations.Migration):
    dependencies = [
        ("nutrition", "0007_reemplazos_culturales_kogui"),
    ]

    operations = [
        migrations.RunPython(aplicar, revertir),
    ]
