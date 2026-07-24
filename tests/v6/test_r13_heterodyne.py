"""P18 — heterodyne detection of a cavity, as a readout model."""

from __future__ import annotations

import numpy as np
import pytest

from r13 import heterodyne as H


# --- a clean, integer-cycle record so projections are exact ---------------

FS = 2000.0
DURATION = 1.0
N = int(FS * DURATION)
T = np.arange(N, dtype=float) / FS       # integer cycles for every tone below


def _tone(amp, f, phase):
    return amp * np.cos(2.0 * np.pi * f * T + phase)


# --- (1) the mix: IF carries amplitude and phase (POWER) ------------------

def test_if_tone_carries_original_amplitude_and_phase():
    amp, f_s, f_lo, phase = 3.0, 200.0, 150.0, 0.7
    w_s, w_lo = 2 * np.pi * f_s, 2 * np.pi * f_lo
    sig = _tone(amp, f_s, phase)
    mix = H.heterodyne_mix(sig, T, w_lo)
    # the IF sits at the signed difference w_s - w_lo
    recovered = mix.if_tone(w_s - w_lo)
    assert abs(abs(recovered) - amp) < 1e-6
    # phase preserved (wrap-safe)
    dphi = np.angle(recovered) - phase
    dphi = (dphi + np.pi) % (2 * np.pi) - np.pi
    assert abs(dphi) < 1e-6


def test_if_tone_test_can_fail_on_wrong_amplitude():
    # guard that the assertion is real: a scaled signal must NOT match
    amp, f_s, f_lo = 3.0, 200.0, 150.0
    w_s, w_lo = 2 * np.pi * f_s, 2 * np.pi * f_lo
    mix = H.heterodyne_mix(_tone(amp, f_s, 0.0), T, w_lo)
    recovered = mix.if_tone(w_s - w_lo)
    assert abs(abs(recovered) - 2 * amp) > 1.0


def test_both_sidebands_appear_the_image_is_present():
    amp, f_s, f_lo = 2.0, 200.0, 150.0
    w_lo = 2 * np.pi * f_lo
    mix = H.heterodyne_mix(_tone(amp, f_s, 0.0), T, w_lo)
    f_if = abs(f_s - f_lo)           # 50 Hz
    f_image = f_s + f_lo             # 350 Hz
    diff = abs(mix.sideband_amplitude(2 * np.pi * f_if))
    summ = abs(mix.sideband_amplitude(2 * np.pi * f_image))
    # both sidebands present at half the signal amplitude
    assert abs(diff - amp / 2) < 1e-6
    assert abs(summ - amp / 2) < 1e-6


def test_if_and_image_frequencies():
    assert H.intermediate_frequency(200.0, 150.0) == 50.0
    assert H.image_frequency(200.0, 150.0) == 350.0


# --- (2) the 3 dB standard-quantum-limit penalty (a MODEL) ----------------

def test_heterodyne_noise_floor_is_3db_above_homodyne():
    hom = H.noise_floor(H.Scheme.HOMODYNE)
    het = H.noise_floor(H.Scheme.HETERODYNE)
    assert het / hom == pytest.approx(2.0)             # factor of two
    assert H.heterodyne_penalty_db() == pytest.approx(10 * np.log10(2))
    assert H.heterodyne_penalty_db() == pytest.approx(3.0103, abs=1e-3)


def test_penalty_is_marked_analytic_model_not_measured():
    budget = H.noise_budget()
    assert budget["claim_class"] == "ANALYTIC_MODEL"
    assert budget["measured_here"] == "nothing"
    assert budget["penalty_is_3db"] is True


# --- (3) the cavity: Lorentzian, FWHM == kappa, phase through pi (POWER) ---

def test_cavity_transmission_is_lorentzian_with_fwhm_equal_kappa():
    kappa = 4.0
    peak = H.cavity_transmission_power(0.0, kappa)
    assert peak == pytest.approx(1.0)
    # half maximum at detuning +/- kappa/2
    half = H.cavity_transmission_power(kappa / 2.0, kappa)
    assert half == pytest.approx(0.5)
    assert H.cavity_fwhm(kappa) == kappa
    # match the Lorentzian shape across a sweep
    delta = np.linspace(-20, 20, 401)
    model = (kappa / 2.0) ** 2 / ((kappa / 2.0) ** 2 + delta ** 2)
    assert np.allclose(H.cavity_transmission_power(delta, kappa), model)


def test_cavity_phase_rolls_through_pi_across_resonance():
    kappa = 4.0
    phase_below = np.angle(H.cavity_response(-1e6, kappa))
    phase_on = np.angle(H.cavity_response(0.0, kappa))
    phase_above = np.angle(H.cavity_response(1e6, kappa))
    assert phase_below == pytest.approx(np.pi / 2, abs=1e-4)
    assert phase_on == pytest.approx(0.0, abs=1e-9)
    assert phase_above == pytest.approx(-np.pi / 2, abs=1e-4)
    assert abs(phase_below - phase_above) == pytest.approx(np.pi, abs=1e-4)


# --- (4) the PDH error signal: antisymmetric, zero on resonance -----------

def test_pdh_error_signal_zero_crossing_on_resonance_and_slope_sign():
    kappa = 4.0
    assert H.pdh_error_signal(0.0, kappa) == pytest.approx(0.0, abs=1e-12)
    # antisymmetric: opposite signs either side
    below = H.pdh_error_signal(-1.0, kappa)
    above = H.pdh_error_signal(1.0, kappa)
    assert below > 0.0 > above
    assert below == pytest.approx(-above)
    # slope through resonance is negative (restoring)
    assert H.pdh_slope_on_resonance(kappa) < 0.0
    eps = 1e-6
    numeric_slope = ((H.pdh_error_signal(eps, kappa)
                      - H.pdh_error_signal(-eps, kappa)) / (2 * eps))
    assert numeric_slope == pytest.approx(H.pdh_slope_on_resonance(kappa),
                                          rel=1e-4)


# --- (5) the load-bearing refusal -----------------------------------------

def test_refuse_model_readout_as_measured_raises():
    with pytest.raises(H.HeterodyneError):
        H.refuse_model_readout_as_measured()


def test_bad_inputs_are_refused():
    with pytest.raises(H.HeterodyneError):
        H.cavity_response(0.0, 0.0)                  # non-positive linewidth
    with pytest.raises(H.HeterodyneError):
        H.heterodyne_mix(np.ones(4), np.ones(3), 1.0)  # shape mismatch


# --- (6) the report --------------------------------------------------------

def test_report_states_verdict_and_measures_nothing():
    r = H.heterodyne_report()
    assert r["verdict"] == "HETERODYNE_CAVITY_READOUT_MODEL"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "ANALYTIC_MODEL"
    assert "what_this_does_not_say" in r
