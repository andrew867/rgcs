"""P57 -- framework-agnostic backend service layer for the CW Atlas.

The smallest stable API surface the atlas exposes to *any* front end. Every
function here is a plain Python function that takes JSON-able arguments and
returns a JSON-able ``dict``; nothing here imports a web framework. FastAPI is
**not** a dependency and is never imported -- a future ``FastAPI`` (or Flask, or
gRPC) layer would call these functions unchanged, and the CLI
(:mod:`cwatlas.cli`) is just one such caller.

The service is a thin, governed facade over the green atlas core:

* :func:`encode_point` -- a declared point -> a canonical CW vector
  (``CW-GEO-1`` baseline or ``CW-HCM-ICO`` icosahedral), reusing
  :mod:`cwatlas.map_to_address`, :mod:`cwatlas.address_to_vector`, and
  :mod:`cwatlas.ico_vector`;
* :func:`decode_vector` -- a canonical vector -> exactly one point or an
  explicit typed refusal, reusing :mod:`cwatlas.decode_canonical`;
* :func:`legacy_search` -- a raw found string -> an alias set (0..N candidates)
  or a refusal, reusing :mod:`cwatlas.ingest` and :mod:`cwatlas.decode_legacy`;
* :func:`round_trip` -- encode then decode a point and report the residual;
* :func:`export_bundle` -- a batch of points -> a hash-chained audit bundle of
  encode receipts, reusing :mod:`cwatlas.audit_bundle`.

Every result carries its CRS (frame), its epoch, and its **claim class**. No
result promotes an arithmetic re-expression into a geographic fact: a canonical
round-trip is a property of the codec, a legacy search is an alias set or a
refusal, and a source vector's geographic semantics stay ``NOT_CLAIMED``.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Deterministic: the same arguments yield byte-identical output. Epochs are
decimal-year strings passed in; nothing here reads a wall-clock.
"""

from __future__ import annotations

import math
from typing import Optional, Sequence

from cwatlas import checksums, claims
from cwatlas.address_to_vector import (
    AddressVectorError,
    address_to_vector,
)
from cwatlas.audit_bundle import (
    AuditReceipt,
    ReceiptType,
    build_audit_bundle,
)
from cwatlas.codec_geo1 import CODEC_ID as GEO1_CODEC_ID
from cwatlas.codec_geo1 import CODEC_VERSION as GEO1_CODEC_VERSION
from cwatlas.decode_canonical import decode_canonical
from cwatlas.decode_legacy import search_legacy
from cwatlas.ico_vector import CODEC_ID as ICO_CODEC_ID
from cwatlas.ico_vector import (
    address_to_ico_vector,
    ico_vector_to_address,
    parse_token_string,
)
from cwatlas.ingest import ingest
from cwatlas.map_to_address import MapClickError, map_click_to_address

#: Phase identity.
PHASE_ID = "P57"
TRANCHE = "T08"

#: Canonical codecs the service can encode/decode.
SUPPORTED_CODECS = (GEO1_CODEC_ID, ICO_CODEC_ID)

#: The standing governance footer stamped on every service result.
_BOUNDARY = {
    "measured_here": "nothing",
    "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
    "source_vector_geographic_semantics": "NOT_CLAIMED",
}


class ServiceError(ValueError):
    """Raised on an invalid service request (bad codec, missing input, ...).

    An explicit result state at the boundary, never a silent guess.
    """


def _boundary(d: dict) -> dict:
    """Attach the standing governance footer to a result dict (copy)."""
    out = dict(d)
    out.update(_BOUNDARY)
    return out


def _require_finite(name: str, value) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ServiceError(f"{name} must be a number, got {value!r}")
    f = float(value)
    if not math.isfinite(f):
        raise ServiceError(f"{name} must be finite, got {value!r}")
    return f


