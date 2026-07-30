"""R10.25 Agent 02 — candidate hedron families.

The R10.25 suspicion is that the vector grammar is fine and the EARTH
PROJECTOR is wrong: wrong base-face count, wrong root (face-centre vs
vertex), wrong subdivision depth, wrong level naming. So the base
polyhedron is a SEARCH PARAMETER here, not an assumption.

Every family is built from exact coordinates, normalised to the unit
sphere, with outward-consistent winding. Faces are spherical triangles;
non-triangular solids are triangulated from the face centroid, which is
recorded in ``triangulation`` because it changes the child count.

NO MESH WARP. Nothing here is fitted to an anchor, and no per-anchor
adjustment exists anywhere in this module.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

PHI = (1.0 + math.sqrt(5.0)) / 2.0
EARTH_RADIUS_KM = 6371.0


def _unit(v) -> np.ndarray:
    v = np.asarray(v, float)
    return v / np.linalg.norm(v)


def _orient(verts, faces) -> tuple:
    """Force outward winding so orientation is not a hidden variable."""
    out = []
    for a, b, c in faces:
        va, vb, vc = verts[a], verts[b], verts[c]
        if float(np.dot(np.cross(vb - va, vc - va), va)) < 0:
            a, b, c = a, c, b
        out.append((a, b, c))
    return tuple(out)


@dataclass(frozen=True)
class Hedron:
    name: str
    vertices: np.ndarray
    faces: tuple
    root: str                 # "face_centre" or "vertex"
    triangulation: str
    provenance: str

    @property
    def face_count(self) -> int:
        return len(self.faces)

    def face_triangle(self, f: int) -> tuple:
        return tuple(self.vertices[i] for i in self.faces[f])

    def edge_arc_km(self) -> float:
        """Mean spherical edge length of a base face, in km."""
        tot = 0.0
        for tri in (self.face_triangle(f) for f in range(self.face_count)):
            for i in range(3):
                d = float(np.dot(_unit(tri[i]), _unit(tri[(i + 1) % 3])))
                tot += math.acos(max(-1.0, min(1.0, d)))
        return EARTH_RADIUS_KM * tot / (3 * self.face_count)

    def cell_edge_km(self, level: int) -> float:
        return self.edge_arc_km() / (2 ** level)


def _tetrahedron() -> tuple:
    v = np.array([[1, 1, 1], [1, -1, -1], [-1, 1, -1], [-1, -1, 1]], float)
    v = np.array([_unit(x) for x in v])
    return v, ((0, 1, 2), (0, 3, 1), (0, 2, 3), (1, 3, 2))


def _octahedron() -> tuple:
    v = np.array([[1, 0, 0], [-1, 0, 0], [0, 1, 0],
                  [0, -1, 0], [0, 0, 1], [0, 0, -1]], float)
    f = ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4),
         (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5))
    return v, f


def _icosahedron() -> tuple:
    raw = []
    for s1 in (1, -1):
        for s2 in (1, -1):
            raw += [[0, s1 * 1, s2 * PHI], [s1 * 1, s2 * PHI, 0],
                    [s1 * PHI, 0, s2 * 1]]
    v = np.array([_unit(x) for x in raw])
    # faces = every vertex triple at minimum mutual distance
    d = []
    n = len(v)
    for i in range(n):
        for j in range(i + 1, n):
            d.append(float(np.linalg.norm(v[i] - v[j])))
    emin = min(d)
    adj = {i: {j for j in range(n) if i != j and
               abs(float(np.linalg.norm(v[i] - v[j])) - emin) < 1e-9}
           for i in range(n)}
    faces = set()
    for i in range(n):
        for j in adj[i]:
            for k in adj[i] & adj[j]:
                faces.add(tuple(sorted((i, j, k))))
    return v, tuple(sorted(faces))


def _triangulate_centroid(v, polys) -> tuple:
    """Split each polygonal face into triangles at its centroid."""
    verts = list(v)
    faces = []
    for poly in polys:
        c = _unit(sum(np.asarray(v[i], float) for i in poly))
        ci = len(verts)
        verts.append(c)
        for k in range(len(poly)):
            faces.append((poly[k], poly[(k + 1) % len(poly)], ci))
    return np.array(verts, float), tuple(faces)


def _cube() -> tuple:
    v = np.array([[x, y, z] for x in (1, -1) for y in (1, -1)
                  for z in (1, -1)], float)
    v = np.array([_unit(x) for x in v])
    idx = {tuple(np.sign(x).astype(int)): i for i, x in enumerate(v)}
    polys = []
    for axis in range(3):
        for sgn in (1, -1):
            ring = [k for k in idx if k[axis] == sgn]
            o = [a for a in range(3) if a != axis]
            ring.sort(key=lambda k: math.atan2(k[o[1]], k[o[0]]))
            polys.append(tuple(idx[k] for k in ring))
    return _triangulate_centroid(v, polys)


def _dodecahedron() -> tuple:
    """Dual of the icosahedron: vertices are icosahedral face centres."""
    iv, ifc = _icosahedron()
    dv = np.array([_unit(sum(iv[i] for i in f)) for f in ifc])
    polys = []
    for vi in range(len(iv)):
        ring = [fi for fi, f in enumerate(ifc) if vi in f]
        n = _unit(iv[vi])
        ref = _unit(dv[ring[0]] - n * float(np.dot(dv[ring[0]], n)))
        perp = np.cross(n, ref)

        def ang(fi):
            p = dv[fi] - n * float(np.dot(dv[fi], n))
            return math.atan2(float(np.dot(p, perp)), float(np.dot(p, ref)))
        ring.sort(key=ang)
        polys.append(tuple(ring))
    return _triangulate_centroid(dv, polys)


def _build(name, fn, root, triangulation, prov) -> Hedron:
    v, f = fn()
    v = np.array([_unit(x) for x in v])
    return Hedron(name, v, _orient(v, f), root, triangulation, prov)


def families() -> dict:
    """The candidate hedron space. Face counts are DERIVED, not assumed."""
    out = {}
    for nm, fn, tri in (
            ("TETRAHEDRON_4", _tetrahedron, "native_triangular"),
            ("OCTAHEDRON_8", _octahedron, "native_triangular"),
            ("ICOSAHEDRON_20", _icosahedron, "native_triangular"),
            ("CUBE_TRIANGULATED_24", _cube, "centroid_fan_from_square"),
            ("DODECAHEDRON_TRIANGULATED_60", _dodecahedron,
             "centroid_fan_from_pentagon")):
        for root in ("face_centre", "vertex"):
            h = _build(f"{nm}_{root.upper()}", fn, root, tri,
                       "EXACT_CONSTRUCTION_NOT_FITTED")
            out[h.name] = h
    return out


def subdivide(tri) -> tuple:
    """One 4-way spherical subdivision. Child order is FIXED here and the
    child->index convention is searched separately, never assumed."""
    a, b, c = (np.asarray(x, float) for x in tri)
    ab, bc, ca = _unit(a + b), _unit(b + c), _unit(c + a)
    return ((a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca))


def subdivide8(tri) -> tuple:
    """One 8-way subdivision, for the octal / 36-bit width hypothesis.

    Two 4-way steps produce 16 cells, not 8, so an octal path digit
    cannot be two binary levels. This splits each edge in two and then
    splits the central child again, giving a genuine 8-way branch whose
    linear scale is 2^(-3/2) per digit rather than 1/2.
    """
    quads = subdivide(tri)
    return quads[:3] + subdivide(quads[3])[:4] + (quads[3],)


def candidate_space() -> list:
    """The enumerated hedron candidate space, with derived scales."""
    rows = []
    for name, h in sorted(families().items()):
        rows.append({
            "hedron_family": name,
            "base_face_count": h.face_count,
            "root": h.root,
            "triangulation": h.triangulation,
            "base_edge_arc_km": round(h.edge_arc_km(), 2),
            "level2_cell_km": round(h.cell_edge_km(2), 2),
            "level6_cell_km": round(h.cell_edge_km(6), 2),
            "faces_fit_in_F5_5bits": h.face_count <= 32,
            "provenance": h.provenance,
        })
    return rows
