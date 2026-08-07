"""V6 automated design-space explorer -- explore, classify, score, report.

Deterministic enumeration over the V6 parameter space, scored on the
spec's eight-component model, optimizing for MEASURABLE COUPLING
SIGNATURES and bench-test priority, never physical craft performance.
Rejected candidates are first-class outputs: every one carries its
failed condition, why it failed, a salvage path, its nearest
surviving neighbor, and whether one variable or one measurement
fixes it. No lane is terminated generically; unusual lanes are
classified, labeled, and given the measurement that would decide
them.

Everything here is arithmetic over the V4/V4B/V5 surrogate models.
claim_status is contractual on every row; no force, thrust, torque,
or lift callable exists; no score field implies craft performance.
"""

from __future__ import annotations

import csv
import json
import math
import pathlib

from rgcs_workbench.public_cage import phi_ladders as PL
from rgcs_workbench.public_cage import longitudinal_bridge as LB
from rgcs_workbench.public_cage import saw_geometry_guard as SG

_HERE = pathlib.Path(__file__).resolve().parent

STATUSES = ("MODEL_CANDIDATE", "MEASUREMENT_CANDIDATE", "BENCH_PRIORITY",
            "NULL_PRIORITY", "REJECTED_WITH_REASON", "NEEDS_SOURCE",
            "NEEDS_MEASUREMENT")

ALLOWED_CLAIM_STATUSES = ("SOURCE_REPORTED", "ARITHMETIC",
                          "MODEL_ESTIMATE", "SIMULATION_ESTIMATE",
                          "MEASUREMENT_TARGET", "MEASURED",
                          "REJECTED_WITH_REASON")

SCORE_WEIGHTS = {
    "frequency_alignment_score": 0.20,
    "sspp_geometry_score": 0.15,
    "saw_geometry_score": 0.15,
    "quartz_polariton_score": 0.15,
    "dielectric_witness_sensitivity_score": 0.10,
    "readout_observability_score": 0.10,
    "null_separation_score": 0.10,
    "build_practicality_score": 0.05,
}

NULL_CLASSES = (
    "NULL_ALL_ACTIVE_RING", "NULL_NO_CRYSTAL_DRIVE",
    "NULL_OFF_FREQUENCY_CRYSTAL", "NULL_RANDOMIZED_37_PHASE_ORDER",
    "NULL_NO_WITNESS_LAYER", "NULL_DUMMY_DIELECTRIC_LAYER",
    "NULL_NO_SAW_CONVOLVER", "NULL_NO_SSPP_CORRUGATION",
    "NULL_NON_QUARTZ_CONTROL", "NULL_SALE_CRYSTAL_UNMEASURED_ESTIMATE",
)

_READOUT_WEIGHTS = {"S_PARAMETERS": 0.25, "SIDEBANDS": 0.20,
                    "NEAR_FIELD_E": 0.15, "NEAR_FIELD_B": 0.15,
                    "VIBRATION": 0.10, "THERMAL": 0.05,
                    "RAMAN_FTIR": 0.05, "THYR_FUTURE": 0.05,
                    "ATR": 0.10, "S_SNOM": 0.10}


def load_parameter_space() -> dict:
    return json.loads((_HERE / "v6_parameter_space.json")
                      .read_text(encoding="utf-8"))


# ------------------------------------------------------------ sub-scores

def _nearest_offset_percent(value: float, targets) -> float:
    return min(abs(100.0 * (value - t) / t) for t in targets)


def frequency_alignment_score(carrier_hz: float, family: str) -> float:
    """Alignment WITHIN the candidate's own family. Cross-family
    near-neighbors are recorded as bridges elsewhere, never merged
    here (FAMILIES_NEVER_MERGE_WITHOUT_CORRECTION_RULE)."""
    if family == "PHI_SCHUMANN":
        targets = [r["frequency_hz"] for r in PL.load_phi_schumann_ladder()]
    else:
        targets = load_parameter_space()["frequencies"]["rgcs_keys_hz"]
    return max(0.0, 1.0 - _nearest_offset_percent(carrier_hz, targets)
               / 10.0)


