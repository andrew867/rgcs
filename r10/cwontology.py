"""P07 — what "CW" means, and why a number is not a quantity.

"CW" is three unrelated things that share three letters:

* ``CW_CODE_WORD`` -- a code word in a codebook. Dimensionless. An
  index or a label.
* ``CW_CONTINUOUS_WAVE`` -- Morse/on-off keying of an unmodulated
  carrier. A modulation mode, not a number.
* ``CW_CARRIER_WAVE`` -- the carrier itself, which has a frequency in
  hertz.

Only the third has a frequency. Treating a code word as though it
were a carrier frequency is not a small slip; it is the difference
between an index into a table and a physical quantity in hertz.

This module also enforces programme contract rule 3: **numeric
similarity across incompatible units is not evidence.** 144 the count,
144 Hz, 144 MHz, 144 cm^-1, phase bin 144 and address field 144 are
six different objects that happen to share a decimal representation.
Comparing them is logged as ``UNIT_COLLISION`` and refused.

Nothing here types the R9 CW integer set as a frequency. Those five
values arrived without units, and this module keeps them that way --
``DIMENSIONLESS`` and explicitly ``UNTYPED_DECIMAL`` -- because a
unit that was never observed cannot be recovered by assumption.
"""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction

#: The three distinct referents of "CW", plus the catch-all.
CW_SENSES = {
    "CW_CODE_WORD": {
        "dimension": "DIMENSIONLESS",
        "meaning": "an entry or index in a codebook",
        "has_frequency": False,
    },
    "CW_CONTINUOUS_WAVE": {
        "dimension": "MODULATION_MODE",
        "meaning": ("on-off keying of an unmodulated carrier "
                    "(Morse); a mode, not a quantity"),
        "has_frequency": False,
    },
    "CW_CARRIER_WAVE": {
        "dimension": "FREQUENCY_HZ",
        "meaning": "the carrier itself, measured in hertz",
        "has_frequency": True,
    },
    "CW_UNSPECIFIED": {
        "dimension": "UNKNOWN",
        "meaning": "sense not established by the source record",
        "has_frequency": False,
    },
}

#: Typed dimensions. Values of different dimension never compare.
DIMENSIONS = (
    "DIMENSIONLESS",      # counts, indices, code words
    "FREQUENCY_HZ",
    "WAVENUMBER_CM1",
    "PHASE_BIN",
    "ADDRESS_FIELD",
    "MODULATION_MODE",
    "UNKNOWN",
)


class UnitCollision(TypeError):
    """Raised when values of incompatible dimension are compared."""


class UntypedValue(ValueError):
    """Raised when an untyped decimal is used as a physical quantity."""


@dataclass(frozen=True)
class TypedValue:
    """A number that knows what kind of thing it is."""

    value: Fraction
    dimension: str
    provenance: str

    def __post_init__(self) -> None:
        if self.dimension not in DIMENSIONS:
            raise ValueError(f"unknown dimension {self.dimension!r}")
        object.__setattr__(self, "value", Fraction(self.value))

    def compatible_with(self, other: "TypedValue") -> bool:
        return self.dimension == other.dimension

    def same_as(self, other: "TypedValue") -> bool:
        """Equality, but only within a dimension.

        This is the whole point of the type: 144 Hz and 144 MHz are
        not equal, and neither is comparable to code word 144.
        """
        if not self.compatible_with(other):
            raise UnitCollision(
                f"UNIT_COLLISION: {self.value} [{self.dimension}] and "
                f"{other.value} [{other.dimension}] are different kinds "
                f"of object. Numeric similarity across incompatible "
                f"units is not evidence (programme contract rule 3).")
        return self.value == other.value


def refuse_untyped_as_frequency(value, note: str = "") -> None:
    """Refuse to promote an untyped decimal to a frequency."""
    raise UntypedValue(
        f"{value} arrived without a unit and cannot be read as a "
        f"frequency. A unit that was never observed is not recoverable "
        f"by assumption, and the decimal separator is itself ambiguous "
        f"across locales. {note}".strip())


# --- the R9 CW integer set, typed honestly -----------------------------

#: Public anonymised fixture. Attributed only to the omega region.
CW_INTEGER_SET = (1516, 1496, 20, 644, 2160)

CW_SET_TYPING = {
    "values": list(CW_INTEGER_SET),
    "dimension": "DIMENSIONLESS",
    "sense": "CW_UNSPECIFIED",
    "status": "UNTYPED_DECIMAL",
    "attribution": "from the omega region",
    "note": (
        "these arrived as bare integers. No unit was recorded, so none "
        "is assigned. They are not hertz, not megahertz, not phase "
        "bins and not addresses until a source record says so."),
}


def typed_cw_set() -> list[TypedValue]:
    return [TypedValue(Fraction(v), "DIMENSIONLESS",
                       "omega region, unit not recorded")
            for v in CW_INTEGER_SET]


def collision_report(a: TypedValue, b: TypedValue) -> dict:
    """Describe a comparison without performing an invalid one."""
    ok = a.compatible_with(b)
    return {
        "a": {"value": str(a.value), "dimension": a.dimension},
        "b": {"value": str(b.value), "dimension": b.dimension},
        "comparable": ok,
        "numerically_equal": a.value == b.value,
        "verdict": "COMPARABLE" if ok else "UNIT_COLLISION",
        "note": ("" if ok else
                 "the values may share digits; they do not share a "
                 "kind, so the coincidence is about notation"),
    }


def cw_ontology_report() -> dict:
    return {
        "senses": CW_SENSES,
        "senses_with_frequency": [
            k for k, v in CW_SENSES.items() if v["has_frequency"]],
        "cw_set": CW_SET_TYPING,
        "rule": (
            "a value in hertz, megahertz, inverse centimetres, "
            "radians, an address field, a phase bin, or a "
            "dimensionless statistic is a different typed object. "
            "Numeric similarity across incompatible units is logged as "
            "UNIT_COLLISION, never as evidence."),
        "what_this_does_not_say": (
            "It does not say the values have no unit in reality -- only "
            "that none was recorded here. If a source record later "
            "supplies one, the typing changes and the analysis is "
            "redone. Assigning a unit now would be inventing the "
            "evidence the analysis is supposed to test."),
    }
