"""P15 — quasi-phase-matching: sinc acceptance, secular growth, Manley-Rowe."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import qpm


def test_conversion_efficiency_is_maximal_at_perfect_matching():
    # POWER: the peak is at dk = 0 and every mismatch is strictly lower.
    L = 5.0
    peak = qpm.conversion_efficiency(0.0, L)
    for dk in (0.1, 0.4, 0.9, 1.5, 2.3):
        assert qpm.conversion_efficiency(dk, L) < peak
    # perfect matching grows as L**2
    assert qpm.conversion_efficiency(0.0, 2.0 * L) == pytest.approx(
        4.0 * qpm.conversion_efficiency(0.0, L))


def test_conversion_efficiency_has_zeros_at_n_pi():
    # POWER: sinc**2(dk*L/2) vanishes at dk*L/2 = n*pi, n != 0.
    L = 5.0
    for n in (1, 2, 3):
        dk = 2.0 * n * math.pi / L
        assert qpm.conversion_efficiency(dk, L) == pytest.approx(0.0, abs=1e-12)
    # and it is NOT zero away from those points
    assert qpm.conversion_efficiency(math.pi / L, L) > 1e-3


def test_matched_grating_grows_secularly_unmatched_stays_bounded():
    # POWER both ways: the matched grating grows with L; the uniform
    # coupling only oscillates under its 2*kappa/|dk| bound.
    c = qpm.secular_growth_contrast(dk=0.5, L=40.0)
    assert c["matched_grows_with_length"] is True
    assert c["matched_at_2L"] > 1.8 * c["matched_at_L"]
    assert c["uniform_stays_bounded"] is True
    assert c["uniform_at_2L"] <= c["uniform_bound"] * 1.01
    assert c["matched_beats_uniform"] is True


def test_uniform_coupling_would_fail_a_growth_claim():
    # The negative half, on its own: the uniform (ungrated) accumulated
    # conversion only oscillates under its 2*kappa/|dk| bound however long
    # the crystal, while the matched grating grows far past that bound.
    dk = 0.5
    bound = 2.0 / abs(dk)
    uniform_max = max(abs(qpm.qpm_effective_coupling(dk, None, L))
                      for L in range(2, 200, 2))
    assert uniform_max <= bound * 1.01
    matched_far = abs(qpm.qpm_effective_coupling(
        dk, qpm.matched_period(dk), 200.0))
    assert matched_far > 10.0 * bound


def test_chirped_grating_broadens_acceptance_bandwidth():
    b = qpm.chirped_broadens_bandwidth(L=10.0, chirp=0.8)
    assert b["chirped_broadens"] is True
    assert b["chirped_fwhm"] > b["fixed_fwhm"]
    assert b["broadening_ratio"] > 2.0


def test_manley_rowe_photon_number_conserved_when_depleted():
    # Strong coupling so the pump visibly depletes and the harmonic grows;
    # the total photon number is still conserved.
    s = qpm.coupled_mode_solve(dk=0.0, L=1.2, kappa=1.0,
                               a_in0=1.0, a_out0=0.0)
    assert s.manley_rowe_defect < 1e-9
    assert abs(s.a_out) > 0.5          # the harmonic grew from zero
    assert abs(s.a_in) < 0.99          # the pump depleted


def test_manley_rowe_holds_off_resonance_too():
    s = qpm.coupled_mode_solve(dk=0.7, L=4.0, kappa=0.8,
                               a_in0=1.0, a_out0=0.3)
    assert s.manley_rowe_defect < 1e-9


def test_undepleted_ode_matches_the_sinc_formula():
    # The numerically integrated undepleted amplitude reproduces the
    # closed-form sinc**2 efficiency.
    dk, L, kappa = 0.7, 4.0, 1.3
    modulus_sq = abs(qpm.undepleted_conversion(dk, L, kappa)) ** 2
    assert modulus_sq == pytest.approx(
        qpm.conversion_efficiency(dk, L, kappa), rel=1e-4)


def test_refuse_model_conversion_as_measured_raises():
    with pytest.raises(qpm.QPMError):
        qpm.refuse_model_conversion_as_measured(0.0, 5.0)


def test_bad_inputs_are_refused():
    with pytest.raises(qpm.QPMError):
        qpm.conversion_efficiency(0.0, 0.0)         # non-positive length
    with pytest.raises(qpm.QPMError):
        qpm.qpm_effective_coupling(0.5, -1.0, 10.0)  # non-positive period
    with pytest.raises(qpm.QPMError):
        qpm.matched_period(0.0)                      # undefined at dk = 0
    with pytest.raises(qpm.QPMError):
        qpm.dynamic_qpm("not callable", 10.0)


def test_report_verdict_and_no_measurement():
    r = qpm.qpm_report()
    assert r["verdict"] == "DYNAMIC_QUASI_PHASE_MATCHING_MODEL"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] in r["claim_classes"]
    assert "what_this_does_not_say" in r
    assert r["manley_rowe"]["defect"] < 1e-9
    assert r["secular_growth_contrast"]["matched_grows_with_length"] is True
    assert r["dynamic_qpm"]["chirped_broadens"] is True
