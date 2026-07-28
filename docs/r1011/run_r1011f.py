"""R10.11F main computation — exact T meshes, edge odds, ratio family.

Run from repo root with PYTHONPATH=. — writes all required outputs to
docs/r1011/evidence/r1011f/.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from pyproj import Geod
from scipy.optimize import linear_sum_assignment

import rgcs_coordinate as rc
from r109 import earth_v2 as e2
from r1011 import flat_hedron as fh

PACK = Path(r"C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/"
            r"internal-docs/plans-v5/"
            r"RGCS_R10_11F_B0_T_Layer2_Mesh_Compensation_Confirmation_Prompt_Pack_2026-07-28")
OUT = Path("docs/r1011/evidence/r1011f")
OUT.mkdir(parents=True, exist_ok=True)
GEOD = Geod(ellps="WGS84")

RATIOS = {"1": 1.0, "10/9": 10 / 9, "9/8": 9 / 8, "81/80": 81 / 80,
          "55/54": 55 / 54}
RATIOS.update({f"({k})^-1": 1 / v for k, v in list(RATIOS.items())
               if k != "1"})
RETRO = {"6/5": 6 / 5, "(6/5)^-1": 5 / 6}      # retrospective only

MIA = (25.7617, -80.1918)
SJU = (18.4655, -66.1057)


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


def mid(a, b):
    m = (a + b) / 2
    return m / np.linalg.norm(m)


# ------------------------------------------------------- mesh builders
def subdivide_global(verts12, faces):
    """Two global spherical-midpoint refinements with dedup."""
    V = [np.asarray(v, float) / np.linalg.norm(v) for v in verts12]
    F = list(faces)
    for _ in range(2):
        cache, NV, NF = {}, list(V), []
        def midi(i, j):
            key = (min(i, j), max(i, j))
            if key not in cache:
                NV.append(mid(NV[i], NV[j]))
                cache[key] = len(NV) - 1
            return cache[key]
        for a, b, c in F:
            ab, bc, ca = midi(a, b), midi(b, c), midi(c, a)
            NF += [(a, ab, ca), (ab, b, bc), (ca, bc, c), (ab, bc, ca)]
        V, F = NV, NF
    return np.array(V), F


ICO_FACES = [(0, 11, 5), (0, 5, 1), (0, 1, 7), (0, 7, 10), (0, 10, 11),
             (1, 5, 9), (5, 11, 4), (11, 10, 2), (10, 7, 6), (7, 1, 8),
             (3, 9, 4), (3, 4, 2), (3, 2, 6), (3, 6, 8), (3, 8, 9),
             (4, 9, 5), (2, 4, 11), (6, 2, 10), (8, 6, 7), (9, 8, 1)]


def rigid_v1_vertices():
    verts = {}
    p = e2.V1_DIR / "MAPPED_ICOSAHEDRON_VERTICES.csv"
    for row in csv.DictReader(open(p)):
        v = np.array([float(row["source_x"]), float(row["source_y"]),
                      float(row["source_z"])])
        verts[int(row["vertex_id"])] = v / np.linalg.norm(v)
    faces = {}
    for row in csv.DictReader(open(e2.V1_DIR / "MAPPED_FACE_CENTROIDS.csv")):
        faces[int(row["mesh_face"])] = tuple(int(x)
                                             for x in row["vertex_ids"].split())
    return [verts[i] for i in range(12)], [faces[f] for f in sorted(faces)]


def build_exact_meshes():
    v1_steps = e2.load_v1_steps()
    rigid12, rigid_faces = rigid_v1_vertices()
    Vr, Fr = subdivide_global(rigid12, rigid_faces)
    T_v1 = e2.apply_steps(Vr, v1_steps)                 # exact V1 T mesh

    m = json.loads((Path("docs/r1011/evidence") /
                    "R10_11_NODE_LIFT_PARAMETERS.json").read_text())
    nodes = np.array(m["nodes_unit_xyz"])
    ff_faces = [tuple(m["faces"][str(k)]) for k in range(20)]
    Vf, Ff = subdivide_global(list(nodes), ff_faces)    # flat-face T mesh
    return (Vr, Fr, T_v1), (Vf, Ff)


def b0_nodes():
    rows = list(csv.DictReader(open(PACK / "03_DATA" / "B0_LAYER2_NODES.csv")))
    lat_k = next(k for k in rows[0] if "lat" in k.lower())
    lon_k = next(k for k in rows[0] if "lon" in k.lower())
    return np.array([unit(float(r[lat_k]), float(r[lon_k])) for r in rows])


# ---------------------------------------------------------- edge odds
def project_fraction_sphere(A, B, P):
    """Great-circle projection of P onto arc A->B: fraction + cross-track."""
    n = np.cross(A, B)
    n = n / np.linalg.norm(n)
    ct = math.degrees(math.asin(np.clip(np.dot(P, n), -1, 1)))
    Pp = P - np.dot(P, n) * n
    Pp = Pp / np.linalg.norm(Pp)
    total = ang(A, B)
    f = ang(A, Pp) / total
    return f, abs(ct), total


def project_fraction_wgs84(A, B, P, samples=4000):
    la1, lo1 = latlon(A)
    la2, lo2 = latlon(B)
    laP, loP = latlon(P)
    pts = GEOD.npts(lo1, la1, lo2, la2, samples)
    _, _, edge_len = GEOD.inv(lo1, la1, lo2, la2)
    best = (None, 1e18, 0.0)
    for i, (lo, la) in enumerate(pts):
        _, _, d = GEOD.inv(lo, la, loP, laP)
        if d < best[1]:
            best = (i, d, (i + 1) / (samples + 1))
    return best[2], best[1] / 1000.0, edge_len / 1000.0


def edge_odds(A, B, P, reverse=False):
    fs, ct_s, _ = project_fraction_sphere(A, B, P)
    fw, ct_w, elen = project_fraction_wgs84(A, B, P)
    out = {}
    for tag, t2, ct in (("sphere", fs, ct_s), ("wgs84", fw, ct_w)):
        q = math.sqrt(max(t2, 1e-15))
        r = q / (1 - q)
        rc = 1 / r if reverse else r
        out[tag] = {"t2": t2, "q": q, "odds_raw": r, "odds_canonical": rc,
                    "cross_track": ct}
    out["ellipsoid_factor"] = (out["wgs84"]["odds_canonical"] /
                               out["sphere"]["odds_canonical"])
    out["edge_length_km"] = elen
    return out


def ratio_compare(odds, include_retro=False):
    fam = dict(RATIOS)
    if include_retro:
        fam.update(RETRO)
    rows = []
    for name, v in fam.items():
        rows.append({"ratio": name, "value": v,
                     "abs_log_odds_error": abs(math.log(odds) - math.log(v)),
                     "relative_error": odds / v - 1,
                     "retrospective": name in RETRO})
    rows.sort(key=lambda r: r["abs_log_odds_error"])
    return rows


def main():
    (Vr, Fr, T_v1), (Vf, Ff) = build_exact_meshes()
    B0 = b0_nodes()

    # correspondence via Hungarian assignment (angular cost)
    def assign(B, T):
        C = np.array([[ang(b, t) for t in T] for b in B])
        ri, ci = linear_sum_assignment(C)
        return ci, C[ri, ci]

    res = {}
    meshes = {"T_EXACT_V1_627": T_v1, "T_EXACT_FLATFACE": Vf}
    corr = {}
    for name, T in meshes.items():
        ci, d = assign(B0, T)
        corr[name] = ci
        res[name] = {"mean_deg": float(d.mean()), "rms_deg":
                     float(np.sqrt((d ** 2).mean())),
                     "min_deg": float(d.min()), "max_deg": float(d.max())}

    # landmark edges: B0 apex node (nearest to Bermuda) and its two
    # neighbours toward Miami / San Juan — matched into each exact mesh
    ber = unit(32.3078, -64.7505)
    apex_b0 = int(np.argmin([ang(v, ber) for v in B0]))
    mia_b0 = int(np.argmin([ang(v, unit(*MIA)) for v in B0]))
    sju_b0 = int(np.argmin([ang(v, unit(*SJU)) for v in B0]))

    edges_out, ratio_rows = [], []
    for name, T in meshes.items():
        ci = corr[name]
        Aa, Bm, Bs = T[ci[apex_b0]], T[ci[mia_b0]], T[ci[sju_b0]]
        for edge_name, (A, B, P, rev) in {
                "apex_to_miami": (Aa, Bm, unit(*MIA), False),
                "apex_to_san_juan": (Aa, Bs, unit(*SJU), True)}.items():
            eo = edge_odds(A, B, P, reverse=rev)
            usable = eo["wgs84"]["cross_track"] < 150.0
            row = {"model": name, "edge": edge_name, "reverse": rev,
                   **{f"sphere_{k}": v for k, v in eo["sphere"].items()},
                   **{f"wgs84_{k}": v for k, v in eo["wgs84"].items()},
                   "ellipsoid_factor": eo["ellipsoid_factor"],
                   "edge_length_km": eo["edge_length_km"],
                   "usable_under_150km_crosstrack": usable}
            edges_out.append(row)
            if usable:
                for rr in ratio_compare(eo["wgs84"]["odds_canonical"],
                                        include_retro=True)[:4]:
                    ratio_rows.append({"model": name, "edge": edge_name,
                                       "odds": eo["wgs84"]["odds_canonical"],
                                       **rr})

    # ---- write outputs ----
    def wcsv(name, rows):
        if not rows:
            (OUT / name).write_text("", encoding="utf-8")
            return
        with open(OUT / name, "w", newline="", encoding="utf-8") as fhh:
            w = csv.DictWriter(fhh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    wcsv("EXACT_EDGE_ODDS.csv", edges_out)
    wcsv("RATIO_FAMILY_COMPARISON.csv", ratio_rows)

    for tag, mesh in (("B0", B0), ("T_V1", T_v1), ("T_FLATFACE", Vf)):
        rows = [{"node": i, "lat": latlon(v)[0], "lon": latlon(v)[1]}
                for i, v in enumerate(mesh)]
        wcsv(f"{tag}_EXACT_LAYER2_NODES.csv", rows)

    with open(OUT / "LAYER2_EDGE_CORRESPONDENCE.csv", "w", newline="",
              encoding="utf-8") as fhh:
        w = csv.writer(fhh)
        w.writerow(["b0_node", "t_v1_node", "t_flatface_node"])
        for i in range(len(B0)):
            w.writerow([i, int(corr["T_EXACT_V1_627"][i]),
                        int(corr["T_EXACT_FLATFACE"][i])])

    print(json.dumps({"correspondence_stats": res,
                      "edges": [{k: r[k] for k in
                                 ("model", "edge", "wgs84_odds_canonical",
                                  "wgs84_cross_track", "ellipsoid_factor",
                                  "usable_under_150km_crosstrack")}
                                for r in edges_out]}, indent=1))
    return res, edges_out, ratio_rows


if __name__ == "__main__":
    main()
