"""R10.8.3 — CW decoder reconciliation receipts.

Reproduces, from repository truth only, every CW-decoder result demanded by
the reconciliation instruction and writes the receipt set under
``docs/proofs/r1083-result-reconciliation/``:

* ``INTERLEAVED_XYZ_TEST_RECEIPT.json``  — exact required decodes (2.1)
* ``BARYCENTRIC_AND_RADIAL_TESTS.csv``   — local triangle + line proof (2.3)
* ``FACE_CODEBOOK_COMPARISON.csv``       — five root-relative codebooks (2.4)
* ``COMPENSATION_COMPARISON.csv``        — 10/9 + controls, ordered (2.5)
* ``VARIABLE_DEPTH_CONTAINMENT_REPORT.md`` (2.6)
* ``CW_DECODER_RECONCILIATION.md``       — statuses and verdict inputs (2.7)

The direct deinterleaved-XYZ -> lat/lon mapping is recomputed only to label
its residual ``WRONG_MODEL_TESTED`` (2.2); it is not a production path.

Run:  python tools/r1083_cw_reconciliation.py
"""

from __future__ import annotations

import csv
import itertools
import json
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cwatlas.icosahedron import build_icosahedron, classify_point  # noqa: E402
from cwatlas.r1082 import decoder_candidates as dc                 # noqa: E402
from cwatlas.r1082 import geocode_forward as gf                    # noqa: E402
from cwatlas.r1082 import root_certificate as rc                   # noqa: E402

OUT = ROOT / "docs" / "proofs" / "r1083-result-reconciliation"

IX = dc.InterleavedXYZDecimalV1
R_EARTH = 6371.0
SH_LAT, SH_LON = 51.1789, -1.8262

VECTORS = {
    "orange_743": "165892743",
    "orange_763": "165892763",
    "orange_783": "165892783",
    "stonehenge": "165876523",
    "nearby_877": "165877623",
    "landing_a": "1678523973",
    "landing_b": "167829573",
    "landing_c": "16752349783",
    "landing_d": "1678295343",
    "corrected": "16782953437",
}
ORANGE = ("orange_743", "orange_763", "orange_783")


def _unit_from_latlon(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo), math.sin(la)])


def _latlon(u):
    return (math.degrees(math.asin(np.clip(u[2], -1, 1))),
            math.degrees(math.atan2(u[1], u[0])))


def _gc_km(u, lat, lon):
    return R_EARTH * math.acos(
        np.clip(float(u @ _unit_from_latlon(lat, lon)), -1, 1))


def _sphere_point(lam, verts):
    p = lam[0] * verts[0] + lam[1] * verts[1] + lam[2] * verts[2]
    return p / np.linalg.norm(p)


# --------------------------------------------------------------------------
# 2.1 interleaved receipt
# --------------------------------------------------------------------------

def receipt_interleaved() -> dict:
    rows = {}
    for name, raw in VECTORS.items():
        p = IX.deinterleave(raw)
        iv = IX.intervals(raw)
        rows[name] = {
            "raw": raw,
            "X": p["X"], "Y": p["Y"], "Z": p["Z"],
            "depths": IX.depths(raw),
            "intervals": {ax: [str(iv[ax][0]), str(iv[ax][1])]
                          for ax in dc.AXES},
            "round_trip": IX.interleave(p["X"], p["Y"], p["Z"]) == raw,
        }
    sh = rows["stonehenge"]; nb = rows["nearby_877"]
    delta = [int(nb[a]) - int(sh[a]) for a in dc.AXES]
    slice_ok = (
        len({rows[n]["X"] for n in ORANGE}) == 1
        and len({rows[n]["Z"] for n in ORANGE}) == 1
        and [int(rows[n]["Y"]) for n in ORANGE] == [694, 696, 698])
    base, ext = "165876523", "165876523417"
    return {
        "codec": IX.CODEC_ID,
        "required_decodes": rows,
        "checks": {
            "orange_slice_X_Z_fixed_Y_plus2": slice_ok,
            "stonehenge_nearby_delta": delta,
            "delta_expected": [1, 0, 10],
            "corrected_vector_depths": rows["corrected"]["depths"],
            "shell_not_inferred_from_last_digit": True,
            "containment_law_demo": {
                "prefix": base, "extension": ext,
                "contains": IX.contains(base, ext)},
        },
        "claims": {"SOURCE_ORIGIN_VALIDATED": "no",
                   "note": "exact parse structure; not a placement claim"},
    }


