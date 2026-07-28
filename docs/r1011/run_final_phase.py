"""R10.11 controls + UK re-decode + anchors + holdout freeze (one-shot)."""
import csv, hashlib, json, math, pathlib
import numpy as np
from scipy.optimize import least_squares
import rgcs_coordinate as rc
from r1011 import flat_hedron as fh
from r109 import earth_v2 as e2, sealed_holdout as sh
from r109.face_node import source_face

EV = pathlib.Path("docs/r1011/evidence")
m = json.load(open(EV / "R10_11_NODE_LIFT_PARAMETERS.json", encoding="utf-8"))
NODES = np.array(m["nodes_unit_xyz"])
FACES = {int(k): tuple(v) for k, v in m["faces"].items()}


def path(raw):
    return tuple(rc.decode_coordinate(raw).to_dict()["q22_path"])


def newmap(raw, mf):
    return fh.latlon(fh.address_point(NODES, FACES, mf, path(raw)))


def ang(a, b):
    return math.degrees(math.acos(float(np.clip(np.dot(fh.unit(*a), fh.unit(*b)), -1, 1))))


ANCH = [("STONEHENGE", 165876523, 12, (51.17881944444445, -1.8262805555555555)),
        ("ERIE", 167849523, 19, (42.114507, -80.076213)),
        ("TORONTO", 168930443, 19, (43.6532, -79.3832))]
base, faces0 = fh.load_base()


def rigid_pos(raw, mf, t=0.5):
    vids = faces0[mf]
    A, B, C = (base[vids[fh.CORNER_PERM[0]]], base[vids[fh.CORNER_PERM[1]]],
               base[vids[fh.CORNER_PERM[2]]])

    def sl(a, b):
        om = math.acos(float(np.clip(np.dot(a, b), -1, 1)))
        if om < 1e-12:
            return a
        return (math.sin((1 - t) * om) * a + math.sin(t * om) * b) / math.sin(om)

    for p in path(raw):
        mAB, mBC, mCA = sl(A, B), sl(B, C), sl(C, A)
        mAB, mBC, mCA = [x / np.linalg.norm(x) for x in (mAB, mBC, mCA)]
        A, B, C = [(A, mAB, mCA), (mAB, B, mBC), (mCA, mBC, C),
                   (mAB, mBC, mCA)][fh.CHILD_MAP[p]]
    c = (A + B + C) / 3
    return fh.latlon(c)


def resid_control(fn):
    return [ang(fn(raw, mf), tgt) for _, raw, mf, tgt in ANCH]


r_mid = resid_control(lambda raw, mf: rigid_pos(raw, mf, 0.5))
sol_t = least_squares(lambda tv: [ang(rigid_pos(raw, mf, float(tv[0])), tgt)
                                  for _, raw, mf, tgt in ANCH],
                      [0.5], bounds=([0.05], [0.95]))
t_best = float(sol_t.x[0])
r_slerp = [ang(rigid_pos(raw, mf, t_best), tgt) for _, raw, mf, tgt in ANCH]


def to_c(ll):
    v = fh.unit(*ll)
    return complex(v[0], v[1]) / (1 - v[2] + 1e-15)


def from_c(z):
    d = 1 + abs(z) ** 2
    return fh.latlon(np.array([2 * z.real / d, 2 * z.imag / d,
                               (abs(z) ** 2 - 1) / d]))


def mob_cost(prm):
    a = complex(prm[0], prm[1]); b = complex(prm[2], prm[3]); c = complex(prm[4], prm[5])
    out = []
    for _, raw, mf, tgt in ANCH:
        w = (a * to_c(rigid_pos(raw, mf)) + b) / (c * to_c(rigid_pos(raw, mf)) + 1)
        out.append(ang(from_c(w), tgt))
    for fixed in ((-70.0, 120.0), (-26.22, -60.03)):
        w = (a * to_c(fixed) + b) / (c * to_c(fixed) + 1)
        out.append(ang(from_c(w), fixed))
    return out


sol_m = least_squares(mob_cost, [1, 0, 0, 0, 0, 0], max_nfev=20000)
r_mob = mob_cost(sol_m.x)[:3]


