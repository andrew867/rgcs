"""P02 — the measurement-provenance authority.

Every observation this platform emits must be bound to the evidence and
the conditions that produced it. This module builds that binding. An
:class:`ObservationRecord` carries, for a single reported quantity: the
instrument, the calibration, the specimen, the fixture, the protocol, the
clock, and the environment it came from; the passed-in start and end
timestamps; an uncertainty budget; the immutable raw artifacts it was
derived from (by content hash); and a :class:`DerivationGraph` -- the
lineage from raw bytes through each analysis step to the reported value.

Three properties make the record trustworthy.

**Lineage is hashed.** The record's :attr:`lineage_hash` is a canonical
hash over the source artifacts' content hashes and every derivation step.
Tamper with any source artifact -- change a single byte -- and its content
hash changes, so the recomputed lineage hash no longer matches and
:func:`verify_lineage` returns False. Derived data cannot be silently
re-based onto different evidence.

**Derived data require their sources.** :func:`build_observation` refuses
to record an observation with no source artifacts. A value with no
traceable raw evidence is not an observation; it is an assertion.

**Bindings cap the claim.** The evidence an observation can support is
capped by what it binds, through :func:`r15.claims.evidence_cap` and
:class:`~r15.claims.EvidenceBindings`. Missing calibration, a clock, a raw
artifact, or any other required binding caps the evidence below a physical
measurement (E4), no matter how clean the number is. And because every
artifact here is software-produced, an observation is never a
``PHYSICAL_MEASUREMENT``: the honest ceiling is ``SYNTHETIC_OBSERVATION``.

Timestamps and epochs are always PASSED IN, never read from a clock, so a
record serialises identically on every run and its lineage hash is
reproducible. Nothing here is measured.
"""

from __future__ import annotations

from dataclasses import dataclass

from r13 import serialize as S
from r15 import claims as C
from r15.artifacts import AcquisitionMode, MeasurementArtifact


#: The standing verdict for this module.
VERDICT = "OBSERVATIONS_PROVENANCE_BOUND_LINEAGE_HASHED_NO_PHYSICAL_CLAIM"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The analysis version stamped on records built by this module. A change
#: to analysis behaviour must bump this so lineage stays honest about which
#: code produced a value.
ANALYSIS_VERSION = "r15.provenance/1"


class ProvenanceError(RuntimeError):
    """Raised on a missing source artifact, a missing binding presented as
    physical, a malformed derivation step, or an attempt to promote a
    synthetic observation to a physical measurement."""


@dataclass(frozen=True)
class DerivationStep:
    """One node in the lineage from raw artifacts to a reported value.

    ``inputs`` are the content hashes (of source artifacts or of upstream
    steps) this step consumes; ``output_hash`` is the canonical content
    hash of its output. ``operation`` names what it did (e.g. ``detrend``,
    ``fft``, ``peak_fit``). The step is itself hashable and immutable.
    """

    step_id: str
    operation: str
    inputs: tuple[str, ...]
    output_hash: str
    analysis_version: str = ANALYSIS_VERSION

    def __post_init__(self) -> None:
        if not str(self.step_id).strip() or not str(self.operation).strip():
            raise ProvenanceError("a derivation step needs a step_id and an "
                                  "operation")
        if not self.inputs:
            raise ProvenanceError(
                f"derivation step {self.step_id!r} has no inputs; a derived "
                f"value must consume at least one upstream hash")
        object.__setattr__(self, "inputs", tuple(self.inputs))

    def as_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "operation": self.operation,
            "inputs": list(self.inputs),
            "output_hash": self.output_hash,
            "analysis_version": self.analysis_version,
        }


