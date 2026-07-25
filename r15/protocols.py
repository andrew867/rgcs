"""P07 — the executable protocol engine: a frozen plan of authorized steps.

An experiment is only reproducible if the *plan* it runs is fixed before
the run and cannot drift during it. This module turns a preregistered
procedure into a typed, ordered, hash-sealed :class:`Protocol` -- a
sequence of authorized steps (arm the apparatus, bind a calibration, a
specimen and a fixture, acquire, record) with setpoints, tolerances,
controls, stop conditions, an analysis plan and a *claim cap* -- and then
freezes it so any later edit is detectable.

**What a protocol carries.** A :class:`Protocol` matches
``protocol_record.schema.json``: an id and a version, the hypotheses it
tests, its controls, its randomization and blinding descriptors, an
ordered tuple of :class:`ProtocolStep`, its stop conditions, its analysis
plan, and its ``claim_cap`` -- the strongest class the protocol is ever
allowed to claim. The claim cap is checked against the R15 taxonomy at
construction: a protocol may never cap itself at a measurement class,
because no plan, however careful, turns a synthetic run into a physical
measurement. The acquisition steps cover the maneuvers the pack calls out
-- sweeps, fixed tones, pulses, ringdowns, environmental soaks,
remounting, reversals and shams -- each an :class:`Maneuver`.

**Binding to capabilities and calibration.** Every step names the
capability it needs. Acquisition steps may also require a bound
calibration. Nothing here operates a device; the binding is what the
runner (P07's :mod:`r15.protocol_runner`) checks an authorized
configuration against before it will compile a plan.

**Freezing.** :func:`freeze` records a SHA-256 seal over the protocol's
canonical serialization (reusing the R13 serialization authority in
:mod:`r13.serialize`, so there is one canonicalisation, not two). The seal
is deterministic -- the same protocol always yields the same hash -- and
tamper-evident: :func:`refuse_edit_after_seal` shows that changing any
field after freezing produces a different hash, i.e. a new version.

Nothing here is measured. Freezing a plan is bookkeeping about *order*;
it does not run the study. :func:`protocols_report` records a claim class
of ``SOFTWARE_IMPLEMENTED`` and the standing verdict
``EXECUTABLE_PROTOCOL_FROZEN_NO_PHYSICAL_RUN``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from r13 import experiments as r13_experiments
from r13 import preregister as r13_preregister
from r13 import serialize as r13_serialize
from r15 import claims as r15_claims

#: The standing verdict for a well-formed, frozen protocol.
DEFAULT_VERDICT = "EXECUTABLE_PROTOCOL_FROZEN_NO_PHYSICAL_RUN"

#: The claim class this module (as software) is entitled to.
MODULE_CLAIM_CLASS = r15_claims.ClaimClass.SOFTWARE_IMPLEMENTED.value

PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"


class ProtocolError(RuntimeError):
    """Raised on a malformed protocol, a claim cap above the software
    ceiling, a step that names no capability, an acquisition step with no
    maneuver, or an edit to a frozen protocol presented as the original."""


# =======================================================================
# The step vocabulary
# =======================================================================

class StepKind(Enum):
    """The authorized step kinds, in the order a run performs them.

    The lifecycle is fixed: the apparatus is ARMed, a calibration, a
    specimen and a fixture are BOUND, acquisition happens, and the result
    is RECORDed. A compiled plan is an ordered sequence of these."""

    ARM = "ARM"
    BIND_CALIBRATION = "BIND_CALIBRATION"
    BIND_SPECIMEN = "BIND_SPECIMEN"
    BIND_FIXTURE = "BIND_FIXTURE"
    ACQUIRE = "ACQUIRE"
    RECORD = "RECORD"


class Maneuver(Enum):
    """The acquisition maneuvers a protocol may schedule.

    An ``ACQUIRE`` step carries exactly one of these. They are the drive /
    excitation patterns the pack enumerates; a ``SHAM`` is a null maneuver
    (the apparatus is exercised with the drive nominally off) and a
    ``REVERSAL`` swaps the sign of the drive, both controls."""

    SWEEP = "SWEEP"
    FIXED_TONE = "FIXED_TONE"
    PULSE = "PULSE"
    RINGDOWN = "RINGDOWN"
    ENVIRONMENTAL_SOAK = "ENVIRONMENTAL_SOAK"
    REMOUNT = "REMOUNT"
    REVERSAL = "REVERSAL"
    SHAM = "SHAM"


class StopKind(Enum):
    """How a stop condition terminates a run."""

    MAX_ACQUISITIONS = "MAX_ACQUISITIONS"   # stop after N acquire steps
    MAX_STEPS = "MAX_STEPS"                  # stop after N total steps
    THRESHOLD_EXCEEDED = "THRESHOLD_EXCEEDED"  # stop if a reading passes a limit
    FAULT_DETECTED = "FAULT_DETECTED"        # stop on an injected/observed fault


@dataclass(frozen=True)
class Setpoint:
    """A commanded value with an explicit tolerance band and unit.

    ``tolerance`` is the symmetric half-width the reading must fall within
    for the setpoint to be considered met; it is part of the plan, not the
    result, and is fixed before the run."""

    name: str
    value: float
    unit: str
    tolerance: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ProtocolError("a setpoint needs a name")
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ProtocolError(f"setpoint {self.name!r} needs a unit")
        if float(self.tolerance) < 0.0:
            raise ProtocolError(
                f"setpoint {self.name!r} tolerance must be non-negative")

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "value": float(self.value),
            "unit": self.unit,
            "tolerance": float(self.tolerance),
        }


@dataclass(frozen=True)
class ProtocolStep:
    """One authorized step: a kind, the capability it needs, and (for an
    acquisition) the maneuver and its setpoints.

    Every step names the ``capability`` the executing configuration must
    be authorized for -- this is the binding the runner checks before it
    will acquire anything. An ``ACQUIRE`` step must carry a
    :class:`Maneuver`; a non-acquisition step must not. ``requires_
    calibration`` marks a step that may not run against an unbound
    calibration."""

    index: int
    kind: StepKind
    capability: str
    maneuver: Maneuver | None = None
    setpoints: tuple = ()
    requires_calibration: bool = False
    description: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.kind, StepKind):
            raise ProtocolError("step kind must be a StepKind")
        if not isinstance(self.capability, str) or not self.capability.strip():
            raise ProtocolError(
                f"step {self.index} ({self.kind.value}) names no capability; "
                f"every step must bind to a capability the configuration is "
                f"authorized for")
        if self.kind is StepKind.ACQUIRE:
            if not isinstance(self.maneuver, Maneuver):
                raise ProtocolError(
                    f"acquisition step {self.index} must carry a Maneuver "
                    f"(sweep, fixed tone, pulse, ringdown, soak, remount, "
                    f"reversal, or sham)")
        else:
            if self.maneuver is not None:
                raise ProtocolError(
                    f"step {self.index} ({self.kind.value}) is not an "
                    f"acquisition and may not carry a maneuver")
        for sp in self.setpoints:
            if not isinstance(sp, Setpoint):
                raise ProtocolError(
                    f"step {self.index} setpoints must be Setpoint instances")

    def as_dict(self) -> dict:
        return {
            "index": self.index,
            "kind": self.kind.value,
            "capability": self.capability,
            "maneuver": self.maneuver.value if self.maneuver else None,
            "setpoints": [sp.as_dict() for sp in self.setpoints],
            "requires_calibration": bool(self.requires_calibration),
            "description": self.description,
        }


@dataclass(frozen=True)
class StopCondition:
    """A rule that terminates a run when its limit is reached.

    ``kind`` selects what is counted or compared and ``limit`` is the
    threshold. Stop conditions are fixed in the plan so a run's length is
    not chosen once the data are in view (the optional-stopping lesson from
    R13's preregistration authority)."""

    name: str
    kind: StopKind
    limit: float
    description: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.kind, StopKind):
            raise ProtocolError("stop condition kind must be a StopKind")
        if not isinstance(self.name, str) or not self.name.strip():
            raise ProtocolError("a stop condition needs a name")

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind.value,
            "limit": float(self.limit),
            "description": self.description,
        }