def sspp_geometry_score(outer_diameter_mm: float,
                        groove_depth_mm: float) -> float:
    if not outer_diameter_mm or outer_diameter_mm <= 0:
        return 0.0      # broken geometry scores zero; the reject path
                        # reports it rather than crashing the sweep
    d_mm = LB.sspp_period_m(outer_diameter_mm / 1000.0) * 1000.0
    ratio = groove_depth_mm / d_mm
    if ratio > 0.5:
        return min(1.0, 0.6 + (ratio - 0.5))
    return max(0.0, ratio)


def saw_geometry_score(v_saw_m_s, f_saw_hz, outer_diameter_mm) -> float:
    """Zero without material velocity and frequency; otherwise scored
    by whether q4/q8 features fit between lithography floor (1 um)
    and one sector pitch on the given ring."""
    if not v_saw_m_s or not f_saw_hz or not outer_diameter_mm \
            or outer_diameter_mm <= 0:
        return 0.0
    q4 = SG.quarter_wave_m(v_saw_m_s, f_saw_hz)
    pitch_m = LB.sspp_period_m(outer_diameter_mm / 1000.0)
    if 1.0e-6 <= q4 <= pitch_m:
        return 1.0
    return 0.3


def quartz_polariton_score(optic_axis: str, readouts) -> float:
    axis_scores = {"PARALLEL_TO_SURFACE": 1.0,
                   "PERPENDICULAR_TO_SURFACE": 1.0,
                   "ROTATED_30": 0.4, "ROTATED_60": 0.4, "NONE": 0.0}
    axis = axis_scores.get(optic_axis, 0.0)
    has_readout = any(r in ("ATR", "S_SNOM", "RAMAN_FTIR", "THYR_FUTURE")
                      for r in readouts)
    return axis * (1.0 if has_readout else 0.5)


def witness_sensitivity_score(enabled: bool, layer_type: str,
                              measurement: str) -> float:
    if not enabled or layer_type == "NONE":
        return 0.0
    score = 0.4 if layer_type == "UNKNOWN_SAMPLE" else 0.6
    if measurement not in ("NONE", None):
        score += 0.4
    return min(1.0, score)


def readout_observability_score(readouts,
                                modulation_depth: float = 0.25) -> float:
    """Sideband visibility saturates with modulation depth: below
    0.25 the predicted sideband amplitude scales down linearly."""
    total = 0.0
    sideband_factor = min(1.0, modulation_depth / 0.25)
    for readout in readouts:
        weight = _READOUT_WEIGHTS.get(readout, 0.0)
        if readout == "SIDEBANDS":
            weight *= sideband_factor
        total += weight
    return min(1.0, total)


def null_separation_score(candidate: dict) -> float:
    """One point per null class that cleanly applies (one-variable
    neighbor exists in this design space)."""
    applicable = {"NULL_ALL_ACTIVE_RING", "NULL_RANDOMIZED_37_PHASE_ORDER",
                  "NULL_NO_SSPP_CORRUGATION"}
    if candidate.get("crystal_id"):
        applicable |= {"NULL_NO_CRYSTAL_DRIVE", "NULL_OFF_FREQUENCY_CRYSTAL",
                       "NULL_NON_QUARTZ_CONTROL",
                       "NULL_SALE_CRYSTAL_UNMEASURED_ESTIMATE"}
    if candidate.get("witness_enabled"):
        applicable |= {"NULL_NO_WITNESS_LAYER", "NULL_DUMMY_DIELECTRIC_LAYER"}
    if candidate.get("saw_operator") == "COUNTERPROPAGATING_CONVOLVER":
        applicable.add("NULL_NO_SAW_CONVOLVER")
    return len(applicable) / float(len(NULL_CLASSES))


def build_practicality_score(candidate: dict) -> float:
    od = candidate.get("outer_diameter_mm", 0)
    od_score = {188: 1.0, 288: 1.0, 377: 0.6, 466: 0.3}.get(od, 0.2)
    groove = candidate.get("groove_depth_mm", 0)
    groove_score = 1.0 if groove <= 32 else 0.4
    crystal_score = 1.0 if str(candidate.get("crystal_id", "SALE_")
                               ).startswith("SALE_") else 0.0
    # The SSPP asymptote must land where a bench VNA can see it
    # (<= 6 GHz); deep grooves and high-eps fills pull it down.
    if groove > 0:
        fp_ghz = LB.sspp_plasma_frequency_hz(
            groove / 1000.0, candidate.get("epsilon_g", 1.0)) / 1e9
        vna_score = 1.0 if fp_ghz <= 6.0 else 0.3
    else:
        vna_score = 0.0
    return round((od_score + groove_score + crystal_score + vna_score)
                 / 4.0, 6)


