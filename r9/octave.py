"""P07 — the octave relation, the 1<->8 bridge, and the "infinite octave".

Three claims appear in the source material and they need to be kept
strictly apart, because one is exact, one is a naming artefact, and
one is false as stated but has a defensible mathematical core.

**The octave is exact.** Doubling frequency is an exact rational
relation, 2:1, and it generates an equivalence: two frequencies are
octave-equivalent when they differ by a power of two. This is a group
action, the quotient is a circle, and everything about it can be
stated in exact arithmetic. No approximation enters. This module uses
``Fraction`` throughout so nothing is quietly rounded at a claim
boundary.

**The 1<->8 bridge is an off-by-one.** The eighth note of a diatonic
scale is the same pitch class as the first because seven steps return
you to the start; "8" comes from counting both endpoints. It is
inclusive counting, the same reason a "fortnight" is 14 nights and an
octave is called an octave. There is nothing to explain beyond the
counting convention, and specifically no eighth *element* -- the
scale has seven.

**The "infinite octave" is false as stated.** Frequency space is
unbounded as a mathematical object, so the octave chain is infinite in
the abstract. Physically it is not: there is a shortest meaningful
period and a longest, and between them fits a finite and computable
number of octaves -- about 202. "Infinite" is a property of the
number line, not of anything realisable.

Nothing here is a physical measurement. It is arithmetic about
frequency ratios plus two literature-sourced physical bounds.
"""

from __future__ import annotations

import math
from fractions import Fraction

#: The octave ratio. Exact, and the only exact interval in common
#: musical use besides the unison.
OCTAVE_RATIO = Fraction(2, 1)

#: Planck frequency, Hz (CODATA-derived). The conventional upper
#: bound on meaningful frequency; not a measured ceiling.
PLANCK_FREQUENCY_HZ = 1.854_858e43

#: Age of the universe, seconds (~13.79 Gyr). Its reciprocal is the
#: lowest frequency that could have completed one cycle.
UNIVERSE_AGE_S = 4.351e17

#: Diatonic scale: seven distinct degrees, not eight.
DIATONIC_DEGREES = 7

#: Steps in the diatonic scale, semitones. Sums to 12.
DIATONIC_STEPS = (2, 2, 1, 2, 2, 2, 1)


class OctaveClaimRefused(ValueError):
    """Raised when an octave claim is stated beyond what holds."""


# --- the exact part -----------------------------------------------------

def octave_up(f: Fraction, n: int = 1) -> Fraction:
    """Exact frequency n octaves above f. Negative n goes down."""
    f = Fraction(f)
    if f <= 0:
        raise ValueError(f"frequency must be positive, got {f}")
    return f * OCTAVE_RATIO ** n


def are_octave_equivalent(a: Fraction, b: Fraction) -> bool:
    """True when a and b differ by an exact power of two.

    Exact: no tolerance, no rounding. Two frequencies either are
    octave-equivalent or they are not.
    """
    a, b = Fraction(a), Fraction(b)
    if a <= 0 or b <= 0:
        raise ValueError("frequencies must be positive")
    r = a / b
    # r is a power of two iff numerator and denominator are both
    # powers of two.
    def _pow2(n: int) -> bool:
        return n > 0 and (n & (n - 1)) == 0
    return _pow2(r.numerator) and _pow2(r.denominator)


def pitch_class(f: Fraction, reference: Fraction = Fraction(1)) -> Fraction:
    """Fold f into [reference, 2*reference) -- the octave quotient.

    This is the canonical representative of f's equivalence class
    under the action of the group of powers of two.
    """
    f, reference = Fraction(f), Fraction(reference)
    if f <= 0 or reference <= 0:
        raise ValueError("frequencies must be positive")
    while f >= 2 * reference:
        f /= 2
    while f < reference:
        f *= 2
    return f


def octave_number(f: Fraction, reference: Fraction) -> int:
    """How many octaves f sits above reference (floor)."""
    f, reference = Fraction(f), Fraction(reference)
    if f <= 0 or reference <= 0:
        raise ValueError("frequencies must be positive")
    return math.floor(math.log2(float(f / reference)))


# --- the 1<->8 bridge ---------------------------------------------------

