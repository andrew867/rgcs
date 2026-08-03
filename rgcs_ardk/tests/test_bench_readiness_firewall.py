from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from rgcs_ardk.bench import BenchVerdict, BenchVerdictRefused, evaluate_bench_result
from rgcs_ardk.reports.firewall import audit_executable_tree, validate_claim_text
from rgcs_ardk.reports.readiness import (
    FabricationEvidence,
    FabricationStatus,
    current_scaffold_evidence,
    evaluate_fabrication_readiness,
)
from rgcs_ardk.reports.release import audit_release_paths, publication_hold, require_public_paths


def test_pass_and_fail_are_both_reachable_with_complete_evidence(complete_result):
    assert evaluate_bench_result(complete_result) is BenchVerdict.PASS
    failed = copy.deepcopy(complete_result)
    failed["angle_tracks"] = False
    assert evaluate_bench_result(failed) is BenchVerdict.FAIL


@pytest.mark.parametrize("name", ["angular_deg", "amplitude_norm"])
def test_each_missing_uncertainty_raises(result_copy, name):
    result = result_copy()
    result["uncertainty"].pop(name)
    with pytest.raises(BenchVerdictRefused, match="uncertainty"):
        evaluate_bench_result(result)


@pytest.mark.parametrize(
    "name",
    [
        "all_active",
        "binary_best",
        "equal_resource_randomized",
        "reversed_lag",
        "rotated",
        "mirrored",
        "dummy_load",
    ],
)
def test_each_required_control_raises_when_missing(result_copy, name):
    result = result_copy()
    result["controls"].pop(name)
    with pytest.raises(BenchVerdictRefused, match="missing controls"):
        evaluate_bench_result(result)


def test_hashes_and_calibration_identifiers_are_structural(result_copy):
    result = result_copy()
    result["raw_data_hashes"] = []
    with pytest.raises(BenchVerdictRefused, match="raw data"):
        evaluate_bench_result(result)
    result = result_copy()
    result["instrument_calibration_ids"] = []
    with pytest.raises(BenchVerdictRefused, match="calibration"):
        evaluate_bench_result(result)


@pytest.mark.parametrize("primary", ["force", "thrust", "lift", "propulsion"])
def test_out_of_boundary_primary_observable_raises(result_copy, primary):
    result = result_copy()
    result["primary_observable"] = primary
    with pytest.raises(BenchVerdictRefused, match="forbidden"):
        evaluate_bench_result(result)


def test_result_language_cannot_infer_out_of_boundary_performance(result_copy):
    result = result_copy()
    result["claim_language"] = "propulsion confirmed by this run"
    with pytest.raises(BenchVerdictRefused, match="boundary"):
        evaluate_bench_result(result)
    with pytest.raises(ValueError, match="boundary"):
        validate_claim_text("thrust confirmed by this run")


def test_crystal_lane_requires_a_matching_control(result_copy):
    result = result_copy()
    result["crystal_lane_included"] = True
    with pytest.raises(BenchVerdictRefused, match="crystal"):
        evaluate_bench_result(result)
    result["controls"]["dummy_crystal"] = True
    assert evaluate_bench_result(result) is BenchVerdict.PASS


def test_run_receipt_schema_is_valid_draft_2020_12():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(Path("rgcs_ardk/bench/schemas/run_receipt_schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


def test_current_scaffold_fabrication_status_is_refused():
    report = evaluate_fabrication_readiness(current_scaffold_evidence())
    assert report.status is FabricationStatus.REFUSED
    assert "manufacturer stackup is not approved" in report.blockers
    assert "complete bench receipt is missing" in report.blockers


def _complete_fabrication_evidence(**changes) -> FabricationEvidence:
    values = {
        "authority_valid": True,
        "seed_used": False,
        "board_a_generated": True,
        "board_b_generated": True,
        "boards_separate": True,
        "deterministic_nets": True,
        "geometry_valid": True,
        "publication_hold": True,
        "manufacturer_stackup": "reviewed-stackup-id",
        "drc_board_a": True,
        "drc_board_b": True,
        "fabrication_hashes": {"archive": "a" * 64},
        "bom_reviewed": True,
        "assembly_drawing_reviewed": True,
        "pick_place_reviewed_if_populated": True,
        "safety_reviewed": True,
        "board_a_calibrated": True,
        "board_b_dummy_load_complete": True,
        "board_b_symmetric_control_complete": True,
    }
    values.update(changes)
    return FabricationEvidence(**values)


def test_readiness_pass_requires_complete_nonforbidden_receipt(complete_result):
    report = evaluate_fabrication_readiness(_complete_fabrication_evidence(), complete_result)
    assert report.status is FabricationStatus.PASS
    incomplete = copy.deepcopy(complete_result)
    incomplete.pop("uncertainty")
    with pytest.raises(BenchVerdictRefused, match="uncertainty"):
        evaluate_fabrication_readiness(_complete_fabrication_evidence(), incomplete)


def test_explicit_drc_failure_is_fail_not_missing_evidence(complete_result):
    report = evaluate_fabrication_readiness(
        _complete_fabrication_evidence(drc_board_a=False),
        complete_result,
    )
    assert report.status is FabricationStatus.FAIL


def test_executable_namespace_audit_is_clean():
    audit = audit_executable_tree()
    assert audit.files_scanned > 0
    assert audit.identifiers_scanned > 0
    assert audit.leaks == ()


def test_publication_hold_and_private_lane_filter_are_live():
    assert publication_hold() is True
    allowed = [
        "rgcs_ardk/geometry/kernel.py",
        "docs/proofs/r1074-annular-devkit/pcb_design_spec.md",
    ]
    assert require_public_paths(allowed) == tuple(sorted(allowed))
    audit = audit_release_paths(allowed + ["rgcs_ardk/private/message_ascii.txt"])
    assert audit.publication_hold is True
    assert audit.rejected_paths == ("rgcs_ardk/private/message_ascii.txt",)
