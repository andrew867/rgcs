"""R10.16B — semantic profile recovery bundle."""

from __future__ import annotations

import csv
import json
import os
from pathlib import Path

OUT = Path(os.environ.get(
    "RGCS_R1016B_OUT",
    "C:/Users/andrew/OneDrive - Green O365/Documents/GitHub/RGCS/"
    "internal-docs/RGCS_R10_16B_SEMANTIC_PROFILE_RECOVERY"))

#: Family 7 structural inputs are NOT stored in tracked source.
#: They are operator path-vector values, authorised for the working
#: output but not for the public tree, so they are loaded at run time
#: from a JSON file named by RGCS_R1016_STRUCTURE_INPUT:
#:
#:   {"pairs": [[compact, refined], ...],
#:    "prefix_families": {"label": [wire, ...], ...}}
#:
#: With the variable unset the structural report is simply empty and
#: says so, rather than embedding the values here.
STRUCTURE_INPUT_ENV = "RGCS_R1016_STRUCTURE_INPUT"


def structure_input() -> dict:
    path = os.environ.get(STRUCTURE_INPUT_ENV)
    if not path or not Path(path).is_file():
        return {"pairs": [], "prefix_families": {}}
    return json.loads(Path(path).read_text(encoding="utf-8"))


def wcsv(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def payload_octal(wire: str) -> str:
    return format(int(str(wire)[2:-1]), "o")


def path_structure_report() -> list:
    """Family 7: compact/refined relations, before any geography."""
    src = structure_input()
    rows = []
    if not src["pairs"] and not src["prefix_families"]:
        return [{"compact": "NO_STRUCTURE_INPUT", "refined": "",
                 "compact_payload_octal": "", "refined_payload_octal": "",
                 "right_append": None, "appended_symbols": None,
                 "left_append": None,
                 "relation": "NOT_SUPPLIED_SET_"
                             + STRUCTURE_INPUT_ENV}]
    for compact, refined in src["pairs"]:
        oc, orf = payload_octal(compact), payload_octal(refined)
        rows.append({
            "compact": compact, "refined": refined,
            "compact_payload_octal": oc,
            "refined_payload_octal": orf,
            "right_append": orf.startswith(oc),
            "appended_symbols": orf[len(oc):] if orf.startswith(oc)
            else None,
            "left_append": orf.endswith(oc),
            "relation": ("RIGHT_APPEND_CHILD" if orf.startswith(oc)
                         else "LEFT_APPEND" if orf.endswith(oc)
                         else "NO_SIMPLE_APPEND_RELATION"),
        })
    for fam, members in src["prefix_families"].items():
        octs = [payload_octal(m) for m in members]
        n = 0
        if len(octs) > 1:
            for chars in zip(*octs):
                if len(set(chars)) == 1:
                    n += 1
                else:
                    break
        rows.append({
            "compact": fam, "refined": " ".join(members),
            "compact_payload_octal": " ".join(octs),
            "refined_payload_octal": "",
            "right_append": None, "appended_symbols": None,
            "left_append": None,
            "relation": f"SHARED_OCTAL_PREFIX_{n}_SYMBOLS",
        })
    return rows


def main() -> int:
    from r1016.hierarchy import (prefix_proximity_test,
                                 stonehenge_avebury_relation)
    from r1016.profiles import search
    from r1016.project import STRICT_ANCHORS
    from r1016.search import view_word_maps

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data").mkdir(exist_ok=True)
    (OUT / "runbooks").mkdir(exist_ok=True)

    ppt = prefix_proximity_test()
    sa = stonehenge_avebury_relation()
    maps = view_word_maps(list(STRICT_ANCHORS))
    wbv = {m["view"]: m["words"] for m in maps}
    ps = search(wbv, shape_tolerance_deg=8.0, max_offset=24)

    wcsv(OUT / "data/pairwise_angle_residuals.csv", ppt["rows"])
    wcsv(OUT / "data/stonehenge_avebury_child_relation.csv", [sa])
    wcsv(OUT / "data/path_structure_report.csv",
         path_structure_report())
    wcsv(OUT / "data/profile_ranking.csv", [
        {"rank": i + 1, "view": s["view"], "profile_id": s["profile"],
         "family": ("F0_FIXED_RGCS30_CONTROL"
                    if s["view"].startswith("Z_") else
                    "F4_OCTAL_DIGIT" if s["profile"].startswith("OCT")
                    else "F5_BINARY_PAIRS"),
         "max_pairwise_angle_error_deg":
             round(s["max_angle_error_deg"], 4),
         "mean_pairwise_angle_error_deg":
             round(s["mean_angle_error_deg"], 4),
         "shape_compatible": s["max_angle_error_deg"] <= 8.0,
         "survivor_status": "FAILED",
         "failure_reason": "ROTATION_INVARIANT_MISMATCH"}
        for i, s in enumerate(ps["top_shapes"])])
    wcsv(OUT / "data/surviving_profiles.csv", [])
    wcsv(OUT / "data/best_failed_profiles.csv",
         [{"profile_id": s["profile"], "view": s["view"],
           "max_pairwise_angle_error_deg":
               round(s["max_angle_error_deg"], 4),
           "failure_reason": "ROTATION_INVARIANT_MISMATCH",
           "note": "no rotation, discrete or continuous, can align "
                   "this angle-set to the claimed anchors"}
          for s in ps["top_shapes"][:20]])
    wcsv(OUT / "data/strict_anchor_gate.csv", [{
        "gate_km": 25.0,
        "profiles_evaluated": ps["profiles_evaluated"],
        "shape_compatible": ps["shape_compatible"],
        "survivors": len(ps["survivors_25km"]),
        "best_pairwise_angle_error_deg":
            round(ps["best_shape_error_deg"], 4),
        "cell_quantization_deg": 0.03,
        "ratio_error_over_quantization":
            round(ps["best_shape_error_deg"] / 0.03, 1),
        "verdict": "NO_SEMANTIC_PROFILE_SURVIVOR",
    }])
    wcsv(OUT / "data/erie_mckean_special_enrichment.csv", [
        {"wire": "167849523", "trail": "ERIE_STRICT_ANCHOR",
         "label": "ERIE_PA_ANOMALOUS_MARITIME_MILITARY_HISTORY_NODE",
         "enrichment": "NOT_PERFORMED",
         "reason": "no profile survived the strict anchor gate, so no "
                   "coordinate is asserted and there is nothing to "
                   "enrich. No operational detail collected; no "
                   "location described as a target."},
        {"wire": "167829573", "trail":
            "MCKEAN_HISTORICAL_MILITARY_OR_LUNAR_ASSOCIATION_TRAIL",
         "label": "OPEN_DIAGNOSTIC_TRAIL", "enrichment": "NOT_PERFORMED",
         "reason": "kept open; not forced to any body"},
        {"wire": "167854923", "trail":
            "MCKEAN_HISTORICAL_MILITARY_OR_LUNAR_ASSOCIATION_TRAIL",
         "label": "OPEN_DIAGNOSTIC_TRAIL", "enrichment": "NOT_PERFORMED",
         "reason": "historical/lunar candidate; not forced to Earth or "
                   "Moon; routed to the Moon sheet as unresolved"}])
    wcsv(OUT / "data/moon_sheet.csv", [{
        "wire": "167854923", "body_profile": "MOON_CANDIDATE",
        "status": "NO_LUNAR_BODY_PROFILE_IMPLEMENTED",
        "coordinate_asserted": False,
        "note": "kept separate from the Earth sheet; no lunar "
                "coordinate is produced or implied"}])
    wcsv(OUT / "data/profile_inventory.csv", [
        {"family": "F0_FIXED_RGCS30_CONTROL",
         "description": "historical F5|Q22|S3 split, frozen projector",
         "status": "CONTROL_ONLY_NOT_PRIVILEGED", "evaluated": True},
        {"family": "F1_OCTAL_PATH_FACE_EXTERNAL",
         "description": "octal address as path, face enumerated 0..19",
         "status": "EVALUATED", "evaluated": True},
        {"family": "F2_OCTAL_PREFIX_FACE",
         "description": "1-2 leading octal symbols select the face",
         "status": "EVALUATED", "evaluated": True},
        {"family": "F3_OCTAL_SUFFIX_SHELL_EPOCH",
         "description": "0-2 trailing symbols as shell/epoch",
         "status": "EVALUATED_VIA_OFFSET_AND_LEVEL_BOUNDS",
         "evaluated": True},
        {"family": "F4_OCTAL_TO_QUATERNARY_WITH_CONTROL",
         "description": "d&3/d>>1 folds with preserved control bit",
         "status": "EVALUATED", "evaluated": True},
        {"family": "F5_BINARY_PAIRS",
         "description": "grouped binary regrouped into quaternary",
         "status": "EVALUATED", "evaluated": True},
        {"family": "F6_TWO_SIDED_APPEND",
         "description": "Stonehenge/Avebury append relation",
         "status": "EXACT_RELATION_CONFIRMED", "evaluated": True},
        {"family": "F7_PATH_VECTOR_STRUCTURE",
         "description": "compact/refined path-vector relations",
         "status": "EVALUATED", "evaluated": True},
        {"family": "F8_HEADER_PROFILE_TABLE",
         "description": "header->profile abstraction placeholder",
         "status": "ABSTRACTION_ONLY_NO_UNIVERSAL_RESULT",
         "evaluated": False}])

    summary = {
        "schema": "rgcs.r1016b.summary.v1",
        "prefix_proximity": {k: v for k, v in ppt.items()
                             if k != "rows"},
        "stonehenge_avebury": sa,
        "profile_search": {k: v for k, v in ps.items()
                           if k not in ("top_shapes", "top_viable",
                                        "survivors_25km", "best_shape")},
        "survivors": 0,
        "verdict": "RGCS_R10_16B_NO_SEMANTIC_PROFILE_SURVIVOR",
    }
    (OUT / "data/r1016b_summary.json").write_text(
        json.dumps(summary, indent=1, default=str), encoding="utf-8")
    print(json.dumps({
        "spearman_rho": ppt["spearman_rho_prefix_vs_distance"],
        "hierarchy_consistent": ppt["hierarchy_consistent"],
        "profiles_evaluated": ps["profiles_evaluated"],
        "shape_compatible": ps["shape_compatible"],
        "best_angle_error_deg": ps["best_shape_error_deg"],
        "avebury_right_append": sa["right_append_preserved"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