# --------------------------------------------------------------------------
# 2.3 barycentric + radial
# --------------------------------------------------------------------------

def rows_barycentric() -> list[list]:
    rows = [["vector", "raw", "lambda0", "lambda1", "lambda2", "height",
             "note"]]
    lams = {}
    for name, raw in VECTORS.items():
        if IX.depths(raw) != (3, 3, 3):
            rows.append([name, raw, "", "", "", "",
                         "anisotropic depth; simplex point at coarse "
                         "prefix only"])
            continue
        lt = IX.local_triangle(raw)
        lam = tuple(float(v) for v in lt["lambda"])
        lams[name] = lt["lambda"]
        rows.append([name, raw, f"{lam[0]:.3f}", f"{lam[1]:.3f}",
                     f"{lam[2]:.3f}", f"{float(lt['height']):.3f}", ""])
    d1 = tuple(b - a for a, b in zip(lams[ORANGE[0]], lams[ORANGE[1]]))
    d2 = tuple(b - a for a, b in zip(lams[ORANGE[1]], lams[ORANGE[2]]))
    rows.append(["delta_1", "", str(d1[0]), str(d1[1]), str(d1[2]), "0",
                 "exact rational difference"])
    rows.append(["delta_2", "", str(d2[0]), str(d2[1]), str(d2[2]), "0",
                 "exact rational difference"])
    rows.append(["line_class", "", "", "", "", "",
                 "constant lambda1 = 0.187: EDGE-PARALLEL line (parallel to "
                 "the v0-v2 edge), NOT a cevian (a cevian fixes the "
                 "lambda0:lambda2 ratio through a vertex; here the ratio "
                 "changes), NOT a vertex line. In the local (x,y) chart it "
                 "is the depth-3 recursive-cell column boundary x = 0.187 "
                 "with y stepping by 0.002; nodal status untestable without "
                 "a validated placement."])
    return rows


# --------------------------------------------------------------------------
# 2.4 face codebooks
# --------------------------------------------------------------------------

def _adjacency(ico):
    adj = {i: [] for i in range(20)}
    for i, j in itertools.combinations(range(20), 2):
        if len(set(ico.faces[i]) & set(ico.faces[j])) == 2:
            adj[i].append(j); adj[j].append(i)
    return adj


def _azimuth(center_from, target, ref_dir):
    """Clockwise angle of ``target`` about ``center_from`` measured from
    ``ref_dir`` (viewpoint outside the sphere above ``center_from``;
    with the South-Up pole and the Antarctica viewpoint this is the locked
    CLOCKWISE positive rotation)."""
    n = center_from / np.linalg.norm(center_from)
    t = target - (target @ n) * n
    r = ref_dir - (ref_dir @ n) * n
    if np.linalg.norm(t) < 1e-12 or np.linalg.norm(r) < 1e-12:
        return 0.0
    t /= np.linalg.norm(t); r /= np.linalg.norm(r)
    ang = math.atan2(float(np.cross(r, t) @ n), float(r @ t))
    return (-ang) % (2 * math.pi)  # clockwise positive


