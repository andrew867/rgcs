"""Root-relative source-face codebooks (R10.8.4 §7).

Five finite, declared codebooks map :class:`SourceFaceID` <->
:class:`PhysicalMeshFaceID` deterministically from the locked frame (Wilkes
root face, SAA azimuth, South-Up, clockwise above Antarctica). Source face
17 is never equated with mesh-array face 17 except through one of these
explicit permutations.
"""

from __future__ import annotations

import itertools
import math

import numpy as np

from cwatlas.icosahedron import build_icosahedron

CODEBOOK_IDS = ("A_BFS_RINGS_CW_FROM_SAA", "B_ANTIPODAL_PAIRS",
                "C_XYZ_NORMAL_ORDER", "D_CW_DUAL_SPIRAL",
                "E_VERTEX_TRIPLE_CANONICAL")


def face_adjacency(ico) -> dict:
    adj = {i: [] for i in range(20)}
    for i, j in itertools.combinations(range(20), 2):
        if len(set(ico.faces[i]) & set(ico.faces[j])) == 2:
            adj[i].append(j)
            adj[j].append(i)
    return adj


def _azimuth_cw(center_from, target, ref_dir):
    """Clockwise angle of ``target`` about ``center_from`` from ``ref_dir``
    (external viewpoint; matches the locked CLOCKWISE positive rotation)."""
    n = center_from / np.linalg.norm(center_from)
    t = target - (target @ n) * n
    r = ref_dir - (ref_dir @ n) * n
    if np.linalg.norm(t) < 1e-12 or np.linalg.norm(r) < 1e-12:
        return 0.0
    t = t / np.linalg.norm(t)
    r = r / np.linalg.norm(r)
    ang = math.atan2(float(np.cross(r, t) @ n), float(r @ t))
    return (-ang) % (2 * math.pi)


def build_codebooks(root_face: int, saa_dir) -> dict:
    """All five codebooks as source-id -> mesh-id orderings (bijections).

    ``root_face`` is the mesh face containing the Wilkes direction in the
    working frame; ``saa_dir`` is the SAA phase-zero direction in the same
    frame. Both come from the sealed root certificate upstream.
    """
    ico = build_icosahedron()
    centers = ico.face_normals
    adj = face_adjacency(ico)
    rootc = centers[root_face]

    def cw(faces):
        return sorted(faces, key=lambda f: (
            round(_azimuth_cw(rootc, centers[f], saa_dir), 9), f))

    rings, seen, frontier = [[root_face]], {root_face}, [root_face]
    while len(seen) < 20:
        nxt = sorted({n for f in frontier for n in adj[f]} - seen)
        frontier = cw(nxt)
        rings.append(frontier)
        seen |= set(frontier)
    bfs = [f for ring in rings for f in ring]

    ant = {i: int(np.argmin(centers @ centers[i])) for i in range(20)}
    pairs, used = [], set()
    for f in bfs:
        if f not in used:
            pairs.append((f, ant[f]))
            used |= {f, ant[f]}
    antipodal = [f for p in pairs for f in p]

    xyz = sorted(range(20), key=lambda f: (
        -round(centers[f][2], 9),
        round(math.atan2(-centers[f][1], centers[f][0]), 9)))

    spiral, cur = [root_face], root_face
    while len(spiral) < 20:
        cand = [n for n in adj[cur] if n not in spiral]
        if not cand:
            cand = [f for f in bfs if f not in spiral]
        cur = min(cand, key=lambda f: (
            round(_azimuth_cw(rootc, centers[f], saa_dir), 9), f))
        spiral.append(cur)

    canonical = sorted(range(20), key=lambda f: tuple(sorted(ico.faces[f])))

    books = {"A_BFS_RINGS_CW_FROM_SAA": bfs,
             "B_ANTIPODAL_PAIRS": antipodal,
             "C_XYZ_NORMAL_ORDER": xyz,
             "D_CW_DUAL_SPIRAL": spiral,
             "E_VERTEX_TRIPLE_CANONICAL": canonical}
    for name, order in books.items():
        if sorted(order) != list(range(20)):
            raise AssertionError(f"codebook {name} is not a bijection")
    return books
