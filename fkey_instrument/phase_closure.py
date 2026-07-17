"""Phase-closure engine (Agent A05).

Exact commensurability: when do tones close an integer number of
cycles in a common window, how long is that window, and how does
timing quantization erode the closure? All exact (Fraction)."""

from __future__ import annotations

from fractions import Fraction
from math import gcd

from .relations import RelationError, hz


def period_s(f) -> Fraction:
    f = hz(f) if not isinstance(f, Fraction) else f
    if f <= 0:
        raise RelationError("frequency must be positive")
    return 1 / f


def cycles_in(f, window_s) -> Fraction:
    """Exact cycle count of f in a window; integer iff closed."""
    f = hz(f) if not isinstance(f, Fraction) else f
    w = Fraction(window_s) if not isinstance(window_s, Fraction) \
        else window_s
    return f * w


def closes(f, window_s) -> bool:
    return cycles_in(f, window_s).denominator == 1


def common_closure_window(freqs) -> dict:
    """Smallest window in which EVERY tone closes an integer cycle
    count: T = 1 / gcd(f_i) for rational f_i (gcd of fractions =
    gcd(nums)/lcm(dens))."""
    fr = [hz(f) if not isinstance(f, Fraction) else f for f in freqs]
    num = fr[0].numerator
    den = fr[0].denominator
    for f in fr[1:]:
        num = gcd(num, f.numerator)
        den = den * f.denominator // gcd(den, f.denominator)
    g = Fraction(num, den)
    window = 1 / g
    return {"gcd_hz": g, "window_s": window,
            "cycles": {str(f): cycles_in(f, window) for f in fr},
            "note": "every listed tone completes an integer cycle "
                    "count in this window; closure is a timing "
                    "statement, not an energy statement"}


def closure_drift(f_requested, f_realized, window_s) -> dict:
    """Phase error accumulated over a window when the realized
    frequency differs from the requested one (A16/timing notes:
    requested and realized are different fields)."""
    fq = hz(f_requested) if not isinstance(f_requested, Fraction) \
        else f_requested
    fr = f_realized if isinstance(f_realized, Fraction) else \
        hz(f_realized)
    w = Fraction(window_s) if not isinstance(window_s, Fraction) \
        else window_s
    cyc_err = (fr - fq) * w
    return {"requested_hz": fq, "realized_hz": fr,
            "window_s": w,
            "cycle_error": cyc_err,
            "phase_error_deg": cyc_err * 360,
            "closure_preserved": cyc_err == 0,
            "note": "a nonzero realized offset converts an exact "
                    "closure into a slow phase drift; report it, "
                    "never assume the setpoint"}


def burst_lengths(carrier, envelope) -> dict:
    """Burst design: integer carrier cycles per envelope period.
    20480 Hz carrier / 20.48 Hz envelope = exactly 1000 cycles."""
    c = hz(carrier) if not isinstance(carrier, Fraction) else carrier
    e = hz(envelope) if not isinstance(envelope, Fraction) else \
        envelope
    ratio = c / e
    return {"carrier_hz": c, "envelope_hz": e,
            "carrier_cycles_per_envelope": ratio,
            "integer_closure": ratio.denominator == 1,
            "note": "an integer ratio lets every envelope period end "
                    "on a carrier zero crossing (clean bursts); a "
                    "non-integer ratio forces a phase-reset policy"}
