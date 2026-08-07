"""One function per WHO anthropometric indicator. Each function computes an
LMS z-score against the appropriate WHO table and attaches its clinical
classification (apps.who_standards.classify).

Pure Python -- no Django imports. Every function returns a plain dict (never
raises for "out of range" -- that's a normal clinical scenario, e.g. an
indicator "no aplica" at a given age, not a programming error).

Return dict shape (all functions):
    {
        "aplica": bool,
        "valor_z": float | None,
        "x_input": float,               # the value actually looked up (post any correction)
        "tabla_usada": str | None,       # e.g. "lhfa", "wfl", "wfh"
        "edad_meses": float,
        "clasificacion": str | None,
        "nivel_alerta": str | None,
        "motivo_no_aplica": str | None,  # populated only when aplica=False
        ... indicator-specific extra keys (es_bypass, correccion_cm_aplicada, etc.)
    }
"""
from __future__ import annotations

from typing import Literal

from apps.who_standards import classify
from apps.who_standards.interpolate import OutOfRangeError, get_lms
from apps.who_standards.lms import compute_zscore

TipoMedicion = Literal["acostado", "de_pie"]

# WHO recumbent-length <-> standing-height correction, in cm.
#
# Confirmed via WHO-derived secondary sources (WebSearch summary of WHO
# Multicentre Growth Reference Study methodology; the primary WHO PDF
# (anthro-pc-manual) could not be parsed directly in this session due to a
# binary/encoding fetch issue, so this is NOT a direct primary-source quote
# -- flag for a second look / verification against the primary WHO technical
# report before this goes near a real patient):
#
#   - Child < 24 months, measured STANDING (should have been recumbent):
#     ADD 0.7cm to the measured value before using the length-based table.
#   - Child >= 24 months, measured LYING DOWN / recumbent (should have been
#     standing): SUBTRACT 0.7cm from the measured value before using the
#     height-based table.
#
# Rationale: standing height reads ~0.7cm SHORTER than recumbent length for
# the same child (gravity/spinal compression), so converting standing->length
# means adding back what was "lost", and converting length->height means
# subtracting the extra the child gained by lying down.
CORRECCION_LONGITUD_TALLA_CM = 0.7

EDAD_CORTE_MESES = 24  # WHO convention: <24mo recumbent, >=24mo standing


def _no_aplica(motivo: str, x_input: float, edad_meses: float, tabla: str | None = None) -> dict:
    return {
        "aplica": False,
        "valor_z": None,
        "x_input": x_input,
        "tabla_usada": tabla,
        "edad_meses": edad_meses,
        "clasificacion": None,
        "nivel_alerta": None,
        "motivo_no_aplica": motivo,
    }


def talla_para_edad(sexo: str, edad_meses: float, talla_cm: float) -> dict:
    """Talla/longitud-para-edad (stunting). Uses `lhfa_*`.

    Assumes talla_cm was measured using the age-appropriate WHO convention
    (recumbent length if edad_meses < 24, standing height if >= 24) -- the
    lhfa table itself is spliced from a recumbent-length model for months
    <24 and a standing-height model for months >=24 (see PROVENANCE.md).
    This function does not take a tipo_medicion argument; if the caller
    needs to correct for a mismatched measurement convention, apply the
    0.7cm correction (see CORRECCION_LONGITUD_TALLA_CM) to talla_cm before
    calling this function.
    """
    try:
        L, M, S = get_lms("lhfa", sexo, edad_meses)
    except OutOfRangeError:
        return _no_aplica(
            "edad fuera del rango cubierto por el estandar OMS talla-para-edad (0-60 meses)",
            talla_cm,
            edad_meses,
            "lhfa",
        )
    z = compute_zscore(talla_cm, L, M, S)
    resultado = {
        "aplica": True,
        "valor_z": z,
        "x_input": talla_cm,
        "tabla_usada": "lhfa",
        "edad_meses": edad_meses,
        "motivo_no_aplica": None,
        "mediana_oms": M,
    }
    resultado.update(classify.clasificar_talla_para_edad(z))
    return resultado


def peso_para_edad(sexo: str, edad_meses: float, peso_kg: float) -> dict:
    """Peso-para-edad (underweight). Uses `wfa_*`."""
    try:
        L, M, S = get_lms("wfa", sexo, edad_meses)
    except OutOfRangeError:
        return _no_aplica(
            "edad fuera del rango cubierto por el estandar OMS peso-para-edad (0-60 meses)",
            peso_kg,
            edad_meses,
            "wfa",
        )
    z = compute_zscore(peso_kg, L, M, S)
    resultado = {
        "aplica": True,
        "valor_z": z,
        "x_input": peso_kg,
        "tabla_usada": "wfa",
        "edad_meses": edad_meses,
        "motivo_no_aplica": None,
        "mediana_oms": M,
    }
    resultado.update(classify.clasificar_peso_para_edad(z))
    return resultado


