"""P10 — the immutable, append-only measurement ledger: the evidence engine.

Every run, raw artifact, derivation, observation, and receipt is appended
to a single hash-chained ledger and never edited in place. The ledger is
built directly on the R13 provenance layer (:mod:`r13.serialize`): each
entry becomes a :class:`~r13.serialize.Record` whose hash is taken over its
payload, its claim class, a PASSED-IN epoch, and the hash of the record
before it. Editing any past entry changes that record's recomputed hash and
breaks the back-link of every entry after it, so a single tampered row fails
:func:`~r13.serialize.verify_chain` from that point onward -- the ledger is
tamper-evident, not merely tamper-resistant.

Raw artifacts are **content-addressed**. An :class:`Artifact` carries the
SHA-256 of its exact bytes, so the manifest *is* the fingerprint: the same
bytes always address the same way, and a single changed byte changes the
address. Large files that live outside the ledger are carried as an
:class:`ExternalArtifactPointer` -- a URI plus the declared content hash and
byte count -- and :meth:`ExternalArtifactPointer.verify` re-hashes the
fetched bytes so an external store is trusted only through a verified hash,
never on faith.

Artifacts are typed by stage -- ``RAW``, ``CALIBRATED``, ``FILTERED``,
``FITTED``, ``INTERPRETED`` -- and every non-raw stage is produced by a
:class:`Derivation` that records the exact source artifact ids, the software
name and version, and the parameters used. A fit therefore links back to the
precise bytes it consumed and the precise code that produced it.

The ledger binds an observation to the R15 evidence bindings -- instrument,
calibration, specimen, fixture, protocol, clock, environment, raw artifact,
uncertainty. An observation missing any binding is **capped below a physical
measurement** by :mod:`r15.claims`: a requested measurement class collapses
to the software ceiling and the evidence level cannot reach E4. No clock is
ever read; every epoch is passed in. Nothing here is measured -- the ledger
records provenance and integrity, and a matching hash proves the bytes, not
the physics.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13 import serialize
from r15 import claims

#: The standing verdict for this module.
VERDICT = "IMMUTABLE_MEASUREMENT_LEDGER_APPEND_ONLY_HASH_CHAINED"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"


class LedgerError(RuntimeError):
    """Raised on a malformed entry, a broken binding contract, a failed
    external-pointer verification, or an attempt to stamp with a live
    clock."""


class ArtifactKind(Enum):
    """The stage of a measurement artifact. RAW is the immutable acquisition
    output; every later stage must be produced by a recorded derivation."""

    RAW = "RAW"
    CALIBRATED = "CALIBRATED"
    FILTERED = "FILTERED"
    FITTED = "FITTED"
    INTERPRETED = "INTERPRETED"


class AcquisitionMode(Enum):
    """How an artifact was acquired. The four lanes are kept distinct so a
    synthetic or replayed byte-stream can never be mistaken for a real one."""

    REAL = "REAL"
    REPLAY = "REPLAY"
    SYNTHETIC = "SYNTHETIC"
    FAULT_INJECTION = "FAULT_INJECTION"


class LedgerEntryKind(Enum):
    """What a ledger record is about."""

    RUN = "RUN"
    ARTIFACT = "ARTIFACT"
    EXTERNAL_ARTIFACT = "EXTERNAL_ARTIFACT"
    DERIVATION = "DERIVATION"
    OBSERVATION = "OBSERVATION"
    RECEIPT = "RECEIPT"


# --- content addressing -------------------------------------------------

def sha256_hex(data: bytes) -> str:
    """SHA-256 of raw bytes, as hex -- the content address of an artifact."""
    if not isinstance(data, (bytes, bytearray, memoryview)):
        raise LedgerError("content addressing requires raw bytes")
    return hashlib.sha256(bytes(data)).hexdigest()


def array_bytes(arr: np.ndarray) -> bytes:
    """Canonical bytes for a numeric raw artifact.

    A contiguous copy with an explicit dtype and shape gives a stable,
    reproducible byte string for content addressing, independent of the
    array's incidental memory layout.
    """
    a = np.ascontiguousarray(arr)
    header = f"{a.dtype.str}|{a.shape}|".encode(serialize.ENCODING)
    return header + a.tobytes(order="C")


# --- artifacts ----------------------------------------------------------

@dataclass(frozen=True)
class Artifact:
    """A content-addressed, immutable measurement artifact.

    ``content_hash`` is the SHA-256 of the exact bytes, so the manifest is
    the fingerprint. The dataclass is frozen: an artifact cannot be mutated
    in place, and any different content produces a different address.
    """

    artifact_id: str
    run_id: str
    kind: ArtifactKind
    media_type: str
    content_hash: str
    bytes: int
    instrument_id: str
    calibration_id: str
    mode: AcquisitionMode = AcquisitionMode.SYNTHETIC
    immutable: bool = True

    def __post_init__(self) -> None:
        if not self.immutable:
            raise LedgerError("a ledger artifact is immutable by construction")
        if self.bytes < 0:
            raise LedgerError("artifact byte count cannot be negative")

    @classmethod
    def from_bytes(cls, artifact_id: str, run_id: str, kind: ArtifactKind,
                   media_type: str, data: bytes, instrument_id: str,
                   calibration_id: str,
                   mode: AcquisitionMode = AcquisitionMode.SYNTHETIC
                   ) -> "Artifact":
        """Build an artifact by content-addressing ``data``."""
        raw = bytes(data)
        return cls(
            artifact_id=artifact_id,
            run_id=run_id,
            kind=kind,
            media_type=media_type,
            content_hash=sha256_hex(raw),
            bytes=len(raw),
            instrument_id=instrument_id,
            calibration_id=calibration_id,
            mode=mode,
        )

    def verify(self, data: bytes) -> bool:
        """True iff ``data`` hashes to this artifact's content address."""
        return sha256_hex(bytes(data)) == self.content_hash

    def to_manifest(self) -> dict:
        """A manifest conforming to ``measurement_artifact.schema.json``."""
        return {
            "artifact_id": self.artifact_id,
            "run_id": self.run_id,
            "kind": self.kind.value,
            "media_type": self.media_type,
            "hash": self.content_hash,
            "bytes": self.bytes,
            "instrument_id": self.instrument_id,
            "calibration_id": self.calibration_id,
            "mode": self.mode.value,
            "immutable": True,
        }