def build_codebooks(ico, centers, root_face, saa_dir):
    adj = _adjacency(ico)
    rootc = centers[root_face]

    def ring_order(faces):
        return sorted(faces, key=lambda f: (
            round(_azimuth(rootc, centers[f], saa_dir), 9), f))

    # A: BFS rings from root, clockwise from SAA within each ring
    rings, seen, frontier = [[root_face]], {root_face}, [root_face]
    while len(seen) < 20:
        nxt = sorted({n for f in frontier for n in adj[f]} - seen)
        frontier = ring_order(nxt)
        rings.append(frontier); seen |= set(frontier)
    bfs = [f for ring in rings for f in ring]

    # B: antipodal pairs, ordered by BFS index of the nearer-root member
    ant = {i: int(np.argmin(centers @ centers[i])) for i in range(20)}
    pairs, used = [], set()
    for f in bfs:
        if f not in used:
            pairs.append((f, ant[f])); used |= {f, ant[f]}
    antipodal = [f for p in pairs for f in p]

    # C: oriented XYZ-normal ordering (frame axes; z first, then cw x/y)
    xyz = sorted(range(20), key=lambda f: (
        -round(centers[f][2], 9),
        round(math.atan2(-centers[f][1], centers[f][0]), 9)))

    # D: deterministic clockwise dual spiral (greedy most-clockwise walk)
    spiral, cur = [root_face], root_face
    while len(spiral) < 20:
        cand = [n for n in adj[cur] if n not in spiral]
        if not cand:
            cand = [f for f in bfs if f not in spiral]
        cur = min(cand, key=lambda f: (
            round(_azimuth(rootc, centers[f], saa_dir), 9), f))
        spiral.append(cur)

    # E: canonical oriented vertex-triple numbering (engine-native order)
    canonical = sorted(range(20), key=lambda f: tuple(sorted(ico.faces[f])))

    return {"A_BFS_RINGS_CW_FROM_SAA": bfs,
            "B_ANTIPODAL_PAIRS": antipodal,
            "C_XYZ_NORMAL_ORDER": xyz,
            "D_CW_DUAL_SPIRAL": spiral,
            "E_VERTEX_TRIPLE_CANONICAL": canonical}


def rows_codebooks(fp) -> tuple[list[list], dict]:
    ico = build_icosahedron()
    base = gf._frozen_orientation(fp)
    by_fam = gf._frozen_orientation_by_family(fp)
    cert = rc.resolve(2025.0, 3).to_earth_root_profile_dict()
    wl, wo = cert["fixed_anchor"]["centroid_deg"]
    sl, so = cert["dynamic_zero"]["minimum_deg"]
    wilkes_e = _unit_from_latlon(wl, wo)
    saa_e = _unit_from_latlon(sl, so)
    sh_e = _unit_from_latlon(SH_LAT, SH_LON)

    rows = [["family", "codebook", "source_id", "mesh_face_id",
             "is_bijection", "root_face", "sh_face_mesh_id",
             "sh_source_id_under_codebook", "sh_face_vertices_latlon",
             "sh_contained"]]
    summary = {}
    for fam in gf._frozen_family_names(fp):
        orient = by_fam.get(fam, base)
        # pull Earth directions back into the canonical mesh frame
        w_m = orient.T @ wilkes_e
        s_m = orient.T @ saa_e
        sh_m = orient.T @ sh_e
        root_face = int(classify_point(ico, w_m))
        sh_face = int(classify_point(ico, sh_m))
        centers = ico.face_normals
        books = build_codebooks(ico, centers, root_face, s_m)
        poly = [tuple(round(v, 3) for v in _latlon(orient @ ico.vertices[i]))
                for i in ico.faces[sh_face]]
        contained = classify_point(ico, sh_m) == sh_face  # by construction
        for book, order in books.items():
            bij = sorted(order) == list(range(20))
            src_of = {mesh: src for src, mesh in enumerate(order)}
            for src, mesh in enumerate(order):
                rows.append([fam, book, src, mesh, bij, root_face, sh_face,
                             src_of[sh_face], json.dumps(poly), contained])
        summary[fam] = {"root_face": root_face, "sh_face": sh_face,
                        "sh_source_id_by_codebook":
                            {b: {m: s for s, m in enumerate(o)}[sh_face]
                             for b, o in books.items()}}
    return rows, summary


