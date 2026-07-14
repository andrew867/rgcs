"""Unit tests: rgcs_core.resonance and rgcs_core.coupled_modes
(RGCS-M.18..M.29, M.46..M.49)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from rgcs_core.resonance import (resonance_offset, linear_detuning,
                                 linewidth_fwhm_hz, effective_q, epsilon_q,
                                 classify_resonance, sweep_span_hz,
                                 corrected_resonance_offset)
from rgcs_core.coupled_modes import (coupled_two_mode, n_mode_eigenproblem,
                                     avoided_crossing_sweep,
                                     coupling_rate_from_g_hz,
                                     g_hz_from_coupling_rate,
                                     coupling_consistency,
                                     coupling_geometry_scaling,
                                     integrate_stuart_landau)


def test_offset_detuning_identity():
    f_m, f_x = 41100.0, 20480.0
    eps = resonance_offset(f_m, f_x)
    d = linear_detuning(f_m, f_x)
    assert eps == pytest.approx((1 + d) ** 2 - 1, rel=1e-12)


def test_q_derived_classes():
    # Q_m = 1000, Q_x = 800 -> Q_eff = 888.9, eps_Q = 1.125e-3 (model doc).
    assert effective_q(1000, 800) == pytest.approx(888.888888888, rel=1e-9)
    eq = epsilon_q(1000, 800)
    assert eq == pytest.approx(1.125e-3, rel=1e-9)
    assert classify_resonance(0.5 * eq, 1000, 800,
                              u_eps=1e-5)["resonance_class"] \
        == "WITHIN_LINEWIDTH"
    assert classify_resonance(3 * eq, 1000, 800,
                              u_eps=1e-5)["resonance_class"] == "NEAR"
    assert classify_resonance(20 * eq, 1000, 800,
                              u_eps=1e-5)["resonance_class"] == "MODERATE"
    assert classify_resonance(100 * eq, 1000, 800,
                              u_eps=1e-5)["resonance_class"] == "FAR"


def test_classification_requires_uncertainty():
    with pytest.raises(TypeError):
        classify_resonance(1e-3, 1000, 800)   # u_eps is mandatory


def test_sweep_span_floors():
    # At zero detuning the 6-linewidth floor dominates (RGCS-M.21).
    span = sweep_span_hz(40960.0, 20480.0, 1000.0, 1000.0)
    assert span == pytest.approx(6 * 40.96)
    # Tiny frequencies with huge Q: 10 Hz floor.
    assert sweep_span_hz(20.0, 10.0, 1e6, 1e6) == 10.0


def test_corrected_offset_sign_flip():
    # Signed corrections can move eps through zero (LT-Delta2).
    base = corrected_resonance_offset(40960.0, 20480.0)
    assert base["epsilon_corrected"] == pytest.approx(0.0, abs=1e-15)
    up = corrected_resonance_offset(40960.0, 20480.0,
                                    deltas_m={"loading": +0.001})
    dn = corrected_resonance_offset(40960.0, 20480.0,
                                    deltas_m={"loading": -0.001})
    assert up["epsilon_corrected"] > 0 > dn["epsilon_corrected"]
    assert up["first_order_valid"]
    big = corrected_resonance_offset(40960.0, 20480.0,
                                     deltas_m={"loading": 0.05})
    assert not big["first_order_valid"]


def test_corrected_offset_uncertainty_near_zero():
    # Near eps = 0: u(eps) ~ 2 sqrt((u_m/f_m)^2 + (u_x/f_x)^2).
    r = corrected_resonance_offset(40960.0, 20480.0, u_f_m_hz=4.096,
                                   u_f_x_hz=2.048)
    expect = 2 * math.sqrt((4.096 / 40960) ** 2 + (2.048 / 20480) ** 2)
    assert r["u_epsilon"] == pytest.approx(expect, rel=1e-6)


def test_two_mode_mixing_and_strong_coupling():
    r = coupled_two_mode(20480.0, 20460.0, 25.0, 1000.0, 800.0)
    assert r["splitting_hz"] == pytest.approx(
        2 * math.hypot(10.0, 25.0))
    assert -45.0 < r["mixing_angle_deg"] <= 45.0
    assert r["strong_coupling_ratio"] == pytest.approx(
        2 * 25.0 / (20480 / 1000 + 20460 / 800))
    # QA-D-04 corrected map: |K| = 2*pi*g (anti-Hermitian K = i*2*pi*g).
    assert r["coupling_rate_s"] == pytest.approx(2.0 * math.pi * 25.0)


def test_n_mode_matches_two_mode():
    two = coupled_two_mode(1000.0, 1000.0, 10.0)
    nm = n_mode_eigenproblem([1000.0, 1000.0],
                             [[0.0, 10.0], [10.0, 0.0]])
    vals = nm["hybrid_frequencies_hz"]
    assert vals[0] == pytest.approx(two["lower_hybrid_hz"])
    assert vals[1] == pytest.approx(two["upper_hybrid_hz"])
    # Eigenvectors orthonormal.
    v = nm["mode_vectors"]
    assert np.allclose(v.T @ v, np.eye(2), atol=1e-12)


def test_avoided_crossing_min_splitting_is_2g():
    sweep = avoided_crossing_sweep(np.linspace(900, 1100, 201), 1000.0, 10.0)
    assert sweep["min_splitting_hz"] == pytest.approx(20.0, rel=1e-6)
    assert np.all(sweep["upper_hz"] >= sweep["lower_hz"])


def test_coupling_consistency_k_equals_two_pi_g():
    # QA-D-04 corrected map: |K| = 2*pi*g.
    g = 12.5
    k = coupling_rate_from_g_hz(g)
    assert k == pytest.approx(2.0 * math.pi * g)
    assert g_hz_from_coupling_rate(k) == pytest.approx(g)
    ok = coupling_consistency(k, g)
    assert ok["consistent"] and not ok["warning_flag"]
    bad = coupling_consistency(2.0 * k, g)
    assert bad["warning_flag"]


def test_coupling_geometry_scaling():
    # g scales as R^-1/2 (H-05): quadrupling R halves g.
    assert coupling_geometry_scaling(10.0, 100.0, 400.0) == pytest.approx(5.0)


def test_stuart_landau_deterministic_ringdown():
    # Single undriven mode: |z| decays as exp(-gamma t) (RGCS-M.49).
    fs, n = 200_000.0, 4000
    gamma = 50.0
    out = integrate_stuart_landau([2 * math.pi * 1000.0], [0.0], [gamma],
                                  [[0.0]], [[0.0]], [1.0 + 0j], fs, n)
    amp = out["amplitude"][:, 0]
    t = out["t_s"]
    assert amp[0] == 1.0
    assert amp[-1] == pytest.approx(math.exp(-gamma * t[-1]), rel=1e-2)


def test_stuart_landau_locking_threshold_pi_delta_f():
    # RGCS-M.48 phase reduction: two saturated modes detuned by delta_f
    # lock when K exceeds K_c ~ pi * delta_f (the same pi factor as the
    # K = pi g frequency-domain consistency map).
    fs, n = 100_000.0, 30_000
    f1, f2 = 1000.0, 1010.0                       # delta_f = 10 Hz
    k_c = math.pi * (f2 - f1)                     # ~31.4 s^-1
    common = dict(
        omega_rad_s=[2 * math.pi * f1, 2 * math.pi * f2],
        gain_s=[400.0, 400.0], damping_s=[100.0, 100.0],
        beta=[[3.0, 0.0], [0.0, 3.0]],
        z0=[10.0 + 0j, 10.0j], fs_hz=fs, n_samples=n)

    def drift(k: float) -> float:
        out = integrate_stuart_landau(
            coupling_k_s=[[0.0, k], [k, 0.0]], **common)
        dphi = np.unwrap(out["phase_rad"][:, 0] - out["phase_rad"][:, 1])
        tail = dphi[n // 2:]
        return float(abs(tail[-1] - tail[0]))     # rad drift over 0.15 s

    assert drift(4.0 * k_c) < 0.05                # locked well above K_c
    expected_unlocked = 2 * math.pi * (f2 - f1) * (n / 2) / fs
    assert drift(0.1 * k_c) > 0.5 * expected_unlocked   # drifting below K_c


def test_stuart_landau_saturation_amplitude():
    # Van-der-Pol-like saturation: steady |z| = sqrt((G - gamma)/beta).
    fs, n = 100_000.0, 60_000
    g, gamma, beta = 400.0, 100.0, 3.0
    out = integrate_stuart_landau([2 * math.pi * 500.0], [g], [gamma],
                                  [[beta]], [[0.0]], [0.1 + 0j], fs, n)
    assert out["amplitude"][-1, 0] == pytest.approx(
        math.sqrt((g - gamma) / beta), rel=1e-3)


def test_stuart_landau_noise_requires_seed():
    with pytest.raises(ValueError):
        integrate_stuart_landau([1.0], [0.0], [1.0], [[0.0]], [[0.0]],
                                [1.0], 1000.0, 10, noise=0.1)


def test_stuart_landau_seeded_reproducibility():
    args = ([2 * math.pi * 100.0], [10.0], [5.0], [[1.0]], [[0.0]],
            [0.5 + 0j], 10_000.0, 500)
    a = integrate_stuart_landau(*args, noise=0.3, seed=42)
    b = integrate_stuart_landau(*args, noise=0.3, seed=42)
    assert np.array_equal(a["z"], b["z"])
