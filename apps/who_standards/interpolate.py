"""Linear interpolation of WHO LMS (L, M, S) parameters between tabulated
rows, for x_values that fall between two published integer ages (months) or
0.5cm length/height increments.
"""
from __future__ import annotations

from apps.who_standards.loader import INDEX_COLUMN, get_table


class OutOfRangeError(ValueError):
    """Raised when x_value falls outside the WHO table's published range.

    Callers (apps.who_standards.indicators) decide what this means clinically
    per indicator -- e.g. "indicador no aplicable a esta edad" -- this
    exception intentionally does NOT get silently swallowed/clamped here.
    """

    def __init__(self, indicador: str, sexo: str, x_value: float, lo: float, hi: float):
        self.indicador = indicador
        self.sexo = sexo
        self.x_value = x_value
        self.lo = lo
        self.hi = hi
        super().__init__(
            f"x_value={x_value!r} fuera de rango para indicador={indicador!r} "
            f"sexo={sexo!r}: la tabla WHO cubre [{lo!r}, {hi!r}]"
        )


def get_lms(indicador: str, sexo: str, x_value: float) -> tuple[float, float, float]:
    """Return (L, M, S) for x_value, exact if a published row matches,
    otherwise linearly interpolated between the two nearest rows.

    Raises OutOfRangeError if x_value is outside the table's min/max.
    """
    df = get_table(indicador, sexo)
    col = INDEX_COLUMN[indicador]

    lo = float(df[col].min())
    hi = float(df[col].max())
    if x_value < lo or x_value > hi:
        raise OutOfRangeError(indicador, sexo, x_value, lo, hi)

    # Exact match (covers the common case: integer month, or a length/height
    # that lands exactly on a published 0.5cm increment).
    exact = df[df[col] == x_value]
    if not exact.empty:
        row = exact.iloc[0]
        return float(row["L"]), float(row["M"]), float(row["S"])

    # Find the bracketing rows.
    below = df[df[col] < x_value]
    above = df[df[col] > x_value]
    row_lo = below.iloc[-1]
    row_hi = above.iloc[0]

    x_lo, x_hi = float(row_lo[col]), float(row_hi[col])
    frac = (x_value - x_lo) / (x_hi - x_lo)

    def lerp(field: str) -> float:
        v_lo, v_hi = float(row_lo[field]), float(row_hi[field])
        return v_lo + frac * (v_hi - v_lo)

    return lerp("L"), lerp("M"), lerp("S")
