"""P06 — the fixture registry and the boundary conditions it imposes.

A specimen does not float in the drive field: it is clamped, suspended,
bonded, or pressed against a mount, and *how* it is held changes what the
instrument reads. A centre clamp grounds a node and pushes the modes up; a
suspension frees the ends and lets them fall; an elastomer sub-mount adds a
soft spring and a loss path. Those shifts are **real**, they are
**ordinary**, and they are the fixture's, not the specimen's. This module
writes the fixture down as a typed record, models the boundary condition it
imposes on the synthetic modes, and refuses -- loudly -- to let a
fixture-induced shift be read as a signal.

**The record.** A :class:`FixtureRecord` carries a fixture id, a mount type
(centre clamp, three-point, suspension, elastomer, adhesive, or a purely
synthetic mount), its contact geometry, its preload (clamp force and
torque), its material stack, an orientation transform, a coupling medium,
whether an electrode touches the specimen, and -- always -- a repeatability
uncertainty. It serialises to the ``fixture_record`` schema. A fixture id
and a specimen id live in different namespaces and cannot be swapped; a
record whose id looks like a specimen id is refused at construction.

**The boundary condition.** ``FREE``, ``FIXED`` and ``SPRING`` map to end
stiffnesses of the R11 mechanical chain (:mod:`r11.mechboundary`), so the
synthetic modal frequencies come from solving ``K v = omega**2 M v`` for a
grounded chain rather than from an asserted number. Change the support and
the modes change; that change is booked through the R13 boundary-energy
ledger (:mod:`r13.boundaryenergy`) as ordinary boundary work, never as a
new energy channel.

**The firewall.** A fixture change that shifts a measured mode produces a
``FIXTURE_EFFECT`` -- a known ordinary effect in the R15 taxonomy
(:mod:`r15.claims`), one of the explanations a residual must survive.
:func:`fixture_shift_is_ordinary` classifies the shift as exactly that, and
:func:`refuse_fixture_effect_as_signal` refuses every route by which it is
promoted to a specimen signal. Fixture repeatability enters the error
budget through :func:`fixture_error_budget`; a fixture with an unknown
preload cannot support a precision claim, and :func:`assert_precision_claim`
blocks it.

Nothing here is measured. No specimen is mounted, no clamp is torqued, and
every frequency is arithmetic on a declared model in the R11 chain's own
units.
"""

from __future__ import annotations

import hashlib
import itertools
import math
from dataclasses import dataclass, field, replace
from enum import Enum

import numpy as np

from r11 import mechboundary as mb
from r13 import boundaryenergy as be
from r15 import claims as C

# --- verdict, claim vocabulary, tolerances --------------------------------

#: The standing verdict for this module.
VERDICT = "FIXTURE_REGISTRY_AND_BOUNDARY_CONDITIONS_IMPLEMENTED_NO_MEASUREMENT"

#: What software alone produces here: a synthetic fixture, never a mounted
#: specimen. Taken from the R15 claim taxonomy.
CLAIM_CLASS = C.ClaimClass.SYNTHETIC_FIXTURE.value

#: The ordinary-explanation class a fixture-induced shift belongs to.
FIXTURE_EFFECT = C.ClaimClass.FIXTURE_EFFECT.value

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Fixture and specimen ids live in different namespaces and cannot be
#: swapped. A record whose id carries the wrong prefix is refused.
FIXTURE_ID_PREFIX = "FIX-"
SPECIMEN_ID_PREFIX = "SPX-"

#: Default coverage factor for the fixture error budget (2 sigma).
DEFAULT_K_SIGMA = 2.0


class FixtureError(RuntimeError):
    """Raised when a fixture claim exceeds what the registry licenses.

    Covers the structural guards (an ill-formed id, an empty contact set,
    an unknown boundary condition) and the load-bearing refusals
    :func:`refuse_fixture_effect_as_signal`,
    :func:`refuse_fixture_id_as_specimen`, and the precision-claim block in
    :func:`assert_precision_claim`.
    """


# --- (1) the typed vocabularies -------------------------------------------

class MountType(Enum):
    """How the specimen is held. Six kinds, independently typed.

    * ``CENTRE_CLAMP`` -- a single grounded clamp at one node (fixed);
    * ``THREE_POINT`` -- a kinematic three-point support (spring-like);
    * ``SUSPENSION`` -- threads or wires that free the ends (free);
    * ``ELASTOMER`` -- a soft sub-mount, a spring with a loss path;
    * ``ADHESIVE`` -- a bonded joint, a stiff spring;
    * ``SYNTHETIC`` -- a purely synthetic mount with no physical referent.
    """

    CENTRE_CLAMP = "CENTRE_CLAMP"
    THREE_POINT = "THREE_POINT"
    SUSPENSION = "SUSPENSION"
    ELASTOMER = "ELASTOMER"
    ADHESIVE = "ADHESIVE"
    SYNTHETIC = "SYNTHETIC"


class BoundaryCondition(Enum):
    """The idealised boundary a mount imposes on a resonator end.

    * ``FREE`` -- a near-zero end stiffness; the end swings, modes fall;
    * ``SPRING`` -- a finite end stiffness; modes sit in between;
    * ``FIXED`` -- a large end stiffness; the end is grounded, modes rise.
    """

    FREE = "FREE"
    SPRING = "SPRING"
    FIXED = "FIXED"


class CouplingMedium(Enum):
    """What sits in the contact interface between specimen and mount."""

    DRY_CONTACT = "DRY_CONTACT"
    COUPLANT_GEL = "COUPLANT_GEL"
    ELASTOMER_PAD = "ELASTOMER_PAD"
    ADHESIVE_BOND = "ADHESIVE_BOND"
    SUSPENSION_THREAD = "SUSPENSION_THREAD"
    AIR_GAP = "AIR_GAP"


