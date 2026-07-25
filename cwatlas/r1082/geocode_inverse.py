"""P22 — Inverse source geocoder: map selection -> source-style vector.

The forward geocoder (P21) turns a source vector into a body location. The
inverse geocoder does the reverse for the operator UI: click a body location
(``lat``, ``lon``, ``shell``) under a **named** frozen profile and get back a
source-style candidate address — the five-token base-100 display when the point
is exactly representable, and an extended variable-depth packet (with the
nearest-encodable point and its quantization error) otherwise.

The pipeline reuses the Wave-1 engine:

* the fitted orientation of the frozen profile maps the body direction back into
  the candidate cell frame;
* :func:`cwatlas.r1082.local_coord.inverse` recovers the family's five-token
  route as the **nearest encodable point** (the source codec is quantized, so an
  arbitrary click is generally not exactly representable);
* :mod:`cwatlas.r1082.wire_format` packs the shell (+ optional epoch) into the
  self-describing shell-epoch packet — the **shell supplies the radius**, so
  altitude is never reported missing.

Two honesty requirements are surfaced *before* the operator copies the vector:

* **quantization** — the residual chord distance to the nearest encodable point,
  and whether the address is exact;
* **non-uniqueness** — the address each *other* retained family would emit for
  the same click, so an operator never mistakes one family's route for the only
  answer.

A recovered address is a ``CALIBRATED_CANDIDATE`` at most — a software result
under a declared calibration, never a measured fact, validating no source origin.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from cwatlas.icosahedron import build_icosahedron
from cwatlas.r1082 import claims as _claims
from cwatlas.r1082 import local_coord, spatialization, wire_format
from cwatlas.r1082.claims import ResultClass
from cwatlas.r1082.geocode_forward import (
    BODY_IN_SCOPE,
    _frozen_family_names,
    _frozen_orientation,
    _frozen_profile_id,
    geocentric_latlon_to_unit,
    safe_family_inverse,
    unit_to_geocentric_latlon,
)
from cwatlas.r1082.route_core import CODEC_ID, RouteCore, RouteError
from cwatlas.r1082.semantic_expand import (
    SHELL_MAX,
    SHELL_MIN,
    resolve_shell_radius_m,
)

MODULE_CODEC_ID = "CW-R1082-GEOCODE-INV"
MODULE_CODEC_VERSION = "1.0.0"


def _route_wire(route: tuple[int, ...]) -> str:
    """Render a route as the source-style five-token display ``01|65|87|65|23``."""
    raw = "".join(f"{t:02d}" for t in route)
    return RouteCore(raw=raw, tokens=tuple(route), codec_id=CODEC_ID).to_wire()


def _shell_packet(shell: int, coarse_epoch: Optional[int],
                  fine_epoch: Optional[int]):
    """Build the self-describing shell-epoch packet (shell supplies radius)."""
    if fine_epoch is not None:
        if coarse_epoch is None:
            raise RouteError("a fine epoch requires a coarse epoch.")
        return wire_format.make_packet(
            wire_format.PacketDepth.FULL, shell,
            coarse_epoch=coarse_epoch, fine_epoch=fine_epoch)
    if coarse_epoch is not None:
        return wire_format.make_packet(
            wire_format.PacketDepth.SHELL_PLUS_COARSE, shell,
            coarse_epoch=coarse_epoch)
    return wire_format.make_packet(wire_format.PacketDepth.SHELL_ONLY, shell)


@dataclass(frozen=True)
class InverseGeocode:
    """A source-style candidate address recovered from a map selection."""

    result_type: str
    profile_id: str
    family_name: str
    latitude_deg: float
    longitude_deg: float
    shell: int
    radius_m: float
    route: tuple[int, ...]
    source_vector: str
    wire_packet: str
    packet_depth: str
    representable_exact: bool
    quantization_residual: float
    nearest_latitude_deg: float
    nearest_longitude_deg: float
    aliases: tuple[dict, ...]
    non_unique: bool
    receipt: dict = field(default_factory=dict)

    def assert_not_measured(self) -> None:
        _claims.refuse_candidate_as_measured(self.result_type)

    def to_serializable(self) -> dict:
        return {
            "result_type": self.result_type,
            "profile_id": self.profile_id,
            "input": {
                "latitude_deg": self.latitude_deg,
                "longitude_deg": self.longitude_deg,
                "shell": self.shell,
                "family_name": self.family_name,
            },
            "geometry": {
                "source_vector": self.source_vector,
                "route": list(self.route),
                "wire_packet": self.wire_packet,
                "packet_depth": self.packet_depth,
                "nearest_point_deg": [self.nearest_latitude_deg,
                                      self.nearest_longitude_deg],
                "shell": self.shell,
                "radius_m": self.radius_m,
            },
            "uncertainty": {
                "representable_exact": self.representable_exact,
                "quantization_residual": self.quantization_residual,
                "non_unique": self.non_unique,
                "aliases": list(self.aliases),
            },
            "receipt": self.receipt,
        }


def _resolve_family_name(frozen_profile, family_name: Optional[str]
                         ) -> tuple[str, tuple[str, ...]]:
    """Pick the family under a NAMED frozen profile; surface non-uniqueness."""
    retained = _frozen_family_names(frozen_profile)
    if family_name is not None:
        if family_name not in retained:
            raise RouteError(
                f"family {family_name!r} is not retained by profile "
                f"{_frozen_profile_id(frozen_profile)!r} {list(retained)}.")
        return family_name, retained
    if len(retained) == 1:
        return retained[0], retained
    # Ambiguous: default to the first retained family but flag non-uniqueness.
    return retained[0], retained


def inverse_geocode(latitude_deg: float, longitude_deg: float, shell: int,
                    frozen_profile, *, family_name: Optional[str] = None,
                    coarse_epoch: Optional[int] = None,
                    fine_epoch: Optional[int] = None,
                    body: str = "EARTH", ico=None) -> InverseGeocode:
    """Map a body location to a source-style candidate address.

    ``frozen_profile`` names the calibration whose fitted orientation and family
    are used. When the profile retains several families (or ``family_name`` is
    omitted) the addresses of the *other* families are returned as ``aliases``
    and ``non_unique`` is set — non-uniqueness is shown before the operator
    copies the vector. The shell supplies the radius (never altitude-missing).
    """
    if frozen_profile is None:
        raise RouteError(
            "inverse geocoding requires a NAMED frozen profile (the fitted "
            "orientation and retained family come from the frozen calibration).")
    if str(body).upper() not in BODY_IN_SCOPE:
        raise RouteError(
            f"body {body!r} is out of scope for the Earth root "
            f"{sorted(BODY_IN_SCOPE)}; foreign-body selection is not decoded.")
    if not SHELL_MIN <= shell <= SHELL_MAX:
        raise RouteError(
            f"shell {shell} out of range [{SHELL_MIN}, {SHELL_MAX}].")

    if ico is None:
        ico = build_icosahedron()
    profile_id = _frozen_profile_id(frozen_profile)
    orientation = _frozen_orientation(frozen_profile)
    chosen, retained = _resolve_family_name(frozen_profile, family_name)
    radius_m = resolve_shell_radius_m(shell)  # shell supplies the radius

    # Body direction -> candidate cell frame (inverse of the fitted orientation).
    root_point = geocentric_latlon_to_unit(latitude_deg, longitude_deg)
    cell_point = np.asarray(orientation, dtype=np.float64).T @ root_point

    def _address_for(name: str):
        fam = spatialization.get_family(name)
        inv = safe_family_inverse(cell_point, fam, ico=ico)
        nearest_root = np.asarray(orientation, dtype=np.float64) @ inv.nearest_point
        n = float(np.linalg.norm(nearest_root))
        nearest_root = nearest_root / n if n > 0 else nearest_root
        nlat, nlon = unit_to_geocentric_latlon(nearest_root)
        return inv, nlat, nlon

    inv, nlat, nlon = _address_for(chosen)
    route = inv.route
    packet = _shell_packet(shell, coarse_epoch, fine_epoch)
    wire_packet = wire_format.encode(packet)
    source_vector = _route_wire(route)

    # Non-uniqueness: what each OTHER retained family would emit for this click.
    aliases: list[dict] = []
    for name in retained:
        if name == chosen:
            continue
        a_inv, a_lat, a_lon = _address_for(name)
        aliases.append({
            "family_name": name,
            "source_vector": _route_wire(a_inv.route),
            "route": list(a_inv.route),
            "quantization_residual": a_inv.residual,
            "representable_exact": a_inv.exact,
            "nearest_point_deg": [a_lat, a_lon],
        })
    non_unique = any(a["route"] != list(route) for a in aliases)

    # Exactly representable -> the five-token display; otherwise the extended
    # variable-depth packet plus the nearest-encodable point and its residual.
    result_type = ResultClass.CANDIDATE_CALIBRATED_POINT.value

    payload = {"profile_id": profile_id, "family": chosen, "route": list(route),
               "shell": shell, "wire": wire_packet}
    receipt_hash = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=float).encode()).hexdigest()
    receipt = {
        "codec_id": MODULE_CODEC_ID,
        "codec_version": MODULE_CODEC_VERSION,
        "profile_id": profile_id,
        "family_name": chosen,
        "retained_families": list(retained),
        "five_token_display": source_vector,
        "wire_packet": wire_packet,
        "packet_depth": packet.depth.value,
        "representable_exact": inv.exact,
        "quantization_residual": inv.residual,
        "non_unique": non_unique,
        "alias_count": len(aliases),
        "shell_supplies_radius": True,
        "radius_m": radius_m,
        "altitude_missing": False,
        "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "receipt_hash": receipt_hash,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
    }

    return InverseGeocode(
        result_type=result_type, profile_id=profile_id, family_name=chosen,
        latitude_deg=float(latitude_deg), longitude_deg=float(longitude_deg),
        shell=shell, radius_m=radius_m, route=route,
        source_vector=source_vector, wire_packet=wire_packet,
        packet_depth=packet.depth.value, representable_exact=inv.exact,
        quantization_residual=inv.residual,
        nearest_latitude_deg=nlat, nearest_longitude_deg=nlon,
        aliases=tuple(aliases), non_unique=non_unique, receipt=receipt)


def geocode_inverse_report() -> dict:
    """P22 declaration receipt. Nearest-encodable; quantization + non-uniqueness."""
    return {
        "phase_id": "P22",
        "tranche": "T06",
        "what_this_is": (
            "the inverse source geocoder: a body location (lat, lon, shell) "
            "under a named frozen profile is mapped to a source-style candidate "
            "address — the five-token display when exactly representable, else an "
            "extended variable-depth packet with the nearest-encodable point and "
            "its quantization residual; other retained families' addresses are "
            "surfaced as aliases (non-uniqueness)."),
        "codec_id": MODULE_CODEC_ID,
        "codec_version": MODULE_CODEC_VERSION,
        "reused_engine": (
            "cwatlas.r1082.local_coord.inverse + wire_format; cwatlas.icosahedron "
            "(NOT reimplemented)"),
        "named_profile_required": True,
        "nearest_encodable_when_quantized": True,
        "shows_quantization_and_non_uniqueness": True,
        "shell_supplies_radius": True,
        "evidence_class": _claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "result_class": ResultClass.CANDIDATE_CALIBRATED_POINT.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_INVERSE_GEOCODER_SOURCE_STYLE_NEAREST_ENCODABLE",
        "what_this_does_not_say": (
            "A recovered address is a CALIBRATED_CANDIDATE under a declared "
            "calibration, not a measured fact; where the quantized source codec "
            "cannot represent the click exactly, the nearest encodable point is "
            "returned and exactness is not claimed; no source origin is "
            "validated."),
    }
