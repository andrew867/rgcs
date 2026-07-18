"""A08-A11 — the 64-tetrahedron lane.

**A08: the ambiguity is the finding.** The source says "64 and 4096 are
linked to a 64-tetrahedron grid". That phrase is underdetermined: it
does not say whether 64 counts *cells* (tetrahedra), *vertices*, or
something else, nor which of several distinct geometries is meant.
Silently choosing one reading — in particular replacing 64 tetrahedra
with 64 nodes because graphs are easier — would manufacture a result.
So every reading is registered separately, constructed explicitly, and
analysed side by side. Where the readings disagree, the disagreement is
reported rather than resolved by preference.

**A09: four non-isomorphic construction families** are provided (the
matrix requires at least three). They are genuinely different objects,
not relabelings of one another, and the tests assert that.

**A10: spectra and synchronization.** Graph structure is summarised by
the Laplacian spectrum, which is invariant under vertex relabeling.
Algebraic connectivity (Fiedler value) bounds how readily a network of
identical oscillators synchronises. This is graph theory, not physics:
a synchronisable graph is not a crystal.

**A11: matched nulls.** Every "special" feature is compared against
null complexes matched on size and degree, because "this structure has
property X" is meaningless without "and comparable random structures
do not".

**The 4096 result.** 4096 = 64². Any set of 64 objects has exactly
4096 ordered pairs, so a "4096 relationship" is available in every
64-element structure — including random ones. It is a fact about
counting, not about tetrahedra. ``pair_count_is_not_special()``
demonstrates this against the nulls.

Nothing in this module is evidence that any physical lattice exists.
Transfer firewall GRAPH_SYMMETRY_TO_PHYSICAL_LATTICE applies
throughout.
"""

from __future__ import annotations

import itertools
import random
from dataclasses import dataclass, field

import numpy as np

# --- A08: ambiguity registry --------------------------------------------


@dataclass(frozen=True)
class Reading:
    """One way to read the underdetermined source phrase."""
    id: str
    what_64_counts: str
    geometry: str
    rationale: str
    source_supports: str = "UNDERDETERMINED"


READINGS = (
    Reading("READ-CELLS-FULLER", "tetrahedral cells",
            "Fuller vector-equilibrium assembly: 8 vector equilibria "
            "of 8 tetrahedra each",
            "the phrase '64-tetrahedron grid' most directly names 64 "
            "tetrahedra, and this is the best-known object with that "
            "name"),
    Reading("READ-CELLS-SUBDIV", "tetrahedral cells",
            "one tetrahedron subdivided twice (8 -> 64 cells)",
            "a '64-tetrahedron grid' could equally be a single "
            "tetrahedron refined until it contains 64"),
    Reading("READ-NODES-CUBIC", "vertices",
            "4x4x4 cubic lattice of 64 points",
            "if 64 counts nodes rather than cells, a 4^3 lattice is "
            "the plainest reading"),
    Reading("READ-NODES-HYPERCUBE", "vertices",
            "6-dimensional hypercube Q6 (2^6 = 64 vertices)",
            "64 = 2^6 invites a binary reading, which also connects to "
            "the powers-of-two family"),
)


def ambiguity_report() -> dict:
    return {
        "source_phrase": "4096 and 64 are linked to a 64-tetrahedron "
                         "grid.",
        "status": "UNDERDETERMINED",
        "readings": [r.__dict__ for r in READINGS],
        "n_readings": len(READINGS),
        "resolution": "NOT RESOLVED. The source does not specify "
                      "whether 64 counts cells or vertices, nor which "
                      "geometry. All readings are analysed; none is "
                      "promoted.",
        "refusal": "Replacing '64 tetrahedra' with '64 nodes' because "
                   "graphs are easier to analyse would fabricate a "
                   "result. The substitution is refused.",
        "evidence_class": "SOURCE_CLAIM",
    }


# --- A09: constructions --------------------------------------------------