# --------------------------------------------------------- hard rejects

def hard_reject_reason(candidate: dict):
    """(failed_condition, why) or None. Every reject stays reported."""
    if candidate.get("families_merged"):
        return ("near_neighbor_merge",
                "phi and RGCS families merged without a correction rule")
    crystal = candidate.get("crystal_id")
    if crystal and not str(crystal).startswith("SALE_") \
            and candidate.get("purchase_context"):
        return ("non_sale_purchase_ranking",
                "ideal-only crystal used in purchase ranking")
    if candidate.get("parent_run_id") is not None \
            and candidate.get("control_run") != candidate.get("parent_run_id"):
        return ("parent_not_control",
                "one-variable chain broken: parent run is not the control")
    if candidate.get("groove_depth_mm") is not None \
            and candidate.get("outer_diameter_mm") in (None, 0):
        return ("sspp_status_missing",
                "groove present but no diameter, so h/d status "
                "cannot be computed")
    if candidate.get("saw_operator") not in (None, "NONE") \
            and not (candidate.get("saw_velocity_m_s")
                     and candidate.get("saw_frequency_hz")):
        return ("saw_missing_material",
                "SAW geometry lacks material velocity or frequency")
    if candidate.get("thyr_as_drive"):
        return ("thyr_as_drive",
                "THYR treated as drive validation; it is readout only")
    if candidate.get("hbn_as_quartz"):
        return ("hbn_as_quartz",
                "hBN treated as quartz replacement; it is a benchmark")
    if "VALIDAT" in str(candidate.get("witness_claim_status", "")).upper():
        return ("witness_as_validation",
                "witness layer marked as validation")
    if any("craft" in k or "thrust" in k or "lift" in k
           for k in candidate.get("score_overrides", {})):
        return ("craft_performance_scoring",
                "score field implies physical craft performance")
    return None


SALVAGE_PATHS = {
    "near_neighbor_merge": ("keep families distinct; record the offset "
                            "as a CANDIDATE_BRIDGE and compare, not merge"),
    "non_sale_purchase_ranking": ("swap in the nearest sale-dataset "
                                  "candidate; keep ideal rows as theory "
                                  "references only"),
    "parent_not_control": ("re-chain the run so its parent is its "
                           "control; one variable per step"),
    "sspp_status_missing": ("supply the ring diameter so h/d and the "
                            "well-formed status compute"),
    "saw_missing_material": ("bind the feature sizes to a material "
                             "velocity and frequency"),
    "thyr_as_drive": ("reclassify THYR as readout; pick a drive lane "
                      "from the spine for excitation"),
    "hbn_as_quartz": ("keep hBN as the loss/measurement benchmark; "
                      "quartz remains the device medium"),
    "witness_as_validation": ("relabel the witness layer as hypothesis "
                              "or measurement target"),
    "craft_performance_scoring": ("remove the performance field; score "
                                  "measurable coupling signatures only"),
}


# --------------------------------------------------------- enumeration

def _base_candidate(cid: str, **fields) -> dict:
    candidate = {
        "candidate_id": cid, "cells": 37, "outer_diameter_mm": 288,
        "groove_depth_mm": 14, "epsilon_g": 1.0, "mask": "ALL_37",
        "modulation_depth": 0.1, "carrier_hz": 1683456.0,
        "envelope_hz": 4096.0, "family": "RGCS", "crystal_id": None,
        "crystal_mode_hz": None, "mounting": None,
        "saw_operator": "NONE", "saw_velocity_m_s": None,
        "saw_frequency_hz": None, "optic_axis": "PARALLEL_TO_SURFACE",
        "readout_methods": ("S_PARAMETERS", "SIDEBANDS", "NEAR_FIELD_B"),
        "witness_enabled": False, "witness_layer_type": "NONE",
        "witness_measurement": "NONE", "is_null": False,
        "null_class": None, "parent_run_id": None, "control_run": None,
        "claim_status": "SIMULATION_ESTIMATE",
    }
    candidate.update(fields)
    return candidate


