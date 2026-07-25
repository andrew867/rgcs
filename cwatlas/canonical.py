"""P17 -- the canonical CW object schema (typed addresses and results).

This is the stable, typed core the codecs and the map stack rest on. It
defines four objects and one contract:

* :class:`CanonicalCoordinate` -- a *declared* coordinate (body, frame, epoch,
  latitude, longitude, height, shell). It is the input a canonical codec
  encodes. A coordinate without a frame *and* an epoch is refused (System
  Contract invariant 9): a map pin never exists without a CRS and epoch.
* :class:`CanonicalCWAddress` -- the full typed address carrying every field
  the architecture requires (version, namespace, body_id, frame_id, epoch,
  horizontal_coordinate, radial_coordinate, shell_state, local_residual,
  codec_id, checksum, uncertainty, provenance). Its :meth:`to_vector_dict`
  projects to ``cw_vector.schema.json``; its raw string is immutable
  (invariant 1) and bound by a checksum.
* :class:`CodecResult` -- the typed decode outcome projecting to
  ``codec_result.schema.json``. Its status is an explicit enum: an invalid or
  underdetermined input yields ``INVALID`` / ``NO_UNIQUE_GEOGRAPHIC_DECODE`` /
  ``CALIBRATION_REQUIRED``, never a silent guess.
* :class:`CodecDefinition` -- the abstract base every codec implements:
  ``codec_id``, ``version``, ``quantization``, ``encode``, ``decode``.

That a reversible codec round-trips a *declared* coordinate is a
``CANONICAL_ROUND_TRIP`` fact about the codec. It says nothing about what an
operator-reported source vector meant.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Nothing here reads a wall-clock; epochs are decimal-year strings passed in.
"""

from __future__ import annotations

import hashlib
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional, Tuple

from cwatlas import checksums, claims

#: The address-object namespace and its schema version.
NAMESPACE = "RGCS-CW-ATLAS"
ADDRESS_SCHEMA_VERSION = "1.0.0"


class CanonicalError(ValueError):
    """Raised on an invalid, ambiguous, or underdetermined canonical object."""


def _normalize_longitude(lon_deg: float) -> float:
    """Fold longitude into (-180, 180]; both +/-180 map to +180 (dateline).

    Matches :func:`cwatlas.geodesy._normalize_longitude` so an address and the
    geodesy core agree on the dateline convention.
    """
    lon = math.remainder(lon_deg, 360.0)
    if lon <= -180.0:
        lon += 360.0
    return lon


@dataclass(frozen=True)
class CanonicalCoordinate:
    """A declared coordinate: the input a canonical codec encodes.

    ``epoch`` is a decimal-year string (e.g. ``"2020.0"``). ``frame_id`` and
    ``epoch`` are both mandatory: a coordinate that cannot name its CRS and
    epoch is refused, because a map pin requires both (invariant 9).
    """

    body_id: str
    frame_id: str
    epoch: str
    latitude_deg: float
    longitude_deg: float
    height_m: float = 0.0
    shell_state: Optional[int] = None

    def __post_init__(self) -> None:
        if not self.body_id:
            raise CanonicalError("body_id must be a non-empty string")
        # Invariant 9: no coordinate without a declared CRS (frame) and epoch.
        # An empty epoch string is normalised to None so the refusal fires.
        claims.refuse_pin_without_crs_epoch(
            crs=self.frame_id, epoch=(self.epoch or None))
        for name, value in (
            ("latitude_deg", self.latitude_deg),
            ("longitude_deg", self.longitude_deg),
            ("height_m", self.height_m),
        ):
            if not isinstance(value, (int, float)) or not math.isfinite(value):
                raise CanonicalError(f"{name} must be finite, got {value!r}")
        if not (-90.0 <= self.latitude_deg <= 90.0):
            raise CanonicalError(
                f"latitude_deg must be in [-90, 90], got {self.latitude_deg!r}")
        object.__setattr__(
            self, "longitude_deg", _normalize_longitude(float(self.longitude_deg)))
        object.__setattr__(self, "latitude_deg", float(self.latitude_deg))
        object.__setattr__(self, "height_m", float(self.height_m))
        if self.shell_state is not None:
            if not isinstance(self.shell_state, int) or isinstance(
                    self.shell_state, bool):
                raise CanonicalError(
                    f"shell_state must be an int or None, got {self.shell_state!r}")
            if not (0 <= self.shell_state <= 8):
                raise CanonicalError(
                    f"shell_state must be in [0, 8], got {self.shell_state!r}")


def make_provenance(
    raw: str,
    *,
    source_class: str = "SYNTHETIC",
    epoch: str = "0.0",
    operator_note: Optional[str] = None,
    software_commit: Optional[str] = None,
) -> dict:
    """Build a ``provenance_event.schema.json``-conforming provenance dict.

    ``raw_hash`` is the immutable SHA-256 of the raw string (invariant 1). The
    ``timestamp`` is the passed-in decimal-year epoch string -- never a
    wall-clock read -- so provenance is deterministic.
    """
    raw_hash = "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()
    event_id = "cwaddr:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return {
        "event_id": event_id,
        "timestamp": epoch,
        "source_class": source_class,
        "raw_hash": raw_hash,
        "operator_note": operator_note,
        "software_commit": software_commit,
    }


