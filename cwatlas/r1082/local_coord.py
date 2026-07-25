"""P16 — Barycentric local coordinate and profile-specific inverse.

The locked local coordinate is **barycentric** (Locked Decision 12). This
module gives the terminal-cell barycentric coordinate of a point and the
profile-specific **inverse** that maps a point back to a five-token base-100
route under a named spatialization family (P15). It reuses the engine's
:mod:`cwatlas.addressing` / :mod:`cwatlas.subdivision` / :mod:`cwatlas.localize`
primitives — no geometry is reimplemented.

Two directions:

* :func:`forward` — ``(route, family) -> point``. The route names a terminal
  cell; its representative point is the cell centroid. Deterministic.
* :func:`inverse` — ``point -> (route, family)``. The point is encoded to the
  family's address, then the family's arithmetic inverse recovers the route.
  Because the source route core is **quantized** (a finite five-token grid),
  an arbitrary point is generally *not* exactly representable. The inverse
  therefore returns the **nearest encodable point** (the recovered route's
  centroid) and does **not** claim exactness unless the residual is within
  tolerance — no invented precision.

A recovered route is a ``CALIBRATED_CANDIDATE`` at most: a software result under
a declared family, never a measured fact, and it validates no source origin.
See :mod:`cwatlas.r1082.claims`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cwatlas.addressing import barycentric, encode_path, face_triangle
from cwatlas.icosahedron import Icosahedron, build_icosahedron
from cwatlas.localize import cell_centroid, localize_cell
from cwatlas.r1082 import claims as r1082_claims
from cwatlas.r1082.spatialization import (
    PATH_DEPTH,
    SpatializationFamily,
    get_family,
)

LOCAL_CODEC_ID = "CW-R1082-LOCALCOORD"
LOCAL_CODEC_VERSION = "1.0.0"

#: A point whose nearest encodable centroid is within this chord distance is
#: treated as *exactly* encodable (a route centroid fed straight back in).
_EXACT_TOL = 1e-9

#: A barycentric coordinate within this of 0 puts the point on a cell edge;
#: two near-zero coordinates put it near a vertex. Then the local coordinate is
#: reported as an interval/region, not a crisp point (required work #3).
_BOUNDARY_TOL = 1e-6


def _resolve_family(family) -> SpatializationFamily:
    if isinstance(family, SpatializationFamily):
        return family
    if isinstance(family, str):
        return get_family(family)
    raise TypeError(
        "family must be a SpatializationFamily or its name string")


def _unit(point) -> np.ndarray:
    p = np.asarray(point, dtype=np.float64).reshape(-1)
    if p.shape != (3,) or not np.all(np.isfinite(p)):
        raise ValueError("point must be a finite 3-vector")
    n = float(np.linalg.norm(p))
    if n < 1e-15:
        raise ValueError("point must be a non-zero direction")
    return p / n


@dataclass(frozen=True)
class LocalCoordinate:
    """Barycentric local coordinate of a point within its terminal cell.

    Attributes
    ----------
    face_id, path:
        The address whose cell contains the point (depth :data:`PATH_DEPTH`).
    bary:
        ``(u, v, w)`` barycentric coordinate within the terminal cell.
    on_edge, on_vertex:
        Whether the point sits within :data:`_BOUNDARY_TOL` of a cell edge /
        vertex (ambiguity becomes a region, not invented precision).
    interval:
        ``None`` for an interior point, else ``(min_coord, max_coord)`` of the
        barycentric coordinates — the reported region near a boundary.
    """

    face_id: int
    path: tuple[int, ...]
    bary: tuple[float, float, float]
    on_edge: bool
    on_vertex: bool
    interval: tuple[float, float] | None


@dataclass(frozen=True)
class InverseResult:
    """The profile-specific inverse of a point to a route (P16 inverse).

    Attributes
    ----------
    family_name:
        The spatialization family the inverse was taken under.
    route:
        The recovered five-token base-100 route (the candidate).
    face_id, path:
        The address the point encoded to.
    nearest_point:
        ``(3,)`` unit direction of the recovered route's cell centroid — the
        nearest encodable point to the query.
    residual:
        Chord distance between the query direction and ``nearest_point``.
    exact:
        ``True`` only when ``residual <= _EXACT_TOL``; otherwise the point was
        not exactly representable and exactness is **not** claimed.
    result_class:
        The result class (``CANDIDATE_CALIBRATED_POINT``).
    """

    family_name: str
    route: tuple[int, ...]
    face_id: int
    path: tuple[int, ...]
    nearest_point: np.ndarray
    residual: float
    exact: bool
    result_class: str


def forward(route, family, *, ico: Icosahedron | None = None) -> np.ndarray:
    """``(route, family) -> point``: the route's terminal-cell centroid."""
    fam = _resolve_family(family)
    if ico is None:
        ico = build_icosahedron()
    sp = fam.map_route(route, ico=ico)
    return sp.centroid


