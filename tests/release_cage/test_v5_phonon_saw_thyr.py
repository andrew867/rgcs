"""V5 tests: alpha-quartz polaritons, SAW convolver and geometry,
hBN benchmark, THYR readout, and run discipline.

Adapted from 13_TESTS/sample_tests_v5_phonon_saw_thyr.py, wired to
the real cage modules.
"""

from __future__ import annotations

import json
import math
import pathlib

import pytest

from rgcs_workbench.public_cage import alpha_quartz_polariton as AQ
from rgcs_workbench.public_cage import claim_firewall as CF
from rgcs_workbench.public_cage import hyperbolic_materials as HM
from rgcs_workbench.public_cage import saw_convolver as SC
from rgcs_workbench.public_cage import saw_geometry_guard as SG
from rgcs_workbench.public_cage import thyr_readout as TR
from rgcs_workbench.public_cage import v5_measurement_runs as VR

ROOT = pathlib.Path(__file__).resolve().parents[2]
CAGE = ROOT / "rgcs_workbench" / "public_cage"


# ----------------------------------------------------- SAW convolver

def test_us3833867_sum_frequency_example():
    example = SC.load_source_example()
    assert example["f1_mhz"] + example["f2_mhz"] == example["sum_mhz"]
    assert SC.sum_frequency_hz(123e6, 132e6) == 255e6
    assert example["claim_status"] == "SOURCE_REPORTED_EXAMPLE"


def test_convolver_wavevector_and_bidirectionality():
    assert SC.output_wavevector(10.0, 4.0) == 6.0
    with pytest.raises(ValueError, match="bidirectional"):
        SC.convolver_operator(f1_hz=123e6, f2_hz=132e6,
                              launch_right=False)
    result = SC.convolver_operator(f1_hz=123e6, f2_hz=132e6)
    assert result["output_sum_hz"] == 255e6
    assert result["bias_field_role"] == (
        "ATTENUATION_CONTROL_AND_CARRIER_DRIFT")


def test_convolver_refuses_net_gain_as_target():
    with pytest.raises(SC.GainTargetRefused):
        SC.convolver_operator(f1_hz=123e6, f2_hz=132e6,
                              desired_net_gain_db=6.0)


# ------------------------------------------------- SAW geometry guard

def test_us4023124_quarter_and_eighth_geometry():
    assert SG.lambda_saw_m(8.0, 1.0) == 8.0
    assert SG.quarter_wave_m(8.0, 1.0) == 2.0
    assert SG.eighth_wave_m(8.0, 1.0) == 1.0


def test_geometry_requires_velocity_and_frequency():
    lam = SG.lambda_saw_m(3488.0, 123e6)
    assert lam > 0
    with pytest.raises(ValueError, match="velocity and a frequency"):
        SG.lambda_saw_m(0.0, 123e6)


def test_overlap_and_strip_regions_are_separated():
    overlap = SG.overlap_electrode_geometry(3488.0, 123e6)
    strips = SG.correction_strip_geometry(3488.0, 123e6,
                                          spacing_multiple=3)
    assert overlap["role"] == "ACTIVE_DRIVE"
    assert strips["role"] == "WAVEFRONT_CORRECTION"
    lam = SG.lambda_saw_m(3488.0, 123e6)
    assert math.isclose(overlap["electrode_width_m"], lam / 4.0)
    assert math.isclose(strips["strip_width_m"], lam / 8.0)
    assert math.isclose(strips["effective_spacing_m"], 3.0 * lam / 4.0)
    with pytest.raises(ValueError, match="odd multiple"):
        SG.correction_strip_geometry(3488.0, 123e6, spacing_multiple=2)


def test_aperture_modes_never_mix():
    assert SG.aperture_guard("uniform")["aperture_mode"] == "uniform"
    with pytest.raises(ValueError, match="never a mixture"):
        SG.aperture_guard("uniform+length_weighted")


# --------------------------------------------- alpha-quartz polaritons

def test_quartz_tensor_branch_selection_uses_distinct_components():
    parallel = AQ.branch_components("optic_axis_parallel_to_surface",
                                    eps_parallel=2.3,
                                    eps_perpendicular=-2.0)
    perpendicular = AQ.branch_components(
        "optic_axis_perpendicular_to_surface",
        eps_parallel=2.3, eps_perpendicular=-2.0)
    assert (parallel["eps_x"], parallel["eps_z"]) != (
        perpendicular["eps_x"], perpendicular["eps_z"])
    omega = 2.0 * math.pi * 30.0e12
    k_par = AQ.polariton_k(omega, parallel["eps_x"], parallel["eps_z"])
    k_perp = AQ.polariton_k(omega, perpendicular["eps_x"],
                            perpendicular["eps_z"])
    assert k_par != k_perp


def test_fringe_profile_and_measured_k_conversion():
    s0 = AQ.fringe_profile(0.0, 1.0, 10e-6, 5e-6, phase_rad=0.0)
    assert s0 == 0.0                       # sin(0)
    k0 = 2.0 * math.pi / 10.6e-6
    kp = AQ.measured_k_from_fringes(5e-6, k0, math.radians(30.0))
    assert math.isclose(kp, 2.0 * math.pi / 5e-6
                        - k0 * math.cos(math.radians(30.0)))


