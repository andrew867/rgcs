"""P39 — the eight-shell radial mapping model, and the two over-claims it
refuses.

R12's :mod:`r12.shells8` established that a 3-bit S3 field addresses
exactly ``2**3 = 8`` radial registers, and that turning an index into a
physical radius needs a basis, an origin and a spacing law declared
independently of the index. This module builds the concrete layered model
on top of that register: eight concentric shells with explicit boundary
radii, a boundary-to-index assignment, and the wave physics of crossing a
boundary.

**The mapping is a coarse bin.** :class:`EightShell` holds nine strictly
increasing boundary radii and :meth:`~EightShell.assign_shell` maps a
radius to one of eight shell indices ``0..7``. The boundaries are
monotonic by construction, the assignment is exact at each boundary, and a
radius outside the modelled range is refused rather than clamped. But
assignment is many-to-one *within* a shell: every radius in a shell maps
to the same index, so an index is a bin, not a decoded layer identity.
:func:`refuse_shell_as_decoded_layer` refuses that promotion.

**Boundary transfer is impedance physics, and the ledger closes.** A wave
crossing a shell boundary partially reflects and partially transmits.
:func:`shell_transfer` computes the reflected and transmitted energy
fractions from the two impedances by the normal-incidence Fresnel
relations, in exact rational arithmetic, so ``R + T == 1`` holds exactly
(POWER) and a matched boundary gives ``T == 1, R == 0``. It is an
``ANALYTIC_MODEL``, not a measurement.

**Radial eigenmodes scale with thickness.** Standing modes in a shell
cavity have wavenumbers ``k_n = n*pi/L``; the spacing is ``pi/L`` and the
count in a fixed band scales with the thickness ``L``.
:func:`radial_mode_count` and :func:`mode_spacing` carry that scaling.

Nothing here is measured. The shells, boundaries, impedances and modes are
declared model quantities in dimensionless model units; no layer is
observed and no wave is launched. The standing verdict is
``EIGHT_SHELL_MAPPING_MODEL``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from r12.shells8 import (
    SHELL_COUNT,
    ShellBasis,
    refuse_shell_index_out_of_range,
)


class ShellMapError(ValueError):
    """Raised when the eight-shell mapping is asked to over-claim: a radius
    outside the modelled range, a non-monotonic boundary set, a shell index
    read as a decoded layer, or a model quantity read as measured."""


# --- claim vocabulary ---------------------------------------------------

class ClaimClass(Enum):
    """The claim classes a statement in this module may declare."""

    EXACT_IDENTITY = "EXACT_IDENTITY"
    SOURCE_ESTABLISHED_PHYSICS = "SOURCE_ESTABLISHED_PHYSICS"
    CONVENTIONAL_LITERATURE = "CONVENTIONAL_LITERATURE"
    DERIVED_ARITHMETIC = "DERIVED_ARITHMETIC"
    ANALYTIC_MODEL = "ANALYTIC_MODEL"
    NUMERICAL_SIMULATION = "NUMERICAL_SIMULATION"
    REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
    ENGINEERING_CANDIDATE = "ENGINEERING_CANDIDATE"
    RETROSPECTIVE_NUMERIC_MATCH = "RETROSPECTIVE_NUMERIC_MATCH"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"


CLAIM_CLASSES: tuple[str, ...] = tuple(c.value for c in ClaimClass)

#: The mapping and its wave physics are analytic models.
CLAIM_CLASS = ClaimClass.ANALYTIC_MODEL.value
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
VERDICT = "EIGHT_SHELL_MAPPING_MODEL"

MODEL_UNITS = "DIMENSIONLESS_MODEL_UNITS"

#: A shell model has SHELL_COUNT shells and therefore SHELL_COUNT + 1
#: boundary radii (the inner and outer edge of the stack).
BOUNDARY_COUNT = SHELL_COUNT + 1


# --- the eight-shell layered model -------------------------------------

@dataclass(frozen=True)
class EightShell:
    """Eight concentric shells with explicit, monotonic boundary radii.

    ``boundaries`` holds ``SHELL_COUNT + 1`` strictly increasing radii:
    shell ``i`` occupies ``[boundaries[i], boundaries[i+1])`` for
    ``i < 7`` and ``[boundaries[7], boundaries[8]]`` for the outer shell.
    The radii are model quantities under a declared basis, not measured
    layer depths.
    """

    boundaries: tuple
    units: str = MODEL_UNITS
    basis: ShellBasis = ShellBasis.UNDECLARED

    def __post_init__(self) -> None:
        b = tuple(float(x) for x in self.boundaries)
        if len(b) != BOUNDARY_COUNT:
            raise ShellMapError(
                f"an eight-shell model needs exactly {BOUNDARY_COUNT} "
                f"boundary radii (inner and outer edge of {SHELL_COUNT} "
                f"shells), got {len(b)}")
        if any(not math.isfinite(x) for x in b):
            raise ShellMapError("boundary radii must be finite")
        if any(b[i + 1] <= b[i] for i in range(len(b) - 1)):
            raise ShellMapError(
                "boundary radii must be strictly increasing; a shell stack "
                "with a non-monotonic or zero-thickness boundary is not a "
                "radial ordering")
        if not isinstance(self.basis, ShellBasis):
            raise ShellMapError("basis must be a ShellBasis member")
        object.__setattr__(self, "boundaries", b)

    def boundaries_monotonic(self) -> bool:
        """True iff the boundary radii are strictly increasing."""
        b = self.boundaries
        return all(b[i + 1] > b[i] for i in range(len(b) - 1))

    def thickness(self, index: int) -> float:
        """The radial thickness of one shell."""
        refuse_shell_index_out_of_range(index)
        return self.boundaries[index + 1] - self.boundaries[index]

    def assign_shell(self, radius: float) -> int:
        """Map a radius to its shell index ``0..7``.

        Refuses a radius below the inner edge or above the outer edge --
        that is an address outside the model, not a value to clamp. The
        outer edge is inclusive and lands in the outermost shell. The
        returned index is re-checked against the S3 register range reused
        from :mod:`r12.shells8`.
        """
        r = float(radius)
        if not math.isfinite(r):
            raise ShellMapError("a radius must be finite")
        b = self.boundaries
        if r < b[0] or r > b[-1]:
            raise ShellMapError(
                f"radius {r} lies outside the modelled range "
                f"[{b[0]}, {b[-1]}]; it addresses no shell and is not "
                f"clamped to one")
        for i in range(SHELL_COUNT):
            if r < b[i + 1]:
                return refuse_shell_index_out_of_range(i)
        return refuse_shell_index_out_of_range(SHELL_COUNT - 1)


def default_eight_shell(inner: float = 1000.0, step: float = 500.0,
                        basis: ShellBasis = ShellBasis.UNDECLARED
                        ) -> EightShell:
    """A linearly spaced eight-shell model, for exercising the mapping."""
    if step <= 0:
        raise ShellMapError("shell step must be positive")
    boundaries = tuple(float(inner) + float(step) * i
                       for i in range(BOUNDARY_COUNT))
    return EightShell(boundaries=boundaries, basis=basis)


# --- boundary transfer: reflection and transmission, ledger closed -----

def _as_positive_fraction(value, what: str) -> Fraction:
    """Read an impedance as an exact positive Fraction."""
    if isinstance(value, Fraction):
        f = value
    elif isinstance(value, bool):
        raise ShellMapError(f"{what} must be a number, not a bool")
    elif isinstance(value, int):
        f = Fraction(value)
    elif isinstance(value, float):
        if not math.isfinite(value):
            raise ShellMapError(f"{what} must be finite")
        f = Fraction(value).limit_denominator(10 ** 12)
    else:
        raise ShellMapError(f"{what} must be an int, float or Fraction")
    if f <= 0:
        raise ShellMapError(f"{what} must be positive")
    return f


def shell_transfer(impedance_in, impedance_out) -> dict:
    """Reflected and transmitted energy fractions at a shell boundary.

    Normal-incidence impedance mismatch (Fresnel): with amplitude
    reflection ``(Z2 - Z1)/(Z2 + Z1)``, the energy fractions are
    ``R = (Z2 - Z1)^2 / (Z1 + Z2)^2`` and ``T = 4 Z1 Z2 / (Z1 + Z2)^2``.
    Computed in exact rational arithmetic, so ``R + T == 1`` holds exactly
    (the algebraic identity ``(Z2 - Z1)^2 + 4 Z1 Z2 = (Z1 + Z2)^2``), and a
    matched boundary (``Z1 == Z2``) gives ``T == 1, R == 0``.
    """
    z1 = _as_positive_fraction(impedance_in, "impedance_in")
    z2 = _as_positive_fraction(impedance_out, "impedance_out")
    denom = (z1 + z2) ** 2
    R = (z2 - z1) ** 2 / denom
    T = 4 * z1 * z2 / denom
    energy_sum = R + T
    return {
        "impedance_in": str(z1),
        "impedance_out": str(z2),
        "reflected_fraction": R,
        "transmitted_fraction": T,
        "reflected_float": float(R),
        "transmitted_float": float(T),
        "energy_sum": energy_sum,
        "energy_conserved_exact": energy_sum == 1,
        "matched": z1 == z2,
        "claim_class": ClaimClass.ANALYTIC_MODEL.value,
        "note": (
            "normal-incidence Fresnel energy fractions in exact rational "
            "arithmetic; R + T = 1 by the identity "
            "(Z2 - Z1)^2 + 4 Z1 Z2 = (Z1 + Z2)^2"),
    }


# --- radial eigenmodes in a shell cavity -------------------------------

def mode_spacing(thickness: float) -> float:
    """Wavenumber spacing ``pi / L`` of the radial standing modes."""
    L = float(thickness)
    if L <= 0:
        raise ShellMapError("shell thickness must be positive")
    return math.pi / L


def radial_modes(thickness: float, n_modes: int) -> list[float]:
    """The first ``n_modes`` standing-mode wavenumbers ``k_n = n*pi/L``."""
    L = float(thickness)
    if L <= 0:
        raise ShellMapError("shell thickness must be positive")
    if n_modes < 1:
        raise ShellMapError("n_modes must be positive")
    return [n * math.pi / L for n in range(1, int(n_modes) + 1)]


def radial_mode_count(thickness: float, k_max: float) -> int:
    """How many standing modes fit below ``k_max``; scales with thickness.

    Modes have ``k_n = n*pi/L``, so the count is ``floor(k_max * L / pi)``
    and grows in proportion to the shell thickness ``L``.
    """
    L = float(thickness)
    if L <= 0:
        raise ShellMapError("shell thickness must be positive")
    if k_max < 0:
        raise ShellMapError("k_max must be non-negative")
    return int(math.floor(float(k_max) * L / math.pi))


# --- load-bearing refusals ---------------------------------------------

def refuse_shell_as_decoded_layer(index: int = 0, radius: float = 0.0,
                                  **_k) -> None:
    """A shell index is a coarse bin, not a decoded physical layer.

    Assignment is many-to-one within a shell: every radius in a shell maps
    to the same index, so the index discards the radius. Reading a shell
    assignment as a decoded layer identity is promoting a bin label to a
    measurement of which physical layer a signal came from.
    """
    raise ShellMapError(
        f"refused: shell index {index} is a coarse bin, not a decoded "
        f"layer. Assignment is many-to-one -- every radius within a shell "
        f"maps to the same index, so the index throws away the radius "
        f"(here {radius}). A bin label is not a decoded destination or a "
        f"measured physical layer identity; the mapping is an "
        f"ANALYTIC_MODEL, not an observation of which layer anything is "
        f"in.")


def refuse_model_shell_as_measured(*_a, **_k) -> None:
    """The shell model quantities are computed, not observed.

    The boundary radii, the reflected and transmitted fractions, and the
    eigenmode wavenumbers are all definitions and derivations of the
    declared model. No layered medium was probed, no wave was launched,
    and no reflection was recorded, so none of these numbers may be read as
    a measurement.
    """
    raise ShellMapError(
        "refused: the eight-shell boundaries, the transfer fractions and "
        "the radial eigenmodes are ANALYTIC_MODEL quantities in "
        "dimensionless model units. No layered medium was probed, no wave "
        "was launched and no reflection was recorded, so none of them is a "
        "BENCH_MEASUREMENT. PHYSICAL_VALIDATION_NOT_CLAIMED.")


# --- the report ---------------------------------------------------------

def shellmap_report() -> dict:
    model = default_eight_shell()
    matched = shell_transfer(2, 2)
    mismatch = shell_transfer(2, 3)
    return {
        "what_this_is": (
            "an eight-shell radial mapping model built on the r12.shells8 "
            "register: eight concentric shells with monotonic boundary "
            "radii, an exact boundary-to-index assignment, normal-incidence "
            "boundary transfer with a closed energy ledger, and "
            "thickness-scaled radial eigenmodes"),
        "shell_count": SHELL_COUNT,
        "boundary_count": BOUNDARY_COUNT,
        "boundaries_monotonic": model.boundaries_monotonic(),
        "assign_shell_at_inner_edge": model.assign_shell(model.boundaries[0]),
        "assign_shell_at_outer_edge": model.assign_shell(model.boundaries[-1]),
        "matched_boundary_transmits_fully": (
            matched["transmitted_float"] == 1.0
            and matched["reflected_float"] == 0.0),
        "mismatch_energy_conserved_exact": mismatch["energy_conserved_exact"],
        "mismatch_reflected": mismatch["reflected_float"],
        "mismatch_transmitted": mismatch["transmitted_float"],
        "mode_spacing_halves_when_thickness_doubles": (
            mode_spacing(1000.0) == 2.0 * mode_spacing(2000.0)),
        "mode_count_scales_with_thickness": (
            radial_mode_count(2000.0, 0.1)
            >= 2 * radial_mode_count(1000.0, 0.1) - 1),
        "refusals_available": [
            "refuse_shell_as_decoded_layer (always raises)",
            "refuse_model_shell_as_measured (always raises)",
        ],
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any physical layered medium was probed, that a "
            "wave was launched or a reflection recorded, or that a shell "
            "index decodes which physical layer a signal came from. The "
            "boundaries, the transfer fractions and the eigenmodes are "
            "computed definitions of a declared model in dimensionless "
            "units; assignment is a coarse many-to-one bin, not a decoded "
            "layer identity, and the energy ledger closes because the "
            "Fresnel relations are an identity, not because anything was "
            "measured. Nothing here is measured."),
        "verdict": VERDICT,
    }


__all__ = [
    "ShellMapError", "ClaimClass", "CLAIM_CLASSES", "CLAIM_CLASS",
    "PHYSICAL_VALIDATION", "VERDICT", "MODEL_UNITS", "BOUNDARY_COUNT",
    "EightShell", "default_eight_shell", "shell_transfer", "mode_spacing",
    "radial_modes", "radial_mode_count", "refuse_shell_as_decoded_layer",
    "refuse_model_shell_as_measured", "shellmap_report",
]
