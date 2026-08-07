"""WHO LMS method core math.

Pure Python / math stdlib only -- no Django, no numpy/pandas dependency
needed here (the rest of the package uses pandas for table loading, but
this module is the mathematical core and is kept minimal and dependency-light
on purpose).

Reference: WHO Multicentre Growth Reference Study Group. WHO Child Growth
Standards: Methods and development.
"""
from __future__ import annotations

import math


def compute_zscore(x: float, L: float, M: float, S: float) -> float:
    """Compute the WHO LMS z-score for a measured value `x` given the
    L (Box-Cox power), M (median) and S (coefficient of variation)
    parameters for the relevant age/length row.

    Formula (WHO Child Growth Standards, Methods and Development):
        if L != 0:  z = ((x/M)**L - 1) / (L*S)
        if L == 0:  z = ln(x/M) / S
    """
    if x <= 0:
        raise ValueError(f"x must be positive, got {x!r}")
    if M <= 0:
        raise ValueError(f"M must be positive, got {M!r}")
    if S == 0:
        raise ValueError("S must be non-zero")

    if L != 0:
        return ((x / M) ** L - 1) / (L * S)
    return math.log(x / M) / S


def value_at_zscore(z: float, L: float, M: float, S: float) -> float:
    """Inverse of compute_zscore: solve for the measured value `x` that
    corresponds to a given z-score under the same L/M/S parameters.

    Used to draw the +-1/+-2/+-3 SD WHO reference bands on growth charts.

    Formula (algebraic inverse of the LMS formula):
        if L != 0:  x = M * (1 + L*S*z) ** (1/L)
        if L == 0:  x = M * exp(S*z)
    """
    if M <= 0:
        raise ValueError(f"M must be positive, got {M!r}")
    if S == 0:
        raise ValueError("S must be non-zero")

    if L != 0:
        base = 1 + L * S * z
        if base <= 0:
            raise ValueError(
                f"z={z!r} is out of the valid domain for L={L!r}, S={S!r} "
                f"(1 + L*S*z must be positive)"
            )
        return M * (base ** (1 / L))
    return M * math.exp(S * z)
