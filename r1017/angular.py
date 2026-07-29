"""R10.17 Phase 1 — angular hedron calibration, no warp.

For every point: containing root face, level-1 macrocell, level-2 cell,
nearest vertex and distance, nearest edge and distance, barycentric
coordinates in the containing triangle, and a VERTEX / EDGE /
FACE_INTERIOR / MONITOR_CELL classification.

Allowed freedoms are discrete and global: rigid frame rotation from
the sealed contexts, face offset 0-19, handedness, child order,
South-Up / North-Up. No mesh warp, no local deformation, no per-point
offset.

The decisive angular score is NOT distance to a nice place. It is
whether the geometric cell containing a point's claimed lat/lon agrees
with the face and path already encoded in that point's SurfaceWord.
"""

from __future__ import annotations

import math

import numpy as np

from cwatlas.r1085a import final_projection as fp
from r12 import icosarefine as rf

EARTH_R_KM = 6371.0088


def unit_from_latlon(lat_deg: float, lon_deg: float) -> np.ndarray:
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo), math.sin(la)])


def ground_to_mesh(p_ground: np.ndarray, rotation) -> np.ndarray:
    """Inverse of the mesh->ground rigid rotation."""
    return np.asarray(rotation, float).T @ np.asarray(p_ground, float)


def barycentric(p: np.ndarray, tri) -> np.ndarray:
    m = np.column_stack([np.asarray(v, float) for v in tri])
    w = np.linalg.solve(m, np.asarray(p, float))
    return w / w.sum()


def angular_km(a: np.ndarray, b: np.ndarray) -> float:
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    return EARTH_R_KM * math.acos(min(1.0, max(-1.0, float(a @ b))))


def point_to_segment_km(p, a, b, samples: int = 512) -> tuple:
    """Great-circle distance from p to the arc ab, by dense sampling."""
    a = np.asarray(a, float) / np.linalg.norm(a)
    b = np.asarray(b, float) / np.linalg.norm(b)
    best, best_t = float("inf"), 0.0
    for i in range(samples + 1):
        t = i / samples
        q = (1 - t) * a + t * b
        n = np.linalg.norm(q)
        if n == 0:
            continue
        d = angular_km(p, q / n)
        if d < best:
            best, best_t = d, t
    return best, best_t


def classify_point(lat: float, lon: float, rotation,
                   face_offset: int = 0, levels: int = 2) -> dict:
    """Full angular classification of one lat/lon."""
    p_ground = unit_from_latlon(lat, lon)
    p_mesh = ground_to_mesh(p_ground, rotation)
    face = fp._classify_face_mesh(p_mesh)
    face_eff = (face + face_offset) % 20
    path = fp._descend(face, p_mesh, levels=levels)
    tri_face = [np.asarray(v, float) for v in rf.face_triangle(face)]
    tri_cell = [np.asarray(v, float)
                for v in rf.cell_triangle(face, path)]

    bary_face = barycentric(p_mesh, tri_face)
    bary_cell = barycentric(p_mesh, tri_cell)

    # nearest vertex of the containing CELL and of the root FACE
    v_cell = min(range(3), key=lambda i: angular_km(p_mesh, tri_cell[i]))
    d_vertex_cell = angular_km(p_mesh, tri_cell[v_cell])
    v_face = min(range(3), key=lambda i: angular_km(p_mesh, tri_face[i]))
    d_vertex_face = angular_km(p_mesh, tri_face[v_face])

    # nearest edge of the containing cell
    edges = ((0, 1), (1, 2), (2, 0))
    d_edges = [point_to_segment_km(p_mesh, tri_cell[i], tri_cell[j])[0]
               for i, j in edges]
    e_idx = int(np.argmin(d_edges))
    d_edge_cell = d_edges[e_idx]

    # cell scale for a relative classification
    cell_edge_km = angular_km(tri_cell[0], tri_cell[1])
    rel_vertex = d_vertex_cell / cell_edge_km if cell_edge_km else 1.0
    rel_edge = d_edge_cell / cell_edge_km if cell_edge_km else 1.0
    if rel_vertex < 0.10:
        cls = "VERTEX"
    elif rel_edge < 0.10:
        cls = "EDGE"
    elif min(bary_cell) > 0.20:
        cls = "FACE_INTERIOR"
    else:
        cls = "MONITOR_CELL"

    return {
        "lat": lat, "lon": lon,
        "root_face": face, "root_face_with_offset": face_eff,
        "level1_macrocell": path[0] if path else None,
        "level2_cell": path[1] if len(path) > 1 else None,
        "path": list(path),
        "barycentric_face": [round(float(x), 6) for x in bary_face],
        "barycentric_cell": [round(float(x), 6) for x in bary_cell],
        "nearest_face_vertex_index": v_face,
        "nearest_face_vertex_km": d_vertex_face,
        "nearest_cell_vertex_index": v_cell,
        "nearest_cell_vertex_km": d_vertex_cell,
        "nearest_cell_edge": f"{edges[e_idx][0]}-{edges[e_idx][1]}",
        "nearest_cell_edge_km": d_edge_cell,
        "cell_edge_length_km": cell_edge_km,
        "relative_vertex_distance": rel_vertex,
        "relative_edge_distance": rel_edge,
        "classification": cls,
    }


def surface_word_face(word: int) -> int:
    return (int(word) >> 25) & 0b11111


def surface_word_path(word: int, levels: int = 2) -> list:
    """Leading path levels encoded in Q22 (2 bits per level)."""
    q22 = (int(word) >> 3) & ((1 << 22) - 1)
    bits = format(q22, "022b")
    return [int(bits[2 * i:2 * i + 2], 2) for i in range(levels)]


def address_agreement(point, rotation, face_offset: int = 0) -> dict:
    """Does the GEOMETRY agree with the ADDRESS for this point?

    This is the angular score that matters: no place names, just
    whether the cell containing the claimed lat/lon is the cell the
    SurfaceWord already names.
    """
    if point.surface_word is None or point.lat is None:
        return {"point_id": point.point_id, "testable": False,
                "reason": "no surface word or no coordinate"}
    geo = classify_point(point.lat, point.lon, rotation, face_offset)
    addr_face = surface_word_face(point.surface_word)
    addr_path = surface_word_path(point.surface_word, 2)
    return {
        "point_id": point.point_id, "testable": True,
        "geometric_face": geo["root_face_with_offset"],
        "address_face": addr_face,
        "face_match": geo["root_face_with_offset"] == addr_face,
        "geometric_path": geo["path"][:2],
        "address_path": addr_path,
        "level1_match": (geo["level1_macrocell"] == addr_path[0]),
        "level2_match": (geo["level2_cell"] == addr_path[1]),
        "classification": geo["classification"],
    }