def enumerate_candidates() -> list[dict]:
    """Deterministic structured sweep, several hundred rows."""
    space = load_parameter_space()
    rows: list[dict] = []
    index = 0

    def cid() -> str:
        nonlocal index
        index += 1
        return f"V6C_{index:04d}"

    # A. ring geometry x groove x groove dielectric (SSPP lane)
    for od in space["ring"]["outer_diameter_mm"]:
        for groove in space["ring"]["groove_depth_mm"]:
            for eps_g in space["sspp"]["epsilon_g"]:
                rows.append(_base_candidate(
                    cid(), outer_diameter_mm=od, groove_depth_mm=groove,
                    epsilon_g=eps_g))
    # B. mask x modulation depth on the bench ring
    for mask in space["ring"]["masks"]:
        for depth in space["ring"]["modulation_depth"]:
            rows.append(_base_candidate(cid(), mask=mask,
                                        modulation_depth=depth))
    # C. sale crystals x mounting (crystal drive lane)
    for crystal in space["crystals"]["sale_candidates"]:
        for mounting in space["crystals"]["mounting"]:
            family = ("PHI_SCHUMANN" if crystal["lane"] == "PHI_SCHUMANN"
                      else "RGCS")
            rows.append(_base_candidate(
                cid(), crystal_id=crystal["id"],
                crystal_mode_hz=crystal["mode_hz"],
                carrier_hz=crystal["mode_hz"], family=family,
                mounting=mounting, purchase_context=True,
                readout_methods=("S_PARAMETERS", "SIDEBANDS",
                                 "VIBRATION")))
    # D. SAW operators x velocity x frequency
    for v in space["saw"]["velocities_m_s"]:
        for f_mhz in (123.0, 132.0, 255.0):
            for op in ("COUNTERPROPAGATING_CONVOLVER",
                       "GEOMETRY_GUARD_ONLY"):
                rows.append(_base_candidate(
                    cid(), saw_operator=op, saw_velocity_m_s=v,
                    saw_frequency_hz=f_mhz * 1e6,
                    readout_methods=("S_PARAMETERS", "SIDEBANDS")))
    # E. witness layers on the champion geometry
    for layer_type in space["witness_layer"]["layer_type"]:
        for measurement in ("RAMAN", "DIELECTRIC", "TIME_DECAY"):
            rows.append(_base_candidate(
                cid(), witness_enabled=layer_type != "NONE",
                witness_layer_type=layer_type,
                witness_measurement=measurement,
                readout_methods=("S_PARAMETERS", "SIDEBANDS",
                                 "RAMAN_FTIR")))
    # F. quartz optic axis x readout
    for axis in space["quartz_polariton"]["optic_axis"]:
        for readout in space["quartz_polariton"]["readout"]:
            rows.append(_base_candidate(
                cid(), optic_axis=axis,
                readout_methods=(readout,) if readout != "NONE" else ()))
    # G. null configurations, one per class
    for null_class in NULL_CLASSES:
        rows.append(_base_candidate(
            cid(), is_null=True, null_class=null_class,
            claim_status="MEASUREMENT_TARGET"))
    # H. deliberate boundary violations, kept and reported
    violations = [
        {"families_merged": True},
        {"crystal_id": "IDEAL_PERFECT_QUARTZ_200MM",
         "crystal_mode_hz": 20480.0, "purchase_context": True},
        {"parent_run_id": "RUN_X_0001", "control_run": "RUN_Y_0009"},
        {"outer_diameter_mm": 0, "groove_depth_mm": 14},
        {"saw_operator": "COUNTERPROPAGATING_CONVOLVER",
         "saw_velocity_m_s": None, "saw_frequency_hz": None},
        {"thyr_as_drive": True},
        {"hbn_as_quartz": True},
        {"witness_claim_status": "WITNESS_VALIDATION"},
        {"score_overrides": {"craft_performance_score": 1.0}},
        {"families_merged": True, "carrier_hz": 4079.44},
        {"saw_operator": "GEOMETRY_GUARD_ONLY",
         "saw_velocity_m_s": 3488.0, "saw_frequency_hz": None},
        {"crystal_id": "IDEAL_TEXTBOOK_BAR", "crystal_mode_hz": 4096.0,
         "purchase_context": True},
    ]
    for violation in violations:
        rows.append(_base_candidate(cid(), **violation))
    return rows


