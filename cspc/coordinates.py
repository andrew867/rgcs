"""A04/A05 — unit-aware frequency coordinates and the powers-of-eight
ladder decoder.

A *frequency coordinate* expresses a frequency exactly relative to a
declared reference and radix:

    f = reference * radix**level * residual        (all exact)

``level`` is an integer; ``residual`` is an exact Fraction in
[1, radix). The decomposition is unique and the round trip is exact —
property-tested over broad ranges — because everything is
``Fraction``. A float round trip would quietly manufacture agreement.

Naming discipline (CSPC-CORR-003): with radix 8, ``level`` counts
powers of EIGHT. Level 11 is 8^11 = 2^33, i.e. thirty-three octaves.
``octaves`` is reported separately and is always 3*level for radix 8,
so no document can call an 8-level an octave by accident.

A coordinate is a description, not a mechanism. Landing on a tidy
level says something about arithmetic, never about whether a specimen
responds.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

from .units import Quantity, exact

#: References the programme is allowed to decompose against. Declared
#: up front so a reference cannot be chosen after seeing a result.
REFERENCES = {
    "SRC_2_45_GHZ": Fraction(2450000000),
    "F_4096": Fraction(4096),
    "F_8": Fraction(8),
    "F_1HZ": Fraction(1),
}

LEGAL_RADIX = (2, 8, 10)


class CoordinateError(ValueError):
    pass


@dataclass(frozen=True)
class FrequencyCoordinate:
    """Exact coordinate of a frequency against (reference, radix)."""
    frequency_hz: Fraction
    reference_hz: Fraction
    radix: int
    level: int
    residual: Fraction          # in [1, radix)

    @property
    def octaves(self) -> Fraction:
        """Span in octaves (factors of two). For radix 8 this is
        3*level plus the residual's own octave content — reported so
        'level' is never mistaken for 'octave' (CSPC-CORR-003)."""
        return Fraction(3 if self.radix == 8 else
                        1 if self.radix == 2 else 0) * self.level

    def reconstruct(self) -> Fraction:
        return self.reference_hz * Fraction(self.radix) ** self.level \
            * self.residual

    @property
    def exact_round_trip(self) -> bool:
        return self.reconstruct() == self.frequency_hz

    @property
    def is_exact_power(self) -> bool:
        """True when the frequency sits exactly on a ladder rung."""
        return self.residual == 1

    def to_dict(self) -> dict:
        return {"frequency_hz": str(self.frequency_hz),
                "reference_hz": str(self.reference_hz),
                "radix": self.radix, "level": self.level,
                "residual": str(self.residual),
                "octaves": str(self.octaves),
                "exact_power": self.is_exact_power,
                "claim": "DERIVED_ARITHMETIC; a coordinate is a "
                         "description, not a coupling mechanism"}


def decompose(frequency, reference="SRC_2_45_GHZ", radix: int = 8
              ) -> FrequencyCoordinate:
    """Exact decomposition of ``frequency`` against a declared
    reference and radix."""
    if radix not in LEGAL_RADIX:
        raise CoordinateError(f"radix {radix} not in {LEGAL_RADIX}")
    f = frequency.in_unit("Hz") if isinstance(frequency, Quantity) \
        else exact(frequency)
    if f <= 0:
        raise CoordinateError("frequency must be positive")
    ref = REFERENCES[reference] if isinstance(reference, str) \
        else exact(reference)
    if ref <= 0:
        raise CoordinateError("reference must be positive")

    ratio = f / ref
    level = 0
    r = Fraction(radix)
    # exact integer walk; no logarithms, so no float drift
    while ratio >= r:
        ratio /= r
        level += 1
    while ratio < 1:
        ratio *= r
        level -= 1
    return FrequencyCoordinate(f, ref, radix, level, ratio)


def compose(reference, radix: int, level: int, residual=1) -> Fraction:
    """Inverse of :func:`decompose`, exactly."""
    ref = REFERENCES[reference] if isinstance(reference, str) \
        else exact(reference)
    return ref * Fraction(radix) ** level * exact(residual)


# --- powers-of-eight ladder (A05) ---------------------------------------

@dataclass(frozen=True)
class LadderRung:
    level: int
    frequency_hz: Fraction
    octaves_below_reference: int
    exact_decimal: str


def eight_ladder(reference="SRC_2_45_GHZ", levels: int = 12) -> list:
    """The 2.45 GHz powers-of-eight fold ladder, exactly.

    Rung n is reference / 8**n. Each rung records that it is 3n octaves
    below the reference, never n.
    """
    ref = REFERENCES[reference] if isinstance(reference, str) \
        else exact(reference)
    out = []
    for n in range(levels + 1):
        f = ref / Fraction(8) ** n
        from decimal import Decimal
        d = Decimal(f.numerator) / Decimal(f.denominator)
        out.append(LadderRung(n, f, 3 * n, format(d.normalize(), "f")))
    return out


def decode_to_ladder(frequency, reference="SRC_2_45_GHZ") -> dict:
    """Where does a frequency sit on the powers-of-eight ladder?

    Reports the nearest rung, whether it is exact, and the exact
    residual ratio. An inexact hit is reported as inexact — the decoder
    never rounds a near miss into a rung.
    """
    coord = decompose(frequency, reference, 8)
    # level is negative going down from the reference
    n = -coord.level
    return {
        "nearest_fold_level": n,
        "exact_rung": coord.is_exact_power,
        "residual_ratio": coord.residual,
        "octaves_below_reference": 3 * n,
        "note": f"level {n} means 8^{n} = 2^{3 * n}; that is "
                f"{3 * n} octaves, not {n}",
        "claim": "DERIVED_ARITHMETIC",
    }
