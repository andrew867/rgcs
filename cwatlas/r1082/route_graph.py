"""P14 — Dodecahedral-dual route graph for locked-profile adjacency.

Locked Decision 4 makes the **dodecahedral dual** the active adjacency graph:
routing between root cells uses *dual-vertex* adjacency, where each dual vertex
is one icosahedral face centre (Locked Decision 5). This module is a thin
wrapper over the reused :mod:`cwatlas.dodecahedron` engine — it does **not**
rebuild the dual — and adds path / neighbour queries and route certificates on
top of it.

The whole point of the dual is that a face and a vertex are *not* the same
object. Two refusals are reused / added so the API cannot conflate them:

* an :class:`~cwatlas.dodecahedron.IcosaFaceId` is not a
  :class:`~cwatlas.dodecahedron.DodecaVertexId`; the only bridge is
  :func:`~cwatlas.dodecahedron.dual_vertex_of_face` (reused);
* a **dodecahedral pentagon face** is never the selected root — the root is a
  face *centre* / dual *vertex*, so :func:`refuse_dodeca_face_as_root` refuses
  any attempt to treat a dodeca face centre as the root (required work #4).

``DERIVED_MATHEMATICS`` / ``SOFTWARE``. A vertex id and a path are combinatorial
objects, not places, and route length asserts nothing physical. See
:mod:`cwatlas.r1082.claims`.
"""

from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import dataclass

from cwatlas.dodecahedron import (
    ConflationError,
    Dodecahedron,
    DodecaVertexId,
    IcosaFaceId,
    NUM_FACES as DODECA_NUM_FACES,
    NUM_VERTICES as DODECA_NUM_VERTICES,
    build_dodecahedron,
    dual_vertex_of_face,
    require_dodeca_vertex,
)
from cwatlas.r1082 import claims as r1082_claims

GRAPH_ID = "CW-R1082-DODECA-DUAL"
GRAPH_VERSION = "1.0.0"

#: A regular dodecahedron is 3-regular: every dual vertex has exactly 3
#: neighbours (its icosa face shares an edge with 3 others).
EXPECTED_DEGREE = 3


def refuse_dodeca_face_as_root(x=None, *_a, **_k) -> None:
    """Refuse treating a dodecahedral pentagon *face* as the selected root.

    The locked root feature is an icosahedral face centre, i.e. a dodecahedral
    *vertex* (Locked Decision 5). A dodecahedral face (one of the 12 pentagons)
    is a different object and must never be called the root.
    """
    raise ConflationError(
        "refused: the selected root is an icosahedral face centre == a "
        "dodecahedral-dual VERTEX, never a dodecahedral pentagon FACE. A "
        "dodeca face centre is not the root and must not be coerced into one.")


@dataclass(frozen=True)
class RouteCertificate:
    """A deterministic shortest-route certificate on the dual graph.

    Attributes
    ----------
    start, end:
        Endpoint dodeca-vertex ids (plain ints in ``0..19``).
    path:
        The vertex-id sequence from ``start`` to ``end`` inclusive, the
        deterministic (lowest-id tie-broken) BFS shortest path.
    hops:
        Edge count ``len(path) - 1``.
    graph_id, graph_version, graph_digest:
        The authority the certificate was cut against.
    """

    start: int
    end: int
    path: tuple[int, ...]
    hops: int
    graph_id: str
    graph_version: str
    graph_digest: str