def snyder_pos(raw, mf):
    vids = faces0[mf]
    A, B, C = (base[vids[fh.CORNER_PERM[0]]], base[vids[fh.CORNER_PERM[1]]],
               base[vids[fh.CORNER_PERM[2]]])
    for p in path(raw):
        mAB, mBC, mCA = (A + B) / 2, (B + C) / 2, (C + A) / 2
        A, B, C = [(A, mAB, mCA), (mAB, B, mBC), (mCA, mBC, C),
                   (mAB, mBC, mCA)][fh.CHILD_MAP[p]]
    c = (A + B + C) / 3
    return fh.latlon(c)


r_sny = resid_control(snyder_pos)
new_res = [ang(newmap(raw, mf), tgt) for _, raw, mf, tgt in ANCH]
rows = [
    ["V1_GAUSSIAN_RBF", "627 warp steps", 0.0, 0.0, 0, "smooth calibrated; historical profile"],
    ["V2_DIRECT_MONTREAL_RBF", "868 steps", 0.0, 0.0, 361, "FOLDED - rejected diagnostic"],
    ["REGULAR_SPHERICAL_MIDPOINT", "0", max(r_mid), sum(r_mid) / 3, 0, "rigid control"],
    ["PARAM_SLERP_t=" + f"{t_best:.4f}", "1", max(r_slerp), sum(r_slerp) / 3, 0,
     "traversal-curved control (not source-matched)"],
    ["MOBIUS_CONTROL", "6", max(r_mob), sum(r_mob) / 3, 0,
     "global conformal control (not source-matched)"],
    ["SNYDER_STYLE_EQUAL_AREA_APPROX", "0", max(r_sny), sum(r_sny) / 3, 0,
     "planar equal-area proxy, NOT full ISEA (labelled approximation)"],
    ["FLAT_FACE_NODE_CURVATURE_NEW", "24 (12 node dirs)", max(new_res),
     sum(new_res) / 3, 0,
     "SOURCE-MATCHED; convex; 0 folds depth-6; exact inverse lookup"],
]
with open(EV / "R10_11_MAP_COMPARISON.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["model", "params", "max_anchor_residual_deg",
                "mean_anchor_residual_deg", "orientation_reversals_L6", "notes"])
    w.writerows(rows)
for r in rows:
    print(r[0], "max_res:", round(float(r[2]), 5), "folds:", r[4])

with open(EV / "R10_11_ANCHOR_RESULTS.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["name", "raw", "mesh_face", "target_lat", "target_lon",
                "model_lat", "model_lon", "residual_deg", "in_fit"])
    for name, raw, mf, tgt in ANCH:
        mres = newmap(raw, mf)
        w.writerow([name, raw, mf, *tgt, *[round(x, 6) for x in mres],
                    round(ang(mres, tgt), 6), True])
    mm = newmap(165879243, 12)
    w.writerow(["MONTREAL_DIRECT_EXCLUDED", 165879243, 12, 45.508822, -73.554077,
                *[round(x, 6) for x in mm],
                round(ang(mm, (45.508822, -73.554077)), 4), False])
    cy = newmap(165892733, 12)
    w.writerow(["CYYT_COMPACT_OLD_PATHS", 165892733, 12, 47.6186, -52.7519,
                *[round(x, 6) for x in cy],
                round(ang(cy, (47.6186, -52.7519)), 4), False])
print("montreal excluded resid:", round(ang(newmap(165879243, 12), (45.508822, -73.554077)), 3))
print("cyyt-old-path resid vs StJohns:", round(ang(newmap(165892733, 12), (47.6186, -52.7519)), 3))

census = list(csv.DictReader(open(EV / "RGCS_COMPLETE_VECTOR_CENSUS_2026-07-27.csv", encoding="utf-8")))
uk = [r for r in census if r["role"] == "SOURCE_REPORTED_ADDITIONAL_LANDING_SITE_SET"]
uk_rows = []
for r in uk:
    raw = int(r["raw_vector"])
    nm = newmap(raw, 12)
    uk_rows.append([raw, r["model_output_or_candidate"][:60],
                    *[round(x, 5) for x in nm]])