def test_atr_gap_changes_witness_metadata():
    contact = AQ.atr_witness_metadata(0.0, 0.0)
    gapped = AQ.atr_witness_metadata(2.0, 0.0)
    assert contact["witness_sensitivity"] == "CONTACT_BASELINE"
    assert gapped["witness_sensitivity"] == "ATR_GAP_OR_LAYER_SENSITIVE"
    assert gapped["label"] == "MODEL_ESTIMATE"


def test_quartz_medium_field_contract():
    missing = AQ.validate_medium({"crystal_cut": "X-cut"})
    assert len(missing) == len(AQ.MEDIUM_REQUIRED_FIELDS) - 1


# ------------------------------------------------------ hBN benchmark

def test_hbn_benchmark_requires_wide_scan_for_long_lifetimes():
    row = HM.benchmark_row(
        material="10B hBN", isotope_fraction=0.99, thickness_nm=120,
        reststrahlen_band="II", branch_id="M0",
        propagation_length_um=25, lifetime_ps=4.2, q_factor=400,
        launch_type="edge_launch", scan_width_um=40,
        incidence_angle_alpha=30.0, edge_angle_beta=90.0)
    assert row["role"] == HM.ROLE
    with pytest.raises(ValueError, match="scan at least as wide"):
        HM.benchmark_row(
            material="10B hBN", isotope_fraction=0.99, thickness_nm=120,
            reststrahlen_band="II", branch_id="M0",
            propagation_length_um=25, lifetime_ps=4.2, q_factor=400,
            launch_type="edge_launch", scan_width_um=10,
            incidence_angle_alpha=30.0, edge_angle_beta=90.0)


def test_hbn_is_benchmark_not_quartz_replacement():
    assert "NOT_QUARTZ_REPLACEMENT" in HM.ROLE


# ------------------------------------------------------- THYR readout

def test_thyr_sideband_relation():
    bands = TR.sidebands(100.0, 7.0)
    assert bands["stokes"] == 193.0
    assert bands["anti_stokes"] == 207.0
    assert bands["role"] == TR.ROLE


def test_thyr_resonance_list_preserves_unresolved_feature():
    observed = TR.source_resonances_thz()
    assert observed == [2.0, 5.2, 7.0, 13.4, 14.3, 16.3]
    feature = TR.unresolved_feature()
    assert "9 to 10" in feature["range_thz"]
    assert feature["status"] == "UNRESOLVED_IN_SOURCE"


def test_thyr_is_readout_not_drive():
    assert TR.ROLE == "READOUT_LANE_NOT_DRIVE_VALIDATION"


# ----------------------------------------------- run rows and witness

def test_one_variable_at_a_time_rows_have_controls():
    rows = VR.v5_run_sequence()
    assert VR.validate_run_sequence(rows) == []
    assert rows[0]["parent_run_id"] is None
    for row in rows[1:]:
        assert row["parent_run_id"] == row["control_run"]
        assert row["claim_status"] == "SIMULATION_ESTIMATE"


def test_v5_witness_layer_extends_v4b_without_breaking_it():
    layer = VR.witness_layer_v5(ATR_possible=True, surface_gap_um=2.0)
    assert layer["ATR_possible"] is True
    for field in VR.V5_WITNESS_EXTENSION_FIELDS:
        assert field in layer
    with pytest.raises(ValueError, match="unknown witness fields"):
        VR.witness_layer_v5(lift_measured=True)
    with pytest.raises(ValueError, match="invalid V5 witness layer"):
        VR.witness_layer_v5(claim_status="WITNESS_VALIDATION")


# ------------------------------------------------- ledger and scans

def test_v5_reference_ledger_present_and_bounded():
    rows = json.loads((CAGE / "v5_reference_ledger.json")
                      .read_text(encoding="utf-8"))
    ids = [r["id"] for r in rows]
    assert len(ids) == 8 and len(set(ids)) == 8
    for row in rows:
        assert row["claim_boundary"], row["id"]
    blob = " ".join(ids)
    for anchor in ("US3833867", "US4023124", "FALGE", "HBN", "RUBANO"):
        assert anchor in blob.upper(), anchor


def test_v5_files_scan_clean():
    targets = [
        ROOT / "docs" / "research"
        / "v5_phonon_polariton_saw_convolver_bridge.md",
        ROOT / "docs" / "research"
        / "v5_measurement_model_and_readout_plan.md",
        CAGE / "alpha_quartz_polariton.py", CAGE / "saw_convolver.py",
        CAGE / "saw_geometry_guard.py", CAGE / "hyperbolic_materials.py",
        CAGE / "thyr_readout.py", CAGE / "v5_measurement_runs.py",
        CAGE / "v5_reference_ledger.json", CAGE / "v5_seed_data.json",
    ]
    report = CF.firewall_report(CF.scan_paths(targets))
    assert report["clean"], report


def test_no_force_thrust_torque_or_lift_callables_in_v5_modules():
    import inspect
    for module in (AQ, SC, SG, HM, TR, VR):
        for name, obj in inspect.getmembers(module, callable):
            for banned in ("force", "thrust", "torque", "lift", "newton"):
                assert banned not in name.lower(), (module.__name__, name)