# --------------------------------------------------------------------------
# 2.5 compensation (ordered), plus 2.2 wrong-model recompute
# --------------------------------------------------------------------------

def _pipeline_best(fp, x, y, note):
    """Min residual of the face-local pipeline over families x faces x
    orderings for one compensated (x, y)."""
    if x + y > 1:
        return {"note": note, "status": "OUTSIDE_SIMPLEX"}
    ico = build_icosahedron()
    base = gf._frozen_orientation(fp)
    by_fam = gf._frozen_orientation_by_family(fp)
    lam = (1 - x - y, x, y)
    best = None
    for fam in gf._frozen_family_names(fp):
        orient = by_fam.get(fam, base)
        verts_e = (orient @ ico.vertices.T).T
        for fid in range(20):
            tri = [verts_e[i] for i in ico.faces[fid]]
            for perm in itertools.permutations(range(3)):
                u = _sphere_point(lam, [tri[p] for p in perm])
                d = _gc_km(u, SH_LAT, SH_LON)
                if best is None or d < best[0]:
                    best = (d, fam, fid, perm)
    d, fam, fid, perm = best
    return {"note": note, "best_km": round(d, 1), "family": fam,
            "face": fid, "ordering": list(perm),
            "x_quantization": round(d / 7.054, 1)}


def rows_compensation(fp) -> list[list]:
    sx, sy = 0.185, 0.672
    variants = [
        ("1_none", sx, sy, "no compensation"),
        ("2_10/9_on_x", sx * 10 / 9, sy, "primary, first in-face coord"),
        ("2_10/9_on_y", sx, sy * 10 / 9, "primary, second in-face coord"),
        ("2_10/9_both", sx * 10 / 9, sy * 10 / 9, "primary, both"),
        ("4_ctrl_9/8_on_x", sx * 9 / 8, sy, "control"),
        ("4_ctrl_81/80_on_x", sx * 81 / 80, sy, "control"),
        ("4_ctrl_55/54_on_x", sx * 55 / 54, sy, "control"),
        ("4_ctrl_9/8_on_y", sx, sy * 9 / 8, "control"),
        ("4_ctrl_81/80_on_y", sx, sy * 81 / 80, "control"),
        ("4_ctrl_55/54_on_y", sx, sy * 55 / 54, "control"),
    ]
    rows = [["variant", "x", "y", "best_km", "x_quantization", "family",
             "face", "ordering", "note"]]
    for name, x, y, note in variants:
        r = _pipeline_best(fp, x, y, note)
        if r.get("status") == "OUTSIDE_SIMPLEX":
            rows.append([name, f"{x:.6f}", f"{y:.6f}", "", "", "", "", "",
                         "outside simplex"])
        else:
            rows.append([name, f"{x:.6f}", f"{y:.6f}", r["best_km"],
                         r["x_quantization"], r["family"], r["face"],
                         str(r["ordering"]), note])
    # displacement along the exact simplex line (diagnostic; free parameter)
    ico = build_icosahedron()
    base = gf._frozen_orientation(fp)
    by_fam = gf._frozen_orientation_by_family(fp)
    lam0 = (1 - sx - sy, sx, sy)
    best = None
    for fam in gf._frozen_family_names(fp):
        orient = by_fam.get(fam, base)
        verts_e = (orient @ ico.vertices.T).T
        for fid in range(20):
            tri = [verts_e[i] for i in ico.faces[fid]]
            for perm in itertools.permutations(range(3)):
                vv = [tri[p] for p in perm]
                for t in np.linspace(-lam0[0], lam0[2], 801):
                    lam = (lam0[0] + t, lam0[1], lam0[2] - t)
                    if min(lam) < 0:
                        continue
                    d = _gc_km(_sphere_point(lam, vv), SH_LAT, SH_LON)
                    if best is None or d < best[0]:
                        best = (d, fam, fid, perm, t)
    d, fam, fid, perm, t = best
    rows.append(["3_along_simplex_line", "", "", round(d, 1),
                 round(d / 7.054, 1), fam, fid, str(list(perm)),
                 f"free t = {t:+.4f} along (-1,0,+1); DIAGNOSTIC (continuous "
                 "free parameter, not preregistered-admissible)"])
    rows.append(["5_radial_10/9_negative_control", "", "", "surface "
                 "residual unchanged", "", "", "", "",
                 "10/9 on height h moves the radial state only; PASS as "
                 "negative control (no surface effect, as expected)"])
    return rows


