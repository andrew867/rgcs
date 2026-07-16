"""Agent M12: nonlinear spin + phonon-controlled exchange (gates H6,
H7)."""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core.refmodels import nonlinear_spin as ns

AFM = "reference.nonlinear_afm"
PEX = "reference.phonon_exchange"


def test_equilibrium_and_small_oscillation():
    out = ns.spin_trajectory(AFM, amp=0.0)
    assert not out["value"]["switched"]
    assert np.max(np.abs(out["phi"])) < 1e-9        # stays at minimum
    small = ns.spin_trajectory(AFM, amp=0.1)
    assert small["value"]["regime"] == "under_barrier_oscillation"
    assert 0 < np.max(np.abs(small["phi"])) < 1.0   # sub-barrier


def test_threshold_crossing_switching_and_phase_slip():
    """Gate H6: below/above threshold; ~pi phase slip on switching;
    damping settles to a stable minimum."""
    kw = dict(gamma=0.15, t_end=120.0, n=60000)
    th = ns.switching_threshold(AFM, 0.1, 5.0, **kw)
    assert 0.1 < th["threshold_amp"] < 5.0
    below = ns.spin_trajectory(AFM, th["threshold_amp"] * 0.9, **kw)
    just_above = ns.spin_trajectory(AFM, th["threshold_amp"] * 1.02,
                                    **kw)
    assert not below["value"]["switched"]
    assert just_above["value"]["switched"]
    # ~pi slip in the single-switch band just above threshold
    slip = just_above["value"]["phase_slip_rad"]
    assert slip == pytest.approx(np.pi, rel=0.35)
    # damping settles the switched state
    tail = just_above["phi"][-5000:]
    assert np.std(tail) < 0.05
    assert just_above["value"]["long_lived_offset"] == 1.0
    # strong overdrive legitimately runs through MULTIPLE wells —
    # reported as a larger k*pi slip, not disguised
    hard = ns.spin_trajectory(AFM, th["threshold_amp"] * 1.3, **kw)
    assert hard["value"]["phase_slip_rad"] > np.pi


def test_faraday_projection_and_transfer_function():
    out = ns.spin_trajectory(AFM, amp=0.3)
    assert np.allclose(out["faraday"], np.sin(out["phi"]))
    # identity transfer reproduces the waveform; a smoothing FIR
    # reduces peak drive
    w = ns.gaussian_torque(np.linspace(0, 60, 1000), 5, 0.8, 2.0)
    assert np.array_equal(ns.waveform_transfer(w), w)
    smooth = ns.waveform_transfer(w, np.ones(25) / 25)
    assert np.max(np.abs(smooth)) < np.max(np.abs(w))


def test_deterministic_integration():
    a = ns.spin_trajectory(AFM, amp=1.0)
    b = ns.spin_trajectory(AFM, amp=1.0)
    assert np.array_equal(a["phi"], b["phi"])


def test_exchange_q_null_offresonance_and_shift_signs():
    """Gate H6/H7 support: Q=0 null; off-resonance null; c1 sign sets
    red vs blue shift; transient chirp present."""
    null = ns.phonon_exchange(PEX, drive_amp=0.0, drive_freq=1.0)
    assert abs(null["value"]["max_shift"]) < 1e-9
    on = ns.phonon_exchange(PEX, 0.5, drive_freq=1.0, c1=+0.3)
    off = ns.phonon_exchange(PEX, 0.5, drive_freq=8.0, c1=+0.3)
    assert on["value"]["q_peak"] > 5 * off["value"]["q_peak"]
    assert on["value"]["max_shift"] > 0.01           # blue (c1>0)
    red = ns.phonon_exchange(PEX, 0.5, drive_freq=1.0, c1=-0.3)
    assert red["value"]["min_shift"] < -0.01         # red (c1<0)
    assert on["value"]["max_chirp"] > 0


def test_classifier_direct_vs_indirect():
    """Gate H7: synthetic avoided crossing -> direct; envelope-tracking
    single branch -> indirect; never confused."""
    t = np.linspace(0, 1, 400)
    # direct: two branches with persistent gap
    delta = np.linspace(-1, 1, 400)
    g = 0.2
    upper = np.sqrt(delta ** 2 + g ** 2)
    lower = -np.sqrt(delta ** 2 + g ** 2)
    env = np.exp(-((t - 0.5) / 0.2) ** 2)
    out_d = ns.coupling_mechanism_classifier(
        np.stack([lower, upper]), env)
    assert out_d["mechanism"] == "direct_hybridization"
    # indirect: single branch tracking the drive envelope
    single = 1.0 + 0.1 * env
    out_i = ns.coupling_mechanism_classifier(single[None, :], env)
    assert out_i["mechanism"] == "indirect_parameter_modulation"
    assert out_i["envelope_correlation"] > 0.9
    # the exchange model itself classifies as INDIRECT
    ex = ns.phonon_exchange(PEX, 0.5, 1.0)
    envq = np.convolve(np.abs(ex["q"]),
                       np.ones(500) / 500, mode="same")
    out_m = ns.coupling_mechanism_classifier(ex["omega_s"][None, :],
                                             envq)
    assert out_m["mechanism"] == "indirect_parameter_modulation"


def test_quartz_rejected_both_models():
    a = ns.spin_trajectory("material.alpha_quartz", 1.0)
    b = ns.phonon_exchange("material.alpha_quartz", 0.5, 1.0)
    assert a["classification"] == b["classification"] == \
        "NOT_APPLICABLE"
