from django.db import migrations

# Sustitutos culturalmente apropiados para la comunidad Kogui (Sierra
# Nevada de Santa Marta), a partir de una lista provista por un contacto
# comunitario/experto (Fredy Jiménez, 2026-09-04) -- transcrita tal como
# fue entregada. Los valores nutricionales (kcal y macros por 100g,
# porción de referencia) son ESTIMACIONES aproximadas de tablas de
# composición de alimentos estándar para las especies identificables; los
# que no se pudieron estimar con confianza (marcados None) se dejan sin
# dato en vez de inventar una cifra -- ver Alimento.notas de cada uno.
#
# (nombre, grupo, edad_minima_meses, notas, region_especifica, disponible,
#  porcion_g, kcal_100g, proteina_g_100g, carbohidratos_g_100g, grasa_g_100g)
NUEVOS_ALIMENTOS = [
    (
        "Arepa de Yuca", "cereal", 8,
        "Reemplazo de la arepa de maíz para la comunidad Kogui -- también puede "
        "prepararse con malanga (mafafa). Aporta carbohidratos de digestión lenta sin "
        "depender del maíz procesado.",
        "kogui", True, 50, 180.0, 1.5, 42.0, 0.3,
    ),
    (
        "Majule (chicha suave de plátano/yuca)", "lacteo", 24,
        "Bebida fermentada tradicional que cumple, en la dieta Kogui, el rol de aporte "
        "de fermentos vivos que en otras dietas cubre el kumis. AVISO: el contenido "
        "alcohólico de una chicha fermentada varía según el tiempo de fermentación -- "
        "no ofrecer a niños pequeños sin que un profesional de salud o un miembro "
        "experto de la comunidad confirme que la preparación específica es apta para "
        "esa edad. Se deja marcado como NO disponible por defecto hasta esa revisión.",
        "kogui", False, 150, None, None, None, None,
    ),
    (
        "Hojas de Batata (Camote)", "verdura", 6,
        "Reemplazo de la acelga para la comunidad Kogui -- hojas jóvenes de batata, de "
        "crecimiento silvestre y cultivado en la Sierra. Cocinar bien y cortar en "
        "trozos pequeños.",
        "kogui", True, 30, 35.0, 3.0, 6.4, 0.4,
    ),
    (
        "Lulo silvestre", "fruta", 8,
        "Reemplazo de la mandarina para la comunidad Kogui, respetando la "
        "estacionalidad de las cuencas de la Sierra.",
        "kogui", True, 60, 28.0, 1.0, 6.0, 0.2,
    ),
    (
        "Guanábana del monte", "fruta", 8,
        "Reemplazo alternativo de la mandarina para la comunidad Kogui. Retirar bien "
        "las semillas antes de dar al niño.",
        "kogui", True, 80, 66.0, 1.0, 16.8, 0.3,
    ),
    (
        "Chaya", "verdura", 8,
        "Reemplazo del brócoli para la comunidad Kogui -- conocida como \"árbol "
        "espinaca\" por sus brotes ricos en hierro y proteína vegetal. Cocinar bien: "
        "las hojas crudas de chaya no deben consumirse.",
        "kogui", True, 30, 28.0, 3.6, 4.2, 0.4,
    ),
    (
        "Guatila (Chayote)", "verdura", 6,
        "Reemplazo alternativo del brócoli para la comunidad Kogui. Cocinar bien y "
        "cortar en trozos pequeños.",
        "kogui", True, 50, 19.0, 0.8, 4.5, 0.1,
    ),
    (
        "Hojas de Blanquita", "verdura", 8,
        "Reemplazo de la espinaca para la comunidad Kogui -- planta de hoja silvestre "
        "identificada por la comunidad, que crece alrededor de los bohíos y chagras. "
        "Información nutricional pendiente de confirmar con la comunidad/un "
        "profesional de nutrición -- no se carga un valor aproximado para evitar una "
        "cifra sin sustento.",
        "kogui", True, None, None, None, None, None,
    ),
    (
        "Verdolaga nativa", "verdura", 8,
        "Reemplazo alternativo de la espinaca para la comunidad Kogui.",
        "kogui", True, 30, 16.0, 1.3, 3.4, 0.1,
    ),
    # Sustitutos alternativos de consumo cotidiano (catálogo general, no
    # restringidos a una comunidad) -- misma fuente.
    (
        "Cazabe de yuca", "cereal", 10,
        "Alternativa a la arepa de maíz. Verificar que esté bien cocido y ofrecer en "
        "trozos pequeños.",
        "", True, 30, 330.0, 1.0, 80.0, 0.5,
    ),
    (
        "Patacón (plátano verde asado)", "cereal", 8,
        "Alternativa a la arepa de maíz -- versión asada, no frita.",
        "", True, 70, 130.0, 1.3, 32.0, 0.4,
    ),
    (
        "Papa criolla", "cereal", 6,
        "Alternativa a la arepa de maíz. Cocinar bien y cortar en trozos pequeños.",
        "", True, 70, 95.0, 2.0, 21.0, 0.1,
    ),
    (
        "Leche de coco", "lacteo", 12,
        "Alternativa al kumis para quien no consume lácteos de vaca -- versión "
        "fresca/diluida, no la enlatada concentrada; alta en grasa saturada, ofrecer "
        "con moderación.",
        "", True, 100, 180.0, 1.8, 3.0, 18.0,
    ),
    (
        "Kale (col rizada)", "verdura", 8,
        "Alternativa a la acelga/espinaca. Cocinar bien y cortar en trozos pequeños.",
        "", True, 40, 35.0, 2.9, 4.4, 1.5,
    ),
    (
        "Hojas de mostaza", "verdura", 8,
        "Alternativa a la acelga/espinaca. Cocinar bien.",
        "", True, 40, 27.0, 2.9, 4.7, 0.4,
    ),
    (
        "Bok Choy (acelga china)", "verdura", 8,
        "Alternativa a la acelga/espinaca. Cocinar bien y cortar en trozos pequeños.",
        "", True, 40, 13.0, 1.5, 1.2, 0.2,
    ),
    (
        "Berros", "verdura", 8,
        "Alternativa a la acelga/espinaca.",
        "", True, 30, 11.0, 2.3, 1.3, 0.1,
    ),
    (
        "Naranja agria", "fruta", 8,
        "Alternativa a la mandarina.",
        "", True, 80, 45.0, 0.9, 11.5, 0.2,
    ),
    (
        "Toronja", "fruta", 8,
        "Alternativa a la mandarina.",
        "", True, 80, 42.0, 0.8, 10.7, 0.1,
    ),
    (
        "Uchuva", "fruta", 8,
        "Alternativa a la mandarina.",
        "", True, 40, 53.0, 1.9, 11.2, 0.2,
    ),
    (
        "Coliflor", "verdura", 8,
        "Alternativa al brócoli. Cocinar bien y cortar en trozos pequeños.",
        "", True, 50, 25.0, 1.9, 5.0, 0.3,
    ),
    (
        "Coles de Bruselas", "verdura", 10,
        "Alternativa al brócoli. Cocinar bien y cortar en trozos pequeños.",
        "", True, 50, 36.0, 2.6, 7.1, 0.3,
    ),
    (
        "Espárragos", "verdura", 10,
        "Alternativa al brócoli. Cocinar bien y cortar en trozos pequeños.",
        "", True, 40, 22.0, 2.4, 4.1, 0.2,
    ),
    (
        "Tarwi", "proteina", 12,
        "Debe remojarse y lavarse varios días antes de cocinar para eliminar el "
        "amargor natural (alcaloides) -- una preparación inadecuada puede ser tóxica. "
        "Cocinar bien, en puré para menores de 12 meses.",
        "", True, 50, 119.0, 15.6, 8.6, 4.5,
    ),
    (
        "Arracacha", "cereal", 8,
        "Alternativa al bore. Cocinar bien y cortar en trozos pequeños.",
        "", True, 70, 108.0, 0.9, 25.0, 0.2,
    ),
]

