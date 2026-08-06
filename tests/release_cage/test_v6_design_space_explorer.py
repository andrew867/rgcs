"""V6 design-space explorer -- acceptance criteria as tests.

Ported from the pack's sample tests plus the V6 acceptance list:
at least 100 candidates, at least 10 reported rejections with
reasons and salvage paths, at least 10 bench priorities, chained
parent/control runs, no craft-performance scoring, and the nine
required output artifacts present and coherent.
"""

from __future__ import annotations

import csv
import math
import pathlib

import pytest

from rgcs_workbench.public_cage import claim_firewall as CF
from rgcs_workbench.public_cage import design_space_explorer as DX

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "docs" / "research" / "v6_explorer"


@pytest.fixture(scope="module")
def result():
    return DX.explore()


# --------------------------------------------------- pack sample tests

def test_288mm_period_matches_sector_pitch():
    d_mm = math.pi * 288 / 37
    assert 24.4 < d_mm < 24.5


def test_us3833867_source_sum_retained():
    assert 123 + 132 == 255


def test_score_does_not_use_craft_performance_fields():
    forbidden = {"lift_score", "thrust_score", "craft_performance_score"}
    assert set(DX.SCORE_WEIGHTS).isdisjoint(forbidden)
    assert abs(sum(DX.SCORE_WEIGHTS.values()) - 1.0) < 1e-12


# ------------------------------------------------- exploration volume

def test_at_least_100_candidates_explored(result):
    assert result["counts"]["total"] >= 100
    assert result["counts"]["total"] == len(result["rows"])


def test_every_row_carries_an_allowed_claim_status(result):
    for row in result["rows"]:
        assert row["claim_status"] in DX.ALLOWED_CLAIM_STATUSES, (
            row["candidate_id"], row["claim_status"])
        assert row["status"] in DX.STATUSES


def test_exploration_is_deterministic(result):
    again = DX.explore()
    assert [r["candidate_id"] for r in result["accepted"][:20]] == \
        [r["candidate_id"] for r in again["accepted"][:20]]
    assert result["champion"]["score_total"] == \
        again["champion"]["score_total"]


# --------------------------------------------------------- rejections

def test_at_least_10_rejections_each_with_reason_and_salvage(result):
    rejected = result["rejected"]
    assert len(rejected) >= 10
    for row in rejected:
        assert row["failed_condition"]
        assert row["why_it_failed"]
        assert row["salvage_path"]
        assert "nearest_surviving_neighbor" in row
        assert isinstance(row["fixable_by_one_variable"], bool)
        assert isinstance(row["measurement_resolvable"], bool)


def test_every_hard_reject_class_is_exercised(result):
    conditions = {r["failed_condition"] for r in result["rejected"]}
    assert conditions >= {"near_neighbor_merge",
                          "non_sale_purchase_ranking",
                          "parent_not_control", "sspp_status_missing",
                          "saw_missing_material", "thyr_as_drive",
                          "hbn_as_quartz", "witness_as_validation",
                          "craft_performance_scoring"}


# --------------------------------------------------- accepted classes

def test_at_least_10_bench_priorities(result):
    bench = result["bench_priorities"]
    assert len(bench) >= 10
    for row in bench:
        assert row["top_observables"]
        assert row["top_nulls"]
        assert row["build_practicality_score"] >= 0.5


def test_all_null_classes_ranked(result):
    classes = {r["null_class"] for r in result["null_priorities"]}
    assert classes == set(DX.NULL_CLASSES)


def test_rotated_optic_axis_needs_source_not_termination(result):
    needy = [r for r in result["accepted"] if r["status"] == "NEEDS_SOURCE"]
    assert needy, "rotated-axis lane must be classified, not dropped"
    for row in needy:
        assert "field-solver" in row["needs"]


def test_sspp_flip_candidates_found(result):
    flips = result["sspp_flip_candidates"]
    assert flips
    closest = flips[0]
    assert abs(closest["h_over_d"] - 0.5) < 0.01
    assert closest["outer_diameter_mm"] == 188
    assert closest["groove_depth_mm"] == 8


# ----------------------------------------------------- run discipline

def test_sweep_plan_chains_parent_as_control(result):
    plan = result["sweep_plan"]
    assert len(plan) >= 20
    assert plan[0]["parent_run_id"] is None
    for previous, row in zip(plan, plan[1:]):
        assert row["parent_run_id"] == previous["run_id"]
        assert row["control_run"] == row["parent_run_id"]
        assert row["claim_status"] == "SIMULATION_ESTIMATE"


def test_sensitivity_ranks_variables(result):
    sens = result["sensitivity"]
    deltas = [s["max_abs_score_delta"] for s in sens]
    assert deltas == sorted(deltas, reverse=True)
    assert sens[0]["max_abs_score_delta"] > 0


# ------------------------------------------------- generated artifacts

REQUIRED_OUTPUTS = ("parameter_space.json", "sweep_plan.csv",
                    "scoring_model.py", "ranked_configurations.csv",
                    "sensitivity_report.md", "null_priority_matrix.md",
                    "bench_build_priority.md", "rejected_candidates.md",
                    "discovery_summary.md")


def test_all_required_outputs_exist():
    for name in REQUIRED_OUTPUTS:
        assert (OUTDIR / name).is_file(), name


def test_ranked_csv_matches_a_fresh_exploration(result):
    with open(OUTDIR / "ranked_configurations.csv", encoding="utf-8",
              newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == len(result["accepted"])
    assert rows[0]["candidate_id"] == result["accepted"][0]["candidate_id"]
    assert rows[0]["claim_status"] == "SIMULATION_ESTIMATE"


def test_discovery_summary_covers_required_sections():
    text = (OUTDIR / "discovery_summary.md").read_text(encoding="utf-8")
    for heading in ("Best non-obvious candidate", "Strongest null",
                    "Most sensitive variable", "Biggest model uncertainty",
                    "Next measurement", "Claim boundary"):
        assert heading in text, heading


def test_generated_reports_scan_clean():
    targets = [OUTDIR / n for n in REQUIRED_OUTPUTS
               if n.endswith((".md", ".py"))]
    targets.append(ROOT / "rgcs_workbench" / "public_cage"
                   / "design_space_explorer.py")
    report = CF.firewall_report(CF.scan_paths(targets))
    assert report["clean"], report


def test_no_force_thrust_torque_or_lift_callables():
    import inspect
    for name, obj in inspect.getmembers(DX, callable):
        for banned in ("force", "thrust", "torque", "lift", "newton"):
            assert banned not in name.lower(), name
