"""P42 -- deterministic canonical decode (vector -> exactly one point).

The canonical arm of the inverse decoder. Architecture spec, Decode behavior:

    canonical vector -> exactly one point or explicit invalid result

A CW-GEO-1 (canonical) vector carries its codec id, version, and checksum. This
module runs the reversible codec's decode and resolves the vector to **exactly
one** :class:`GeographicPoint` -- with its CRS (frame) and epoch -- or an
**explicit invalid / refusal** result when the checksum fails, the version is
wrong, or the payload is malformed. It **never** returns an alias set for a
canonical vector: canonical decode is deterministic and single-valued by
construction, and asking for aliases here is a typed refusal.

That the codec round-trips a declared coordinate is a ``CANONICAL_ROUND_TRIP``
fact about the codec. It is *not* a claim that any operator-reported source
vector identifies a real place; a canonical vector is one the atlas itself
emitted (or a byte-identical copy), not a found artefact.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Deterministic: same vector and receipt id -> identical result. No wall-clock.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from cwatlas import claims
from cwatlas.canonical import CanonicalCoordinate, CodecStatus
from cwatlas.codec_geo1 import CWGeo1Codec, LAT_QUANT_DEG

#: WGS84-ish equatorial radius used only to express the quantization half-step
#: as a metres floor. Not a body model; just a scale for the uncertainty number.
_EARTH_RADIUS_M = 6378137.0


class CanonicalDecodeError(ValueError):
    """Raised on an illegal use of the canonical decoder."""


class DecodeStatus(Enum):
    """The explicit outcomes of a canonical decode."""

    OK_POINT = "OK_POINT"
    INVALID = "INVALID"
    REFUSED = "REFUSED"


@dataclass(frozen=True)
class GeographicPoint:
    """Exactly one decoded point, carrying its CRS (frame) and epoch.

    A canonical decode resolves to one of these or to nothing. ``crs`` is the
    frame id; ``epoch`` is the decimal-year string. Both are mandatory -- a map
    point without a CRS and epoch is refused (invariant 9).
    """

    body_id: str
    crs: str
    epoch: str
    latitude_deg: float
    longitude_deg: float
    height_m: float
    shell_state: Optional[int]
    codec_id: str
    codec_version: str
    uncertainty_m: float

    def __post_init__(self) -> None:
        # Invariant 9: no point without a declared CRS (frame) and epoch.
        claims.refuse_pin_without_crs_epoch(
            crs=self.crs, epoch=(self.epoch or None))
        if not (-90.0 <= self.latitude_deg <= 90.0):
            raise CanonicalDecodeError(
                f"latitude_deg out of range: {self.latitude_deg!r}")
        if not (-180.0 <= self.longitude_deg <= 180.0):
            raise CanonicalDecodeError(
                f"longitude_deg out of range: {self.longitude_deg!r}")
        if not math.isfinite(self.uncertainty_m) or self.uncertainty_m < 0.0:
            raise CanonicalDecodeError(
                f"uncertainty_m must be non-negative, got {self.uncertainty_m!r}")

    def to_dict(self) -> dict:
        return {
            "body_id": self.body_id,
            "crs": self.crs,
            "epoch": self.epoch,
            "latitude_deg": self.latitude_deg,
            "longitude_deg": self.longitude_deg,
            "height_m": self.height_m,
            "shell_state": self.shell_state,
            "codec_id": self.codec_id,
            "codec_version": self.codec_version,
            "uncertainty_m": self.uncertainty_m,
        }


@dataclass(frozen=True)
class CanonicalDecodeResult:
    """A typed canonical-decode outcome: one point, or an explicit non-point.

    ``point`` is populated iff ``status is DecodeStatus.OK_POINT``. There is
    deliberately no ``candidates`` field: a canonical vector never yields an
    alias set.
    """

    status: DecodeStatus
    codec_id: str
    point: Optional[GeographicPoint]
    reason: str
    claim_class: str
    receipt_id: str

    def __post_init__(self) -> None:
        if self.status is DecodeStatus.OK_POINT and self.point is None:
            raise CanonicalDecodeError(
                "OK_POINT requires exactly one GeographicPoint")
        if self.status is not DecodeStatus.OK_POINT and self.point is not None:
            raise CanonicalDecodeError(
                "a non-OK_POINT result must not carry a point")

    def is_point(self) -> bool:
        return self.status is DecodeStatus.OK_POINT

    def require_point(self) -> GeographicPoint:
        """Return the sole point, or raise on an invalid/refused decode."""
        if self.point is None:
            raise CanonicalDecodeError(
                f"no point: canonical decode was {self.status.value} "
                f"({self.reason})")
        return self.point

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "codec_id": self.codec_id,
            "point": self.point.to_dict() if self.point else None,
            "reason": self.reason,
            "claim_class": self.claim_class,
            "receipt_id": self.receipt_id,
        }


def _quantization_floor_m() -> float:
    """The canonical quantization half-step expressed in metres of latitude."""
    return 0.5 * LAT_QUANT_DEG * math.pi / 180.0 * _EARTH_RADIUS_M


def _receipt_id(vector: str) -> str:
    """Deterministic receipt id derived from the vector (no wall-clock)."""
    return "P42-" + hashlib.sha256(vector.encode("utf-8")).hexdigest()[:16]


def refuse_alias_for_canonical(*_a, **_k) -> None:
    """A canonical vector may not be decoded to an alias set (deterministic)."""
    raise claims.ClaimError(
        "refused: a canonical (CW-GEO-1) vector resolves to exactly one point "
        "or an explicit invalid result. It never yields an alias set -- "
        "canonical decode is deterministic and single-valued by construction.")


def decode_canonical(
    vector: str,
    *,
    receipt_id: Optional[str] = None,
    codec: Optional[CWGeo1Codec] = None,
) -> CanonicalDecodeResult:
    """Decode a canonical CW-GEO-1 vector to exactly one point, or INVALID.

    A checksum failure, a version mismatch, or a malformed payload yields an
    explicit :attr:`DecodeStatus.INVALID` (a ``REFUSAL`` claim), never a guess
    and never an alias set. A well-formed vector yields exactly one
    :class:`GeographicPoint` (a ``CANONICAL_ROUND_TRIP`` claim).
    """
    if not isinstance(vector, str):
        raise CanonicalDecodeError(
            f"vector must be a str, got {type(vector).__name__}")
    codec = codec or CWGeo1Codec()
    rid = receipt_id or _receipt_id(vector)
    result = codec.decode_result(vector, receipt_id=rid)

    if result.status is CodecStatus.OK_POINT:
        # A canonical codec yields exactly one candidate by construction.
        if len(result.candidates) != 1:
            refuse_alias_for_canonical()  # never reached in practice; guards it
        c = result.candidates[0]
        point = GeographicPoint(
            body_id=c["body_id"],
            crs=c["frame_id"],
            epoch=c["epoch"],
            latitude_deg=c["latitude_deg"],
            longitude_deg=c["longitude_deg"],
            height_m=c["height_m"],
            shell_state=c["shell_state"],
            codec_id=result.codec_id,
            codec_version=codec.version,
            uncertainty_m=_quantization_floor_m(),
        )
        return CanonicalDecodeResult(
            status=DecodeStatus.OK_POINT,
            codec_id=result.codec_id,
            point=point,
            reason="reversible CW-GEO-1 round-trip within declared quantization",
            claim_class=claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
            receipt_id=rid,
        )

    # INVALID from the codec (bad checksum / wrong version / malformed).
    reason = result.warnings[0] if result.warnings else "invalid canonical vector"
    return CanonicalDecodeResult(
        status=DecodeStatus.INVALID,
        codec_id=result.codec_id,
        point=None,
        reason=reason,
        claim_class=claims.ClaimClass.REFUSAL.value,
        receipt_id=rid,
    )


def encode_canonical(coordinate: CanonicalCoordinate, *,
                     codec: Optional[CWGeo1Codec] = None) -> str:
    """Encode a declared coordinate to a canonical vector (round-trip helper).

    Provided so callers and tests can build the exact vector that
    :func:`decode_canonical` inverts, without importing the codec directly.
    """
    codec = codec or CWGeo1Codec()
    return codec.encode(coordinate)


def decode_canonical_report() -> dict:
    """P42 declaration receipt. One point or an explicit invalid; never aliases."""
    return {
        "module": "cwatlas.decode_canonical",
        "phase_id": "P42",
        "tranche": "T06",
        "decode_statuses": [s.value for s in DecodeStatus],
        "decode_behavior": (
            "canonical vector -> exactly one GeographicPoint (with CRS and "
            "epoch) or an explicit INVALID result; never an alias set"),
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "DETERMINISTIC_CANONICAL_DECODE_ONE_POINT_OR_INVALID",
        "what_this_does_not_say": (
            "A canonical round-trip is a verified property of the CW-GEO-1 "
            "codec over a coordinate the atlas declared. It is not evidence "
            "that any operator-reported source vector identifies a real "
            "location; that a canonical vector decodes cleanly says nothing "
            "about a found artefact's meaning."),
    }
