"""P15 — Barycentric coordinates and one-to-eight refinement primitives.

Two reusable primitives for the recursive icosahedral path codec (the octal
"8-way path" of CW-HCM-ICO-1, chained twelve deep by a later phase):

1. **Local barycentric coordinates** on a spherical triangle, with an exact
   point <-> barycentric round-trip (radial projection onto the triangle
   plane, then affine barycentric, and back onto the sphere).

2. **One-to-eight refinement**. A triangle is split into 4 by its edge
   midpoints, and each of those 4 sub-triangles is bisected by the median from
   its anchor vertex, giving 8 children that tile the parent exactly. The child
   index is octal (``0..7``); locating a point returns the child whose
   sub-triangle contains it, and this is the exact inverse of refinement.

MATHEMATICAL_TRANSLATION / SOFTWARE level. A child index is a cell selector in
a synthetic tessellation, not a place. See :mod:`cwatlas.claims`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cwatlas import claims

CODEC_ID = "CW-HCM-ICO-1"
CODEC_VERSION = "1.0.0"

#: Octal branching factor of the refinement.
CHILDREN_PER_NODE = 8
MAX_CHILD_INDEX = CHILDREN_PER_NODE - 1

_SUM_TOL = 1e-9
_INSIDE_TOL = 1e-9
_DEGEN_TOL = 1e-12


@dataclass(frozen=True)
class SphericalTriangle:
    """Three unit-vector corners of a triangular cell on the unit sphere."""

    a: np.ndarray
    b: np.ndarray
    c: np.ndarray

    @staticmethod
    def of(a, b, c) -> "SphericalTriangle":
        """Build from three directions, normalizing and refusing degeneracy."""
        va, vb, vc = (_unit(a, "a"), _unit(b, "b"), _unit(c, "c"))
        normal = np.cross(vb - va, vc - va)
        if float(np.linalg.norm(normal)) < _DEGEN_TOL:
            raise ValueError("degenerate triangle: corners are collinear")
        return SphericalTriangle(va, vb, vc)

    def corners(self) -> np.ndarray:
        """``(3, 3)`` array of the three unit corners."""
        return np.array([self.a, self.b, self.c], dtype=np.float64)


def _unit(vec, name: str) -> np.ndarray:
    v = np.asarray(vec, dtype=np.float64).reshape(-1)
    if v.shape != (3,):
        raise ValueError(f"{name} must be a 3-vector")
    if not np.all(np.isfinite(v)):
        raise ValueError(f"{name} must be finite")
    n = float(np.linalg.norm(v))
    if n < 1e-15:
        raise ValueError(f"{name} must be a non-zero direction")
    return v / n


def to_barycentric(tri: SphericalTriangle, point) -> tuple[float, float, float]:
    """Barycentric ``(u, v, w)`` of ``point`` on the triangle's plane.

    The point is radially projected from the origin onto the plane of the
    triangle, then expressed in the affine barycentric basis of the corners.
    ``u + v + w == 1`` by construction. A direction parallel to the triangle
    plane (no radial intersection) is a refusal.
    """
    p = _unit(point, "point")
    a, b, c = tri.a, tri.b, tri.c
    normal = np.cross(b - a, c - a)
    denom = float(normal @ p)
    if abs(denom) < _DEGEN_TOL:
        raise ValueError(
            "refused: direction does not radially intersect the triangle "
            "plane (grazing / parallel).")
    t = float(normal @ a) / denom
    planar = t * p
    return _planar_barycentric(a, b, c, planar)


def _planar_barycentric(a, b, c, p) -> tuple[float, float, float]:
    v0, v1, v2 = b - a, c - a, p - a
    d00 = float(v0 @ v0)
    d01 = float(v0 @ v1)
    d11 = float(v1 @ v1)
    d20 = float(v2 @ v0)
    d21 = float(v2 @ v1)
    det = d00 * d11 - d01 * d01
    if abs(det) < _DEGEN_TOL:
        raise ValueError("refused: degenerate triangle basis")
    v = (d11 * d20 - d01 * d21) / det
    w = (d00 * d21 - d01 * d20) / det
    u = 1.0 - v - w
    return (u, v, w)


def from_barycentric(tri: SphericalTriangle, bary) -> np.ndarray:
    """Unit direction for barycentric ``(u, v, w)``; refuse if not a partition.

    Coordinates must sum to 1 within tolerance (they may be negative, denoting
    a point outside the triangle but still on its plane). The reconstructed
    direction is normalized back onto the sphere.
    """
    b = np.asarray(bary, dtype=np.float64).reshape(-1)
    if b.shape != (3,):
        raise ValueError("bary must be a 3-vector (u, v, w)")
    if not np.all(np.isfinite(b)):
        raise ValueError("bary must be finite")
    if abs(float(b.sum()) - 1.0) > _SUM_TOL:
        raise ValueError(
            f"refused: barycentric coordinates must sum to 1, got {float(b.sum())!r}")
    point = b[0] * tri.a + b[1] * tri.b + b[2] * tri.c
    n = float(np.linalg.norm(point))
    if n < 1e-15:
        raise ValueError("refused: barycentric combination collapsed to origin")
    return point / n


# Quadrant vertices in parent-barycentric coordinates. Each quadrant is
# (P, Q, R); the anchor P is listed first and the median P->mid(Q, R) bisects
# it into child 0 (the Q side) and child 1 (the R side).
_A = (1.0, 0.0, 0.0)
_B = (0.0, 1.0, 0.0)
_C = (0.0, 0.0, 1.0)
_MAB = (0.5, 0.5, 0.0)
_MBC = (0.0, 0.5, 0.5)
_MCA = (0.5, 0.0, 0.5)
_QUADRANTS = (
    (_A, _MAB, _MCA),    # near a
    (_MAB, _B, _MBC),    # near b
    (_MCA, _MBC, _C),    # near c
    (_MAB, _MBC, _MCA),  # central
)


def _child_bary_triangles() -> list[tuple[tuple, tuple, tuple]]:
    """The 8 child triangles as parent-barycentric vertex triples, index 0..7."""
    out: list[tuple[tuple, tuple, tuple]] = []
    for (P, Q, R) in _QUADRANTS:
        P, Q, R = np.array(P), np.array(Q), np.array(R)
        mqr = (Q + R) / 2.0
        out.append((tuple(P), tuple(Q), tuple(mqr)))   # child .0 : Q side
        out.append((tuple(P), tuple(mqr), tuple(R)))   # child .1 : R side
    return out


def refine(tri: SphericalTriangle) -> tuple[SphericalTriangle, ...]:
    """Return the 8 child spherical triangles, tiling the parent, index 0..7."""
    children: list[SphericalTriangle] = []
    for (pP, pQ, pR) in _child_bary_triangles():
        va = from_barycentric(tri, pP)
        vb = from_barycentric(tri, pQ)
        vc = from_barycentric(tri, pR)
        children.append(SphericalTriangle.of(va, vb, vc))
    return tuple(children)


def child(tri: SphericalTriangle, index: int) -> SphericalTriangle:
    """Return a single child triangle by octal index ``0..7``."""
    if not isinstance(index, int) or isinstance(index, bool):
        raise TypeError("child index must be a plain int")
    if not 0 <= index <= MAX_CHILD_INDEX:
        raise ValueError(f"refused: child index must be in 0..7, got {index!r}")
    return refine(tri)[index]


def child_index(tri: SphericalTriangle, point) -> int:
    """Octal index ``0..7`` of the child sub-triangle containing ``point``.

    Exact inverse of :func:`refine`: for the centroid of child ``i`` the result
    is ``i``. A point outside the parent triangle is a refusal.
    """
    u, v, w = to_barycentric(tri, point)
    if min(u, v, w) < -_INSIDE_TOL:
        raise ValueError(
            f"refused: point is outside the triangle (bary={u:.6g},{v:.6g},{w:.6g})")

    if u >= 0.5:
        quad = 0
    elif v >= 0.5:
        quad = 1
    elif w >= 0.5:
        quad = 2
    else:
        quad = 3

    pb = np.array([u, v, w], dtype=np.float64)
    P, Q, R = (np.array(x, dtype=np.float64) for x in _QUADRANTS[quad])
    # Local barycentric within the quadrant (least-squares on the 2 free axes).
    mat = np.array([Q - P, R - P], dtype=np.float64).T  # (3, 2)
    lq, lr = np.linalg.lstsq(mat, pb - P, rcond=None)[0]
    half = 0 if lq >= lr else 1
    return quad * 2 + half


def subdivision_report() -> dict:
    """Governance report for the subdivision primitives."""
    return {
        "phase": "P15",
        "what_this_is": (
            "local barycentric coordinates on a spherical triangle plus a "
            "one-to-eight (octal) refinement that tiles and inverts exactly"),
        "codec_id": CODEC_ID,
        "codec_version": CODEC_VERSION,
        "children_per_node": CHILDREN_PER_NODE,
        "child_index_range": [0, MAX_CHILD_INDEX],
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_SUBDIVISION_ROUND_TRIP_OCTAL_NO_GEO_CLAIM",
        "what_this_does_not_say": (
            "A barycentric coordinate and a child index are positions within a "
            "synthetic tessellation. No geographic meaning is asserted."),
    }
