"""RGCS v4.7.x R3 — Root-Space Resolver, Anisotropic Phase Lens,
Optical Spin, HAL Memory, Nested Tetrahedral Atlas.

    Lore proposes. Mathematics translates. Software attacks.
    Evidence decides. Provenance remembers.

The R3 correction (00_START_HERE): a root is NOT "the first place
where phase residual is zero" — zero wrapped residual admits integer-
cycle aliases. A root is a typed, calibrated, alias-resolved,
gauge-declared, uncertainty-bounded relational reference state.

Extends cspc/ and pmwr/ throughout; nothing here is physical evidence.
"""

from __future__ import annotations

SCHEMA_VERSION = "1.0.0"
PROGRAMME_ID = "RGCS-V4.7X-R3"

#: The six typed root classes (core/16). "Root" is not one object.
ROOT_CLASSES = (
    "SYNTHETIC_HIERARCHY_ROOT",
    "PHASE_AUTHORITY_ROOT",
    "CALIBRATED_INSTRUMENT_ROOT",
    "RECONSTRUCTED_SOURCE_STATE_ROOT",
    "PHYSICAL_REFERENCE_NETWORK_ROOT",
    "GAUGE_FIXED_CANONICAL_ROOT",
)

#: Resolution statuses (core/17). The failure statuses are first-class
#: outputs, not errors.
ROOT_STATUSES = (
    "ROOT_ALIAS_UNRESOLVED",
    "ROOT_NON_UNIQUE",
    "ROOT_PARTIALLY_IDENTIFIED",
    "ROOT_LOCK_BOUNDED",
    "ROOT_LOCK_REJECTED",
    "ABSOLUTE_VACUUM_ROOT_UNSUPPORTED",
    "NONLOCAL_REFERENCE_FRAME_UNSUPPORTED",
)

#: Forbidden collapses (core/16): tempting identification -> refusal.
FORBIDDEN_COLLAPSES = {
    "HIERARCHY_ROOT_IS_VACUUM_ORIGIN":
        "the codec's parent address is a bookkeeping object, not a "
        "location in vacuum",
    "EIGENMODE_IS_SPACETIME_EIGENSTATE":
        "a crystal eigenmode is a mechanical pattern, not a spacetime "
        "state",
    "PHASE_ZERO_IS_ABSOLUTE_PHASE":
        "phase zero is a declared epoch on a declared authority; "
        "absolute phase is modulo 2*pi (v4.7 doctrine)",
    "CANONICAL_REPRESENTATIVE_IS_UNIQUE_ONTOLOGY":
        "a gauge-fixed representative is a chosen member of an "
        "equivalence class, not the one true state",
    "REFERENCE_NETWORK_IS_PREFERRED_FRAME":
        "a physical reference network is relational; no measurement "
        "in it establishes a universal preferred frame",
    "SOURCE_ESTIMATE_IS_HISTORICAL_TRUTH":
        "a deconvolved source estimate is bounded inference, not a "
        "complete recovered history",
}

#: Spin/torsion categories (core/04). Never merged implicitly.
SPIN_CATEGORIES = (
    "INTRINSIC_SPIN_DENSITY",
    "CLASSICAL_ANGULAR_MOMENTUM",
    "EM_SPIN_ANGULAR_MOMENTUM",
    "EM_ORBITAL_ANGULAR_MOMENTUM",
    "MECHANICAL_TORSION",
    "DEFECT_TORSION_ANALOG",
    "SPACETIME_TORSION",
)


class ClaimBoundaryError(ValueError):
    """An operation would cross an R3 boundary or forbidden collapse."""


class GaugeError(ValueError):
    """A gauge/canonical-representative rule was violated or omitted."""


def validate_root_class(cls: str) -> str:
    if cls not in ROOT_CLASSES:
        raise ClaimBoundaryError(f"{cls!r} is not a typed root class")
    return cls


def validate_root_status(status: str) -> str:
    if status not in ROOT_STATUSES:
        raise ClaimBoundaryError(f"{status!r} is not a root status")
    return status


def refuse_collapse(key: str) -> None:
    """Raise the named forbidden collapse as an error, citing why."""
    raise ClaimBoundaryError(
        f"forbidden collapse {key}: {FORBIDDEN_COLLAPSES[key]}")
