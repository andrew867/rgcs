"""R10.11F-A analytic solve — ratio-driven shared-edge refinement.

The 627-step fitted warp is REVOKED (operator retraction, verbatim in
the pack). No fitted mesh substitutes. Active construction:

    frozen B0 + analytic T frame (Wilkes/SAA-clocked rigid solid)
    -> ratio-driven shared-edge refinement (source-approved r = 10/9,
       split fraction q = r/(1+r) = 10/19, canonical edge orientation:
       lower global node id -> higher)
    -> WGS84 realization for distances

Frozen anchors (Stonehenge/Erie/Toronto/Montreal/orange) act ONLY as
checks after the source-approved law is applied — they select nothing.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

import numpy as np

import rgcs_coordinate as rc
from r109 import earth_v2 as e2

OUT = Path("docs/r1011/evidence/r1011fa")
R_PRIMARY = 10 / 9
Q = R_PRIMARY / (1 + R_PRIMARY)          # 10/19
CORNER_PERM = (1, 0, 2)
CHILD_MAP = (2, 1, 0, 3)

FAMILY = {"1": 1.0, "10/9": 10 / 9, "9/8": 9 / 8, "81/80": 81 / 80,
          "55/54": 55 / 54, "(10/9)^-1": 9 / 10, "(9/8)^-1": 8 / 9,
          "(81/80)^-1": 80 / 81, "(55/54)^-1": 54 / 55}
PHI = (1 + 5 ** 0.5) / 2
IRRATIONALS = {"phi/ (phi+ .5)": PHI / (PHI + 0.5), "sqrt(5)/2": 5 ** 0.5 / 2,
               "phi^2/ (phi^2 - .5)": PHI ** 2 / (PHI ** 2 - 0.5),
               "sqrt(2)-0.3": 2 ** 0.5 - 0.3, "2-phi+0.2": 2 - PHI + 0.2}


def unit(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo), math.sin(la)])


def latlon(v):
    v = np.asarray(v, float) / np.linalg.norm(v)
    return (math.degrees(math.asin(np.clip(v[2], -1, 1))),
            math.degrees(math.atan2(v[1], v[0])))


def ang(a, b):
    return math.degrees(math.acos(float(np.clip(np.dot(a, b), -1, 1))))


def split_point(a, b, q):
    """Spherical split at arc fraction q from a toward b."""
    om = math.acos(float(np.clip(np.dot(a, b), -1, 1)))
    if om < 1e-15:
        return a
    v = (math.sin((1 - q) * om) * a + math.sin(q * om) * b) / math.sin(om)
    return v / np.linalg.norm(v)


def load_frame():
    verts = {}
    for row in csv.DictReader(open(e2.V1_DIR / "MAPPED_ICOSAHEDRON_VERTICES.csv")):
        v = np.array([float(row["source_x"]), float(row["source_y"]),
                      float(row["source_z"])])
        verts[int(row["vertex_id"])] = v / np.linalg.norm(v)
    faces = {}
    for row in csv.DictReader(open(e2.V1_DIR / "MAPPED_FACE_CENTROIDS.csv")):
        faces[int(row["mesh_face"])] = tuple(int(x)
                                             for x in row["vertex_ids"].split())
    return verts, faces


def decode_compensated(verts, faces, mesh_face, path, q):
    """Recursive decode with ratio-driven shared-edge splits.

    Canonical orientation is tracked by carrying each corner's GLOBAL
    ancestry key (tuple); an edge splits at fraction q from the corner
    with the LOWER key toward the higher — identical from both incident
    faces (shared-edge exactness by construction)."""
    vids = faces[mesh_face]
    corners = [(verts[vids[CORNER_PERM[i]]], f"{vids[CORNER_PERM[i]]:03d}")
               for i in range(3)]

    def esplit(ca, cb):
        (va, ka), (vb, kb) = ca, cb
        # canonical orientation: split q of the way from the LOWER key
        # toward the higher — string keys are globally comparable, so
        # both incident faces derive the identical point.
        if ka <= kb:
            p = split_point(va, vb, q)
            key = f"({ka}|{kb})"
        else:
            p = split_point(vb, va, q)
            key = f"({kb}|{ka})"
        return (p, key)

    A, B, C = corners
    for pdig in path:
        mAB, mBC, mCA = esplit(A, B), esplit(B, C), esplit(C, A)
        A, B, C = [(A, mAB, mCA), (mAB, B, mBC),
                   (mCA, mBC, C), (mAB, mBC, mCA)][CHILD_MAP[pdig]]
    cen = A[0] + B[0] + C[0]
    return cen / np.linalg.norm(cen)


ANCHORS = [("STONEHENGE", 165876523, 12, (51.17881944444445, -1.8262805555555555)),
           ("ERIE", 167849523, 19, (42.114507, -80.076213)),
           ("TORONTO", 168930443, 19, (43.6532, -79.3832)),
           ("MONTREAL_DIRECT", 165879243, 12, (45.508822, -73.554077)),
           ("ORANGE_A", 165892743, 12, (49.87628265441528, -2.6955552559494955))]


def main():
    verts, faces = load_frame()
    rows = []
    for law_name, r in {**FAMILY, **{f"IRR:{k}": v for k, v in
                                     IRRATIONALS.items()}}.items():
        q = r / (1 + r)
        errs = []
        for name, raw, mf, tgt in ANCHORS:
            path = rc.decode_coordinate(raw).to_dict()["q22_path"]
            p = decode_compensated(verts, faces, mf, path, q)
            errs.append(ang(p, unit(*tgt)))
        rows.append({"law": law_name, "ratio": r, "q": q,
                     "anchor_rms_deg": float(np.sqrt(np.mean(np.array(errs) ** 2))),
                     "anchor_max_deg": max(errs),
                     **{ANCHORS[i][0]: round(errs[i], 4)
                        for i in range(len(ANCHORS))},
                     "class": "IRRATIONAL_SECONDARY" if law_name.startswith("IRR")
                     else ("PRIMARY_SOURCE_APPROVED" if law_name == "10/9"
                           else "PREREGISTERED_CONTROL")})
    rows.sort(key=lambda x: x["anchor_rms_deg"])
    with open(OUT / "R10_11FA_ANALYTIC_COMPENSATION_CHECK.csv", "w",
              newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    for x in rows[:6]:
        print(f"{x['law']:>18s} q={x['q']:.5f} rms={x['anchor_rms_deg']:8.3f} "
              f"max={x['anchor_max_deg']:8.3f}")
    print("...")
    for x in rows[-2:]:
        print(f"{x['law']:>18s} q={x['q']:.5f} rms={x['anchor_rms_deg']:8.3f}")
    return rows


if __name__ == "__main__":
    main()
