"""A02 — dimensional and precision audit.

Two independent properties are tracked for every quantity, because
conflating them is the programme's most likely self-deception:

1. **Exactness of the arithmetic.** Values are ``Fraction``; binary
   floats are refused at the boundary. ``2.45e9 / 8**9`` really is
   ``18.25392246246337890625`` Hz, exactly.

2. **Empirical significance of the originating input.** ``2.45 GHz`` is
   a *nominal* figure carrying three significant figures. Dividing it
   by an exact power of eight does not manufacture twenty-two digits of
   physical knowledge. The exact quotient is a fact about arithmetic;
   its physical significance is still three figures.

This is transfer firewall 8 (SOURCE_PRECISION_TO_MEASUREMENT_PRECISION)
made mechanical: ``Quantity`` carries ``sig_figs`` and
``precision_audit`` reports any rendering that claims more resolution
than the input supports.

Dimensions are exponent vectors over the seven SI base units, so Hz
(s^-1) can never be silently added to s or to a dimensionless ratio.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from fractions import Fraction

getcontext().prec = 80

BASE_UNITS = ("s", "m", "kg", "A", "K", "mol", "cd")

#: name -> (dimension exponents, factor to SI base)
_DERIVED = {
    "": ((0, 0, 0, 0, 0, 0, 0), Fraction(1)),
    "1": ((0, 0, 0, 0, 0, 0, 0), Fraction(1)),
    "s": ((1, 0, 0, 0, 0, 0, 0), Fraction(1)),
    "m": ((0, 1, 0, 0, 0, 0, 0), Fraction(1)),
    "kg": ((0, 0, 1, 0, 0, 0, 0), Fraction(1)),
    "K": ((0, 0, 0, 0, 1, 0, 0), Fraction(1)),
    "Hz": ((-1, 0, 0, 0, 0, 0, 0), Fraction(1)),
    "rad": ((0, 0, 0, 0, 0, 0, 0), Fraction(1)),
    "N": ((-2, 1, 1, 0, 0, 0, 0), Fraction(1)),
    "J": ((-2, 2, 1, 0, 0, 0, 0), Fraction(1)),
    "W": ((-3, 2, 1, 0, 0, 0, 0), Fraction(1)),
    "nm": ((0, 1, 0, 0, 0, 0, 0), Fraction(1, 10**9)),
    "km": ((0, 1, 0, 0, 0, 0, 0), Fraction(1000)),
    "GHz": ((-1, 0, 0, 0, 0, 0, 0), Fraction(10**9)),
    "MHz": ((-1, 0, 0, 0, 0, 0, 0), Fraction(10**6)),
    "kHz": ((-1, 0, 0, 0, 0, 0, 0), Fraction(1000)),
}


class DimensionError(ValueError):
    """Raised when an operation mixes incompatible dimensions."""


class PrecisionError(ValueError):
    """Raised when a rendering would claim unsupported precision."""


def exact(value) -> Fraction:
    """Exact parse. Floats are REFUSED: a binary float is already an
    approximation and would let a coincidence be manufactured."""
    if isinstance(value, Fraction):
        return value
    if isinstance(value, int):
        return Fraction(value)
    if isinstance(value, Decimal):
        return Fraction(value)
    if isinstance(value, float):
        raise ValueError(
            f"float {value!r} refused: pass an int, Decimal, Fraction, "
            "or decimal string so the value stays exact")
    if isinstance(value, str):
        return Fraction(value.strip())
    raise ValueError(f"cannot parse {value!r} exactly")


@dataclass(frozen=True)
class Dimension:
    exponents: tuple = (0,) * 7

    def __mul__(self, other: "Dimension") -> "Dimension":
        return Dimension(tuple(a + b for a, b in
                               zip(self.exponents, other.exponents)))

    def __truediv__(self, other: "Dimension") -> "Dimension":
        return Dimension(tuple(a - b for a, b in
                               zip(self.exponents, other.exponents)))

    def __pow__(self, n: int) -> "Dimension":
        return Dimension(tuple(a * n for a in self.exponents))

    @property
    def dimensionless(self) -> bool:
        return all(e == 0 for e in self.exponents)

    def __str__(self) -> str:
        parts = [f"{u}^{e}" if e != 1 else u
                 for u, e in zip(BASE_UNITS, self.exponents) if e]
        return "·".join(parts) if parts else "dimensionless"


def unit_dimension(unit: str) -> Dimension:
    if unit not in _DERIVED:
        raise DimensionError(f"unknown unit {unit!r}")
    return Dimension(_DERIVED[unit][0])


@dataclass(frozen=True)
class Quantity:
    """An exact value with a dimension and a declared empirical
    significance.

    ``sig_figs=None`` means *exact by definition* (an integer count, a
    defined constant such as c, or an exact power of two). A finite
    ``sig_figs`` means the originating measurement/nominal figure
    supports only that many digits, however exact the later arithmetic.
    """
    value: Fraction                 # in SI base units
    dimension: Dimension
    sig_figs: int | None = None
    unit_hint: str = ""
    provenance: str = ""
    evidence_class: str = "DERIVED_ARITHMETIC"

    @classmethod
    def of(cls, value, unit: str, sig_figs: int | None = None,
           provenance: str = "",
           evidence_class: str = "DERIVED_ARITHMETIC") -> "Quantity":
        if unit not in _DERIVED:
            raise DimensionError(f"unknown unit {unit!r}")
        dims, factor = _DERIVED[unit]
        return cls(exact(value) * factor, Dimension(dims), sig_figs,
                   unit, provenance, evidence_class)

    # --- algebra --------------------------------------------------------
    def _combine_sig(self, other: "Quantity") -> int | None:
        if self.sig_figs is None:
            return other.sig_figs
        if other.sig_figs is None:
            return self.sig_figs
        return min(self.sig_figs, other.sig_figs)

    def __mul__(self, other):
        if isinstance(other, Quantity):
            return Quantity(self.value * other.value,
                            self.dimension * other.dimension,
                            self._combine_sig(other),
                            provenance=f"({self.provenance})*({other.provenance})")
        return Quantity(self.value * exact(other), self.dimension,
                        self.sig_figs, self.unit_hint, self.provenance)

    def __truediv__(self, other):
        if isinstance(other, Quantity):
            if other.value == 0:
                raise ZeroDivisionError("division by zero quantity")
            return Quantity(self.value / other.value,
                            self.dimension / other.dimension,
                            self._combine_sig(other),
                            provenance=f"({self.provenance})/({other.provenance})")
        return Quantity(self.value / exact(other), self.dimension,
                        self.sig_figs, self.unit_hint, self.provenance)

    def __add__(self, other: "Quantity") -> "Quantity":
        if self.dimension != other.dimension:
            raise DimensionError(
                f"cannot add {self.dimension} to {other.dimension}")
        return Quantity(self.value + other.value, self.dimension,
                        self._combine_sig(other))

    def __sub__(self, other: "Quantity") -> "Quantity":
        if self.dimension != other.dimension:
            raise DimensionError(
                f"cannot subtract {other.dimension} from {self.dimension}")
        return Quantity(self.value - other.value, self.dimension,
                        self._combine_sig(other))

    def __pow__(self, n: int) -> "Quantity":
        return Quantity(self.value ** n, self.dimension ** n,
                        self.sig_figs)

    # --- rendering ------------------------------------------------------
    def in_unit(self, unit: str) -> Fraction:
        """Exact value expressed in ``unit``; refuses a dimension
        mismatch."""
        if unit not in _DERIVED:
            raise DimensionError(f"unknown unit {unit!r}")
        dims, factor = _DERIVED[unit]
        if Dimension(dims) != self.dimension:
            raise DimensionError(
                f"cannot express {self.dimension} as {unit!r} "
                f"({Dimension(dims)})")
        return self.value / factor

    def exact_str(self, unit: str) -> str:
        """Full exact decimal expansion (arithmetic truth). Callers must
        not present this as measured precision — see precision_audit."""
        v = self.in_unit(unit)
        d = Decimal(v.numerator) / Decimal(v.denominator)
        return format(d.normalize(), "f")

    def significant_str(self, unit: str) -> str:
        """Value rounded to the empirically supported significance.

        This is the number that may appear in a physical statement.
        """
        v = self.in_unit(unit)
        d = Decimal(v.numerator) / Decimal(v.denominator)
        if self.sig_figs is None:
            return format(d.normalize(), "f")
        if d == 0:
            return "0"
        from decimal import Context
        return format(Context(prec=self.sig_figs).create_decimal(d)
                      .normalize(), "f")

    def precision_audit(self, unit: str) -> dict:
        """Report exact vs supported rendering and whether quoting the
        exact expansion would overclaim."""
        ex = self.exact_str(unit)
        sig = self.significant_str(unit)
        ex_digits = len(ex.replace("-", "").replace(".", "").lstrip("0"))
        return {
            "unit": unit,
            "exact": ex,
            "supported": sig,
            "sig_figs": self.sig_figs,
            "exact_digits": ex_digits,
            "overclaims_if_quoted_exactly":
                self.sig_figs is not None and ex_digits > self.sig_figs,
            "note":
                "exact arithmetic; empirical significance limited by the "
                f"originating input ({self.sig_figs} s.f.)"
                if self.sig_figs is not None
                else "exact by definition",
            "evidence_class": self.evidence_class,
        }

    def __repr__(self) -> str:
        u = self.unit_hint or str(self.dimension)
        return (f"Quantity({self.significant_str(self.unit_hint) if self.unit_hint else float(self.value)} "
                f"{u}, sig={self.sig_figs})")


# --- defined constants (exact by definition; sig_figs=None) -------------

#: SI-defined speed of light in vacuum.
C_VACUUM = Quantity.of(299792458, "m", None,
                       "SI definition (exact)") / Quantity.of(1, "s", None)