class FixtureProvenance(Enum):
    """The four acquisition modes, kept distinct.

    Only ``SYNTHETIC`` is reachable here: no fixture has been machined,
    and no run has been replayed. ``REAL``, ``REPLAY`` and
    ``FAULT_INJECTION`` are declared so the mode is never silently assumed.
    """

    SYNTHETIC = "SYNTHETIC"
    REPLAY = "REPLAY"
    REAL = "REAL"
    FAULT_INJECTION = "FAULT_INJECTION"


class PerturbationClass(Enum):
    """Expected ways a fixture perturbs a reading. Every one is ordinary.

    These are the FIXTURE_EFFECT sub-kinds: a fixture change is *expected*
    to move a mode, change a Q, split a degenerate pair, or add a contact
    resonance. None of them is a specimen signal.
    """

    MODAL_FREQUENCY_SHIFT = "MODAL_FREQUENCY_SHIFT"
    Q_FACTOR_CHANGE = "Q_FACTOR_CHANGE"
    AMPLITUDE_CHANGE = "AMPLITUDE_CHANGE"
    MODE_SPLITTING = "MODE_SPLITTING"
    CONTACT_RESONANCE = "CONTACT_RESONANCE"


#: Each boundary condition maps to an end stiffness of the R11 chain. The
#: values are model numbers in the chain's own units; FIXED grounds the
#: end, FREE barely holds it, SPRING sits between. The support end stays
#: grounded so the stiffness matrix is positive definite in every case.
BOUNDARY_STIFFNESS: dict[BoundaryCondition, float] = {
    BoundaryCondition.FREE: 0.02,
    BoundaryCondition.SPRING: 0.8,
    BoundaryCondition.FIXED: 50.0,
}

#: The idealised boundary each mount type imposes.
MOUNT_BOUNDARY: dict[MountType, BoundaryCondition] = {
    MountType.CENTRE_CLAMP: BoundaryCondition.FIXED,
    MountType.THREE_POINT: BoundaryCondition.SPRING,
    MountType.SUSPENSION: BoundaryCondition.FREE,
    MountType.ELASTOMER: BoundaryCondition.SPRING,
    MountType.ADHESIVE: BoundaryCondition.FIXED,
    MountType.SYNTHETIC: BoundaryCondition.SPRING,
}


# --- (2) the record components --------------------------------------------

@dataclass(frozen=True)
class ContactPoint:
    """One place the specimen touches the mount.

    ``position_mm`` is the contact location in the fixture frame,
    ``boundary`` the idealised condition it imposes, and
    ``normal_stiffness_n_per_m`` the model stiffness of the contact. Every
    value is a declared model number, not a measurement.
    """

    label: str
    position_mm: tuple[float, float, float]
    boundary: BoundaryCondition
    normal_stiffness_n_per_m: float

    def __post_init__(self) -> None:
        if not str(self.label).strip():
            raise FixtureError("a contact point needs a label")
        if len(tuple(self.position_mm)) != 3:
            raise FixtureError("position_mm must be a 3-tuple (x, y, z)")
        if not all(math.isfinite(float(v)) for v in self.position_mm):
            raise FixtureError("every contact coordinate must be finite")
        if not isinstance(self.boundary, BoundaryCondition):
            raise FixtureError("boundary must be a BoundaryCondition")
        if self.normal_stiffness_n_per_m < 0.0:
            raise FixtureError("contact stiffness cannot be negative")

    def as_dict(self) -> dict:
        return {
            "label": self.label,
            "position_mm": [float(v) for v in self.position_mm],
            "boundary": self.boundary.value,
            "normal_stiffness_n_per_m": float(self.normal_stiffness_n_per_m),
        }


@dataclass(frozen=True)
class Preload:
    """The clamp force and torque applied to hold the specimen.

    ``clamp_force_n`` or ``torque_nm`` of ``None`` means the preload is
    **unrecorded**, not zero: an unknown preload cannot support a precision
    claim (see :func:`assert_precision_claim`).
    ``repeatability_frac`` is the relative repeatability of the preload
    from mount to mount.
    """

    clamp_force_n: float | None = None
    torque_nm: float | None = None
    repeatability_frac: float = 0.05

    def __post_init__(self) -> None:
        for name, v in (("clamp_force_n", self.clamp_force_n),
                        ("torque_nm", self.torque_nm)):
            if v is not None and (not math.isfinite(float(v)) or float(v) < 0.0):
                raise FixtureError(f"{name} must be finite and non-negative "
                                   f"or None for an unrecorded preload")
        if not (0.0 <= float(self.repeatability_frac) < 1.0):
            raise FixtureError("repeatability_frac must be in [0, 1)")

    @property
    def is_known(self) -> bool:
        """Whether a clamp force has actually been recorded."""
        return self.clamp_force_n is not None

    def as_dict(self) -> dict:
        return {
            "clamp_force_n": (None if self.clamp_force_n is None
                              else float(self.clamp_force_n)),
            "torque_nm": (None if self.torque_nm is None
                          else float(self.torque_nm)),
            "repeatability_frac": float(self.repeatability_frac),
            "is_known": self.is_known,
        }


