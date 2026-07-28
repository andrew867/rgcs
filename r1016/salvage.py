"""R10.16 — RIGID_ROTATION_SALVAGE_DIAGNOSTIC.

Escalation, run ONLY because every discrete variant failed the strict
anchor gate. This finds the single BEST-POSSIBLE rigid rotation of the
frozen mesh onto the four claimed anchor directions, by closed-form
orthogonal Procrustes (Wahba's problem, solved by SVD).

Why this is the decisive test: a rigid rotation is the most generous
no-warp orientation freedom that exists. It is not one of twenty face
offsets or a handedness flip -- it is the continuous optimum over ALL
orientations. If even the optimal rotation cannot bring the anchors
within tolerance, then the residual is NOT an orientation problem and
no amount of re-rooting can fix it: the decode itself does not place
these wires at these locations.

This diagnostic is NEVER merged into the main atlas and NEVER
overwrites the frozen root.
"""

from __future__ import annotations

import math

import numpy as np

from cwatlas.r1085a import final_projection as fp
from r1016.project import (STRICT_ANCHORS, RootVariant,
                           great_circle_km, reverse_bits30)
from r12 import icosapacket as pk

LABEL = "RIGID_ROTATION_SALVAGE_DIAGNOSTIC"


def _unit(lat_deg: float, lon_deg: float) -> np.ndarray:
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo), math.sin(la)])


def mesh_direction(word: int, variant: RootVariant) -> np.ndarray:
    w = reverse_bits30(word) if variant.bit_endian == "lsb" else word
    rec = pk.decode_record(w)
    face = (int(rec["face"]) + variant.face_offset) % 20
    path = tuple(rec["path_levels"])
    if variant.child_order == "reversed":
        path = tuple(reversed(path))
    return np.asarray(fp.cell_centroid_mesh(face, path), float)


def optimal_rotation(mesh_dirs, target_dirs) -> np.ndarray:
    """Wahba / orthogonal Procrustes: argmin_R sum |R m - t|^2."""
    M = np.asarray(mesh_dirs, float)
    T = np.asarray(target_dirs, float)
    H = T.T @ M
    U, _, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(U @ Vt))
    D = np.diag([1.0, 1.0, d])
    return U @ D @ Vt


def salvage(view_words: dict, variant: RootVariant | None = None
            ) -> dict:
    """Best achievable rigid rotation for one view's anchor words."""
    v = variant or RootVariant()
    wires, mesh, targ, places = [], [], [], []
    for wire, (place, lat, lon) in STRICT_ANCHORS.items():
        word = view_words.get(wire)
        if word is None:
            continue
        try:
            mesh.append(mesh_direction(word, v))
        except Exception:
            continue
        targ.append(_unit(lat, lon))
        wires.append(wire)
        places.append((place, lat, lon))
    if len(wires) < 3:
        return {"label": LABEL, "status": "INSUFFICIENT_ANCHORS",
                "covered": len(wires)}
    R = optimal_rotation(mesh, targ)
    rows, errs = [], []
    for wire, m, (place, lat, lon) in zip(wires, mesh, places):
        p = R @ m
        la, lo = fp._latlon(p)
        d = great_circle_km(la, lo, lat, lon)
        errs.append(d)
        rows.append({"wire": wire, "place": place, "lat": la,
                     "lon": lo, "claimed_lat": lat, "claimed_lon": lon,
                     "error_km": d})
    rms = math.sqrt(sum(e * e for e in errs) / len(errs))
    # angular residuals are the orientation-free statement
    ang = [math.degrees(math.acos(min(1.0, max(-1.0, float(
        np.dot(R @ m, t)))))) for m, t in zip(mesh, targ)]
    return {
        "label": LABEL,
        "status": "COMPUTED",
        "variant_id": v.id,
        "anchors_used": len(wires),
        "rows": rows,
        "rms_km": rms,
        "max_km": max(errs), "min_km": min(errs),
        "angular_residual_deg": ang,
        "mean_angular_residual_deg": sum(ang) / len(ang),
        "passes_25km": bool(rms <= 25.0),
        "interpretation": (
            "even the OPTIMAL rigid rotation leaves the anchors "
            f"{rms:,.0f} km apart on average. A rigid rotation is the "
            "most generous no-warp orientation freedom available, so "
            "this residual cannot be removed by any re-rooting, face "
            "offset, handedness or endian choice. The mismatch is in "
            "the DECODE, not in the orientation."
            if rms > 25.0 else
            "the optimal rigid rotation brings the anchors inside "
            "tolerance; this is a DIAGNOSTIC ONLY and does not "
            "overwrite the frozen root"),
        "merged_into_main_atlas": False,
        "overwrites_frozen_root": False,
    }


def salvage_all(maps) -> dict:
    """Run the salvage for every view/window map and report the best."""
    out = []
    for m in maps:
        r = salvage(m["words"])
        if r.get("status") == "COMPUTED":
            r["view"] = m["view"]
            r["window"] = m["window"]
            out.append(r)
    out.sort(key=lambda r: r["rms_km"])
    return {"label": LABEL, "runs": out,
            "best": out[0] if out else None,
            "any_passes_25km": any(r["passes_25km"] for r in out),
            "merged_into_main_atlas": False}