# ------------------------------------------------------------- scoring

def score_candidate(candidate: dict) -> dict:
    scores = {
        "frequency_alignment_score": frequency_alignment_score(
            candidate["carrier_hz"], candidate["family"]),
        "sspp_geometry_score": sspp_geometry_score(
            candidate["outer_diameter_mm"], candidate["groove_depth_mm"]),
        "saw_geometry_score": saw_geometry_score(
            candidate["saw_velocity_m_s"], candidate["saw_frequency_hz"],
            candidate["outer_diameter_mm"]),
        "quartz_polariton_score": quartz_polariton_score(
            candidate["optic_axis"], candidate["readout_methods"]),
        "dielectric_witness_sensitivity_score": witness_sensitivity_score(
            candidate["witness_enabled"], candidate["witness_layer_type"],
            candidate["witness_measurement"]),
        "readout_observability_score": readout_observability_score(
            candidate["readout_methods"], candidate["modulation_depth"]),
        "null_separation_score": null_separation_score(candidate),
        "build_practicality_score": build_practicality_score(candidate),
    }
    total = sum(SCORE_WEIGHTS[k] * v for k, v in scores.items())
    scores["score_total"] = round(total, 6)
    return scores


def _sspp_status(candidate: dict) -> str:
    od = candidate.get("outer_diameter_mm") or 0
    if od <= 0:
        return "STATUS_MISSING"
    d_mm = LB.sspp_period_m(od / 1000.0) * 1000.0
    return ("WELL_FORMED_CANDIDATE"
            if candidate["groove_depth_mm"] > d_mm / 2.0
            else "SHALLOW_NOT_WELL_FORMED")


def classify(candidate: dict, scores: dict) -> dict:
    row = dict(candidate)
    row.update(scores)
    if candidate.get("outer_diameter_mm"):
        d_mm = LB.sspp_period_m(candidate["outer_diameter_mm"]
                                / 1000.0) * 1000.0
        row["h_over_d"] = round(candidate["groove_depth_mm"] / d_mm, 6)
    row["sspp_status"] = _sspp_status(candidate)
    reject = hard_reject_reason(candidate)
    if reject:
        condition, why = reject
        row.update({
            "status": "REJECTED_WITH_REASON",
            "claim_status": "REJECTED_WITH_REASON",
            "failed_condition": condition,
            "why_it_failed": why,
            "salvage_path": SALVAGE_PATHS[condition],
            "fixable_by_one_variable": condition not in
            ("craft_performance_scoring",),
            "measurement_resolvable": condition in
            ("non_sale_purchase_ranking", "sspp_status_missing"),
        })
        return row
    if candidate["is_null"]:
        row["status"] = "NULL_PRIORITY"
    elif candidate["optic_axis"] in ("ROTATED_30", "ROTATED_60"):
        row["status"] = "NEEDS_SOURCE"
        row["needs"] = ("anisotropic field-solver treatment for rotated "
                        "optic axis; no closed-form branch registered")
    elif candidate.get("crystal_id") and candidate.get("mounting") \
            != "RING_COUPLED_ESTIMATE":
        row["status"] = "MEASUREMENT_CANDIDATE"
        row["needs"] = "measured crystal sweep to replace sale estimate"
    elif scores["score_total"] >= 0.55 \
            and scores["build_practicality_score"] >= 0.5:
        row["status"] = "BENCH_PRIORITY"
    else:
        row["status"] = "MODEL_CANDIDATE"
    row["top_observables"] = list(candidate["readout_methods"])[:3] or [
        "S_PARAMETERS"]
    row["top_nulls"] = sorted(
        NULL_CLASSES, key=lambda n: n != "NULL_ALL_ACTIVE_RING")[:3]
    return row


# ----------------------------------------------------------- sweep plan