# =======================================================================
# The protocol
# =======================================================================

@dataclass(frozen=True)
class Protocol:
    """A frozen-able experimental protocol matching
    ``protocol_record.schema.json``.

    The ``claim_cap`` is the strongest class this protocol may ever claim,
    and it is validated at construction against the R15 taxonomy: a cap set
    to a measurement class is refused, because no plan turns a synthetic
    run into a physical measurement. ``steps`` must be non-empty and its
    indices must be 0..n-1 in order, so a compiled plan is unambiguous.
    ``preregistration_hash`` optionally carries the seal of the R13
    preregistration this protocol implements."""

    protocol_id: str
    version: str
    hypotheses: tuple
    controls: tuple
    randomization: dict
    blinding: dict
    steps: tuple
    stop_conditions: tuple
    analysis_plan: dict
    claim_cap: str
    preregistration_hash: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.protocol_id, str) or \
                not self.protocol_id.strip():
            raise ProtocolError("protocol_id must be a non-empty string")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ProtocolError("version must be a non-empty string")
        if not self.hypotheses:
            raise ProtocolError(
                "a protocol must state at least one hypothesis it tests")
        if not self.steps:
            raise ProtocolError(
                "a protocol with no steps compiles to nothing; add the "
                "authorized steps (arm, bind, acquire, record)")
        for i, step in enumerate(self.steps):
            if not isinstance(step, ProtocolStep):
                raise ProtocolError("every step must be a ProtocolStep")
            if step.index != i:
                raise ProtocolError(
                    f"step indices must be 0..n-1 in order; step at "
                    f"position {i} has index {step.index}")
        for sc in self.stop_conditions:
            if not isinstance(sc, StopCondition):
                raise ProtocolError(
                    "every stop condition must be a StopCondition")
        self._validate_claim_cap()

    def _validate_claim_cap(self) -> None:
        """Refuse a claim cap at or above a physical-measurement class.

        The R15 taxonomy separates what software can produce from what only
        physical acquisition can. A protocol executed here reaches, at
        most, a synthetic observation; a plan that caps itself at
        ``PHYSICAL_MEASUREMENT`` (or any measurement class) is claiming an
        outcome the environment cannot produce."""
        if not isinstance(self.claim_cap, str) or not self.claim_cap.strip():
            raise ProtocolError("claim_cap must be a non-empty string")
        try:
            capped = r15_claims.ClaimClass(self.claim_cap)
        except ValueError:
            raise ProtocolError(
                f"claim_cap {self.claim_cap!r} is not an R15 claim class")
        if capped in r15_claims.MEASUREMENT_CLASSES:
            raise ProtocolError(
                f"refused: a protocol may not cap its claim at "
                f"{self.claim_cap!r}, a measurement class. Executing this "
                f"plan here produces at most a SYNTHETIC_OBSERVATION; a "
                f"physical measurement needs an instrument operating on a "
                f"specimen, which this environment does not provide. Cap the "
                f"claim at a software-reachable class.")

    def acquisition_steps(self) -> tuple:
        return tuple(s for s in self.steps if s.kind is StepKind.ACQUIRE)

    def required_capabilities(self) -> tuple:
        """The distinct capabilities every step binds to, in first-seen
        order. The runner checks an authorized configuration covers these."""
        seen: list = []
        for s in self.steps:
            if s.capability not in seen:
                seen.append(s.capability)
        return tuple(seen)

    def to_record(self) -> dict:
        """The dict matching ``protocol_record.schema.json`` -- also the
        canonical object the seal is taken over."""
        return {
            "protocol_id": self.protocol_id,
            "version": self.version,
            "hypotheses": list(self.hypotheses),
            "controls": list(self.controls),
            "randomization": dict(self.randomization),
            "blinding": dict(self.blinding),
            "steps": [s.as_dict() for s in self.steps],
            "stop_conditions": [sc.as_dict() for sc in self.stop_conditions],
            "analysis_plan": dict(self.analysis_plan),
            "claim_cap": self.claim_cap,
            "preregistration_hash": self.preregistration_hash,
        }