@dataclass(frozen=True)
class ExternalArtifactPointer:
    """A verified pointer to a large file held outside the ledger.

    The bytes are not stored; the pointer carries their declared SHA-256 and
    size. :meth:`verify` re-hashes fetched bytes, so an external store is
    trusted only through a matching hash.
    """

    artifact_id: str
    run_id: str
    kind: ArtifactKind
    media_type: str
    uri: str
    content_hash: str
    bytes: int
    instrument_id: str
    calibration_id: str
    mode: AcquisitionMode = AcquisitionMode.SYNTHETIC

    def verify(self, data: bytes) -> bool:
        """True iff fetched ``data`` matches the declared hash and size."""
        raw = bytes(data)
        return len(raw) == self.bytes and sha256_hex(raw) == self.content_hash

    def to_manifest(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "run_id": self.run_id,
            "kind": self.kind.value,
            "media_type": self.media_type,
            "uri": self.uri,
            "hash": self.content_hash,
            "bytes": self.bytes,
            "instrument_id": self.instrument_id,
            "calibration_id": self.calibration_id,
            "mode": self.mode.value,
            "external": True,
            "immutable": True,
        }


@dataclass(frozen=True)
class Derivation:
    """The record of how a non-raw artifact was produced.

    It links the output to the exact source artifact ids, the software name
    and version, and the parameters used, so a fit or filter is reproducible
    from named bytes and named code.
    """

    output_artifact_id: str
    input_artifact_ids: tuple[str, ...]
    software: str
    software_version: str
    parameters: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.input_artifact_ids:
            raise LedgerError(
                "a derivation must name at least one source artifact")
        if not self.software or not self.software_version:
            raise LedgerError(
                "a derivation must record software name and version")

    def to_manifest(self) -> dict:
        return {
            "output_artifact_id": self.output_artifact_id,
            "input_artifact_ids": list(self.input_artifact_ids),
            "software": self.software,
            "software_version": self.software_version,
            "parameters": self.parameters,
        }


# --- binding-driven claim capping --------------------------------------

def cap_class_for_bindings(requested: claims.ClaimClass,
                           bindings: claims.EvidenceBindings
                           ) -> claims.ClaimClass:
    """Cap a requested claim class by the available evidence bindings.

    Without every physical binding, a requested measurement class collapses
    to the software ceiling (``MODEL_PREDICTION``): the ledger refuses to
    label an unbound entry as a physical measurement.
    """
    if not bindings.complete_for_physical():
        return claims.cap_claim_to_software(requested)
    return requested


# --- the ledger ---------------------------------------------------------

@dataclass(frozen=True)
class LedgerEntry:
    """One appended entry: its kind, the record that carries it, and (for an
    observation) the class and evidence level actually granted after capping."""

    entry_kind: LedgerEntryKind
    record: serialize.Record
    granted_class: str | None = None
    granted_evidence: str | None = None


