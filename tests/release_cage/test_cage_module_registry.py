"""Public module registry -- eight modules, exact statuses, real paths."""

from __future__ import annotations

import pathlib

from rgcs_workbench.public_cage import registry as REG

ROOT = pathlib.Path(__file__).resolve().parents[2]


def test_registry_is_structurally_valid_against_the_live_tree():
    problems = REG.validate_module_registry(repo_root=ROOT)
    assert problems == [], problems


def test_all_eight_modules_present_with_exact_statuses():
    reg = REG.load_module_registry()
    by_id = {m["id"]: m for m in reg["modules"]}
    assert sorted(by_id) == sorted(REG.EXPECTED_MODULE_IDS)
    for mod_id, status in REG.EXPECTED_STATUSES.items():
        assert by_id[mod_id]["status"] == status


def test_every_boundary_sentence_uses_the_required_shape():
    """This module does X. It does not claim Y. Z remains pending."""
    for mod in REG.load_module_registry()["modules"]:
        b = mod["boundary"]
        assert b.startswith("This module does "), mod["id"]
        assert "It does not claim " in b, mod["id"]


def test_hard_boundaries_include_the_two_non_negotiables():
    hb = REG.load_module_registry()["hard_boundaries"]
    assert "NO_PHYSICAL_CLAIM_ADVANCED" in hb
    assert "TERRA_RC4_PRESERVED" in hb


def test_evidence_classes_match_the_spec_pack():
    ec = REG.load_evidence_classes()
    assert ec["allowed"] == [
        "SOFTWARE_VERIFIED",
        "OPERATIONAL_CALIBRATED_PROFILE",
        "MEASUREMENT_HYPOTHESIS",
        "MATHEMATICAL_DERIVATION",
        "SOURCE_PROVENANCE_RECORD",
        "BENCH_PROTOCOL",
        "PUBLIC_ARCHIVE_RECORD",
    ]
    assert "WALL_POWER_FORCE_PERFORMANCE" in ec["refused_public"]
    assert len(ec["refused_public"]) == 7


def test_h_me_ssp_protocol_record_is_hypothesis_gated():
    proto = REG.load_h_me_ssp_001_protocol()
    assert proto["id"] == "H-ME-SSP-001"
    assert proto["status"] == "PUBLIC_RESEARCH_HYPOTHESIS_NOT_VALIDATED"
    for refused in ("thrust", "lift", "antigravity", "free energy",
                    "source authentication"):
        assert refused in proto["claims_refused"]


def test_no_module_maps_to_a_missing_path():
    root = ROOT
    for mod in REG.load_module_registry()["modules"]:
        for rel in mod["repo_paths"]:
            assert (root / rel).exists(), f"{mod['id']}: {rel}"