def encode_point(
    *,
    body_id: str,
    frame_id: str,
    epoch: str,
    latitude_deg: float,
    longitude_deg: float,
    uncertainty_m: Optional[float] = None,
    height_m: Optional[float] = None,
    shell_state: Optional[int] = None,
    codec: str = GEO1_CODEC_ID,
    software_commit: Optional[str] = None,
) -> dict:
    """Encode a declared point to a canonical CW vector.

    ``codec`` selects the baseline ``CW-GEO-1`` or the icosahedral
    ``CW-HCM-ICO``. ``uncertainty_m`` is a **required, explicit** input (no
    hidden precision default). ``frame_id`` (CRS) and ``epoch`` are mandatory: a
    point without them is refused (invariant 9). The result is a
    ``CANONICAL_ROUND_TRIP`` fact about the codec and carries its CRS + epoch.
    """
    if codec not in SUPPORTED_CODECS:
        raise ServiceError(
            f"unsupported codec {codec!r}; supported: {list(SUPPORTED_CODECS)}")
    if uncertainty_m is None:
        raise ServiceError(
            "uncertainty_m is a required explicit input; the service rejects a "
            "hidden precision default")
    lat = _require_finite("latitude_deg", latitude_deg)
    lon = _require_finite("longitude_deg", longitude_deg)
    unc = _require_finite("uncertainty_m", uncertainty_m)
    try:
        address = map_click_to_address(
            body_id=body_id,
            frame_id=frame_id,
            epoch=epoch,
            latitude_deg=lat,
            longitude_deg=lon,
            uncertainty_m=unc,
            height_m=height_m,
            shell_state=shell_state,
        )
    except (MapClickError, claims.ClaimError) as exc:
        raise ServiceError(str(exc)) from exc

    if codec == GEO1_CODEC_ID:
        try:
            enc = address_to_vector(address, software_commit=software_commit)
        except AddressVectorError as exc:
            raise ServiceError(str(exc)) from exc
        vector = enc.vector
        codec_version = GEO1_CODEC_VERSION
    else:  # ICO_CODEC_ID
        try:
            ico = address_to_ico_vector(address)
        except Exception as exc:  # IcoVectorError and friends
            raise ServiceError(str(exc)) from exc
        vector = ico.token_string()
        codec_version = ico.codec_version

    return _boundary({
        "operation": "encode",
        "codec_id": codec,
        "codec_version": codec_version,
        "body_id": address.body_id,
        "crs": address.frame_id,
        "epoch": address.epoch,
        "vector": vector,
        "point": {
            "latitude_deg": address.latitude_deg,
            "longitude_deg": address.longitude_deg,
            "height_m": address.height_m,
            "shell_state": address.shell_state,
            "uncertainty_m": address.uncertainty_m,
        },
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
    })


def _refusal(reason: str, *, operation: str = "decode",
             codec_id: Optional[str] = None) -> dict:
    """A typed refusal result -- never an exception, never a guessed point."""
    return _boundary({
        "operation": operation,
        "status": "REFUSED",
        "codec_id": codec_id,
        "point": None,
        "reason": reason,
        "crs": None,
        "epoch": None,
        "claim_class": claims.ClaimClass.REFUSAL.value,
    })