@dataclass(frozen=True)
class DerivationGraph:
    """The ordered lineage from source artifacts to the reported value.

    ``source_hashes`` are the content hashes of the immutable raw
    artifacts at the root; ``steps`` are the analysis nodes in dependency
    order. The graph is canonically serialisable, so its hash is stable and
    changes if any source hash or any step changes.
    """

    source_hashes: tuple[str, ...]
    steps: tuple[DerivationStep, ...]

    def __post_init__(self) -> None:
        if not self.source_hashes:
            raise ProvenanceError(
                "a derivation graph must root in at least one source "
                "artifact hash")
        object.__setattr__(self, "source_hashes", tuple(self.source_hashes))
        object.__setattr__(self, "steps", tuple(self.steps))

    def as_list(self) -> list[dict]:
        """The derivation graph as a JSON-ready list, roots first."""
        rows: list[dict] = [
            {"node": "source_artifact", "hash": h} for h in self.source_hashes
        ]
        rows.extend(s.as_dict() for s in self.steps)
        return rows

    def structure(self) -> dict:
        """The canonical structure the lineage hash is taken over."""
        return {
            "source_hashes": list(self.source_hashes),
            "steps": [s.as_dict() for s in self.steps],
        }


def make_linear_graph(artifacts: tuple[MeasurementArtifact, ...],
                      operations: tuple[str, ...]) -> DerivationGraph:
    """Build a straight-line derivation graph over ``artifacts``.

    Each operation consumes the previous node's hash (the merged source
    hashes for the first) and produces a canonical output hash. Purely
    structural: it records lineage, it does not compute physics.
    """
    if not artifacts:
        raise ProvenanceError("a derivation graph needs source artifacts")
    source_hashes = tuple(a.content_hash for a in artifacts)
    steps: list[DerivationStep] = []
    prev_inputs: tuple[str, ...] = source_hashes
    for i, op in enumerate(operations):
        out = S.content_hash({"op": op, "index": i, "inputs": list(prev_inputs)})
        step = DerivationStep(
            step_id=f"STEP_{i:02d}_{op}",
            operation=op,
            inputs=prev_inputs,
            output_hash=out,
        )
        steps.append(step)
        prev_inputs = (out,)
    return DerivationGraph(source_hashes=source_hashes, steps=tuple(steps))


def compute_lineage_hash(graph: DerivationGraph, *, quantity: str,
                         value, units: str) -> str:
    """Canonical hash binding a reported value to its full lineage.

    Taken over the derivation graph structure (which includes every source
    artifact's content hash) plus the reported quantity, value, and units.
    A one-byte change to any source artifact changes its content hash,
    hence the graph structure, hence this hash.
    """
    return S.content_hash({
        "graph": graph.structure(),
        "quantity": quantity,
        "value": value,
        "units": units,
    })


def _bindings_from(*, instrument_id, calibration_id, specimen_id, fixture_id,
                   protocol_id, environment_id, clock, uncertainty,
                   has_raw_artifact: bool) -> C.EvidenceBindings:
    """Assemble the R15 evidence bindings from what is actually present."""
    return C.EvidenceBindings(
        instrument=bool(instrument_id),
        calibration=bool(calibration_id),
        specimen=bool(specimen_id),
        fixture=bool(fixture_id),
        protocol=bool(protocol_id),
        clock=bool(clock),
        environment=bool(environment_id),
        raw_artifact=has_raw_artifact,
        uncertainty=bool(uncertainty),
    )