with open(EV / "R10_11_UK_CLUSTER_NEWMAP.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["raw", "v1_named_output_model_derived", "newmap_lat", "newmap_lon"])
    w.writerows(uk_rows)
print("UK cluster size:", len(uk_rows), "first:", uk_rows[0])

state_files = sorted([*pathlib.Path("r1011").glob("*.py"),
                      *pathlib.Path("r1010").glob("*.py"),
                      *pathlib.Path("r109").glob("*.py")])
h = hashlib.sha256()
for fpath in state_files:
    h.update(fpath.name.encode())
    h.update(fpath.read_bytes())
h.update(json.dumps(m["nodes_unit_xyz"]).encode())
STATE = h.hexdigest()
mesh_by_source = {int(r["source_face_id"]): int(r["physical_mesh_face"])
                  for r in csv.DictReader(open(str(e2.V1_DIR / "FACE_CODEBOOK_OPTION_A_OFFSET14.csv")))}
v1steps = e2.load_v1_steps()
preds = []
for rec in sh.RECORDS:
    raw = rec.raw
    entry = {"raw": raw, "raw_sha256": rec.sha256(), "octal": format(raw, "o")}
    if raw < (1 << 30):
        t = rc.decode_coordinate(raw).to_dict()
        mf = mesh_by_source[source_face(t["face_id"])]
        A, B, C = fh.face_corners(NODES, FACES, mf, t["q22_path"])
        rep_pt = (A + B + C) / 3
        rep_pt /= np.linalg.norm(rep_pt)
        la, lo = fh.latlon(rep_pt)
        poly = [list(fh.latlon(x)) for x in (A, B, C)]
        unc = max(ang((la, lo), tuple(fh.latlon(x))) for x in (A, B, C))
        v1p = e2.latlon(e2.apply_steps([e2.prewarp_unit(raw, mf)], v1steps)[0])
        entry.update({
            "family": "T10", "f5": t["face_id"], "s3": t["extracted_shell"],
            "mesh_face": mf,
            "newmap": {"operator": m["profile_id"], "lat": la, "lon": lo,
                       "terminal_polygon": poly,
                       "uncertainty_radius_deg": unc},
            "v1_continuity": {"operator": "EARTH_ALIGNMENT_V1_LEGACY_CALIBRATED",
                              "lat": v1p[0], "lon": v1p[1]},
            "prediction_class": "PRE_REVEAL_GEOMETRIC_CANDIDATE - no label, "
                                "no gazetteer, no location claim"})
    else:
        entry.update({"family": "T11",
                      "prediction_class": "BLOCKED - unified codec unresolved "
                                          "(261 candidates across R10.9/10/11, 0 survivors)"})
    preds.append(entry)
freeze = {
    "schema": "rgcs.r1011.holdout-freeze.v1", "intake_id": sh.INTAKE_ID,
    "intake_sha256": sh.intake_sha256(),
    "implementation_state_sha256": STATE,
    "parent_commit": "f34bb521c32e7fadd699596401377da3353a4a9a",
    "frozen": {
        "codec": "old F5|Q22|S3 profile DEMOTED to exact historical structural "
                 "profile; unified codec UNRESOLVED (0 survivors)",
        "map": m["profile_id"] + " (convex, 0 folds L6, exact anchors)",
        "controls": "see R10_11_MAP_COMPARISON.csv"},
    "gate": "predictions frozen+hashed; operator may ask the source for labels; "
            "verbatim recording; no retuning after reveal"}
(EV / "R10_11_HOLDOUT_FREEZE_RECEIPT.json").write_text(
    json.dumps(freeze, indent=2) + "\n", encoding="utf-8")
doc = {"schema": "rgcs.r1011.pre-reveal-predictions.v1", "freeze": freeze,
       "predictions": preds}
digest = hashlib.sha256(json.dumps(doc, indent=2, default=float).encode()).hexdigest()
doc["receipt_sha256_of_predictions"] = digest
(EV / "R10_11_PREREVEAL_PREDICTIONS.json").write_text(
    json.dumps(doc, indent=2, default=float) + "\n", encoding="utf-8")
print("freeze state:", STATE[:16], "digest:", digest[:16])
for p in preds:
    if p.get("family") == "T10":
        print(p["raw"], "newmap:", round(p["newmap"]["lat"], 4),
              round(p["newmap"]["lon"], 4), "+/-",
              round(p["newmap"]["uncertainty_radius_deg"], 4))
