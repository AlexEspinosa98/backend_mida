from __future__ import annotations

import pytest

from apps.who_standards.lms import compute_zscore, value_at_zscore


@pytest.mark.parametrize("L,M,S", [(1.0, 87.1161, 0.03507), (-0.3521, 8.4227, 0.08229), (0.0, 15.0, 0.1)])
@pytest.mark.parametrize("z", [-3, -2, -1, 0, 1, 2, 3])
def test_value_at_zscore_is_inverse_of_compute_zscore(L, M, S, z):
    x = value_at_zscore(z, L, M, S)
    z_roundtrip = compute_zscore(x, L, M, S)
    assert z_roundtrip == pytest.approx(z, abs=1e-9)


def test_compute_zscore_zero_at_median():
    assert compute_zscore(87.1161, 1.0, 87.1161, 0.03507) == pytest.approx(0.0, abs=1e-9)


def test_compute_zscore_l_equal_zero_uses_log_formula():
    # BMI/weight tables sometimes have L far from 0, but L==0 exactly uses
    # the log-based branch -- verify it doesn't raise and behaves sanely.
    z = compute_zscore(20.0, 0.0, 15.0, 0.1)
    assert z > 0  # x > M -> positive z
    assert compute_zscore(15.0, 0.0, 15.0, 0.1) == pytest.approx(0.0, abs=1e-9)