# =======================================================================
# Freezing: seal and detect edits
# =======================================================================

#: seal -> canonical serialization. The freeze ledger, append-only in
#: practice, so a seal can be recognised as one this process issued.
_FREEZE_LEDGER: dict = {}


def compile_hash(protocol: Protocol) -> str:
    """The SHA-256 seal over the protocol's canonical record.

    Reuses :func:`r13.serialize.content_hash`, so canonicalisation is the
    single R13 authority (sorted keys, fixed float format) rather than a
    second, divergent one. The hash depends only on the plan's content, so
    the same protocol always seals identically and any changed field
    changes the seal."""
    if not isinstance(protocol, Protocol):
        raise ProtocolError("expected a Protocol")
    return r13_serialize.content_hash(protocol.to_record())


@dataclass(frozen=True)
class SealedProtocol:
    """A protocol frozen at an explicit epoch, plus its seal.

    ``seal`` is the hash the protocol had at freeze time. :meth:`verify`
    recomputes the hash from the carried protocol and compares: if the
    protocol object is the one that was frozen, they match; if a field was
    changed, they do not. ``sealed_epoch`` is passed in, never read from a
    clock, so freezing is deterministic."""

    protocol: Protocol
    seal: str
    sealed_epoch: int

    def verify(self) -> bool:
        """True iff the carried protocol still hashes to the sealed value."""
        return compile_hash(self.protocol) == self.seal


