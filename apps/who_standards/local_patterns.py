"""Comparación complementaria contra el patrón de crecimiento LOCAL
documentado para niños Kogui y Arhuaco (Sierra Nevada de Santa Marta),
además de la comparación estándar contra la OMS.

Fuente y metodología completa: apps/who_standards/data/local_patterns/
PROVENANCE.md -- léelo antes de tocar este archivo. En resumen: esto es
una APROXIMACIÓN basada en estadísticas agregadas de un estudio
(Arbeláez et al., Gonawindúa Institución Pública de Salud Indígena), NO
una tabla LMS mes a mes con el mismo rigor que las tablas oficiales OMS
de apps/who_standards/data/*.csv. Solo cubre Talla-para-edad y
Peso-para-edad, que es donde el estudio documenta un sesgo real al usar
solo la referencia OMS; para IMC, Peso-para-talla y Perímetro Braquial el
estudio concluye que la población local YA es comparable a la OMS, así
que ahí no se calcula un ajuste aparte -- se usa el z-score OMS tal cual.

Pure Python -- no Django imports.
"""
from __future__ import annotations

from typing import Literal

Etnia = Literal["kogui", "arhuaco"]

ETNIAS_CON_PATRON_LOCAL = ("kogui", "arhuaco")

EXPLICACION_METODOLOGIA = (
    "Además de comparar contra el patrón internacional de la OMS, este reporte incluye "
    "una segunda comparación contra el patrón de crecimiento documentado para la "
    "comunidad indígena del paciente (Kogui o Arhuaco, Sierra Nevada de Santa Marta), "
    "con base en un estudio de Arbeláez et al. (Gonawindúa Institución Pública de Salud "
    "Indígena) sobre 13,835 valoraciones antropométricas de niños y niñas de estas "
    "etnias. Ese estudio encontró que la talla y el peso para la edad de estos niños "
    "están sistemáticamente por debajo de la mediana OMS de forma poblacional -- pero "
    "que su índice de masa corporal, peso-para-talla y perímetro braquial SÍ son "
    "comparables al patrón OMS, es decir, su composición corporal relativa es normal "
    "pese a su menor talla/peso absolutos. Por eso, cuando la talla-para-edad o el "
    "peso-para-edad muestran un hallazgo frente a la OMS que la comparación comunitaria "
    "no confirma, esto es consistente con un patrón poblacional saludable y no debe, por "
    "sí solo, interpretarse como desnutrición -- la valoración de riesgo nutricional real "
    "debe apoyarse en el IMC, el peso-para-talla y el perímetro braquial. Esta "
    "comparación comunitaria es una APROXIMACIÓN estadística basada en un estudio con "
    "datos agregados (no en una tabla de referencia mes a mes con el mismo rigor que la "
    "OMS) -- ver apps/who_standards/data/local_patterns/PROVENANCE.md para el detalle "
    "metodológico completo."
)

# Desfase promedio (talla observada - talla media OMS, en cm) por
# etnia×sexo, "en meseta" (valor típico a partir de ~24 meses según el
# estudio). DE de la diferencia: solo disponible como cifra GLOBAL
# combinada en el resumen final del estudio (8.60cm), no desagregada por
# etnia/sexo -- se usa igual para las 4 combinaciones por falta de un
# dato más específico (ver PROVENANCE.md).
_TALLA_EDAD_OFFSET_CM: dict[tuple[Etnia, str], float] = {
    ("arhuaco", "F"): -7.18,
    ("arhuaco", "M"): -7.62,
    ("kogui", "F"): -10.77,
    ("kogui", "M"): -11.10,
}
_TALLA_EDAD_SD_CM = 8.60

