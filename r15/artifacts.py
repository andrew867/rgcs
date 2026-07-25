"""P02 — immutable measurement artifacts and their content hashes.

An *artifact* is the raw, immutable evidence a measurement lane emits: a
trace, a spectrum, an image, a log. This module gives that raw evidence a
typed manifest and a content hash, so every downstream observation can be
bound back to the exact bytes it was derived from, and so a single-byte
change to those bytes is detectable.

Four laws are enforced here.

**The bytes are the artifact.** :class:`MeasurementArtifact` carries the
raw bytes themselves; its :attr:`content_hash` is the SHA-256 of exactly
those bytes. Two artifacts with identical bytes hash identically; a
one-byte change yields a different hash. That is the tamper-evidence.

**An artifact is immutable.** The record is a frozen dataclass and its
payload is an immutable ``bytes`` object, so it cannot be edited in place.
Replay and analysis operate on copies; the original evidence is never
mutated. Its manifest always carries ``immutable = True``.

**Acquisition modes stay distinct.** Every artifact declares how its bytes
came to exist -- ``REAL`` (a physical device, which does not exist in this
environment), ``REPLAY`` (bytes re-read from a prior artifact),
``SYNTHETIC`` (a deterministic simulator), or ``FAULT_INJECTION`` (a
deliberately corrupted fixture for negative tests). A ``SYNTHETIC`` or
``REPLAY`` artifact is software output; it is never a physical
measurement.

**Every artifact binds an instrument and a calibration.** The manifest
matches ``measurement_artifact.schema.json`` and requires an
``instrument_id`` and a ``calibration_id``; an artifact without them is
refused at construction.

Nothing here is measured. Every artifact this module builds is synthetic,
so the strongest claim any of them supports is a synthetic observation.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

import numpy as np

from r13 import serialize as S


#: The standing verdict for this module.
VERDICT = "MEASUREMENT_ARTIFACTS_IMMUTABLE_AND_HASHED"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"


class ArtifactError(RuntimeError):
    """Raised on a malformed artifact, a missing binding, or a mutation
    attempt on immutable evidence."""


class AcquisitionMode(Enum):
    """How an artifact's bytes came to exist. Kept strictly distinct.

    Only ``REAL`` denotes a physical device operating on a specimen, and no
    ``REAL`` device exists in this environment: everything built here is
    ``SYNTHETIC``, ``REPLAY``, or ``FAULT_INJECTION`` and is therefore
    software output, never a physical measurement.
    """

    REAL = "REAL"
    REPLAY = "REPLAY"
    SYNTHETIC = "SYNTHETIC"
    FAULT_INJECTION = "FAULT_INJECTION"


#: The modes whose bytes are produced by software, never by a device.
SOFTWARE_MODES = frozenset({
    AcquisitionMode.REPLAY,
    AcquisitionMode.SYNTHETIC,
    AcquisitionMode.FAULT_INJECTION,
})


class ArtifactKind(Enum):
    """The kind of raw evidence an artifact holds."""

    RAW_TRACE = "RAW_TRACE"
    RAW_SPECTRUM = "RAW_SPECTRUM"
    RAW_IMAGE = "RAW_IMAGE"
    RAW_TIMESERIES = "RAW_TIMESERIES"
    RAW_LOG = "RAW_LOG"


@dataclass(frozen=True)
class MeasurementArtifact:
    """One immutable raw artifact with a content hash over its own bytes.

    ``raw`` is the exact evidence; ``content_hash`` is its SHA-256.
    ``instrument_id`` and ``calibration_id`` are required bindings -- an
    artifact that cannot name the instrument that produced it and the
    calibration in force is refused. The record is frozen and ``raw`` is
    immutable, so the artifact cannot be altered after construction; the
    manifest always reports ``immutable = True``.
    """

    artifact_id: str
    run_id: str
    kind: ArtifactKind
    media_type: str
    raw: bytes
    instrument_id: str
    calibration_id: str
    mode: AcquisitionMode = AcquisitionMode.SYNTHETIC

    def __post_init__(self) -> None:
        for name in ("artifact_id", "run_id", "media_type",
                     "instrument_id", "calibration_id"):
            if not str(getattr(self, name)).strip():
                raise ArtifactError(
                    f"a measurement artifact needs a non-empty {name}")
        if not isinstance(self.kind, ArtifactKind):
            raise ArtifactError("kind must be an ArtifactKind")
        if not isinstance(self.mode, AcquisitionMode):
            raise ArtifactError("mode must be an AcquisitionMode")
        if not isinstance(self.raw, (bytes, bytearray)):
            raise ArtifactError("raw evidence must be bytes")
        if len(self.raw) == 0:
            raise ArtifactError(
                "an artifact must carry raw bytes; an empty artifact has no "
                "evidence to hash")
        # Normalise to an immutable bytes object so the payload cannot be
        # edited in place through a shared bytearray reference.
        object.__setattr__(self, "raw", bytes(self.raw))

    @property
    def content_hash(self) -> str:
        """SHA-256 of the raw bytes. Stable for identical bytes; a
        one-byte change alters it."""
        return hashlib.sha256(self.raw).hexdigest()

    @property
    def size_bytes(self) -> int:
        return len(self.raw)

    @property
    def is_physical(self) -> bool:
        """True only for a ``REAL`` acquisition. Software modes are never
        physical, so this is False for every artifact built here."""
        return self.mode is AcquisitionMode.REAL

    def to_manifest(self) -> dict:
        """A manifest conforming to ``measurement_artifact.schema.json``.

        The raw bytes are not included -- only their hash and size -- so the
        manifest can travel without carrying (or exposing) the evidence.
        ``immutable`` is a constant ``True``.
        """
        return {
            "artifact_id": self.artifact_id,
            "run_id": self.run_id,
            "kind": self.kind.value,
            "media_type": self.media_type,
            "hash": self.content_hash,
            "bytes": self.size_bytes,
            "instrument_id": self.instrument_id,
            "calibration_id": self.calibration_id,
            "immutable": True,
        }

    @property
    def manifest_hash(self) -> str:
        """Content hash of the canonical manifest (path- and order-stable),
        via the R13 canonical serializer."""
        return S.content_hash(self.to_manifest())

    def verify(self, expected_hash: str) -> bool:
        """True iff the current bytes still hash to ``expected_hash``.

        A tampered artifact (any byte changed) fails this check.
        """
        return self.content_hash == expected_hash

    def replay(self) -> "MeasurementArtifact":
        """A ``REPLAY`` copy of this artifact: identical bytes and bindings,
        a new mode. Reproduces the same content hash without mutating the
        original evidence."""
        return MeasurementArtifact(
            artifact_id=self.artifact_id,
            run_id=self.run_id,
            kind=self.kind,
            media_type=self.media_type,
            raw=self.raw,
            instrument_id=self.instrument_id,
            calibration_id=self.calibration_id,
            mode=AcquisitionMode.REPLAY,
        )


def synthesize_raw(rng: np.random.Generator, n_bytes: int) -> bytes:
    """Deterministic synthetic raw bytes from a seeded numpy Generator.

    The same seeded generator always yields the same bytes, so a synthetic
    acquisition is reproducible and its content hash is stable.
    """
    if n_bytes <= 0:
        raise ArtifactError("n_bytes must be positive")
    return rng.integers(0, 256, size=n_bytes, dtype=np.uint8).tobytes()


def synthetic_artifact(*, artifact_id: str, run_id: str, instrument_id: str,
                       calibration_id: str, seed: int, n_bytes: int = 256,
                       kind: ArtifactKind = ArtifactKind.RAW_TRACE,
                       media_type: str = "application/octet-stream",
                       ) -> MeasurementArtifact:
    """Build a deterministic ``SYNTHETIC`` artifact from a seed.

    A synthetic artifact is software output. It is a fixture for exercising
    the provenance authority, never a physical measurement.
    """
    rng = np.random.default_rng(seed)
    return MeasurementArtifact(
        artifact_id=artifact_id,
        run_id=run_id,
        kind=kind,
        media_type=media_type,
        raw=synthesize_raw(rng, n_bytes),
        instrument_id=instrument_id,
        calibration_id=calibration_id,
        mode=AcquisitionMode.SYNTHETIC,
    )


def fault_injected(artifact: MeasurementArtifact, *,
                   byte_index: int = 0) -> MeasurementArtifact:
    """A ``FAULT_INJECTION`` copy with exactly one byte flipped.

    Used to prove tamper-evidence: the returned artifact differs from the
    original in a single byte and therefore has a different content hash.
    The original is not mutated.
    """
    if not 0 <= byte_index < artifact.size_bytes:
        raise ArtifactError("byte_index out of range")
    buf = bytearray(artifact.raw)
    buf[byte_index] ^= 0x01
    return MeasurementArtifact(
        artifact_id=artifact.artifact_id + "_FAULT",
        run_id=artifact.run_id,
        kind=artifact.kind,
        media_type=artifact.media_type,
        raw=bytes(buf),
        instrument_id=artifact.instrument_id,
        calibration_id=artifact.calibration_id,
        mode=AcquisitionMode.FAULT_INJECTION,
    )


def refuse_mutation(*_a, **_k) -> None:
    """Refuse to mutate an immutable artifact in place.

    Raw evidence is write-once. A replay or an analysis produces a new
    object; the original bytes are never edited, so the original content
    hash always remains verifiable.
    """
    raise ArtifactError(
        "refused: a measurement artifact is immutable evidence. Editing its "
        "bytes in place would destroy the tamper-evidence its content hash "
        "provides. Produce a new artifact (replay / fault-injection) instead.")


def artifacts_report() -> dict:
    """The standing result: an immutable, hashed synthetic artifact and its
    manifest. Nothing is measured."""
    art = synthetic_artifact(
        artifact_id="ART_DEMO_0001", run_id="RUN_DEMO",
        instrument_id="INSTR_SYNTH", calibration_id="CAL_SELFTEST",
        seed=20260724, n_bytes=256)
    tampered = fault_injected(art, byte_index=0)
    replayed = art.replay()
    return {
        "what_this_is": (
            "immutable measurement artifacts carrying their raw bytes, a "
            "SHA-256 content hash over exactly those bytes, and a manifest "
            "conforming to measurement_artifact.schema.json"),
        "claim_class": "SYNTHETIC_FIXTURE",
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "modes": [m.value for m in AcquisitionMode],
        "software_modes": sorted(m.value for m in SOFTWARE_MODES),
        "example_manifest": art.to_manifest(),
        "one_byte_change_alters_hash": art.content_hash != tampered.content_hash,
        "replay_reproduces_hash": art.content_hash == replayed.content_hash,
        "replay_does_not_mutate_original": art.verify(art.content_hash),
        "artifact_is_physical": art.is_physical,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any artifact is a physical measurement. Every "
            "artifact built here is SYNTHETIC or REPLAY -- software output, "
            "not an instrument reading of a specimen. A matching content "
            "hash proves the bytes are unaltered (integrity), never who "
            "produced them or that they were physically acquired. Nothing "
            "here is measured."),
    }