@dataclass(frozen=True)
class RouteGraph:
    """The dodecahedral-dual adjacency graph as a routing authority.

    Attributes
    ----------
    graph_id, version:
        Versioned identity; part of :meth:`graph_digest`.
    dod:
        The reused :class:`cwatlas.dodecahedron.Dodecahedron`.
    adjacency:
        ``(20,)`` tuple of ascending neighbour-id tuples, one per dual vertex.
    """

    graph_id: str
    version: str
    dod: Dodecahedron
    adjacency: tuple[tuple[int, ...], ...]

    def degree(self, vertex: DodecaVertexId) -> int:
        """Number of dual neighbours of ``vertex`` (requires a DodecaVertexId)."""
        v = require_dodeca_vertex(vertex)
        return len(self.adjacency[v.value])

    def neighbors(self, vertex: DodecaVertexId) -> tuple[DodecaVertexId, ...]:
        """Adjacent dual vertices of ``vertex``, ascending.

        Refuses a bare int or an :class:`IcosaFaceId`: adjacency is a
        vertex-space query, so the argument must already be a
        :class:`DodecaVertexId` (map a face through
        :func:`root_vertex_for_face` first).
        """
        v = require_dodeca_vertex(vertex)
        return tuple(DodecaVertexId(n) for n in self.adjacency[v.value])

    def shortest_path(self, start: DodecaVertexId,
                     end: DodecaVertexId) -> RouteCertificate:
        """Deterministic BFS shortest path between two dual vertices.

        Ties are broken by lowest neighbour id, so the path is single-valued
        and reproducible across runs and platforms.
        """
        s = require_dodeca_vertex(start)
        e = require_dodeca_vertex(end)
        path = self._bfs(s.value, e.value)
        return RouteCertificate(
            start=s.value,
            end=e.value,
            path=tuple(path),
            hops=len(path) - 1,
            graph_id=self.graph_id,
            graph_version=self.version,
            graph_digest=self.graph_digest(),
        )

    def _bfs(self, s: int, e: int) -> list[int]:
        if s == e:
            return [s]
        prev: dict[int, int] = {s: s}
        queue: deque[int] = deque([s])
        while queue:
            u = queue.popleft()
            for w in self.adjacency[u]:  # already ascending -> deterministic
                if w not in prev:
                    prev[w] = u
                    if w == e:
                        return self._reconstruct(prev, s, e)
                    queue.append(w)
        raise ValueError(f"no path between {s} and {e} (disconnected graph?)")

    @staticmethod
    def _reconstruct(prev: dict[int, int], s: int, e: int) -> list[int]:
        chain = [e]
        while chain[-1] != s:
            chain.append(prev[chain[-1]])
        chain.reverse()
        return chain

    def graph_digest(self) -> str:
        """Content hash over the graph id, version, and adjacency structure."""
        blob = json.dumps(
            {
                "graph_id": self.graph_id,
                "version": self.version,
                "adjacency": [list(a) for a in self.adjacency],
            },
            sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def build_route_graph(dod: Dodecahedron | None = None) -> RouteGraph:
    """Build the dual route graph over the reused dodecahedron (P14)."""
    if dod is None:
        dod = build_dodecahedron()
    adj: list[list[int]] = [[] for _ in range(DODECA_NUM_VERTICES)]
    for u, w in dod.edges:
        adj[u].append(w)
        adj[w].append(u)
    adjacency = tuple(tuple(sorted(a)) for a in adj)
    return RouteGraph(
        graph_id=GRAPH_ID,
        version=GRAPH_VERSION,
        dod=dod,
        adjacency=adjacency,
    )


def root_vertex_for_face(face: IcosaFaceId) -> DodecaVertexId:
    """The sanctioned bridge: icosa face -> dual (root) vertex.

    Thin re-export of :func:`cwatlas.dodecahedron.dual_vertex_of_face` so a
    root face centre (Locked Decision 5) can be named as its dual vertex for
    routing, without ever coercing a bare int or a face id into a vertex id.
    """
    return dual_vertex_of_face(face)


def route_graph_report() -> dict:
    """Governance report for the dual route graph."""
    graph = build_route_graph()
    degrees = sorted({len(a) for a in graph.adjacency})
    return {
        "phase": "P14",
        "tranche": "T04",
        "what_this_is": (
            "the dodecahedral-dual route graph for EARTH_ROOT_D_V1 adjacency: "
            "path / neighbour queries and route certificates on the dual "
            "(vertex) adjacency, wrapping cwatlas.dodecahedron"),
        "graph_id": graph.graph_id,
        "graph_version": graph.version,
        "graph_digest": graph.graph_digest(),
        "num_dual_vertices": DODECA_NUM_VERTICES,
        "num_dual_edges": len(graph.dod.edges),
        "num_dodeca_faces": DODECA_NUM_FACES,
        "degree_set": degrees,
        "expected_degree": EXPECTED_DEGREE,
        "reused_engine": "cwatlas.dodecahedron (NOT reimplemented)",
        "conflation_guards": [
            "IcosaFaceId is not a DodecaVertexId (require_dodeca_vertex)",
            "a dodecahedral pentagon face is never the root "
            "(refuse_dodeca_face_as_root)",
        ],
        "evidence_class": r1082_claims.EvidenceClass.DERIVED_MATHEMATICS.value,
        "level": "SOFTWARE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_DODECA_DUAL_ROUTE_GRAPH_NO_CONFLATION",
        "what_this_does_not_say": (
            "The dual graph is a combinatorial object; a vertex id, a path, and "
            "a hop count denote nothing geographic. A route length is not a "
            "physical distance and validates no source origin."),
    }
