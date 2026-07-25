"""P14 — Dodecahedral dual topology.

The dodecahedron is the topological dual of the icosahedron (P13):

* each icosahedron **face** becomes a dodecahedron **vertex** (20 of them);
* each icosahedron **vertex** becomes a dodecahedron **pentagon face** (12);
* each icosahedron **edge** becomes a dodecahedron **edge** (30).

The whole point of this module is that the dual is a *distinct* graph. An
icosahedron face id and a dodecahedron vertex id are numerically both small
integers, and it is tempting to treat one as the other. That conflation is a
bug, so it is made a typed refusal: ids are wrapped, and the only bridge
between the two number spaces is the explicit dual map.

MATHEMATICAL_TRANSLATION / SOFTWARE level. No geographic meaning. See
:mod:`cwatlas.claims`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from cwatlas import claims
from cwatlas.icosahedron import Icosahedron, build_icosahedron

CODEC_ID = "CW-HCM-DODECA-1"
CODEC_VERSION = "1.0.0"

NUM_VERTICES = 20
NUM_EDGES = 30
NUM_FACES = 12


class ConflationError(claims.ClaimError):
    """Raised when an icosa face id is used where a dodeca vertex id is due."""


@dataclass(frozen=True)
class IcosaFaceId:
    """A face id in the icosahedron's numbering (``0..19``)."""

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise TypeError("IcosaFaceId wraps a plain int")
        if not 0 <= self.value < 20:
            raise ValueError(f"icosa face id out of range: {self.value!r}")


@dataclass(frozen=True)
class DodecaVertexId:
    """A vertex id in the dodecahedron's numbering (``0..19``).

    A *distinct* type from :class:`IcosaFaceId` even though both range over
    ``0..19``: the equal ranges are exactly why conflation is easy and must be
    refused.
    """

    value: int

    def __post_init__(self) -> None:
        if not isinstance(self.value, int) or isinstance(self.value, bool):
            raise TypeError("DodecaVertexId wraps a plain int")
        if not 0 <= self.value < 20:
            raise ValueError(f"dodeca vertex id out of range: {self.value!r}")


def dual_vertex_of_face(face: IcosaFaceId) -> DodecaVertexId:
    """The dual map: icosa face -> dodeca vertex.

    This is the *only* sanctioned bridge from the face number space to the
    vertex number space. It requires a typed :class:`IcosaFaceId`; passing a
    bare int or a :class:`DodecaVertexId` is a refusal.
    """
    if not isinstance(face, IcosaFaceId):
        raise ConflationError(
            "refused: dual_vertex_of_face requires an IcosaFaceId; a bare int "
            "or a DodecaVertexId is not an icosa face and must not be coerced "
            "into one.")
    return DodecaVertexId(face.value)


def require_dodeca_vertex(x) -> DodecaVertexId:
    """Guard: accept a :class:`DodecaVertexId`, refuse a face id or bare int.

    The refusal is the deliberate behaviour: to obtain a dodeca vertex from an
    icosa face you must go through :func:`dual_vertex_of_face`, never by
    treating the face id as if it were already a vertex id.
    """
    if isinstance(x, IcosaFaceId):
        raise ConflationError(
            "refused: an IcosaFaceId is not a DodecaVertexId. Map it through "
            "dual_vertex_of_face() first; a face is not a vertex.")
    if not isinstance(x, DodecaVertexId):
        raise ConflationError(
            f"refused: expected a DodecaVertexId, got {type(x).__name__}. The "
            f"two number spaces are distinct and are not interchangeable.")
    return x


@dataclass(frozen=True)
class Dodecahedron:
    """The dodecahedral dual as a distinct graph.

    Attributes
    ----------
    vertices:
        ``(20, 3)`` unit vectors, one per icosahedron face (its centroid
        direction). Vertex id ``v`` corresponds to icosa face ``v`` via the
        dual map.
    edges:
        ``(30,)`` tuple of ``(u, v)`` dodeca-vertex-index pairs, ``u < v``.
    faces:
        ``(12,)`` tuple of pentagons, each a tuple of 5 dodeca vertex indices
        in cyclic order around the corresponding icosahedron vertex.
    """

    vertices: np.ndarray
    edges: tuple[tuple[int, int], ...]
    faces: tuple[tuple[int, int, int, int, int], ...]

    def euler_characteristic(self) -> int:
        """V - E + F. Must equal 2."""
        return len(self.vertices) - len(self.edges) + len(self.faces)