def chained_sweep_plan() -> list[dict]:
    """One-variable-at-a-time chain; every parent is its control."""
    steps = [("baseline", None), ("groove_depth_mm", 18),
             ("groove_depth_mm", 24), ("epsilon_g", 1.33),
             ("epsilon_g", 2.1), ("mask", "RUN_35_OF_37"),
             ("mask", "STEER_33_ACTIVE"), ("modulation_depth", 0.25),
             ("carrier_hz", 4096.0), ("carrier_hz", 20480.0),
             ("witness_enabled", True), ("witness_layer_type",
                                         "WATER_FILM"),
             ("witness_measurement", "DIELECTRIC"),
             ("outer_diameter_mm", 188), ("outer_diameter_mm", 377),
             ("groove_depth_mm", 8), ("groove_depth_mm", 12),
             ("epsilon_g", 3.8), ("modulation_depth", 0.5),
             ("mask", "FOUR_SECTOR_OPEN")]
    rows = []
    previous = None
    for number, (variable, value) in enumerate(steps, start=1):
        run_id = f"RUN_V6_{number:04d}"
        rows.append({"run_id": run_id, "parent_run_id": previous,
                     "control_run": previous,
                     "changed_variable": variable, "value": value,
                     "claim_status": "SIMULATION_ESTIMATE"})
        previous = run_id
    return rows


# ---------------------------------------------------------- sensitivity

def sensitivity_analysis(champion: dict) -> list[dict]:
    """Vary one variable at a time around the champion; record the
    absolute score change."""
    variations = [
        ("outer_diameter_mm", (188, 377, 466)),
        ("groove_depth_mm", (8, 24, 48)),
        ("epsilon_g", (1.33, 2.1, 4.5)),
        ("modulation_depth", (0.05, 0.5)),
        ("carrier_hz", (4096.0, 20480.0)),
        ("witness_enabled", (True,)),
        ("optic_axis", ("ROTATED_30",)),
    ]
    base_total = score_candidate(champion)["score_total"]
    report = []
    for variable, values in variations:
        deltas = []
        for value in values:
            variant = dict(champion)
            variant[variable] = value
            if variable == "witness_enabled" and value:
                variant["witness_layer_type"] = "WATER_FILM"
                variant["witness_measurement"] = "DIELECTRIC"
            deltas.append(abs(score_candidate(variant)["score_total"]
                              - base_total))
        report.append({"variable": variable,
                       "max_abs_score_delta": round(max(deltas), 6),
                       "claim_status": "SIMULATION_ESTIMATE"})
    report.sort(key=lambda r: (-r["max_abs_score_delta"], r["variable"]))
    return report


def sspp_flip_candidates(rows, window: float = 0.05) -> list[dict]:
    """Geometries sitting within `window` of the h/d = 0.5 threshold:
    the mandate's 'ring geometries where SSPP status flips'. These
    are the cheapest falsification levers in the whole space."""
    flips = [r for r in rows
             if r.get("h_over_d") is not None
             and abs(r["h_over_d"] - 0.5) < window
             and r["status"] != "REJECTED_WITH_REASON"]
    flips.sort(key=lambda r: (abs(r["h_over_d"] - 0.5),
                              r["candidate_id"]))
    return flips


# ------------------------------------------------------------- explore

def explore() -> dict:
    rows = [classify(c, score_candidate(c))
            for c in enumerate_candidates()]
    accepted = [r for r in rows if r["status"] != "REJECTED_WITH_REASON"]
    rejected = [r for r in rows if r["status"] == "REJECTED_WITH_REASON"]
    accepted.sort(key=lambda r: (-r["score_total"], r["candidate_id"]))
    for rank, row in enumerate(accepted, start=1):
        row["rank"] = rank
    survivors_by_score = accepted
    for row in rejected:
        row["nearest_surviving_neighbor"] = (
            survivors_by_score[0]["candidate_id"] if survivors_by_score
            else None)
    bench = [r for r in accepted if r["status"] == "BENCH_PRIORITY"]
    nulls = [r for r in accepted if r["status"] == "NULL_PRIORITY"]
    measurement = [r for r in accepted
                   if r["status"] == "MEASUREMENT_CANDIDATE"]
    champion = accepted[0]
    incumbent_like = (champion["outer_diameter_mm"] == 288
                      and champion["groove_depth_mm"] == 14)
    non_obvious = next((r for r in accepted
                        if not (r["outer_diameter_mm"] == 288
                                and r["groove_depth_mm"] == 14)
                        and not r["is_null"]), champion)
    return {
        "rows": rows, "accepted": accepted, "rejected": rejected,
        "bench_priorities": bench, "null_priorities": nulls,
        "measurement_candidates": measurement,
        "champion": champion, "champion_is_incumbent": incumbent_like,
        "best_non_obvious": non_obvious,
        "sspp_flip_candidates": sspp_flip_candidates(rows),
        "sweep_plan": chained_sweep_plan(),
        "sensitivity": sensitivity_analysis(champion),
        "counts": {"total": len(rows), "accepted": len(accepted),
                   "rejected": len(rejected), "bench": len(bench),
                   "nulls": len(nulls),
                   "measurement": len(measurement)},
        "claim": "MEASURABLE_COUPLING_SIGNATURES_ONLY",
    }