def decode_vector(
    vector,
    *,
    codec: Optional[str] = None,
    receipt_id: Optional[str] = None,
) -> dict:
    """Decode a canonical CW vector to exactly one point, or a typed refusal.

    Always returns a typed ``dict`` -- a malformed, mis-versioned, unknown, or
    checksum-failing vector yields a ``REFUSAL``/``INVALID`` result rather than
    raising. When ``codec`` is not given it is read from the vector's ``codec=``
    marker; a vector with no declared codec is refused (never silently
    defaulted). A decoded point carries its CRS (frame) and epoch.
    """
    if not isinstance(vector, str) or not vector:
        return _refusal("vector must be a non-empty string")

    detected = codec
    if detected is None:
        try:
            detected, _ = checksums.parse_codec_version(vector)
        except checksums.ChecksumError as exc:
            return _refusal(str(exc))

    if detected == GEO1_CODEC_ID:
        try:
            result = decode_canonical(vector, receipt_id=receipt_id)
        except Exception as exc:  # never crash the boundary
            return _refusal(f"canonical decode error: {exc}",
                            codec_id=GEO1_CODEC_ID)
        d = result.to_dict()
        point = d.get("point")
        out = {
            "operation": "decode",
            "codec_id": d.get("codec_id"),
            "status": d.get("status"),
            "point": point,
            "reason": d.get("reason"),
            "crs": point.get("crs") if point else None,
            "epoch": point.get("epoch") if point else None,
            "claim_class": d.get("claim_class"),
            "receipt_id": d.get("receipt_id"),
        }
        return _boundary(out)

    if detected == ICO_CODEC_ID:
        try:
            ico = parse_token_string(vector)
            address = ico_vector_to_address(ico)
        except Exception as exc:
            return _refusal(f"icosahedral decode error: {exc}",
                            codec_id=ICO_CODEC_ID)
        return _boundary({
            "operation": "decode",
            "codec_id": ICO_CODEC_ID,
            "status": "OK_POINT",
            "point": {
                "body_id": address.body_id,
                "crs": address.frame_id,
                "epoch": address.epoch,
                "latitude_deg": address.latitude_deg,
                "longitude_deg": address.longitude_deg,
                "height_m": address.height_m,
                "shell_state": address.shell_state,
                "codec_id": ICO_CODEC_ID,
                "codec_version": ico.codec_version,
                "uncertainty_m": address.uncertainty_m,
            },
            "reason": "reversible CW-HCM-ICO round-trip within reconstruction tolerance",
            "crs": address.frame_id,
            "epoch": address.epoch,
            "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        })

    return _refusal(
        f"unsupported codec {detected!r}; supported: {list(SUPPORTED_CODECS)}",
        codec_id=detected)


def legacy_search(
    raw,
    *,
    use_digits: bool = True,
    ingest_id: str = "service-legacy",
) -> dict:
    """Run the legacy candidate codecs over a raw found string.

    Returns a typed ``dict`` carrying the alias set (0..N candidates, each with
    a score, uncertainty, and search-space count) as a
    ``LEGACY_ALIAS_CANDIDATE`` result, or a ``REFUSAL`` when no legacy codec
    admitted the string. Never forces a pin (invariant 4); never returns a
    location. Always returns a typed result rather than raising, so it is safe
    for the fuzz harness.
    """
    if not isinstance(raw, str):
        return _boundary({
            "operation": "legacy",
            "raw": None,
            "status": "REFUSAL",
            "count": 0,
            "reason": f"raw must be a string, got {type(raw).__name__}",
            "claim_class": claims.ClaimClass.REFUSAL.value,
        })
    try:
        ingested = ingest(raw, ingest_id=ingest_id)
        search_string = (
            ingested.digits_only() if use_digits else ingested.normalized)
        result = search_legacy(search_string)
    except Exception as exc:  # empty vector, ingest error, etc.
        return _boundary({
            "operation": "legacy",
            "raw": raw,
            "status": "REFUSAL",
            "count": 0,
            "reason": f"no admissible legacy decode: {exc}",
            "claim_class": claims.ClaimClass.REFUSAL.value,
        })
    out = result.to_dict()
    out["operation"] = "legacy"
    return _boundary(out)


def round_trip(
    *,
    body_id: str,
    frame_id: str,
    epoch: str,
    latitude_deg: float,
    longitude_deg: float,
    uncertainty_m: float,
    height_m: Optional[float] = None,
    shell_state: Optional[int] = None,
    codec: str = GEO1_CODEC_ID,
    software_commit: Optional[str] = None,
) -> dict:
    """Encode a point, decode the vector, and report the residual.

    The exact ``point -> vector -> point`` round-trip is the POWER property of
    the canonical codecs. The result records both the encoded vector and the
    decoded point, the great-circle-free component residual in degrees, and
    whether the round-trip closed within the codec's declared tolerance.
    """
    encoded = encode_point(
        body_id=body_id,
        frame_id=frame_id,
        epoch=epoch,
        latitude_deg=latitude_deg,
        longitude_deg=longitude_deg,
        uncertainty_m=uncertainty_m,
        height_m=height_m,
        shell_state=shell_state,
        codec=codec,
        software_commit=software_commit,
    )
    decoded = decode_vector(encoded["vector"], codec=codec)
    point = decoded.get("point")
    ok = bool(point) and decoded.get("status") == "OK_POINT"
    if ok:
        dlat = abs(point["latitude_deg"] - encoded["point"]["latitude_deg"])
        dlon = abs(point["longitude_deg"] - encoded["point"]["longitude_deg"])
        residual_deg = max(dlat, dlon)
    else:
        residual_deg = None
    # CW-GEO-1 declares a 1e-8 deg grid; CW-HCM-ICO reconstructs to ~1e-9 rad.
    tolerance_deg = 1e-6
    return _boundary({
        "operation": "roundtrip",
        "codec_id": codec,
        "crs": frame_id,
        "epoch": epoch,
        "closed": bool(ok and residual_deg is not None
                       and residual_deg <= tolerance_deg),
        "residual_deg": residual_deg,
        "tolerance_deg": tolerance_deg,
        "encoded": encoded,
        "decoded": decoded,
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
    })


def export_bundle(
    points: Sequence[dict],
    *,
    software_commit: Optional[str] = None,
    codec: str = GEO1_CODEC_ID,
) -> dict:
    """Encode a batch of points and seal the receipts into an audit bundle.

    Each point is a mapping with ``body_id``, ``frame_id``, ``epoch``,
    ``latitude_deg``, ``longitude_deg``, ``uncertainty_m`` (and optional
    ``height_m``/``shell_state``). Every encode receipt records the vector, CRS,
    epoch, and its ``CANONICAL_ROUND_TRIP`` claim; the receipts are hash-chained
    and privacy-scanned by :mod:`cwatlas.audit_bundle`, so no private token can
    enter the signed bundle. Returns the serialized, verifiable bundle.
    """
    if not isinstance(points, (list, tuple)) or not points:
        raise ServiceError("export_bundle needs a non-empty list of points")
    receipts = []
    for i, p in enumerate(points):
        if not isinstance(p, dict):
            raise ServiceError(f"point {i} must be a mapping, got {type(p).__name__}")
        encoded = encode_point(
            body_id=p["body_id"],
            frame_id=p["frame_id"],
            epoch=p["epoch"],
            latitude_deg=p["latitude_deg"],
            longitude_deg=p["longitude_deg"],
            uncertainty_m=p.get("uncertainty_m"),
            height_m=p.get("height_m"),
            shell_state=p.get("shell_state"),
            codec=codec,
            software_commit=software_commit,
        )
        try:
            epoch_num = float(encoded["epoch"])
        except (TypeError, ValueError):
            epoch_num = 0.0
        receipts.append(AuditReceipt(
            receipt_id=f"encode-{i}",
            receipt_type=ReceiptType.DECODE_RECEIPT,
            epoch=epoch_num,
            content={
                "vector": encoded["vector"],
                "codec_id": encoded["codec_id"],
                "crs": encoded["crs"],
                "epoch": encoded["epoch"],
                "claim_class": encoded["claim_class"],
            },
        ))
    try:
        bundle = build_audit_bundle(receipts, software_commit=software_commit)
    except Exception as exc:  # privacy refusal, schema error, ...
        raise ServiceError(str(exc)) from exc
    out = bundle.to_dict()
    out["operation"] = "export"
    return out


def verify_vector(vector) -> dict:
    """Verify a canonical vector: checksum integrity plus a decode attempt.

    Returns a typed ``dict`` -- ``checksum_ok`` reports whether the checksum
    still binds the payload, and ``decode`` is the full :func:`decode_vector`
    result. Never raises.
    """
    checksum_ok = False
    if isinstance(vector, str) and vector:
        try:
            checksum_ok = checksums.verify_vector(vector)
        except Exception:
            checksum_ok = False
    decoded = decode_vector(vector)
    return _boundary({
        "operation": "verify",
        "vector": vector if isinstance(vector, str) else None,
        "checksum_ok": checksum_ok,
        "valid": bool(checksum_ok and decoded.get("status") == "OK_POINT"),
        "decode": decoded,
        "claim_class": decoded.get("claim_class"),
    })


def service_report() -> dict:
    """P57 declaration receipt. What the service layer is -- and is not."""
    return {
        "module": "cwatlas.service",
        "phase_id": PHASE_ID,
        "tranche": TRANCHE,
        "framework_agnostic": True,
        "web_framework_imported": "none (FastAPI/Flask NOT a dependency)",
        "operations": [
            "encode_point", "decode_vector", "legacy_search", "round_trip",
            "export_bundle", "verify_vector",
        ],
        "supported_codecs": list(SUPPORTED_CODECS),
        "every_result_carries": ["crs", "epoch", "claim_class"],
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_SERVICE_LAYER_FRAMEWORK_AGNOSTIC_CRS_EPOCH_CLAIM_CLASS",
        "what_this_does_not_say": (
            "The service is a governed facade over the reversible codecs and the "
            "legacy candidate search. A canonical round-trip is a property of "
            "the codec; a legacy search is an alias set or a refusal; no source "
            "vector is promoted to a geographic fact."),
    }
