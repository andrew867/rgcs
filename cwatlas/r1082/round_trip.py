"""P23 — Profile-specific round trip and nearest-encodable point.

This phase *proves* the forward and inverse geocoders are consistent — without
claiming exactness where the source codec is quantized. It separates two round
trips that must never be conflated:

* **Canonical exact round trip** — ``route -> point -> route`` through the codec
  alone (no orientation, no shell). A declared canonical address round-trips
  exactly; this is a ``CANONICAL_EXACT_POINT`` property of the codec, a
  ``DERIVED_MATHEMATICS`` fact, not a measured coordinate.
* **Source-style calibrated round trip** — ``route -> body location -> route``
  through the frozen profile's fitted orientation and the shell. This is a
  ``CANDIDATE_CALIBRATED_POINT``: a software result under a declared calibration.

For an **arbitrary** body point (a click that is not a route centroid) the
inverse returns the **nearest encodable point** and an explicit
``quantization_error`` (the residual chord distance). Near a terminal-cell edge
or vertex the local coordinate is reported as an **interval/region**, never a
false-exact point (reusing :func:`cwatlas.r1082.local_coord.local_barycentric`).

The **shell supplies the radius** throughout: with a shell present, altitude is
never "missing" — attempting to report it as missing is refused by
:func:`cwatlas.r1082.claims.refuse_altitude_missing_when_shell_present`.

Nothing here is measured; a recovered route is a ``CALIBRATED_CANDIDATE`` at
most and validates no source origin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from cwatlas.icosahedron import build_icosahedron
from cwatlas.r1082 import claims as _claims
from cwatlas.r1082 import local_coord, spatialization
from cwatlas.r1082.claims import ResultClass
from cwatlas.r1082.geocode_forward import (
    _frozen_orientation,
    geocentric_latlon_to_unit,
    safe_family_inverse,
    unit_to_geocentric_latlon,
)
from cwatlas.r1082.semantic_expand import (
    SHELL_MAX,
    SHELL_MIN,
    resolve_shell_radius_m,
)

MODULE_CODEC_ID = "CW-R1082-ROUNDTRIP"
MODULE_CODEC_VERSION = "1.0.0"

#: A residual at or below this chord distance is treated as exact (a route
#: centroid fed straight back in). Mirrors ``local_coord._EXACT_TOL``.
EXACT_TOL = local_coord._EXACT_TOL


@dataclass(frozen=True)
class RoundTripResult:
    """The outcome of one round trip, with its residual and result class."""

    kind: str                      # "CANONICAL_EXACT" | "SOURCE_STYLE_CALIBRATED"
    family_name: str
    route_in: tuple[int, ...]
    route_out: tuple[int, ...]
    exact: bool
    quantization_error: float
    result_type: str
    on_edge: bool = False
    on_vertex: bool = False
    interval: Optional[tuple[float, float]] = None
    shell: Optional[int] = None
    radius_m: Optional[float] = None

    def matches(self) -> bool:
        return self.route_in == self.route_out


@dataclass(frozen=True)
class NearestEncodable:
    """The nearest encodable point for an arbitrary (non-representable) click."""

    family_name: str
    query_latitude_deg: float
    query_longitude_deg: float
    route: tuple[int, ...]
    nearest_latitude_deg: float
    nearest_longitude_deg: float
    quantization_error: float
    exact: bool
    on_edge: bool
    on_vertex: bool
    interval: Optional[tuple[float, float]]
    shell: int
    radius_m: float
    result_type: str = field(
        default=ResultClass.CANDIDATE_CALIBRATED_POINT.value)


def canonical_exact_round_trip(route, family, *, ico=None) -> RoundTripResult:
    """``route -> point -> route`` through the codec alone (exact by construction)."""
    fam = spatialization.get_family(family) if isinstance(family, str) else family
    if ico is None:
        ico = build_icosahedron()
    point = local_coord.forward(route, fam, ico=ico)
    inv = local_coord.inverse(point, fam, ico=ico)
    return RoundTripResult(
        kind="CANONICAL_EXACT",
        family_name=fam.name,
        route_in=tuple(route),
        route_out=inv.route,
        exact=inv.exact,
        quantization_error=inv.residual,
        result_type=ResultClass.CANONICAL_EXACT_POINT.value,
    )


def source_style_round_trip(route, family, frozen_profile, *, shell: int = 3,
                            ico=None) -> RoundTripResult:
    """``route -> body location -> route`` through the fitted orientation + shell.

    A calibrated round trip: the frozen orientation is applied on the way out and
    inverted on the way back. Because the orientation is orthonormal it preserves
    the terminal cell, so a route recovers exactly — but the class is only a
    ``CANDIDATE_CALIBRATED_POINT`` (a software result), never canonical-exact.
    """
    if not SHELL_MIN <= shell <= SHELL_MAX:
        raise ValueError(f"shell {shell} out of range [{SHELL_MIN}, {SHELL_MAX}].")
    fam = spatialization.get_family(family) if isinstance(family, str) else family
    if ico is None:
        ico = build_icosahedron()
    orientation = _frozen_orientation(frozen_profile)
    radius_m = resolve_shell_radius_m(shell)  # shell supplies the radius

    cell_point = local_coord.forward(route, fam, ico=ico)
    root_point = orientation @ cell_point
    root_point = root_point / np.linalg.norm(root_point)
    lat, lon = unit_to_geocentric_latlon(root_point)

    # ... and back: body location -> cell frame -> route.
    back_root = geocentric_latlon_to_unit(lat, lon)
    back_cell = np.asarray(orientation, dtype=np.float64).T @ back_root
    inv = local_coord.inverse(back_cell, fam, ico=ico)
    return RoundTripResult(
        kind="SOURCE_STYLE_CALIBRATED",
        family_name=fam.name,
        route_in=tuple(route),
        route_out=inv.route,
        exact=inv.exact,
        quantization_error=inv.residual,
        result_type=ResultClass.CANDIDATE_CALIBRATED_POINT.value,
        shell=shell,
        radius_m=radius_m,
    )


def nearest_encodable_point(latitude_deg: float, longitude_deg: float, family,
                            frozen_profile=None, *, shell: int = 3, ico=None
                            ) -> NearestEncodable:
    """The nearest encodable source point for an arbitrary body click.

    An arbitrary click is generally NOT a route centroid, so exactness is not
    claimed: the residual chord distance is returned as ``quantization_error``.
    Near a cell edge/vertex the barycentric coordinate is reported as an
    interval (a region), not a false-exact point. The shell supplies the radius.
    """
    if not SHELL_MIN <= shell <= SHELL_MAX:
        raise ValueError(f"shell {shell} out of range [{SHELL_MIN}, {SHELL_MAX}].")
    fam = spatialization.get_family(family) if isinstance(family, str) else family
    if ico is None:
        ico = build_icosahedron()
    orientation = (_frozen_orientation(frozen_profile)
                   if frozen_profile is not None else np.eye(3))
    radius_m = resolve_shell_radius_m(shell)

    root_point = geocentric_latlon_to_unit(latitude_deg, longitude_deg)
    cell_point = np.asarray(orientation, dtype=np.float64).T @ root_point
    inv = safe_family_inverse(cell_point, fam, ico=ico)
    lc = local_coord.local_barycentric(cell_point, ico=ico)

    nearest_root = orientation @ inv.nearest_point
    nearest_root = nearest_root / np.linalg.norm(nearest_root)
    nlat, nlon = unit_to_geocentric_latlon(nearest_root)
    return NearestEncodable(
        family_name=fam.name,
        query_latitude_deg=float(latitude_deg),
        query_longitude_deg=float(longitude_deg),
        route=inv.route,
        nearest_latitude_deg=nlat, nearest_longitude_deg=nlon,
        quantization_error=inv.residual, exact=inv.exact,
        on_edge=lc.on_edge, on_vertex=lc.on_vertex, interval=lc.interval,
        shell=shell, radius_m=radius_m)


def assert_shell_supplies_radius(shell: int) -> float:
    """Confirm the shell supplies the radius; altitude is never missing.

    Returns the shell radius. A shell profile is always present here, so any
    attempt to report altitude as missing is refused by the locked-root rule.
    """
    if not SHELL_MIN <= shell <= SHELL_MAX:
        raise ValueError(f"shell {shell} out of range [{SHELL_MIN}, {SHELL_MAX}].")
    return resolve_shell_radius_m(shell)


def refuse_altitude_missing(shell: int) -> None:
    """Refuse a claim of missing altitude while a shell is present (guard)."""
    _claims.refuse_altitude_missing_when_shell_present(shell_state=shell)


def round_trip_report() -> dict:
    """P23 declaration receipt. Nearest-encodable; no false exactness."""
    return {
        "phase_id": "P23",
        "tranche": "T06",
        "what_this_is": (
            "the profile-specific round-trip prover: it separates the canonical "
            "exact route<->point<->route codec identity (CANONICAL_EXACT_POINT) "
            "from the source-style calibrated round trip through the fitted "
            "orientation and shell (CANDIDATE_CALIBRATED_POINT), and returns the "
            "nearest-encodable point plus an explicit quantization error for an "
            "arbitrary click — an interval/region near cell edges/vertices, "
            "never a false-exact point."),
        "codec_id": MODULE_CODEC_ID,
        "codec_version": MODULE_CODEC_VERSION,
        "reused_engine": (
            "cwatlas.r1082.local_coord (forward/inverse/local_barycentric) + "
            "spatialization; cwatlas.icosahedron (NOT reimplemented)"),
        "canonical_exact_vs_calibrated_separated": True,
        "nearest_encodable_when_quantized": True,
        "region_near_boundary_not_false_exact": True,
        "shell_supplies_radius": True,
        "altitude_missing_when_shell_present": "REFUSED",
        "exact_tolerance": EXACT_TOL,
        "evidence_class": _claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        "max_evidence": _claims.MAX_CANDIDATE_EVIDENCE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_ROUND_TRIP_NEAREST_ENCODABLE_NO_FALSE_EXACTNESS",
        "what_this_does_not_say": (
            "The canonical round trip is a mathematical property of the codec; "
            "the calibrated round trip is a software result under a declared "
            "calibration. Neither is a measured fact, and where the quantized "
            "source codec cannot represent a point exactly, exactness is not "
            "claimed. No source origin is validated."),
    }
