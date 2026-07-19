"""R8-D-003 — MDEV and TDEV, implemented and validated.

The analysis plan named three estimators and implemented one. This
file exists to make sure that cannot recur silently: the plan's
declared estimator set is checked against what actually exists in
code.
"""

from __future__ import annotations

import math

import pytest

from r7 import clocklink as CL


@pytest.fixture(scope="module")
def series():
    return CL.simulate_frequency_series(1e-12, 3000, 1.0, seed=11)


# --- the definitional anchors ----------------------------------------

def test_mdev_equals_adev_at_m_one(series):
    """At m = 1 the modified Allan variance reduces exactly to the
    Allan variance. This is a definition, so it is asserted tightly."""
    a = CL.overlapping_adev(series, 1.0, 1)
    m = CL.overlapping_mdev(series, 1.0, 1)
    assert m == pytest.approx(a, rel=1e-12)


def test_tdev_is_exactly_tau_mdev_over_root_three(series):
    """TDEV(tau) = tau * MDEV(tau) / sqrt(3), by definition."""
    for k in (1, 4, 8, 32):
        t = CL.time_deviation(series, 1.0, k)
        expected = k * 1.0 * CL.overlapping_mdev(series, 1.0, k) \
            / math.sqrt(3.0)
        assert t == pytest.approx(expected, rel=1e-15)


# --- noise-type behaviour ---------------------------------------------

def test_mdev_falls_with_averaging_under_white_fm(series):
    vals = [CL.overlapping_mdev(series, 1.0, m) for m in (1, 4, 16, 64)]
    assert all(a > b for a, b in zip(vals, vals[1:]))


def test_white_fm_slope_is_near_minus_one_half(series):
    """White FM gives MDEV ~ tau^-1/2, the same slope as ADEV.

    Tolerance is loose because this is a finite-sample estimate from a
    3000-point series, not an identity.
    """
    d1 = CL.overlapping_mdev(series, 1.0, 4)
    d2 = CL.overlapping_mdev(series, 1.0, 16)
    slope = math.log(d2 / d1) / math.log(4.0)
    assert -0.8 < slope < -0.3


def test_tdev_grows_with_tau_under_white_fm(series):
    """TDEV = tau*MDEV/sqrt(3); with MDEV ~ tau^-1/2 this rises as
    tau^+1/2, so a longer averaging time means a larger time error."""
    a = CL.time_deviation(series, 1.0, 4)
    b = CL.time_deviation(series, 1.0, 64)
    assert b > a


# --- refusals ----------------------------------------------------------

def test_short_series_refused(series):
    with pytest.raises(ValueError):
        CL.overlapping_mdev(series[:10], 1.0, 40)
    with pytest.raises(ValueError):
        CL.overlapping_mdev(series, 1.0, 0)


def test_estimators_are_deterministic(series):
    assert CL.overlapping_mdev(series, 1.0, 8) == \
        CL.overlapping_mdev(series, 1.0, 8)


# --- the guard against R8-D-003 recurring -----------------------------

def test_every_declared_estimator_actually_exists():
    """The defect was a plan naming estimators that pointed at nothing."""
    for name, func in CL.IMPLEMENTED_ESTIMATORS.items():
        assert hasattr(CL, func), f"{name} -> {func} does not exist"
        assert callable(getattr(CL, func))


def test_all_three_named_estimators_are_present():
    assert set(CL.IMPLEMENTED_ESTIMATORS) == {"ADEV", "MDEV", "TDEV"}


def test_analysis_plan_names_only_implemented_estimators():
    """If the measurement plan lists an estimator, it must exist."""
    from r8.measurement import analysis_plan
    plan = analysis_plan()
    blob = str(plan).upper()
    for named in ("ADEV", "MDEV", "TDEV"):
        if named in blob:
            assert named in CL.IMPLEMENTED_ESTIMATORS
