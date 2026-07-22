"""P05 — the 4096 / 925 / 20.48 phase frames, exact, with residuals shown.

A small set of frequencies and ratios is frozen in the source delta.
All of it is exact rational arithmetic, and this module keeps it exact
(``Fraction``) so nothing rounds at a claim boundary.

The one place honesty is load-bearing is the "ratio match". The delta
notes that

    q^{-1} = 4096 / 925 = 4.428108...

is *close* to

    8300 / 1876 = 4.424307...

and the pack is explicit: **the match is approximate and its nonzero
residual must always be shown.** So this module computes the residual
exactly -- 1649/433825, about 0.086% -- and refuses to report the two
as equal. A coincidence at the 1-in-1000 level is a coincidence, not an
identity, and the difference between "close" and "equal" is exactly the
difference this project exists to keep.

Everything here is arithmetic. No frequency is generated, no crystal is
driven, nothing is measured.
"""

from __future__ import annotations

import math
from fractions import Fraction

# --- the frozen quantities, exact --------------------------------------

FREQ_4096 = 4096                 # = 2**12, exact
DIV_200 = 200
FREQ_20_48 = Fraction(FREQ_4096, DIV_200)     # 512/25 = 20.48 exactly

PERIOD_4096_S = Fraction(1, FREQ_4096)        # 244.140625 us exactly
PERIOD_20_48_S = Fraction(1, 1) / FREQ_20_48  # 48.828125 ms exactly

Q = Fraction(925, FREQ_4096)                  # 0.225830078125 exactly
Q_INV = Fraction(FREQ_4096, 925)              # 4.428108...

#: The approximate companion. NOT equal to Q_INV.
APPROX_RATIO = Fraction(8300, 1876)


class ExactnessError(ValueError):
    """Raised when an approximate match is reported as exact."""


def frozen_exact() -> dict:
    """Every frozen quantity, exact, with its float shadow for reading."""
    return {
        "freq_4096_hz": FREQ_4096,
        "is_power_of_two": FREQ_4096 == 2 ** 12,
        "freq_20_48_hz": str(FREQ_20_48),
        "freq_20_48_float": float(FREQ_20_48),
        "period_4096_us": float(PERIOD_4096_S) * 1e6,   # 244.140625
        "period_20_48_ms": float(PERIOD_20_48_S) * 1e3,  # 48.828125
        "q": str(Q),
        "q_float": float(Q),                             # 0.225830078125
        "q_inv": str(Q_INV),
        "q_inv_float": float(Q_INV),
    }


def periods_are_exact() -> bool:
    """The periods are exact dyadic rationals (denominators are 2^k)."""
    return (float(PERIOD_4096_S) * 1e6 == 244.140625
            and float(PERIOD_20_48_S) * 1e3 == 48.828125)


# --- the ratio match, with its residual --------------------------------

def ratio_residual() -> dict:
    """q^-1 vs 8300/1876: close, not equal, residual shown exactly."""
    resid = Q_INV - APPROX_RATIO
    rel = resid / Q_INV
    return {
        "q_inv": str(Q_INV),
        "q_inv_float": float(Q_INV),
        "approx_ratio": str(APPROX_RATIO),
        "approx_ratio_float": float(APPROX_RATIO),
        "residual_exact": str(resid),                    # 1649/433825
        "residual_float": float(resid),
        "relative_residual": float(rel),
        "relative_residual_percent": float(rel) * 100,   # ~0.086%
        "are_equal": resid == 0,
        "verdict": "APPROXIMATE_NOT_EXACT",
        "note": (
            "the two agree to about one part in a thousand and are not "
            "equal. A residual of 1649/433825 is small, and small is "
            "not zero. Reporting them as equal would manufacture an "
            "identity out of a coincidence."),
    }


def refuse_exact_ratio_claim() -> None:
    """Refuse to call the approximate ratio an identity."""
    resid = Q_INV - APPROX_RATIO
    raise ExactnessError(
        f"4096/925 and 8300/1876 are not equal. Their exact difference "
        f"is {resid} ({float(resid):.6g}), about "
        f"{float(resid / Q_INV) * 100:.3f}%. The match is approximate "
        f"and the residual must always be shown; it is not an identity "
        f"and confers no exactness on anything built from it.")


# --- exact residual reporting for an arbitrary frame -------------------

def frame_residual(target_hz: Fraction | int, frame_hz: Fraction | int
                   ) -> dict:
    """How exactly does a target land on a phase frame?

    Returns the exact remainder of target/frame. A zero remainder means
    the target is an exact multiple of the frame; anything else is
    reported as the exact fractional residual, never rounded away.
    """
    t, f = Fraction(target_hz), Fraction(frame_hz)
    if f <= 0:
        raise ValueError("frame frequency must be positive")
    ratio = t / f
    nearest = round(ratio)
    resid = ratio - nearest
    return {
        "target_hz": str(t),
        "frame_hz": str(f),
        "ratio": str(ratio),
        "nearest_integer": nearest,
        "residual_exact": str(resid),
        "residual_float": float(resid),
        "exact_multiple": resid == 0,
    }


# --- other frozen facts, exact -----------------------------------------

def reluctance_wheel_rpm(teeth: int, freq_hz: int) -> Fraction:
    """f = teeth * rpm / 60, inverted for rpm. 200 teeth, 4096 Hz -> 1228.8."""
    if teeth <= 0 or freq_hz <= 0:
        raise ValueError("teeth and frequency must be positive")
    return Fraction(freq_hz * 60, teeth)


def slate_division_degrees(n: int = 24) -> Fraction:
    """360/n. The 24-fold candidate gives 15 degrees exactly."""
    return Fraction(360, n)


def nine_two_five_root_three() -> dict:
    """925*sqrt(3): irrational, so it is float and labelled as such."""
    val = 925 * math.sqrt(3)
    return {
        "value": val,
        "is_exact": False,
        "note": ("sqrt(3) is irrational, so this is a floating-point "
                 "approximation, not an exact rational like the "
                 "frequency ratios"),
    }


def phaseframe_report() -> dict:
    return {
        "exact": frozen_exact(),
        "periods_exact": periods_are_exact(),
        "ratio_match": ratio_residual(),
        "reluctance_wheel_rpm_200_4096": float(
            reluctance_wheel_rpm(200, 4096)),
        "slate_15_degrees": float(slate_division_degrees(24)),
        "the_discipline": (
            "every ratio is exact rational arithmetic; the one "
            "approximate coincidence (4096/925 vs 8300/1876) always "
            "carries its residual and is never called an identity"),
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "It does not say these frequencies are physically "
            "privileged or that any apparatus produces them. 4096 = "
            "2**12 is a property of the radix; the periods are exact "
            "because the frequencies are dyadic; and a ratio matching "
            "another to 0.086% is a coincidence at that level, nothing "
            "more."),
    }
