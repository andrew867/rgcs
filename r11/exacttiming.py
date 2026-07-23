"""P07 — the macrocycle, in exact seconds and exact carrier cycles.

A macrocycle of **552.001953125 ms** sits in the source delta. Written as
a decimal it looks like a measurement someone rounded; written as a
rational it is nothing of the sort. It is

    552.001953125 ms = 552 ms + 1/512 ms = 282625/512000 s = 2261/4096 s

exactly, and the ``4096`` in that denominator is the whole point. The
figure is a dyadic rational -- a whole number of periods of a 4096 Hz
timebase -- so at 4096 Hz the macrocycle closes on an integer, 2261
cycles, with residue exactly zero.

**Why this module refuses floats.** ``552.001953125`` happens to be
representable in binary64, but ``0.552001953125`` seconds compared
against ``2261/4096`` through any chain of float multiplications is a
comparison that can go either way depending on the order of operations,
and a closure claim decided by the last bit of a mantissa is not a
closure claim at all. Every timing quantity here is a ``Fraction`` or an
``int``. :func:`refuse_float_timing` is the load-bearing guard: hand it a
float and it raises rather than quietly accepting a value that has
already lost the exactness the claim depends on.
:func:`refuse_rounded_closure` refuses the second failure mode -- calling
something closed because it is close.

The registered carriers, audited exactly over one macrocycle:

    4096 Hz      -> 2261        cycles      residue 0            EXACT
    925 Hz       -> 2091425/4096 cycles     residue 2465/4096    not exact
                    (= 510.601806640625, fractional part 0.601806640625)
    512/25 Hz    -> 2261/200    cycles      residue 61/200       not exact
    (20.48 Hz)      (= 11.305, fractional part 0.305)
    13 MHz       -> 459265625/64 cycles     residue 25/64        not exact

**The registered residue, and a negative result about it.** The delta
asks to register a macrocycle residue of ``-1/125`` cycle. That value is
retained -- see :func:`registered_residue` -- but it cannot be produced
by any integer-hertz carrier over this macrocycle, and the module says so
rather than bending the macrocycle to fit.

The proof is short. We would need integers ``f`` and ``N`` with

    f * 2261/4096 = N - 1/125
    =>  f = 4096 * (125N - 1) / (125 * 2261) = 4096 * (125N - 1) / 282625

Now ``282625 = 5^3 * 7 * 17 * 19`` is odd, so ``gcd(282625, 4096) = 1``
and ``282625`` must divide ``125N - 1``. But ``282625 = 125 * 2261``, so
in particular ``125`` would have to divide ``125N - 1``, and
``125N - 1 = -1 (mod 125)``, which is never ``0``. No such integer ``f``
exists.

The same fact stated forward: because ``gcd(2261, 4096) = 1``, the map
``f -> f * 2261/4096 mod 1`` runs over **exactly** the multiples of
``1/4096`` as ``f`` runs over the integers. So an integer carrier can
realise a residue ``r`` if and only if ``4096 * r`` is an integer.
``4096 * 0 = 0`` is (witness ``f = 4096``); ``4096 * (-1/125)`` is not.
The registered ``-1/125`` is therefore reported as
``RESIDUE_NOT_REALISABLE_BY_INTEGER_CARRIER``: a supplied datum whose
carrier is unresolved, carried like every other unresolved source value,
and not massaged into agreement.

Everything here is exact rational arithmetic. No clock is read, no
oscillator is run, nothing is timed.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

# --- the macrocycle, exact ----------------------------------------------

#: The macrocycle, in seconds, exactly. 552.001953125 ms = 2261/4096 s.
MACROCYCLE_S = Fraction(2261, 4096)

#: The same value written as it arrives in the delta: 552 ms + 1/512 ms.
MACROCYCLE_MS_LITERAL = Fraction(552) + Fraction(1, 512)      # 282625/512

#: Milliseconds per second, as an exact integer scale factor.
MS_PER_S = 1000

#: The timebase whose denominator the macrocycle is built on.
TIMEBASE_HZ = 4096

#: The residue registered by the source delta, in cycles. See the module
#: docstring: no integer-hertz carrier can realise it over this macrocycle.
REGISTERED_RESIDUE_CYCLES = Fraction(-1, 125)

#: 282625 = 125 * 2261 = 5^3 * 7 * 17 * 19. The modulus in the proof.
RESIDUE_MODULUS = 282625
RESIDUE_MODULUS_FACTORS: tuple[int, ...] = (5, 5, 5, 7, 17, 19)

VERDICT = "EXACT_TIMING_REGISTERED"
RESIDUE_STATUS = "RESIDUE_NOT_REALISABLE_BY_INTEGER_CARRIER"

EVIDENCE_CLASS = "DERIVED_ARITHMETIC"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"


class TimingError(ValueError):
    """Raised when a timing value arrives as a float, when closure is
    claimed from an approximate equality, or when a duration or frequency
    is not a usable exact rational."""


# --- carriers -----------------------------------------------------------

class Carrier(Enum):
    """The registered carriers, by neutral label."""

    F_4096 = "F_4096_HZ"
    F_925 = "F_925_HZ"
    F_20_48 = "F_20_48_HZ"
    F_13MHZ = "F_13_MHZ"


#: Every registered carrier as an exact frequency in hertz. 20.48 Hz is
#: 512/25 exactly; writing it as 20.48 would already be a rounding.
REGISTERED_CARRIERS: dict[Carrier, Fraction] = {
    Carrier.F_4096: Fraction(4096),
    Carrier.F_925: Fraction(925),
    Carrier.F_20_48: Fraction(512, 25),
    Carrier.F_13MHZ: Fraction(13_000_000),
}

#: The same set keyed by plain number, for callers that have a frequency
#: and not a label.
REGISTERED_CARRIER_HZ: tuple[Fraction, ...] = tuple(
    REGISTERED_CARRIERS.values())


# --- the load-bearing guard --------------------------------------------

def refuse_float_timing(x: object, what: str = "timing value") -> Fraction:
    """Refuse a float timing value; return the exact ``Fraction`` otherwise.

    This is the guard the rest of the module is built on. A float has
    already thrown away the distinction between "closes" and "closes to
    within one ulp", and no later arithmetic can put it back. Ints,
    ``Fraction``s and exact decimal strings pass through and are returned
    as ``Fraction``; floats and complex numbers raise.
    """
    if isinstance(x, bool):
        raise TimingError(
            f"refusing a boolean as a {what}: {x!r} is not a duration or "
            f"a frequency.")
    if isinstance(x, float):
        raise TimingError(
            f"refusing the float {x!r} as a {what}. Timing here is exact "
            f"or it is not timing: the macrocycle is {MACROCYCLE_S} s "
            f"({_decimal_str(MACROCYCLE_S * MS_PER_S)} ms) exactly, and a "
            f"binary64 value compared against it decides closure on the "
            f"last bit of a mantissa rather than on arithmetic. Pass "
            f"Fraction({Fraction(x).limit_denominator(10 ** 12)}) or an "
            f"exact decimal string instead.")
    if isinstance(x, complex):
        raise TimingError(
            f"refusing the complex value {x!r} as a {what}.")
    if isinstance(x, (int, Fraction)):
        return Fraction(x)
    try:
        return Fraction(x)                       # exact decimal strings
    except (TypeError, ValueError):
        raise TimingError(
            f"cannot read {x!r} as an exact {what}; give an int, a "
            f"Fraction, or an exact decimal string.") from None


def _decimal_str(x: Fraction) -> str:
    """Exact decimal text when the fraction terminates, else 'p/q'."""
    if x.denominator == 1:
        return str(x.numerator)
    d, twos, fives = x.denominator, 0, 0
    while d % 2 == 0:
        d //= 2
        twos += 1
    while d % 5 == 0:
        d //= 5
        fives += 1
    if d != 1:
        return f"{x.numerator}/{x.denominator}"
    places = max(twos, fives)
    scaled = x.numerator * 10 ** places // x.denominator
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled)).rjust(places + 1, "0")
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


# --- the macrocycle in both units --------------------------------------

def macrocycle_ms() -> Fraction:
    """The macrocycle in milliseconds, exactly: 282625/512 ms."""
    return MACROCYCLE_S * MS_PER_S


def macrocycle_s() -> Fraction:
    """The macrocycle in seconds, exactly: 2261/4096 s."""
    return MACROCYCLE_S


def macrocycle_facts() -> dict:
    """Every way of writing the macrocycle, all of them exact."""
    ms = macrocycle_ms()
    return {
        "seconds_exact": str(MACROCYCLE_S),                     # 2261/4096
        "seconds_decimal": _decimal_str(MACROCYCLE_S),
        "milliseconds_exact": str(ms),                          # 282625/512
        "milliseconds_decimal": _decimal_str(ms),           # 552.001953125
        "milliseconds_as_552_plus_1_over_512":
            ms == MACROCYCLE_MS_LITERAL,
        "seconds_as_282625_over_512000":
            MACROCYCLE_S == Fraction(282625, 512000),
        "milliseconds_as_552001953125_over_1e9":
            ms == Fraction(552001953125, 10 ** 9),
        "denominator_is_the_4096_timebase": MACROCYCLE_S.denominator == 4096,
        "is_dyadic_rational":
            MACROCYCLE_S.denominator & (MACROCYCLE_S.denominator - 1) == 0,
        "numerator": MACROCYCLE_S.numerator,                    # 2261
        "numerator_factors": [7, 17, 19],
        "verdict": VERDICT,
    }


# --- exact cycle counting -----------------------------------------------

def cycles(freq_hz: Fraction | int,
           duration_s: Fraction | int = MACROCYCLE_S) -> Fraction:
    """Exact number of carrier cycles in a duration: f * t.

    Both arguments pass through :func:`refuse_float_timing`, so the
    result is an exact ``Fraction`` or there is no result.
    """
    f = refuse_float_timing(freq_hz, "frequency in hertz")
    t = refuse_float_timing(duration_s, "duration in seconds")
    if f < 0:
        raise TimingError(f"frequency must be non-negative, got {f}")
    if t < 0:
        raise TimingError(f"duration must be non-negative, got {t}")
    return f * t


def whole_cycles(freq_hz: Fraction | int,
                 duration_s: Fraction | int = MACROCYCLE_S) -> int:
    """The integer part of the cycle count (floor), exactly."""
    return math.floor(cycles(freq_hz, duration_s))


def fractional_cycles(freq_hz: Fraction | int,
                      duration_s: Fraction | int = MACROCYCLE_S) -> Fraction:
    """The unsigned fractional part of the cycle count, in [0, 1).

    This is the "how far past the last whole cycle" reading: 925 Hz over
    the macrocycle gives 2465/4096 = 0.601806640625.
    """
    c = cycles(freq_hz, duration_s)
    return c - math.floor(c)


def residue_cycles(freq_hz: Fraction | int,
                   duration_s: Fraction | int = MACROCYCLE_S) -> Fraction:
    """The signed residue of the cycle count, in (-1/2, 1/2].

    The signed form answers "how far is the nearest whole cycle, and in
    which direction", which is the question a phase residue asks. Exact.
    """
    r = fractional_cycles(freq_hz, duration_s)
    return r - 1 if r > Fraction(1, 2) else r


def closes_exactly(freq_hz: Fraction | int,
                   duration_s: Fraction | int = MACROCYCLE_S) -> bool:
    """Does the carrier complete a whole number of cycles in the duration?

    Computed, not asserted, and computed exactly: the cycle count is a
    ``Fraction`` and this asks whether its denominator is 1.
    """
    return cycles(freq_hz, duration_s).denominator == 1


@dataclass(frozen=True)
class CarrierClosure:
    """One carrier audited over one duration. Every field is exact."""

    label: str
    freq_hz: Fraction
    duration_s: Fraction
    cycles: Fraction
    whole_cycles: int
    fractional_cycles: Fraction
    residue_cycles: Fraction
    closes_exactly: bool

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "freq_hz_exact": str(self.freq_hz),
            "freq_hz_decimal": _decimal_str(self.freq_hz),
            "duration_s_exact": str(self.duration_s),
            "cycles_exact": str(self.cycles),
            "cycles_decimal": _decimal_str(self.cycles),
            "whole_cycles": self.whole_cycles,
            "fractional_cycles_exact": str(self.fractional_cycles),
            "fractional_cycles_decimal": _decimal_str(self.fractional_cycles),
            "residue_cycles_exact": str(self.residue_cycles),
            "residue_cycles_decimal": _decimal_str(self.residue_cycles),
            "closes_exactly": self.closes_exactly,
        }


def audit_carrier(freq_hz: Fraction | int,
                  duration_s: Fraction | int = MACROCYCLE_S,
                  label: str = "") -> CarrierClosure:
    """Audit one carrier over one duration, exactly."""
    f = refuse_float_timing(freq_hz, "frequency in hertz")
    t = refuse_float_timing(duration_s, "duration in seconds")
    c = cycles(f, t)
    return CarrierClosure(
        label=label or f"F_{_decimal_str(f)}_HZ",
        freq_hz=f,
        duration_s=t,
        cycles=c,
        whole_cycles=math.floor(c),
        fractional_cycles=fractional_cycles(f, t),
        residue_cycles=residue_cycles(f, t),
        closes_exactly=c.denominator == 1,
    )


def audit_registered_carriers(
        duration_s: Fraction | int = MACROCYCLE_S) -> list[dict]:
    """Every registered carrier over the macrocycle, exact, in order."""
    return [audit_carrier(hz, duration_s, label=c.value).as_dict()
            for c, hz in REGISTERED_CARRIERS.items()]


def carriers_that_close(
        duration_s: Fraction | int = MACROCYCLE_S) -> tuple[str, ...]:
    """Labels of the registered carriers that close exactly. Computed."""
    return tuple(c.value for c, hz in REGISTERED_CARRIERS.items()
                 if closes_exactly(hz, duration_s))


# --- the registered residue and its infeasibility -----------------------

def registered_residue() -> Fraction:
    """The residue the source delta registers: -1/125 cycle, exactly."""
    return REGISTERED_RESIDUE_CYCLES


def achievable_residues_are_multiples_of() -> Fraction:
    """The residue lattice an integer carrier can reach: 1/4096 cycle.

    Because ``gcd(2261, 4096) = 1``, ``f * 2261/4096 mod 1`` runs over
    every multiple of ``1/4096`` as ``f`` runs over the integers, and
    over nothing else.
    """
    return Fraction(1, MACROCYCLE_S.denominator)


def smallest_integer_carrier_for_residue(
        residue: Fraction | int) -> int | None:
    """Smallest positive integer hertz realising ``residue``, or None.

    Solves ``2261 * f = k (mod 4096)`` where ``k = 4096 * residue``. The
    congruence is solvable exactly when ``k`` is an integer, because
    ``gcd(2261, 4096) = 1`` makes 2261 invertible mod 4096.
    """
    r = refuse_float_timing(residue, "residue in cycles")
    n, d = MACROCYCLE_S.numerator, MACROCYCLE_S.denominator
    k = r * d
    if k.denominator != 1:
        return None
    f = (int(k) * pow(n, -1, d)) % d
    return f if f else d          # f = 0 (mod 4096) -> smallest positive


def integer_carrier_with_residue_exists(residue: Fraction | int) -> bool:
    """Can any integer-hertz carrier leave ``residue`` over the macrocycle?

    Computed from the congruence, not asserted. True for 0 (witness
    f = 4096); False for the registered -1/125.
    """
    return smallest_integer_carrier_for_residue(residue) is not None


def residue_feasibility_proof(
        residue: Fraction | int = REGISTERED_RESIDUE_CYCLES) -> dict:
    """The factorisation and the modular argument, as data.

    For ``residue = -1/125`` this reports the chain in the module
    docstring: ``282625 = 5^3 * 7 * 17 * 19``, ``gcd(282625, 4096) = 1``,
    so ``282625 | 125N - 1``; but ``125 | 282625`` and
    ``125N - 1 = -1 (mod 125)``, so no integer carrier exists.
    """
    r = refuse_float_timing(residue, "residue in cycles")
    q = r.denominator
    n, d = MACROCYCLE_S.numerator, MACROCYCLE_S.denominator
    modulus = q * n                       # 125 * 2261 = 282625 for -1/125
    witness = smallest_integer_carrier_for_residue(r)
    feasible = witness is not None
    return {
        "residue_exact": str(r),
        "residue_decimal": _decimal_str(r),
        "macrocycle_s_exact": str(MACROCYCLE_S),
        "equation": (
            f"f * {n}/{d} = N {'-' if r < 0 else '+'} "
            f"{abs(r.numerator)}/{q}  for integers f, N"),
        "solved_for_f": (
            f"f = {d} * ({q}N {'-' if r < 0 else '+'} "
            f"{abs(r.numerator)}) / ({q} * {n}) = {d} * ({q}N "
            f"{'-' if r < 0 else '+'} {abs(r.numerator)}) / {modulus}"),
        "modulus": modulus,
        "modulus_factors": (list(RESIDUE_MODULUS_FACTORS)
                            if modulus == RESIDUE_MODULUS
                            else _factorise(modulus)),
        "modulus_factorisation": _factor_text(
            list(RESIDUE_MODULUS_FACTORS) if modulus == RESIDUE_MODULUS
            else _factorise(modulus)),
        "modulus_is_282625": modulus == RESIDUE_MODULUS,
        "gcd_modulus_4096": math.gcd(modulus, d),
        "gcd_modulus_timebase_is_one": math.gcd(modulus, d) == 1,
        "gcd_2261_4096": math.gcd(n, d),
        "so_modulus_must_divide": (
            f"{q}N {'-' if r < 0 else '+'} {abs(r.numerator)}"),
        "but_modulus_contains_factor": q,
        "and_the_remainder_mod_that_factor": int(
            (-abs(r.numerator) if r < 0 else abs(r.numerator)) % q),
        "modular_contradiction": (
            f"{q} divides {modulus}, so {q} would have to divide "
            f"{q}N {'-' if r < 0 else '+'} {abs(r.numerator)}; but that is "
            f"{'-' if r < 0 else '+'}{abs(r.numerator)} (mod {q}), which is "
            f"never 0" if not feasible else
            "no contradiction: the congruence is solvable"),
        "achievable_residue_lattice": (
            f"multiples of 1/{d} cycle, because gcd({n}, {d}) = 1"),
        "residue_times_timebase": str(r * d),
        "residue_times_timebase_is_integer": (r * d).denominator == 1,
        "integer_carrier_exists": feasible,
        "smallest_integer_carrier_hz": witness,
        "status": (RESIDUE_STATUS if not feasible
                   else "RESIDUE_REALISABLE_BY_INTEGER_CARRIER"),
        "note": (
            "the registered residue is retained as a supplied datum whose "
            "carrier is unresolved. It is not rounded away, and the "
            "macrocycle is not adjusted to accommodate it"
            if not feasible else
            "an integer carrier realises this residue exactly"),
    }


def _factorise(n: int) -> list[int]:
    """Prime factors with multiplicity, ascending. Small integers only."""
    n, out, p = abs(int(n)), [], 2
    while p * p <= n:
        while n % p == 0:
            out.append(p)
            n //= p
        p += 1 if p == 2 else 2
    if n > 1:
        out.append(n)
    return out


def _factor_text(factors: list[int]) -> str:
    """'5^3 * 7 * 17 * 19' from [5, 5, 5, 7, 17, 19]."""
    parts, i = [], 0
    while i < len(factors):
        j = i
        while j < len(factors) and factors[j] == factors[i]:
            j += 1
        parts.append(f"{factors[i]}" if j - i == 1
                     else f"{factors[i]}^{j - i}")
        i = j
    return " * ".join(parts)


def registered_residue_status() -> dict:
    """The registered residue, its proof, and its honest standing."""
    proof = residue_feasibility_proof(REGISTERED_RESIDUE_CYCLES)
    return {
        "registered_residue_exact": str(REGISTERED_RESIDUE_CYCLES),
        "registered_residue_decimal": _decimal_str(REGISTERED_RESIDUE_CYCLES),
        "proof": proof,
        "realisable_by_integer_carrier": False,
        "control_residue_zero_is_realisable":
            integer_carrier_with_residue_exists(Fraction(0)),
        "control_residue_zero_witness_hz":
            smallest_integer_carrier_for_residue(Fraction(0)),
        "status": RESIDUE_STATUS,
        "retained": True,
        "what_was_not_done": (
            "the macrocycle was not rescaled, the residue was not rounded "
            "to the nearest 1/4096, and no non-integer carrier was "
            "invented to absorb it"),
    }


# --- the second refusal: closure is exact or it is not ------------------

def refuse_rounded_closure(freq_hz: Fraction | int = Fraction(925),
                           duration_s: Fraction | int = MACROCYCLE_S,
                           tolerance_cycles: object = None,
                           claim: str = "closes") -> None:
    """Refuse a closure claim resting on an approximate equality.

    Raises unconditionally. Closure is a predicate on an exact rational:
    either the cycle count has denominator 1 or it does not. "Closes to
    within a tolerance" is a different statement, it is not what
    :func:`closes_exactly` reports, and allowing the two to be spoken as
    one is how an arithmetic residue becomes an imagined lock.
    """
    f = refuse_float_timing(freq_hz, "frequency in hertz")
    t = refuse_float_timing(duration_s, "duration in seconds")
    c = cycles(f, t)
    exact = c.denominator == 1
    tol = "" if tolerance_cycles is None \
        else f" within a tolerance of {tolerance_cycles!r} cycles"
    raise TimingError(
        f"refusing the claim that {_decimal_str(f)} Hz {claim}{tol} over "
        f"{_decimal_str(t)} s. The exact cycle count is {c} "
        f"({_decimal_str(c)}), residue {residue_cycles(f, t)}, and this "
        f"carrier "
        f"{'DOES close exactly' if exact else 'does NOT close exactly'}. "
        f"Closure is a denominator, not a distance: a rounded or "
        f"tolerance-bounded equality is a statement about how close two "
        f"numbers are, and closes_exactly reports whether a rational is "
        f"an integer. Use closes_exactly for the predicate and "
        f"residue_cycles for the distance, and do not report the second "
        f"as the first.")


# --- report -------------------------------------------------------------

def exacttiming_report() -> dict:
    """One summary of what this module computes and, loudly, disclaims."""
    return {
        "macrocycle": macrocycle_facts(),
        "carriers": audit_registered_carriers(),
        "carriers_that_close": list(carriers_that_close()),
        "registered_residue": registered_residue_status(),
        "the_discipline": (
            "every duration is a Fraction of a second and every cycle "
            "count is a Fraction of a cycle. refuse_float_timing rejects "
            "a float before it can decide a closure on a mantissa bit, "
            "and refuse_rounded_closure rejects a closure claimed from a "
            "tolerance rather than from a denominator"),
        "what_would_change_this": (
            "an independently supplied carrier frequency -- integer or "
            "not -- that produces the registered -1/125 residue over a "
            "macrocycle no one adjusted afterwards, or a source that "
            "revises the -1/125 figure itself"),
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any oscillator runs at these frequencies, "
            "that any macrocycle was ever timed, or that a clock was "
            "read. It does not say the exact closure at 4096 Hz is "
            "meaningful: 552.001953125 ms is 2261/4096 s, so a 4096 Hz "
            "carrier closes on it by construction -- the closure is a "
            "restatement of how the number was written, not a discovery "
            "about it. It does not say the registered -1/125 residue is "
            "wrong; it says no integer-hertz carrier can produce it over "
            "this macrocycle, so the residue is retained as a supplied "
            "datum with an unresolved carrier "
            "(RESIDUE_NOT_REALISABLE_BY_INTEGER_CARRIER) rather than "
            "forced to fit. And it does not say 925 Hz, 20.48 Hz or "
            "13 MHz fail at anything -- they simply do not close on this "
            "duration, which is arithmetic, not a fault."),
        "verdict": VERDICT,
    }


__all__ = [
    "MACROCYCLE_S", "MACROCYCLE_MS_LITERAL", "MS_PER_S", "TIMEBASE_HZ",
    "REGISTERED_RESIDUE_CYCLES", "RESIDUE_MODULUS", "RESIDUE_MODULUS_FACTORS",
    "VERDICT", "RESIDUE_STATUS", "EVIDENCE_CLASS", "MEASURED_HERE",
    "PHYSICAL_VALIDATION",
    "TimingError",
    "Carrier", "REGISTERED_CARRIERS", "REGISTERED_CARRIER_HZ",
    "refuse_float_timing", "refuse_rounded_closure",
    "macrocycle_s", "macrocycle_ms", "macrocycle_facts",
    "cycles", "whole_cycles", "fractional_cycles", "residue_cycles",
    "closes_exactly", "CarrierClosure", "audit_carrier",
    "audit_registered_carriers", "carriers_that_close",
    "registered_residue", "achievable_residues_are_multiples_of",
    "smallest_integer_carrier_for_residue",
    "integer_carrier_with_residue_exists", "residue_feasibility_proof",
    "registered_residue_status",
    "exacttiming_report",
]
