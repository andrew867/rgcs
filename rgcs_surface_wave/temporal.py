"""R10.15 Phase B10 — temporal switching coefficients.

    S_n = (1/T_m) integral_0^{T_m} S(t) exp(+i n omega_m t) dt

Analytic coefficients are given where they exist (sinusoid, square,
PWM) and every waveform is ALSO evaluated by exact DFT quadrature, so
the two paths cross-check each other. Parseval closes against the mean
square of the waveform.

The ``sham`` waveform is the control that matters most: identical mean
value and identical dissipated power, zero modulation depth. Any
effect that survives a sham drive is not a modulation effect.
"""

from __future__ import annotations

import cmath
import math

import numpy as np

from rgcs_surface_wave.evidence import ClaimClass

WAVEFORMS = ("sinusoidal", "stepped", "pwm", "traveling", "reversed",
             "sham", "randomized")


class TemporalError(ValueError):
    pass


def _samples(kind: str, n_samples: int, duty: float, depth: float,
             phase_rad: float, seed: int) -> np.ndarray:
    t = np.arange(n_samples) / n_samples          # one period, [0,1)
    if kind == "sinusoidal":
        return 1.0 + depth * np.cos(2 * np.pi * t + phase_rad)
    if kind in ("stepped", "pwm"):
        # PWM allows a phase offset; 'stepped' is the zero-phase square
        shifted = (t - (phase_rad / (2 * np.pi) if kind == "pwm" else 0.0)) % 1.0
        return np.where(shifted < duty, 1.0, 0.0)
    if kind == "traveling":
        # unit-amplitude single-harmonic travelling drive
        return 1.0 + depth * np.cos(2 * np.pi * t + phase_rad)
    if kind == "reversed":
        return 1.0 + depth * np.cos(-2 * np.pi * t + phase_rad)
    if kind == "sham":
        # SAME mean and SAME mean-square as the stepped drive, but no
        # modulation: a constant at the RMS level of the square wave.
        return np.full(n_samples, math.sqrt(duty))
    if kind == "randomized":
        rng = np.random.default_rng(seed)
        return (rng.random(n_samples) < duty).astype(float)
    raise TemporalError(
        f"unknown waveform {kind!r}; declared waveforms are "
        f"{', '.join(WAVEFORMS)}")


def analytic_coefficient(kind: str, n: int, duty: float = 0.5,
                         depth: float = 1.0,
                         phase_rad: float = 0.0) -> complex | None:
    """Closed-form S_n where one exists, else None."""
    if kind in ("sinusoidal", "traveling"):
        if n == 0:
            return 1.0 + 0j
        if n == 1:
            return 0.5 * depth * cmath.exp(1j * phase_rad)
        if n == -1:
            return 0.5 * depth * cmath.exp(-1j * phase_rad)
        return 0j
    if kind == "reversed":
        if n == 0:
            return 1.0 + 0j
        if n == -1:
            return 0.5 * depth * cmath.exp(1j * phase_rad)
        if n == 1:
            return 0.5 * depth * cmath.exp(-1j * phase_rad)
        return 0j
    if kind == "stepped":
        if n == 0:
            return complex(duty)
        return (cmath.exp(1j * 2 * math.pi * n * duty) - 1.0) \
            / (1j * 2 * math.pi * n)
    if kind == "sham":
        return complex(math.sqrt(duty)) if n == 0 else 0j
    return None


def coefficients(kind: str, n_max: int = 16, duty: float = 0.5,
                 depth: float = 1.0, phase_rad: float = 0.0,
                 seed: int = 20260728, n_samples: int = 4096) -> dict:
    """Exact DFT coefficients plus analytic cross-check and Parseval."""
    if not (0.0 < duty <= 1.0):
        raise TemporalError("duty must lie in (0, 1]")
    if depth < 0:
        raise TemporalError("modulation depth must be non-negative")
    s = _samples(kind, n_samples, duty, depth, phase_rad, seed)
    # S_n with exp(+i n omega t): conjugate of the numpy forward DFT
    spec = np.conj(np.fft.fft(s)) / n_samples
    out, analytic, worst = {}, {}, 0.0
    for n in range(-n_max, n_max + 1):
        c = complex(spec[n % n_samples])
        out[n] = c
        a = analytic_coefficient(kind, n, duty, depth, phase_rad)
        if a is not None:
            analytic[n] = a
            worst = max(worst, abs(a - c))
    lhs = float(np.mean(np.abs(s) ** 2))
    rhs = float(np.sum(np.abs(spec) ** 2))
    return {
        "schema": "rgcs.r1015.temporal.v1",
        "waveform": kind, "duty": duty, "depth": depth,
        "phase_rad": phase_rad, "n_max": n_max,
        "coefficients": {str(n): [c.real, c.imag]
                         for n, c in out.items()},
        "magnitude": {str(n): abs(c) for n, c in out.items()},
        "dc": abs(out[0]),
        "analytic_available": bool(analytic),
        "analytic_max_deviation": worst,
        "parseval_lhs_mean_square": lhs,
        "parseval_rhs_sum_sq": rhs,
        "parseval_residual": abs(lhs - rhs),
        "modulation_depth_effective": (
            0.0 if kind == "sham"
            else float(max(abs(c) for n, c in out.items() if n != 0))),
        "is_control": kind in ("sham", "randomized"),
        "claim_class": ClaimClass.DERIVED.value,
    }


def sham_matches(reference: dict, sham: dict,
                 tol: float = 1e-9) -> dict:
    """Verify the sham control matches mean power but not modulation."""
    same_power = abs(reference["parseval_lhs_mean_square"]
                     - sham["parseval_lhs_mean_square"]) < tol
    no_mod = sham["modulation_depth_effective"] < tol
    return {"same_mean_square_power": bool(same_power),
            "sham_has_no_modulation": bool(no_mod),
            "valid_control": bool(same_power and no_mod),
            "note": "a valid sham dissipates the same average power "
                    "with zero modulation depth, so any surviving "
                    "effect is not a modulation effect"}
