"""P35 -- Advanced icosahedral CW vector generation (CW-HCM-ICO).

The advanced forward codec of the geocoder: a typed :class:`GeospatialAddress`
is turned into a canonical icosahedral vector carrying a **face**, an **octal
path**, a continuous **residual**, a **shell/height** record, and a
**checksum**, with a human-readable token display. The vector is inverted back
to the same address to full floating-point precision (the POWER property).

The pipeline reuses the green icosahedral core:

* the address ``(latitude, longitude)`` is mapped to the body ellipsoid's
  outward *normal direction* ``(cos phi cos lam, cos phi sin lam, sin phi)`` --
  an exact bijection with ``(lat, lon)``;
* :func:`cwatlas.localize.forward` places that direction in a terminal
  spherical cell (face + octal path) and pins it with a barycentric residual
  from the cell centroid; and
* :func:`cwatlas.localize.inverse` reconstructs the direction exactly, which
  maps back to the original ``(lat, lon)``.

The refinement depth is selectable. At the canonical depth 12 the octal path
packs into 36 bits, aligned with the ``CW-PACK40-1`` path field. Height and
shell are carried alongside the direction (the icosahedral address encodes a
direction, not an altitude), so nothing about them is silently dropped.

An exact reversible round-trip is a ``CANONICAL_ROUND_TRIP`` fact about the
codec. A face id, an octal path, and a residual are selectors in a synthetic
tessellation, not a place, and assert nothing geographic about any source
vector.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Nothing here reads a wall-clock; the epoch is carried through as a string.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from cwatlas import checksums, claims
from cwatlas.addressing import (
    BITS_PER_DIGIT,
    CWPACK40_DEPTH,
    MAX_REFINEMENT_DEPTH,
    AddressError,
)
from cwatlas.icosahedron import build_icosahedron
from cwatlas.localize import ExactAddress, forward, inverse
from cwatlas.map_to_address import GeospatialAddress, MapClickError, map_click_to_address
from cwatlas.mars_frame import get_body

#: Phase identity.
PHASE_ID = "P35"
TRANCHE = "T05"

#: Codec identity (the advanced icosahedral codec family).
CODEC_ID = "CW-HCM-ICO"
CODEC_VERSION = "1.0.0"

#: The reconstruction tolerance of the reversible icosahedral core, in radians
#: of direction. The address -> vector -> address round-trip recovers latitude
#: and longitude to within this angle scaled onto the body.
RECONSTRUCTION_TOL_RAD = 1e-9

#: Module-level cached icosahedron (deterministic; built once).
_ICO = None


def _ico():
    global _ICO
    if _ICO is None:
        _ICO = build_icosahedron()
    return _ICO


class IcoVectorError(ValueError):
    """Raised on an invalid address, depth, or corrupted icosahedral vector."""


def latlon_to_direction(latitude_deg: float, longitude_deg: float) -> np.ndarray:
    """``(lat, lon)`` -> unit outward ellipsoid-normal direction.

    ``n = (cos phi cos lam, cos phi sin lam, sin phi)``. This is a bijection
    with ``(lat, lon)`` on the sphere and is body-independent (the normal
    direction does not depend on the ellipsoid radii).
    """
    phi = math.radians(latitude_deg)
    lam = math.radians(longitude_deg)
    cphi = math.cos(phi)
    return np.array(
        [cphi * math.cos(lam), cphi * math.sin(lam), math.sin(phi)],
        dtype=np.float64)


def direction_to_latlon(direction) -> tuple[float, float]:
    """Unit direction -> ``(latitude_deg, longitude_deg)`` (inverse of above)."""
    v = np.asarray(direction, dtype=np.float64).reshape(-1)
    if v.shape != (3,) or not np.all(np.isfinite(v)):
        raise IcoVectorError("direction must be a finite 3-vector")
    n = float(np.linalg.norm(v))
    if n < 1e-15:
        raise IcoVectorError("direction must be a non-zero 3-vector")
    v = v / n
    lat = math.degrees(math.asin(max(-1.0, min(1.0, float(v[2])))))
    lon = math.degrees(math.atan2(float(v[1]), float(v[0])))
    return (lat, lon)


def _octal_string(path: tuple[int, ...]) -> str:
    return "".join(str(d) for d in path)


def _packed_hex(path: tuple[int, ...]) -> tuple[str, int]:
    value = 0
    for d in path:
        value = (value << BITS_PER_DIGIT) | int(d)
    bits = BITS_PER_DIGIT * len(path)
    return (format(value, "x"), bits)


@dataclass(frozen=True)
class IcoVector:
    """A canonical icosahedral CW vector (CW-HCM-ICO).

    Carries the discrete address (``face_id``, ``path``), the continuous
    ``residual`` that makes it exact, the body/frame/epoch it is stamped
    against, the optional ``height_m`` and ``shell_state``, and a ``checksum``
    binding the whole payload.
    """

    codec_id: str
    codec_version: str
    body_id: str
    frame_id: str
    epoch: str
    face_id: int
    path: tuple[int, ...]
    residual: tuple[float, float, float]
    height_m: Optional[float]
    shell_state: Optional[int]
    checksum: str = field(default="")

    @property
    def depth(self) -> int:
        return len(self.path)

    @property
    def exact_address(self) -> ExactAddress:
        return ExactAddress(
            face_id=self.face_id, path=self.path, residual=self.residual)

    def payload(self) -> str:
        """The canonical, checksum-covered payload string (no checksum tag)."""
        octal = _octal_string(self.path)
        packed_hex, bits = _packed_hex(self.path)
        res = ",".join(repr(float(r)) for r in self.residual)
        h = "-" if self.height_m is None else repr(float(self.height_m))
        shell = "-" if self.shell_state is None else str(self.shell_state)
        return (
            f"v={self.codec_version};codec={self.codec_id};body={self.body_id};"
            f"frame={self.frame_id};epoch={self.epoch};face={self.face_id};"
            f"path={octal};pack={packed_hex}/{bits};res={res};h={h};shell={shell}")

    def token_string(self) -> str:
        """The full decodable vector string (payload + checksum tag)."""
        return checksums.append_checksum(self.payload())

    def token_display(self) -> str:
        """A compact human-readable token for the UI."""
        packed_hex, bits = _packed_hex(self.path)
        tag = self.checksum or checksums.checksum(self.payload())
        return (
            f"{self.codec_id} face={self.face_id:02d} "
            f"path={_octal_string(self.path) or '(root)'} "
            f"pack=0x{packed_hex}[{bits}b] {tag}")

    def verify_checksum(self) -> bool:
        """``True`` iff the stored checksum still binds the payload."""
        if not self.checksum:
            return False
        return checksums.verify(self.payload(), self.checksum)


def address_to_ico_vector(
    address: GeospatialAddress,
    *,
    depth: int = CWPACK40_DEPTH,
) -> IcoVector:
    """Encode a geospatial address to a canonical icosahedral CW vector.

    ``depth`` selects the refinement level; depth 12 yields a 36-bit path
    (``CW-PACK40-1`` aligned). Refuses a depth below zero or beyond the reused
    subdivision construction's numerical floor.
    """
    if not isinstance(address, GeospatialAddress):
        raise IcoVectorError("address must be a GeospatialAddress")
    get_body(address.body_id)  # refuse an unknown body
    direction = latlon_to_direction(address.latitude_deg, address.longitude_deg)
    try:
        exact = forward(_ico(), direction, depth)
    except AddressError as exc:
        raise IcoVectorError(str(exc)) from exc
    residual = tuple(float(r) for r in exact.residual)
    vec = IcoVector(
        codec_id=CODEC_ID,
        codec_version=CODEC_VERSION,
        body_id=address.body_id,
        frame_id=address.frame_id,
        epoch=address.epoch,
        face_id=int(exact.face_id),
        path=tuple(int(d) for d in exact.path),
        residual=residual,
        height_m=address.height_m,
        shell_state=address.shell_state,
    )
    # Bind the checksum to the finalized payload.
    return IcoVector(
        codec_id=vec.codec_id, codec_version=vec.codec_version,
        body_id=vec.body_id, frame_id=vec.frame_id, epoch=vec.epoch,
        face_id=vec.face_id, path=vec.path, residual=vec.residual,
        height_m=vec.height_m, shell_state=vec.shell_state,
        checksum=checksums.checksum(vec.payload()))


def ico_vector_to_address(vector: IcoVector) -> GeospatialAddress:
    """Invert an icosahedral CW vector back to a typed geospatial address.

    Reconstructs the direction from ``(face, path, residual)`` and maps it back
    to ``(lat, lon)``; body, frame, epoch, height, and shell are carried
    through. A vector whose checksum does not bind its payload is refused.
    """
    if not isinstance(vector, IcoVector):
        raise IcoVectorError("vector must be an IcoVector")
    if not vector.verify_checksum():
        raise IcoVectorError(
            "checksum verification failed: the icosahedral vector is corrupted")
    try:
        direction = inverse(_ico(), vector.exact_address)
    except AddressError as exc:
        raise IcoVectorError(str(exc)) from exc
    latitude_deg, longitude_deg = direction_to_latlon(direction)
    body = get_body(vector.body_id)
    uncertainty_m = RECONSTRUCTION_TOL_RAD * body.semi_major_axis_m
    try:
        return map_click_to_address(
            body_id=vector.body_id,
            frame_id=vector.frame_id,
            epoch=vector.epoch,
            latitude_deg=latitude_deg,
            longitude_deg=longitude_deg,
            uncertainty_m=uncertainty_m,
            height_m=vector.height_m,
            shell_state=vector.shell_state,
        )
    except MapClickError as exc:
        raise IcoVectorError(str(exc)) from exc


def parse_token_string(token: str) -> IcoVector:
    """Parse a decodable :meth:`IcoVector.token_string` back into an IcoVector.

    Refuses a token whose checksum fails. The residual floats are recovered
    exactly (Python ``repr`` of a float round-trips), so a parse then
    re-encode is bit-identical.
    """
    if not isinstance(token, str) or not token:
        raise IcoVectorError("token must be a non-empty string")
    if not checksums.verify_vector(token):
        raise IcoVectorError("checksum verification failed: token is corrupted")
    payload, _tag = checksums.split_checksum(token)
    fields: dict[str, str] = {}
    for part in payload.split(";"):
        key, _, val = part.partition("=")
        fields[key] = val
    required = {"v", "codec", "body", "frame", "epoch", "face", "path", "res",
                "h", "shell"}
    missing = required - fields.keys()
    if missing:
        raise IcoVectorError(f"token missing fields: {sorted(missing)}")
    try:
        face_id = int(fields["face"])
        path = tuple(int(c) for c in fields["path"]) if fields["path"] else ()
        residual = tuple(float(x) for x in fields["res"].split(","))
    except ValueError as exc:
        raise IcoVectorError(f"malformed icosahedral token: {exc}") from exc
    if len(residual) != 3:
        raise IcoVectorError("residual must have three components")
    height_m = None if fields["h"] == "-" else float(fields["h"])
    shell_state = None if fields["shell"] == "-" else int(fields["shell"])
    return IcoVector(
        codec_id=fields["codec"],
        codec_version=fields["v"],
        body_id=fields["body"],
        frame_id=fields["frame"],
        epoch=fields["epoch"],
        face_id=face_id,
        path=path,
        residual=residual,  # type: ignore[arg-type]
        height_m=height_m,
        shell_state=shell_state,
        checksum=checksums.checksum(payload),
    )


def ico_vector_report() -> dict:
    """What this codec claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.ico_vector",
        "phase_id": PHASE_ID,
        "tranche": TRANCHE,
        "codec_id": CODEC_ID,
        "codec_version": CODEC_VERSION,
        "cwpack40_depth": CWPACK40_DEPTH,
        "cwpack40_path_bits": BITS_PER_DIGIT * CWPACK40_DEPTH,
        "max_refinement_depth": MAX_REFINEMENT_DEPTH,
        "direction_convention": "ELLIPSOID_OUTWARD_NORMAL_UNIT_DIRECTION",
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_HCM_ICO_ADVANCED_VECTOR_EXACT_REVERSIBLE_ROUND_TRIP",
        "what_this_does_not_say": (
            "A face, an octal path, and a residual are selectors in a "
            "synthetic tessellation. Their exact round-trip is a property of "
            "the codec, not evidence that any operator-reported source vector "
            "identifies a real location."),
    }
