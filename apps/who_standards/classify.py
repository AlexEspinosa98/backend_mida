"""WHO-standard clinical classification bands, derived from a computed
z-score (or, for MUAC, from an absolute cm cutoff instead).

Pure Python -- no Django imports.
"""
from __future__ import annotations

from typing import TypedDict


class Clasificacion(TypedDict, total=False):
    clasificacion: str
    nivel_alerta: str  # 'normal' | 'alerta' | 'severo' | 'informativo'
    es_bypass: bool  # True when classification came from an absolute cutoff, not z-score


def clasificar_talla_para_edad(z: float) -> Clasificacion:
    """Stunting / talla-para-edad (T/E)."""
    if z < -3:
        return {"clasificacion": "Talla Baja Severa", "nivel_alerta": "severo"}
    if z < -2:
        return {"clasificacion": "Talla Baja", "nivel_alerta": "alerta"}
    if z <= 2:
        return {"clasificacion": "Normal", "nivel_alerta": "normal"}
    return {"clasificacion": "Talla Alta", "nivel_alerta": "informativo"}


def clasificar_peso_para_talla(z: float) -> Clasificacion:
    """Wasting / peso-para-talla (P/T)."""
    if z < -3:
        return {"clasificacion": "Emaciacion Severa", "nivel_alerta": "severo"}
    if z < -2:
        return {"clasificacion": "Emaciacion Moderada", "nivel_alerta": "alerta"}
    if z <= 2:
        return {"clasificacion": "Normal", "nivel_alerta": "normal"}
    if z <= 3:
        return {"clasificacion": "Sobrepeso", "nivel_alerta": "alerta"}
    return {"clasificacion": "Obesidad", "nivel_alerta": "severo"}


def clasificar_peso_para_edad(z: float) -> Clasificacion:
    """Underweight / peso-para-edad (P/E). WHO does not define an
    overweight/upper category for this indicator alone."""
    if z < -3:
        return {"clasificacion": "Desnutricion Global Severa", "nivel_alerta": "severo"}
    if z < -2:
        return {"clasificacion": "Desnutricion Global Moderada", "nivel_alerta": "alerta"}
    return {"clasificacion": "Normal", "nivel_alerta": "normal"}


def clasificar_imc_para_edad(z: float) -> Clasificacion:
    """BMI-for-age (IMC/E). Same bands as peso-para-talla."""
    if z < -3:
        return {"clasificacion": "Delgadez Severa", "nivel_alerta": "severo"}
    if z < -2:
        return {"clasificacion": "Delgadez Moderada", "nivel_alerta": "alerta"}
    if z <= 2:
        return {"clasificacion": "Normal", "nivel_alerta": "normal"}
    if z <= 3:
        return {"clasificacion": "Sobrepeso", "nivel_alerta": "alerta"}
    return {"clasificacion": "Obesidad", "nivel_alerta": "severo"}


def clasificar_perimetro_cefalico(z: float) -> Clasificacion:
    """Head circumference-for-age (PC/E)."""
    if z < -2:
        return {"clasificacion": "Microcefalia", "nivel_alerta": "alerta"}
    if z <= 2:
        return {"clasificacion": "Normal", "nivel_alerta": "normal"}
    return {"clasificacion": "Macrocefalia", "nivel_alerta": "alerta"}


def clasificar_perimetro_braquial(pb_cm: float, z: float | None = None) -> Clasificacion:
    """MUAC / perimetro braquial-for-age (PB/E).

    Classification is driven by the ABSOLUTE cm cutoff (WHO/UNICEF
    convention), NOT by the z-score -- a child can have a "normal" z-score
    for their age but still be in absolute danger, which is exactly why
    MUAC is used as a rapid community screening tool independent of age.

    Cutoffs (WHO/UNICEF joint statement on severe acute malnutrition):
        < 11.5 cm            -> "Critico" (desnutricion aguda severa)
        11.5 cm <= x < 12.5cm -> "Moderado" (riesgo)
        >= 12.5 cm            -> "Normal"

    The z-score (if provided) is still stored for reference/audit but must
    NOT be used to override the cm-based classification -- callers should
    check `es_bypass=True` to know this result did not come from the LMS
    z-score bands.
    """
    if pb_cm < 11.5:
        clasificacion = "Critico"
        nivel_alerta = "severo"
    elif pb_cm < 12.5:
        clasificacion = "Moderado"
        nivel_alerta = "alerta"
    else:
        clasificacion = "Normal"
        nivel_alerta = "normal"
    return {
        "clasificacion": clasificacion,
        "nivel_alerta": nivel_alerta,
        "es_bypass": True,
    }


def aplicar_override_edema(resultado_peso_talla: dict) -> dict:
    """Given a peso_para_talla (P/T, wasting) result dict, force it to the
    most severe classification when bilateral pitting edema is present.

    Bilateral edema is, by WHO/UNICEF definition, kwashiorkor-type severe
    acute malnutrition REGARDLESS of the weight-for-height z-score -- a
    child with edema and an otherwise "normal" P/T z-score is still severely
    malnourished (the edema itself is fluid retention masking true tissue
    wasting). This function does not decide whether edema is present -- the
    caller (a later LangGraph clinical-assessment node) passes that flag in
    after clinical exam; this module only implements the override rule.

    This function does NOT mutate the input dict -- it returns a new dict.
    """
    resultado = dict(resultado_peso_talla)
    resultado["clasificacion"] = "Emaciacion Severa (con edema)"
    resultado["nivel_alerta"] = "severo"
    resultado["edema_aplicado"] = True
    return resultado