def build_dodecahedron(ico: Icosahedron | None = None) -> Dodecahedron:
    """Construct the dodecahedral dual from an icosahedron (P13).

    Dual vertices are icosa-face centroid directions. Two dual vertices are
    adjacent iff the corresponding icosa faces share an edge. Each dual face is
    the ring of icosa faces incident to one icosa vertex, ordered cyclically.
    """
    if ico is None:
        ico = build_icosahedron()

    # Dual vertices: one unit centroid direction per icosa face.
    vertices = ico.face_normals.copy()
    vertices.flags.writeable = False

    # Dual edges: icosa faces sharing exactly two vertices (a shared edge).
    n_faces = len(ico.faces)
    face_sets = [set(f) for f in ico.faces]
    edges: list[tuple[int, int]] = []
    for u in range(n_faces):
        for w in range(u + 1, n_faces):
            if len(face_sets[u] & face_sets[w]) == 2:
                edges.append((u, w))
    edges.sort()

    # Dual faces: for each icosa vertex, the incident faces, cyclically ordered.
    faces: list[tuple[int, int, int, int, int]] = []
    for vtx in range(len(ico.vertices)):
        incident = [fid for fid, f in enumerate(ico.faces) if vtx in f]
        ring = _order_ring(ico, vtx, incident)
        if len(ring) != 5:
            raise ValueError(
                f"icosa vertex {vtx} has {len(ring)} incident faces, expected 5")
        faces.append(tuple(ring))  # type: ignore[arg-type]
    faces.sort()

    return Dodecahedron(vertices=vertices, edges=tuple(edges),
                        faces=tuple(faces))


def _order_ring(ico: Icosahedron, vtx: int, incident: list[int]) -> list[int]:
    """Order incident dual vertices cyclically around an icosa vertex.

    Project each incident face centroid onto the plane perpendicular to the
    icosa vertex direction and sort by polar angle. The starting point is the
    lowest face id, so the ordering is deterministic (up to a fixed rotation).
    """
    axis = ico.vertices[vtx]
    axis = axis / np.linalg.norm(axis)
    # A stable in-plane basis (u, w) orthogonal to axis.
    seed = np.array([1.0, 0.0, 0.0]) if abs(axis[0]) < 0.9 \
        else np.array([0.0, 1.0, 0.0])
    u = seed - (seed @ axis) * axis
    u = u / np.linalg.norm(u)
    w = np.cross(axis, u)

    centroids = ico.face_normals
    angled = []
    for fid in incident:
        c = centroids[fid]
        ang = float(np.arctan2(c @ w, c @ u))
        angled.append((ang, fid))
    angled.sort(key=lambda t: (t[0], t[1]))
    ring = [fid for _, fid in angled]
    # Rotate so the ring starts at its lowest face id: deterministic anchor.
    start = ring.index(min(ring))
    return ring[start:] + ring[:start]


def dodecahedron_report() -> dict:
    """Governance report for the dual topology."""
    ico = build_icosahedron()
    dod = build_dodecahedron(ico)
    return {
        "phase": "P14",
        "what_this_is": (
            "the 20-vertex dodecahedral dual of the icosahedron, as a distinct "
            "graph with typed ids that refuse face/vertex conflation"),
        "codec_id": CODEC_ID,
        "codec_version": CODEC_VERSION,
        "counts": {
            "vertices": len(dod.vertices),
            "edges": len(dod.edges),
            "faces": len(dod.faces),
        },
        "euler_characteristic": dod.euler_characteristic(),
        "dual_incidence": {
            "icosa_faces_to_dodeca_vertices": len(ico.faces),
            "icosa_vertices_to_dodeca_faces": len(ico.vertices),
            "icosa_edges_to_dodeca_edges": len(ico.edges),
        },
        "conflation_guard": "IcosaFaceId and DodecaVertexId are distinct types",
        "claim_class": claims.ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_DODECA_DUAL_DISTINCT_NO_CONFLATION",
        "what_this_does_not_say": (
            "The dual graph is a combinatorial object. Neither a vertex id nor "
            "a face id denotes a place; no geographic meaning is asserted."),
    }
