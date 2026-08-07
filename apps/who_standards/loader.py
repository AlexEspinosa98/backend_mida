"""Loads the 14 normalized WHO LMS CSVs (see apps/who_standards/data/) once,
cached, keyed by indicator + sex.

Pure Python + pandas -- no Django imports, so this stays independently
importable/testable outside a Django app registry.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

import pandas as pd

DATA_DIR = Path(__file__).parent / "data"

Sexo = Literal["M", "F"]

# Age-indexed indicators: edad_meses,L,M,S
AGE_INDEXED_FILES = {
    ("lhfa", "M"): "lhfa_boys.csv",
    ("lhfa", "F"): "lhfa_girls.csv",
    ("wfa", "M"): "wfa_boys.csv",
    ("wfa", "F"): "wfa_girls.csv",
    ("bfa", "M"): "bfa_boys.csv",
    ("bfa", "F"): "bfa_girls.csv",
    ("hcfa", "M"): "hcfa_boys.csv",
    ("hcfa", "F"): "hcfa_girls.csv",
    ("acfa", "M"): "acfa_boys.csv",
    ("acfa", "F"): "acfa_girls.csv",
}

# Length/height-indexed indicators: longitud_talla_cm,L,M,S
LENGTH_INDEXED_FILES = {
    ("wfl", "M"): "wfl_boys_0_2y.csv",
    ("wfl", "F"): "wfl_girls_0_2y.csv",
    ("wfh", "M"): "wfh_boys_2_5y.csv",
    ("wfh", "F"): "wfh_girls_2_5y.csv",
}

ALL_FILES = {**AGE_INDEXED_FILES, **LENGTH_INDEXED_FILES}

# Which x-axis column each table is indexed by.
INDEX_COLUMN = {
    "lhfa": "edad_meses",
    "wfa": "edad_meses",
    "bfa": "edad_meses",
    "hcfa": "edad_meses",
    "acfa": "edad_meses",
    "wfl": "longitud_talla_cm",
    "wfh": "longitud_talla_cm",
}


def _normalize_sexo(sexo: str) -> Sexo:
    s = sexo.strip().upper()
    if s in ("M", "MASCULINO", "BOY", "BOYS", "H", "HOMBRE"):
        return "M"
    if s in ("F", "FEMENINO", "GIRL", "GIRLS", "MUJER"):
        return "F"
    raise ValueError(f"sexo no reconocido: {sexo!r} (use 'M' o 'F')")


@lru_cache(maxsize=None)
def _load_csv(indicador: str, sexo: Sexo) -> pd.DataFrame:
    key = (indicador, sexo)
    if key not in ALL_FILES:
        raise KeyError(
            f"indicador/sexo no soportado: {key!r}. "
            f"indicadores validos: {sorted({k[0] for k in ALL_FILES})}"
        )
    path = DATA_DIR / ALL_FILES[key]
    if not path.exists():
        raise FileNotFoundError(
            f"tabla WHO no encontrada en {path} -- "
            f"corre apps/who_standards/data/_convert_raw.py"
        )
    df = pd.read_csv(path)
    return df


def get_table(indicador: str, sexo: str) -> pd.DataFrame:
    """Return the full LMS DataFrame for a given indicator + sex.

    indicador: one of 'lhfa', 'wfa', 'bfa', 'hcfa', 'acfa', 'wfl', 'wfh'
    sexo: 'M' or 'F' (also accepts common Spanish/English aliases)
    """
    return _load_csv(indicador, _normalize_sexo(sexo))


def get_lms_row(indicador: str, sexo: str, x_value: float) -> pd.Series | None:
    """Return the exact table row matching x_value (on the indicator's
    index column), or None if there's no exact match at that value.

    This does NOT interpolate -- see interpolate.get_lms() for that.
    """
    df = get_table(indicador, sexo)
    col = INDEX_COLUMN[indicador]
    matches = df[df[col] == x_value]
    if matches.empty:
        return None
    return matches.iloc[0]


def table_range(indicador: str, sexo: str) -> tuple[float, float]:
    """Return (min, max) of the index column for this indicator/sex table."""
    df = get_table(indicador, sexo)
    col = INDEX_COLUMN[indicador]
    return float(df[col].min()), float(df[col].max())