def freeze(protocol: Protocol, *, epoch: int) -> SealedProtocol:
    """Seal a protocol before confirmatory execution and record the seal.

    A confirmatory run is only meaningful if the plan predates it. Freezing
    hashes the whole plan and records the hash; a run then references the
    seal, and any edit to the plan after freezing changes the hash, so an
    edited plan cannot masquerade as the frozen one."""
    seal = compile_hash(protocol)
    _FREEZE_LEDGER.setdefault(seal, r13_serialize.serialize(
        protocol.to_record()))
    return SealedProtocol(protocol=protocol, seal=seal, sealed_epoch=int(epoch))


def is_frozen(seal_or_sealed) -> bool:
    """True iff this seal (or this sealed protocol's seal) is in the
    freeze ledger."""
    if isinstance(seal_or_sealed, SealedProtocol):
        return seal_or_sealed.seal in _FREEZE_LEDGER
    if isinstance(seal_or_sealed, str):
        return seal_or_sealed in _FREEZE_LEDGER
    return False


#: The fields whose change after freezing makes it a different protocol
#: wearing the old seal. In practice every field is load-bearing, but the
#: version and steps are the ones an edit most often touches.
LOADBEARING_FIELDS = ("version", "steps", "stop_conditions",
                      "analysis_plan", "claim_cap")


def refuse_edit_after_seal(sealed: SealedProtocol,
                           proposed: Protocol) -> dict:
    """Refuse to present an edited protocol as the frozen one.

    The protocol is frozen, and its seal published. If someone edits a
    setpoint, a stop condition, or the step list and re-presents the plan
    as the sealed one, the edit is detectable: the proposed protocol hashes
    differently. The edit is legal *as a new version* -- it simply gets a
    new seal -- and forbidden as a silent replacement of the old. This
    raises when the proposed plan differs from the sealed one."""
    if not isinstance(sealed, SealedProtocol):
        raise ProtocolError("first argument must be a SealedProtocol")
    if not isinstance(proposed, Protocol):
        raise ProtocolError("second argument must be a Protocol")
    proposed_hash = compile_hash(proposed)
    if proposed_hash != sealed.seal:
        raise ProtocolError(
            f"refused: this protocol differs from the frozen one and may "
            f"not be presented as it. The frozen seal is {sealed.seal}; the "
            f"proposed plan hashes to {proposed_hash}. A protocol edited "
            f"after freezing is a new version and must be frozen afresh "
            f"under its own seal, not run under the previous commitment.")
    return {
        "seal": sealed.seal,
        "proposed_hash": proposed_hash,
        "identical": True,
    }


def refuse_prediction_as_measurement(*_a, **_k) -> None:
    """A protocol's predicted signature is not a measured outcome.

    A protocol says what *would* be observed if the hypothesis holds.
    Compiling and freezing it commits the plan; it does not run the study,
    and it certainly does not measure anything. The strongest a frozen
    plan establishes is that the plan existed, in full, before the run."""
    raise ProtocolError(
        "refused: a frozen protocol is a plan, not a result. Its hypotheses "
        "and predicted signatures are commitments about what a run would "
        "show; freezing hashes the plan and does not operate any apparatus. "
        "No measurement is produced by compiling or sealing a protocol.")


# =======================================================================
# A worked example protocol
# =======================================================================

