"""R10.18 Phase 3 — solve F5 -> face and Q22 -> child lineage.

The maps are DERIVED, not searched. For a fixed frame variant the
geometry already fixes which cell contains each anchor, so:

  * the face map is forced by  F5 -> containing_root_face;
  * the child map is forced by Q22[k] -> containing_path[k].

Both are then tested for FUNCTION CONSISTENCY: one input may not
demand two different outputs. A contradiction refutes that frame
variant outright, which is far stronger than failing to find a match
by search.

Cells are compared by CONTAINMENT of the point in the addressed cell,
never by per-level index equality.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from cwatlas.r1085a import final_projection as fp
from r12 import icosarefine as rf
from r1018.lineage import bary, contains


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


def frames(contexts=None) -> dict:
    frame, _ = fp.training_alignment(2025.0)
    out = {"TRAINED": np.asarray(frame.rotation, float)}
    for ctx, rot in fp.sealed_contexts().items():
        out[ctx] = np.asarray(rot, float)
    if contexts:
        out = {k: v for k, v in out.items() if k in contexts}
    return out


def containing_lineage(lat, lon, rotation, handedness, pole,
                       depth: int = 11) -> dict:
    """The cell that actually contains the point, by explicit descent.

    Descent picks the child that CONTAINS the point; if none contains
    it (numerical edge case), the best barycentric child is taken and
    the step is flagged.
    """
    lat, lon = flip(lat, lon, handedness, pole)
    p_ground = unit_from_latlon(lat, lon)
    p = np.asarray(rotation, float).T @ p_ground
    face, best = None, -np.inf
    for f in range(20):
        w = min(bary(rf.face_triangle(f), p))
        if w > best:
            face, best = f, w
    tri = tuple(np.asarray(v, float) for v in rf.face_triangle(face))
    path, flags = [], []
    for lvl in range(depth):
        kids = rf._subdivide(tri)
        hit = [i for i, k in enumerate(kids) if contains(k, p)]
        if len(hit) == 1:
            idx = hit[0]
        else:
            idx = max(range(4), key=lambda i: min(bary(kids[i], p)))
            flags.append(f"L{lvl + 1}:{'ambiguous' if hit else 'edge'}")
        path.append(idx)
        tri = tuple(np.asarray(v, float) for v in kids[idx])
    return {"face": face, "path": tuple(path),
            "face_bary_min": best, "flags": flags,
            "cell_id": f"F{face}:" + ".".join(str(x) for x in path)}


def _consistent_map(pairs) -> tuple:
    """Build a map from (input, output) pairs; None if contradictory."""
    m = {}
    for a, b in pairs:
        if a in m and m[a] != b:
            return None, f"{a} -> {m[a]} and {b}"
    for a, b in pairs:
        m[a] = b
    inv = {}
    for a, b in m.items():
        if b in inv:
            return None, f"non-injective: {inv[b]} and {a} -> {b}"
        inv[b] = a
    return m, None


@dataclass
class AnchorSpec:
    name: str
    lat: float
    lon: float
    f5: int
    q22: tuple
    surface_word: int
    profile: str = "canonical"


def solve_variant(anchors, rotation, handedness, pole,
                  levels: int = 2, uniform_child: bool = True) -> dict:
    """Derive and test the required maps for one frame variant."""
    face_pairs, child_pairs, per_level = [], [], {}
    geo = {}
    for a in anchors:
        g = containing_lineage(a.lat, a.lon, rotation, handedness,
                               pole, depth=levels)
        geo[a.name] = g
        face_pairs.append((a.f5, g["face"]))
        for k in range(levels):
            child_pairs.append((a.q22[k], g["path"][k]))
            per_level.setdefault(k, []).append(
                (a.q22[k], g["path"][k]))

    face_map, face_err = _consistent_map(face_pairs)
    if uniform_child:
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

    # Containment verification: does each point actually sit inside the
    # cell its address names under the derived maps?
    verified, rows = 0, []
    level_maps_ok = bool(level_maps) and all(
        v is not None for v in (level_maps or {}).values())
    if face_map and (child_map or level_maps_ok):
        for a in anchors:
            f = face_map.get(a.f5)
            if f is None:
                continue
            if uniform_child:
                path = tuple(child_map.get(x) for x in a.q22[:levels])
            else:
                path = tuple(level_maps[k].get(a.q22[k])
                             for k in range(levels))
            if any(x is None for x in path):
                continue
            lat, lon = flip(a.lat, a.lon, handedness, pole)
            p = np.asarray(rotation, float).T @ unit_from_latlon(lat, lon)
            tri = rf.cell_triangle(f, path)
            ok = contains(tri, p)
            verified += ok
            rows.append({"anchor": a.name, "addressed_cell":
                         f"F{f}:" + ".".join(str(x) for x in path),
                         "geometric_cell": geo[a.name]["cell_id"],
                         "point_inside_addressed_cell": ok})
    return {
        "handedness": handedness, "pole": pole,
        "face_map": face_map, "face_contradiction": face_err,
        "child_map": child_map, "level_maps": level_maps,
        "child_contradiction": child_err,
        "maps_consistent": bool(face_map) and bool(
            child_map or level_maps_ok),
        "anchors_verified_by_containment": verified,
        "anchors_total": len(anchors),
        "rows": rows,
        "geometric": {k: v["cell_id"] for k, v in geo.items()},
    }


def solve(anchors, levels: int = 2, contexts=None) -> dict:
    results = []
    for ctx, rot in frames(contexts).items():
        for hd in ("right", "mirrored"):
            for po in ("south_up", "north_up"):
                for uniform in (True, False):
                    r = solve_variant(anchors, rot, hd, po, levels,
                                      uniform)
                    r["context"] = ctx
                    r["child_model"] = ("UNIFORM"
                                        if uniform else "PER_LEVEL")
                    r["variant_id"] = (f"{ctx}/{hd[:3]}/{po[:5]}/"
                                       f"{r['child_model']}")
                    results.append(r)
    results.sort(key=lambda r: (-r["anchors_verified_by_containment"],
                                not r["maps_consistent"]))
    survivors = [r for r in results
                 if r["anchors_verified_by_containment"]
                 == r["anchors_total"] and r["maps_consistent"]]
    return {
        "schema": "rgcs.r1018.projector-solve.v1",
        "variants": len(results),
        "consistent_map_variants": sum(1 for r in results
                                       if r["maps_consistent"]),
        "survivors": survivors,
        "best": results[0] if results else None,
        "top": results[:10],
    }
