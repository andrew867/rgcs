"""P13 — Spherical icosahedron construction (CW-HCM-ICO-1 base grid).

A numerically stable, fully deterministic 20-face spherical icosahedron built
from the golden ratio. The 12 vertices lie on the unit sphere; the 30 edges
and 20 faces are derived combinatorially and given a stable numbering that does
not depend on run order, floating-point tie-breaks, or platform.

This is a MATHEMATICAL_TRANSLATION at the SOFTWARE level: it is a geometric
data structure. It asserts nothing geographic. A face id is a cell of a
synthetic tessellation, not a place. See :mod:`cwatlas.claims`.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import numpy as np

from cwatlas import claims

#: Codec identity for the icosahedral base grid.
CODEC_ID = "CW-HCM-ICO-1"
CODEC_VERSION = "1.0.0"

#: The golden ratio, phi = (1 + sqrt(5)) / 2. Kept as an exact construction of
#: the icosahedron vertices; the decimal is derived, never hand-typed.
GOLDEN_RATIO = (1.0 + np.sqrt(5.0)) / 2.0

#: Counts fixed by the regular icosahedron (V - E + F = 2).
NUM_VERTICES = 12
NUM_EDGES = 30
NUM_FACES = 20

#: Tolerance used when comparing squared distances to classify edges. The
#: gap between the icosahedral edge length and the next chord is large, so a
#: modest absolute tolerance is unambiguous.
_EDGE_TOL = 1e-9


def _base_vertices() -> np.ndarray:
    """Return the 12 icosahedron vertices as unit vectors, deterministically.

    The vertices are the cyclic sign permutations of ``(0, +-1, +-phi)``. We
    generate the full set, sort it lexicographically for a stable order that is
    independent of construction order, then project onto the unit sphere.
    """
    phi = GOLDEN_RATIO
    raw: list[tuple[float, float, float]] = []
    for s1 in (-1.0, 1.0):
        for s2 in (-1.0, 1.0):
            raw.append((0.0, s1 * 1.0, s2 * phi))
            raw.append((s1 * 1.0, s2 * phi, 0.0))
            raw.append((s1 * phi, 0.0, s2 * 1.0))
    # Deterministic lexicographic ordering: rounding the key removes any
    # sign-of-zero or last-bit noise from the ordering decision only.
    raw_sorted = sorted(raw, key=lambda v: (round(v[0], 12), round(v[1], 12),
                                            round(v[2], 12)))
    arr = np.array(raw_sorted, dtype=np.float64)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    return arr / norms


@dataclass(frozen=True)
class Icosahedron:
    """A spherical icosahedron with a stable combinatorial numbering.

    Attributes
    ----------
    vertices:
        ``(12, 3)`` unit vectors, in the deterministic base order.
    edges:
        ``(30,)`` tuple of ``(i, j)`` vertex-index pairs, ``i < j``, sorted.
    faces:
        ``(20,)`` tuple of ``(i, j, k)`` vertex-index triples, ``i < j < k``,
        sorted. The face index into this tuple is the stable face id ``0..19``.
    """

    vertices: np.ndarray
    edges: tuple[tuple[int, int], ...]
    faces: tuple[tuple[int, int, int], ...]

    @property
    def face_normals(self) -> np.ndarray:
        """Unit outward normal (== unit centroid direction) per face."""
        v = self.vertices
        cent = np.array([v[list(f)].mean(axis=0) for f in self.faces],
                        dtype=np.float64)
        return cent / np.linalg.norm(cent, axis=1, keepdims=True)

    def euler_characteristic(self) -> int:
        """V - E + F. Must equal 2 for a sphere."""
        return len(self.vertices) - len(self.edges) + len(self.faces)


def build_icosahedron() -> Icosahedron:
    """Construct the deterministic spherical icosahedron.

    Edges are the vertex pairs at the minimal chord length; faces are the
    vertex triples whose three pairs are all edges. Both are sorted so the
    numbering is identical across runs and platforms.
    """
    verts = _base_vertices()
    n = len(verts)

    # Squared pairwise distances; the minimum is the edge length.
    d2 = np.zeros((n, n), dtype=np.float64)
    for i, j in combinations(range(n), 2):
        diff = verts[i] - verts[j]
        d2[i, j] = d2[j, i] = float(diff @ diff)
    min_d2 = min(d2[i, j] for i, j in combinations(range(n), 2))

    adj = [[False] * n for _ in range(n)]
    edges: list[tuple[int, int]] = []
    for i, j in combinations(range(n), 2):
        if abs(d2[i, j] - min_d2) <= _EDGE_TOL:
            adj[i][j] = adj[j][i] = True
            edges.append((i, j))
    edges.sort()

    faces: list[tuple[int, int, int]] = []
    for i, j, k in combinations(range(n), 3):
        if adj[i][j] and adj[j][k] and adj[i][k]:
            faces.append((i, j, k))
    faces.sort()

    verts.flags.writeable = False
    return Icosahedron(vertices=verts, edges=tuple(edges), faces=tuple(faces))


def _as_unit_vector(point) -> np.ndarray:
    """Validate and normalize a direction. Refuse degenerate input."""
    p = np.asarray(point, dtype=np.float64).reshape(-1)
    if p.shape != (3,):
        raise ValueError("point must be a 3-vector")
    if not np.all(np.isfinite(p)):
        raise ValueError("point must be finite")
    norm = float(np.linalg.norm(p))
    if norm < 1e-15:
        raise ValueError("point must be a non-zero direction on the sphere")
    return p / norm


def classify_point(ico: Icosahedron, point) -> int:
    """Return the face id ``0..19`` whose spherical triangle contains ``point``.

    The radial ray from the origin through ``point`` exits a regular
    icosahedron through exactly one face. Because all faces are congruent and
    equidistant, that face is the one whose unit centroid direction is closest
    to the direction of ``point`` (nearest-centre == spherical-triangle
    membership, the Voronoi boundary being the shared edge arc). Ties on an
    edge are resolved to the lowest face id, so the result is single-valued.
    """
    p = _as_unit_vector(point)
    dots = ico.face_normals @ p
    return int(np.argmax(dots))


def face_area(ico: Icosahedron, face_id: int) -> float:
    """Spherical-triangle area (steradians) of a face on the unit sphere.

    Uses the Van Oosterom-Strackee solid-angle formula, which is numerically
    stable for the small, well-conditioned icosahedral triangles.
    """
    if not 0 <= face_id < len(ico.faces):
        raise ValueError(f"face_id out of range: {face_id!r}")
    i, j, k = ico.faces[face_id]
    a, b, c = ico.vertices[i], ico.vertices[j], ico.vertices[k]
    triple = abs(float(a @ np.cross(b, c)))
    denom = 1.0 + float(a @ b) + float(b @ c) + float(c @ a)
    return 2.0 * float(np.arctan2(triple, denom))


def total_area(ico: Icosahedron) -> float:
    """Sum of all face areas; equals 4*pi for the closed unit sphere."""
    return float(sum(face_area(ico, f) for f in range(len(ico.faces))))


def icosahedron_report() -> dict:
    """Governance report: what this module is and, emphatically, is not."""
    ico = build_icosahedron()
    return {
        "phase": "P13",
        "what_this_is": (
            "a deterministic 20-face spherical icosahedron (CW-HCM-ICO-1 base "
            "grid) built from the golden ratio"),
        "codec_id": CODEC_ID,
        "codec_version": CODEC_VERSION,
        "counts": {
            "vertices": len(ico.vertices),
            "edges": len(ico.edges),
            "faces": len(ico.faces),
        },
        "euler_characteristic": ico.euler_characteristic(),
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_ICOSAHEDRON_DETERMINISTIC_NO_GEO_CLAIM",
        "what_this_does_not_say": (
            "A face id is a cell of a synthetic tessellation, not a place. No "
            "geographic or extraterrestrial meaning is asserted from the grid "
            "geometry."),
    }
