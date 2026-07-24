"""P09 — atomistic-to-continuum homogenization."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import homogenize as H


# --- the acoustic limit --------------------------------------------------

def test_chain_slope_equals_continuum_sound_speed():
    K, m, a = 12.0, 3.0, 0.7
    c = H.sound_speed_from_chain(K, m, a)
    slope = H.long_wavelength_slope(H.chain_dispersion(K, m, a))
    assert slope == pytest.approx(c, rel=H.ACOUSTIC_TOL)
    # and it is the analytic a*sqrt(K/m), not some other number
    assert c == pytest.approx(a * math.sqrt(K / m))


def test_sound_speed_requires_positive_inputs():
    with pytest.raises(H.HomogenizeError):
        H.sound_speed_from_chain(-1.0, 1.0, 1.0)
    with pytest.raises(H.HomogenizeError):
        H.sound_speed_from_chain(1.0, 0.0, 1.0)


def test_slope_refuses_a_gapped_optical_branch():
    # a branch with omega(0) != 0 has no continuum sound speed
    with pytest.raises(H.HomogenizeError):
        H.long_wavelength_slope(lambda k: 5.0 + k ** 2)


# --- effective stiffness -------------------------------------------------

def test_series_spring_homogenization_matches_analytic():
    K1, K2 = 4.0, 9.0
    eff = H.effective_stiffness_series(K1, K2)
    assert eff == pytest.approx(2.0 * K1 * K2 / (K1 + K2))
    # dominated by the softer spring: below the arithmetic mean
    assert eff < 0.5 * (K1 + K2)


def test_identical_springs_recover_the_constant():
    assert H.effective_stiffness_series(5.0, 5.0) == pytest.approx(5.0)


# --- the trigonal elastic tensor -----------------------------------------

def test_trigonal_structure_and_symmetry():
    ce = H.ContinuumElastic.alpha_quartz()
    C = ce.C
    assert C.shape == (6, 6)
    assert ce.is_symmetric()
    assert ce.trigonal_structure_ok()
    # explicit spot checks of the pattern
    assert C[0, 0] == C[1, 1]
    assert C[3, 3] == C[4, 4]
    assert C[0, 3] == pytest.approx(-C[1, 3])
    assert C[4, 5] == pytest.approx(C[0, 3])
    assert C[5, 5] == pytest.approx(0.5 * (C[0, 0] - C[0, 1]))
    # a required-zero entry really is zero
    assert C[0, 4] == 0.0


def test_a_broken_pattern_is_detected():
    ce = H.ContinuumElastic.alpha_quartz()
    bad = ce.C.copy()
    bad[0, 4] = bad[4, 0] = 1.0        # forbidden off-block entry
    assert not H.ContinuumElastic(bad, ce.density).trigonal_structure_ok()


def test_a_non_symmetric_stiffness_is_refused():
    bad = np.eye(6)
    bad[0, 1] = 2.0                    # not mirrored
    with pytest.raises(H.HomogenizeError):
        H.ContinuumElastic(bad, 1000.0)


# --- the Christoffel equation --------------------------------------------

def test_christoffel_has_three_real_nonnegative_velocities():
    ce = H.ContinuumElastic.alpha_quartz()
    for n in ([1.0, 0.0, 0.0], [0.0, 0.0, 1.0], [1.0, 1.0, 1.0]):
        v = H.christoffel_velocities(ce.C, n, ce.density)
        assert v.shape == (3,)
        assert np.all(np.isreal(v))
        assert np.all(v >= 0.0)
        # ascending, and one clearly-faster quasi-longitudinal mode
        assert np.all(np.diff(v) >= -1e-12)
        assert v[-1] > 0.0


def test_christoffel_refuses_a_null_direction():
    ce = H.ContinuumElastic.alpha_quartz()
    with pytest.raises(H.HomogenizeError):
        H.christoffel_velocities(ce.C, [0.0, 0.0, 0.0], ce.density)


# --- the refusal ---------------------------------------------------------

def test_refuse_homogenized_as_measured_raises():
    with pytest.raises(H.HomogenizeError):
        H.refuse_homogenized_as_measured("the continuum sound speed")


# --- the report ----------------------------------------------------------

def test_report_verdict_and_claims_nothing():
    r = H.homogenize_report()
    assert r["verdict"] == "ATOMISTIC_TO_CONTINUUM_HOMOGENIZED_ANALYTIC"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "ANALYTIC_MODEL"
    assert r["elastic_tensor"]["magnitudes_provenance"] == \
        "CONVENTIONAL_LITERATURE"
    assert "what_this_does_not_say" in r