# Diferencia promedio de peso (peso observado - peso medio OMS, en kg) y
# su desviación estándar, por etnia×sexo -- este es el dato más preciso
# del estudio (tabla con IC 95% y tamaño de muestra >7000 por grupo).
_PESO_EDAD_OFFSET_KG: dict[tuple[Etnia, str], float] = {
    ("arhuaco", "F"): -1.11,
    ("arhuaco", "M"): -1.24,
    ("kogui", "F"): -2.39,
    ("kogui", "M"): -2.55,
}
_PESO_EDAD_SD_KG: dict[tuple[Etnia, str], float] = {
    ("arhuaco", "F"): 0.91,
    ("arhuaco", "M"): 0.79,
    ("kogui", "F"): 1.11,
    ("kogui", "M"): 1.02,
}

# Edad (meses) hasta la cual se aplica una rampa lineal del desfase (de 0
# a su valor completo) en vez de aplicarlo de golpe desde el nacimiento.
# Justificación: el estudio describe y grafica ("brecha de talla/peso vs
# OMS") que la diferencia es ~0 al nacer y crece hasta estabilizarse
# alrededor de los 18-24 meses -- esta rampa es una decisión de
# implementación nuestra para no exagerar el ajuste en recién nacidos,
# el estudio no tabula la forma exacta de la rampa mes a mes.
_EDAD_RAMPA_MESES = 24.0


def factor_rampa(edad_meses: float) -> float:
    if edad_meses <= 0:
        return 0.0
    if edad_meses >= _EDAD_RAMPA_MESES:
        return 1.0
    return edad_meses / _EDAD_RAMPA_MESES


def _normalizar_etnia(etnia: str | None) -> Etnia | None:
    if not etnia:
        return None
    e = etnia.strip().lower()
    if e in ETNIAS_CON_PATRON_LOCAL:
        return e  # type: ignore[return-value]
    return None


def talla_para_edad_comunitaria(
    etnia: str | None, sexo: str, edad_meses: float, talla_cm: float, mediana_oms_cm: float
) -> dict | None:
    """Compara talla_cm contra la mediana OMS AJUSTADA por el desfase
    comunitario documentado. Devuelve None si la etnia no tiene patrón
    local disponible (no es un error -- simplemente no aplica).

    mediana_oms_cm: la M (mediana) de la tabla LMS OMS ya interpolada
    para esta edad/sexo (calculada por el llamador con who_standards.
    interpolate.get_lms + lms -- este módulo no vuelve a tocar las
    tablas OMS, solo las desplaza).
    """
    e = _normalizar_etnia(etnia)
    if e is None:
        return None

    offset_completo = _TALLA_EDAD_OFFSET_CM.get((e, sexo))
    if offset_completo is None:
        return None

    offset_aplicado = offset_completo * factor_rampa(edad_meses)
    mediana_local = mediana_oms_cm + offset_aplicado
    valor_z = (talla_cm - mediana_local) / _TALLA_EDAD_SD_CM

    return {
        "etnia": e,
        "valor_z": valor_z,
        "mediana_comunitaria_cm": mediana_local,
        "offset_aplicado_cm": offset_aplicado,
        "offset_meseta_cm": offset_completo,
        "fuente": "Arbeláez et al., Gonawindúa IPSI -- aproximación agregada, ver PROVENANCE.md",
    }


def peso_para_edad_comunitario(
    etnia: str | None, sexo: str, edad_meses: float, peso_kg: float, mediana_oms_kg: float
) -> dict | None:
    """Análogo a talla_para_edad_comunitaria pero para peso-para-edad."""
    e = _normalizar_etnia(etnia)
    if e is None:
        return None

    offset_completo = _PESO_EDAD_OFFSET_KG.get((e, sexo))
    sd = _PESO_EDAD_SD_KG.get((e, sexo))
    if offset_completo is None or sd is None:
        return None

    offset_aplicado = offset_completo * factor_rampa(edad_meses)
    mediana_local = mediana_oms_kg + offset_aplicado
    valor_z = (peso_kg - mediana_local) / sd

    return {
        "etnia": e,
        "valor_z": valor_z,
        "mediana_comunitaria_kg": mediana_local,
        "offset_aplicado_kg": offset_aplicado,
        "offset_meseta_kg": offset_completo,
        "fuente": "Arbeláez et al., Gonawindúa IPSI -- aproximación agregada, ver PROVENANCE.md",
    }
