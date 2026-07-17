"""Oscillator electronics, feedback, and packaging (Agent R10).

A RESONATOR IS NOT AN OSCILLATOR. A resonator is a passive frequency-
selective element; an oscillator adds a sustaining amplifier, a limiter,
and a feedback path — and only the closed loop oscillates. That
distinction is enforced: `is_oscillator()` requires the Barkhausen
conditions, and no passive record can claim oscillation.

Models: Barkhausen criterion, Leeson phase-noise, amplitude control,
temperature compensation (TCF), aging, package stress."""

from __future__ import annotations

import math

import numpy as np


class OscError(RuntimeError):
    pass


def barkhausen(loop_gain: float, loop_phase_deg: float,
               tol_deg: float = 5.0) -> dict:
    """Oscillation start-up requires |G·H| >= 1 at a frequency where
    the loop phase is 0 (mod 360)."""
    phase_ok = abs(((loop_phase_deg + 180) % 360) - 180) <= tol_deg
    gain_ok = loop_gain >= 1.0
    return {"gain_condition": gain_ok, "phase_condition": phase_ok,
            "oscillates": gain_ok and phase_ok,
            "note": "gain > 1 without phase = amplifier; phase "
                    "without gain = filter; oscillation needs both"}


def is_oscillator(record: dict) -> bool:
    """The enforcement point: a system may be called an oscillator
    only with a sustaining amplifier, a declared loop, and Barkhausen
    satisfied. A bare resonator fails all three."""
    return bool(record.get("sustaining_amplifier")
                and record.get("feedback_loop")
                and record.get("barkhausen", {}).get("oscillates"))


def leeson_phase_noise(f0_hz: float, q_loaded: float,
                       noise_figure_db: float, power_dbm: float,
                       flicker_corner_hz: float,
                       offsets_hz=(1.0, 10.0, 100.0, 1e3, 1e4)
                       ) -> dict:
    """Leeson model:
    L(fm) = 10 log10[ (1/2) * (1 + (f0/(2 Q fm))^2)
                      * (1 + fc/fm) * F k T / P ]"""
    k_t = 1.380649e-23 * 290.0
    f_lin = 10 ** (noise_figure_db / 10)
    p_w = 10 ** ((power_dbm - 30) / 10)
    out = {}
    for fm in offsets_hz:
        s = 0.5 * (1 + (f0_hz / (2 * q_loaded * fm)) ** 2) \
            * (1 + flicker_corner_hz / fm) * f_lin * k_t / p_w
        out[f"{fm:g}"] = 10 * math.log10(s)
    return {"f0_hz": f0_hz, "q_loaded": q_loaded,
            "phase_noise_dbc_hz": out,
            "lesson": "loaded Q is the whole game inside the "
                      "half-bandwidth: 2x Q is ~6 dB"}


def amplitude_control(gain_initial: float, settle_target: float =
                      1.0, alr_bandwidth_hz: float = 10.0) -> dict:
    """Automatic level control: excess start-up gain must be shed or
    the resonator is driven nonlinear (drive-level dependence pulls
    the frequency — the DLD channel from C06)."""
    if gain_initial <= 1.0:
        raise OscError("start-up requires loop gain > 1")
    return {"startup_gain": gain_initial,
            "steady_state_gain": settle_target,
            "excess_db": 20 * math.log10(gain_initial),
            "alr_bandwidth_hz": alr_bandwidth_hz,
            "warning": "without ALC the amplitude grows until "
                       "something limits it — usually the resonator's "
                       "nonlinearity, which shifts the frequency"}


def tcf_compensation(f0_hz: float, tcf_ppm_per_c: float,
                     t_c: np.ndarray, t_ref_c: float = 25.0) -> dict:
    """First-order temperature coefficient of frequency and the
    residual after a matched compensation element."""
    t = np.asarray(t_c, float)
    df_ppm = tcf_ppm_per_c * (t - t_ref_c)
    residual_ppm = 0.05 * tcf_ppm_per_c * (t - t_ref_c)  # 95% comp
    return {"uncompensated_ppm": df_ppm.tolist(),
            "compensated_residual_ppm": residual_ppm.tolist(),
            "note": "declared 95% first-order compensation; "
                    "second-order curvature remains"}


def aging_model(f0_hz: float, rate_ppb_per_day: float,
                days: np.ndarray) -> dict:
    """Logarithmic aging: df/f = a * ln(1 + t/tau), the standard
    crystal-aging form; early drift dominates."""
    d = np.asarray(days, float)
    tau = 30.0
    a = rate_ppb_per_day * tau
    drift_ppb = a * np.log1p(d / tau)
    return {"drift_ppb": drift_ppb.tolist(),
            "note": "burn-in captures most aging; a certificate "
                    "issued before burn-in overstates stability"}


def package_stress(f0_hz: float, mount_stress_mpa: float,
                   stress_sensitivity_ppm_per_mpa: float = 0.5
                   ) -> dict:
    return {"df_ppm": mount_stress_mpa
            * stress_sensitivity_ppm_per_mpa,
            "note": "die-attach and lid-seal stress pull frequency; "
                    "package design is a frequency decision"}