@dataclass(frozen=True)
class OrientationTransform:
    """The rigid placement of the specimen in the fixture frame.

    ``euler_deg`` is an intrinsic (x, y, z) rotation in degrees and
    ``translation_mm`` a translation. A fixture remount that changes either
    is a *new binding* (see :func:`mount`), because it changes where the
    specimen sits in the drive field.
    """

    euler_deg: tuple[float, float, float] = (0.0, 0.0, 0.0)
    translation_mm: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def __post_init__(self) -> None:
        for name, tpl in (("euler_deg", self.euler_deg),
                          ("translation_mm", self.translation_mm)):
            if len(tuple(tpl)) != 3 or not all(
                    math.isfinite(float(v)) for v in tpl):
                raise FixtureError(f"{name} must be a finite 3-tuple")

    def as_dict(self) -> dict:
        return {
            "euler_deg": [float(v) for v in self.euler_deg],
            "translation_mm": [float(v) for v in self.translation_mm],
        }


@dataclass(frozen=True)
class FixtureUncertainty:
    """The repeatability uncertainty a fixture contributes.

    Every term is a relative (fractional) standard uncertainty. These are
    the fixture's contribution to the error budget: how much the modal
    frequency wanders on remount, and how repeatable the clamp force is.
    """

    modal_freq_repeatability_frac: float = 5e-4
    remount_shift_frac: float = 1e-3
    clamp_force_repeatability_frac: float = 0.05
    note: str = "fractional repeatability of a synthetic fixture; unmeasured"

    def __post_init__(self) -> None:
        for name, v in (
                ("modal_freq_repeatability_frac",
                 self.modal_freq_repeatability_frac),
                ("remount_shift_frac", self.remount_shift_frac),
                ("clamp_force_repeatability_frac",
                 self.clamp_force_repeatability_frac)):
            if not (math.isfinite(float(v)) and 0.0 <= float(v) < 1.0):
                raise FixtureError(f"{name} must be in [0, 1)")

    def as_dict(self) -> dict:
        return {
            "modal_freq_repeatability_frac":
                float(self.modal_freq_repeatability_frac),
            "remount_shift_frac": float(self.remount_shift_frac),
            "clamp_force_repeatability_frac":
                float(self.clamp_force_repeatability_frac),
            "note": self.note,
            "measured_here": MEASURED_HERE,
        }


# --- (3) id discipline: fixtures and specimens do not swap ----------------

def _looks_like_specimen_id(value: str) -> bool:
    return str(value).startswith(SPECIMEN_ID_PREFIX)


def _looks_like_fixture_id(value: str) -> bool:
    return str(value).startswith(FIXTURE_ID_PREFIX)


def check_fixture_id(fixture_id: str) -> str:
    """Validate a fixture id, or refuse it. Fixture ids carry ``FIX-``.

    A value that carries the specimen prefix is refused: a fixture id and a
    specimen id live in different namespaces and one is never the other.
    """
    fid = str(fixture_id).strip()
    if not fid:
        raise FixtureError("a fixture needs a non-empty id")
    if _looks_like_specimen_id(fid):
        raise refuse_fixture_id_as_specimen(fid)
    if not _looks_like_fixture_id(fid):
        raise FixtureError(
            f"a fixture id must start with {FIXTURE_ID_PREFIX!r}; got "
            f"{fid!r}. Fixture and specimen ids are separate namespaces")
    return fid


def check_specimen_id(specimen_id: str) -> str:
    """Validate a specimen id for binding, or refuse it. Specimens carry
    ``SPX-``; a fixture id passed as a specimen is refused."""
    sid = str(specimen_id).strip()
    if not sid:
        raise FixtureError("a specimen needs a non-empty id")
    if _looks_like_fixture_id(sid):
        raise FixtureError(
            f"{sid!r} is a fixture id (prefix {FIXTURE_ID_PREFIX!r}), not a "
            f"specimen id; a fixture cannot stand in for the specimen it "
            f"holds")
    if not sid.startswith(SPECIMEN_ID_PREFIX):
        raise FixtureError(
            f"a specimen id must start with {SPECIMEN_ID_PREFIX!r}; got "
            f"{sid!r}")
    return sid


# --- (4) the fixture record -----------------------------------------------

