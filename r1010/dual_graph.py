"""R10.10 Phase 3 — Wilkes-rooted dual-graph orientation propagation.

Faces and vertex triples come from the FROZEN V1 rigid mesh
(``docs/r109/earth_v1/.../MAPPED_ICOSAHEDRON_VERTICES.csv`` +
``MAPPED_FACE_CENTROIDS.csv``) — nothing here invents geometry. The
Wilkes root is mesh face 0 (V1 root profile ``root_mesh_face=0``).

For each directed face crossing F->G over the shared primal edge:

1. the two shared global vertices are identified;
2. the unmatched source vertex (in F, not G) and unmatched destination
   vertex (in G, not F) are identified;
3. the edge-induced local-label permutation maps F's local index of a
   shared vertex to G's local index of the SAME vertex, and F's
   unmatched index to G's unmatched index;
4. its parity is recorded;
5. orientation states propagate O_G = T(F->G) ∘ O_F along a
   deterministic BFS tree from the Wilkes root.

Path independence is AUDITED, not assumed: every directed edge is
checked against the BFS assignment, and every dual 5-cycle around a
primal vertex has its holonomy computed. A nontrivial holonomy is
reported as "transition/phase model incomplete" per the spec.
"""

from __future__ import annotations

import csv
from collections import deque
from pathlib import Path

from r1010.orientation import IDENTITY, Orientation, OrientationError

V1_DIR = Path(__file__).resolve().parents[1] / "docs" / "r109" / "earth_v1" / \
    "RGCS_Earth_Alignment_Candidate_2026-07-26"

WILKES_ROOT_FACE = 0     # V1 root profile: root_mesh_face = 0


def load_faces() -> dict[int, tuple[int, int, int]]:
    faces = {}
    for row in csv.DictReader(open(V1_DIR / "MAPPED_FACE_CENTROIDS.csv")):
        faces[int(row["mesh_face"])] = tuple(
            int(v) for v in row["vertex_ids"].split())
    if len(faces) != 20:
        raise OrientationError(f"expected 20 faces, got {len(faces)}")
    return faces


def adjacency(faces: dict[int, tuple[int, int, int]]) -> list[tuple[int, int]]:
    """The 30 undirected dual edges (faces sharing a primal edge)."""
    edges = []
    ids = sorted(faces)
    for i, f in enumerate(ids):
        for g in ids[i + 1:]:
            if len(set(faces[f]) & set(faces[g])) == 2:
                edges.append((f, g))
    if len(edges) != 30:
        raise OrientationError(f"expected 30 adjacencies, got {len(edges)}")
    return edges


def edge_transition(faces, f: int, g: int) -> Orientation:
    """The edge-induced permutation T(F->G): local index in F -> local
    index in G, shared vertices to themselves, unmatched to unmatched."""
    vf, vg = faces[f], faces[g]
    shared = set(vf) & set(vg)
    if len(shared) != 2:
        raise OrientationError(f"faces {f},{g} are not edge-adjacent")
    (a,) = set(vf) - shared            # unmatched source vertex
    (b,) = set(vg) - shared            # unmatched destination vertex
    perm = [None, None, None]
    for i_local, v in enumerate(vf):
        target = b if v == a else v
        perm[i_local] = vg.index(target)
    return Orientation(tuple(perm))


def propagate(faces=None) -> dict:
    """BFS orientation assignment from the Wilkes root + full audit."""
    faces = faces or load_faces()
    edges = adjacency(faces)
    nbrs: dict[int, list[int]] = {f: [] for f in faces}
    for f, g in edges:
        nbrs[f].append(g)
        nbrs[g].append(f)
    for f in nbrs:
        nbrs[f].sort()                 # deterministic BFS

    assign: dict[int, Orientation] = {WILKES_ROOT_FACE: IDENTITY}
    parent: dict[int, int | None] = {WILKES_ROOT_FACE: None}
    q = deque([WILKES_ROOT_FACE])
    while q:
        f = q.popleft()
        for g in nbrs[f]:
            if g in assign:
                continue
            assign[g] = edge_transition(faces, f, g).compose(assign[f])
            parent[g] = f
            q.append(g)
    reachable = len(assign) == 20

    # audit 1: every directed edge vs the BFS assignment
    edge_rows = []
    consistent_edges = 0
    for f, g in edges:
        for (s, d) in ((f, g), (g, f)):
            t = edge_transition(faces, s, d)
            expected = t.compose(assign[s])
            ok = expected.perm == assign[d].perm
            consistent_edges += ok
            edge_rows.append({
                "src": s, "dst": d, "transition": t.serialize(),
                "parity": t.parity, "consistent_with_bfs": bool(ok)})
            # invertibility
            back = edge_transition(faces, d, s)
            if back.compose(t).perm != IDENTITY.perm:
                raise OrientationError(
                    f"directed transitions {s}<->{d} do not invert")

    # audit 2: holonomy of every dual 5-cycle around a primal vertex
    verts_to_faces: dict[int, list[int]] = {}
    for f, tri in faces.items():
        for v in tri:
            verts_to_faces.setdefault(v, []).append(f)
    cycles = []
    for v, ring in sorted(verts_to_faces.items()):
        ring = sorted(ring)
        # order the ring as an actual cycle by adjacency
        cyc = [ring[0]]
        rest = set(ring[1:])
        while rest:
            nxt = next(g for g in sorted(rest)
                       if len(set(faces[cyc[-1]]) & set(faces[g])) == 2)
            cyc.append(nxt)
            rest.remove(nxt)
        hol = IDENTITY
        for i in range(len(cyc)):
            hol = edge_transition(faces, cyc[i],
                                  cyc[(i + 1) % len(cyc)]).compose(hol)
        cycles.append({"primal_vertex": v, "cycle": cyc,
                       "holonomy": hol.serialize(),
                       "holonomy_parity": hol.parity,
                       "trivial": hol.perm == IDENTITY.perm})

    return {
        "root_face": WILKES_ROOT_FACE,
        "all_faces_reachable": reachable,
        "assignments": {f: assign[f].serialize() for f in sorted(assign)},
        "bfs_parent": {f: parent[f] for f in sorted(parent)},
        "directed_edges": edge_rows,
        "directed_edge_count": len(edge_rows),
        "edges_consistent_with_bfs": consistent_edges,
        "path_independent": consistent_edges == len(edge_rows),
        "vertex_cycles": cycles,
        "nontrivial_holonomy_cycles": sum(1 for c in cycles
                                          if not c["trivial"]),
    }
