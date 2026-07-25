"""P18 -- CW-GEO-1, the direct reversible geodetic baseline codec.

CW-GEO-1 encodes a *declared* canonical coordinate (latitude, longitude,
height, on a named body/frame/epoch) to a versioned, checksummed CW vector
string, and decodes it back exactly within a declared quantization grid. It is
the atlas baseline: the simplest reversible codec, against which every richer
grammar (icosahedral, packed, legacy) is later measured.

Two properties make it a canonical codec (System Contract invariant 3):

* **Reversible within declared quantization.** ``encode`` snaps each component
  to a fixed integer grid and writes the integers; ``decode`` reads them back.
  The recovered coordinate differs from the input by at most half a grid step,
  and ``encode(decode(vector)) == vector`` byte-for-byte (idempotent).
* **Self-describing and guarded.** Every vector carries its codec id, its
  codec version, and a checksum. ``decode`` refuses a vector whose checksum
  fails or whose version does not match (via :mod:`cwatlas.checksums`).

CW-GEO-1 is *independent of any source-vector semantics*. It maps a coordinate
you declare; it never reads or interprets an operator-reported vector. That it
round-trips is a ``CANONICAL_ROUND_TRIP`` fact about the codec.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Nothing here reads a wall-clock; epochs are decimal-year strings passed in.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

from cwatlas import canonical, checksums, claims
from cwatlas.canonical import (
    CanonicalCoordinate,
    CanonicalCWAddress,
    CodecDefinition,
    CodecResult,
    CodecStatus,
)

CODEC_ID = "CW-GEO-1"
CODEC_VERSION = "1.0.0"

#: Declared quantization grid. Round-trip is exact to within one step.
#: 1e-8 deg ~ 1.1 mm of latitude; 1e-4 m = 0.1 mm of height.
LAT_QUANT_DEG = 1e-8
LON_QUANT_DEG = 1e-8
HEIGHT_QUANT_M = 1e-4


class Geo1Error(ValueError):
    """Raised on a malformed, mis-versioned, or checksum-failing CW-GEO-1 vector."""


@dataclass(frozen=True)
class DecodedGeo:
    """A decoded coordinate plus the quantization residual it discarded."""

    coordinate: CanonicalCoordinate
    tokens: Tuple[int, int, int]
    shell_state: int | None


def _quantize(value: float, step: float) -> int:
    return int(round(value / step))


def _dequantize(q: int, step: float) -> float:
    return q * step


class CWGeo1Codec(CodecDefinition):
    """The CW-GEO-1 direct reversible geodetic baseline codec."""

    @property
    def codec_id(self) -> str:
        return CODEC_ID

    @property
    def version(self) -> str:
        return CODEC_VERSION

    @property
    def quantization(self) -> dict:
        return {
            "latitude_deg": LAT_QUANT_DEG,
            "longitude_deg": LON_QUANT_DEG,
            "height_m": HEIGHT_QUANT_M,
            "round_trip_tolerance": {
                "latitude_deg": LAT_QUANT_DEG,
                "longitude_deg": LON_QUANT_DEG,
                "height_m": HEIGHT_QUANT_M,
            },
        }

    # -- encode ------------------------------------------------------------

    def _payload(self, coord: CanonicalCoordinate) -> Tuple[str, Tuple[int, int, int]]:
        q_lat = _quantize(coord.latitude_deg, LAT_QUANT_DEG)
        q_lon = _quantize(coord.longitude_deg, LON_QUANT_DEG)
        q_h = _quantize(coord.height_m, HEIGHT_QUANT_M)
        shell = "-" if coord.shell_state is None else str(coord.shell_state)
        payload = (
            f"v={CODEC_VERSION};codec={CODEC_ID};body={coord.body_id};"
            f"frame={coord.frame_id};epoch={coord.epoch};"
            f"lat={q_lat};lon={q_lon};h={q_h};shell={shell}"
        )
        return payload, (q_lat, q_lon, q_h)

    def encode(self, coordinate: CanonicalCoordinate) -> str:
        """Encode a declared coordinate to a versioned, checksummed CW vector."""
        if not isinstance(coordinate, CanonicalCoordinate):
            raise Geo1Error(
                f"encode expects a CanonicalCoordinate, got {type(coordinate)!r}")
        payload, _tokens = self._payload(coordinate)
        return checksums.append_checksum(payload)

    # -- decode ------------------------------------------------------------

    def _parse(self, vector: str) -> DecodedGeo:
        if not isinstance(vector, str) or not vector:
            raise Geo1Error("vector must be a non-empty string")
        if not checksums.verify_vector(vector):
            raise Geo1Error(
                "checksum verification failed: the vector is corrupted or was "
                "written under a different checksum version")
        try:
            checksums.require_version(vector, CODEC_ID, CODEC_VERSION)
        except checksums.ChecksumError as exc:
            raise Geo1Error(str(exc)) from exc
        payload, _tag = checksums.split_checksum(vector)
        fields = {}
        for part in payload.split(";"):
            key, _, val = part.partition("=")
            fields[key] = val
        required = {"body", "frame", "epoch", "lat", "lon", "h", "shell"}
        missing = required - fields.keys()
        if missing:
            raise Geo1Error(f"vector missing fields: {sorted(missing)}")
        try:
            q_lat = int(fields["lat"])
            q_lon = int(fields["lon"])
            q_h = int(fields["h"])
        except ValueError as exc:
            raise Geo1Error(f"non-integer quantized field: {exc}") from exc
        shell_txt = fields["shell"]
        shell = None if shell_txt == "-" else int(shell_txt)
        coord = CanonicalCoordinate(
            body_id=fields["body"],
            frame_id=fields["frame"],
            epoch=fields["epoch"],
            latitude_deg=_dequantize(q_lat, LAT_QUANT_DEG),
            longitude_deg=_dequantize(q_lon, LON_QUANT_DEG),
            height_m=_dequantize(q_h, HEIGHT_QUANT_M),
            shell_state=shell,
        )
        return DecodedGeo(coordinate=coord, tokens=(q_lat, q_lon, q_h),
                          shell_state=shell)

    def decode(self, vector: str) -> CanonicalCoordinate:
        """Decode a CW-GEO-1 vector to its declared coordinate (exactly one).

        Raises :class:`Geo1Error` on a malformed, mis-versioned, or
        checksum-failing vector -- an explicit failure, never a silent guess.
        """
        return self._parse(vector).coordinate

    def decode_result(self, vector: str, *, receipt_id: str) -> CodecResult:
        """Decode into a typed :class:`CodecResult` (``OK_POINT`` / ``INVALID``).

        A canonical vector resolves to exactly one point; a bad vector yields an
        explicit ``INVALID`` result object rather than an exception.
        """
        try:
            decoded = self._parse(vector)
        except Geo1Error as exc:
            return CodecResult(
                status=CodecStatus.INVALID,
                codec_id=CODEC_ID,
                candidates=(),
                receipt_id=receipt_id,
                warnings=(str(exc),),
            )
        c = decoded.coordinate
        candidate = {
            "body_id": c.body_id,
            "frame_id": c.frame_id,
            "epoch": c.epoch,
            "latitude_deg": c.latitude_deg,
            "longitude_deg": c.longitude_deg,
            "height_m": c.height_m,
            "shell_state": c.shell_state,
            "tokens": list(decoded.tokens),
        }
        return CodecResult(
            status=CodecStatus.OK_POINT,
            codec_id=CODEC_ID,
            candidates=(candidate,),
            receipt_id=receipt_id,
        )

    # -- typed canonical address ------------------------------------------

    def encode_address(
        self,
        coordinate: CanonicalCoordinate,
        *,
        uncertainty_m: float | None = None,
        source_class: str = "SYNTHETIC",
        software_commit: str | None = None,
    ) -> CanonicalCWAddress:
        """Encode a coordinate to a full typed :class:`CanonicalCWAddress`.

        The address carries the immutable raw payload, its checksum tag, the
        quantization tokens, and the sub-quantization ``local_residual`` so the
        (small) quantization loss is transparent rather than hidden.
        """
        payload, tokens = self._payload(coordinate)
        vector = checksums.append_checksum(payload)
        _, tag = checksums.split_checksum(vector)
        # Recover the quantized coordinate to compute the residual + fields.
        dec_lat = _dequantize(tokens[0], LAT_QUANT_DEG)
        dec_lon = _dequantize(tokens[1], LON_QUANT_DEG)
        dec_h = _dequantize(tokens[2], HEIGHT_QUANT_M)
        residual = (
            coordinate.latitude_deg - dec_lat,
            coordinate.longitude_deg - dec_lon,
            coordinate.height_m - dec_h,
        )
        # Uncertainty defaults to the declared quantization half-step in metres
        # (~ half of 1e-8 deg of latitude), a floor from quantization alone.
        if uncertainty_m is None:
            uncertainty_m = 0.5 * LAT_QUANT_DEG * math.pi / 180.0 * 6378137.0
        provenance = canonical.make_provenance(
            payload,
            source_class=source_class,
            epoch=coordinate.epoch,
            software_commit=software_commit,
        )
        return CanonicalCWAddress(
            version=CODEC_VERSION,
            namespace=canonical.NAMESPACE,
            body_id=coordinate.body_id,
            frame_id=coordinate.frame_id,
            epoch=coordinate.epoch,
            horizontal_coordinate=(dec_lat, dec_lon),
            radial_coordinate=dec_h,
            shell_state=coordinate.shell_state,
            local_residual=residual,
            codec_id=CODEC_ID,
            checksum=tag,
            uncertainty=float(uncertainty_m),
            provenance=provenance,
            raw=payload,
            tokens=tokens,
        )


def codec_geo1_report() -> dict:
    """What this codec claims -- and, deliberately, what it does not."""
    codec = CWGeo1Codec()
    return {
        "module": "cwatlas.codec_geo1",
        "phase_id": "P18",
        "codec_id": codec.codec_id,
        "codec_version": codec.version,
        "quantization": codec.quantization,
        "independent_of_source_vectors": True,
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_GEO_1_REVERSIBLE_BASELINE_ROUND_TRIP_WITHIN_QUANTIZATION",
        "what_this_does_not_say": (
            "CW-GEO-1 round-trips a coordinate you declare. It does not read, "
            "interpret, or validate any operator-reported source vector, and "
            "its reversibility is no evidence about what such a vector meant."),
    }
