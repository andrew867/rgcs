"""R10.17 Phase 1 — discrete angular variant search scored on ADDRESS
AGREEMENT rather than on kilometres to a claimed place.

Every previous run scored the angular layer by great-circle distance
between a projected point and a named place. That conflates two
questions. This scores the only question the angular layer can answer
on its own: does the geometric cell containing a point's claimed
lat/lon carry the same face and path that the point's SurfaceWord
already encodes?

Freedoms are discrete and global: sealed rotation context, face offset
0-19, handedness, pole, and -- because the mesh face NUMBERING is a
convention rather than a measurement -- an optional face PERMUTATION
drawn from a declared finite set. No mesh warp, no local deformation,
no per-point freedom.
"""

from __future__ import annotations

import itertools

import numpy as np

from cwatlas.r1085a import final_projection as fp
from r1017.angular import (classify_point, surface_word_face,
                           surface_word_path, unit_from_latlon)


def _rotations(contexts=("ALL_SEALED",)) -> dict:
    frame, _ = fp.training_alignment(2025.0)
    rots = {"TRAINED": np.asarray(frame.rotation, float)}
    for ctx, rot in fp.sealed_contexts().items():
        rots[ctx] = np.asarray(rot, float)
    return rots


def _flip(lat, lon, handedness, pole):
    if pole == "north_up":
        lat, lon = -lat, lon + 180.0
    if handedness == "mirrored":
        lon = -lon
    return lat, ((lon + 180.0) % 360.0) - 180.0


def score_variant(points, rotation, face_offset: int,
                  handedness: str, pole: str,
                  permutation: dict | None = None) -> dict:
    """Agreement score for one discrete variant."""
    rows, face_hits, l1_hits, l2_hits, n = [], 0, 0, 0, 0
    for p in points:
        if p.surface_word is None or p.lat is None:
            continue
        lat, lon = _flip(p.lat, p.lon, handedness, pole)
        geo = classify_point(lat, lon, rotation, 0)
        gf = geo["root_face"]
        gf = permutation.get(gf, gf) if permutation else \
            (gf + face_offset) % 20
        af = surface_word_face(p.surface_word)
        ap = surface_word_path(p.surface_word, 2)
        fm = gf == af
        l1 = geo["level1_macrocell"] == ap[0]
        l2 = geo["level2_cell"] == ap[1]
        face_hits += fm
        l1_hits += l1
        l2_hits += l2
        n += 1
        rows.append({"point_id": p.point_id, "geometric_face": gf,
                     "address_face": af, "face_match": fm,
                     "geometric_path": geo["path"][:2],
                     "address_path": ap, "level1_match": l1,
                     "level2_match": l2})
    total = face_hits + l1_hits + l2_hits
    return {"face_matches": face_hits, "level1_matches": l1_hits,
            "level2_matches": l2_hits, "points": n,
            "total_score": total, "max_score": 3 * n,
            "full_agreement": total == 3 * n and n > 0,
            "rows": rows}


def search(points, contexts=("ALL_SEALED",),
           allow_permutation: bool = True) -> dict:
    """Exhaust the discrete angular variant space."""
    rots = _rotations(contexts)
    results = []
    for ctx, rot in rots.items():
        for fo in range(20):
            for hd in ("right", "mirrored"):
                for po in ("south_up", "north_up"):
                    s = score_variant(points, rot, fo, hd, po)
                    results.append({
                        "variant_id": f"{ctx}/F{fo:02d}/{hd[:3]}/{po[:5]}",
                        "context": ctx, "face_offset": fo,
                        "handedness": hd, "pole": po,
                        "permutation": None, **s})
    # A face PERMUTATION is a relabeling of a numbering convention, not
    # a deformation. It is searched only as a declared fallback and is
    # marked so it can never be mistaken for a geometric result.
    perm_results = []
    if allow_permutation:
        for ctx, rot in rots.items():
            for hd in ("right", "mirrored"):
                for po in ("south_up", "north_up"):
                    perm = _fit_permutation(points, rot, hd, po)
                    if perm is None:
                        continue
                    s = score_variant(points, rot, 0, hd, po, perm)
                    perm_results.append({
                        "variant_id":
                            f"{ctx}/PERM/{hd[:3]}/{po[:5]}",
                        "context": ctx, "face_offset": None,
                        "handedness": hd, "pole": po,
                        "permutation": perm,
                        "permutation_status":
                            "FACE_RELABELING_DIAGNOSTIC",
                        **s})
    results.sort(key=lambda r: -r["total_score"])
    perm_results.sort(key=lambda r: -r["total_score"])
    return {
        "schema": "rgcs.r1017.angular-search.v1",
        "variants_evaluated": len(results),
        "permutation_variants": len(perm_results),
        "best": results[0] if results else None,
        "best_permutation": perm_results[0] if perm_results else None,
        "full_agreement_variants": [r for r in results
                                    if r["full_agreement"]],
        "top": results[:12],
        "top_permutation": perm_results[:6],
    }


def _fit_permutation(points, rotation, handedness, pole):
    """The face relabeling implied by the points, if it is consistent.

    A relabeling is only admissible when it is a FUNCTION: one
    geometric face may not be asked to carry two different address
    faces. That consistency check is the whole value of this step.
    """
    mapping = {}
    for p in points:
        if p.surface_word is None or p.lat is None:
            continue
        lat, lon = _flip(p.lat, p.lon, handedness, pole)
        gf = classify_point(lat, lon, rotation, 0)["root_face"]
        af = surface_word_face(p.surface_word)
        if gf in mapping and mapping[gf] != af:
            return None                     # inconsistent relabeling
        mapping[gf] = af
    return mapping or None
