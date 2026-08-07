from __future__ import annotations

import pytest

from apps.who_standards import local_patterns


def test_etnia_sin_patron_local_devuelve_none():
    assert local_patterns.talla_para_edad_comunitaria("ninguna", "F", 30, 80.0, 90.0) is None
    assert local_patterns.talla_para_edad_comunitaria(None, "F", 30, 80.0, 90.0) is None
    assert local_patterns.peso_para_edad_comunitario("otra_etnia", "M", 30, 10.0, 12.0) is None


def test_talla_comunitaria_en_meseta_kogui():
    # A los 24 meses (fin de la rampa), el offset completo ya se aplica.
    r = local_patterns.talla_para_edad_comunitaria("kogui", "F", 24, 76.0, 87.0)
    assert r is not None
    assert r["offset_aplicado_cm"] == pytest.approx(-10.77, abs=1e-6)
    assert r["mediana_comunitaria_cm"] == pytest.approx(87.0 - 10.77)
    assert r["valor_z"] == pytest.approx((76.0 - (87.0 - 10.77)) / 8.60)


def test_talla_comunitaria_rampa_a_mitad():
    # A los 12 meses (mitad de la rampa de 24 meses), solo la mitad del offset.
    r = local_patterns.talla_para_edad_comunitaria("kogui", "M", 12, 70.0, 75.0)
    assert r is not None
    assert r["offset_aplicado_cm"] == pytest.approx(-11.10 / 2)


def test_talla_comunitaria_recien_nacido_sin_offset():
    r = local_patterns.talla_para_edad_comunitaria("arhuaco", "F", 0, 50.0, 49.0)
    assert r is not None
    assert r["offset_aplicado_cm"] == pytest.approx(0.0)
    assert r["mediana_comunitaria_cm"] == pytest.approx(49.0)


def test_peso_comunitario_usa_sd_especifica_por_etnia_sexo():
    r = local_patterns.peso_para_edad_comunitario("arhuaco", "M", 24, 10.0, 12.0)
    assert r is not None
    assert r["offset_aplicado_kg"] == pytest.approx(-1.24)
    esperado_mediana = 12.0 - 1.24
    assert r["valor_z"] == pytest.approx((10.0 - esperado_mediana) / 0.79)


def test_indicadores_sin_patron_local_no_se_ven_afectados():
    # imc/pt/pb/pc no tienen función comunitaria expuesta -- confirmamos
    # que el módulo simplemente no ofrece esas funciones (decisión
    # explícita: el estudio dice que ya son comparables a la OMS).
    assert not hasattr(local_patterns, "imc_para_edad_comunitario")
    assert not hasattr(local_patterns, "peso_para_talla_comunitario")
