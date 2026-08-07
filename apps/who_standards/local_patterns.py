"""Comparación complementaria contra el patrón de crecimiento LOCAL
documentado para niños Kogui y Arhuaco (Sierra Nevada de Santa Marta),
además de la comparación estándar contra la OMS.

Fuente y metodología completa: apps/who_standards/data/local_patterns/
PROVENANCE.md -- léelo antes de tocar este archivo. En resumen: esto es
una APROXIMACIÓN basada en estadísticas agregadas de un estudio
(Arbeláez et al., Gonawindúa Institución Pública de Salud Indígena), NO
una tabla LMS mes a mes con el mismo rigor que las tablas oficiales OMS
de apps/who_standards/data/*.csv.

Cubre 4 indicadores, con dos niveles de precisión distintos:
- Talla-para-edad y Peso-para-edad: el estudio da un desfase (y, para
  peso, una desviación estándar) DESGLOSADO por etnia×sexo -- aquí es
  donde documenta un sesgo real de los indicadores simples frente a la
  OMS.
- IMC-para-edad y Peso-para-talla: el estudio concluye que estos YA son
  comparables a la OMS (su composición corporal relativa es normal), pero
  igual reporta una cifra de diferencia promedio + DE -- aquí SOLO como
  cifra GLOBAL combinando ambas etnias (no desglosada por etnia/sexo,
  menos precisa que las dos anteriores). Se incluye para poder mostrar
  también su gráfica comparativa, confirmando visualmente con datos
  reales la conclusión del estudio de que no hay sesgo relevante aquí.
- Perímetro cefálico y perímetro braquial: el estudio no tabula cifras
  utilizables para perímetro cefálico (no lo evaluó), y el perímetro
  braquial se clasifica por un corte clínico absoluto en cm (no por
  z-score) -- ninguno de los dos tiene una comparación comunitaria aquí.

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
    "que su índice de masa corporal y su peso-para-talla SÍ son comparables al patrón "
    "OMS, es decir, su composición corporal relativa es normal pese a su menor talla/peso "
    "absolutos. Por eso, cuando la talla-para-edad o el peso-para-edad muestran un "
    "hallazgo frente a la OMS que la comparación comunitaria no confirma, esto es "
    "consistente con un patrón poblacional saludable y no debe, por sí solo, "
    "interpretarse como desnutrición -- la valoración de riesgo nutricional real debe "
    "apoyarse en el IMC, el peso-para-talla y el perímetro braquial. Se incluye también "
    "la gráfica comunitaria de IMC y peso-para-talla, precisamente para mostrar con "
    "datos reales que, a diferencia de talla y peso para la edad, en estos dos SÍ "
    "coinciden ambas comparaciones. El perímetro cefálico no fue evaluado por el estudio "
    "y el perímetro braquial se clasifica por un corte clínico absoluto en centímetros "
    "(no por z-score), por lo que ninguno de los dos tiene una gráfica comunitaria "
    "propia. Esta comparación comunitaria es una APROXIMACIÓN estadística basada en un "
    "estudio con datos agregados (no en una tabla de referencia mes a mes con el mismo "
    "rigor que la OMS; para IMC y peso-para-talla la cifra ni siquiera está desglosada "
    "por etnia, solo hay un promedio combinado) -- ver "
    "apps/who_standards/data/local_patterns/PROVENANCE.md para el detalle metodológico "
    "completo."
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
        "sd": _TALLA_EDAD_SD_CM,
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
        "sd": sd,
        "fuente": "Arbeláez et al., Gonawindúa IPSI -- aproximación agregada, ver PROVENANCE.md",
    }


# Diferencia promedio y DE para IMC y peso-para-talla -- a diferencia de
# talla/peso-para-edad, el estudio solo reporta estas dos como cifra
# GLOBAL combinando Kogui + Arhuaco (resumen final del estudio), no
# desglosada por etnia ni sexo. Se aplican igual a ambas etnias por falta
# de un dato más específico. Sin rampa por edad: el estudio no describe
# ni grafica una forma de "brecha creciente" para estos dos indicadores
# como sí lo hace para talla y peso-para-edad, así que aplicamos el
# desfase constante en vez de inventar una forma sin evidencia.
_IMC_OFFSET = 0.78
_IMC_SD = 1.82
_PESO_TALLA_OFFSET_KG = 0.29
_PESO_TALLA_SD_KG = 1.50


def imc_para_edad_comunitario(
    etnia: str | None, imc: float, mediana_oms: float
) -> dict | None:
    """Compara el IMC contra la mediana OMS ajustada por el desfase
    comunitario GLOBAL (no desglosado por etnia/sexo, ver nota arriba).
    Se incluye principalmente para mostrar, con datos reales, que esta
    comparación normalmente coincide con la OMS (a diferencia de T/E y
    P/E) -- tal como concluye el estudio."""
    e = _normalizar_etnia(etnia)
    if e is None:
        return None

    mediana_local = mediana_oms + _IMC_OFFSET
    valor_z = (imc - mediana_local) / _IMC_SD

    return {
        "etnia": e,
        "valor_z": valor_z,
        "mediana_comunitaria": mediana_local,
        "offset_aplicado": _IMC_OFFSET,
        "offset_meseta": _IMC_OFFSET,
        "sd": _IMC_SD,
        "desglose": "global (Kogui + Arhuaco combinados, no por etnia/sexo)",
        "fuente": "Arbeláez et al., Gonawindúa IPSI -- aproximación agregada, ver PROVENANCE.md",
    }


def peso_para_talla_comunitario(
    etnia: str | None, peso_kg: float, mediana_oms_kg: float
) -> dict | None:
    """Análogo a imc_para_edad_comunitario pero para peso-para-talla."""
    e = _normalizar_etnia(etnia)
    if e is None:
        return None

    mediana_local = mediana_oms_kg + _PESO_TALLA_OFFSET_KG
    valor_z = (peso_kg - mediana_local) / _PESO_TALLA_SD_KG

    return {
        "etnia": e,
        "valor_z": valor_z,
        "mediana_comunitaria_kg": mediana_local,
        "offset_aplicado_kg": _PESO_TALLA_OFFSET_KG,
        "offset_meseta_kg": _PESO_TALLA_OFFSET_KG,
        "sd": _PESO_TALLA_SD_KG,
        "desglose": "global (Kogui + Arhuaco combinados, no por etnia/sexo)",
        "fuente": "Arbeláez et al., Gonawindúa IPSI -- aproximación agregada, ver PROVENANCE.md",
    }