@dataclass(frozen=True)
class FixtureRecord:
    """A typed record of how a specimen is mounted.

    Conforms to the ``fixture_record`` schema (``fixture_id``,
    ``mount_type``, ``contact_points``, ``preload``, ``materials``,
    ``orientation_transform``, ``uncertainty``). It also carries the
    coupling medium, whether an electrode contacts the specimen, the
    dominant boundary condition, the expected perturbation classes, and the
    acquisition provenance -- ``SYNTHETIC`` here, because no fixture is
    built.

    The record does *not* carry a specimen id: binding a specimen is a
    separate act (:func:`mount`) that produces a :class:`RunBinding`, so a
    fixture and a specimen can never be conflated in one field.
    """

    fixture_id: str
    mount_type: MountType
    contact_points: tuple[ContactPoint, ...]
    preload: Preload
    materials: tuple[str, ...]
    orientation: OrientationTransform = field(
        default_factory=OrientationTransform)
    uncertainty: FixtureUncertainty = field(
        default_factory=FixtureUncertainty)
    coupling: CouplingMedium = CouplingMedium.DRY_CONTACT
    electrode_contact: bool = False
    provenance: FixtureProvenance = FixtureProvenance.SYNTHETIC
    expected_perturbations: tuple[PerturbationClass, ...] = (
        PerturbationClass.MODAL_FREQUENCY_SHIFT,)

    def __post_init__(self) -> None:
        object.__setattr__(self, "fixture_id", check_fixture_id(self.fixture_id))
        if not isinstance(self.mount_type, MountType):
            raise FixtureError("mount_type must be a MountType")
        if not self.contact_points:
            raise FixtureError(
                "a fixture needs at least one contact point; a specimen that "
                "touches nothing is not mounted")
        if not all(isinstance(c, ContactPoint) for c in self.contact_points):
            raise FixtureError("every contact point must be a ContactPoint")
        if not self.materials or not all(
                str(m).strip() for m in self.materials):
            raise FixtureError(
                "a fixture needs a non-empty material stack; the interface "
                "material is part of the boundary condition")
        if not isinstance(self.preload, Preload):
            raise FixtureError("preload must be a Preload")
        if not isinstance(self.coupling, CouplingMedium):
            raise FixtureError("coupling must be a CouplingMedium")
        if not isinstance(self.provenance, FixtureProvenance):
            raise FixtureError("provenance must be a FixtureProvenance")

    @property
    def boundary(self) -> BoundaryCondition:
        """The dominant boundary condition this mount imposes."""
        return MOUNT_BOUNDARY[self.mount_type]

    def as_record(self) -> dict:
        """The record as the ``fixture_record`` schema requires it.

        Every required key is present: ``fixture_id`` (str), ``mount_type``
        (str), ``contact_points`` (array), ``preload`` (object),
        ``materials`` (array), ``orientation_transform`` (object) and
        ``uncertainty`` (object).
        """
        return {
            "fixture_id": self.fixture_id,
            "mount_type": self.mount_type.value,
            "contact_points": [c.as_dict() for c in self.contact_points],
            "preload": self.preload.as_dict(),
            "materials": list(self.materials),
            "orientation_transform": self.orientation.as_dict(),
            "uncertainty": self.uncertainty.as_dict(),
            # provenance and firewall context, beyond the required keys
            "coupling": self.coupling.value,
            "electrode_contact": bool(self.electrode_contact),
            "boundary": self.boundary.value,
            "expected_perturbations": [p.value
                                       for p in self.expected_perturbations],
            "provenance": self.provenance.value,
            "claim_class": CLAIM_CLASS,
            "measured_here": MEASURED_HERE,
        }

    def content_hash(self) -> str:
        """A deterministic hash of the record's identifying content."""
        return _canonical_hash(self.as_record())


def _canonical_hash(obj: object) -> str:
    """A deterministic SHA-256 over a canonical rendering of ``obj``."""
    canonical = _canonical_string(obj)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _canonical_string(obj: object) -> str:
    """A stable, sorted, wall-clock-free string form of a JSON-like value."""
    if isinstance(obj, dict):
        items = sorted((str(k), _canonical_string(v)) for k, v in obj.items())
        return "{" + ",".join(f"{k}:{v}" for k, v in items) + "}"
    if isinstance(obj, (list, tuple)):
        return "[" + ",".join(_canonical_string(v) for v in obj) + "]"
    if isinstance(obj, bool):
        return "true" if obj else "false"
    if obj is None:
        return "null"
    if isinstance(obj, float):
        return repr(float(obj))
    return str(obj)


# --- (5) remounting as a new binding --------------------------------------

@dataclass(frozen=True)
class RunBinding:
    """A specimen bound to a fixture for one mount.

    A binding names the fixture, the specimen, and the mount index -- the
    zero-based count of times this specimen has been mounted in this
    fixture. Its ``binding_hash`` folds all three together, so **remounting
    the same specimen in the same fixture produces a distinct binding**:
    the mount index differs, so the hash differs, and the two runs are not
    the same binding even though the parts are identical.
    """

    binding_id: str
    fixture_id: str
    specimen_id: str
    mount_index: int
    fixture_content_hash: str
    binding_hash: str

    def as_dict(self) -> dict:
        return {
            "binding_id": self.binding_id,
            "fixture_id": self.fixture_id,
            "specimen_id": self.specimen_id,
            "mount_index": self.mount_index,
            "fixture_content_hash": self.fixture_content_hash,
            "binding_hash": self.binding_hash,
            "claim_class": CLAIM_CLASS,
            "measured_here": MEASURED_HERE,
        }


def mount(fixture: FixtureRecord, specimen_id: str,
          mount_index: int = 0) -> RunBinding:
    """Bind a specimen into a fixture for one mount, and record the binding.

    Refuses to bind a specimen whose id is really a fixture id (they cannot
    swap), and refuses a negative mount index. The binding hash includes
    the mount index, so calling :func:`mount` again with the next index --
    a *remount* -- yields a distinct binding, which is exactly how the
    registry records that the specimen was taken out and put back.
    """
    fid = check_fixture_id(fixture.fixture_id)
    sid = check_specimen_id(specimen_id)
    if fid == sid:
        raise FixtureError(
            "a fixture id and a specimen id cannot be equal; they are "
            "different namespaces")
    if int(mount_index) < 0:
        raise FixtureError("mount_index must be a non-negative integer")
    content = fixture.content_hash()
    payload = {
        "fixture_id": fid,
        "specimen_id": sid,
        "mount_index": int(mount_index),
        "fixture_content_hash": content,
    }
    binding_hash = _canonical_hash(payload)
    binding_id = f"BND-{binding_hash[:16]}"
    return RunBinding(
        binding_id=binding_id, fixture_id=fid, specimen_id=sid,
        mount_index=int(mount_index), fixture_content_hash=content,
        binding_hash=binding_hash)


def remount(fixture: FixtureRecord, previous: RunBinding) -> RunBinding:
    """Take the specimen out and put it back: a new binding, next index."""
    if previous.fixture_id != check_fixture_id(fixture.fixture_id):
        raise FixtureError(
            "a remount must use the same fixture as the previous binding")
    return mount(fixture, previous.specimen_id, previous.mount_index + 1)


# --- (6) boundary conditions and synthetic modal frequencies --------------