def classify_observation(mode: AcquisitionMode,
                         bindings: C.EvidenceBindings
                         ) -> tuple[C.ClaimClass, C.EvidenceLevel]:
    """Classify an observation by its acquisition mode and its bindings.

    The rules, in order:

    * If any required binding is missing, the observation cannot be a
      physical measurement: the evidence is capped below E4 by
      :func:`r15.claims.evidence_cap`, and the class drops to the software
      ceiling. This holds regardless of mode.
    * A ``REAL`` acquisition with every binding present would support a
      ``PHYSICAL_MEASUREMENT`` at E4 -- but no ``REAL`` device exists here,
      so this branch is never reached by any record this module builds.
    * Otherwise (a software-mode acquisition with complete bindings) the
      honest class is ``SYNTHETIC_OBSERVATION`` at E2 -- a deterministic
      synthetic observation, never a physical one.
    """
    complete = bindings.complete_for_physical()
    if not complete:
        # Missing binding: capped below physical measurement.
        ev = C.evidence_cap(bindings, C.EvidenceLevel.E4)
        if mode in (AcquisitionMode.SYNTHETIC, AcquisitionMode.REPLAY,
                    AcquisitionMode.FAULT_INJECTION):
            return C.ClaimClass.SYNTHETIC_OBSERVATION, ev
        # A REAL-but-unbound reading collapses to the software ceiling: it
        # is not trustworthy as a physical measurement.
        return C.cap_claim_to_software(C.ClaimClass.PHYSICAL_MEASUREMENT), ev
    if mode is AcquisitionMode.REAL:
        return C.ClaimClass.PHYSICAL_MEASUREMENT, C.EvidenceLevel.E4
    return C.ClaimClass.SYNTHETIC_OBSERVATION, C.EvidenceLevel.E2


@dataclass(frozen=True)
class ObservationRecord:
    """A single reported quantity bound to its provenance.

    Carries the instrument / calibration / specimen / fixture / protocol /
    environment bindings, the clock (passed-in start/end epochs), the
    uncertainty budget, the immutable source artifacts (by content hash),
    the derivation graph, and the resulting claim class and evidence level.
    Frozen and canonically serialisable; the lineage hash is reproducible.
    """

    observation_id: str
    run_id: str
    quantity: str
    value: object
    units: str
    uncertainty: dict
    source_artifact_hashes: tuple[str, ...]
    graph: DerivationGraph
    bindings: C.EvidenceBindings
    claim_class: C.ClaimClass
    evidence: C.EvidenceLevel
    lineage_hash: str
    analysis_version: str = ANALYSIS_VERSION
    instrument_id: str | None = None
    calibration_id: str | None = None
    specimen_id: str | None = None
    fixture_id: str | None = None
    protocol_id: str | None = None
    environment_id: str | None = None
    clock: dict | None = None

    @property
    def is_physical(self) -> bool:
        return self.claim_class in C.MEASUREMENT_CLASSES

    @property
    def missing_bindings(self) -> list[str]:
        return self.bindings.missing()

    def to_record(self) -> dict:
        """A record conforming to ``observation_record.schema.json``."""
        return {
            "observation_id": self.observation_id,
            "run_id": self.run_id,
            "source_artifacts": list(self.source_artifact_hashes),
            "analysis_version": self.analysis_version,
            "quantity": self.quantity,
            "value": self.value,
            "units": self.units,
            "uncertainty": dict(self.uncertainty),
            "claim_class": self.claim_class.value,
            "derivation_graph": self.graph.as_list(),
        }

    def provenance(self) -> dict:
        """The full binding set, for audit. Not part of the schema record."""
        return {
            "instrument_id": self.instrument_id,
            "calibration_id": self.calibration_id,
            "specimen_id": self.specimen_id,
            "fixture_id": self.fixture_id,
            "protocol_id": self.protocol_id,
            "environment_id": self.environment_id,
            "clock": dict(self.clock) if self.clock else None,
            "evidence_level": self.evidence.name,
            "missing_bindings": self.missing_bindings,
            "lineage_hash": self.lineage_hash,
        }


