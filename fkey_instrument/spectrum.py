"""Waveform and spectrum engine (Agent A06).

Analytic Fourier content for the drive waveforms the instrument can
produce, hardware shaping (finite MOSFET edges), plant filtering, and
alias/Nyquist checks. The A06 gate: a frequency relation is not added
to expected output components until THIS engine (or an explicit
analytic mechanism) produces it."""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np

from .relations import hz


def sine_harmonics(n_max: int = 15) -> dict:
    """An ideal sine has ONE line. Its fifth harmonic is exactly
    zero — the analytic anchor of the whole key comparison."""
    return {1: 1.0, **{n: 0.0 for n in range(2, n_max + 1)}}


def square_harmonics(duty: float = 0.5, n_max: int = 15) -> dict:
    """Fourier magnitude of a unipolar rectangular wave with the DC
    term removed, normalized to the fundamental of the 50% case:
    |c_n| ∝ (2/(n·pi))·|sin(n·pi·d)|. At d = 0.5 the even harmonics
    vanish and odd n carry 1/n — the 5th harmonic is 1/5 of the
    fundamental."""
    if not 0 < duty < 1:
        raise ValueError("duty in (0,1)")
    out = {}
    for n in range(1, n_max + 1):
        out[n] = abs(2.0 / (n * math.pi)
                     * math.sin(n * math.pi * duty))
    return out


def fifth_harmonic_comparison() -> dict:
    """The pack's key comparison, computed not asserted."""
    sq = square_harmonics(0.5)
    return {"sine_fifth": sine_harmonics()[5],
            "square_fifth_over_fundamental": sq[5] / sq[1],
            "statement": "an ideal 4096 Hz sine contains NO 20480 Hz "
                         "component; an ideal 50% square carries an "
                         "odd fifth harmonic at exactly 1/5 of its "
                         "fundamental Fourier amplitude — before any "
                         "hardware or plant filtering"}


def edge_rolloff(harmonic_freq_hz: float, rise_time_s: float) -> float:
    """Finite MOSFET edges low-pass the ideal square: model each edge
    as a linear ramp of duration t_r -> the spectrum is multiplied by
    sinc(pi f t_r). Returns the magnitude factor at one frequency."""
    x = math.pi * harmonic_freq_hz * rise_time_s
    return 1.0 if x == 0 else abs(math.sin(x) / x)


def plant_filter(f_hz: float, f0_hz: float, q: float) -> complex:
    """Second-order resonant transfer (actuator or fixture):
    H(f) = 1 / (1 - (f/f0)^2 + j f/(f0 Q))."""
    r = f_hz / f0_hz
    return 1.0 / complex(1.0 - r * r, r / q)


def expected_line(drive_hz, harmonic: int, duty: float,
                  rise_time_s: float, plant_f0_hz: float,
                  plant_q: float) -> dict:
    """End-to-end expected magnitude of one drive harmonic through
    edges and the plant — the number the optimizer is allowed to use
    as 'expected target spectral amplitude'."""
    f_line = float(hz(drive_hz) * harmonic) \
        if not isinstance(drive_hz, float) else drive_hz * harmonic
    base = square_harmonics(duty, max(harmonic, 1)).get(harmonic, 0.0)
    edge = edge_rolloff(f_line, rise_time_s)
    plant = abs(plant_filter(f_line, plant_f0_hz, plant_q))
    return {"line_hz": f_line, "fourier_amplitude": base,
            "edge_factor": edge, "plant_gain": plant,
            "expected_amplitude": base * edge * plant,
            "mechanism": "HARMONIC" if base > 0 else "NONE",
            "note": "zero fourier_amplitude means the waveform does "
                    "not generate this line at all (A06 gate)"}


def synthesize(waveform: str, f_hz: float, fs_hz: float,
               duration_s: float, duty: float = 0.5) -> np.ndarray:
    t = np.arange(0.0, duration_s, 1.0 / fs_hz)
    if waveform == "sine":
        return np.sin(2 * np.pi * f_hz * t)
    if waveform == "square":
        return np.where((t * f_hz) % 1.0 < duty, 1.0, -1.0)
    raise ValueError(f"unknown waveform {waveform}")


def fft_lines(x: np.ndarray, fs_hz: float, n_lines: int = 8) -> list:
    """Peak lines from an FFT with a Hann window; used to CROSS-CHECK
    the analytic content (A22 requires an independent check)."""
    w = np.hanning(len(x))
    spec = np.abs(np.fft.rfft(x * w))
    freqs = np.fft.rfftfreq(len(x), 1.0 / fs_hz)
    idx = np.argsort(spec)[::-1]
    out = []
    for i in idx:
        f = float(freqs[i])
        if any(abs(f - o["f_hz"]) < fs_hz / len(x) * 4 for o in out):
            continue
        out.append({"f_hz": f, "amplitude": float(spec[i])})
        if len(out) >= n_lines:
            break
    return out


def nyquist_check(f_line_hz: float, fs_hz: float) -> dict:
    """Alias arithmetic: where does a line land after sampling? The
    A17 warning quantified — a 20.48 kHz line sampled at 48 kS/s is
    genuinely below Nyquist but close enough that response rolloff
    must be CALIBRATED, not assumed."""
    ny = fs_hz / 2.0
    if f_line_hz <= ny:
        margin = ny - f_line_hz
        return {"aliased": False, "nyquist_hz": ny,
                "margin_hz": margin,
                "marginal": margin < 0.15 * ny,
                "note": "below Nyquist" +
                        ("; MARGINAL — calibrate the anti-alias and "
                         "sensor rolloff before trusting amplitudes "
                         "(A17)" if margin < 0.15 * ny else "")}
    alias = abs(f_line_hz - round(f_line_hz / fs_hz) * fs_hz)
    return {"aliased": True, "nyquist_hz": ny,
            "appears_at_hz": alias,
            "note": "this line ALIASES: an apparent peak at "
                    f"{alias:.1f} Hz would be a sampling artifact, "
                    "not a mechanical response (A24 attack: fake "
                    "20 kHz peak)"}
