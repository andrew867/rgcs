"""R12 — eight radial shells, addressed but not yet projected.

The S3 field of the icosahedral packet grammar is three bits, and three
bits address exactly ``2**3 = 8`` shells. That much is arithmetic and is
asserted. Everything past it is a choice that has not been made.

**A shell index is not a radius.** A 3-bit index picks one of eight
registers; it does not, on its own, name a physical radius. Turning an
index into a radius needs three things declared *independently* of the
index:

1. a **basis** -- is the radius a geocentric radius, an altitude above
   the ellipsoid, or an atomic-shell analogue? (:class:`ShellBasis`);
2. an **origin** -- the radius the innermost register sits at;
3. a **spacing law** -- how the registers step outward.

Fix none of them and the index is ambiguous. :func:`spacing_laws`
carries four candidate laws -- LINEAR, GEOMETRIC, HYDROGENIC_N_SQUARED
and LOGARITHMIC -- and :func:`radii_under_all_laws` shows they return
**different radii for the same index** from the same origin and step. So
the index alone under-determines the radius, and
:func:`refuse_radius_from_index` raises unless basis, origin and law are
all declared.

**The atomic-shell reading is an ANALOGY, not evidence.** That there are
eight registers is not evidence of atomic structure, and hydrogenic
``n**2`` scaling is one candidate law among several -- the same lesson
:mod:`r11.orbitalscaling` reached for planetary radii, where the random
order-statistic null was competitive with the "meaningful" fits.
:func:`refuse_atomic_shell_physics` always raises.

**The observed readings are retained without kinematics.** Three ranges
of one inward-moving shell were reported -- 3478, 1903, 1238 miles,
ordered inward -- with their timestamps MISSING. Without a clock there
is no speed, no orbit and no arrival time, exactly as
:mod:`r11.shelladdr` sets out; those refusals are reused here rather
than restated. The readings map onto the eight-shell register only under
a declared basis, origin and law; with any of those unfixed the mapping
is UNRESOLVED.

Nothing here is measured. The ranges are reported values, the arithmetic
on them is exact, and no radius, index or projection is a physical
observation made by this software. The standing verdict is
**EIGHT_SHELL_REGISTER_DEFINED_PROJECTION_UNRESOLVED**.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from r11 import shelladdr
from r11.shelladdr import (
    MOVING_SHELL_SEQUENCE_A,
    is_ordered_inward,
    refuse_eta,
    refuse_orbit,
    refuse_speed,
)


class Shells8Error(ValueError):
    """Raised when the eight-shell register is asked to over-claim: a
    radius from an undeclared projection, an out-of-range index, atomic
    physics from an analogy, or kinematics from untimed readings."""


# --- typed claim vocabulary (the repository-wide set) ------------------

class ClaimClass(Enum):
    """The claim classes this repository is allowed to emit."""

    EXACT_IDENTITY = "EXACT_IDENTITY"
    SOURCE_ESTABLISHED_PHYSICS = "SOURCE_ESTABLISHED_PHYSICS"
    REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
    ENGINEERING_CANDIDATE = "ENGINEERING_CANDIDATE"
    RETROSPECTIVE_NUMERIC_MATCH = "RETROSPECTIVE_NUMERIC_MATCH"
    PROSPECTIVE_PREDICTION = "PROSPECTIVE_PREDICTION"
    BENCH_MEASUREMENT = "BENCH_MEASUREMENT"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"


CLAIM_CLASS = ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
VERDICT = "EIGHT_SHELL_REGISTER_DEFINED_PROJECTION_UNRESOLVED"

PROJECTION_UNRESOLVED = "PROJECTION_UNRESOLVED"

# --- the count is arithmetic: 3 bits address 8 shells ------------------

S3_BITS = 3
SHELL_COUNT = 2 ** S3_BITS          # 8, asserted at import
assert SHELL_COUNT == 8, "the S3 field is 3 bits and must address 8 shells"

SHELL_INDEX_MIN = 0
SHELL_INDEX_MAX = SHELL_COUNT - 1   # 7


# --- what a shell's radius could be indexed against --------------------

class ShellBasis(Enum):
    """What the shell radius is measured against. Undeclared by default.

    A radius means different things under each basis, so a register whose
    basis is ``UNDECLARED`` carries an index and no radius.
    """

    GEOCENTRIC_RADIUS = "GEOCENTRIC_RADIUS"
    ALTITUDE_ABOVE_ELLIPSOID = "ALTITUDE_ABOVE_ELLIPSOID"
    ATOMIC_SHELL_ANALOGUE = "ATOMIC_SHELL_ANALOGUE"
    UNDECLARED = "UNDECLARED"


class SpacingLaw(Enum):
    """How the eight registers step outward. Several are possible, and
    they disagree, which is the point."""

    LINEAR = "LINEAR"                          # r0 + s * n
    GEOMETRIC = "GEOMETRIC"                    # r0 * (1 + s) ** n
    HYDROGENIC_N_SQUARED = "HYDROGENIC_N_SQUARED"  # r0 * (n + 1) ** 2
    LOGARITHMIC = "LOGARITHMIC"               # r0 + s * ln(n + 1)


def spacing_laws() -> tuple:
    """The candidate spacing laws, in fixed order."""
    return tuple(SpacingLaw)


# --- the shell and the register ----------------------------------------

@dataclass(frozen=True)
class Shell:
    """One radial register, 0..7, with its bounds, units and basis.

    ``inner_radius``/``outer_radius`` are whatever the declared basis and
    units make them; when the basis is ``UNDECLARED`` they are register
    labels, not radii.
    """

    index: int
    inner_radius: float
    outer_radius: float
    units: str
    basis: ShellBasis = ShellBasis.UNDECLARED

    def __post_init__(self) -> None:
        refuse_shell_index_out_of_range(self.index)
        if not isinstance(self.basis, ShellBasis):
            raise Shells8Error(
                f"shell {self.index}: basis must be a ShellBasis member")


def refuse_shell_index_out_of_range(index: int) -> int:
    """Return the index if it addresses a shell; refuse otherwise.

    The S3 field is three bits: only ``0..7`` name a shell. An index
    outside that range is not a small overflow to be clamped, it is an
    address that does not exist.
    """
    if not isinstance(index, int) or isinstance(index, bool):
        raise Shells8Error("shell index must be a plain int")
    if index < SHELL_INDEX_MIN or index > SHELL_INDEX_MAX:
        raise Shells8Error(
            f"refused: shell index {index} is outside 0..{SHELL_INDEX_MAX}. "
            f"The S3 field is {S3_BITS} bits and addresses exactly "
            f"{SHELL_COUNT} shells; an index beyond that range names no "
            f"register.")
    return index


@dataclass(frozen=True)
class ShellRegister:
    """The eight radial shells, indexed 0..7."""

    shells: tuple
    basis: ShellBasis = ShellBasis.UNDECLARED

    def __post_init__(self) -> None:
        if len(self.shells) != SHELL_COUNT:
            raise Shells8Error(
                f"the register holds exactly {SHELL_COUNT} shells, got "
                f"{len(self.shells)}")
        for i, shell in enumerate(self.shells):
            if not isinstance(shell, Shell):
                raise Shells8Error(f"entry {i} is not a Shell")
            if shell.index != i:
                raise Shells8Error(
                    f"shell at position {i} carries index {shell.index}")

    def shell(self, index: int) -> Shell:
        return self.shells[refuse_shell_index_out_of_range(index)]


def _undeclared_register(units: str = "REGISTER_LABEL") -> ShellRegister:
    """Eight shells whose radii are labels, not radii: basis UNDECLARED."""
    return ShellRegister(
        shells=tuple(Shell(i, float(i), float(i + 1), units,
                           ShellBasis.UNDECLARED)
                     for i in range(SHELL_COUNT)),
        basis=ShellBasis.UNDECLARED)


#: The register as it stands: eight registers, no basis, no radii.
DEFAULT_REGISTER = _undeclared_register()


# --- the unresolved projection: index -> radius needs three choices ----

def radius_under_law(index: int, law: SpacingLaw,
                     origin: float, spacing: float) -> float:
    """Radius for one index under one declared law, origin and spacing.

    This is deliberately not called by anything that has not first passed
    :func:`refuse_radius_from_index`; it is the arithmetic that shows the
    four laws disagree.
    """
    refuse_shell_index_out_of_range(index)
    if not isinstance(law, SpacingLaw):
        raise Shells8Error("law must be a SpacingLaw member")
    r0 = float(origin)
    s = float(spacing)
    n = index
    if law is SpacingLaw.LINEAR:
        return r0 + s * n
    if law is SpacingLaw.GEOMETRIC:
        return r0 * (1.0 + s) ** n
    if law is SpacingLaw.HYDROGENIC_N_SQUARED:
        return r0 * (n + 1) ** 2
    if law is SpacingLaw.LOGARITHMIC:
        return r0 + s * math.log(n + 1)
    raise Shells8Error(f"unknown spacing law {law!r}")


def radii_under_all_laws(index: int, origin: float = 1.0,
                         spacing: float = 1.0) -> dict:
    """The radius each candidate law assigns to one index.

    Same index, same origin, same step, four different radii. That the
    values disagree is the demonstration that the index alone does not
    determine a radius.
    """
    return {law.value: radius_under_law(index, law, origin, spacing)
            for law in SpacingLaw}


def laws_disagree(index: int = 3, origin: float = 1.0,
                  spacing: float = 1.0, tol: float = 1e-9) -> bool:
    """True iff the four laws give pairwise-distinct radii for an index."""
    values = list(radii_under_all_laws(index, origin, spacing).values())
    for i in range(len(values)):
        for j in range(i + 1, len(values)):
            if abs(values[i] - values[j]) <= tol:
                return False
    return True


def refuse_radius_from_index(index: int,
                             basis: ShellBasis | None = None,
                             origin: float | None = None,
                             law: SpacingLaw | None = None,
                             spacing: float | None = None) -> float:
    """Refuse a radius from an index unless the projection is declared.

    A radius needs a basis (and not ``UNDECLARED``), an origin, and a
    spacing law -- all fixed independently of the index. With any of them
    missing the answer is not a radius, it is one of four different radii
    the same index would take under laws nobody has chosen. With all of
    them declared this returns that radius, labelled by the choices that
    produced it.
    """
    refuse_shell_index_out_of_range(index)
    missing = []
    if basis is None or basis is ShellBasis.UNDECLARED:
        missing.append("basis")
    if origin is None:
        missing.append("origin")
    if law is None:
        missing.append("law")
    if missing:
        raise Shells8Error(
            f"refused: cannot map shell index {index} to a radius while "
            f"{', '.join(missing)} {'is' if len(missing) == 1 else 'are'} "
            f"undeclared. A 3-bit index picks a register, not a length; "
            f"the same index takes four different radii under LINEAR, "
            f"GEOMETRIC, HYDROGENIC_N_SQUARED and LOGARITHMIC laws "
            f"(see radii_under_all_laws). Declare a basis, an origin and a "
            f"law -- each independently of the index -- or leave the "
            f"projection {PROJECTION_UNRESOLVED}.")
    if not isinstance(basis, ShellBasis):
        raise Shells8Error("basis must be a ShellBasis member")
    if not isinstance(law, SpacingLaw):
        raise Shells8Error("law must be a SpacingLaw member")
    return radius_under_law(index, law, float(origin),
                            0.0 if spacing is None else float(spacing))


def refuse_atomic_shell_physics(*_args, **_kwargs) -> None:
    """Refuse to read eight shells as evidence of atomic structure.

    Eight registers is a fact about a 3-bit field, not about atoms. The
    atomic-shell reading is an ANALOGY: hydrogenic ``n**2`` scaling is
    one candidate law among several, and -- as :mod:`r11.orbitalscaling`
    found for planetary radii -- a random order-statistic null is
    competitive with the "meaningful" fit. An analogy that a random
    control matches is not evidence, and this always raises.
    """
    raise Shells8Error(
        "refused: eight shells is not evidence of atomic structure. That "
        "the S3 field addresses 2**3 = 8 registers is arithmetic about a "
        "3-bit field; reading it as electron shells is an ANALOGY only. "
        "Hydrogenic n**2 scaling is one candidate spacing law among four "
        "here, and the r11.orbitalscaling result stands: a random "
        "order-statistic null is competitive with the 'meaningful' fit, "
        "so an analogy a random control matches carries no evidential "
        "weight. No atomic physics is claimed from the shell count.")


# --- the observed readings: retained, no kinematics --------------------

#: The three reported ranges of one inward-moving shell, in miles, in the
#: candidate order reported. Neutral alias reusing the r11 sequence.
OBSERVED_SHELL_READINGS_MILES: tuple = (
    Fraction(3478), Fraction(1903), Fraction(1238))

#: The readings carry no timestamps, so no kinematics are derivable.
OBSERVED_READINGS_TIMESTAMPS = None


def observed_readings_ordered_inward() -> bool:
    """True iff the reported ranges are strictly decreasing (inward).

    Reuses :func:`r11.shelladdr.is_ordered_inward` on the R11 sequence,
    which carries the same three ranges, rather than re-checking a second
    copy of the numbers.
    """
    return is_ordered_inward(MOVING_SHELL_SEQUENCE_A)


def refuse_reading_kinematics(quantity: str = "speed") -> None:
    """Refuse speed, orbit or arrival time from the untimed readings.

    Delegates to the R11 refusals so the reasoning is reused, not
    restated: three ranges with MISSING timestamps have no time
    difference to divide by, so no speed, orbit or ETA exists.
    """
    key = str(quantity).lower()
    try:
        if key in ("orbit", "trajectory"):
            refuse_orbit()
        elif key in ("eta", "arrival", "arrival_time"):
            refuse_eta()
        else:
            refuse_speed()
    except shelladdr.ShellAddrError as exc:
        raise Shells8Error(str(exc)) from exc
    raise Shells8Error(                                   # pragma: no cover
        "refused: the untimed readings carry no kinematics")


def map_readings_onto_register(basis: ShellBasis | None = None,
                               origin: float | None = None,
                               law: SpacingLaw | None = None,
                               spacing: float | None = None) -> dict:
    """Map the three readings onto the register, only under a declared law.

    With basis, origin and law all declared, each reading is placed at
    the shell whose radius (under that law) is nearest to it, and the
    mapping is returned. With any of them undeclared the mapping is
    ``PROJECTION_UNRESOLVED`` and no reading is placed -- the readings are
    retained, but a placement without a declared projection would be one
    of several, presented as the one.
    """
    if basis is None or basis is ShellBasis.UNDECLARED \
            or origin is None or law is None:
        return {
            "status": PROJECTION_UNRESOLVED,
            "readings_miles": [str(r) for r in OBSERVED_SHELL_READINGS_MILES],
            "ordered_inward": observed_readings_ordered_inward(),
            "timestamps": OBSERVED_READINGS_TIMESTAMPS,
            "placements": None,
            "note": (
                "the readings are retained; a placement without a declared "
                "basis, origin and law would be one of several possible "
                "mappings presented as the mapping"),
        }
    radii = [radius_under_law(i, law, float(origin),
                              0.0 if spacing is None else float(spacing))
             for i in range(SHELL_COUNT)]
    placements = []
    for reading in OBSERVED_SHELL_READINGS_MILES:
        target = float(reading)
        best_i = min(range(SHELL_COUNT),
                     key=lambda i: abs(radii[i] - target))
        placements.append({"reading_miles": str(reading),
                           "shell_index": best_i,
                           "shell_radius": radii[best_i]})
    return {
        "status": "PROJECTION_DECLARED",
        "basis": basis.value,
        "origin": float(origin),
        "law": law.value,
        "readings_miles": [str(r) for r in OBSERVED_SHELL_READINGS_MILES],
        "ordered_inward": observed_readings_ordered_inward(),
        "timestamps": OBSERVED_READINGS_TIMESTAMPS,
        "placements": placements,
    }


# --- the report --------------------------------------------------------

def shells8_report() -> dict:
    return {
        "what_this_is": (
            "a register of exactly eight radial shells addressed by the "
            "3-bit S3 field, whose projection from index to physical "
            "radius is unresolved without a declared basis, origin and "
            "spacing law"),
        "s3_bits": S3_BITS,
        "shell_count": SHELL_COUNT,
        "two_cubed_is_eight": 2 ** S3_BITS == SHELL_COUNT,
        "shell_index_range": [SHELL_INDEX_MIN, SHELL_INDEX_MAX],
        "bases": [b.value for b in ShellBasis],
        "spacing_laws": [law.value for law in SpacingLaw],
        "laws_disagree_for_index_3": laws_disagree(3),
        "radii_for_index_3": radii_under_all_laws(3),
        "projection_status": PROJECTION_UNRESOLVED,
        "observed_readings_miles": [
            str(r) for r in OBSERVED_SHELL_READINGS_MILES],
        "observed_readings_ordered_inward":
            observed_readings_ordered_inward(),
        "observed_readings_timestamps": OBSERVED_READINGS_TIMESTAMPS,
        "refusals": [
            "refuse_shell_index_out_of_range",
            "refuse_radius_from_index",
            "refuse_atomic_shell_physics",
            "refuse_reading_kinematics",
        ],
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say the eight shells sit at any particular radii, "
            "that the shell count is evidence of atomic structure, or that "
            "the three readings can be placed on a shell. That 2**3 = 8 is "
            "arithmetic about a 3-bit field; the atomic-shell reading is an "
            "ANALOGY only, and hydrogenic n**2 scaling is one candidate law "
            "among four that give different radii for the same index, so a "
            "radius from an index alone is refused. The three reported "
            "ranges are retained in the order reported with their "
            "timestamps MISSING; without a clock there is no speed, no "
            "orbit and no arrival time, and a placement onto the register "
            "is UNRESOLVED until a basis, origin and law are declared. "
            "Nothing here is measured."),
        "verdict": VERDICT,
    }


__all__ = [
    "Shells8Error", "ClaimClass", "CLAIM_CLASS", "PHYSICAL_VALIDATION",
    "VERDICT", "PROJECTION_UNRESOLVED", "S3_BITS", "SHELL_COUNT",
    "SHELL_INDEX_MIN", "SHELL_INDEX_MAX", "ShellBasis", "SpacingLaw",
    "spacing_laws", "Shell", "refuse_shell_index_out_of_range",
    "ShellRegister", "DEFAULT_REGISTER", "radius_under_law",
    "radii_under_all_laws", "laws_disagree", "refuse_radius_from_index",
    "refuse_atomic_shell_physics", "OBSERVED_SHELL_READINGS_MILES",
    "OBSERVED_READINGS_TIMESTAMPS", "observed_readings_ordered_inward",
    "refuse_reading_kinematics", "map_readings_onto_register",
    "shells8_report",
]
