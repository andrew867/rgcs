"""P09 — nonlinear inverse estimation: power, calibration, and refusal."""

from __future__ import annotations

import numpy as np
import pytest

from r10 import nlinverse as N


# --- forward models behave -----------------------------------------------

def test_single_exponential_is_a_decay():
    y = N.single_exponential([2.0, 0.7], np.array([0.0, 1.0]))
    assert y[0] == pytest.approx(2.0)
    assert y[1] == pytest.approx(2.0 * np.exp(-0.7))


def test_double_exponential_wrong_arity_raises():
    with pytest.raises(ValueError):
        N.double_exponential([1.0, 0.5], np.array([1.0]))


# --- POWER: identifiable single exponential ------------------------------

def test_fit_recovers_planted_single_exponential():
    x, y = N.planted_single_exponential(seed=1)
    res = N.fit(N.single_exponential, x, y,
                p0=N.REFERENCE_SINGLE_PARAMS * 1.3)
    assert res.success
    # Estimate is close to the planted truth.
    rel = np.abs(res.params - N.REFERENCE_SINGLE_PARAMS) \
        / np.abs(N.REFERENCE_SINGLE_PARAMS)
    assert rel.max() < 0.1


def test_power_recovery_truth_lies_in_the_reported_ci():
    out = N.power_recovery(seed=3)
    assert out["success"]
    assert out["all_in_ci"]


def test_single_exponential_is_identifiable():
    ident = N.identifiability(N.single_exponential,
                             N.REFERENCE_SINGLE_PARAMS, N.REFERENCE_X)
    assert ident["identifiable"]
    assert ident["rank"] == 2


# --- CALIBRATION: coverage ~ nominal -------------------------------------

def test_coverage_is_near_nominal_on_identifiable_problem():
    cov = N.coverage_test(N.single_exponential, N.REFERENCE_SINGLE_PARAMS,
                          N.REFERENCE_X, N.REFERENCE_NOISE,
                          trials=500, nominal=0.95, seed=7)
    assert cov["failures"] == 0
    # Every parameter's empirical coverage sits near the 95% promise.
    assert cov["min_coverage"] >= 0.88
    assert cov["mean_coverage"] == pytest.approx(0.95, abs=0.05)


def test_z_multiplier_matches_known_value():
    assert N.z_for_nominal(0.95) == pytest.approx(1.959963985, abs=1e-6)


# --- NON-IDENTIFIABLE: detection and refusal -----------------------------

def test_double_exponential_with_equal_rates_is_not_identifiable():
    ident = N.identifiability(N.double_exponential,
                             N.NONIDENTIFIABLE_PARAMS, N.REFERENCE_X)
    assert not ident["identifiable"]
    # Rank drops below the four nominal parameters, cond blows up.
    assert ident["rank"] < 4
    assert ident["cond"] > N.DEFAULT_COND_MAX


def test_refusal_raises_on_the_nonidentifiable_model():
    with pytest.raises(N.InverseError):
        N.refuse_point_estimate_when_nonidentifiable(
            N.double_exponential, N.NONIDENTIFIABLE_PARAMS, N.REFERENCE_X)


def test_refusal_returns_the_report_when_well_posed():
    rep = N.refuse_point_estimate_when_nonidentifiable(
        N.single_exponential, N.REFERENCE_SINGLE_PARAMS, N.REFERENCE_X)
    assert rep["identifiable"]


def test_nonidentifiable_example_carries_the_verdict():
    demo = N.nonidentifiable_example()
    assert demo["verdict"] == "NON_IDENTIFIABLE"
    assert not demo["identifiability"]["identifiable"]


# --- underdetermined fit is refused --------------------------------------

def test_fit_refuses_when_fewer_points_than_parameters():
    x = np.array([1.0, 2.0])
    y = np.array([1.0, 0.5])
    with pytest.raises(N.InverseError):
        N.fit(N.double_exponential, x, y, p0=[1.0, 0.5, 1.0, 0.6])


# --- report --------------------------------------------------------------

def test_report_measures_nothing():
    r = N.nlinverse_report(seed=11)
    assert r["measured_here"] == "nothing"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"


def test_report_default_verdict_is_software_only():
    r = N.nlinverse_report(seed=11)
    assert r["verdict"] == "NONLINEAR_INVERSE_SOFTWARE_ONLY"


def test_report_bundles_power_and_coverage_and_the_refusal_demo():
    r = N.nlinverse_report(seed=11)
    assert r["identifiable_reference"]["power"]["all_in_ci"]
    assert r["identifiable_reference"]["coverage"]["mean_coverage"] \
        == pytest.approx(0.95, abs=0.06)
    assert not r["nonidentifiable_demo"]["identifiability"]["identifiable"]
