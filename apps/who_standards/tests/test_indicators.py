from __future__ import annotations

from apps.who_standards import indicators


def test_talla_para_edad_end_to_end():
    # WHO median (M) for boys at 24 months is 87.1161cm -> should be ~Normal
    r = indicators.talla_para_edad("M", 24, 87.1)
    assert r["aplica"] is True
    assert abs(r["valor_z"]) < 0.1
    assert r["clasificacion"] == "Normal"
    assert r["tabla_usada"] == "lhfa"


def test_peso_para_edad_end_to_end():
    # WHO median for girls at 12 months is ~8.95kg -> Normal
    r = indicators.peso_para_edad("F", 12, 8.9)
    assert r["aplica"] is True
    assert r["clasificacion"] == "Normal"
    assert r["tabla_usada"] == "wfa"


def test_peso_para_talla_end_to_end_normal_no_correction_needed():
    # child under 24mo, measured lying down (age-appropriate) -> no correction
    r = indicators.peso_para_talla("M", 10, 8.4, 70.0, tipo_medicion="acostado")
    assert r["aplica"] is True
    assert r["tabla_usada"] == "wfl"
    assert r["correccion_cm_aplicada"] == 0.0
    assert r["clasificacion"] == "Normal"


def test_peso_para_talla_applies_positive_correction_when_under_24mo_measured_standing():
    # child <24mo but measured standing -> ADD 0.7cm before using length table
    r = indicators.peso_para_talla("M", 10, 8.4, 70.0, tipo_medicion="de_pie")
    assert r["aplica"] is True
    assert r["tabla_usada"] == "wfl"
    assert r["correccion_cm_aplicada"] == 0.7
    assert r["talla_cm_ajustada"] == 70.7


def test_peso_para_talla_applies_negative_correction_when_24mo_or_older_measured_lying():
    # child >=24mo but measured lying down -> SUBTRACT 0.7cm before height table
    r = indicators.peso_para_talla("M", 30, 12.0, 90.0, tipo_medicion="acostado")
    assert r["aplica"] is True
    assert r["tabla_usada"] == "wfh"
    assert r["correccion_cm_aplicada"] == -0.7
    assert r["talla_cm_ajustada"] == 89.3


def test_peso_para_talla_no_correction_when_24mo_or_older_measured_standing():
    r = indicators.peso_para_talla("M", 30, 12.0, 90.0, tipo_medicion="de_pie")
    assert r["correccion_cm_aplicada"] == 0.0
    assert r["talla_cm_ajustada"] == 90.0
    assert r["tabla_usada"] == "wfh"


def test_imc_para_edad_end_to_end():
    r = indicators.imc_para_edad("M", 30, 12.8, 90.0)
    assert r["aplica"] is True
    assert r["tabla_usada"] == "bfa"
    assert r["imc"] == pytest_approx(12.8 / (0.9**2))
    assert r["clasificacion"] in {
        "Normal",
        "Delgadez Moderada",
        "Delgadez Severa",
        "Sobrepeso",
        "Obesidad",
    }


def test_perimetro_cefalico_end_to_end_normal():
    r = indicators.perimetro_cefalico_para_edad("F", 6, 42.2)
    assert r["aplica"] is True
    assert r["tabla_usada"] == "hcfa"
    assert r["clasificacion"] == "Normal"


def test_perimetro_cefalico_no_aplica_outside_age_range():
    r = indicators.perimetro_cefalico_para_edad("F", 70, 48.0)  # >60mo
    assert r["aplica"] is False
    assert r["valor_z"] is None
    assert r["clasificacion"] is None
    assert r["motivo_no_aplica"] is not None

    r2 = indicators.perimetro_cefalico_para_edad("F", -1, 48.0)
    assert r2["aplica"] is False


def test_perimetro_braquial_end_to_end_normal():
    r = indicators.perimetro_braquial_para_edad("M", 20, 14.9)
    assert r["aplica"] is True
    assert r["tabla_usada"] == "acfa"
    assert r["es_bypass"] is True
    assert r["clasificacion"] == "Normal"
    assert r["valor_z"] is not None  # still computed/stored for reference


def test_perimetro_braquial_no_aplica_outside_age_range():
    # acfa table only covers 3-60 months
    r = indicators.perimetro_braquial_para_edad("M", 1, 13.0)
    assert r["aplica"] is False
    assert r["motivo_no_aplica"] is not None

    r2 = indicators.perimetro_braquial_para_edad("M", 61, 13.0)
    assert r2["aplica"] is False


def test_perimetro_braquial_critico_by_absolute_cutoff_even_with_normal_zscore():
    # A very young child with a low MUAC can have a z-score that isn't
    # extreme yet still be clinically "Critico" by the absolute cutoff.
    r = indicators.perimetro_braquial_para_edad("M", 6, 11.0)
    assert r["aplica"] is True
    assert r["clasificacion"] == "Critico"
    assert r["es_bypass"] is True


def pytest_approx(value, rel=1e-6):
    import pytest

    return pytest.approx(value, rel=rel)