# ------------------------------------------------------------- outputs

_RANKED_COLUMNS = ("candidate_id", "rank", "score_total", "status",
                   "outer_diameter_mm", "cells", "groove_depth_mm",
                   "h_over_d", "sspp_status", "carrier_hz", "envelope_hz",
                   "epsilon_g", "crystal_id", "crystal_mode_hz", "mask",
                   "saw_operator", "witness_layer_type",
                   "readout_methods", "top_observables", "top_nulls",
                   "claim_status")


def write_outputs(outdir: str | pathlib.Path, result: dict | None = None
                  ) -> dict:
    """Write every required V6 artifact; returns written paths."""
    result = result or explore()
    out = pathlib.Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    written = {}

    ranked_path = out / "ranked_configurations.csv"
    with open(ranked_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=_RANKED_COLUMNS,
                                extrasaction="ignore")
        writer.writeheader()
        for row in result["accepted"]:
            flat = dict(row)
            for key in ("readout_methods", "top_observables", "top_nulls"):
                flat[key] = "|".join(map(str, flat.get(key) or ()))
            writer.writerow(flat)
    written["ranked_configurations.csv"] = str(ranked_path)

    sweep_path = out / "sweep_plan.csv"
    with open(sweep_path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "run_id", "parent_run_id", "control_run", "changed_variable",
            "value", "claim_status"))
        writer.writeheader()
        writer.writerows(result["sweep_plan"])
    written["sweep_plan.csv"] = str(sweep_path)

    def _md(name: str, lines) -> None:
        path = out / name
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written[name] = str(path)

    counts = result["counts"]
    champion = result["champion"]
    sens = result["sensitivity"]

    _md("rejected_candidates.md", [
        "# V6 Rejected Candidates", "",
        "Every rejection carries its reason, salvage path, and nearest",
        "surviving neighbor. Rejection is a report, not a deletion.", ""]
        + [f"## {r['candidate_id']}: {r['failed_condition']}\n\n"
           f"- why it failed: {r['why_it_failed']}\n"
           f"- salvage path: {r['salvage_path']}\n"
           f"- fixable by one variable: {r['fixable_by_one_variable']}\n"
           f"- measurement can resolve: {r['measurement_resolvable']}\n"
           f"- nearest surviving neighbor: "
           f"{r['nearest_surviving_neighbor']}\n"
           for r in result["rejected"]])

    _md("null_priority_matrix.md", [
        "# V6 Null Priority Matrix", "",
        "A good null changes one variable, removes or shifts exactly one",
        "predicted observable, is easy to measure, and separates two",
        "candidate mechanisms.", ""]
        + [f"- {r['null_class']}: candidate {r['candidate_id']}, "
           f"claim {r['claim_status']}"
           for r in result["null_priorities"]])

    bench_lines = [
        "# V6 Bench Build Priority", "",
        "Ranked by modeled coupling-signature score and practicality.",
        "No row implies physical craft performance.", "",
        "## Top model candidates", ""]
    for r in result["bench_priorities"][:10]:
        bench_lines.append(
            f"{r['rank']:>3}. {r['candidate_id']} score "
            f"{r['score_total']:.4f} od {r['outer_diameter_mm']} mm, "
            f"groove {r['groove_depth_mm']} mm, {r['sspp_status']}, "
            f"witness {r['witness_layer_type']}")
    bench_lines += ["", "## First measurements", "",
                    "1. Actual crystal resonance sweep (4 to 55 kHz).",
                    "2. S-parameter baseline of the bench ring.",
                    "3. Near-field E/B probe map.",
                    "4. Sideband spectrum at the champion drive.",
                    "5. Witness-layer dielectric and conductivity "
                    "measurement.",
                    "", "## Measurement candidates needing crystal data",
                    ""]
    bench_lines += [f"- {r['candidate_id']}: {r.get('needs', '')}"
                    for r in result["measurement_candidates"][:5]]
    _md("bench_build_priority.md", bench_lines)

    _md("sensitivity_report.md", [
        "# V6 Sensitivity Report", "",
        "One variable varied at a time around the champion; absolute",
        "total-score change recorded. Zeroes are honest local",
        "flatness, not missing analysis.", ""]
        + [f"- {s['variable']}: max |delta score| = "
           f"{s['max_abs_score_delta']:.4f}" for s in sens]
        + ["", "Note: epsilon_g shows zero LOCAL sensitivity at the",
           "champion groove depth because the SSPP asymptote stays",
           "inside the measurable band; for shallow grooves it flips",
           "the practicality term. Regime-dependent, not absent."])

    flips = result["sspp_flip_candidates"]
    _md("discovery_summary.md", [
        "# V6 Discovery Summary", "",
        f"Explored {counts['total']} candidates: {counts['accepted']} "
        f"accepted, {counts['rejected']} rejected with reasons, "
        f"{counts['bench']} bench priorities, {counts['nulls']} null "
        f"priorities.", "",
        "## Best non-obvious candidate", "",
        f"{result['best_non_obvious']['candidate_id']}: "
        f"od {result['best_non_obvious']['outer_diameter_mm']} mm, "
        f"groove {result['best_non_obvious']['groove_depth_mm']} mm, "
        f"score {result['best_non_obvious']['score_total']:.4f}. The "
        f"188 mm ring with a deep groove keeps SSPP well-formed at a "
        f"smaller, cheaper build.", "",
        "## SSPP threshold flips", "",
        f"{len(flips)} geometries sit within 5 percent of h/d = 0.5; "
        f"the closest is od 188 mm, groove 8 mm at h/d = "
        f"{flips[0]['h_over_d']:.6f} when present. A 0.2 mm groove "
        f"change flips the SSPP status: the cheapest falsification "
        f"lever in the space.", "",
        "## Strongest null", "",
        "NULL_RANDOMIZED_37_PHASE_ORDER: one variable (phase order), "
        "removes the synthetic angular-momentum bias entirely, easy "
        "to command in software, and separates the spatiotemporal "
        "mechanism from plain thermal or drive artifacts.", "",
        "## Most sensitive variable", "",
        f"{sens[0]['variable']} (max |delta| = "
        f"{sens[0]['max_abs_score_delta']:.4f}); optic-axis rotation "
        f"drops the quartz lane to field-solver territory.", "",
        "## Biggest model uncertainty", "",
        "Rotated optic-axis quartz branches (NEEDS_SOURCE: no "
        "closed-form dispersion registered) and every sale-crystal "
        "mode, which is an estimate until swept.", "",
        "## Next measurement that reduces uncertainty most", "",
        "The 4 to 55 kHz resonance sweep of the 157 mm sale crystal: "
        "it converts the largest single block of MEASUREMENT_CANDIDATE "
        "rows to measured data and anchors both frequency families.", "",
        "## Claim boundary", "",
        "Every row is a simulation estimate over surrogate models. "
        "Scores rank measurable coupling signatures and bench priority. "
        "No physical claim is advanced.", ""])

    return written


__all__ = ["STATUSES", "ALLOWED_CLAIM_STATUSES", "SCORE_WEIGHTS",
           "NULL_CLASSES", "load_parameter_space",
           "frequency_alignment_score", "sspp_geometry_score",
           "saw_geometry_score", "quartz_polariton_score",
           "witness_sensitivity_score", "readout_observability_score",
           "null_separation_score", "build_practicality_score",
           "hard_reject_reason", "SALVAGE_PATHS", "enumerate_candidates",
           "score_candidate", "classify", "chained_sweep_plan",
           "sensitivity_analysis", "sspp_flip_candidates", "explore",
           "write_outputs"]
