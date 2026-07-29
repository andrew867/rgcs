"""R10.25 — reproducible run driver. Emits every required receipt.

Run:  python -m r1025.run <output_dir>
"""

from __future__ import annotations

import csv
import json
import math
import sys
from pathlib import Path

from r1016.quarantine import QUARANTINED, assert_clean
from r1025 import hedra
from r1025.projector import (
    HARD_ANCHORS,
    Candidate,
    containing_lineage,
    evaluate,
    fields,
    q22_symbols,
)
from r1025.search import (
    _p_map_ok,
    eligible_hedra,
    false_hit_expectation,
    grid_orientations,
    run,
    sealed_orientations,
)

EARTH_R = 6371.0

#: Holdouts. DIAGNOSTIC ONLY -- never used to select or tune a
#: projector, and never scored by place name.
HOLDOUTS = [
    ("BALTIC_SEA_ANOMALY", 55.866667, 18.600000, "MONITOR_HOLDOUT"),
    ("NORTH_SEA_57N_5E", 57.0, 5.0, "MONITOR_HOLDOUT"),
    ("RING_OF_BRODGAR", 59.0010, -3.2290, "SOFT_HOLDOUT"),
    ("GOBEKLI_TEPE", 37.2232, 38.9224, "SOFT_HOLDOUT"),
    ("BERMUDA_REGION_MIAMI", 25.7617, -80.1918, "REGION_VERTEX_PLACEHOLDER"),
    ("BERMUDA_REGION_BERMUDA", 32.3078, -64.7505, "REGION_VERTEX_PLACEHOLDER"),
    ("BERMUDA_REGION_SAN_JUAN", 18.4655, -66.1057, "REGION_VERTEX_PLACEHOLDER"),
]

#: Wilkes Land is REQUIRED by the pack to come from an exact sourced
#: centroid. No such source is available in this environment, so it is
#: recorded as unresolved rather than guessed.
WILKES_STATUS = ("WILKES_LAND_GRAVITY_ANOMALY", None, None,
                 "ROOT_CANDIDATE_UNRESOLVED_NO_EXACT_SOURCE")


def gc_km(a, b) -> float:
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    return EARTH_R * 2 * math.asin(math.sqrt(
        math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2)
        * math.sin((lo2 - lo1) / 2) ** 2))


