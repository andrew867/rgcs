"""P04 — the R15 crystal and specimen registry.

An experiment is only as trustworthy as its record of *what was in the
holder*. This module is the authority for that record: it creates typed,
immutable, content-hashed :class:`SpecimenRecord` entries for quartz,
glass controls, PCB disks, metal disks and synthetic specimens, tracks
their revision history, and moves them through the lifecycle states a real
specimen passes -- registered, measured, damaged, quarantined, retired.

**A registered specimen is not a measured one.** Registering a specimen
records *metadata* -- material, cut, dimensions and tolerances, mass,
provenance, surface finish, defects. That is a description, not an
acquisition. A specimen with no bound physical artifact is a
``SOURCE_CLAIM`` (or, when it is a fabricated fixture, a
``SYNTHETIC_FIXTURE``); it is **never** a ``PHYSICAL_MEASUREMENT``.
:func:`refuse_specimen_as_measured` raises rather than let a described
specimen be read as measured, and :meth:`SpecimenRegistry.promote_to_measured`
refuses without bound artifacts, refuses a missing dimension, and blocks
the ``REAL`` acquisition path because no hardware exists in this
environment.

**Every field carries its epistemic status.** A :class:`Quantity` is
tagged ``MEASURED``, ``NOMINAL``, ``INFERRED`` or ``UNKNOWN``. An unknown
value stays unknown -- it has no number and cannot masquerade as one --
and a nominal value cannot be read as measured (:func:`require_measured`
raises). Density inferred from a nominal mass and nominal geometry is
tagged ``INFERRED``, never ``MEASURED``.

**Synthetic specimens are visibly synthetic.** A specimen whose material
is ``SYNTHETIC``, or whose artifacts were produced in ``SYNTHETIC`` or
``FAULT_INJECTION`` mode, reports the ``SYNTHETIC_FIXTURE`` claim class and
flags ``synthetic: true`` in its record. The four acquisition modes
(``REAL``, ``REPLAY``, ``SYNTHETIC``, ``FAULT_INJECTION``) stay distinct.

**The crystallographic frame is reused, not reinvented.** For quartz the
orientation is tied to the alpha-quartz lattice frame from
:mod:`r13.crystalframe`: the CONVENTIONAL_LITERATURE lattice constants
``a ~ 4.913 A`` and ``c ~ 5.405 A`` and the enantiomorphic space-group
pair ``P3_121 / P3_221``. Those constants are quoted, not measured here,
and a cut plane's normal is established-physics geometry, not a
diffraction result.

Nothing in this module is measured. No specimen is cut, weighed, mounted
or scanned; the registry records what a specimen *would* be specified by
and refuses every promotion of that description into a measurement.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field, replace
from enum import Enum
from typing import Optional

import numpy as np

from r13.crystalframe import (
    LatticeFrame,
    QUARTZ_A_ANGSTROM,
    QUARTZ_C_ANGSTROM,
    QUARTZ_SPACE_GROUPS,
)
from r15 import claims
from r15.claims import ClaimClass

# --- verdict and module claim class -------------------------------------

DEFAULT_VERDICT = "SPECIMEN_REGISTRY_TYPED_NO_SPECIMEN_MEASURED"

#: This module is software that builds and governs typed specimen records.
CLAIM_CLASS = "SOFTWARE_IMPLEMENTED"


class SpecimenError(RuntimeError):
    """Raised on a malformed record or an illegal lifecycle transition.

    Governance refusals that relabel a description as a measurement raise
    :class:`r15.claims.ClaimError` instead; see
    :func:`refuse_specimen_as_measured`.
    """


# --- epistemic status of a single field ---------------------------------

class FieldClass(Enum):
    """How a recorded value is known. Kept strictly separate: a nominal or
    inferred value must never be read as measured, and an unknown value has
    no number at all."""

    MEASURED = "MEASURED"     # read off an instrument, with uncertainty
    NOMINAL = "NOMINAL"       # a spec / target / catalogue value
    INFERRED = "INFERRED"     # computed from other fields, not observed
    UNKNOWN = "UNKNOWN"       # not known; carries no value


@dataclass(frozen=True)
class Quantity:
    """A scalar with a unit, an epistemic status, and an optional uncertainty.

    An ``UNKNOWN`` quantity must carry ``value=None`` -- it stays unknown.
    A ``MEASURED``, ``NOMINAL`` or ``INFERRED`` quantity must carry a finite
    value. Only a ``MEASURED`` quantity may carry a non-null uncertainty,
    and :func:`require_measured` is the guard that keeps a nominal or
    inferred value from being read as measured.
    """

    value: Optional[float] = None
    unit: str = ""
    field_class: FieldClass = FieldClass.UNKNOWN
    uncertainty: Optional[float] = None

    def __post_init__(self) -> None:
        if self.field_class is FieldClass.UNKNOWN:
            if self.value is not None:
                raise SpecimenError(
                    "an UNKNOWN quantity must have value=None; unknown "
                    "remains unknown")
            if self.uncertainty is not None:
                raise SpecimenError(
                    "an UNKNOWN quantity cannot carry an uncertainty")
            return
        if self.value is None or not math.isfinite(float(self.value)):
            raise SpecimenError(
                f"a {self.field_class.value} quantity needs a finite value")
        if self.uncertainty is not None:
            if self.field_class is not FieldClass.MEASURED:
                raise SpecimenError(
                    "only a MEASURED quantity may carry an uncertainty")
            if not math.isfinite(float(self.uncertainty)) or \
                    float(self.uncertainty) < 0.0:
                raise SpecimenError("uncertainty must be finite and >= 0")

    @property
    def known(self) -> bool:
        """True iff a value is actually recorded."""
        return self.value is not None and self.field_class is not \
            FieldClass.UNKNOWN

    @property
    def measured(self) -> bool:
        return self.field_class is FieldClass.MEASURED

    def to_dict(self) -> dict:
        return {
            "value": None if self.value is None else float(self.value),
            "unit": self.unit,
            "class": self.field_class.value,
            "uncertainty": (None if self.uncertainty is None
                            else float(self.uncertainty)),
        }

    @classmethod
    def unknown(cls, unit: str = "") -> "Quantity":
        """A quantity that is explicitly not known."""
        return cls(value=None, unit=unit, field_class=FieldClass.UNKNOWN)


def require_measured(q: Quantity, what: str = "the quantity") -> Quantity:
    """Return ``q`` iff it is MEASURED; otherwise refuse.

    This is the guard that stops a nominal, inferred or unknown value from
    being consumed where a measurement is required.
    """
    if not isinstance(q, Quantity):
        raise SpecimenError(f"{what} must be a Quantity")
    if q.field_class is not FieldClass.MEASURED:
        raise claims.ClaimError(
            f"refused: {what} is {q.field_class.value}, not MEASURED. A "
            f"{q.field_class.value} value cannot masquerade as a measured "
            f"one. PHYSICAL_VALIDATION_NOT_CLAIMED.")
    return q


# --- materials, handedness, acquisition mode, lifecycle -----------------

class Material(Enum):
    """The specimen materials the registry supports today."""

    ALPHA_QUARTZ = "alpha-quartz"
    GLASS_CONTROL = "glass-control"
    PCB_DISK = "pcb-disk"
    METAL_DISK = "metal-disk"
    SYNTHETIC = "synthetic"


class Handedness(Enum):
    """Enantiomorph of a chiral crystal. Alpha-quartz is chiral: ``RIGHT``
    is the ``P3_121`` setting, ``LEFT`` the ``P3_221`` enantiomorph.
    ``NOT_APPLICABLE`` for achiral materials (glass, metal); ``UNKNOWN`` when
    undetermined."""

    LEFT = "left-handed (P3_221)"
    RIGHT = "right-handed (P3_121)"
    NOT_APPLICABLE = "not-applicable"
    UNKNOWN = "unknown"


class AcquisitionMode(Enum):
    """How an artifact bound to a specimen was produced. The four modes are
    kept distinct so a synthetic or replayed artifact can never be mistaken
    for a real acquisition."""

    REAL = "REAL"                        # a real instrument on a real specimen
    REPLAY = "REPLAY"                    # a recorded prior acquisition
    SYNTHETIC = "SYNTHETIC"              # a deterministic simulator output
    FAULT_INJECTION = "FAULT_INJECTION"  # a deliberately corrupted fixture


class SpecimenState(Enum):
    """The lifecycle of a specimen record.

    ``REGISTERED`` is metadata only. ``MEASURED`` has bound artifacts.
    ``DAMAGED``, ``QUARANTINED`` and ``RETIRED`` are the off-nominal states;
    ``RETIRED`` is terminal.
    """

    REGISTERED = "REGISTERED"
    MEASURED = "MEASURED"
    DAMAGED = "DAMAGED"
    QUARANTINED = "QUARANTINED"
    RETIRED = "RETIRED"


#: The synthetic acquisition modes: an artifact from any of these is a
#: fixture, not a real reading.
_SYNTHETIC_MODES = frozenset({
    AcquisitionMode.SYNTHETIC, AcquisitionMode.FAULT_INJECTION})


# --- geometry, orientation, provenance, defects -------------------------

@dataclass(frozen=True)
class Geometry:
    """A specimen's shape and its dimensions with tolerances.

    ``dimensions`` maps a named extent (``diameter``, ``thickness``, ...) to
    a :class:`Quantity` that carries its own value, unit, class and (for a
    measured extent) uncertainty. ``shape`` is a free-form label
    (``disk``, ``blank``, ``plate``).
    """

    shape: str = "unspecified"
    dimensions: tuple[tuple[str, Quantity], ...] = ()

    def __post_init__(self) -> None:
        names = [n for n, _ in self.dimensions]
        if len(names) != len(set(names)):
            raise SpecimenError("duplicate dimension name in geometry")
        for n, q in self.dimensions:
            if not isinstance(q, Quantity):
                raise SpecimenError(f"dimension {n!r} must be a Quantity")

    def get(self, name: str) -> Optional[Quantity]:
        for n, q in self.dimensions:
            if n == name:
                return q
        return None

    def has_known_extent(self) -> bool:
        """True iff at least one dimension carries a known value."""
        return any(q.known for _, q in self.dimensions)

    def to_dict(self) -> dict:
        return {
            "shape": self.shape,
            "dimensions": {n: q.to_dict() for n, q in self.dimensions},
        }


@dataclass(frozen=True)
class Orientation:
    """Crystallographic (or trivial) orientation of a specimen.

    For quartz this is tied to the alpha-quartz lattice frame of
    :mod:`r13.crystalframe`: the CONVENTIONAL_LITERATURE lattice constants
    and the enantiomorphic space-group pair, plus an optional cut plane
    ``(hkl)`` whose normal is established-physics geometry. For an
    amorphous or isotropic material the scheme is trivial and no lattice is
    carried.
    """

    scheme: str = "unspecified"
    field_class: FieldClass = FieldClass.UNKNOWN
    plane_hkl: Optional[tuple[int, int, int]] = None
    lattice_a: Optional[float] = None
    lattice_c: Optional[float] = None
    space_groups: tuple[str, ...] = ()
    lattice_class: str = "CONVENTIONAL_LITERATURE"

    def __post_init__(self) -> None:
        if self.plane_hkl is not None:
            if len(self.plane_hkl) != 3:
                raise SpecimenError("plane_hkl must be a 3-tuple (h, k, l)")
            if all(int(i) == 0 for i in self.plane_hkl):
                raise SpecimenError(
                    "the (0,0,0) plane has no normal and no orientation")

    def frame(self) -> LatticeFrame:
        """The alpha-quartz lattice frame for this orientation.

        Reuses :class:`r13.crystalframe.LatticeFrame` at the recorded (or
        default literature) lattice constants. Refuses when no lattice is
        carried (an amorphous specimen has no crystallographic frame).
        """
        if self.lattice_a is None or self.lattice_c is None:
            raise SpecimenError(
                "no crystallographic lattice on this orientation; an "
                "amorphous / isotropic specimen has no lattice frame")
        return LatticeFrame(a=float(self.lattice_a), c=float(self.lattice_c))

    def plane_normal(self) -> np.ndarray:
        """The reciprocal-space normal ``G(hkl)`` of the cut plane.

        Established-physics geometry from the lattice frame, not a measured
        surface normal. Refuses when no cut plane is recorded.
        """
        if self.plane_hkl is None:
            raise SpecimenError("no cut plane recorded on this orientation")
        h, k, l = (int(i) for i in self.plane_hkl)
        return self.frame().reciprocal_vector(h, k, l)

    def to_dict(self) -> dict:
        return {
            "scheme": self.scheme,
            "class": self.field_class.value,
            "plane_hkl": (None if self.plane_hkl is None
                          else list(self.plane_hkl)),
            "lattice_a_angstrom": self.lattice_a,
            "lattice_c_angstrom": self.lattice_c,
            "space_groups": list(self.space_groups),
            "lattice_class": self.lattice_class,
        }

    @classmethod
    def quartz(cls, cut: str = "unspecified",
               plane_hkl: Optional[tuple[int, int, int]] = None,
               field_class: FieldClass = FieldClass.NOMINAL) -> "Orientation":
        """An alpha-quartz orientation from the literature lattice frame.

        The lattice constants and space groups come from
        :mod:`r13.crystalframe` as CONVENTIONAL_LITERATURE values; they are
        not measured here. ``field_class`` describes how the *cut angle* is
        known (nominal from the order, or measured on an alignment station).
        """
        return cls(scheme=cut, field_class=field_class, plane_hkl=plane_hkl,
                   lattice_a=QUARTZ_A_ANGSTROM, lattice_c=QUARTZ_C_ANGSTROM,
                   space_groups=tuple(QUARTZ_SPACE_GROUPS),
                   lattice_class="CONVENTIONAL_LITERATURE")

    @classmethod
    def amorphous(cls, scheme: str = "isotropic") -> "Orientation":
        """A trivial orientation for glass / metal (no crystallographic
        frame)."""
        return cls(scheme=scheme, field_class=FieldClass.NOMINAL)


@dataclass(frozen=True)
class Provenance:
    """Where a specimen came from and how any artifacts were acquired."""

    supplier: str = "UNSPECIFIED"
    lot: str = "UNSPECIFIED"
    cut_history: tuple[str, ...] = ()
    acquisition_mode: Optional[AcquisitionMode] = None
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "supplier": self.supplier,
            "lot": self.lot,
            "cut_history": list(self.cut_history),
            "acquisition_mode": (None if self.acquisition_mode is None
                                 else self.acquisition_mode.value),
            "notes": self.notes,
        }


@dataclass(frozen=True)
class Defect:
    """A recorded flaw. ``kind`` is e.g. ``inclusion``, ``chip``, ``twin``,
    ``scratch``; ``severity`` is a short qualitative label."""

    kind: str
    severity: str = "unspecified"
    note: str = ""

    def to_dict(self) -> dict:
        return {"kind": self.kind, "severity": self.severity,
                "note": self.note}


# --- the specimen record -------------------------------------------------

def derive_specimen_id(seed: str) -> str:
    """A deterministic, immutable specimen id derived from a seed string.

    Seeded (no wall-clock, no randomness), so the same seed always yields
    the same id. Formatted UUID-like for readability.
    """
    if not seed:
        raise SpecimenError("a specimen id seed must be non-empty")
    h = hashlib.sha256(f"RGCS-R15-SPECIMEN::{seed}".encode("utf-8")).hexdigest()
    return f"SPC-{h[0:8]}-{h[8:12]}-{h[12:16]}-{h[16:20]}-{h[20:32]}"


@dataclass(frozen=True)
class SpecimenRecord:
    """An immutable, content-hashed record of a single specimen revision.

    The identity (``specimen_id``) is fixed across every revision; each
    revision is a new frozen record with an incremented ``revision`` and a
    ``revision_reason``. A record with no bound ``artifacts`` is a
    description, not a measurement.
    """

    specimen_id: str
    material: Material
    mass: Quantity
    geometry: Geometry
    orientation: Orientation
    provenance: Provenance
    handedness: Handedness = Handedness.UNKNOWN
    surface_finish: str = "UNSPECIFIED"
    density: Quantity = field(default_factory=lambda: Quantity.unknown("g/cm^3"))
    defects: tuple[Defect, ...] = ()
    photos: tuple[str, ...] = ()
    artifacts: tuple[str, ...] = ()
    state: SpecimenState = SpecimenState.REGISTERED
    revision: int = 0
    revision_reason: str = "created"

    def __post_init__(self) -> None:
        if not self.specimen_id:
            raise SpecimenError("a specimen needs an id")
        if not isinstance(self.material, Material):
            raise SpecimenError("material must be a Material")
        if not isinstance(self.mass, Quantity):
            raise SpecimenError("mass must be a Quantity")
        if self.revision < 0:
            raise SpecimenError("revision must be a non-negative integer")
        if self.state is SpecimenState.MEASURED and not self.artifacts:
            raise SpecimenError(
                "a MEASURED specimen must have at least one bound artifact")

    # -- epistemic surface -----------------------------------------------

    @property
    def acquisition_mode(self) -> Optional[AcquisitionMode]:
        return self.provenance.acquisition_mode

    @property
    def is_synthetic(self) -> bool:
        """True iff the material is synthetic or any artifact is a synthetic
        / fault-injected fixture. Such specimens are visibly synthetic."""
        return (self.material is Material.SYNTHETIC
                or self.acquisition_mode in _SYNTHETIC_MODES)

    @property
    def has_physical_artifact(self) -> bool:
        return bool(self.artifacts)

    # -- canonical serialization + content hash --------------------------

    def to_record(self, include_hash: bool = True) -> dict:
        """The canonical dict form, conforming to
        ``specimen_record.schema.json``."""
        rec = {
            "specimen_id": self.specimen_id,
            "material": self.material.value,
            "mass": self.mass.to_dict(),
            "geometry": self.geometry.to_dict(),
            "orientation": self.orientation.to_dict(),
            "provenance": self.provenance.to_dict(),
            "handedness": self.handedness.value,
            "surface_finish": self.surface_finish,
            "density": self.density.to_dict(),
            "defects": [d.to_dict() for d in self.defects],
            "photos": list(self.photos),
            "artifacts": list(self.artifacts),
            "status": self.state.value,
            "revision": self.revision,
            "revision_reason": self.revision_reason,
            "synthetic": self.is_synthetic,
            "claim_class": specimen_claim_class(self).value,
        }
        if include_hash:
            rec["content_hash"] = _hash_record(rec)
        return rec

    def content_hash(self) -> str:
        """The SHA-256 of the canonical record (excluding the hash field)."""
        return _hash_record(self.to_record(include_hash=False))


def _canonical_bytes(obj: dict) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True).encode("utf-8")


def _hash_record(rec_without_hash: dict) -> str:
    body = {k: v for k, v in rec_without_hash.items() if k != "content_hash"}
    return hashlib.sha256(_canonical_bytes(body)).hexdigest()


def verify_record(record: dict) -> bool:
    """True iff a serialized record's ``content_hash`` matches its body.

    Any tamper with any field flips the recomputed hash and this returns
    False.
    """
    claimed = record.get("content_hash")
    if not claimed:
        return False
    return _hash_record(record) == claimed


# --- the claim class of a specimen --------------------------------------

def specimen_claim_class(rec: SpecimenRecord) -> ClaimClass:
    """The honest claim class of a specimen record.

    A synthetic / fault-injected specimen is a ``SYNTHETIC_FIXTURE``. A
    described specimen with no bound artifact is a ``SOURCE_CLAIM``. A
    replayed acquisition is a ``SYNTHETIC_OBSERVATION``. No path here
    returns a measurement class: real acquisition does not exist in this
    environment.
    """
    if rec.is_synthetic:
        return ClaimClass.SYNTHETIC_FIXTURE
    if rec.state is SpecimenState.REGISTERED or not rec.has_physical_artifact:
        return ClaimClass.SOURCE_CLAIM
    if rec.acquisition_mode is AcquisitionMode.REPLAY:
        return ClaimClass.SYNTHETIC_OBSERVATION
    # A REAL artifact would be a PHYSICAL_MEASUREMENT, but that is blocked
    # at promotion time; a described specimen never reaches it from here.
    return claims.cap_claim_to_software(ClaimClass.PHYSICAL_MEASUREMENT)


# --- the load-bearing refusal -------------------------------------------

def refuse_specimen_as_measured(rec: Optional[SpecimenRecord] = None,
                                *_a, **_k) -> None:
    """Refuse to read a described specimen as a physical measurement.

    Registering a specimen records metadata -- a description of a part. A
    description is a ``SOURCE_CLAIM`` (or a ``SYNTHETIC_FIXTURE`` when the
    part is fabricated); it is never a ``PHYSICAL_MEASUREMENT``. Promoting
    a specimen to measured needs bound physical artifacts from a real
    acquisition, which does not exist in this environment.
    """
    detail = ""
    if rec is not None:
        detail = (f" specimen {rec.specimen_id!r} is in state "
                  f"{rec.state.value} with "
                  f"{len(rec.artifacts)} bound artifact(s)")
    raise claims.ClaimError(
        "refused: a registered specimen is a described part, not a "
        "measurement." + detail + ". A specimen with no bound physical "
        "artifact is a SOURCE_CLAIM / SOFTWARE_IMPLEMENTED record, never a "
        "PHYSICAL_MEASUREMENT. Real acquisition with real artifacts does "
        "not exist here. PHYSICAL_VALIDATION_NOT_CLAIMED.")


# --- the registry --------------------------------------------------------

class SpecimenRegistry:
    """An in-memory registry of specimens and their revision histories.

    Identity is immutable: every specimen keeps its ``specimen_id`` across
    revisions, and each lifecycle change appends a new frozen
    :class:`SpecimenRecord` to that specimen's history. The registry never
    mutates a record in place.
    """

    def __init__(self) -> None:
        self._history: dict[str, list[SpecimenRecord]] = {}

    # -- registration -----------------------------------------------------

    def register(self, record: SpecimenRecord) -> SpecimenRecord:
        """Register a new specimen at revision 0 (state REGISTERED)."""
        if record.specimen_id in self._history:
            raise SpecimenError(
                f"specimen {record.specimen_id!r} is already registered")
        if record.revision != 0:
            raise SpecimenError("a freshly registered specimen is revision 0")
        if record.state is not SpecimenState.REGISTERED:
            raise SpecimenError(
                "registration starts in the REGISTERED state; artifacts are "
                "bound by promote_to_measured, not at registration")
        self._history[record.specimen_id] = [record]
        return record

    def current(self, specimen_id: str) -> SpecimenRecord:
        """The latest revision of a specimen."""
        return self._require(specimen_id)[-1]

    def history(self, specimen_id: str) -> tuple[SpecimenRecord, ...]:
        """The full, ordered revision history of a specimen."""
        return tuple(self._require(specimen_id))

    def ids(self) -> tuple[str, ...]:
        return tuple(self._history)

    def _require(self, specimen_id: str) -> list[SpecimenRecord]:
        if specimen_id not in self._history:
            raise SpecimenError(f"no such specimen {specimen_id!r}")
        return self._history[specimen_id]

    # -- the core revision primitive -------------------------------------

    def _revise(self, specimen_id: str, reason: str,
                **changes) -> SpecimenRecord:
        chain = self._require(specimen_id)
        cur = chain[-1]
        if cur.state is SpecimenState.RETIRED:
            raise SpecimenError(
                f"specimen {specimen_id!r} is RETIRED; a retired specimen is "
                f"terminal and cannot be revised")
        nxt = replace(cur, revision=cur.revision + 1,
                      revision_reason=reason, **changes)
        chain.append(nxt)
        return nxt

    # -- lifecycle transitions -------------------------------------------

    def promote_to_measured(self, specimen_id: str, *,
                            artifacts: tuple[str, ...],
                            mode: AcquisitionMode,
                            reason: str = "artifacts bound") -> SpecimenRecord:
        """Bind physical artifacts and move a specimen to MEASURED.

        Refuses without artifacts, refuses without at least one known
        dimension, and blocks the ``REAL`` acquisition mode -- no real
        hardware or acquisition exists in this environment, so a real
        physical measurement is a BLOCKED_MISSING_INPUT, not a result.
        Synthetic / replay / fault-injection artifacts are accepted and the
        specimen stays visibly non-physical.
        """
        cur = self.current(specimen_id)
        if not artifacts:
            refuse_specimen_as_measured(cur)
        if not cur.geometry.has_known_extent():
            raise SpecimenError(
                f"refused: specimen {specimen_id!r} has no known dimension; "
                f"a measured specimen needs at least one recorded extent")
        if not cur.mass.known:
            raise SpecimenError(
                f"refused: specimen {specimen_id!r} has an unknown mass; a "
                f"measured specimen needs a recorded mass")
        if mode is AcquisitionMode.REAL:
            raise SpecimenError(
                "BLOCKED_MISSING_INPUT: REAL acquisition requires physical "
                "hardware and a real specimen, neither of which exists in "
                "this environment. A REAL physical measurement is blocked, "
                "not produced. PHYSICAL_VALIDATION_NOT_CLAIMED.")
        new_prov = replace(cur.provenance, acquisition_mode=mode)
        return self._revise(specimen_id, reason,
                            state=SpecimenState.MEASURED,
                            artifacts=tuple(artifacts), provenance=new_prov)

    def mark_damaged(self, specimen_id: str, defect: Defect,
                     reason: str = "damage recorded") -> SpecimenRecord:
        """Record damage: append a new revision in the DAMAGED state with a
        new defect."""
        cur = self.current(specimen_id)
        return self._revise(specimen_id, reason,
                            state=SpecimenState.DAMAGED,
                            defects=cur.defects + (defect,))

    def quarantine(self, specimen_id: str,
                   reason: str = "quarantined") -> SpecimenRecord:
        """Move a specimen into the QUARANTINED state."""
        return self._revise(specimen_id, reason,
                            state=SpecimenState.QUARANTINED)

    def retire(self, specimen_id: str,
               reason: str = "retired") -> SpecimenRecord:
        """Move a specimen into the terminal RETIRED state."""
        return self._revise(specimen_id, reason, state=SpecimenState.RETIRED)


# --- inferred density ----------------------------------------------------

def infer_density(mass: Quantity, geometry: Geometry) -> Quantity:
    """Infer disk density from mass and a disk geometry (g/cm^3), INFERRED.

    A right circular disk of diameter ``d`` and thickness ``t`` has volume
    ``pi (d/2)^2 t``. The result is always tagged ``INFERRED`` -- it is
    computed from the recorded mass and geometry, never observed -- and
    reduces to ``UNKNOWN`` if any input is unknown.
    """
    d = geometry.get("diameter")
    t = geometry.get("thickness")
    if not (mass.known and d is not None and d.known
            and t is not None and t.known):
        return Quantity.unknown("g/cm^3")
    radius_cm = float(d.value) / 2.0
    volume_cm3 = math.pi * radius_cm * radius_cm * float(t.value)
    if volume_cm3 <= 0.0:
        raise SpecimenError("non-positive volume; cannot infer density")
    return Quantity(value=float(mass.value) / volume_cm3, unit="g/cm^3",
                    field_class=FieldClass.INFERRED)


# --- example synthetic fixtures (visibly synthetic) ---------------------

def make_quartz_blank(specimen_id: Optional[str] = None,
                      seed: str = "quartz-blank-A") -> SpecimenRecord:
    """A registered alpha-quartz blank, metadata only (a SOURCE_CLAIM).

    Nominal 8.00 mm diameter, 0.30 mm thickness, mass and cut nominal; the
    orientation is tied to the alpha-quartz lattice frame via a (0,0,1)
    c-plane cut. Nothing is measured.
    """
    sid = specimen_id or derive_specimen_id(seed)
    geom = Geometry(shape="disk", dimensions=(
        ("diameter", Quantity(8.00e-1, "cm", FieldClass.NOMINAL)),
        ("thickness", Quantity(3.00e-2, "cm", FieldClass.NOMINAL)),
    ))
    mass = Quantity(4.0e-2, "g", FieldClass.NOMINAL)
    orient = Orientation.quartz(cut="c-plane", plane_hkl=(0, 0, 1),
                                field_class=FieldClass.NOMINAL)
    prov = Provenance(supplier="SYNTHETIC-FIXTURE-SUPPLIER", lot="LOT-0001",
                      cut_history=("as-grown", "c-plane cut"),
                      acquisition_mode=None,
                      notes="synthetic public fixture; nothing measured")
    return SpecimenRecord(
        specimen_id=sid, material=Material.ALPHA_QUARTZ, mass=mass,
        geometry=geom, orientation=orient, provenance=prov,
        handedness=Handedness.RIGHT, surface_finish="optically polished (nom.)",
        density=infer_density(mass, geom))


def make_glass_control(specimen_id: Optional[str] = None,
                       seed: str = "glass-control-A") -> SpecimenRecord:
    """A registered fused-silica glass control disk (SOURCE_CLAIM)."""
    sid = specimen_id or derive_specimen_id(seed)
    geom = Geometry(shape="disk", dimensions=(
        ("diameter", Quantity(8.00e-1, "cm", FieldClass.NOMINAL)),
        ("thickness", Quantity(3.00e-2, "cm", FieldClass.NOMINAL)),
    ))
    mass = Quantity(4.2e-2, "g", FieldClass.NOMINAL)
    orient = Orientation.amorphous(scheme="fused-silica (isotropic)")
    prov = Provenance(supplier="SYNTHETIC-FIXTURE-SUPPLIER", lot="LOT-0002",
                      cut_history=("cast", "ground"), acquisition_mode=None,
                      notes="synthetic public fixture; nothing measured")
    return SpecimenRecord(
        specimen_id=sid, material=Material.GLASS_CONTROL, mass=mass,
        geometry=geom, orientation=orient, provenance=prov,
        handedness=Handedness.NOT_APPLICABLE,
        surface_finish="ground (nom.)",
        density=infer_density(mass, geom))


def make_synthetic_specimen(specimen_id: Optional[str] = None,
                            seed: str = "synthetic-A") -> SpecimenRecord:
    """A visibly synthetic specimen fixture (SYNTHETIC_FIXTURE class)."""
    sid = specimen_id or derive_specimen_id(seed)
    geom = Geometry(shape="disk", dimensions=(
        ("diameter", Quantity(8.00e-1, "cm", FieldClass.NOMINAL)),
        ("thickness", Quantity(3.00e-2, "cm", FieldClass.NOMINAL)),
    ))
    mass = Quantity(4.0e-2, "g", FieldClass.NOMINAL)
    prov = Provenance(supplier="SYNTHETIC", lot="SYNTH-0001",
                      cut_history=("generated",),
                      acquisition_mode=AcquisitionMode.SYNTHETIC,
                      notes="deterministic synthetic fixture")
    return SpecimenRecord(
        specimen_id=sid, material=Material.SYNTHETIC, mass=mass,
        geometry=geom, orientation=Orientation.amorphous(scheme="synthetic"),
        provenance=prov, handedness=Handedness.NOT_APPLICABLE,
        surface_finish="synthetic")


# --- the report ----------------------------------------------------------

def specimens_report() -> dict:
    reg = SpecimenRegistry()
    quartz = reg.register(make_quartz_blank())
    reg.register(make_glass_control())
    synth = make_synthetic_specimen()
    return {
        "what_this_is": (
            "the R15 crystal and specimen registry: typed, immutable, "
            "content-hashed specimen records for quartz, glass controls, "
            "PCB / metal disks and synthetic specimens, with revision "
            "history and the registered / measured / damaged / quarantined "
            "/ retired lifecycle"),
        "materials": [m.value for m in Material],
        "field_classes": [f.value for f in FieldClass],
        "acquisition_modes": [a.value for a in AcquisitionMode],
        "lifecycle_states": [s.value for s in SpecimenState],
        "registered_vs_measured": (
            "REGISTERED is metadata only (a SOURCE_CLAIM); MEASURED needs "
            "bound physical artifacts, and REAL acquisition is blocked here"),
        "example_quartz_id": quartz.specimen_id,
        "example_quartz_claim_class": specimen_claim_class(quartz).value,
        "example_synthetic_claim_class": specimen_claim_class(synth).value,
        "example_content_hash": quartz.content_hash(),
        "quartz_lattice_constants_angstrom": {
            "a": QUARTZ_A_ANGSTROM, "c": QUARTZ_C_ANGSTROM,
            "class": "CONVENTIONAL_LITERATURE"},
        "quartz_space_groups": list(QUARTZ_SPACE_GROUPS),
        "refusals": [
            "a described specimen is not a measurement "
            "(refuse_specimen_as_measured)",
            "a nominal / inferred / unknown value cannot be read as measured "
            "(require_measured)",
            "promotion without artifacts, without a known dimension, or "
            "under REAL mode is refused / blocked",
        ],
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say any specimen was cut, weighed, mounted, "
            "oriented or scanned. Every record is a description; the quartz "
            "lattice constants are quoted literature values, not measured "
            "here; density is INFERRED from nominal fields, never observed; "
            "and no specimen reaches a PHYSICAL_MEASUREMENT class, because "
            "real acquisition does not exist in this environment."),
    }
