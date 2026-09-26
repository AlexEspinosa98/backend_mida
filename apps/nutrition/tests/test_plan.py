from __future__ import annotations

import pytest

from apps.nutrition.models import Alimento
from apps.nutrition.plan import generar_plan_semanal, resumen_disponibilidad

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _catalogo_limpio():
    """Los tests de rotación necesitan un catálogo conocido y controlado
    -- se limpia el catálogo sembrado por la migración de datos antes de
    cada test para evitar colisiones de nombre y conteos impredecibles."""
    Alimento.objects.all().delete()


def _crear(nombre, grupo, edad_minima_meses=6, disponible=True, **extra):
    return Alimento.objects.create(
        nombre=nombre,
        grupo=grupo,
        edad_minima_meses=edad_minima_meses,
        disponible=disponible,
        **extra,
    )


def test_menor_de_6_meses_no_aplica():
    plan = generar_plan_semanal(4)
    assert plan["aplica"] is False
    assert "lactancia materna exclusiva" in plan["motivo_no_aplica"]
    assert plan["dias"] == []


def test_plan_completo_tiene_7_dias_con_las_4_comidas():
    _crear("Banano", "fruta")
    _crear("Zanahoria", "verdura")
    _crear("Pollo", "proteina")
    _crear("Arroz", "cereal")
    _crear("Yogur", "lacteo")

    plan = generar_plan_semanal(24)
    assert plan["aplica"] is True
    assert len(plan["dias"]) == 7
    dias_nombres = [d["dia"] for d in plan["dias"]]
    assert dias_nombres == ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    for dia in plan["dias"]:
        assert set(dia["comidas"].keys()) == {"Desayuno", "Almuerzo", "Merienda", "Cena"}


def test_rotacion_usa_varios_alimentos_cuando_hay_mas_de_uno():
    _crear("Banano", "fruta")
    _crear("Guayaba", "fruta")
    _crear("Pollo", "proteina")
    _crear("Arroz", "cereal")
    _crear("Zanahoria", "verdura")
    _crear("Yogur", "lacteo")

    plan = generar_plan_semanal(24)
    frutas_usadas = {
        alimento["nombre"]
        for dia in plan["dias"]
        for alimento in dia["comidas"]["Desayuno"]
        if alimento["nombre"] in {"Banano", "Guayaba"}
    }
    # Con 2 frutas disponibles y 7 días, deben rotar -- no debe usarse solo una.
    assert frutas_usadas == {"Banano", "Guayaba"}


def test_alimento_no_disponible_no_se_usa():
    _crear("Banano", "fruta", disponible=False)
    _crear("Guayaba", "fruta", disponible=True)
    _crear("Pollo", "proteina")
    _crear("Arroz", "cereal")
    _crear("Zanahoria", "verdura")
    _crear("Yogur", "lacteo")

    plan = generar_plan_semanal(24)
    nombres_usados = {
        alimento["nombre"]
        for dia in plan["dias"]
        for comida in dia["comidas"].values()
        for alimento in comida
    }
    assert "Banano" not in nombres_usados


def test_alimento_por_debajo_de_edad_minima_no_se_usa():
    _crear("Leche entera", "lacteo", edad_minima_meses=12)
    _crear("Pollo", "proteina")
    _crear("Arroz", "cereal")
    _crear("Zanahoria", "verdura")
    _crear("Banano", "fruta")

    plan = generar_plan_semanal(8)  # menor a 12 meses
    nombres_usados = {
        alimento["nombre"]
        for dia in plan["dias"]
        for comida in dia["comidas"].values()
        for alimento in comida
    }
    assert "Leche entera" not in nombres_usados
    # el grupo lacteo queda sin opciones a esta edad
    assert "lacteo" in plan["grupos_sin_opciones"]


def test_grupo_vacio_no_rompe_el_plan_y_se_reporta():
    # Sin ningún alimento del grupo "proteina" registrado.
    _crear("Banano", "fruta")
    _crear("Arroz", "cereal")
    _crear("Zanahoria", "verdura")
    _crear("Yogur", "lacteo")

    plan = generar_plan_semanal(24)
    assert plan["aplica"] is True
    assert "proteina" in plan["grupos_sin_opciones"]
    for dia in plan["dias"]:
        for alimento in dia["comidas"]["Almuerzo"]:
            assert alimento["nombre"] != ""  # no hay entradas vacías/None colgando


def test_resumen_disponibilidad_respeta_disponible_y_edad():
    _crear("Banano", "fruta", disponible=True)
    _crear("Mango dañado", "fruta", disponible=False)
    _crear("Leche entera", "lacteo", edad_minima_meses=12)

    resumen = resumen_disponibilidad(8)
    assert "Banano" in resumen["fruta"]
    assert "Mango dañado" not in resumen["fruta"]
    assert "Leche entera" not in resumen["lacteo"]