#: The R11 chain the fixture study runs on: a grounded, conservative
#: mass-spring chain with no electrode, so every modal change is the
#: boundary condition's doing and nothing else. Model numbers throughout.
DEFAULT_FIXTURE_CHAIN = mb.ChainConfig(
    n_nodes=6, node_mass=1.0, internal_stiffness=1.0,
    support_stiffness=0.6, boundary_stiffness=BOUNDARY_STIFFNESS[
        BoundaryCondition.SPRING],
    electrode_mass=0.0, electrode_stiffness=0.0,
).conservative()


def modal_frequencies(boundary: BoundaryCondition,
                      chain: mb.ChainConfig = DEFAULT_FIXTURE_CHAIN,
                      ) -> np.ndarray:
    """The ascending synthetic modal frequencies for a boundary condition.

    The boundary condition sets the end stiffness of the R11 chain; the
    frequencies come from solving ``K v = omega**2 M v`` for that grounded
    chain (:func:`r11.mechboundary.system_modes`). They are model numbers
    in the chain's own units, not a measurement of anything.
    """
    if boundary not in BOUNDARY_STIFFNESS:
        raise FixtureError(f"unknown boundary condition {boundary!r}")
    config = replace(chain, boundary_stiffness=BOUNDARY_STIFFNESS[boundary])
    system = mb.build_system(config)
    return mb.system_modes(system).omega


@dataclass(frozen=True)
class FixtureShift:
    """A modal shift caused by changing the fixture boundary condition."""

    from_boundary: BoundaryCondition
    to_boundary: BoundaryCondition
    mode_index: int
    omega_before: float
    omega_after: float

    @property
    def delta(self) -> float:
        return self.omega_after - self.omega_before

    @property
    def fractional_shift(self) -> float:
        if self.omega_before == 0.0:
            raise FixtureError("cannot take a fractional shift of a zero mode")
        return self.delta / self.omega_before

    def as_dict(self) -> dict:
        return {
            "from_boundary": self.from_boundary.value,
            "to_boundary": self.to_boundary.value,
            "mode_index": self.mode_index,
            "omega_before": self.omega_before,
            "omega_after": self.omega_after,
            "delta": self.delta,
            "fractional_shift": self.fractional_shift,
        }


def fixture_modal_shift(from_boundary: BoundaryCondition,
                        to_boundary: BoundaryCondition,
                        mode_index: int = 0,
                        chain: mb.ChainConfig = DEFAULT_FIXTURE_CHAIN,
                        ) -> FixtureShift:
    """How much one mode moves when the fixture boundary changes.

    Both frequencies come from the same chain with different end
    stiffnesses, so the difference is entirely the fixture's doing. That is
    the whole point: the shift is real, and it is ordinary.
    """
    omega_before = modal_frequencies(from_boundary, chain)
    omega_after = modal_frequencies(to_boundary, chain)
    if not 0 <= int(mode_index) < omega_before.size:
        raise FixtureError("mode index outside the synthetic modal basis")
    return FixtureShift(
        from_boundary=from_boundary, to_boundary=to_boundary,
        mode_index=int(mode_index),
        omega_before=float(omega_before[int(mode_index)]),
        omega_after=float(omega_after[int(mode_index)]))


def fixture_change_ledger(from_boundary: BoundaryCondition,
                          to_boundary: BoundaryCondition,
                          coordinate: float = 1.0) -> dict:
    """Book a fixture boundary change through the R13 energy ledger.

    Changing the end stiffness while the resonator holds energy does
    boundary work (:mod:`r13.boundaryenergy`); the ledger closes with that
    work on the input side and reports no new energy. The fixture is the
    route through which an external agent (the clamp, the actuator) pays,
    never a source.
    """
    change = be.BoundaryChange(
        domain=be.BoundaryDomain.MECHANICAL,
        param_before=BOUNDARY_STIFFNESS[from_boundary],
        param_after=BOUNDARY_STIFFNESS[to_boundary],
        coordinate=float(coordinate))
    return be.abrupt_change(change).as_dict()


# --- (7) the firewall: a fixture effect is not a signal -------------------

def fixture_shift_is_ordinary(from_boundary: BoundaryCondition,
                              to_boundary: BoundaryCondition,
                              mode_index: int = 0,
                              chain: mb.ChainConfig = DEFAULT_FIXTURE_CHAIN,
                              ) -> dict:
    """Classify a fixture-induced modal shift as a FIXTURE_EFFECT.

    A shift produced by changing the mount is a *known ordinary effect*: it
    is one of the explanations a residual must survive before it can even
    be called an ``UNEXPLAINED_INSTRUMENT_RESIDUAL``. This returns the
    shift with claim class ``FIXTURE_EFFECT`` and ``is_signal`` false, and
    it books the change through the energy ledger to show nothing new was
    created.
    """
    shift = fixture_modal_shift(from_boundary, to_boundary, mode_index, chain)
    ledger = fixture_change_ledger(from_boundary, to_boundary)
    return {
        "what_this_is": (
            "a modal-frequency shift caused by changing the fixture "
            "boundary condition, classified as a known ordinary effect"),
        "shift": shift.as_dict(),
        "energy_ledger": ledger,
        "is_signal": False,
        "is_ordinary": True,
        "claim_class": FIXTURE_EFFECT,
        "ordinary_explanation": (
            "a fixture change shifts a mode; the shift is the mount's, not "
            "the specimen's, and it must be subtracted before any residual "
            "is examined"),
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
    }


