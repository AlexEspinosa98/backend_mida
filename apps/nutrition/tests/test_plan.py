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


def _crear(nombre, grupo, edad_minima_meses=6, disponible=True):
    return Alimento.objects.create(
        nombre=nombre, grupo=grupo, edad_minima_meses=edad_minima_meses, disponible=disponible
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