def peso_para_talla(
    sexo: str,
    edad_meses: float,
    peso_kg: float,
    talla_cm: float,
    tipo_medicion: TipoMedicion,
) -> dict:
    """Peso-para-talla/longitud (wasting). Uses `wfl_*_0_2y` (recumbent
    length) or `wfh_*_2_5y` (standing height) depending on the CHILD'S AGE
    (not which table nominally "covers" the raw cm value) -- WHO convention:
    < 24 months -> should be measured lying down, use the length table;
    >= 24 months -> should be measured standing, use the height table.

    If tipo_medicion does not match the age-appropriate convention, applies
    the WHO 0.7cm recumbent/standing correction before doing the LMS lookup.
    See CORRECCION_LONGITUD_TALLA_CM docstring above for the direction of
    this correction and its verification status (WebSearch-confirmed, not a
    primary-source PDF quote -- flagged for a second look).
    """
    edad_apropiada: TipoMedicion = "acostado" if edad_meses < EDAD_CORTE_MESES else "de_pie"
    correccion_aplicada = 0.0

    if edad_meses < EDAD_CORTE_MESES:
        tabla = "wfl"
        if tipo_medicion == "de_pie":
            # measured standing but we need recumbent length -> add 0.7cm
            correccion_aplicada = CORRECCION_LONGITUD_TALLA_CM
        talla_ajustada = talla_cm + correccion_aplicada
    else:
        tabla = "wfh"
        if tipo_medicion == "acostado":
            # measured lying down but we need standing height -> subtract 0.7cm
            correccion_aplicada = -CORRECCION_LONGITUD_TALLA_CM
        talla_ajustada = talla_cm + correccion_aplicada

    try:
        L, M, S = get_lms(tabla, sexo, talla_ajustada)
    except OutOfRangeError:
        return _no_aplica(
            "longitud/talla (ajustada) fuera del rango cubierto por el estandar OMS peso-para-talla",
            talla_ajustada,
            edad_meses,
            tabla,
        )
    z = compute_zscore(peso_kg, L, M, S)
    resultado = {
        "aplica": True,
        "valor_z": z,
        "x_input": peso_kg,
        "tabla_usada": tabla,
        "edad_meses": edad_meses,
        "motivo_no_aplica": None,
        "tipo_medicion_reportado": tipo_medicion,
        "tipo_medicion_esperado_para_edad": edad_apropiada,
        "correccion_cm_aplicada": correccion_aplicada,
        "talla_cm_ajustada": talla_ajustada,
    }
    resultado.update(classify.clasificar_peso_para_talla(z))
    return resultado


def imc_para_edad(sexo: str, edad_meses: float, peso_kg: float, talla_cm: float) -> dict:
    """IMC/BMI-para-edad. BMI = kg / (m^2), then LMS lookup against `bfa_*`."""
    talla_m = talla_cm / 100.0
    imc = peso_kg / (talla_m**2)
    try:
        L, M, S = get_lms("bfa", sexo, edad_meses)
    except OutOfRangeError:
        return _no_aplica(
            "edad fuera del rango cubierto por el estandar OMS IMC-para-edad (0-60 meses)",
            imc,
            edad_meses,
            "bfa",
        )
    z = compute_zscore(imc, L, M, S)
    resultado = {
        "aplica": True,
        "valor_z": z,
        "x_input": imc,
        "tabla_usada": "bfa",
        "edad_meses": edad_meses,
        "motivo_no_aplica": None,
        "imc": imc,
    }
    resultado.update(classify.clasificar_imc_para_edad(z))
    return resultado


def perimetro_cefalico_para_edad(sexo: str, edad_meses: float, pc_cm: float) -> dict:
    """Perimetro cefalico-para-edad (head circumference). Uses `hcfa_*`.
    Returns aplica=False (not an exception) if edad_meses is outside the
    0-60 month range covered by the WHO table.
    """
    try:
        L, M, S = get_lms("hcfa", sexo, edad_meses)
    except OutOfRangeError:
        return _no_aplica(
            "edad fuera del rango cubierto por el estandar OMS perimetro-cefalico (0-60 meses)",
            pc_cm,
            edad_meses,
            "hcfa",
        )
    z = compute_zscore(pc_cm, L, M, S)
    resultado = {
        "aplica": True,
        "valor_z": z,
        "x_input": pc_cm,
        "tabla_usada": "hcfa",
        "edad_meses": edad_meses,
        "motivo_no_aplica": None,
    }
    resultado.update(classify.clasificar_perimetro_cefalico(z))
    return resultado


def perimetro_braquial_para_edad(sexo: str, edad_meses: float, pb_cm: float) -> dict:
    """Perimetro braquial-para-edad / MUAC. Uses `acfa_*`, which covers
    3-60 months (confirmed by inspection -- see PROVENANCE.md; the "3-5" in
    WHO's own raw filename is misleading, it does NOT mean 3-5 years).
    Returns aplica=False (not an exception) if edad_meses is outside that
    3-60 month range.

    Classification comes from the absolute cm cutoff (see
    classify.clasificar_perimetro_braquial), not from the z-score -- the
    z-score is still computed and returned for reference/audit.
    """
    try:
        L, M, S = get_lms("acfa", sexo, edad_meses)
    except OutOfRangeError:
        return _no_aplica(
            "edad fuera del rango cubierto por el estandar OMS perimetro-braquial (3-60 meses)",
            pb_cm,
            edad_meses,
            "acfa",
        )
    z = compute_zscore(pb_cm, L, M, S)
    resultado = {
        "aplica": True,
        "valor_z": z,
        "x_input": pb_cm,
        "tabla_usada": "acfa",
        "edad_meses": edad_meses,
        "motivo_no_aplica": None,
    }
    resultado.update(classify.clasificar_perimetro_braquial(pb_cm, z))
    return resultado