class MeasurementLedger:
    """An append-only, hash-chained ledger of measurement provenance.

    Backed by the R13 record chain: :meth:`verify` recomputes every hash and
    back-link, so mutating any past entry breaks verification downstream.
    Never edits a stored entry and never reads a clock -- epochs are passed
    in.
    """

    def __init__(self) -> None:
        self._records: tuple[serialize.Record, ...] = ()
        self._entries: tuple[LedgerEntry, ...] = ()

    def __len__(self) -> int:
        return len(self._records)

    @property
    def records(self) -> tuple[serialize.Record, ...]:
        return self._records

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        return self._entries

    def tip_hash(self) -> str:
        """The hash of the last record, or the genesis link if empty."""
        if not self._records:
            return serialize.GENESIS_PREV_HASH
        return self._records[-1].record_hash

    def _append(self, kind: LedgerEntryKind, body: dict, epoch,
                claim_class: str, *, granted_class: str | None = None,
                granted_evidence: str | None = None) -> LedgerEntry:
        if epoch is None:
            raise LedgerError(
                "an epoch must be passed in; the ledger never reads a clock")
        payload = {"entry_kind": kind.value, "body": body}
        self._records = serialize.append_record(
            self._records, payload, epoch, claim_class)
        entry = LedgerEntry(
            entry_kind=kind,
            record=self._records[-1],
            granted_class=granted_class,
            granted_evidence=granted_evidence,
        )
        self._entries = self._entries + (entry,)
        return entry

    def append_run(self, run_id: str, mode: AcquisitionMode, protocol_id: str,
                   epoch) -> LedgerEntry:
        """Open a run in the ledger."""
        body = {"run_id": run_id, "mode": mode.value,
                "protocol_id": protocol_id}
        return self._append(LedgerEntryKind.RUN, body, epoch,
                            claims.ClaimClass.SOFTWARE_IMPLEMENTED.value)

    def append_artifact(self, artifact: Artifact, epoch) -> LedgerEntry:
        """Append a content-addressed artifact manifest."""
        return self._append(LedgerEntryKind.ARTIFACT, artifact.to_manifest(),
                            epoch,
                            claims.ClaimClass.SYNTHETIC_FIXTURE.value)

    def append_external_artifact(self, pointer: ExternalArtifactPointer,
                                 epoch) -> LedgerEntry:
        """Append a hash-verified external artifact pointer."""
        return self._append(LedgerEntryKind.EXTERNAL_ARTIFACT,
                            pointer.to_manifest(), epoch,
                            claims.ClaimClass.SYNTHETIC_FIXTURE.value)

    def append_derivation(self, derivation: Derivation, epoch) -> LedgerEntry:
        """Append a derivation linking an output to its exact sources/code."""
        return self._append(LedgerEntryKind.DERIVATION,
                            derivation.to_manifest(), epoch,
                            claims.ClaimClass.SOFTWARE_IMPLEMENTED.value)

    def append_observation(self, observation_id: str, run_id: str,
                           source_artifacts: tuple[str, ...],
                           analysis_version: str, quantity: str, value,
                           units: str, uncertainty: dict,
                           bindings: claims.EvidenceBindings,
                           requested_class: claims.ClaimClass,
                           requested_evidence: claims.EvidenceLevel,
                           epoch) -> LedgerEntry:
        """Append an observation, capped by its evidence bindings.

        A missing binding caps the class below a physical measurement and the
        evidence level below E4. The capped values are what enter the record,
        so the chain itself never carries an over-claim.
        """
        granted_class = cap_class_for_bindings(requested_class, bindings)
        granted_evidence = claims.evidence_cap(bindings, requested_evidence)
        body = {
            "observation_id": observation_id,
            "run_id": run_id,
            "source_artifacts": list(source_artifacts),
            "analysis_version": analysis_version,
            "quantity": quantity,
            "value": value,
            "units": units,
            "uncertainty": uncertainty,
            "claim_class": granted_class.value,
            "evidence_level": granted_evidence.name,
            "bindings_complete": bindings.complete_for_physical(),
            "missing_bindings": bindings.missing(),
        }
        return self._append(LedgerEntryKind.OBSERVATION, body, epoch,
                            granted_class.value,
                            granted_class=granted_class.value,
                            granted_evidence=granted_evidence.name)

    def append_receipt(self, receipt: dict, epoch) -> LedgerEntry:
        """Append a terminal receipt for a run."""
        return self._append(LedgerEntryKind.RECEIPT, receipt, epoch,
                            claims.ClaimClass.SOFTWARE_IMPLEMENTED.value)

    def verify(self) -> bool:
        """Recompute every hash and back-link; False if any entry tampered."""
        if not self._records:
            return True
        return serialize.verify_chain(self._records)

    def verify_report(self) -> dict:
        """Per-record integrity breakdown."""
        if not self._records:
            return {"verified": True, "length": 0, "records": []}
        return serialize.verify_chain_report(self._records)


# --- report -------------------------------------------------------------

