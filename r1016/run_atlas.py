"""R10.16 — generate the full atlas bundle."""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

OUT = Path(os.environ.get(
    "RGCS_R1016_OUT",
    "C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/"
    "internal-docs/RGCS_R10_16_VECTOR_ATLAS_PUBLIC_WORKING"))


def main() -> int:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from cwatlas.r1085a import final_projection as fp
    from r1016.atlas import (CONFIDENCE, FEATURE_CLASSES,
                             PLACE_ENRICHMENT_STATUS, build_rows,
                             write_csv, write_geojson, write_kml)
    from r1016.inventory import LUNAR_CANDIDATES, inventory
    from r1016.project import STRICT_ANCHORS, STRICT_GATE_RMS_KM
    from r1016.salvage import salvage_all
    from r1016.search import run, view_word_maps

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data").mkdir(exist_ok=True)
    (OUT / "maps").mkdir(exist_ok=True)
    (OUT / "runbooks").mkdir(exist_ok=True)

    print("[1/7] exhaustive discrete model search ...")
    res = run(contexts=("ALL_SEALED",))
    gate_passed = res["survivor_count"] > 0
    best = res["best"]

    print("[2/7] rigid-rotation salvage diagnostic ...")
    sal = salvage_all(view_word_maps(list(STRICT_ANCHORS)))

    print("[3/7] projecting all vectors under the best model ...")
    frame, _ = fp.training_alignment(2025.0)
    rot = {"TRAINED": np.asarray(frame.rotation, float)}
    rot.update({k: np.asarray(v, float)
                for k, v in fp.sealed_contexts().items()})
    rows = build_rows(gate_passed, best,
                      rot[best["variant"].context],
                      include_private=True)

    inv = inventory(include_private=True)
    write_csv(OUT / "data/vector_projection_candidates.csv", rows)
    n_geo = write_geojson(
        OUT / "data/vector_projection_candidates.geojson", rows)
    n_kml = write_kml(OUT / "data/vector_projection_candidates.kml",
                      rows)

    print("[4/7] model ranking, anchor fit, holdout, ocean reports ...")
    write_csv(OUT / "data/model_ranking.csv", [
        {"rank": i + 1, "view": r["view"], "window": r["window"],
         "root_variant_id": r["variant_id"],
         "anchor_coverage": r["anchor_coverage"],
         "strict_anchor_rms_km": round(r["rms_km"], 3),
         "worst_anchor_km": round(r["max_km"], 3),
         "passes_25km_gate": r["passes_gate"]}
        for i, r in enumerate(res["top"])])

    afr = []
    for r in res["top"][:5]:
        for row in r["rows"]:
            afr.append({"view": r["view"], "window": r["window"],
                        "root_variant_id": r["variant_id"], **row})
    write_csv(OUT / "data/anchor_fit_report.csv", afr)

    write_csv(OUT / "data/holdout_report.csv", [{
        "status": "NOT_RUN",
        "reason": "a holdout test ranks models that have already "
                  "passed calibration. No model passed the strict "
                  "anchor gate, so there is nothing to rank and a "
                  "holdout score would be meaningless.",
        "strict_gate_km": STRICT_GATE_RMS_KM,
        "best_rms_km": round(best["rms_km"], 1) if best else None,
    }])

    coord_rows = [r for r in rows if r.get("lat") is not None]
    write_csv(OUT / "data/ocean_failure_report.csv", [{
        "status": "OCEAN_TEST_NOT_DECISIVE",
        "coordinates_produced": len(coord_rows),
        "land_ocean_determination":
            "UNDETERMINED_NO_COASTLINE_DATASET",
        "reason": "no offline coastline dataset is available, so no "
                  "land/ocean call is made. The run does NOT claim "
                  "OCEAN_HEAVY_NO_WARP_FAILURE, because that label "
                  "requires an actual ocean determination. The "
                  "controlling failure is the strict anchor gate, "
                  "which failed for every discrete variant and for "
                  "the optimal rigid rotation.",
        "controlling_failure":
            "STRICT_ANCHOR_GATE_FAILED_ALL_DISCRETE_VARIANTS",
    }])

    write_csv(OUT / "data/place_feature_enrichment.csv", [{
        "status": "DEFERRED", "detail": PLACE_ENRICHMENT_STATUS,
        "policy": "coordinates first, place-enrich second",
        "feature_classes_available": "; ".join(FEATURE_CLASSES),
        "targeting_language": "NONE - no location is described as a "
                              "target, and no operational detail is "
                              "collected",
    }])

    print("[5/7] maps ...")
    def scatter(path, subset, title, xlim=(-180, 180), ylim=(-90, 90)):
        fig, ax = plt.subplots(figsize=(11, 6), dpi=140)
        ax.set_xlim(*xlim); ax.set_ylim(*ylim)
        ax.grid(True, lw=0.3, alpha=0.5)
        ax.set_xlabel("longitude (deg)"); ax.set_ylabel("latitude (deg)")
        if subset:
            ax.scatter([r["lon"] for r in subset],
                       [r["lat"] for r in subset], s=14, alpha=0.7,
                       label=f"diagnostic positions (n={len(subset)})")
        for wire, (place, la, lo) in STRICT_ANCHORS.items():
            ax.scatter([lo], [la], marker="*", s=180, c="crimson",
                       zorder=5)
            ax.annotate(place, (lo, la), fontsize=7,
                        xytext=(3, 3), textcoords="offset points")
        ax.set_title(title + "\nDIAGNOSTIC ONLY - no model passed the "
                             "strict anchor gate", fontsize=9)
        ax.legend(loc="lower left", fontsize=7)
        fig.tight_layout(); fig.savefig(path); plt.close(fig)

    scatter(OUT / "maps/world_all_candidates.png", coord_rows,
            "RGCS R10.16 - all diagnostic vector positions")
    scatter(OUT / "maps/uk_cluster.png",
            [r for r in coord_rows
             if -12 <= r["lon"] <= 4 and 48 <= r["lat"] <= 62],
            "UK / Channel window", (-12, 4), (48, 62))
    scatter(OUT / "maps/north_america_cluster.png",
            [r for r in coord_rows
             if -100 <= r["lon"] <= -55 and 35 <= r["lat"] <= 55],
            "North America window", (-100, -55), (35, 55))
    moon = [r for r in rows if r["body_profile"] == "MOON"]
    if moon:
        fig, ax = plt.subplots(figsize=(8, 5), dpi=140)
        ax.text(0.5, 0.5,
                "MOON SHEET\n\n"
                + "\n".join(sorted(LUNAR_CANDIDATES))
                + "\n\nNo lunar body profile is implemented.\n"
                  "No lunar coordinate is asserted.\n"
                  "Kept as an open diagnostic trail.",
                ha="center", va="center", fontsize=10)
        ax.axis("off"); fig.tight_layout()
        fig.savefig(OUT / "maps/moon_sheet.png"); plt.close(fig)

    print("[6/7] runbook + atlas document ...")
    summary = {
        "schema": "rgcs.r1016.atlas-summary.v1",
        "gate_passed": gate_passed,
        "gate_km": STRICT_GATE_RMS_KM,
        "models_evaluated": res["models_evaluated"],
        "full_anchor_models": res["models_with_full_anchor_coverage"],
        "survivors": res["survivor_count"],
        "best_rms_km": best["rms_km"] if best else None,
        "best_model": {k: v for k, v in best.items()
                       if k not in ("variant", "rows")} if best else None,
        "views_tested": res["views_tested"],
        "salvage_best_rms_km": (sal["best"]["rms_km"]
                                if sal["best"] else None),
        "salvage_passes": sal["any_passes_25km"],
        "inventory": {k: v for k, v in inv.items() if k != "rows"},
        "rows_emitted": len(rows),
        "coordinates_emitted": len(coord_rows),
        "geojson_features": n_geo, "kml_placemarks": n_kml,
        "verdict": res["verdict"],
    }
    (OUT / "data/atlas_summary.json").write_text(
        json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in
                      ("gate_passed", "models_evaluated", "survivors",
                       "best_rms_km", "salvage_best_rms_km",
                       "rows_emitted", "coordinates_emitted")},
                     indent=1, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
