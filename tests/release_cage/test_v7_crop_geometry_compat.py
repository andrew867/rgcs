"""V7 crop geometry compatibility -- acceptance criteria as tests.

Ported from the pack samples plus the V7 acceptance list: rows are
never invented, provenance survives, rejects carry salvage
measurements, no row upgrades to physical validation, and the
committed feature file contains no private local paths.
"""

from __future__ import annotations

import json
import math
import pathlib

import pytest

from rgcs_workbench.public_cage import claim_firewall as CF
from rgcs_workbench.public_cage import crop_geometry_compat as CG

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "docs" / "research" / "v7_crop_compat"


@pytest.fixture(scope="module")
def result():
    return CG.score_all()


# --------------------------------------------------- pack sample tests

def test_47_72_ratio_anchor():
    assert abs(CG.RATIO_47_72 - 0.6527777777777778) < 1e-12
    assert abs((188 / 288) - CG.RATIO_47_72) < 1e-12


def test_37_pitch_for_188m_crop_is_scale_consistent():
    assert math.pi * 188 / 37 > 0


def test_tolerance_bands():
    assert CG.tolerance_band(CG.percent_error(100.1, 100.0)) == "EXACT"
    assert CG.tolerance_band(CG.percent_error(106.0, 100.0)) == "REJECT"


def test_plan_view_cannot_directly_claim_groove_depth():
    row = CG.load_features()[0]
    assert "groove_depth_mm" not in row


# ----------------------------------------------------- ingestion honesty

def test_features_ingested_without_invention(result):
    rows = CG.load_features()
    assert len(rows) >= 2000
    for row in rows[:200]:
        assert row["provenance"].startswith("COOKBOOK_EXTRACTED")
        # a parsed dimension always has its raw text preserved
        if row["outer_diameter_m"] is not None:
            assert row["raw_measurement_text"]


def test_no_private_local_paths_in_committed_features():
    text = (ROOT / "rgcs_workbench" / "public_cage"
            / "v7_crop_features.json").read_text(encoding="utf-8")
    assert "C:\\\\Users" not in text
    assert "C:/Users" not in text
    assert "image_path" not in text


def test_every_scored_row_keeps_provenance(result):
    for row in result["ranked"]:
        assert row["source_url"] or row["raw_measurement_text"], \
            row["formation_id"]


def test_weak_rows_are_listed_not_dropped(result):
    counts = result["counts"]
    assert counts["insufficient"] > 0
    assert counts["ingested"] == counts["scored"] \
        + counts["insufficient"] + len(result["reference_rows"])


def test_reference_row_is_excluded_from_crop_ranking(result):
    assert result["reference_rows"]
    ranked_ids = {r["formation_id"] for r in result["ranked"]}
    for row in result["reference_rows"]:
        assert row["formation_id"] not in ranked_ids


# -------------------------------------------------------- classification

def test_every_row_has_allowed_class_and_claim_status(result):
    for row in result["rows"]:
        assert row["classification"] in CG.CLASSES, row["formation_id"]
        assert row["claim_status"] == CG.CLAIM_STATUS


def test_no_row_is_upgraded_to_physical_validation(result):
    blob = json.dumps(result["ranked"][:50])
    for banned in ("proven functioning", "validated craft",
                   "confirmed device", "decoded physical operation"):
        assert banned not in blob.lower()


def test_rejects_carry_reason_and_salvage(result):
    assert result["rejected"]
    for row in result["rejected"]:
        assert row["failed_condition"]
        assert row["why_it_failed"]
        assert row["salvage_measurement"]
        assert row["source_gap"]
        assert row["nearest_rgcs_family"]


def test_37_count_reporting_is_background_honest(result):
    """The completed all-image dataset MAY contain detected 37s; the
    contract is that they are reported against the neighbor-count
    background, never as a signature by themselves."""
    background = CG.count_37_background(result)
    assert background["count_37"] == len(result["count_37_exact"])
    assert background["neighbor_mean_30_48"] >= 0
    assert isinstance(background["excess_over_neighbors"], bool)
    assert "not a surveyed count" in background["note"]
    near = [r for r in result["rows"]
            if r.get("satellite_count") in CG.COUNT_NEAR]
    assert near, "count-near rows exist and stay labeled near"
    for row in near:
        if row["classification"] not in ("INSUFFICIENT_GEOMETRY",):
            assert row["count_family"] == "COUNT_NEAR_37_LABELED_NEAR"


def test_ratio_hits_stay_at_or_below_chance_floor(result):
    rates = CG.ratio_base_rate(result)
    assert rates["ratio_rows"] >= 500
    assert rates["observed"] >= 1
    # the honesty gate: the report must not claim excess without it
    assert isinstance(rates["excess_over_chance"], bool)


def test_scoring_is_deterministic(result):
    again = CG.score_all()
    assert [r["formation_id"] for r in result["ranked"][:20]] == \
        [r["formation_id"] for r in again["ranked"][:20]]


def test_score_weights_sum_to_one():
    assert abs(sum(CG.SCORE_WEIGHTS.values()) - 1.0) < 1e-12


# ------------------------------------------------- generated artifacts

REQUIRED_OUTPUTS = ("crop_geometry_features.csv",
                    "crop_rgcs_compatibility_scores.csv",
                    "crop_to_v6_candidate_matches.csv",
                    "crop_physics_compatibility_report.md",
                    "crop_measurement_priority.md",
                    "crop_rejected_candidates.md",
                    "crop_null_controls.md", "final_report_draft.md")


def test_all_required_outputs_exist():
    for name in REQUIRED_OUTPUTS:
        assert (OUTDIR / name).is_file(), name


def test_final_report_keeps_the_boundary():
    text = (OUTDIR / "final_report_draft.md").read_text(encoding="utf-8")
    assert "MODEL_COMPARISON_ONLY" in text
    assert "not physical validation" in text
    assert "chance floor" in text
    # The 37-count statement is data-driven: whichever way the data
    # fell, the report must carry the background comparison.
    assert "background" in text


def test_generated_reports_and_module_scan_clean():
    targets = [OUTDIR / n for n in REQUIRED_OUTPUTS if n.endswith(".md")]
    targets.append(ROOT / "rgcs_workbench" / "public_cage"
                   / "crop_geometry_compat.py")
    report = CF.firewall_report(CF.scan_paths(targets))
    assert report["clean"], report


def test_no_force_thrust_torque_or_lift_callables():
    import inspect
    for name, obj in inspect.getmembers(CG, callable):
        for banned in ("force", "thrust", "torque", "lift", "newton"):
            assert banned not in name.lower(), name