def _write(path: Path, rows, fields_=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = fields_ or sorted({k for r in rows for k in r})
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def authority_receipt() -> list:
    """Agent 00 — what the run is allowed to use, and what it refuses."""
    rows = []
    for a in HARD_ANCHORS:
        f5, q, s3 = fields(a.vector)
        rows.append({
            "id": a.name, "vector": a.vector, "authority": "HARD_ANCHOR_ACTIVE",
            "F5": f5, "S3": s3,
            "q22_symbols": " ".join(map(str, q22_symbols(q))),
            "surface_octal10": format(a.vector, "010o"),
            "lat": a.lat, "lon": a.lon,
            "in_scoring": True, "reason": "non-quarantined hard anchor"})
    for v, why in sorted(QUARANTINED.items()):
        rows.append({"id": "MONTREAL_QUARANTINE", "vector": v,
                     "authority": "HARD_EXCLUDE", "in_scoring": False,
                     "reason": why})
    rows.append({"id": WILKES_STATUS[0], "vector": "",
                 "authority": WILKES_STATUS[3], "in_scoring": False,
                 "reason": "pack requires an exact sourced centroid; none "
                           "available in this environment, so it is NOT "
                           "guessed and NOT used as a frame parameter"})
    return rows


def depth_offset_tests() -> list:
    """Where does each anchor pair first diverge, and at what scale?"""
    rows = []
    ico = hedra.families()["ICOSAHEDRON_20_FACE_CENTRE"]
    edge = ico.edge_arc_km()
    pairs = [(a, b) for i, a in enumerate(HARD_ANCHORS)
             for b in HARD_ANCHORS[i + 1:]]
    for a, b in pairs:
        sep = gc_km((a.lat, a.lon), (b.lat, b.lon))
        same_face = a.f5 == b.f5
        pa, pb = a.path, b.path
        div = next((i for i in range(11) if pa[i] != pb[i]), None)
        need = math.ceil(math.log2(edge / sep)) if sep else None
        for off in range(5):
            sdiv = None
            if div is not None:
                sdiv = div - off if div >= off else None
            rows.append({
                "pair": f"{a.name}|{b.name}",
                "separation_km": round(sep, 1),
                "same_F5_root_face": same_face,
                "first_divergent_q22_symbol": div,
                "depth_offset": off,
                "implied_spatial_level_of_divergence": sdiv,
                "cell_km_at_that_level": (round(edge / 2 ** (sdiv + 1), 1)
                                          if sdiv is not None else None),
                "min_level_needed_to_resolve_separation": need,
                "consistent": (None if sdiv is None else
                               (edge / 2 ** (sdiv + 1)) >= sep * 0.5),
                "note": "divergence at spatial level L means the points "
                        "sit in different level-(L+1) cells, which "
                        "requires them to straddle a boundary when their "
                        "separation is much smaller than the cell",
            })
    return rows


def dds36_tests() -> list:
    """Integrate or reject the 36-bit DDS/NCO width hypothesis."""
    rows = []
    base = 2.45e9
    claimed = 0.0356521923094988
    for bits in (30, 32, 36, 40, 48):
        step = base / 2 ** bits
        rows.append({
            "model": f"DDS_NCO_{bits}BIT",
            "clock_hz": base, "step_hz": step,
            "matches_claimed_0_03565": abs(step - claimed) < 1e-12,
            "relative_error": abs(step - claimed) / claimed,
            "verdict": ("ARITHMETIC_MATCH" if abs(step - claimed) < 1e-12
                        else "NO_MATCH")})
    # width/depth arithmetic for the address, independent of any clock
    for name, total, f5b, s3b, branch in (
            ("W30_F5_Q22_S3_QUATERNARY", 30, 5, 3, 4),
            ("W36_F5_Q28_S3_QUATERNARY", 36, 5, 3, 4),
            ("W36_12_OCTAL_PATH", 36, 0, 0, 8),
            ("W36_F5_Q28_S3_OCTAL", 36, 5, 3, 8)):
        pathbits = total - f5b - s3b
        per = int(math.log2(branch))
        levels = pathbits // per
        ico = hedra.families()["ICOSAHEDRON_20_FACE_CENTRE"]
        lin = 2 ** (per / 2.0) if branch == 8 else 2.0
        rows.append({
            "model": name, "total_bits": total, "path_bits": pathbits,
            "branch": branch, "levels": levels,
            "finest_cell_km": round(ico.edge_arc_km() / (lin ** levels), 4),
            "matches_claimed_0_03565": "", "verdict":
                "ADDRESS_WIDTH_ARITHMETIC_ONLY_NO_CLOCK_CLAIM"})
    return rows


def holdout_tests(hed, rot, hd, po, depth=6) -> list:
    rows = []
    for name, lat, lon, role in HOLDOUTS:
        g = containing_lineage(hed, lat, lon, rot, hd, po, depth)
        rows.append({
            "holdout": name, "role": role, "lat": lat, "lon": lon,
            "root_face": g["face"], "path": ".".join(map(str, g["path"])),
            "cell_id": g["cell_id"], "edge_flags": ";".join(g["flags"]),
            "scored": False,
            "note": "geometry signature only; DIAGNOSTIC, never training, "
                    "never place-name scored"})
    rows.append({"holdout": WILKES_STATUS[0], "role": WILKES_STATUS[3],
                 "lat": "", "lon": "", "root_face": "", "path": "",
                 "cell_id": "", "edge_flags": "", "scored": False,
                 "note": "NOT GUESSED: pack requires an exact sourced "
                         "centroid and none is available here"})
    return rows


def main(outdir: str) -> dict:
    out = Path(outdir)
    data, reports = out / "data", out / "reports"
    assert_clean([a.vector for a in HARD_ANCHORS], where="R10.25 run")

    _write(data / "authority_cleanup_receipt.csv", authority_receipt())
    _write(data / "hedron_candidate_space.csv", hedra.candidate_space())
    _write(data / "depth_offset_tests.csv", depth_offset_tests())
    _write(data / "dds36_vector_width_tests.csv", dds36_tests())

    results = {}
    for lane in ("SEALED", "GRID"):
        r = run(lane)
        results[lane] = r

    # per-child-model false-hit accounting
    fh_rows = []
    for lane, r in results.items():
        n_by = {}
        for rej in r["rejections"]:
            cid = rej.get("candidate_id", "")
            if "/UNIFORM/" in cid or cid.endswith("UNIFORM"):
                n_by["UNIFORM"] = n_by.get("UNIFORM", 0) + 1
            elif cid:
                n_by["PER_LEVEL"] = n_by.get("PER_LEVEL", 0) + 1
        for s in r["survivors"]:
            n_by[s["child_model"]] = n_by.get(s["child_model"], 0) + 1
        for model in ("UNIFORM", "PER_LEVEL"):
            surv = [s for s in r["survivors"] if s["child_model"] == model]
            deep = [s for s in surv if s["spatial_depth"] >= 6]
            n = n_by.get(model, 0)
            for depth in (3, 6):
                pairs = 3 * depth
                p = (_p_map_ok(pairs, 4) if model == "UNIFORM"
                     else _p_map_ok(3, 4) ** depth)
                fh_rows.append({
                    "lane": lane, "child_model": model,
                    "spatial_depth": depth,
                    "candidates_in_lane_model": n,
                    "pairs_constraining_each_map":
                        pairs if model == "UNIFORM" else 3,
                    "p_random_candidate_passes": p,
                    "expected_false_survivors": n * p,
                    "observed_survivors_any_depth": len(surv),
                    "observed_survivors_depth_ge_6": len(deep)})
    _write(data / "false_hit_expectation.csv", fh_rows)

    surv_rows, rej_rows = [], []
    for lane, r in results.items():
        for s in r["survivors"]:
            surv_rows.append({
                "lane": lane, "candidate_id": s["candidate_id"],
                "hedron": s["hedron"], "orientation": s["orientation"],
                "handedness": s["handedness"], "pole": s["pole"],
                "depth_offset": s["depth_offset"], "branch": s["branch"],
                "child_model": s["child_model"],
                "spatial_depth": s["spatial_depth"],
                "anchors_verified": s["anchors_verified"],
                "child_map": json.dumps(s["child_map"]),
                "face_map": json.dumps(s["face_map"]),
                "evidential": (s["child_model"] == "UNIFORM"
                               and s["spatial_depth"] >= 6)})
        for j in r["rejections"]:
            rej_rows.append({"lane": lane, **j})
    _write(data / "terra_projector_survivors.csv", surv_rows)
    _write(data / "terra_projector_rejections.csv", rej_rows)

    keep, _ = eligible_hedra()
    ico = keep["ICOSAHEDRON_20_FACE_CENTRE"]
    rot = sealed_orientations().get("TRAINED",
                                    sealed_orientations()["IDENTITY"])
    _write(data / "anomaly_holdout_point_ledger.csv",
           holdout_tests(ico, rot, "right", "south_up"))

    evidential = [s for s in surv_rows if s["evidential"]]
    verdict = ("R10_25_EARTH_PROJECTOR_SURVIVOR_FOUND" if evidential
               else "R10_25_EARTH_PROJECTOR_STILL_UNRECOVERED_"
                    "EXACT_FAILURE_EMITTED")

    exact = []
    for lane, r in results.items():
        for model in ("UNIFORM", "PER_LEVEL"):
            for depth in (2, 3, 4, 6, 8):
                surv = [s for s in r["survivors"]
                        if s["child_model"] == model
                        and s["spatial_depth"] == depth]
                exact.append({
                    "lane": lane, "child_model": model,
                    "spatial_depth": depth,
                    "survivors": len(surv),
                    "min_depth_required_for_erie_toronto": 6,
                    "discriminating": depth >= 6 and model == "UNIFORM",
                    "exact_failure":
                        "" if surv else
                        ("NO_CANDIDATE_SURVIVES_CHILD_MAP_CONSISTENCY_AND_"
                         "CONTAINMENT_AT_THIS_DEPTH")})
    _write(data / "exact_failure_table.csv", exact)

    summary = {
        "verdict": verdict,
        "lanes": {k: {"candidates_tested": v["candidates_tested"],
                      "survivors": len(v["survivors"]),
                      "survivors_depth_ge_6": len(v["survivors_at_depth_ge_6"]),
                      "uniform_survivors": len(
                          [s for s in v["survivors"]
                           if s["child_model"] == "UNIFORM"])}
                  for k, v in results.items()},
        "evidential_survivors": len(evidential),
        "hedra_rejected": results["SEALED"]["hedra_rejected"],
    }
    (data / "run_summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8")
    return summary


if __name__ == "__main__":
    print(json.dumps(main(sys.argv[1]), indent=2))