# Alimentos generales que no son culturalmente apropiados/accesibles para
# la comunidad Kogui según la misma fuente -- se marcan excluido_para_region
# para que no se ofrezcan a esos pacientes, sin quitarlos del catálogo
# general (los sigue viendo cualquier otro paciente).
EXCLUSIONES_KOGUI = [
    ("Arepa de maíz", "cereal"),
    ("Kumis", "lacteo"),
    ("Acelga", "verdura"),
    ("Mandarina", "fruta"),
    ("Brócoli", "verdura"),
    ("Bore", "cereal"),
    ("Espinaca", "verdura"),
]


def sembrar(apps, schema_editor):
    Alimento = apps.get_model("nutrition", "Alimento")
    for (
        nombre, grupo, edad_minima_meses, notas, region_especifica, disponible,
        porcion_g, kcal, proteina, carbohidratos, grasa,
    ) in NUEVOS_ALIMENTOS:
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
    for nombre, grupo in EXCLUSIONES_KOGUI:
        Alimento.objects.filter(nombre=nombre, grupo=grupo).update(excluido_para_region="kogui")


def deshacer(apps, schema_editor):
    Alimento = apps.get_model("nutrition", "Alimento")
    nombres = [n for n, *_ in NUEVOS_ALIMENTOS]
    Alimento.objects.filter(nombre__in=nombres).delete()
    for nombre, grupo in EXCLUSIONES_KOGUI:
        Alimento.objects.filter(nombre=nombre, grupo=grupo).update(excluido_para_region="")


class Migration(migrations.Migration):
    dependencies = [
        ("nutrition", "0006_1_alter_alimento_notas"),
    ]

    operations = [
        migrations.RunPython(sembrar, deshacer),
    ]