def refuse_fixture_effect_as_signal(
        shift: float = 0.0,
        claimed_signal: str = "a specimen resonance shift") -> None:
    """Refuse a fixture-induced modal shift being read as a signal. Raises.

    A change of clamp, support, coupling, or orientation moves the modes.
    That movement is a ``FIXTURE_EFFECT`` -- an ordinary explanation in the
    R15 taxonomy, not a property of the specimen. Attributing it to the
    specimen conflates the mount with the sample and manufactures a signal
    out of the bench. To read a shift as a specimen signal, the fixture
    must be held identical across the comparison and its repeatability must
    bound the shift; a shift produced *by changing the fixture* fails that
    at the first step.
    """
    raise FixtureError(
        f"refused: attributing a fixture-induced modal shift of "
        f"{float(shift):g} to {claimed_signal!r}. A change of mount, "
        f"preload, coupling medium, or orientation shifts the modes by "
        f"itself; that shift is a {FIXTURE_EFFECT}, one of the ordinary "
        f"explanations a residual must survive, not a specimen signal. The "
        f"fixture is the route, not the source: hold it identical across "
        f"the comparison and bound the shift by its repeatability before "
        f"any residual is examined. {VERDICT}")


def refuse_fixture_id_as_specimen(fixture_id: str = "FIX-0000") -> FixtureError:
    """Build the refusal for a fixture id used where a specimen is meant.

    Returned (not raised) so callers can ``raise`` it in context. A fixture
    id and a specimen id are different namespaces and one is never the
    other; swapping them would let the mount masquerade as the sample.
    """
    return FixtureError(
        f"refused: {fixture_id!r} is a fixture id (prefix "
        f"{FIXTURE_ID_PREFIX!r}) used where a specimen id (prefix "
        f"{SPECIMEN_ID_PREFIX!r}) is required. Fixture and specimen ids are "
        f"separate namespaces and cannot be swapped: a fixture holds a "
        f"specimen, it is not one. {VERDICT}")


# --- (8) the error budget and the precision-claim gate --------------------

def fixture_error_budget(fixture: FixtureRecord,
                         quantity: str = "modal_frequency_fractional",
                         clamp_force_sensitivity: float = 0.5,
                         coverage_factor: float = DEFAULT_K_SIGMA) -> dict:
    """The fixture's contribution to the error budget, in quadrature.

    Conforms to the ``error_budget`` schema. Three components enter: the
    modal-frequency repeatability, the remount shift, and the clamp-force
    repeatability propagated through a declared sensitivity. They combine
    in quadrature to a fractional combined standard uncertainty, reported
    with a coverage factor. Every number is a declared model repeatability,
    not a measured one.
    """
    if float(coverage_factor) <= 0.0:
        raise FixtureError("coverage factor must be positive")
    u = fixture.uncertainty
    clamp_term = float(clamp_force_sensitivity) * u.clamp_force_repeatability_frac
    components = [
        {"name": "fixture_modal_repeatability",
         "sigma": float(u.modal_freq_repeatability_frac),
         "kind": "fixture", "distribution": "normal"},
        {"name": "fixture_remount_shift",
         "sigma": float(u.remount_shift_frac),
         "kind": "fixture", "distribution": "normal"},
        {"name": "clamp_force_repeatability",
         "sigma": float(clamp_term),
         "kind": "fixture", "distribution": "normal",
         "sensitivity": float(clamp_force_sensitivity),
         "known_preload": fixture.preload.is_known},
    ]
    combined = float(np.sqrt(sum(c["sigma"] ** 2 for c in components)))
    return {
        "budget_id": f"EB-FIX-{fixture.fixture_id}",
        "quantity": quantity,
        "components": components,
        "combination_method": "quadrature",
        "combined_uncertainty": combined,
        "coverage_factor": float(coverage_factor),
        "expanded_uncertainty": combined * float(coverage_factor),
        "preload_known": fixture.preload.is_known,
        "claim_class": CLAIM_CLASS,
        "measured_here": MEASURED_HERE,
        "note": ("the fixture's contribution to the error budget; every "
                 "term is a declared repeatability, none is measured"),
    }


def precision_claim_supported(fixture: FixtureRecord) -> bool:
    """Whether the fixture can support a precision claim.

    It cannot without a recorded clamp force: an unknown preload leaves the
    contact stiffness -- and hence the modal frequency -- unconstrained, so
    the repeatability that a precision claim rests on is undefined.
    """
    return fixture.preload.is_known


def assert_precision_claim(fixture: FixtureRecord) -> None:
    """Block a precision claim when the preload is unrecorded. Raises then.

    A missing preload is a ``BLOCKED_MISSING_INPUT`` for anything that
    depends on the contact stiffness being repeatable.
    """
    if not precision_claim_supported(fixture):
        raise FixtureError(
            f"refused: a precision claim for fixture "
            f"{fixture.fixture_id!r} with an unrecorded preload. The clamp "
            f"force sets the contact stiffness and therefore the modal "
            f"frequency; without it the repeatability a precision claim "
            f"rests on is undefined. This is BLOCKED_MISSING_INPUT until a "
            f"clamp force is recorded. {VERDICT}")


# --- (9) reversal and sensor-permutation plans ----------------------------

def reversal_plan(fixture: FixtureRecord, n_remounts: int = 3) -> dict:
    """A deterministic remount/reversal plan to average out fixture bias.

    The specimen is mounted, dismounted, and remounted ``n_remounts``
    times, alternating a 180-degree reversal so a fixed orientation bias
    cancels across the set. Each mount is a distinct binding index; the
    plan is a protocol, not a run, and nothing in it is executed here.
    """
    if int(n_remounts) < 1:
        raise FixtureError("a reversal plan needs at least one remount")
    steps = []
    for i in range(int(n_remounts)):
        steps.append({
            "mount_index": i,
            "action": "MOUNT" if i == 0 else "REMOUNT",
            "reversal_deg": 180.0 if i % 2 == 1 else 0.0,
            "note": ("alternating reversal so a fixed orientation bias "
                     "cancels across the remounts"),
        })
    return {
        "fixture_id": fixture.fixture_id,
        "n_remounts": int(n_remounts),
        "steps": steps,
        "purpose": ("separate a fixed fixture bias from any specimen "
                    "property by averaging over remounts and reversals"),
        "claim_class": CLAIM_CLASS,
        "measured_here": MEASURED_HERE,
        "executed": False,
    }


