"""Unit tests: rgcs_core.coherence (COH-M1..M14) — synthetic checks
independent of the golden CSVs (those are in tests/regression)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from rgcs_core.coherence import (analytic_signal, instantaneous_phase,
                                 instantaneous_frequency, circular_mean,
                                 circular_resultant, circular_variance,
                                 rayleigh_test, coherence_window,
                                 coherence_series, noise_baseline_theory,
                                 phase_linearity,
                                 amplitude_normalized_coherence,
                                 band_power_fraction, coherence_onset_time,
                                 coherence_decay_time, phase_locking_value,
                                 windowed_phase_rates,
                                 spatial_phase_anisotropy,
                                 phase_rate_shear_scalar,
                                 circular_variance_tensor,
                                 fit_exponential_decay, model_comparison,
                                 threshold_detect_bootstrap)

FS = 100_000.0
F0 = 5_000.0


def tone(n: int, f0: float = F0, amp: float = 1.0,
         phase0: float = 0.0) -> np.ndarray:
    t = np.arange(n) / FS
    return amp * np.exp(1j * (2 * np.pi * f0 * t + phase0))


def test_analytic_signal_recovers_tone():
    t = np.arange(2000) / FS
    x = np.cos(2 * np.pi * F0 * t)
    z = analytic_signal(x)
    f = instantaneous_frequency(z, FS)
    assert np.mean(f[50:-50]) == pytest.approx(F0, abs=1.0)
    # Real part is the original record.
    assert np.allclose(z.real, x, atol=1e-9)


def test_pure_tone_coherence_is_one():
    _, c = coherence_series(tone(2000), FS)
    assert np.min(c) == pytest.approx(1.0, abs=1e-9)


def test_coherence_amplitude_invariance():
    z = tone(2000)
    _, c1 = coherence_series(z, FS)
    _, c2 = coherence_series(7.3 * z, FS)
    assert np.allclose(c1, c2, atol=1e-12)


def test_white_noise_coherence_near_baseline():
    rng = np.random.default_rng(123)
    z = (rng.standard_normal(4000) + 1j * rng.standard_normal(4000)) \
        / math.sqrt(2)
    _, c = coherence_series(z, FS)
    baseline = noise_baseline_theory(200)
    assert np.mean(c) == pytest.approx(baseline, abs=0.03)
    assert np.max(c) < 0.3


def test_circular_stats_concentrated_and_uniform():
    conc = np.full(50, 0.7)
    assert circular_resultant(conc) == pytest.approx(1.0)
    assert circular_mean(conc) == pytest.approx(0.7)
    assert circular_variance(conc) == pytest.approx(0.0)
    uni = np.linspace(-np.pi, np.pi, 360, endpoint=False)
    assert circular_resultant(uni) == pytest.approx(0.0, abs=1e-12)


def test_rayleigh_calibration():
    rng = np.random.default_rng(20260714)
    p_uniform = rayleigh_test(rng.uniform(-np.pi, np.pi, 100))["p"]
    assert p_uniform > 0.05
    p_conc = rayleigh_test(0.05 * rng.standard_normal(100))["p"]
    assert p_conc < 1e-6


def test_phase_linearity_bounds():
    assert phase_linearity(tone(1000)) == pytest.approx(1.0, abs=1e-9)
    rng = np.random.default_rng(7)
    z = np.exp(1j * rng.uniform(-np.pi, np.pi, 1000))
    assert phase_linearity(z) < 0.2


def test_amplitude_normalized_coherence_matches_for_tone():
    z = tone(2000)
    _, c1 = coherence_series(z, FS)
    _, c2 = amplitude_normalized_coherence(z, FS)
    assert np.allclose(c1, c2, atol=1e-9)


def test_band_power_fraction_bounds():
    assert band_power_fraction(tone(2000), FS, F0, 500.0) \
        == pytest.approx(1.0, abs=1e-6)
    assert band_power_fraction(tone(2000, f0=20_000.0), FS, F0, 500.0) \
        == pytest.approx(0.0, abs=1e-6)


def test_onset_and_decay_times():
    tc = np.arange(20) * 0.5e-3
    c = np.concatenate([np.full(5, 0.1), np.full(15, 0.9)])
    assert coherence_onset_time(tc, c, 0.5) == pytest.approx(tc[5])
    assert math.isnan(coherence_onset_time(tc, np.full(20, 0.1), 0.5))
    # Decay: synthetic exponential fall from a peak.
    t2 = np.arange(30) * 1e-3
    c2 = 0.08 + 0.9 * np.exp(-t2 / 0.01)
    tau = coherence_decay_time(t2, c2, 0.08)
    assert tau == pytest.approx(0.01, rel=0.05)


def test_phase_locking_value_limits():
    ph = np.linspace(0, 100, 1000)
    assert phase_locking_value(ph, ph + 0.3) == pytest.approx(1.0)
    rng = np.random.default_rng(11)
    assert phase_locking_value(ph, rng.uniform(-np.pi, np.pi, 1000)) < 0.1


def test_anisotropy_identities():
    # GAN-05 identity set (ledger G-15 analogue) on the direct scalar.
    s0 = phase_rate_shear_scalar(10.0, 10.0, 10.0)
    assert s0["sigma_phi2_s2"] == 0.0
    s1 = phase_rate_shear_scalar(1.0, 2.0, 4.0)
    s2 = phase_rate_shear_scalar(4.0, 1.0, 2.0)          # permutation
    s3 = phase_rate_shear_scalar(1.0 + 5, 2.0 + 5, 4.0 + 5)  # common shift
    assert s1["sigma_phi2_s2"] == pytest.approx(s2["sigma_phi2_s2"])
    assert s1["sigma_phi2_s2"] == pytest.approx(s3["sigma_phi2_s2"])
    assert s1["sigma_phi2_s2"] == pytest.approx(
        ((1 - 2) ** 2 + (2 - 4) ** 2 + (4 - 1) ** 2) / 3)


def test_windowed_anisotropy_zero_for_identical_channels():
    t = np.arange(3000) / FS
    phi = 2 * np.pi * F0 * t
    phases = np.vstack([phi, phi, phi])
    out = spatial_phase_anisotropy(phases, FS)
    assert out["scalar_rad2_per_s2"] == pytest.approx(0.0, abs=1e-12)


def test_windowed_anisotropy_matches_detuning():
    t = np.arange(3000) / FS
    detunings = [-50.0, 0.0, 50.0]
    phases = np.vstack([2 * np.pi * (F0 + d) * t for d in detunings])
    out = spatial_phase_anisotropy(phases, FS)
    theory = ((2 * np.pi * 50) ** 2 + (2 * np.pi * 100) ** 2
              + (2 * np.pi * 50) ** 2) / 3
    assert out["scalar_rad2_per_s2"] == pytest.approx(theory, rel=1e-6)
    # Common-rate shift invariance on the windowed statistic.
    phases2 = phases + (2 * np.pi * 123.0 * t)
    out2 = spatial_phase_anisotropy(phases2, FS)
    assert out2["scalar_rad2_per_s2"] == pytest.approx(
        out["scalar_rad2_per_s2"], rel=1e-9)


def test_circular_variance_tensor_locked_vs_random():
    t = np.arange(400) / FS
    phi = 2 * np.pi * F0 * t
    locked = np.vstack([phi, phi + 0.5, phi - 0.2])
    out = circular_variance_tensor(locked)
    assert out["scalar_mean_offdiag"] == pytest.approx(0.0, abs=1e-12)
    rng = np.random.default_rng(3)
    rnd = rng.uniform(-np.pi, np.pi, (3, 400))
    assert circular_variance_tensor(rnd)["scalar_mean_offdiag"] > 0.8


def test_fit_exponential_decay_recovers_tau():
    t = np.linspace(0, 0.05, 200)
    y = 2.5 * np.exp(-t / 0.008)
    fit = fit_exponential_decay(t, y)
    assert fit["tau_s"] == pytest.approx(0.008, rel=1e-6)
    assert fit["A"] == pytest.approx(2.5, rel=1e-6)


def test_model_comparison_picks_truth():
    rng = np.random.default_rng(99)
    t = np.linspace(0, 0.1, 150)
    y_exp = 1.0 * np.exp(-t / 0.02) + 0.002 * rng.standard_normal(150)
    mc = model_comparison(t, np.abs(y_exp) + 1e-9)
    assert mc["best_by_AIC"] == "exponential"
    y_const = 0.5 + 0.002 * rng.standard_normal(150)
    mc2 = model_comparison(t, y_const)
    assert mc2["best_by_AIC"] == "no_change"


def test_threshold_bootstrap_reproducible():
    x = np.arange(10, dtype=float)
    rng = np.random.default_rng(5)
    y = np.where(x[:, None] < 5, 0.1, 0.9) + 0.02 * rng.standard_normal(
        (10, 8))
    r1 = threshold_detect_bootstrap(x, y, n_boot=200, seed=77)
    r2 = threshold_detect_bootstrap(x, y, n_boot=200, seed=77)
    assert r1["threshold"] == r2["threshold"]
    assert (r1["ci_lo"], r1["ci_hi"]) == (r2["ci_lo"], r2["ci_hi"])
    assert r1["ci_lo"] <= r1["threshold"] <= r1["ci_hi"]
    assert 4.0 <= r1["threshold"] <= 5.5


def test_windowed_phase_rates_shape_and_value():
    t = np.arange(1000) / FS
    phases = np.vstack([2 * np.pi * 100.0 * t, 2 * np.pi * 200.0 * t])
    rates = windowed_phase_rates(phases, FS)
    assert rates.shape[0] == 2
    assert np.allclose(rates[0], 2 * np.pi * 100.0, rtol=1e-9)
    assert np.allclose(rates[1], 2 * np.pi * 200.0, rtol=1e-9)
