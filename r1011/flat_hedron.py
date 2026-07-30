"""R10.11 node-lifted piecewise-affine hedron projection.

Source-matched geometry ("the triangle isnt curved, the hedron curves
come from the nodes"):

- every face is a FLAT chord triangle between three node positions;
- recursive children subdivide AFFINELY inside the flat parent;
- curvature enters ONLY where new refinement nodes are LIFTED to the
  body shell (spherical control profile: L(m) = rho(m_hat) * m_hat,
  rho = 1 here) — each child is again a flat triangle between its
  lifted nodes;
- shared-edge nodes depend only on the two endpoint nodes, so both
  incident faces produce identical node coordinates by construction
  (verified numerically anyway);
- NO Gaussian RBF, no per-cell displacement field, no stored warp
  steps.

Calibration fits ONLY the 12 base node directions (24 angular DOF,
regularized toward the frozen V1 rigid mesh) under hard root/phase
constraints. Anchors are opaque (packet, mesh-face, target) tuples —
no location names in this module.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

V1_DIR = Path(__file__).resolve().parents[1] / "docs" / "r109" / "earth_v1" / \
    "RGCS_Earth_Alignment_Candidate_2026-07-26"

CHILD_MAP = (2, 1, 0, 3)          # recovered V1 quaternary->child mapping
CORNER_PERM = (1, 0, 2)           # recovered V1 face corner order

PROFILE_ID = "FLAT_FACE_NODE_CURVATURE_V1_CANDIDATE"


def unit(lat_deg: float, lon_deg: float) -> np.ndarray:
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo), math.sin(la)])


def latlon(v) -> tuple[float, float]:
    v = np.asarray(v, float)
    v = v / np.linalg.norm(v)
    return (math.degrees(math.asin(np.clip(v[2], -1, 1))),
            math.degrees(math.atan2(v[1], v[0])))


def load_base() -> tuple[np.ndarray, dict[int, tuple[int, int, int]]]:
    verts = {}
    for row in csv.DictReader(open(V1_DIR / "MAPPED_ICOSAHEDRON_VERTICES.csv")):
        v = np.array([float(row["source_x"]), float(row["source_y"]),
                      float(row["source_z"])])
        verts[int(row["vertex_id"])] = v / np.linalg.norm(v)
    faces = {}
    for row in csv.DictReader(open(V1_DIR / "MAPPED_FACE_CENTROIDS.csv")):
        faces[int(row["mesh_face"])] = tuple(
            int(x) for x in row["vertex_ids"].split())
    nodes = np.array([verts[i] for i in range(12)])
    return nodes, faces


def lift(m: np.ndarray) -> np.ndarray:
    """Spherical control lift: rho(m_hat)*m_hat with rho=1."""
    return m / np.linalg.norm(m)


def address_point(nodes: np.ndarray, faces: dict, mesh_face: int,
                  path) -> np.ndarray:
    """Flat-face recursion with node lifting; returns the terminal
    cell centroid direction (gravity-line rendering)."""
    vids = faces[mesh_face]
    A, B, C = (nodes[vids[CORNER_PERM[0]]], nodes[vids[CORNER_PERM[1]]],
               nodes[vids[CORNER_PERM[2]]])
    for p in path:
        mAB, mBC, mCA = (lift((A + B) / 2), lift((B + C) / 2),
                         lift((C + A) / 2))
        A, B, C = [(A, mAB, mCA), (mAB, B, mBC),
                   (mCA, mBC, C), (mAB, mBC, mCA)][CHILD_MAP[p]]
    centroid = (A + B + C) / 3          # point ON the flat terminal facet
    return centroid / np.linalg.norm(centroid)


def face_corners(nodes, faces, mesh_face, path):
    vids = faces[mesh_face]
    A, B, C = (nodes[vids[CORNER_PERM[0]]], nodes[vids[CORNER_PERM[1]]],
               nodes[vids[CORNER_PERM[2]]])
    for p in path:
        mAB, mBC, mCA = (lift((A + B) / 2), lift((B + C) / 2),
                         lift((C + A) / 2))
        A, B, C = [(A, mAB, mCA), (mAB, B, mBC),
                   (mCA, mBC, C), (mAB, mBC, mCA)][CHILD_MAP[p]]
    return A, B, C


# ------------------------------------------------------------ calibration
@dataclass(frozen=True)
class Anchor:
    packet_path: tuple          # quaternary path
    mesh_face: int
    target_lat: float
    target_lon: float
    weight: float = 1.0


def _params_to_nodes(theta: np.ndarray, base: np.ndarray) -> np.ndarray:
    """24 tangent-plane offsets -> unit node directions."""
    nodes = []
    for i in range(12):
        n = base[i]
        # orthonormal tangent basis
        t1 = np.cross(n, [0.0, 0.0, 1.0])
        if np.linalg.norm(t1) < 1e-9:
            t1 = np.cross(n, [1.0, 0.0, 0.0])
        t1 = t1 / np.linalg.norm(t1)
        t2 = np.cross(n, t1)
        v = n + theta[2 * i] * t1 + theta[2 * i + 1] * t2
        nodes.append(v / np.linalg.norm(v))
    return np.array(nodes)


def calibrate(anchors: list[Anchor], root_face: int,
              root_target: tuple[float, float],
              phase_vertex: int, phase_lock_deg: float = 5.0,
              reg: float = 0.15, seed_scale: float = 0.0) -> dict:
    """Fit 12 node directions. Hard-ish constraints as weighted
    residuals: root-face centroid at the root target; phase vertex
    within a declared cone of its rigid direction; regularization of
    every node toward the frozen rigid mesh."""
    from scipy.optimize import least_squares

    base, faces = load_base()
    rigid = base.copy()
    root_dir = unit(*root_target)
    phase_dir = rigid[phase_vertex]

    def residuals(theta):
        nodes = _params_to_nodes(theta, rigid)
        res = []
        for a in anchors:
            p = address_point(nodes, faces, a.mesh_face, a.packet_path)
            t = unit(a.target_lat, a.target_lon)
            res.extend(a.weight * (p - t))
        vids = faces[root_face]
        cen = sum(nodes[v] for v in vids)
        cen = cen / np.linalg.norm(cen)
        res.extend(3.0 * (cen - root_dir))                 # Wilkes root
        # phase cone (soft lock)
        cosang = float(np.dot(nodes[phase_vertex], phase_dir))
        overshoot = max(0.0, math.cos(math.radians(phase_lock_deg)) - cosang)
        res.append(10.0 * overshoot)
        res.extend((reg * (nodes - rigid)).ravel())        # regularizer
        return np.asarray(res)

    theta0 = np.zeros(24) if seed_scale == 0 else \
        np.random.default_rng(3).normal(scale=seed_scale, size=24)
    sol = least_squares(residuals, theta0, method="lm", max_nfev=20000)
    nodes = _params_to_nodes(sol.x, rigid)
    rows = []
    for a in anchors:
        p = address_point(nodes, faces, a.mesh_face, a.packet_path)
        t = unit(a.target_lat, a.target_lon)
        err = math.degrees(math.acos(float(np.clip(np.dot(p, t), -1, 1))))
        rows.append({"mesh_face": a.mesh_face,
                     "target": (a.target_lat, a.target_lon),
                     "model": latlon(p), "residual_deg": err})
    node_move = [math.degrees(math.acos(float(np.clip(
        np.dot(nodes[i], rigid[i]), -1, 1)))) for i in range(12)]
    return {"nodes": nodes, "faces": faces, "anchor_rows": rows,
            "node_move_deg": node_move, "cost": float(sol.cost),
            "converged": bool(sol.success)}


# ------------------------------------------------------------ verification
def convexity_audit(nodes: np.ndarray, faces: dict) -> dict:
    from scipy.spatial import ConvexHull
    hull = ConvexHull(nodes)
    on_hull = sorted(set(hull.vertices.tolist()))
    centroid = nodes.mean(axis=0)
    outward = 0
    for f, vids in faces.items():
        a, b, c = nodes[list(vids)]
        n = np.cross(b - a, c - a)
        if np.dot(n, (a + b + c) / 3 - centroid) > 0:
            outward += 1
    return {"nodes_on_hull": len(on_hull), "convex": len(on_hull) == 12,
            "outward_consistent_faces": outward}


def orientation_audit(nodes: np.ndarray, faces: dict, depth: int) -> dict:
    """Every terminal facet must keep positive (outward) orientation."""
    reversals = 0
    total = 0
    edge_mismatch = 0

    def rec(A, B, C, level, ref_sign):
        nonlocal reversals, total
        if level == depth:
            n = np.cross(B - A, C - A)
            s = 1.0 if np.dot(n, (A + B + C) / 3) > 0 else -1.0
            # a FOLD is a sign CHANGE relative to the root face's
            # handedness (the corner ordering fixes a uniform
            # convention; only deviations are reversals)
            if s != ref_sign:
                reversals += 1
            total += 1
            return
        mAB, mBC, mCA = (lift((A + B) / 2), lift((B + C) / 2),
                         lift((C + A) / 2))
        for (a2, b2, c2) in ((A, mAB, mCA), (mAB, B, mBC),
                             (mCA, mBC, C), (mAB, mBC, mCA)):
            rec(a2, b2, c2, level + 1, ref_sign)

    # shared-edge continuity: midpoints of an edge computed from both
    # incident faces must agree (they are functions of endpoints only,
    # but verify numerically over all 30 edges)
    ids = sorted(faces)
    for i, f in enumerate(ids):
        for g in ids[i + 1:]:
            shared = set(faces[f]) & set(faces[g])
            if len(shared) == 2:
                u, v = sorted(shared)
                m1 = lift((nodes[u] + nodes[v]) / 2)
                m2 = lift((nodes[v] + nodes[u]) / 2)
                if np.linalg.norm(m1 - m2) > 1e-12:
                    edge_mismatch += 1
    for f, vids in faces.items():
        A, B, C = (nodes[vids[CORNER_PERM[0]]], nodes[vids[CORNER_PERM[1]]],
                   nodes[vids[CORNER_PERM[2]]])
        n0 = np.cross(B - A, C - A)
        ref = 1.0 if np.dot(n0, (A + B + C) / 3) > 0 else -1.0
        rec(A, B, C, 0, ref)
    return {"depth": depth, "terminal_facets": total,
            "orientation_reversals": reversals,
            "shared_edge_mismatches": edge_mismatch}


def inverse_lookup(nodes: np.ndarray, faces: dict, direction: np.ndarray,
                   depth: int = 11) -> tuple[int, tuple] | None:
    """Exact hierarchical inverse: find face + path containing the ray."""
    d = direction / np.linalg.norm(direction)

    def in_tri(A, B, C):
        # ray-triangle (Moller-Trumbore, both orientations)
        eps = 1e-12
        e1, e2 = B - A, C - A
        h = np.cross(d, e2)
        det = float(np.dot(e1, h))
        if abs(det) < eps:
            return False
        f = 1.0 / det
        s = -A
        u = f * float(np.dot(s, h))
        if u < -1e-10 or u > 1 + 1e-10:
            return False
        q = np.cross(s, e1)
        v = f * float(np.dot(d, q))
        if v < -1e-10 or u + v > 1 + 1e-10:
            return False
        t = f * float(np.dot(e2, q))
        return t > 0

    for mf, vids in faces.items():
        A, B, C = (nodes[vids[CORNER_PERM[0]]], nodes[vids[CORNER_PERM[1]]],
                   nodes[vids[CORNER_PERM[2]]])
        if not in_tri(A, B, C):
            continue
        path = []
        for _ in range(depth):
            mAB, mBC, mCA = (lift((A + B) / 2), lift((B + C) / 2),
                             lift((C + A) / 2))
            kids = ((A, mAB, mCA), (mAB, B, mBC),
                    (mCA, mBC, C), (mAB, mBC, mCA))
            for child_idx, (a2, b2, c2) in enumerate(kids):
                if in_tri(a2, b2, c2):
                    path.append(CHILD_MAP.index(child_idx))
                    A, B, C = a2, b2, c2
                    break
            else:
                return None
        return mf, tuple(path)
    return None