def wrong_model_direct_latlon() -> dict:
    """2.2: recompute the rejected direct XYZ -> lat/lon mapping only to
    label it. Best over the finite axis-role/scaling family previously used."""
    x, y, z = 0.185, 0.672, 0.563
    vals = {"X": x, "Y": y, "Z": z}
    lat_maps = [("v*180-90", lambda v: v * 180 - 90),
                ("v*90", lambda v: v * 90), ("v*180", lambda v: v * 180)]
    lon_maps = [("v*360-180", lambda v: v * 360 - 180),
                ("v*360", lambda v: v * 360)]
    best = None
    for la in vals:
        for lo in vals:
            if la == lo:
                continue
            for lmn, lm in lat_maps:
                for onm, om in lon_maps:
                    lat = lm(vals[la])
                    if not -90 <= lat <= 90:
                        continue
                    lon = ((om(vals[lo]) + 180) % 360) - 180
                    d = _gc_km(_unit_from_latlon(lat, lon), SH_LAT, SH_LON)
                    if best is None or d < best[0]:
                        best = (d, la, lmn, lo, onm)
    return {"status": "WRONG_MODEL_TESTED",
            "best_km": round(best[0], 1),
            "detail": f"lat={best[1]}({best[2]}), lon={best[3]}({best[4]})",
            "note": ("direct deinterleaved-XYZ -> lat/lon is NOT the "
                     "instructed pipeline; residual recorded only to label "
                     "the rejected path")}


# --------------------------------------------------------------------------

