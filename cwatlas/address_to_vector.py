"""P34 -- Geospatial address to the CW-GEO-1 canonical baseline vector.

The second stage of the forward geocoder: a typed :class:`GeospatialAddress`
(P33) is encoded to the versioned, checksummed CW-GEO-1 baseline vector
(:mod:`cwatlas.codec_geo1`), and decoded back to the *same* address exactly
within the codec's declared quantization grid. That exact map -> vector -> map
round-trip is the POWER property of this phase.

CW-GEO-1 is the atlas baseline codec: a direct reversible geodetic encoding
that snaps each component to a fixed integer grid and carries its codec id,
codec version, and a checksum on every vector. The generated vector therefore
carries its CRS (frame) and epoch inside the payload; nothing about it is
timeless or frame-free.

Round-trip reversibility is a ``CANONICAL_ROUND_TRIP`` fact about the codec. It
asserts nothing about what an operator-reported source vector meant, and it
validates nothing physical.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Nothing here reads a wall-clock; the epoch is carried through as a string.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cwatlas import checksums, claims
from cwatlas.canonical import CanonicalCoordinate, CanonicalCWAddress
from cwatlas.codec_geo1 import CODEC_ID, CODEC_VERSION, CWGeo1Codec, Geo1Error
from cwatlas.map_to_address import GeospatialAddress, MapClickError, map_click_to_address

#: Phase identity.
PHASE_ID = "P34"
TRANCHE = "T05"


class AddressVectorError(ValueError):
    """Raised on an address that cannot be encoded, or a vector that cannot decode."""


@dataclass(frozen=True)
class Geo1Encoding:
    """The result of encoding a geospatial address to CW-GEO-1.

    Attributes
    ----------
    address:
        The source :class:`GeospatialAddress`.
    canonical:
        The full typed :class:`CanonicalCWAddress` the codec produced (carrying
        the immutable raw payload, checksum tag, tokens, and residual).
    vector:
        The decodable CW-GEO-1 vector string (raw payload + checksum tag).
    """

    address: GeospatialAddress
    canonical: CanonicalCWAddress
    vector: str

    def verify(self) -> bool:
        """``True`` iff the vector's checksum still binds its payload."""
        return checksums.verify_vector(self.vector)


def _coordinate_of(address: GeospatialAddress) -> CanonicalCoordinate:
    """Project a geospatial address onto a declared canonical coordinate."""
    if not isinstance(address, GeospatialAddress):
        raise AddressVectorError("address must be a GeospatialAddress")
    try:
        return CanonicalCoordinate(
            body_id=address.body_id,
            frame_id=address.frame_id,
            epoch=address.epoch,
            latitude_deg=address.latitude_deg,
            longitude_deg=address.longitude_deg,
            height_m=0.0 if address.height_m is None else address.height_m,
            shell_state=address.shell_state,
        )
    except Exception as exc:  # canonical raises CanonicalError / ClaimError
        raise AddressVectorError(str(exc)) from exc


def address_to_vector(
    address: GeospatialAddress,
    *,
    software_commit: Optional[str] = None,
) -> Geo1Encoding:
    """Encode a geospatial address to the CW-GEO-1 canonical baseline vector.

    Returns a :class:`Geo1Encoding` carrying the typed canonical address and
    the decodable vector string. The vector embeds the body, frame, epoch, and
    quantized coordinate, and is bound by a checksum.
    """
    coord = _coordinate_of(address)
    codec = CWGeo1Codec()
    canonical = codec.encode_address(
        coord,
        uncertainty_m=address.uncertainty_m,
        software_commit=software_commit,
    )
    vector = codec.encode(coord)
    return Geo1Encoding(address=address, canonical=canonical, vector=vector)


def vector_to_address(vector: str) -> GeospatialAddress:
    """Decode a CW-GEO-1 vector back to a typed :class:`GeospatialAddress`.

    The exact inverse of :func:`address_to_vector` within the codec's declared
    quantization: the decoded address carries the same body, frame, epoch, and
    (quantized) coordinate. A malformed, mis-versioned, or checksum-failing
    vector is an explicit refusal, never a silent guess.
    """
    codec = CWGeo1Codec()
    try:
        coord = codec.decode(vector)
    except Geo1Error as exc:
        raise AddressVectorError(str(exc)) from exc
    # The quantization half-step in metres is the codec's declared floor.
    uncertainty_m = codec.encode_address(coord).uncertainty
    try:
        return map_click_to_address(
            body_id=coord.body_id,
            frame_id=coord.frame_id,
            epoch=coord.epoch,
            latitude_deg=coord.latitude_deg,
            longitude_deg=coord.longitude_deg,
            uncertainty_m=uncertainty_m,
            height_m=coord.height_m,
            shell_state=coord.shell_state,
        )
    except MapClickError as exc:
        raise AddressVectorError(str(exc)) from exc


def address_to_vector_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    codec = CWGeo1Codec()
    return {
        "module": "cwatlas.address_to_vector",
        "phase_id": PHASE_ID,
        "tranche": TRANCHE,
        "codec_id": CODEC_ID,
        "codec_version": CODEC_VERSION,
        "quantization": codec.quantization,
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "GEOSPATIAL_ADDRESS_TO_CW_GEO_1_EXACT_ROUND_TRIP",
        "what_this_does_not_say": (
            "An exact address -> vector -> address round-trip is a verified "
            "property of CW-GEO-1, not evidence that any operator-reported "
            "source vector identifies a real location."),
    }
