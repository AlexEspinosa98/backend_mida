from __future__ import annotations

import pytest

from apps.who_standards.interpolate import OutOfRangeError, get_lms
from apps.who_standards.loader import get_lms_row


def test_exact_integer_age_returns_published_row():
    L, M, S = get_lms("lhfa", "M", 12)
    row = get_lms_row("lhfa", "M", 12)
    assert L == pytest.approx(float(row["L"]))
    assert M == pytest.approx(float(row["M"]))
    assert S == pytest.approx(float(row["S"]))


def test_fractional_age_interpolates_between_neighbors():
    L14, M14, S14 = get_lms("lhfa", "M", 14)
    L15, M15, S15 = get_lms("lhfa", "M", 15)
    L, M, S = get_lms("lhfa", "M", 14.5)
    # M should land strictly between the two neighboring rows' M values
    lo, hi = sorted([M14, M15])
    assert lo < M < hi
    # and should be very close to the midpoint for a linear interpolation
    assert M == pytest.approx((M14 + M15) / 2, abs=1e-6)


def test_fractional_length_interpolates_between_neighbors():
    L1, M1, S1 = get_lms("wfl", "F", 63.0)
    L2, M2, S2 = get_lms("wfl", "F", 63.5)
    L, M, S = get_lms("wfl", "F", 63.4)
    lo, hi = sorted([M1, M2])
    assert lo <= M <= hi


def test_out_of_range_raises():
    with pytest.raises(OutOfRangeError):
        get_lms("lhfa", "M", -1)
    with pytest.raises(OutOfRangeError):
        get_lms("lhfa", "M", 61)
    with pytest.raises(OutOfRangeError):
        get_lms("acfa", "F", 2)  # acfa starts at month 3
    with pytest.raises(OutOfRangeError):
        get_lms("wfl", "M", 200)  # far beyond 110cm