def sensor_permutation_plan(sensors: tuple[str, ...],
                            max_permutations: int = 6) -> dict:
    """A deterministic sensor-permutation plan.

    Permuting which sensor sits at which port separates a per-sensor
    fixture effect (a contact resonance at one position) from a specimen
    property (which follows the specimen, not the port). The permutations
    are enumerated in lexicographic order and capped, so the plan is
    reproducible. It is a protocol; no sensor is read here.
    """
    names = tuple(str(s) for s in sensors)
    if len(names) < 2:
        raise FixtureError(
            "a sensor-permutation plan needs at least two sensors")
    if len(set(names)) != len(names):
        raise FixtureError("sensor labels must be distinct")
    if int(max_permutations) < 1:
        raise FixtureError("max_permutations must be positive")
    perms = list(itertools.islice(
        itertools.permutations(names), int(max_permutations)))
    return {
        "sensors": list(names),
        "n_permutations": len(perms),
        "permutations": [list(p) for p in perms],
        "purpose": ("a fixture effect stays with the port; a specimen "
                    "property follows the specimen. Permuting sensors "
                    "across ports tells the two apart"),
        "claim_class": CLAIM_CLASS,
        "measured_here": MEASURED_HERE,
        "executed": False,
    }


# --- (10) the registry ----------------------------------------------------

def _centre_clamp() -> FixtureRecord:
    return FixtureRecord(
        fixture_id="FIX-CENTRE-CLAMP",
        mount_type=MountType.CENTRE_CLAMP,
        contact_points=(
            ContactPoint("clamp", (0.0, 0.0, 0.0),
                         BoundaryCondition.FIXED, 5.0e4),),
        preload=Preload(clamp_force_n=20.0, torque_nm=0.5,
                        repeatability_frac=0.03),
        materials=("stainless steel clamp", "brass insert"),
        coupling=CouplingMedium.DRY_CONTACT,
        expected_perturbations=(PerturbationClass.MODAL_FREQUENCY_SHIFT,
                                PerturbationClass.MODE_SPLITTING))


def _three_point() -> FixtureRecord:
    return FixtureRecord(
        fixture_id="FIX-THREE-POINT",
        mount_type=MountType.THREE_POINT,
        contact_points=tuple(
            ContactPoint(f"pt{i}", pos, BoundaryCondition.SPRING, 1.2e3)
            for i, pos in enumerate((
                (10.0, 0.0, 0.0), (-5.0, 8.66, 0.0), (-5.0, -8.66, 0.0)))),
        preload=Preload(clamp_force_n=5.0, torque_nm=None,
                        repeatability_frac=0.04),
        materials=("hardened steel ball", "aluminium seat"),
        coupling=CouplingMedium.DRY_CONTACT,
        expected_perturbations=(PerturbationClass.MODAL_FREQUENCY_SHIFT,
                                PerturbationClass.CONTACT_RESONANCE))


def _suspension() -> FixtureRecord:
    return FixtureRecord(
        fixture_id="FIX-SUSPENSION",
        mount_type=MountType.SUSPENSION,
        contact_points=(
            ContactPoint("thread_a", (0.0, 12.0, 0.0),
                         BoundaryCondition.FREE, 2.0),
            ContactPoint("thread_b", (0.0, -12.0, 0.0),
                         BoundaryCondition.FREE, 2.0)),
        preload=Preload(clamp_force_n=None, torque_nm=None,
                        repeatability_frac=0.10),
        materials=("nylon thread", "PTFE knot"),
        coupling=CouplingMedium.SUSPENSION_THREAD,
        expected_perturbations=(PerturbationClass.MODAL_FREQUENCY_SHIFT,
                                PerturbationClass.Q_FACTOR_CHANGE))


def _elastomer() -> FixtureRecord:
    return FixtureRecord(
        fixture_id="FIX-ELASTOMER",
        mount_type=MountType.ELASTOMER,
        contact_points=(
            ContactPoint("pad", (0.0, 0.0, -5.0),
                         BoundaryCondition.SPRING, 3.0e2),),
        preload=Preload(clamp_force_n=2.0, torque_nm=None,
                        repeatability_frac=0.08),
        materials=("silicone elastomer pad", "anodised aluminium base"),
        coupling=CouplingMedium.ELASTOMER_PAD,
        expected_perturbations=(PerturbationClass.MODAL_FREQUENCY_SHIFT,
                                PerturbationClass.Q_FACTOR_CHANGE,
                                PerturbationClass.AMPLITUDE_CHANGE))


def _adhesive() -> FixtureRecord:
    return FixtureRecord(
        fixture_id="FIX-ADHESIVE",
        mount_type=MountType.ADHESIVE,
        contact_points=(
            ContactPoint("bond", (0.0, 0.0, 0.0),
                         BoundaryCondition.FIXED, 8.0e4),),
        preload=Preload(clamp_force_n=0.0, torque_nm=None,
                        repeatability_frac=0.02),
        materials=("cyanoacrylate bond line", "glass substrate"),
        coupling=CouplingMedium.ADHESIVE_BOND,
        electrode_contact=True,
        expected_perturbations=(PerturbationClass.MODAL_FREQUENCY_SHIFT,))