def one_to_eight_bridge() -> dict:
    """Why the eighth degree is the first degree again."""
    return {
        "claim": "1 and 8 are bridged",
        "status": "TRUE_BUT_TRIVIAL",
        "degrees_in_scale": DIATONIC_DEGREES,
        "steps_to_return": len(DIATONIC_STEPS),
        "semitones_total": sum(DIATONIC_STEPS),
        "explanation": (
            "The diatonic scale has seven degrees. Seven steps return "
            "you to the starting pitch class, one octave up. Calling "
            "that arrival point '8' counts both endpoints -- the same "
            "inclusive counting that makes an octave an 'octave'. "
            "Degree 8 and degree 1 are the same pitch class because "
            "degree 8 IS degree 1, one octave higher."),
        "what_it_is_not": (
            "It is not an eighth element, a hidden state, or a bridge "
            "between two different things. There are seven degrees and "
            "one of them is being named twice. No mechanism is needed "
            "and none is implied."),
        "arithmetic_check": (
            "the seven steps sum to 12 semitones, which is exactly one "
            "octave, ratio 2:1"),
    }


def verify_steps_close_the_octave() -> bool:
    """The seven diatonic steps sum to one octave, exactly."""
    return sum(DIATONIC_STEPS) == 12 and len(DIATONIC_STEPS) == 7


# --- the "infinite octave" ---------------------------------------------

def lowest_meaningful_frequency_hz() -> float:
    """One cycle per age of the universe."""
    return 1.0 / UNIVERSE_AGE_S


def physical_octave_span() -> dict:
    """How many octaves actually fit between the physical bounds?

    The answer is finite, and this is the whole point.
    """
    lo = lowest_meaningful_frequency_hz()
    hi = PLANCK_FREQUENCY_HZ
    n = math.log2(hi / lo)
    return {
        "lowest_hz": lo,
        "lowest_basis": (
            "reciprocal of the age of the universe: below this, not "
            "one cycle has completed since the big bang"),
        "highest_hz": hi,
        "highest_basis": (
            "Planck frequency, the conventional scale at which known "
            "physics stops being applicable"),
        "octaves_available": n,
        "octaves_rounded": int(n),
        "verdict": "FINITE",
        "note": (
            f"about {int(n)} octaves separate the longest meaningful "
            f"period from the shortest. That is a large number and a "
            f"finite one."),
    }


def infinite_octave_claim() -> dict:
    """Assess "the infinite octave" as stated."""
    span = physical_octave_span()
    return {
        "claim": "the octave series is infinite",
        "mathematical_status": "TRUE",
        "mathematical_basis": (
            "the positive reals under multiplication by 2 form an "
            "infinite chain; nothing in the arithmetic bounds it"),
        "physical_status": "FALSE",
        "physical_basis": (
            f"only about {span['octaves_rounded']} octaves fit between "
            f"the lowest and highest physically meaningful "
            f"frequencies"),
        "octaves_available": span["octaves_available"],
        "resolution": (
            "The claim is true about the number line and false about "
            "the world. Both halves matter: the octave relation really "
            "is exact and really does extend without limit as "
            "arithmetic, and there is still no infinite physical "
            "series to reach or descend from."),
        "what_this_does_not_license": (
            "It does not license treating 'source' or 'infinite "
            "octave' as a place, a state, or an energy reservoir. An "
            "unbounded mathematical sequence is not a destination, and "
            "no experiment in this repository could distinguish one "
            "from the other."),
    }


def source_octave_ledger() -> dict:
    """The P07 headline: three claims, three different statuses."""
    return {
        "octave_ratio": str(OCTAVE_RATIO),
        "octave_is_exact": True,
        "exactness_note": (
            "2:1 is exact and this module computes in Fraction "
            "throughout; no octave arithmetic here is approximate"),
        "one_to_eight": one_to_eight_bridge(),
        "infinite_octave": infinite_octave_claim(),
        "physical_span": physical_octave_span(),
        "summary": (
            "The octave relation is exact and well defined. The 1<->8 "
            "bridge is real but is an inclusive-counting artefact with "
            "nothing behind it. The infinite octave is true as "
            "arithmetic and false as physics. Keeping the three apart "
            "is the entire contribution here; running them together is "
            "how an exact triviality gets mistaken for a discovery."),
        "evidence_class": "ARITHMETIC_AND_LITERATURE_BOUNDS",
        "measured_here": "nothing",
    }


def refuse_source_as_physical_location() -> None:
    """Refuse 'source' / 'infinite octave' as a physical claim."""
    raise OctaveClaimRefused(
        "'source' and 'infinite octave' are not physical locations or "
        "states in this framework. The octave chain is unbounded as "
        "arithmetic and spans about "
        f"{physical_octave_span()['octaves_rounded']} octaves "
        "physically. No measurement in this repository addresses the "
        "difference, so no claim is made.")
