"""R10.25 Agent 02 — Terra projector solver.

METHOD: DERIVE, THEN REFUTE. Nothing is searched for a match.

For a fixed candidate (hedron family, orientation, handedness, pole,
depth offset, width model) the geometry already fixes which cell
contains each anchor. So the required maps are FORCED:

    F5      -> containing root face
    Q22[k]  -> containing child index at that level

Both are then tested for function consistency (one input may not demand
two different outputs) and injectivity. A contradiction REFUTES that
candidate outright, which is far stronger evidence than failing to find
a match by search.

Cells are compared by CONTAINMENT of the point in the addressed cell,
never by per-level index equality -- comparing a bare child index across
different parents is a category error (R10.18).

NO MESH WARP: the rotation is applied globally to every point; there is
no per-anchor adjustment anywhere in this module.
NO PLACE-NAME SCORING: only vectors and coordinates enter.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from r1016.quarantine import assert_clean
from r1025 import hedra

Q22_SYMBOLS = 11


def unit_from_latlon(lat_deg: float, lon_deg: float) -> np.ndarray:
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo), math.sin(la)])


def flip(lat, lon, handedness, pole):
    if pole == "north_up":
        lat, lon = -lat, lon + 180.0
    if handedness == "mirrored":
        lon = -lon
    return lat, ((lon + 180.0) % 360.0) - 180.0


def bary(tri, p) -> np.ndarray:
    m = np.column_stack([np.asarray(v, float) for v in tri])
    w = np.linalg.solve(m, np.asarray(p, float))
    return w / w.sum()


def contains(tri, p, tol: float = -1e-12) -> bool:
    try:
        return bool(min(bary(tri, p)) > tol)
    except np.linalg.LinAlgError:            # pragma: no cover
        return False


def fields(v: int) -> tuple:
    return (v >> 25) & 31, (v >> 3) & ((1 << 22) - 1), v & 7


def q22_symbols(q: int) -> list:
    return [(q >> (20 - 2 * i)) & 3 for i in range(Q22_SYMBOLS)]


@dataclass(frozen=True)
class Anchor:
    name: str
    vector: int
    lat: float
    lon: float

    @property
    def f5(self) -> int:
        return fields(self.vector)[0]

    @property
    def s3(self) -> int:
        return fields(self.vector)[2]

    @property
    def path(self) -> list:
        return q22_symbols(fields(self.vector)[1])


HARD_ANCHORS = (
    Anchor("STONEHENGE", 165876523, 51.1789, -1.8262),
    Anchor("ERIE", 167849523, 42.1292, -80.0851),
    Anchor("TORONTO", 168930443, 43.6532, -79.3832),
)


def containing_lineage(h, lat, lon, rotation, handedness, pole,
                       depth: int, branch: int = 4) -> dict:
    """The cell that ACTUALLY contains the point, by explicit descent."""
    lat, lon = flip(lat, lon, handedness, pole)
    p = np.asarray(rotation, float).T @ unit_from_latlon(lat, lon)
    face, best = None, -np.inf
    for f in range(h.face_count):
        w = float(min(bary(h.face_triangle(f), p)))
        if w > best:
            face, best = f, w
    tri = h.face_triangle(face)
    split = hedra.subdivide if branch == 4 else hedra.subdivide8
    path, flags = [], []
    for lvl in range(depth):
        kids = split(tri)
        hit = [i for i, k in enumerate(kids) if contains(k, p)]
        if len(hit) == 1:
            idx = hit[0]
        else:
            idx = max(range(len(kids)),
                      key=lambda i: float(min(bary(kids[i], p))))
            flags.append(f"L{lvl + 1}:{'ambiguous' if hit else 'edge'}")
        path.append(idx)
        tri = kids[idx]
    return {"face": face, "path": tuple(path), "face_bary_min": best,
            "flags": flags,
            "cell_id": f"F{face}:" + ".".join(str(x) for x in path)}


def _consistent_map(pairs) -> tuple:
    """Forced map from (input, output) pairs; None on contradiction."""
    m = {}
    for a, b in pairs:
        if a in m and m[a] != b:
            return None, f"{a} -> {m[a]} and {b}"
        m[a] = b
    inv = {}
    for a, b in m.items():
        if b in inv:
            return None, f"non-injective: {inv[b]} and {a} -> {b}"
        inv[b] = a
    return m, None


@dataclass(frozen=True)
class Candidate:
    hedron: str
    orientation: str
    handedness: str
    pole: str
    depth_offset: int          # leading Q22 symbols treated as non-spatial
    branch: int                # 4 = quaternary child, 8 = octal child
    child_model: str           # UNIFORM (low DOF) or PER_LEVEL (high DOF)

    @property
    def id(self) -> str:
        return (f"{self.hedron}/{self.orientation}/{self.handedness[:3]}/"
                f"{self.pole[:5]}/off{self.depth_offset}/b{self.branch}/"
                f"{self.child_model}")


def evaluate(cand: Candidate, h, rotation, anchors, spatial_depth: int) -> dict:
    """Derive the forced maps and try to refute them."""
    assert_clean([a.vector for a in anchors], where="R10.25 projector scoring")
    face_pairs, child_pairs, per_level, geo = [], [], {}, {}
    for a in anchors:
        g = containing_lineage(h, a.lat, a.lon, rotation, cand.handedness,
                               cand.pole, spatial_depth, cand.branch)
        geo[a.name] = g
        face_pairs.append((a.f5, g["face"]))
        syms = a.path[cand.depth_offset:]
        for k in range(spatial_depth):
            if k >= len(syms):
                break
            child_pairs.append((syms[k], g["path"][k]))
            per_level.setdefault(k, []).append((syms[k], g["path"][k]))

    face_map, face_err = _consistent_map(face_pairs)
    if cand.child_model == "UNIFORM":
        child_map, child_err = _consistent_map(child_pairs)
        level_maps = None
    else:
        child_map, child_err, level_maps = None, None, {}
        for k, pairs in per_level.items():
            lm, err = _consistent_map(pairs)
            level_maps[k] = lm
            if lm is None:
                child_err = f"level {k}: {err}"
                break

    level_ok = bool(level_maps) and all(
        v is not None for v in (level_maps or {}).values())
    maps_ok = bool(face_map) and (bool(child_map) or level_ok)

    verified, rows = 0, []
    if maps_ok:
        for a in anchors:
            f = face_map.get(a.f5)
            syms = a.path[cand.depth_offset:][:spatial_depth]
            if f is None:
                continue
            if cand.child_model == "UNIFORM":
                path = tuple(child_map.get(x) for x in syms)
            else:
                path = tuple(level_maps[k].get(syms[k])
                             for k in range(len(syms)))
            if any(x is None for x in path):
                continue
            lat, lon = flip(a.lat, a.lon, cand.handedness, cand.pole)
            p = np.asarray(rotation, float).T @ unit_from_latlon(lat, lon)
            tri = h.face_triangle(f)
            split = (hedra.subdivide if cand.branch == 4
                     else hedra.subdivide8)
            for idx in path:
                tri = split(tri)[idx]
            ok = contains(tri, p)
            verified += ok
            rows.append({"anchor": a.name,
                         "addressed_cell": f"F{f}:" +
                                           ".".join(str(x) for x in path),
                         "geometric_cell": geo[a.name]["cell_id"],
                         "inside": ok})

    reason = None
    if face_err:
        reason = f"FACE_MAP_CONTRADICTION: {face_err}"
    elif child_err:
        reason = f"CHILD_MAP_CONTRADICTION: {child_err}"
    elif verified < len(anchors):
        reason = (f"CONTAINMENT_FAIL: {verified}/{len(anchors)} anchors "
                  f"inside their addressed cell")
    return {
        "candidate_id": cand.id, "hedron": cand.hedron,
        "orientation": cand.orientation, "handedness": cand.handedness,
        "pole": cand.pole, "depth_offset": cand.depth_offset,
        "branch": cand.branch, "child_model": cand.child_model,
        "spatial_depth": spatial_depth,
        "face_map": face_map, "child_map": child_map,
        "level_maps": level_maps,
        "maps_consistent": maps_ok,
        "anchors_verified": verified, "anchors_total": len(anchors),
        "survivor": maps_ok and verified == len(anchors),
        "rejection_reason": reason,
        "rows": rows,
        "child_constraints": len(child_pairs),
        "distinct_f5": len({a.f5 for a in anchors}),
    }