def build_observation(*, observation_id: str, run_id: str, quantity: str,
                      value, units: str, uncertainty: dict,
                      artifacts: tuple[MeasurementArtifact, ...],
                      operations: tuple[str, ...] = ("detrend", "reduce"),
                      instrument_id: str | None = None,
                      calibration_id: str | None = None,
                      specimen_id: str | None = None,
                      fixture_id: str | None = None,
                      protocol_id: str | None = None,
                      environment_id: str | None = None,
                      start_epoch: int | None = None,
                      end_epoch: int | None = None,
                      ) -> ObservationRecord:
    """Build an observation record bound to its raw artifacts and lineage.

    ``start_epoch`` / ``end_epoch`` are PASSED IN (never read from a clock);
    together they form the clock binding. The derivation graph is built
    over ``artifacts`` and the lineage hash is taken over it. The claim
    class and evidence level follow from the acquisition mode and the
    bindings actually present -- a missing binding caps the result below a
    physical measurement.

    Refuses an observation with no source artifacts: derived data require
    the evidence they came from.
    """
    if not artifacts:
        raise ProvenanceError(
            "refused: an observation with no source artifacts is an "
            "assertion, not a measurement. Derived data must name the "
            "immutable raw artifacts they were derived from.")

    # The clock is a passed-in pair of epochs; nothing reads a wall clock.
    clock: dict | None = None
    if start_epoch is not None and end_epoch is not None:
        S.refuse_wallclock_timestamp(start_epoch, reads_clock=False)
        S.refuse_wallclock_timestamp(end_epoch, reads_clock=False)
        clock = {"start_epoch": start_epoch, "end_epoch": end_epoch}

    # Every source artifact here is software-produced; the acquisition mode
    # for the observation is the strongest (least software) of its sources,
    # which in this environment is never REAL.
    mode = _observation_mode(artifacts)

    graph = make_linear_graph(artifacts, operations)
    source_hashes = tuple(a.content_hash for a in artifacts)
    lineage_hash = compute_lineage_hash(graph, quantity=quantity,
                                        value=value, units=units)

    bindings = _bindings_from(
        instrument_id=instrument_id, calibration_id=calibration_id,
        specimen_id=specimen_id, fixture_id=fixture_id,
        protocol_id=protocol_id, environment_id=environment_id,
        clock=clock, uncertainty=uncertainty,
        has_raw_artifact=bool(artifacts))
    claim_class, evidence = classify_observation(mode, bindings)

    return ObservationRecord(
        observation_id=observation_id, run_id=run_id, quantity=quantity,
        value=value, units=units, uncertainty=dict(uncertainty),
        source_artifact_hashes=source_hashes, graph=graph,
        bindings=bindings, claim_class=claim_class, evidence=evidence,
        lineage_hash=lineage_hash, instrument_id=instrument_id,
        calibration_id=calibration_id, specimen_id=specimen_id,
        fixture_id=fixture_id, protocol_id=protocol_id,
        environment_id=environment_id, clock=clock)


def _observation_mode(artifacts: tuple[MeasurementArtifact, ...]
                      ) -> AcquisitionMode:
    """The acquisition mode an observation inherits from its sources.

    An observation is only as physical as its least-physical source. A
    single fault-injected or synthetic source keeps the whole observation
    software-mode; only all-``REAL`` sources could yield ``REAL`` (which
    does not occur here).
    """
    modes = {a.mode for a in artifacts}
    if AcquisitionMode.FAULT_INJECTION in modes:
        return AcquisitionMode.FAULT_INJECTION
    if modes == {AcquisitionMode.REAL}:
        return AcquisitionMode.REAL
    if AcquisitionMode.SYNTHETIC in modes:
        return AcquisitionMode.SYNTHETIC
    return AcquisitionMode.REPLAY


def verify_lineage(record: ObservationRecord,
                   artifacts: tuple[MeasurementArtifact, ...]) -> bool:
    """True iff ``artifacts`` still hash to the record's bound lineage.

    Recomputes the source hashes and the lineage hash from the artifacts as
    they are now and compares to the record. A tampered artifact (any byte
    changed) shifts its content hash, so the recomputed lineage hash no
    longer matches and this returns False.
    """
    current_source_hashes = tuple(a.content_hash for a in artifacts)
    if current_source_hashes != record.source_artifact_hashes:
        return False
    graph = make_linear_graph(artifacts, tuple(s.operation
                                               for s in record.graph.steps))
    recomputed = compute_lineage_hash(graph, quantity=record.quantity,
                                      value=record.value, units=record.units)
    return recomputed == record.lineage_hash


