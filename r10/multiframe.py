"""P08 — the multi-frequency phase frame, exact closures and mixer products.

Four integer frequencies sit in the source delta together: 13 MHz
(13_000_000 Hz), 4096 Hz, 925 Hz, and a 20.48 Hz timebase that is
itself exactly 512/25 Hz. This module does one honest thing with them:
it computes, with exact integer/rational arithmetic, *when* pairs and
triples of these frequencies return to a common phase, and it
enumerates the sum/difference products a mixer would form.

Two closure facts are load-bearing and exact:

    gcd(13_000_000, 4096) = 64   -> the pair closes every 1/64 s
                                    = 15.625 ms exactly
    gcd(13_000_000,  925) = 25   -> the pair closes every 1/25 s
                                    = 40 ms exactly
    gcd(13_000_000, 4096, 925) = 1 -> all three close every 1 s exactly

The closure period is ``Fraction(1, gcd(all frequencies))`` seconds --
never a rounded decimal. Because every frequency is an integer number
of hertz, the arithmetic is exact and the module keeps it that way.

The default output refuses to over-claim. The gcd closures are pure
number theory (verdict ``PHASE_FRAME_EXACT``); they say two integer
frequencies share a beat period, nothing about physics. A *mixer
product* -- the sum or absolute difference of two frequencies -- is
arithmetic too, and this module marks each one
``MIXER_PRODUCT_NO_MEANING_ASSIGNED``. A mixer product is a number you
can compute; it is not a signal anyone detected. ``refuse_mixer_meaning``
raises if someone asks to treat one as a detected tone.

Nothing here is generated, driven, or measured.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from fractions import Fraction

# --- the frozen integer frequencies, exact -----------------------------

FREQ_13MHZ = 13_000_000          # 13 MHz, exact integer hertz
FREQ_4096 = 4096                 # = 2**12, exact
FREQ_925 = 925                   # = 5**2 * 37, exact
DIV_200 = 200
FREQ_20_48 = Fraction(FREQ_4096, DIV_200)     # 512/25 = 20.48 Hz exactly


class MultiFrameError(RuntimeError):
    """Raised when a mixer product is treated as detected evidence."""


# --- exact phase closure via gcd ---------------------------------------

def closure_interval_s(*freqs_hz: int) -> Fraction:
    """Exact common phase-closure interval of integer frequencies.

    Integer frequencies f_1..f_n all return to a common phase at the
    period ``1/gcd(f_1,...,f_n)`` seconds, because gcd is the largest
    frequency that divides them all. Returned as an exact ``Fraction``;
    never rounded.
    """
    if not freqs_hz:
        raise ValueError("need at least one frequency")
    ints = []
    for f in freqs_hz:
        if isinstance(f, Fraction):
            if f.denominator != 1:
                raise ValueError(
                    f"closure_interval_s needs integer hertz, got {f}")
            f = int(f)
        if not isinstance(f, int):
            raise ValueError(f"closure_interval_s needs integers, got {f!r}")
        if f <= 0:
            raise ValueError("frequencies must be positive")
        ints.append(f)
    return Fraction(1, math.gcd(*ints))


def closure_facts() -> dict:
    """The three frozen gcd closures, exact."""
    pair_4096 = closure_interval_s(FREQ_13MHZ, FREQ_4096)
    pair_925 = closure_interval_s(FREQ_13MHZ, FREQ_925)
    triple = closure_interval_s(FREQ_13MHZ, FREQ_4096, FREQ_925)
    return {
        "gcd_13mhz_4096": math.gcd(FREQ_13MHZ, FREQ_4096),          # 64
        "closure_13mhz_4096_s": str(pair_4096),                     # 1/64
        "closure_13mhz_4096_ms": float(pair_4096) * 1e3,            # 15.625
        "gcd_13mhz_925": math.gcd(FREQ_13MHZ, FREQ_925),            # 25
        "closure_13mhz_925_s": str(pair_925),                       # 1/25
        "closure_13mhz_925_ms": float(pair_925) * 1e3,              # 40.0
        "gcd_13mhz_4096_925": math.gcd(FREQ_13MHZ, FREQ_4096, FREQ_925),  # 1
        "closure_triple_s": str(triple),                           # 1
        "all_three_close_at_1s": triple == Fraction(1, 1),
        "verdict": "PHASE_FRAME_EXACT",
    }


def timebase_facts() -> dict:
    """20.48 Hz = 512/25 exactly, and 4096/20.48 = 200 exactly."""
    ratio = Fraction(FREQ_4096) / FREQ_20_48
    return {
        "freq_20_48_hz": str(FREQ_20_48),                # 512/25
        "freq_20_48_equals_512_over_25": FREQ_20_48 == Fraction(512, 25),
        "freq_20_48_float": float(FREQ_20_48),           # 20.48
        "ratio_4096_over_20_48": str(ratio),             # 200
        "ratio_is_exactly_200": ratio == Fraction(200),
        "verdict": "PHASE_FRAME_EXACT",
    }


# --- mixer products carry no meaning -----------------------------------

@dataclass(frozen=True)
class MixerProduct:
    """A sum/difference of two frequencies. Arithmetic, not evidence."""

    f1_hz: Fraction
    f2_hz: Fraction
    sum_hz: Fraction
    difference_hz: Fraction        # absolute difference
    verdict: str = "MIXER_PRODUCT_NO_MEANING_ASSIGNED"


def mixer_product(f1_hz: int | Fraction, f2_hz: int | Fraction
                  ) -> MixerProduct:
    """Exact sum and |difference| of two frequencies.

    A mixer forms f1+f2 and |f1-f2|. This computes both exactly and
    labels the result ``MIXER_PRODUCT_NO_MEANING_ASSIGNED``: the numbers
    are correct arithmetic, and nothing about them is a detected signal.
    """
    a, b = Fraction(f1_hz), Fraction(f2_hz)
    return MixerProduct(
        f1_hz=a, f2_hz=b,
        sum_hz=a + b,
        difference_hz=abs(a - b),
    )


def enumerate_mixer_products() -> list[dict]:
    """Every pairwise mixer product of the four frozen frequencies."""
    freqs = [Fraction(FREQ_13MHZ), Fraction(FREQ_4096),
             Fraction(FREQ_925), FREQ_20_48]
    out = []
    for i in range(len(freqs)):
        for j in range(i + 1, len(freqs)):
            p = mixer_product(freqs[i], freqs[j])
            out.append({
                "f1_hz": str(p.f1_hz),
                "f2_hz": str(p.f2_hz),
                "sum_hz": str(p.sum_hz),
                "difference_hz": str(p.difference_hz),
                "verdict": p.verdict,
            })
    return out


def refuse_mixer_meaning(product: MixerProduct,
                         claimed_signal: str = "a detected tone") -> None:
    """A mixer product is arithmetic; it is never a detected signal."""
    raise MultiFrameError(
        f"the mixer product sum={product.sum_hz} Hz, "
        f"difference={product.difference_hz} Hz is exact arithmetic on "
        f"two frequencies, not {claimed_signal!r}. Calling a sum or "
        f"difference frequency a detected signal invents the evidence: "
        f"no mixer was built, nothing was fed into it, and nothing came "
        f"out. MIXER_PRODUCT_NO_MEANING_ASSIGNED.")


def multiframe_report() -> dict:
    return {
        "frequencies_hz": {
            "13mhz": FREQ_13MHZ,
            "4096": FREQ_4096,
            "925": FREQ_925,
            "20_48": str(FREQ_20_48),
        },
        "closures": closure_facts(),
        "timebase": timebase_facts(),
        "mixer_products": enumerate_mixer_products(),
        "the_discipline": (
            "the gcd closures are exact number theory -- integer "
            "frequencies share a beat period of 1/gcd seconds -- and the "
            "mixer products are exact arithmetic with no meaning "
            "assigned. Neither is a measurement"),
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "PHASE_FRAME_EXACT",
        "what_this_does_not_say": (
            "It does not say these frequencies are physically privileged, "
            "that any apparatus produces or mixes them, or that a sum or "
            "difference frequency was ever detected. A gcd closure is "
            "when two integer frequencies share a phase; a mixer product "
            "is an arithmetic sum or difference. Both are exact, and "
            "neither is evidence of a signal."),
    }