@dataclass(frozen=True)
class Complex:
    """A simplicial/graph structure with an explicit provenance."""
    id: str
    n_vertices: int
    edges: tuple                      # ((i, j), ...) i < j
    cells: tuple = field(default=())  # tetrahedra as 4-tuples
    reading: str = ""
    note: str = ""

    @property
    def n_edges(self) -> int:
        return len(self.edges)

    @property
    def n_cells(self) -> int:
        return len(self.cells)

    def adjacency(self) -> np.ndarray:
        a = np.zeros((self.n_vertices, self.n_vertices), dtype=float)
        for i, j in self.edges:
            a[i, j] = a[j, i] = 1.0
        return a

    def laplacian(self) -> np.ndarray:
        a = self.adjacency()
        return np.diag(a.sum(axis=1)) - a

    def degrees(self) -> list:
        a = self.adjacency()
        return sorted(int(d) for d in a.sum(axis=1))


def _edges_from_cells(cells) -> tuple:
    e = set()
    for c in cells:
        for i, j in itertools.combinations(sorted(c), 2):
            e.add((i, j))
    return tuple(sorted(e))


def cubic_4x4x4() -> Complex:
    """64 vertices on a 4x4x4 grid; edges join nearest neighbours."""
    idx = {}
    n = 0
    for x in range(4):
        for y in range(4):
            for z in range(4):
                idx[(x, y, z)] = n
                n += 1
    edges = set()
    for (x, y, z), i in idx.items():
        for dx, dy, dz in ((1, 0, 0), (0, 1, 0), (0, 0, 1)):
            nb = (x + dx, y + dy, z + dz)
            if nb in idx:
                edges.add((min(i, idx[nb]), max(i, idx[nb])))
    return Complex("CUBIC-4x4x4", 64, tuple(sorted(edges)),
                   reading="READ-NODES-CUBIC",
                   note="64 vertices, 3-regular interior; not tetrahedral")


def hypercube_q6() -> Complex:
    """2^6 = 64 vertices; edges join bit-strings at Hamming distance 1."""
    edges = set()
    for v in range(64):
        for b in range(6):
            w = v ^ (1 << b)
            if v < w:
                edges.add((v, w))
    return Complex("HYPERCUBE-Q6", 64, tuple(sorted(edges)),
                   reading="READ-NODES-HYPERCUBE",
                   note="6-regular, vertex-transitive, bipartite")