def refuse_synthetic_observation_as_physical(record: ObservationRecord
                                             ) -> None:
    """Refuse to relabel a synthetic observation as a physical measurement.

    Delegates to the governance refusal in :mod:`r15.claims`. Every
    observation this module builds is derived from software artifacts, so
    calling it a physical measurement is a forbidden promotion.
    """
    if record.claim_class not in C.MEASUREMENT_CLASSES:
        C.refuse_synthetic_as_physical()


def provenance_report() -> dict:
    """The standing result: a provenance-bound, lineage-hashed synthetic
    observation. Nothing is measured."""
    from r15.artifacts import synthetic_artifact

    a1 = synthetic_artifact(
        artifact_id="ART_PROV_01", run_id="RUN_PROV",
        instrument_id="INSTR_SYNTH", calibration_id="CAL_SELFTEST",
        seed=101, n_bytes=128)
    a2 = synthetic_artifact(
        artifact_id="ART_PROV_02", run_id="RUN_PROV",
        instrument_id="INSTR_SYNTH", calibration_id="CAL_SELFTEST",
        seed=202, n_bytes=128)

    fully_bound = build_observation(
        observation_id="OBS_FULL", run_id="RUN_PROV",
        quantity="amplitude", value=1.2345, units="V",
        uncertainty={"type": "standard", "value": 0.01, "units": "V", "k": 1},
        artifacts=(a1, a2), instrument_id="INSTR_SYNTH",
        calibration_id="CAL_SELFTEST", specimen_id="SPEC_SYNTH",
        fixture_id="FIX_SYNTH", protocol_id="PROTO_SYNTH",
        environment_id="ENV_SYNTH", start_epoch=1000, end_epoch=1001)

    unbound = build_observation(
        observation_id="OBS_NOCLOCK", run_id="RUN_PROV",
        quantity="amplitude", value=1.2345, units="V",
        uncertainty={"type": "standard", "value": 0.01, "units": "V", "k": 1},
        artifacts=(a1, a2), instrument_id="INSTR_SYNTH",
        calibration_id="CAL_SELFTEST", specimen_id="SPEC_SYNTH",
        fixture_id="FIX_SYNTH", protocol_id="PROTO_SYNTH",
        environment_id="ENV_SYNTH")  # no clock -> missing binding

    return {
        "what_this_is": (
            "a measurement-provenance authority: observation records bound "
            "to their instrument, calibration, specimen, fixture, protocol, "
            "clock, environment, timestamps, uncertainty, immutable raw "
            "artifacts, and a hashed derivation lineage"),
        "claim_class": C.ClaimClass.SYNTHETIC_OBSERVATION.value,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "analysis_version": ANALYSIS_VERSION,
        "fully_bound_claim_class": fully_bound.claim_class.value,
        "fully_bound_evidence": fully_bound.evidence.name,
        "fully_bound_is_physical": fully_bound.is_physical,
        "missing_clock_claim_class": unbound.claim_class.value,
        "missing_clock_evidence": unbound.evidence.name,
        "missing_clock_bindings": unbound.missing_bindings,
        "missing_clock_capped_below_physical":
            unbound.evidence.value < C.EvidenceLevel.E4.value,
        "lineage_verifies": verify_lineage(fully_bound, (a1, a2)),
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any observation is a physical measurement. "
            "Every source artifact is software-produced, so even a fully "
            "bound observation is a SYNTHETIC_OBSERVATION, capped below a "
            "physical measurement; a missing binding caps it further. A "
            "matching lineage hash proves the reported value was derived "
            "from exactly these unaltered bytes (integrity), never that the "
            "bytes were physically acquired. Nothing here is measured."),
    }
