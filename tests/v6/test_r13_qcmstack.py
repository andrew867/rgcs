"""R13 QCM stack — Sauerbrey, BVD and ring-down as models, not a device.

Sauerbrey is exactly linear and has the right sign (mass up -> frequency
down) (POWER). fit_bvd recovers the planted R, L, C, C0 from a synthetic
impedance sweep (POWER, round-trip). ringdown_Q recovers the planted Q and
tau from a synthetic decay (POWER), and its linewidth reproduces the BVD
Q = f_s/FWHM. The three routes cross-agree on the same synthetic resonator
(model self-consistency, not measurement agreement). Both refusals raise,
and the report carries the verdict with measured_here == "nothing".
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import qcmstack as Q


# --- (1) the Sauerbrey relation ------------------------------------------

def test_sauerbrey_is_linear_and_mass_up_lowers_frequency():
    """POWER: Delta f = -C_f * Delta m is linear with the correct sign."""
    Cf = 2.0e9
    # sign: a positive mass load lowers the frequency
    assert Q.sauerbrey_delta_f(1e-9, Cf) < 0.0
    # removing mass raises the frequency
    assert Q.sauerbrey_delta_f(-1e-9, Cf) > 0.0
    # linearity: doubling the mass doubles the shift
    assert Q.sauerbrey_delta_f(2e-9, Cf) == pytest.approx(
        2.0 * Q.sauerbrey_delta_f(1e-9, Cf))
    # exact value
    assert Q.sauerbrey_delta_f(3e-9, Cf) == pytest.approx(-6.0)


def test_sauerbrey_constant_inverts_back_to_the_fundamental():
    f0 = 1.0e6
    cf = Q.sauerbrey_constant(f0)
    assert cf > 0.0
    assert Q.sauerbrey_f0_from_Cf(cf) == pytest.approx(f0, rel=1e-9)


# --- (2) the BVD fit ------------------------------------------------------

def test_fit_bvd_recovers_the_planted_rlc_c0():
    """POWER round-trip: recover R, L, C, C0 from a synthetic sweep."""
    sweep = Q.synthetic_bvd_sweep()
    fit = Q.fit_bvd(sweep["freqs_hz"], sweep["Z"])
    assert fit["R"] == pytest.approx(sweep["true_R"], rel=1e-3)
    assert fit["L"] == pytest.approx(sweep["true_L"], rel=1e-3)
    assert fit["C"] == pytest.approx(sweep["true_C"], rel=1e-3)
    assert fit["C0"] == pytest.approx(sweep["true_C0"], rel=1e-2)


def test_fit_bvd_recovers_f_s_f_p_and_q():
    sweep = Q.synthetic_bvd_sweep()
    fit = Q.fit_bvd(sweep["freqs_hz"], sweep["Z"])
    assert fit["f_s_hz"] == pytest.approx(sweep["true_f_s"], rel=1e-4)
    assert fit["f_p_hz"] == pytest.approx(sweep["true_f_p"], rel=1e-3)
    assert fit["Q"] == pytest.approx(sweep["true_Q"], rel=1e-2)
    assert fit["f_p_hz"] > fit["f_s_hz"]


def test_fit_bvd_recovers_a_different_planted_resonator():
    """The fit is not hard-wired to one resonator."""
    other = Q.BVDResonator(R=25.0, L=2.0e-3, C=1.2665e-11, C0=8.0e-11)
    sweep = Q.synthetic_bvd_sweep(other)
    fit = Q.fit_bvd(sweep["freqs_hz"], sweep["Z"])
    assert fit["R"] == pytest.approx(other.R, rel=2e-3)
    assert fit["L"] == pytest.approx(other.L, rel=2e-3)
    assert fit["C"] == pytest.approx(other.C, rel=2e-3)
    assert fit["C0"] == pytest.approx(other.C0, rel=2e-2)


def test_fit_bvd_rejects_a_mismatched_input():
    with pytest.raises(Q.QCMStackError):
        Q.fit_bvd(np.arange(10.0), np.arange(9.0, dtype=complex))


# --- (3) the ring-down ----------------------------------------------------

def test_ringdown_q_recovers_planted_q_and_tau():
    """POWER: recover Q and tau from a synthetic decay."""
    data = Q.synthetic_ringdown(f0=1.0e6, Q=1000.0)
    rd = Q.ringdown_Q(data["signal"], data["t_s"])
    assert rd["tau_s"] == pytest.approx(data["true_tau_s"], rel=0.05)
    assert rd["Q"] == pytest.approx(1000.0, rel=0.05)
    assert rd["f_hz"] == pytest.approx(1.0e6, rel=1e-3)


def test_ringdown_q_definition_matches_omega_tau_over_two():
    data = Q.synthetic_ringdown(f0=1.0e6, Q=1000.0)
    rd = Q.ringdown_Q(data["signal"], data["t_s"])
    assert rd["Q"] == pytest.approx(rd["omega"] * rd["tau_s"] / 2.0, rel=1e-9)


def test_ringdown_recovers_a_different_planted_q():
    data = Q.synthetic_ringdown(f0=2.0e6, Q=1500.0, sample_rate_hz=2.0e7)
    rd = Q.ringdown_Q(data["signal"], data["t_s"])
    assert rd["Q"] == pytest.approx(1500.0, rel=0.05)


def test_ringdown_linewidth_relates_q_to_fwhm():
    """Q = f_s/FWHM must hold within the ring-down itself."""
    data = Q.synthetic_ringdown(f0=1.0e6, Q=1000.0)
    rd = Q.ringdown_Q(data["signal"], data["t_s"])
    # FWHM = 1/(pi*tau); f/FWHM must reproduce the omega*tau/2 Q
    assert rd["fwhm_hz"] == pytest.approx(1.0 / (math.pi * rd["tau_s"]),
                                          rel=1e-9)
    assert rd["q_from_fwhm"] == pytest.approx(rd["Q"], rel=1e-9)


def test_ringdown_refuses_sub_nyquist_sampling():
    with pytest.raises(Q.QCMStackError):
        Q.synthetic_ringdown(f0=1.0e6, Q=1000.0, sample_rate_hz=1.5e6)


# --- (4) the stack self-consistency --------------------------------------

def test_the_three_methods_cross_agree_on_one_synthetic_resonator():
    """Sauerbrey, BVD-linewidth and ring-down agree on f and Q."""
    agreement = Q.stack_agreement()
    assert agreement["f_consistent"] is True
    assert agreement["q_consistent"] is True
    assert agreement["linewidth_consistent"] is True
    assert agreement["all_consistent"] is True
    # the three frequency routes and the two Q routes really do coincide
    assert agreement["f_ringdown_hz"] == pytest.approx(
        agreement["f_s_bvd_hz"], rel=1e-3)
    assert agreement["f0_from_sauerbrey_hz"] == pytest.approx(
        agreement["f_s_bvd_hz"], rel=1e-6)
    assert agreement["Q_ringdown"] == pytest.approx(
        agreement["Q_bvd"], rel=0.02)


# --- (5) the refusals -----------------------------------------------------

def test_refuse_synthetic_fit_as_measured_crystal_always_raises():
    with pytest.raises(Q.QCMStackError) as exc:
        Q.refuse_synthetic_fit_as_measured_crystal()
    assert "BLOCKED_MISSING_INPUT" in str(exc.value)


def test_refuse_model_q_as_device_q_always_raises():
    with pytest.raises(Q.QCMStackError) as exc:
        Q.refuse_model_Q_as_device_Q(q_value=1000.0)
    assert "BLOCKED_MISSING_INPUT" in str(exc.value)


# --- (6) the report -------------------------------------------------------

def test_report_carries_the_verdict_and_measured_here_nothing():
    report = Q.qcmstack_report()
    assert report["verdict"] == "QCM_BVD_RINGDOWN_STACK_MODEL"
    assert Q.VERDICT == "QCM_BVD_RINGDOWN_STACK_MODEL"
    assert report["measured_here"] == "nothing"
    assert report["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert report["claim_class"] in Q.CLAIM_CLASSES
    assert report["stack_agreement"]["all_consistent"] is True
    assert report["what_this_does_not_say"]


def test_module_imports_under_its_package_name():
    from r13 import qcmstack
    assert qcmstack.VERDICT == Q.VERDICT