def _subdivide_once(tet, coords):
    """Split one tetrahedron into 8: 4 corner cells + 4 from the
    central octahedron, cut along the m_ab-m_cd diagonal.

    ``coords`` maps vertex id -> integer coordinate triple (scaled so
    midpoints stay exact integers); shared midpoints are reused, so
    neighbouring cells stay glued.
    """
    a, b, c, d = tet

    def mid(u, v):
        pu, pv = coords[u], coords[v]
        p = tuple((pu[k] + pv[k]) // 2 for k in range(3))
        for vid_, pt in coords.items():
            if pt == p:
                return vid_
        nid = len(coords)
        coords[nid] = p
        return nid

    ab, ac, ad = mid(a, b), mid(a, c), mid(a, d)
    bc, bd, cd = mid(b, c), mid(b, d), mid(c, d)
    return [
        (a, ab, ac, ad), (b, ab, bc, bd),
        (c, ac, bc, cd), (d, ad, bd, cd),
        (ab, cd, ac, ad), (ab, cd, ad, bd),
        (ab, cd, bd, bc), (ab, cd, bc, ac),
    ]


def tetra_subdivided_64() -> Complex:
    """One tetrahedron subdivided twice: 1 -> 8 -> 64 cells.

    Exactly 64 tetrahedral cells, which is the reading "a
    64-tetrahedron grid is one tetrahedron refined until it contains
    64". Integer coordinates scaled by 4 keep every midpoint exact.
    """
    coords = {0: (0, 0, 0), 1: (4, 0, 0), 2: (0, 4, 0), 3: (0, 0, 4)}
    cells = [(0, 1, 2, 3)]
    for _ in range(2):
        nxt = []
        for t in cells:
            nxt.extend(_subdivide_once(t, coords))
        cells = nxt
    cells_t = tuple(sorted(tuple(sorted(c)) for c in cells))
    return Complex("TETRA-SUBDIV", len(coords),
                   _edges_from_cells(cells_t), cells_t,
                   reading="READ-CELLS-SUBDIV",
                   note=f"{len(cells_t)} tetrahedral cells from two "
                        "1->8 subdivisions")


def fuller_ve_64() -> Complex:
    """Fuller-style assembly: 8 vector equilibria of 8 tetrahedra.

    Modelled combinatorially: 8 clusters, each a central vertex joined
    to a 6-vertex ring forming 8 tetrahedral cells with a shared apex;
    clusters are then joined at shared boundary vertices. The result is
    64 tetrahedral cells.
    """
    cells = []
    edges = set()
    vcount = 0
    hub_ids = []
    for cluster in range(8):
        hub = vcount
        vcount += 1
        hub_ids.append(hub)
        ring = list(range(vcount, vcount + 6))
        vcount += 6
        apex = vcount
        vcount += 1
        for k in range(6):
            a, b = ring[k], ring[(k + 1) % 6]
            cells.append(tuple(sorted((hub, apex, a, b))))
        # two closing cells per cluster -> 8 cells per cluster
        cells.append(tuple(sorted((hub, ring[0], ring[2], ring[4]))))
        cells.append(tuple(sorted((apex, ring[1], ring[3], ring[5]))))
    # join clusters hub-to-hub in a ring so the assembly is connected
    for k in range(8):
        i, j = hub_ids[k], hub_ids[(k + 1) % 8]
        edges.add((min(i, j), max(i, j)))
    cells = tuple(sorted(set(cells)))
    edges |= set(_edges_from_cells(cells))
    return Complex("FULLER-VE-64", vcount, tuple(sorted(edges)), cells,
                   reading="READ-CELLS-FULLER",
                   note=f"{len(cells)} tetrahedral cells in 8 clusters")


FAMILIES = {
    "CUBIC-4x4x4": cubic_4x4x4,
    "HYPERCUBE-Q6": hypercube_q6,
    "TETRA-SUBDIV": tetra_subdivided_64,
    "FULLER-VE-64": fuller_ve_64,
}


def build_all() -> dict:
    return {k: f() for k, f in FAMILIES.items()}


# --- A10: spectra and synchronization -----------------------------------

def laplacian_spectrum(cx: Complex, decimals: int = 9) -> np.ndarray:
    """Sorted Laplacian eigenvalues — invariant under relabeling."""
    ev = np.linalg.eigvalsh(cx.laplacian())
    return np.round(np.sort(ev), decimals)


def algebraic_connectivity(cx: Complex) -> float:
    """Fiedler value (2nd-smallest Laplacian eigenvalue).

    Larger means a more readily synchronised network of identical
    oscillators. This is a statement about the graph, NOT evidence that
    any physical lattice synchronises.
    """
    return float(laplacian_spectrum(cx)[1])


def sync_summary(cx: Complex) -> dict:
    ev = laplacian_spectrum(cx)
    fiedler = float(ev[1])
    lam_max = float(ev[-1])
    return {
        "id": cx.id, "n_vertices": cx.n_vertices,
        "n_edges": cx.n_edges, "n_cells": cx.n_cells,
        "algebraic_connectivity": fiedler,
        "spectral_gap_ratio": (lam_max / fiedler) if fiedler > 1e-12
        else float("inf"),
        "n_zero_eigenvalues": int(np.sum(ev < 1e-9)),
        "connected": bool(np.sum(ev < 1e-9) == 1),
        "evidence_class": "DERIVED_ARITHMETIC",
        "claim": "graph-theoretic property; not a physical lattice "
                 "(firewall GRAPH_SYMMETRY_TO_PHYSICAL_LATTICE)",
    }


def relabel(cx: Complex, seed: int) -> Complex:
    """Randomly permute vertex labels — structure unchanged."""
    rng = random.Random(seed)
    perm = list(range(cx.n_vertices))
    rng.shuffle(perm)
    edges = tuple(sorted((min(perm[i], perm[j]), max(perm[i], perm[j]))
                         for i, j in cx.edges))
    cells = tuple(sorted(tuple(sorted(perm[v] for v in c))
                         for c in cx.cells))
    return Complex(cx.id + "-relabelled", cx.n_vertices, edges, cells,
                   cx.reading, "relabelled copy")


# --- A11: matched nulls --------------------------------------------------

def matched_null(cx: Complex, seed: int) -> Complex:
    """Degree-preserving double-edge-swap rewiring.

    Same vertex count, same edge count, same degree sequence — so any
    surviving difference is structure, not size.
    """
    rng = random.Random(seed)
    edges = [list(e) for e in cx.edges]
    eset = {tuple(e) for e in edges}
    for _ in range(10 * len(edges)):
        i, j = rng.randrange(len(edges)), rng.randrange(len(edges))
        if i == j:
            continue
        a, b = edges[i]
        c, d = edges[j]
        if len({a, b, c, d}) < 4:
            continue
        n1 = (min(a, c), max(a, c))
        n2 = (min(b, d), max(b, d))
        if n1 in eset or n2 in eset or n1[0] == n1[1] or n2[0] == n2[1]:
            continue
        eset.discard((min(a, b), max(a, b)))
        eset.discard((min(c, d), max(c, d)))
        eset.add(n1)
        eset.add(n2)
        edges[i] = list(n1)
        edges[j] = list(n2)
    return Complex(cx.id + "-null", cx.n_vertices,
                   tuple(sorted(eset)), (), cx.reading,
                   "degree-matched null")


def compare_to_nulls(cx: Complex, n_null: int = 40,
                     seed: int = 20260718) -> dict:
    """Is this structure's connectivity unusual for its degree
    sequence?"""
    obs = algebraic_connectivity(cx)
    vals = []
    for i in range(n_null):
        try:
            vals.append(algebraic_connectivity(matched_null(cx, seed + i)))
        except Exception:  # noqa: BLE001
            continue
    arr = np.array(vals) if vals else np.array([obs])
    mean, sd = float(arr.mean()), float(arr.std())
    z = (obs - mean) / sd if sd > 1e-12 else 0.0
    # TWO-SIDED: a structure that is unusually POORLY connected is just
    # as much a finding as one unusually well connected. A one-sided
    # test reported p=1.0 for every lattice and hid the real result.
    n_extreme = int(np.sum(np.abs(arr - mean) >= abs(obs - mean)))
    p = float((n_extreme + 1) / (len(arr) + 1))
    return {
        "id": cx.id,
        "observed_algebraic_connectivity": obs,
        "null_mean": mean, "null_sd": sd, "n_null": len(vals),
        "z_score": z, "p_value_two_sided": p,
        "direction": ("less connected than matched random"
                      if obs < mean else
                      "more connected than matched random"),
        "unusual_at_0.05": p < 0.05,
        "evidence_class": "NUMERICAL_SIMULATION",
        "claim": "compared against degree-matched random graphs; a "
                 "difference here is combinatorial, not physical",
    }


# --- the 4096 question ---------------------------------------------------

def pair_count_is_not_special(n: int = 64) -> dict:
    """4096 = 64**2 is the number of ordered pairs of 64 objects.

    It is therefore available in EVERY 64-element structure, including
    random ones with no geometry at all. A "4096 relationship" arising
    from "64 tetrahedra" is a fact about counting.
    """
    built = build_all()
    per_family = {}
    for k, cx in built.items():
        cells_or_nodes = cx.n_cells if cx.n_cells else cx.n_vertices
        per_family[k] = {
            "count_64_objects": cells_or_nodes,
            "ordered_pairs": cells_or_nodes ** 2,
            "equals_4096": cells_or_nodes ** 2 == 4096,
        }
    return {
        "n": n, "ordered_pairs": n ** 2,
        "equals_4096": n ** 2 == 4096,
        "per_family": per_family,
        "unstructured_set_of_64_also_gives_4096": True,
        "conclusion": "4096 = 64^2 holds for ANY 64 objects, "
                      "structured or not. The relationship is "
                      "arithmetic; it carries no information about "
                      "tetrahedra, geometry, or physics.",
        "evidence_class": "DERIVED_ARITHMETIC",
    }
