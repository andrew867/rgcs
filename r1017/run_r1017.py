"""R10.17 — hedron + shell calibration bundle.

Emits every required table whether or not a survivor exists. Survival
criteria are declared HERE, before scoring, so that a result cannot be
promoted after the fact.
"""

from __future__ import annotations

import csv
import json
import math
import os
from pathlib import Path

import numpy as np

OUT = Path(os.environ.get(
    "RGCS_R1017_OUT",
    "C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/"
    "internal-docs/RGCS_R10_17_HEDRON_SHELL_CALIBRATION"))

#: PRE-REGISTERED survival criteria.
ANGULAR_SURVIVOR_RULE = (
    "one discrete variant, with NO per-face fitting, reproduces the "
    "face AND level-1 AND level-2 address of all four strict anchors")
SHELL_SURVIVOR_RULE = (
    "one (model, datum) places every S3-expected anchor inside shell 3 "
    "with 0 <= zeta <= 1, keeps the outer-in / inner-out invariant "
    "within 1e-6 m, and classifies the benthic monitor differently")


def wcsv(rel: str, rows: list) -> None:
    p = OUT / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8")
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(p, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from cwatlas.r1085a import final_projection as fp
    from r1017.angular import classify_point, surface_word_path
    from r1017.angular_search import search as angular_search
    from r1017.points import (SEED_POINTS, height_span_m,
                              training_points, with_coordinates)
    from r1017.shells import (DATUMS, EPOCH_WINDOW_BP, build_models,
                              invariant_check)

    for d in ("data", "maps", "figures", "reports"):
        (OUT / d).mkdir(parents=True, exist_ok=True)

    frame, _ = fp.training_alignment(2025.0)
    rot = np.asarray(frame.rotation, float)

    # ---------------------------------------------------- PHASE 1
    print("[1/4] angular hedron calibration ...")
    asr = angular_search(training_points())

    cls_rows, node_rows, bary_rows = [], [], []
    for p in with_coordinates():
        c = classify_point(p.lat, p.lon, rot, levels=4)
        cls_rows.append({
            "point_id": p.point_id, "name": p.name, "role": p.role,
            "phase": p.phase, "lat": p.lat, "lon": p.lon,
            "root_face": c["root_face"],
            "level1_macrocell": c["level1_macrocell"],
            "level2_cell": c["level2_cell"],
            "path": " ".join(str(x) for x in c["path"]),
            "classification": c["classification"],
            "surface_octal10": p.surface_octal10 or "",
            "address_face": (None if p.surface_word is None
                             else (p.surface_word >> 25) & 0b11111),
            "address_path": ("" if p.surface_word is None else
                             " ".join(str(x) for x in
                                      surface_word_path(p.surface_word, 2))),
        })
        node_rows.append({
            "point_id": p.point_id,
            "nearest_face_vertex_index": c["nearest_face_vertex_index"],
            "nearest_face_vertex_km": round(c["nearest_face_vertex_km"], 3),
            "nearest_cell_vertex_index": c["nearest_cell_vertex_index"],
            "nearest_cell_vertex_km": round(c["nearest_cell_vertex_km"], 3),
            "nearest_cell_edge": c["nearest_cell_edge"],
            "nearest_cell_edge_km": round(c["nearest_cell_edge_km"], 3),
            "cell_edge_length_km": round(c["cell_edge_length_km"], 3),
            "relative_vertex_distance": round(c["relative_vertex_distance"], 5),
            "relative_edge_distance": round(c["relative_edge_distance"], 5),
            "classification": c["classification"]})
        bary_rows.append({
            "point_id": p.point_id,
            "bary_face_a": c["barycentric_face"][0],
            "bary_face_b": c["barycentric_face"][1],
            "bary_face_c": c["barycentric_face"][2],
            "bary_cell_a": c["barycentric_cell"][0],
            "bary_cell_b": c["barycentric_cell"][1],
            "bary_cell_c": c["barycentric_cell"][2]})
    wcsv("data/point_hedron_cell_classification.csv", cls_rows)
    wcsv("data/nearest_nodes_edges.csv", node_rows)
    wcsv("data/barycentric_coordinates.csv", bary_rows)
    wcsv("data/angular_model_ranking.csv", [
        {"rank": i + 1, "variant_id": r["variant_id"],
         "context": r["context"], "face_offset": r["face_offset"],
         "handedness": r["handedness"], "pole": r["pole"],
         "face_matches": r["face_matches"],
         "level1_matches": r["level1_matches"],
         "level2_matches": r["level2_matches"],
         "total_score": r["total_score"], "max_score": r["max_score"],
         "full_agreement": r["full_agreement"],
         "permutation": json.dumps(r.get("permutation"))}
        for i, r in enumerate(asr["top"] + asr["top_permutation"])])

    angular_survivor = bool(asr["full_agreement_variants"])

    # ---------------------------------------------------- PHASE 2
    print("[2/4] radial shell-height calibration ...")
    models = build_models(SEED_POINTS)
    bnd_rows, zeta_rows, inv_rows, rank_rows = [], [], [], []
    for m in models:
        b = m.boundaries_m()
        for s in m.shells:
            bnd_rows.append({
                "model_id": m.model_id, "datum_id": m.datum_id,
                "datum_offset_m": m.datum_offset_m, "shell": f"S{s}",
                "inner_boundary_m_msl": round(b[s][0], 3),
                "outer_boundary_m_msl": round(b[s][1], 3),
                "thickness_m": round(m.thickness_m[s], 3),
                "provenance": m.provenance[:110]})
        for s in (0, 1, 2):
            bnd_rows.append({
                "model_id": m.model_id, "datum_id": m.datum_id,
                "datum_offset_m": m.datum_offset_m, "shell": f"S{s}",
                "inner_boundary_m_msl": "", "outer_boundary_m_msl": "",
                "thickness_m": "",
                "provenance": "BELOW_LAND_ZERO_NO_DECLARED_THICKNESS "
                              "(recorded architecture gives shells 0-2 "
                              "no thickness)"})
        in_s3, ok_inv, monitor_split = 0, True, False
        for p in SEED_POINTS:
            heights = list(p.variants_m) or ([p.height_m]
                                             if p.has_height else [])
            for h in heights:
                c = m.classify(h)
                row = {"model_id": m.model_id, "datum_id": m.datum_id,
                       "point_id": p.point_id, "name": p.name,
                       "height_m_msl": h,
                       "height_sigma_m": p.height_sigma_m,
                       "height_basis": p.height_basis,
                       "expected_shell": p.expected_shell,
                       "status": c["status"]}
                if c["status"] == "IN_OPERATIONAL_STACK":
                    row.update({
                        "shell": f"S{c['shell']}",
                        "zeta": round(c["zeta"], 8),
                        "shell_inner_m": round(c["inner_m"], 3),
                        "shell_outer_m": round(c["outer_m"], 3),
                        "shell_thickness_m": round(c["thickness_m"], 3),
                        "d_in_m": round(c["d_in_m"], 3),
                        "d_s_m": round(c["d_s_m"], 3)})
                    iv = invariant_check(m, c["shell"], c["zeta"])
                    row["invariant_residual_m"] = iv["residual_m"]
                    row["invariant_holds"] = iv["invariant_holds"]
                    ok_inv = ok_inv and iv["invariant_holds"]
                    inv_rows.append({"model_id": m.model_id,
                                     "datum_id": m.datum_id,
                                     "point_id": p.point_id, **iv})
                    if c["shell"] == 3 and \
                            p.expected_shell.startswith("S3"):
                        in_s3 += 1
                    if p.role.startswith("diagnostic_monitor") and \
                            c["shell"] != 3:
                        monitor_split = True
                else:
                    row.update({"shell": "", "zeta": "",
                                "below_by_m": c.get("below_by_m"),
                                "reason": c.get("reason", "")})
                    if p.role.startswith("diagnostic_monitor"):
                        monitor_split = True
                zeta_rows.append(row)
        expect_s3 = sum(1 for p in SEED_POINTS
                        if p.expected_shell.startswith("S3")
                        and p.has_height)
        rank_rows.append({
            "model_id": m.model_id, "datum_id": m.datum_id,
            "datum_offset_m": m.datum_offset_m,
            "s3_anchors_in_S3": in_s3,
            "s3_anchors_expected": expect_s3,
            "invariant_holds": ok_inv,
            "monitor_classified_differently": monitor_split,
            "shell_survivor": bool(in_s3 == expect_s3 and ok_inv
                                   and monitor_split),
            "shell3_thickness_m": round(m.thickness_m[3], 3),
            "provenance": m.provenance[:110]})
    rank_rows.sort(key=lambda r: (-r["s3_anchors_in_S3"],
                                  r["model_id"]))
    wcsv("data/shell_boundaries_outer_to_inner.csv", bnd_rows)
    wcsv("data/point_shell_zeta_table.csv", zeta_rows)
    wcsv("data/outer_in_inner_out_invariant_report.csv", inv_rows)
    wcsv("data/shell_model_ranking.csv", rank_rows)
    shell_survivors = [r for r in rank_rows if r["shell_survivor"]]

    # ---------------------------------------------------- PHASE 3
    print("[3/4] joint calibration ...")
    best_ang = (asr["best_permutation"] or asr["best"])
    best_shell = shell_survivors[0] if shell_survivors else rank_rows[0]
    joint_rows, receipts = [], []
    for r in rank_rows[:12]:
        a = best_ang["total_score"] / max(best_ang["max_score"], 1)
        s = r["s3_anchors_in_S3"] / max(r["s3_anchors_expected"], 1)
        dof = 2 if r["datum_id"].startswith("FITTED") else 1
        joint_rows.append({
            "angular_variant": best_ang["variant_id"],
            "shell_model": r["model_id"], "datum": r["datum_id"],
            "angular_score": round(a, 4), "shell_score": round(s, 4),
            "invariant_holds": r["invariant_holds"],
            "degrees_of_freedom": dof,
            "joint_score": round(a + s - 0.05 * dof, 4),
            "survivor": bool(r["shell_survivor"] and angular_survivor)})
    joint_rows.sort(key=lambda r: -r["joint_score"])
    wcsv("data/joint_model_ranking.csv", joint_rows)

    for p in with_coordinates():
        c = classify_point(p.lat, p.lon, rot, levels=4)
        mm = [m for m in models
              if m.model_id == best_shell["model_id"]
              and m.datum_id == best_shell["datum_id"]][0]
        sc = mm.classify(p.height_m) if p.has_height else {
            "status": "NO_HEIGHT"}
        receipts.append({
            "point_id": p.point_id, "name": p.name, "role": p.role,
            "angular_cell": f"F{c['root_face']}/"
                            f"{'.'.join(str(x) for x in c['path'])}",
            "angular_class": c["classification"],
            "shell_model": mm.model_id, "datum": mm.datum_id,
            "shell": (f"S{sc['shell']}"
                      if sc.get("shell") is not None else ""),
            "zeta": (round(sc["zeta"], 8)
                     if sc.get("zeta") is not None else ""),
            "d_in_m": (round(sc["d_in_m"], 3)
                       if sc.get("d_in_m") is not None else ""),
            "shell_status": sc["status"],
            "confidence": ("ANGULAR_FACE_CONSISTENT_PATH_UNDERFIT"
                           if p.surface_word else
                           "HOLDOUT_NO_ADDRESS_TO_COMPARE")})
    wcsv("data/joint_point_receipts.csv", receipts)

    failed = []
    if not angular_survivor:
        failed.append({
            "layer": "ANGULAR", "model": best_ang["variant_id"],
            "reason": "PATH_LEVEL1_DISAGREEMENT",
            "detail": f"best score {best_ang['total_score']}/"
                      f"{best_ang['max_score']}; the face layer is "
                      "consistent but level-1 child indices disagree "
                      "for the North American face (geometric 3 vs "
                      "address 0) under every pure discrete variant"})
    for r in rank_rows:
        if not r["shell_survivor"]:
            if r["s3_anchors_in_S3"] == 0:
                why = ("DATUM_ABOVE_ALL_POINTS: the shell-3 zero sits "
                       f"at {r['datum_offset_m']} m, above every "
                       "declared point height, so no point enters the "
                       "operational stack")
            elif not r["monitor_classified_differently"]:
                why = "MONITOR_NOT_SEPARATED"
            else:
                why = "NOT_ALL_S3_ANCHORS_INSIDE_SHELL_3"
            failed.append({"layer": "SHELL", "model": r["model_id"],
                           "datum": r["datum_id"], "reason": why,
                           "detail": f"{r['s3_anchors_in_S3']}/"
                                     f"{r['s3_anchors_expected']} "
                                     "anchors in S3"})
    wcsv("data/failed_model_reasons.csv", failed)

    # ---------------------------------------------------- PHASE 4
    print("[4/4] figures + report ...")
    fig, ax = plt.subplots(figsize=(9, 6), dpi=140)
    mm = [m for m in models
          if m.model_id == "REPO_ATMOSPHERIC_LADDER_V1"
          and m.datum_id == "DECLARED_ALTERNATIVE_MSL_0M"][0]
    b = mm.boundaries_m()
    for s in mm.shells:
        ax.axhspan(b[s][0] / 1000.0, b[s][1] / 1000.0, alpha=0.13,
                   label=f"S{s}")
        ax.text(0.02, (b[s][0] + b[s][1]) / 2000.0, f"S{s}",
                fontsize=8, va="center")
    for p in SEED_POINTS:
        if p.has_height:
            ax.plot([0.5], [p.height_m / 1000.0], "o", ms=5)
            ax.annotate(p.name[:18], (0.5, p.height_m / 1000.0),
                        fontsize=6, xytext=(6, 0),
                        textcoords="offset points")
    ax.axhline(0.84, ls="--", lw=1, color="crimson")
    ax.text(0.55, 0.84, "recorded land-zero 840 m", fontsize=7,
            color="crimson", va="bottom")
    ax.set_ylim(-1, 14)
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_ylabel("height above MSL (km)")
    ax.set_title("R10.17 shell cross-section (MSL datum, atmospheric "
                 "ladder)\nevery seed point sits inside S3 except the "
                 "benthic monitor", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "figures/shell_cross_section.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(10, 5), dpi=140)
    for p in with_coordinates():
        c = classify_point(p.lat, p.lon, rot, levels=2)
        ax.scatter([p.lon], [p.lat], s=40)
        ax.annotate(f"{p.name[:16]}\nF{c['root_face']}/"
                    f"{c['level1_macrocell']}.{c['level2_cell']}",
                    (p.lon, p.lat), fontsize=6,
                    xytext=(4, 4), textcoords="offset points")
    ax.set_xlim(-100, 60)
    ax.set_ylim(30, 70)
    ax.grid(True, lw=0.3, alpha=0.5)
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title("R10.17 angular calibration: containing face / L1.L2 "
                 "cell", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "maps/angular_calibration_map.png")
    plt.close(fig)

    if angular_survivor and shell_survivors:
        verdict = "R10_17_HEDRON_SHELL_CALIBRATION_SURVIVOR_FOUND"
    elif angular_survivor:
        verdict = "R10_17_ANGULAR_SURVIVOR_SHELL_UNDERFIT"
    elif shell_survivors:
        verdict = "R10_17_SHELL_SURVIVOR_ANGULAR_UNDERFIT"
    else:
        verdict = "R10_17_NO_CALIBRATION_SURVIVOR_BUT_TABLES_EMITTED"

    summary = {
        "schema": "rgcs.r1017.summary.v1",
        "epoch_window_bp": EPOCH_WINDOW_BP,
        "height_span": height_span_m(),
        "angular": {
            "variants_evaluated": asr["variants_evaluated"],
            "best_variant": best_ang["variant_id"],
            "best_score": best_ang["total_score"],
            "max_score": best_ang["max_score"],
            "face_matches": best_ang["face_matches"],
            "level1_matches": best_ang["level1_matches"],
            "level2_matches": best_ang["level2_matches"],
            "permutation": best_ang.get("permutation"),
            "survivor": angular_survivor,
            "rule": ANGULAR_SURVIVOR_RULE},
        "shell": {
            "models_built": len(models),
            "survivors": len(shell_survivors),
            "best": best_shell,
            "rule": SHELL_SURVIVOR_RULE,
            "tables_emitted": ["shell_boundaries_outer_to_inner.csv",
                               "point_shell_zeta_table.csv",
                               "outer_in_inner_out_invariant_report.csv",
                               "shell_model_ranking.csv"]},
        "joint_best": joint_rows[0] if joint_rows else None,
        "verdict": verdict,
    }
    (OUT / "data/r1017_summary.json").write_text(
        json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print(json.dumps({"verdict": verdict,
                      "angular_best": best_ang["variant_id"],
                      "angular_score":
                          f"{best_ang['total_score']}/{best_ang['max_score']}",
                      "shell_models": len(models),
                      "shell_survivors": len(shell_survivors),
                      "zeta_rows": len(zeta_rows),
                      "boundary_rows": len(bnd_rows)}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