def local_barycentric(point, *, ico: Icosahedron | None = None,
                     depth: int = PATH_DEPTH) -> LocalCoordinate:
    """Barycentric local coordinate of ``point`` within its terminal cell.

    Reuses the engine's scale-invariant barycentric on the localized cell.
    Near an edge or vertex the coordinate is reported as an interval/region.
    """
    if ico is None:
        ico = build_icosahedron()
    p = _unit(point)
    addr = encode_path(ico, p, depth)
    loc = localize_cell(ico, addr.face_id, addr.path)
    u, v, w = barycentric(loc.cell, p)
    coords = (u, v, w)
    near_zero = [abs(c) <= _BOUNDARY_TOL for c in coords]
    on_edge = any(near_zero)
    on_vertex = sum(near_zero) >= 2
    interval = (min(coords), max(coords)) if on_edge else None
    return LocalCoordinate(
        face_id=addr.face_id,
        path=addr.path,
        bary=(u, v, w),
        on_edge=on_edge,
        on_vertex=on_vertex,
        interval=interval,
    )


def inverse(point, family, *, ico: Icosahedron | None = None) -> InverseResult:
    """``point -> (route, family)`` with a nearest-encodable-point (P16 inverse).

    Encodes the point to the family's address at :data:`PATH_DEPTH`, inverts the
    family's arithmetic to recover the route, then reports the recovered route's
    centroid as the nearest encodable point. Exactness is claimed only when the
    query already sits on that centroid (within :data:`_EXACT_TOL`).
    """
    fam = _resolve_family(family)
    if ico is None:
        ico = build_icosahedron()
    p = _unit(point)
    addr = encode_path(ico, p, PATH_DEPTH)
    route = fam.route_of_address(addr.face_id, addr.path)
    # Nearest encodable point: the recovered route's own centroid.
    sp = fam.map_route(route, ico=ico)
    nearest = sp.centroid
    residual = float(np.linalg.norm(p - nearest))
    exact = residual <= _EXACT_TOL
    return InverseResult(
        family_name=fam.name,
        route=route,
        face_id=addr.face_id,
        path=addr.path,
        nearest_point=nearest,
        residual=residual,
        exact=exact,
        result_class=r1082_claims.ResultClass.CANDIDATE_CALIBRATED_POINT.value,
    )


def local_coord_report() -> dict:
    """Governance report for the local coordinate and inverse."""
    return {
        "phase": "P16",
        "tranche": "T04",
        "what_this_is": (
            "barycentric local coordinate plus the profile-specific inverse: "
            "forward (route, family) -> point and inverse point -> (route, "
            "family) with a nearest-encodable-point where the quantized source "
            "codec cannot represent the point exactly"),
        "codec_id": LOCAL_CODEC_ID,
        "codec_version": LOCAL_CODEC_VERSION,
        "local_coordinate": "BARYCENTRIC",
        "path_depth": PATH_DEPTH,
        "exact_tolerance": _EXACT_TOL,
        "boundary_tolerance": _BOUNDARY_TOL,
        "nearest_encodable_when_quantized": True,
        "reused_engine": (
            "cwatlas.addressing / cwatlas.subdivision / cwatlas.localize "
            "(NOT reimplemented)"),
        "evidence_class": r1082_claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        "max_evidence": r1082_claims.MAX_CANDIDATE_EVIDENCE.value,
        "result_class": r1082_claims.ResultClass.CANDIDATE_CALIBRATED_POINT.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_BARYCENTRIC_LOCAL_COORD_INVERSE_NEAREST_ENCODABLE",
        "what_this_does_not_say": (
            "A recovered route is a CALIBRATED_CANDIDATE under a declared "
            "family, not a measured fact. Where the quantized source codec "
            "cannot represent a point exactly, the nearest encodable point is "
            "returned and exactness is not claimed; no source origin is "
            "validated."),
    }
