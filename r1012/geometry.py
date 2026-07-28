"""R10.12 Phases 19-24 — analytic geometry, refusal-first.

Topology, node positions, refinement law, body realization, and shell
projection are SEPARATE layers. The active construction is analytic
(regular Wilkes/SAA-clocked frame); the revoked fitted warp and the
fitted node mesh are never loaded here.

CRITICAL HONESTY GATE (Phase 24): the S6-state->geometry mapping is
UNDERDETERMINED, so a segmented wire's geometry status stops at
STATE_MAPPED. This package does NOT invent latitude/longitude for
segmented wires. (Historical old-profile renderings exist in frozen
receipts only.)
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from r1012.certificate import certify
from r1012.evidence import Tier

_PKG = Path(__file__).resolve().parent / "data"
_DOCS = Path(__file__).resolve().parents[1] / "docs" / "r109" / \
    "earth_v1" / "RGCS_Earth_Alignment_Candidate_2026-07-26"
#: packaged frozen-frame topology preferred (wheel installs); repo docs
#: as fallback. These CSVs are the rigid FRAME (topology + node ids) —
#: not the revoked warp operator.
V1_DIR = _PKG if (_PKG / "MAPPED_ICOSAHEDRON_VERTICES.csv").exists() \
    else _DOCS

GEOMETRY_STAGES = ("TOPOLOGY_ONLY", "STATE_MAPPED", "CELL_MAPPED",
                   "BODY_REALIZED", "SHELL_PROJECTED",
                   "GEOGRAPHY_RENDERED")


class GeometryError(ValueError):
    pass


@dataclass(frozen=True)
class Frame:
    """Phase 20 — exact frame authority object."""
    frame_id: str
    origin: str
    axis: str
    handedness: str
    root_feature: str
    phase_hand: str
    epoch_authority: str
    uncertainty: str
    provenance: str


T_FRAME = Frame(
    "T_ANALYTIC_WILKES_SAA", "Earth centre of mass", "mean rotation axis",
    "South-Up, clockwise above Antarctica", "Wilkes root face centroid",
    "SAA-projected phase direction", "Ba-130 (sole long-origin)",
    "root placement reproduced independently to ~0.05 km",
    "R10.8.2 locked root profile; analytic (no fitted operator)")

B0_FRAME = Frame(
    "B0_APEX_WITNESS", "Earth centre of mass", "mean rotation axis",
    "South-Up", "apex vertex near 32.84N 64.88W (recreational-alignment "
    "origin; independent witness only)",
    "roll fit against two reference points", "n/a",
    "three-point RMS 1.52 deg; convention-limited ~20 km (ellipsoid)",
    "R10.11F pack; NEVER a calibration source")


def load_topology():
    """Phase 19 — 20 faces, 30 globally shared edge IDs, 12 nodes."""
    verts, faces = {}, {}
    for row in csv.DictReader(open(V1_DIR / "MAPPED_ICOSAHEDRON_VERTICES.csv")):
        v = np.array([float(row["source_x"]), float(row["source_y"]),
                      float(row["source_z"])])
        verts[int(row["vertex_id"])] = v / np.linalg.norm(v)
    for row in csv.DictReader(open(V1_DIR / "MAPPED_FACE_CENTROIDS.csv")):
        faces[int(row["mesh_face"])] = tuple(int(x)
                                             for x in row["vertex_ids"].split())
    edges = {}
    for f, tri in faces.items():
        for i in range(3):
            key = tuple(sorted((tri[i], tri[(i + 1) % 3])))
            edges.setdefault(key, []).append(f)
    assert len(edges) == 30 and all(len(v) == 2 for v in edges.values())
    return verts, faces, {f"E{a:02d}_{b:02d}": tuple(fs)
                          for (a, b), fs in sorted(edges.items())}


def _mid(a, b):
    m = (a + b) / 2
    return m / np.linalg.norm(m)


def build_mesh(level: int) -> dict:
    """Phase 23 — analytic shared-edge mesh (midpoint law; NO ratio law
    is selected — r=1 stands per R10.11F-A). Refuses level > 6 global
    (sparse tracing covers deeper)."""
    if level > 6:
        raise GeometryError(
            f"refused: global level-{level} mesh allocation "
            f"(level 11 would be 41.9M vertices); use sparse tracing")
    verts, faces, _ = load_topology()
    V = [verts[i] for i in range(12)]
    F = [tuple(faces[f]) for f in sorted(faces)]
    for _ in range(level):
        cache, NV, NF = {}, list(V), []
        def midi(i, j):
            k = (min(i, j), max(i, j))
            if k not in cache:
                NV.append(_mid(NV[i], NV[j]))
                cache[k] = len(NV) - 1
            return cache[k]
        for a, b, c in F:
            ab, bc, ca = midi(a, b), midi(b, c), midi(c, a)
            NF += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
        V, F = NV, NF
    return {"level": level, "vertices": len(V), "triangles": len(F),
            "euler_ok": len(V) - (len(V) + len(F) - 2) + len(F) == 2,
            "V": V, "F": F}


def audit_mesh(level: int = 4) -> dict:
    m = build_mesh(level)
    V, F = m["V"], m["F"]
    centroid_sign = 0
    reversals = 0
    for a, b, c in F:
        n = np.cross(V[b] - V[a], V[c] - V[a])
        s = 1 if np.dot(n, (V[a] + V[b] + V[c]) / 3) > 0 else -1
        if centroid_sign == 0:
            centroid_sign = s
        elif s != centroid_sign:
            reversals += 1
    return {"level": level, "vertices": m["vertices"],
            "triangles": m["triangles"],
            "orientation_reversals": reversals,
            "shared_edge_construction": "midpoints are functions of "
                                        "endpoint IDs only — cracks "
                                        "impossible by construction",
            "ratio_law": "NONE SELECTED (r=1 stands; R10.11F-A result)"}


def geometry_status(wire) -> dict:
    """Phase 24 — highest JUSTIFIED stage for a wire. Segmented wires
    stop at STATE_MAPPED; no latitude/longitude is invented."""
    c = certify(wire)
    return {
        "wire": str(wire), "stage": "STATE_MAPPED",
        "stages_available": list(GEOMETRY_STAGES),
        "justification": "the segmented frame yields exact E3/S6/child "
                         "fields (STATE_MAPPED); the S6-state->geometry "
                         "mapping is UNDERDETERMINED, so CELL_MAPPED and "
                         "beyond are refused rather than invented",
        "evidence_tier": Tier.UNDERDETERMINED.value,
        "historical_note": "old-profile geographic renderings exist only "
                           "in frozen receipts (HISTORICAL_ONLY)",
    }


def s6_hypothesis_registry() -> dict:
    """Phase 21 — declared, bounded hypothesis families for the
    S6->geometry bridge. ALL currently UNDERDETERMINED; none may use
    place names to fit."""
    fams = [
        {"id": "H1_ROOT_NODE", "form": "state -> one of 64 lattice nodes "
         "(12 vertices + 20 faces + 30 edges + 2 poles?)",
         "status": "UNDERDETERMINED"},
        {"id": "H2_FACE_BARYCENTRIC", "form": "state -> (face, coarse "
         "barycentric cell)", "status": "UNDERDETERMINED"},
        {"id": "H3_EDGE_VERTEX_CLASS", "form": "state -> edge/vertex "
         "class + index", "status": "UNDERDETERMINED"},
        {"id": "H4_NODE_LIFT_CONTROL", "form": "state -> recursive "
         "node-lift control parameter", "status": "UNDERDETERMINED"},
        {"id": "H5_TORO_POLO_PHASE", "form": "state -> (toroidal, "
         "poloidal) phase pair (e.g. 8x8)", "status": "UNDERDETERMINED"},
        {"id": "H6_SHELL_RELATIVE", "form": "state -> shell-relative "
         "geometric register", "status": "UNDERDETERMINED"},
    ]
    return {"schema": "rgcs.r1012.s6-geometry-hypotheses.v1",
            "principal_unresolved_bridge": True,
            "fit_rule": "no family may use place names to fit",
            "families": fams}
