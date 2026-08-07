from __future__ import annotations

from apps.who_standards import classify


# --- talla-para-edad (stunting) ---

def test_talla_para_edad_boundaries():
    assert classify.clasificar_talla_para_edad(-3.0)["clasificacion"] == "Talla Baja"
    assert classify.clasificar_talla_para_edad(-3.001)["clasificacion"] == "Talla Baja Severa"
    assert classify.clasificar_talla_para_edad(-2.0)["clasificacion"] == "Normal"
    assert classify.clasificar_talla_para_edad(-2.001)["clasificacion"] == "Talla Baja"
    assert classify.clasificar_talla_para_edad(2.0)["clasificacion"] == "Normal"
    assert classify.clasificar_talla_para_edad(2.001)["clasificacion"] == "Talla Alta"
    assert classify.clasificar_talla_para_edad(2.001)["nivel_alerta"] == "informativo"


# --- peso-para-talla (wasting) ---

def test_peso_para_talla_boundaries():
    assert classify.clasificar_peso_para_talla(-3.0)["clasificacion"] == "Emaciacion Moderada"
    assert classify.clasificar_peso_para_talla(-3.001)["clasificacion"] == "Emaciacion Severa"
    assert classify.clasificar_peso_para_talla(-2.001)["clasificacion"] == "Emaciacion Moderada"
    assert classify.clasificar_peso_para_talla(-2.0)["clasificacion"] == "Normal"
    assert classify.clasificar_peso_para_talla(2.0)["clasificacion"] == "Normal"
    assert classify.clasificar_peso_para_talla(2.001)["clasificacion"] == "Sobrepeso"
    assert classify.clasificar_peso_para_talla(3.0)["clasificacion"] == "Sobrepeso"
    assert classify.clasificar_peso_para_talla(3.001)["clasificacion"] == "Obesidad"


# --- peso-para-edad (underweight) ---

def test_peso_para_edad_boundaries():
    assert classify.clasificar_peso_para_edad(-3.0)["clasificacion"] == "Desnutricion Global Moderada"
    assert classify.clasificar_peso_para_edad(-3.001)["clasificacion"] == "Desnutricion Global Severa"
    assert classify.clasificar_peso_para_edad(-2.001)["clasificacion"] == "Desnutricion Global Moderada"
    assert classify.clasificar_peso_para_edad(-2.0)["clasificacion"] == "Normal"
    assert classify.clasificar_peso_para_edad(5.0)["clasificacion"] == "Normal"  # no upper category


# --- IMC-para-edad ---

def test_imc_para_edad_boundaries():
    assert classify.clasificar_imc_para_edad(-3.001)["clasificacion"] == "Delgadez Severa"
    assert classify.clasificar_imc_para_edad(-2.001)["clasificacion"] == "Delgadez Moderada"
    assert classify.clasificar_imc_para_edad(0.0)["clasificacion"] == "Normal"
    assert classify.clasificar_imc_para_edad(2.001)["clasificacion"] == "Sobrepeso"
    assert classify.clasificar_imc_para_edad(3.001)["clasificacion"] == "Obesidad"


# --- perimetro cefalico ---

def test_perimetro_cefalico_boundaries():
    assert classify.clasificar_perimetro_cefalico(-2.0)["clasificacion"] == "Normal"
    assert classify.clasificar_perimetro_cefalico(-2.001)["clasificacion"] == "Microcefalia"
    assert classify.clasificar_perimetro_cefalico(2.0)["clasificacion"] == "Normal"
    assert classify.clasificar_perimetro_cefalico(2.001)["clasificacion"] == "Macrocefalia"


# --- perimetro braquial / MUAC (absolute cutoff, not z-score driven) ---

def test_perimetro_braquial_absolute_cutoffs():
    # WHO/UNICEF convention: < 11.5 is severe ("critico")
    r_low = classify.clasificar_perimetro_braquial(11.4)
    assert r_low["clasificacion"] == "Critico"
    assert r_low["nivel_alerta"] == "severo"
    assert r_low["es_bypass"] is True

    # 11.5 exactly falls on the "Moderado" side (>= 11.5 is not severe)
    r_boundary = classify.clasificar_perimetro_braquial(11.5)
    assert r_boundary["clasificacion"] == "Moderado"

    r_mid = classify.clasificar_perimetro_braquial(12.0)
    assert r_mid["clasificacion"] == "Moderado"

    r_boundary2 = classify.clasificar_perimetro_braquial(12.5)
    assert r_boundary2["clasificacion"] == "Normal"

    r_high = classify.clasificar_perimetro_braquial(13.0)
    assert r_high["clasificacion"] == "Normal"
    assert r_high["es_bypass"] is True


def test_perimetro_braquial_ignores_zscore_for_classification():
    # Even with a "normal-looking" z-score, cm cutoff drives classification.
    r = classify.clasificar_perimetro_braquial(11.0, z=0.5)
    assert r["clasificacion"] == "Critico"
    assert r["es_bypass"] is True


# --- edema override ---

def test_aplicar_override_edema_forces_severe():
    resultado_normal = {
        "aplica": True,
        "valor_z": 0.2,
        "clasificacion": "Normal",
        "nivel_alerta": "normal",
    }
    resultado = classify.aplicar_override_edema(resultado_normal)
    assert resultado["clasificacion"] == "Emaciacion Severa (con edema)"
    assert resultado["nivel_alerta"] == "severo"
    assert resultado["edema_aplicado"] is True
    # original dict must not be mutated
    assert resultado_normal["clasificacion"] == "Normal"
    assert "edema_aplicado" not in resultado_normal
