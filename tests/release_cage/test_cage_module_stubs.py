"""Release-matrix tests for every module in the 2026-08-04 spec pack.

One test per row of 03_TESTS/TEST_MATRIX.csv, all sixteen wired for
real. The deeper per-module spec tests live in the sibling
test_cage_* files; this file is the matrix itself, kept thin so a
release reviewer can read it top to bottom against the CSV.

No test in this file computes force, thrust, or any power-to-
performance quantity.
"""

from __future__ import annotations

import math
import pathlib

import pytest

from rgcs_coordinate.codecs import variable_length_36 as VL
from rgcs_workbench.public_cage import archive_schema as AS
from rgcs_workbench.public_cage import claim_firewall as CF
from rgcs_workbench.public_cage import codec_receipts as CR
from rgcs_workbench.public_cage import craft_path_registry as CPR
from rgcs_workbench.public_cage import crystal_objects as CO
from rgcs_workbench.public_cage import manifest as MF
from rgcs_workbench.public_cage import phyrll_lane as PL
from rgcs_workbench.public_cage import registry as REG
from rgcs_workbench.public_cage import terra_frozen as TF

ROOT = pathlib.Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------- MOD-001

def test_codec_001_every_legal_parse_round_trips():
    word = VL.encode(6, 100, 2500, (3, 1), 5)
    receipt = CR.parse_receipt(word.value, width_bits=word.width_bits)
    assert receipt["legal_parse_status"] == CR.STATUS_LEGAL
    assert receipt["round_trip_ok"] is True


def test_codec_002_rejected_parses_include_explicit_reason():
    receipt = CR.parse_receipt(1 << 40)
    assert receipt["legal_parse_status"] == CR.STATUS_REJECTED
    assert "bits" in receipt["reject_reason"]


# ---------------------------------------------------------------- MOD-002

def test_terra_001_rc4_metadata_preserved_exactly():
    p = TF.frozen_profile()
    assert p["repo"] == "andrew867/rgcs-terra"
    assert p["tag"] == "v1.0.0-rc4"
    assert p["commit"] == "4fdee3e7fbdb416d8e4b32dcb422d0977e6f20af"
    assert p["verdict"] == "GREEN_TERRA_ALIGNMENT_SOLVED_CALIBRATED_V1"


def test_terra_002_no_physical_endpoint_validation_claimed():
    assert TF.PHYSICAL_ENDPOINT_VALIDATED is False
    with pytest.raises(TF.PhysicalValidationRefused):
        TF.promote_physical_validation()


# ---------------------------------------------------------------- MOD-003

def test_crys_001_specimen_measurement_requires_uuid_and_context():
    bad = CO.validate_specimen({"specimen_id": "not-a-uuid"})
    assert any("UUID" in p for p in bad)
    assert len(bad) >= len(CO.SPECIMEN_REQUIRED_FIELDS) - 1


def test_crys_002_no_bench_claim_without_bench_receipt():
    with pytest.raises(CO.BenchReceiptRequired):
        CO.bench_claim("resonance observed", bench_receipts=None)


# ---------------------------------------------------------------- MOD-004

def test_phyrll_001_protocol_refuses_force_output_fields():
    problems = PL.validate_measurement_record({
        "voltage_v": 1.0, "current_a": 0.1, "temperature_c": 20.0,
        "magnetometer_response": {}, "force_N": 0.5})
    assert any("refused output field" in p for p in problems)


def test_phyrll_002_dummy_controls_required_for_every_sweep():
    problems = PL.validate_sweep_plan({"controls": [],
                                       "baseline_recorded": False})
    assert any("dummy crystal" in p for p in problems)
    assert any("baseline" in p for p in problems)


# ---------------------------------------------------------------- MOD-005

def test_hmessp_001_derived_geometry_values_reproduce():
    """DERIVED_ARITHMETIC only; no physical quantity is claimed."""
    proto = REG.load_h_me_ssp_001_protocol()
    g, f = proto["geometry"], proto["frequencies"]
    assert g["sector_count"] == 37
    sector_angle = 360.0 / g["sector_count"]
    assert math.isclose(sector_angle, 9.72972972972973, rel_tol=1e-12)
    pitch = math.pi * g["outer_diameter_m"] / g["sector_count"]
    assert math.isclose(pitch, 24.453478e-3, abs_tol=1e-8)
    assert f["external_resonance_hz"] == 4096 * 411 == 1683456
    # One guided period per sector: a loaded slow-wave regime, far
    # below free-space electromagnetic speed.
    v_phase = pitch * f["external_resonance_hz"]
    assert 40000.0 < v_phase < 42000.0
    assert v_phase < 3.0e8 * 1e-3


def test_hmessp_002_all_null_controls_present():
    proto = REG.load_h_me_ssp_001_protocol()
    required = {
        "all-active mask", "35/37 run mask", "33/37 steering mask",
        "mirrored mask", "reversed phase progression",
        "dummy resistive load", "dummy crystal", "nonmagnetic ring",
        "cable reroute", "thermal blank", "acoustic isolation",
        "magnetic background record", "Helmholtz null",
        "magnetic shielding or field cancellation",
    }
    assert required <= set(proto["required_controls"])


# ---------------------------------------------------------------- MOD-006

def test_craft_001_no_performance_claim_without_validation():
    reg = CPR.CraftPathRegistry()
    with pytest.raises(CPR.ValidationRefused):
        reg.add_record({"status": "BENCH_MEASURED",
                        "statement": "craft-scale ring performs"})


def test_craft_002_frequency_spine_roles_remain_separated():
    assert CPR.spine_roles_are_separated()


# ---------------------------------------------------------------- MOD-007

def test_arch_001_every_record_has_source_type_and_hash_status():
    problems = AS.validate_record({"record_id": "ARC-X"})
    assert any("source_type" in p for p in problems)
    assert any("raw_file_hash" in p for p in problems)


def test_arch_002_community_submissions_start_unverified():
    entry = AS.community_intake({"record_id": "ARC-Y", "verified": True})
    assert entry["source_type"] == "COMMUNITY_SUBMISSION_UNVERIFIED"
    assert entry["verified"] is False


# ---------------------------------------------------------------- MOD-008

def test_rel_001_claim_scan_zero_banned_claims_on_gated_surface():
    surface = CF.cage_public_surface(ROOT)
    report = CF.firewall_report(CF.scan_paths(surface))
    assert report["clean"], report
    assert report["verdict"] == "RELEASE_FILTER_CLEAN"


def test_rel_002_manifest_and_sha256sums_complete():
    surface = CF.cage_public_surface(ROOT)
    manifest = MF.build_manifest(
        ROOT, surface, release_id="RGCS_WORKBENCH_PUBLIC_RC1_CAGE",
        created_at="2026-08-05T00:00:00Z")
    assert MF.validate_manifest(manifest, ROOT, surface) == []