def test_alimento_region_especifica_solo_aparece_para_su_etnia():
    _crear("Banano", "fruta")
    _crear("Fruto Kogui", "fruta", region_especifica="kogui")
    _crear("Pollo", "proteina")
    _crear("Arroz", "cereal")
    _crear("Zanahoria", "verdura")
    _crear("Yogur", "lacteo")

    sin_etnia = resumen_disponibilidad(24)
    assert "Fruto Kogui" not in sin_etnia["fruta"]

    otra_etnia = resumen_disponibilidad(24, etnia="arhuaco")
    assert "Fruto Kogui" not in otra_etnia["fruta"]

    misma_etnia = resumen_disponibilidad(24, etnia="kogui")
    assert "Fruto Kogui" in misma_etnia["fruta"]
    assert "Banano" in misma_etnia["fruta"]  # el catálogo general se sigue ofreciendo también


def test_alimento_excluido_para_region_no_aparece_para_esa_etnia():
    _crear("Kumis", "lacteo", excluido_para_region="kogui")
    _crear("Majule", "lacteo", region_especifica="kogui")
    _crear("Pollo", "proteina")
    _crear("Arroz", "cereal")
    _crear("Zanahoria", "verdura")
    _crear("Banano", "fruta")

    para_kogui = resumen_disponibilidad(24, etnia="kogui")
    assert "Kumis" not in para_kogui["lacteo"]
    assert "Majule" in para_kogui["lacteo"]

    para_otra = resumen_disponibilidad(24, etnia="arhuaco")
    assert "Kumis" in para_otra["lacteo"]  # la exclusión es solo para kogui
    assert "Majule" not in para_otra["lacteo"]  # y el reemplazo es solo para kogui

    sin_etnia = resumen_disponibilidad(24)
    assert "Kumis" in sin_etnia["lacteo"]  # el catálogo general no se ve afectado


def test_alimentos_generales_se_ofrecen_a_cualquier_etnia():
    _crear("Banano", "fruta")
    _crear("Pollo", "proteina")
    _crear("Arroz", "cereal")
    _crear("Zanahoria", "verdura")
    _crear("Yogur", "lacteo")

    resumen = resumen_disponibilidad(24, etnia="kogui")
    assert "Banano" in resumen["fruta"]


def test_totales_nutricionales_por_dia_y_promedio_semanal():
    _crear(
        "Banano", "fruta",
        porcion_referencia_g=100, calorias_kcal_100g=90, proteina_g_100g=1,
        carbohidratos_g_100g=20, grasa_g_100g=0.5,
    )
    _crear(
        "Pollo", "proteina",
        porcion_referencia_g=100, calorias_kcal_100g=160, proteina_g_100g=30,
        carbohidratos_g_100g=0, grasa_g_100g=4,
    )
    _crear(
        "Arroz", "cereal",
        porcion_referencia_g=100, calorias_kcal_100g=130, proteina_g_100g=3,
        carbohidratos_g_100g=28, grasa_g_100g=0.3,
    )
    _crear("Zanahoria", "verdura")  # sin datos nutricionales -> día queda incompleto
    _crear(
        "Yogur", "lacteo",
        porcion_referencia_g=100, calorias_kcal_100g=60, proteina_g_100g=3.5,
        carbohidratos_g_100g=5, grasa_g_100g=3,
    )

    plan = generar_plan_semanal(24)
    lunes = plan["dias"][0]

    banano = lunes["comidas"]["Desayuno"][1]  # Desayuno: cereal, fruta, lacteo
    assert banano["nombre"] == "Banano"
    assert banano["calorias_kcal"] == 90.0
    assert banano["porcion_g"] == 100

    # Zanahoria (sin datos) participa en Almuerzo -> el total del día es incompleto.
    assert lunes["totales_nutricionales"]["datos_completos"] is False
    assert lunes["totales_nutricionales"]["calorias_kcal"] > 0

    assert plan["promedio_diario"] is not None
    assert plan["promedio_diario"]["datos_completos"] is False
    assert plan["promedio_diario"]["calorias_kcal"] > 0


def test_alimento_sin_porcion_referencia_no_calcula_calorias():
    _crear("Banano", "fruta", calorias_kcal_100g=90)  # sin porcion_referencia_g
    _crear("Pollo", "proteina")
    _crear("Arroz", "cereal")
    _crear("Zanahoria", "verdura")
    _crear("Yogur", "lacteo")

    plan = generar_plan_semanal(24)
    banano = plan["dias"][0]["comidas"]["Desayuno"][1]
    assert banano["calorias_kcal"] is None