@dataclass(frozen=True)
class CanonicalCWAddress:
    """A typed canonical CW address (architecture "Canonical address" fields).

    The ``raw`` vector string is immutable and bound by ``checksum`` (invariant
    1). ``local_residual`` records the sub-quantization loss discarded by the
    codec, so the quantization is transparent rather than hidden.
    """

    version: str
    namespace: str
    body_id: str
    frame_id: str
    epoch: str
    horizontal_coordinate: Tuple[float, float]
    radial_coordinate: float
    shell_state: Optional[int]
    local_residual: Optional[Tuple[float, float, float]]
    codec_id: str
    checksum: Optional[str]
    uncertainty: float
    provenance: dict
    raw: str = ""
    tokens: Tuple[int, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.raw:
            raise CanonicalError("a canonical address must carry a raw vector")
        # Invariant 9: CRS (frame) and epoch are mandatory on any address.
        claims.refuse_pin_without_crs_epoch(
            crs=self.frame_id, epoch=(self.epoch or None))
        if len(self.horizontal_coordinate) != 2:
            raise CanonicalError("horizontal_coordinate must be (lat, lon)")
        if not math.isfinite(self.uncertainty) or self.uncertainty < 0.0:
            raise CanonicalError(
                f"uncertainty must be a non-negative distance, got "
                f"{self.uncertainty!r}")
        if not isinstance(self.provenance, dict) or "raw_hash" not in self.provenance:
            raise CanonicalError("provenance must be a provenance_event mapping")

    def verify_checksum(self) -> bool:
        """``True`` iff the stored checksum still binds the raw vector.

        A corrupted raw string, or a corrupted checksum, returns ``False``
        (invariant 1: the raw string and its bound hash must agree).
        """
        if not self.checksum:
            return False
        return checksums.verify(self.raw, self.checksum)

    def to_vector_dict(self) -> dict:
        """Project to a ``cw_vector.schema.json``-conforming mapping."""
        return {
            "raw": self.raw,
            "normalized": self.raw,
            "codec_id": self.codec_id,
            "codec_version": self.version,
            "tokens": list(self.tokens),
            "checksum": self.checksum,
            "provenance": self.provenance,
            "private": False,
        }

    def to_geospatial_dict(self) -> dict:
        """Project to a ``geospatial_address.schema.json``-conforming mapping."""
        return {
            "body_id": self.body_id,
            "frame_id": self.frame_id,
            "epoch": self.epoch,
            "latitude_deg": self.horizontal_coordinate[0],
            "longitude_deg": self.horizontal_coordinate[1],
            "height_m": self.radial_coordinate,
            "shell_state": self.shell_state,
            "uncertainty_m": self.uncertainty,
            "coordinate_convention": self.frame_id,
        }


class CodecStatus(Enum):
    """The explicit decode-result statuses (``codec_result.schema.json``)."""

    OK_POINT = "OK_POINT"
    OK_REGION = "OK_REGION"
    OK_ALIAS_SET = "OK_ALIAS_SET"
    INVALID = "INVALID"
    NO_UNIQUE_GEOGRAPHIC_DECODE = "NO_UNIQUE_GEOGRAPHIC_DECODE"
    CALIBRATION_REQUIRED = "CALIBRATION_REQUIRED"


@dataclass(frozen=True)
class CodecResult:
    """A typed decode outcome projecting to ``codec_result.schema.json``.

    A canonical codec resolves to exactly one point (``OK_POINT``) or an
    explicit ``INVALID``; a legacy codec may return an alias set. The status is
    never absent and never a silent guess.
    """

    status: CodecStatus
    codec_id: str
    candidates: Tuple[dict, ...]
    receipt_id: str
    warnings: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, CodecStatus):
            raise CanonicalError(
                f"status must be a CodecStatus, got {self.status!r}")
        if not self.codec_id:
            raise CanonicalError("codec_id must be a non-empty string")
        if not self.receipt_id:
            raise CanonicalError("receipt_id must be a non-empty string")
        # A positive point/region decode must carry at least one candidate.
        if self.status in (CodecStatus.OK_POINT, CodecStatus.OK_REGION,
                           CodecStatus.OK_ALIAS_SET) and not self.candidates:
            raise CanonicalError(
                f"status {self.status.value} requires at least one candidate")

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "codec_id": self.codec_id,
            "candidates": [dict(c) for c in self.candidates],
            "receipt_id": self.receipt_id,
            "warnings": list(self.warnings),
        }


class CodecDefinition(ABC):
    """The abstract base every CW codec implements.

    A codec declares an id, a version, and a quantization, and provides a
    reversible ``encode``/``decode`` pair over declared coordinates. Legacy
    codecs override ``decode`` to return an alias set rather than one point.
    """

    @property
    @abstractmethod
    def codec_id(self) -> str:
        """The codec's stable identifier (e.g. ``"CW-GEO-1"``)."""

    @property
    @abstractmethod
    def version(self) -> str:
        """The codec's semantic version string."""

    @property
    @abstractmethod
    def quantization(self) -> dict:
        """The declared quantization: the grid within which round-trip is exact."""

    @abstractmethod
    def encode(self, coordinate: CanonicalCoordinate) -> str:
        """Encode a declared coordinate to a versioned, checksummed CW vector."""

    @abstractmethod
    def decode(self, vector: str) -> Any:
        """Decode a CW vector back to a coordinate (or an alias set)."""


def canonical_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.canonical",
        "phase_id": "P17",
        "namespace": NAMESPACE,
        "address_schema_version": ADDRESS_SCHEMA_VERSION,
        "objects": [
            "CanonicalCoordinate", "CanonicalCWAddress", "CodecResult",
            "CodecDefinition", "CodecStatus",
        ],
        "codec_statuses": [s.value for s in CodecStatus],
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CANONICAL_CW_OBJECT_SCHEMA_TYPED_CRS_EPOCH_REQUIRED",
        "what_this_does_not_say": (
            "A typed canonical address is a declared coordinate bound by a "
            "checksum. That a codec round-trips it says nothing about whether "
            "any operator-reported source vector identifies a real location."),
    }