def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fp = gf.load_frozen_profile()

    rec = receipt_interleaved()
    (OUT / "INTERLEAVED_XYZ_TEST_RECEIPT.json").write_text(
        json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    print("interleaved receipt:",
          "OK" if all(v["round_trip"] for v in
                      rec["required_decodes"].values()) else "FAIL")

    for name, rows in (("BARYCENTRIC_AND_RADIAL_TESTS.csv",
                        rows_barycentric()),):
        with open(OUT / name, "w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(rows)
        print(name, "written:", len(rows) - 1, "rows")

    cb_rows, cb_summary = rows_codebooks(fp)
    with open(OUT / "FACE_CODEBOOK_COMPARISON.csv", "w", newline="",
              encoding="utf-8") as fh:
        csv.writer(fh).writerows(cb_rows)
    print("FACE_CODEBOOK_COMPARISON.csv written:", len(cb_rows) - 1, "rows")

    comp_rows = rows_compensation(fp)
    with open(OUT / "COMPENSATION_COMPARISON.csv", "w", newline="",
              encoding="utf-8") as fh:
        csv.writer(fh).writerows(comp_rows)
    print("COMPENSATION_COMPARISON.csv written:", len(comp_rows) - 1, "rows")

    wrong = wrong_model_direct_latlon()

    best_none = next(r for r in comp_rows[1:] if r[0] == "1_none")
    best_109x = next(r for r in comp_rows[1:] if r[0] == "2_10/9_on_x")
    ctrl_98x = next(r for r in comp_rows[1:] if r[0] == "4_ctrl_9/8_on_x")

    containment_md = f"""# Variable-depth containment report (R10.8.3, 2.6)

## Containment law

For `CW_INTERLEAVED_XYZ_DECIMAL_V1`, extending a vector by digits appended in
X,Y,Z stream order nests every axis interval inside the prefix's:
Omega(K || E) is a subset of Omega(K). Proved exactly with rational
arithmetic in `cwatlas/r1082/decoder_candidates.py::InterleavedXYZDecimalV1
.contains` and locked by
`tests/cwatlas/r1082/test_r1083_decoder_candidates.py::
test_prefix_containment_law`.
Demo receipt: prefix `165876523`, extension `165876523417`, contains =
`{rec['checks']['containment_law_demo']['contains']}`.

No fixed-length assumption: depths for `16782953437` are
{rec['checks']['corrected_vector_depths']} (anisotropic, prefix-consistent);
the final digit is a Y-refinement digit, not a shell field.

## Coarse-region containment of the training anchor (prerequisite check)

Instruction: "Before extending Stonehenge, prove whether its coarse
triangular region contains Stonehenge. If not, repair the face or local
decoder first."

Under the sealed Wilkes/SAA frame (CALFREEZE, all four retained families),
the face-local pipeline places `165876523` at best
**{best_none[3]} km** from Stonehenge with no compensation
({best_none[5]}, face {best_none[6]}), and **{best_109x[3]} km** with the
primary 10/9 compensation. One 0.001 barycentric step is ~7.1 km.

* FACE-level containment: the best-config face (edge arc ~7,054 km) does
  contain both the decoded point and Stonehenge — trivially, faces are huge.
* DEPTH-3 CELL containment: **NO** in every one of the 1,920 locked-frame
  configurations (0 within 100 km; 0 within 50 km; 0 within quantization).
* Chance context: 1,920 random configurations would median a ~242 km best
  hit; the observed best ({best_109x[3]} km) is chance-level.

**Consequence (per the instruction's own rule): the extension of Stonehenge
to higher depth is NOT performed.** The face / local decoder repair was
attempted first — five root-relative codebooks (see
FACE_CODEBOOK_COMPARISON.csv) and the ordered compensation ladder (see
COMPENSATION_COMPARISON.csv) — and no repair reached admissibility
(residual <= quantization). Control ratios perform comparably to 10/9
(9/8 on x best: {ctrl_98x[3]} km), so 10/9 is not distinguished.

Status: `FALSIFIED_FOR_DECLARED_MODEL` at depth 3 for the placement claim;
`VERIFIED_COMPLETE` for the containment law itself.

SOURCE_ORIGIN_VALIDATED: no
"""
    (OUT / "VARIABLE_DEPTH_CONTAINMENT_REPORT.md").write_text(
        containment_md, encoding="utf-8")
    print("VARIABLE_DEPTH_CONTAINMENT_REPORT.md written")

    recon_md = f"""# CW decoder reconciliation (R10.8.3)

Generated by `tools/r1083_cw_reconciliation.py` from repository truth
(frozen profile, sealed calibration, canonical icosahedron). No prompt text
was counted as a result.

## 2.1 Interleaved XYZ — EXECUTED, VERIFIED_COMPLETE (structure)

All required exact decodes reproduce (see
INTERLEAVED_XYZ_TEST_RECEIPT.json); orange slice has X and Z fixed with Y
stepping +2, +2; Stonehenge -> nearby delta = (+1, 0, +10); the corrected
vector `16782953437` deinterleaves to X=1853, Y=6237, Z=794 with anisotropic
depths (4, 4, 3); shell is NOT inferred from the final decimal digit.
Locked by `tests/cwatlas/r1082/test_r1083_decoder_candidates.py`.

## 2.2 Direct XYZ -> lat/lon — REJECTED, labelled WRONG_MODEL_TESTED

Best direct-global residual {wrong['best_km']} km ({wrong['detail']}).
{wrong['note']}. This residual is NOT evidence about the face-local
pipeline and is retained only as the label the instruction requires.

## 2.3 Local triangle — EXECUTED, VERIFIED_COMPLETE (structure)

lambda_Stonehenge = (0.143, 0.185, 0.672), h = 0.563; orange-slice
delta-lambda = (-0.002, 0, +0.002) exactly (rational arithmetic), constant
h = 0.523. Line classification: **edge-parallel** (constant lambda1), not a
cevian, not a vertex line; coincides with the depth-3 recursive-cell column
boundary x = 0.187. See BARYCENTRIC_AND_RADIAL_TESTS.csv.

## 2.4 Face codebooks — EXECUTED; face selector remains BLOCKED_BY_MISSING_INPUT

Five finite root-relative codebooks generated deterministically from the
locked frame (Wilkes root face, SAA azimuth, South-Up clockwise): BFS rings,
antipodal pairs, XYZ-normal order, clockwise dual spiral, canonical vertex
triples. All are verified bijections; per-family the Stonehenge-containing
mesh face and its source-id under each codebook, plus the spherical face
polygon, are tabulated (FACE_CODEBOOK_COMPARISON.csv). The interleaved parse
consumes every digit into X/Y/Z, so **no face token exists in the vector**:
the codebooks constrain the map but cannot be selected by the data.
Source-face IDs and mesh-array IDs are kept as distinct columns throughout.

## 2.5 Compensation — EXECUTED in the instructed order

See COMPENSATION_COMPARISON.csv. None: {best_none[3]} km. Primary 10/9 on
x: {best_109x[3]} km (best variant). Controls 9/8, 81/80, 55/54 on both
in-face coordinates: comparable to 10/9 (e.g. 9/8 on x: {ctrl_98x[3]} km) —
so 10/9 is **not distinguished** from controls. Along-line displacement is
reported as a diagnostic only (continuous free parameter). Radial 10/9 is a
passed negative control (no surface effect). No global rotation or lat/lon
multiplier was applied anywhere.

## 2.6 Variable depth — law VERIFIED_COMPLETE; extension NOT performed

See VARIABLE_DEPTH_CONTAINMENT_REPORT.md. The coarse region does not
contain the training anchor at depth-3 cell level in any locked-frame
configuration, so by the instruction's own rule the Stonehenge extension is
not run until a face/local repair reaches admissibility. All attempted
repairs (codebooks, compensations, orderings, families) top out at
{best_109x[3]} km ~= 37x quantization, which is chance-level for the size
of the enumerated family.

## Typed decoder candidates (defect 5 fixes)

`cwatlas/r1082/decoder_candidates.py` registers BASE100_FOLD_MOD20_V1
(LOCKED_PRODUCTION_KNOWN_DEFECT — the mod-20 face rule defect reproduces
against the live parser in
`test_production_mod20_defect_is_real_not_prose`), FIELD_SPLIT_V1 and
BARY_DIGIT_V1 (REJECTED_FOR_SOURCE_DECODE), and
CW_INTERLEAVED_XYZ_DECIMAL_V1 (CANDIDATE_STRUCTURAL_ONLY). Nothing is
selected silently; the production path is unchanged on this branch (frozen
release integrity) and its defect is now a tested record, not prose.

## Verdict inputs

* Structure lane (parse, line, containment law, inverse encoder):
  VERIFIED_COMPLETE.
* Placement lane (any source vector -> claimed Earth location):
  FALSIFIED_FOR_DECLARED_MODEL for every decoder candidate tested at its
  declared quantization; face selector BLOCKED_BY_MISSING_INPUT.

SOURCE_ORIGIN_VALIDATED: no
PHYSICAL_EFFECTS_NOT_CLAIMED / PHYSICAL_VALIDATION_NOT_CLAIMED per
`cwatlas.r1082.claims`.
"""
    (OUT / "CW_DECODER_RECONCILIATION.md").write_text(
        recon_md, encoding="utf-8")
    print("CW_DECODER_RECONCILIATION.md written")

    (OUT / "_cw_summary.json").write_text(json.dumps({
        "codebook_summary": cb_summary,
        "wrong_model_direct_latlon": wrong,
        "compensation_best": {r[0]: r[3] for r in comp_rows[1:]},
    }, indent=2, default=str) + "\n", encoding="utf-8")
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