def measurement_ledger_report() -> dict:
    """The standing result: a worked, deterministic ledger over passed-in
    epochs, demonstrating content addressing, derivation linkage, tamper
    detection, external hash verification, and binding-driven capping."""
    ledger = MeasurementLedger()
    ledger.append_run("run-0001", AcquisitionMode.SYNTHETIC, "protocol-freeze-1",
                      epoch=1000)

    # A raw, content-addressed numeric artifact.
    rng = np.random.default_rng(0)
    raw = array_bytes(rng.standard_normal(64))
    raw_art = Artifact.from_bytes(
        "art-raw-1", "run-0001", ArtifactKind.RAW, "application/octet-stream",
        raw, "instr-A", "cal-A", AcquisitionMode.SYNTHETIC)
    ledger.append_artifact(raw_art, epoch=1001)

    # A fitted artifact derived from the raw one, with software + params.
    fit = Artifact.from_bytes(
        "art-fit-1", "run-0001", ArtifactKind.FITTED, "application/json",
        b'{"amplitude": 1.0}', "instr-A", "cal-A")
    ledger.append_artifact(fit, epoch=1002)
    deriv = Derivation(
        output_artifact_id="art-fit-1",
        input_artifact_ids=("art-raw-1",),
        software="rgcs.fit", software_version="1.2.3",
        parameters={"model": "lorentzian", "max_iter": 200})
    ledger.append_derivation(deriv, epoch=1003)

    # An observation with INCOMPLETE bindings -> capped below physical.
    partial = claims.EvidenceBindings(instrument=True, calibration=True)
    obs = ledger.append_observation(
        "obs-1", "run-0001", ("art-fit-1",), "analysis-1",
        "resonance_frequency", 32768.0, "Hz",
        {"type": "combined", "value": 0.5},
        partial, claims.ClaimClass.PHYSICAL_MEASUREMENT,
        claims.EvidenceLevel.E4, epoch=1004)

    # An external large-file pointer, hash-verified.
    payload = b"x" * 4096
    ptr = ExternalArtifactPointer(
        "art-ext-1", "run-0001", ArtifactKind.RAW, "application/octet-stream",
        "file:///store/art-ext-1.bin", sha256_hex(payload), len(payload),
        "instr-A", "cal-A")

    verified_before = ledger.verify()

    # Tamper demonstration on a detached copy: editing a past record breaks
    # verification downstream. The live ledger above is never mutated.
    good = ledger.records
    tampered = list(good)
    victim = tampered[1]
    tampered[1] = serialize.Record(
        payload={"entry_kind": "ARTIFACT", "body": {"tampered": True}},
        claim_class=victim.claim_class, epoch=victim.epoch,
        prev_hash=victim.prev_hash, record_hash=victim.record_hash)
    tamper_detected = not serialize.verify_chain(tuple(tampered))

    return {
        "what_this_is": (
            "an append-only, hash-chained measurement ledger. Runs, "
            "content-addressed artifacts, derivations, observations, and "
            "receipts are appended and never edited; mutating any past entry "
            "breaks verification downstream. Raw artifacts are addressed by "
            "SHA-256, external files are trusted only through a verified "
            "hash, and an observation missing evidence bindings is capped "
            "below a physical measurement"),
        "claim_class": claims.ClaimClass.SOFTWARE_IMPLEMENTED.value,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "ledger_length": len(ledger),
        "chain_verifies": verified_before,
        "tamper_detected": tamper_detected,
        "raw_artifact_address": raw_art.content_hash,
        "raw_artifact_reverifies": raw_art.verify(raw),
        "external_pointer_verifies": ptr.verify(payload),
        "external_pointer_rejects_wrong_bytes": not ptr.verify(payload + b"!"),
        "fit_links_source": deriv.input_artifact_ids,
        "fit_software": f"{deriv.software}@{deriv.software_version}",
        "observation_requested_class": "PHYSICAL_MEASUREMENT",
        "observation_granted_class": obs.granted_class,
        "observation_granted_evidence": obs.granted_evidence,
        "observation_capped_below_physical":
            obs.granted_class != "PHYSICAL_MEASUREMENT",
        "epochs_passed_in_never_wallclock": True,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It measures nothing. A matching content hash proves the bytes "
            "are unaltered (integrity), not who produced them and not that "
            "any physics occurred. A complete set of bindings here is over "
            "synthetic fixtures, so no entry is promoted to a physical "
            "measurement; the capping only ever removes over-claims, it "
            "never grants one."),
    }


__all__ = [
    "VERDICT", "PHYSICAL_VALIDATION", "LedgerError",
    "ArtifactKind", "AcquisitionMode", "LedgerEntryKind",
    "sha256_hex", "array_bytes",
    "Artifact", "ExternalArtifactPointer", "Derivation",
    "cap_class_for_bindings", "LedgerEntry", "MeasurementLedger",
    "measurement_ledger_report",
]