def _synthetic() -> FixtureRecord:
    return FixtureRecord(
        fixture_id="FIX-SYNTHETIC",
        mount_type=MountType.SYNTHETIC,
        contact_points=(
            ContactPoint("virtual", (0.0, 0.0, 0.0),
                         BoundaryCondition.SPRING, 1.0),),
        preload=Preload(clamp_force_n=1.0, torque_nm=None,
                        repeatability_frac=0.0),
        materials=("synthetic model interface",),
        coupling=CouplingMedium.AIR_GAP,
        provenance=FixtureProvenance.SYNTHETIC,
        expected_perturbations=(PerturbationClass.MODAL_FREQUENCY_SHIFT,))


#: The example registry: one record per mount type. Every one is a
#: SYNTHETIC design line; no fixture has been machined.
FIXTURE_REGISTRY: dict[str, FixtureRecord] = {
    r.fixture_id: r for r in (
        _centre_clamp(), _three_point(), _suspension(),
        _elastomer(), _adhesive(), _synthetic())
}


def fixture(fixture_id: str) -> FixtureRecord:
    """The registered fixture record for an id."""
    try:
        return FIXTURE_REGISTRY[fixture_id]
    except KeyError:
        raise FixtureError(
            f"{fixture_id!r} is not a registered fixture; the registry "
            f"holds {sorted(FIXTURE_REGISTRY)}") from None


# --- (11) the report ------------------------------------------------------

def fixtures_report() -> dict:
    """The standing statement of what the fixture registry is and is not."""
    example = fixture("FIX-CENTRE-CLAMP")
    shift = fixture_shift_is_ordinary(
        BoundaryCondition.FREE, BoundaryCondition.FIXED)
    return {
        "what_this_is": (
            "a typed fixture registry and boundary-condition model: how a "
            "specimen is mounted (centre clamp, three-point, suspension, "
            "elastomer, adhesive, synthetic), its contact geometry, "
            "preload, materials, orientation and repeatability, and the "
            "synthetic modal frequencies the boundary condition imposes"),
        "mount_types": [m.value for m in MountType],
        "boundary_conditions": [b.value for b in BoundaryCondition],
        "boundary_stiffness": {b.value: BOUNDARY_STIFFNESS[b]
                               for b in BoundaryCondition},
        "coupling_media": [c.value for c in CouplingMedium],
        "provenance_modes": [p.value for p in FixtureProvenance],
        "expected_perturbation_classes": [p.value for p in PerturbationClass],
        "n_registered": len(FIXTURE_REGISTRY),
        "registered": sorted(FIXTURE_REGISTRY),
        "example_record": example.as_record(),
        "example_error_budget": fixture_error_budget(example),
        "fixture_shift_is_a_fixture_effect": {
            "claim_class": shift["claim_class"],
            "is_signal": shift["is_signal"],
        },
        "id_namespaces": {
            "fixture_prefix": FIXTURE_ID_PREFIX,
            "specimen_prefix": SPECIMEN_ID_PREFIX,
            "can_swap": False,
        },
        "reused": [
            "r11.mechboundary (grounded chain, K v = omega**2 M v modes)",
            "r13.boundaryenergy (fixture change booked as boundary work)",
            "r15.claims (FIXTURE_EFFECT ordinary-explanation class)",
        ],
        "refusals": [
            "refuse_fixture_effect_as_signal",
            "refuse_fixture_id_as_specimen",
            "assert_precision_claim blocks on an unrecorded preload",
        ],
        "firewalls": [
            "a fixture-induced modal shift is a FIXTURE_EFFECT, never a "
            "specimen signal",
            "a fixture id and a specimen id are separate namespaces and "
            "cannot be swapped",
            "an unrecorded preload blocks any precision claim",
            "remounting the same specimen produces a distinct binding",
        ],
        "hardware_status": (
            "SYNTHETIC - no fixture has been machined, no specimen mounted, "
            "no clamp torqued; every record is a synthetic design line"),
        "claim_class": CLAIM_CLASS,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any fixture exists, that any specimen was "
            "mounted, or that any clamp force, torque, modal frequency or "
            "repeatability was measured: every number is a declared model "
            "value in the R11 chain's own units. It does not say a fixture "
            "change is a signal -- a shift produced by changing the mount "
            "is a FIXTURE_EFFECT, an ordinary explanation, and the "
            "firewall refuses to promote it. No apparatus was operated."),
    }


__all__ = [
    "VERDICT", "CLAIM_CLASS", "FIXTURE_EFFECT", "MEASURED_HERE",
    "PHYSICAL_VALIDATION", "FIXTURE_ID_PREFIX", "SPECIMEN_ID_PREFIX",
    "FixtureError", "MountType", "BoundaryCondition", "CouplingMedium",
    "FixtureProvenance", "PerturbationClass", "BOUNDARY_STIFFNESS",
    "MOUNT_BOUNDARY", "ContactPoint", "Preload", "OrientationTransform",
    "FixtureUncertainty", "check_fixture_id", "check_specimen_id",
    "FixtureRecord", "RunBinding", "mount", "remount",
    "DEFAULT_FIXTURE_CHAIN", "modal_frequencies", "FixtureShift",
    "fixture_modal_shift", "fixture_change_ledger",
    "fixture_shift_is_ordinary", "refuse_fixture_effect_as_signal",
    "refuse_fixture_id_as_specimen", "fixture_error_budget",
    "precision_claim_supported", "assert_precision_claim", "reversal_plan",
    "sensor_permutation_plan", "FIXTURE_REGISTRY", "fixture",
    "fixtures_report",
]