def _example_protocol() -> Protocol:
    """A complete, well-formed protocol for the baseline modal survey.

    Its hypothesis is taken from the R13 experiment registry (reusing that
    authority rather than restating it) and its ``preregistration_hash`` is
    the seal of the R13 worked preregistration, so the example demonstrates
    the binding to both R13 authorities."""
    survey = r13_experiments.get_experiment(
        r13_experiments.ExperimentId.P25_BASELINE_MODAL_SURVEY)
    steps = (
        ProtocolStep(0, StepKind.ARM, capability="SIGNAL_SOURCE",
                     description="arm the drive at safe defaults"),
        ProtocolStep(1, StepKind.BIND_CALIBRATION, capability="CALIBRATION",
                     description="bind the frequency reference"),
        ProtocolStep(2, StepKind.BIND_SPECIMEN, capability="SPECIMEN_MOUNT",
                     description="bind the specimen under test"),
        ProtocolStep(3, StepKind.BIND_FIXTURE, capability="FIXTURE",
                     description="bind the mounting fixture"),
        ProtocolStep(
            4, StepKind.ACQUIRE, capability="SPECTRUM_ANALYZER",
            maneuver=Maneuver.SWEEP, requires_calibration=True,
            setpoints=(
                Setpoint("f_start", 1.0e6, "Hz", 1.0e3),
                Setpoint("f_stop", 5.0e6, "Hz", 1.0e3),
                Setpoint("points", 4096.0, "count", 0.0),
            ),
            description="swept-sine survey of the low-order modes"),
        ProtocolStep(
            5, StepKind.ACQUIRE, capability="SPECTRUM_ANALYZER",
            maneuver=Maneuver.SHAM, requires_calibration=True,
            setpoints=(Setpoint("drive", 0.0, "V", 0.0),),
            description="sham: drive nominally off, same acquisition"),
        ProtocolStep(6, StepKind.RECORD, capability="DATALOGGER",
                     description="record raw artifacts and metadata"),
    )
    stop_conditions = (
        StopCondition("max_acquisitions", StopKind.MAX_ACQUISITIONS, 2.0,
                      "stop after the survey and its sham"),
        StopCondition("fault", StopKind.FAULT_DETECTED, 1.0,
                      "abort on any injected or observed fault"),
    )
    return Protocol(
        protocol_id="R15_P07_BASELINE_MODAL_SURVEY",
        version="1.0.0",
        hypotheses=(survey.hypothesis,),
        controls=("sham (drive off)", "shuffled-frequency null"),
        randomization={"order": "fixed", "seed_field": "config.seed"},
        blinding={"labels": "condition codes masked at analysis"},
        steps=steps,
        stop_conditions=stop_conditions,
        analysis_plan={
            "null_model": survey.null_model,
            "decision_rule": survey.decision_rule,
            "estimator": "Lorentzian fit to resolved peaks",
        },
        claim_cap=r15_claims.ClaimClass.SYNTHETIC_OBSERVATION.value,
        preregistration_hash=r13_preregister.example_seal(),
    )


#: The worked example protocol, built once.
EXAMPLE_PROTOCOL: Protocol = _example_protocol()


def example_seal(*, epoch: int = 20260724) -> SealedProtocol:
    """Freeze the worked example and return the sealed protocol."""
    return freeze(EXAMPLE_PROTOCOL, epoch=epoch)


# =======================================================================
# The report
# =======================================================================

def protocols_report() -> dict:
    sealed = example_seal()
    return {
        "what_this_is": (
            "an executable protocol engine: a typed, ordered plan of "
            "authorized steps (arm, bind calibration/specimen/fixture, "
            "acquire, record) with setpoints, tolerances, controls, stop "
            "conditions, an analysis plan and a claim cap, frozen under a "
            "deterministic hash before any run"),
        "step_kinds": [k.value for k in StepKind],
        "maneuvers": [m.value for m in Maneuver],
        "stop_kinds": [k.value for k in StopKind],
        "example_protocol_id": EXAMPLE_PROTOCOL.protocol_id,
        "example_version": EXAMPLE_PROTOCOL.version,
        "example_required_capabilities":
            list(EXAMPLE_PROTOCOL.required_capabilities()),
        "example_seal": sealed.seal,
        "seal_is_deterministic": sealed.seal == compile_hash(EXAMPLE_PROTOCOL),
        "seal_verifies": sealed.verify(),
        "example_claim_cap": EXAMPLE_PROTOCOL.claim_cap,
        "bound_to_r13_preregistration":
            EXAMPLE_PROTOCOL.preregistration_hash,
        "refusals": [
            "refuse_edit_after_seal",
            "refuse_prediction_as_measurement",
        ],
        "claim_class": MODULE_CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not run the protocol, operate any apparatus, or measure "
            "anything. Freezing hashes the plan so a later edit is "
            "detectable; it is a statement about the ORDER in which the plan "
            "and any future data were fixed, nothing more. The claim cap is "
            "held at a software-reachable class because executing this plan "
            "in this environment produces at most a SYNTHETIC_OBSERVATION, "
            "never a physical measurement."),
    }
