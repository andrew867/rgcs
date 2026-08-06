"""V4B tests: longitudinal-mode bridge and dielectric witness layer.

Adapted from the pack's sample tests plus the spec acceptance rules:
the model runs with and without a layer, epsilon_d alone moves the
SPP factor and residual, loss alone moves the damping status, labels
are contractual, and a witness is never a validation.
"""

from __future__ import annotations

import math
import pathlib

import pytest

from rgcs_workbench.public_cage import archive_schema as AS
from rgcs_workbench.public_cage import claim_firewall as CF
from rgcs_workbench.public_cage import longitudinal_bridge as LB

ROOT = pathlib.Path(__file__).resolve().parents[2]


# ------------------------------------------------------ core arithmetic

def test_spp_factor_air_reference_value():
    # eps_m=-2, eps_d=1: |(-2*1)/(-2+1)| = 2 -> sqrt(2)
    assert math.isclose(LB.spp_factor(-2.0, 1.0), math.sqrt(2.0))


def test_dielectric_witness_layer_changes_spp_factor():
    assert LB.spp_factor(-2.0, 1.0) != LB.spp_factor(-2.0, 4.0 / 3.0)


def test_spp_singular_denominator_is_refused():
    with pytest.raises(ValueError, match="singular"):
        LB.spp_factor(-1.0, 1.0)


def test_plasma_frequency_and_drude_limits():
    omega_p = LB.plasma_frequency_rad_s(1.0e28, 9.109e-31)
    assert omega_p > 0
    eps = LB.drude_epsilon(2.0 * omega_p, omega_p, 0.0)
    assert eps.real > 0                      # above omega_p: positive
    eps = LB.drude_epsilon(0.5 * omega_p, omega_p, 0.0)
    assert eps.real < 0                      # below omega_p: metallic
    with pytest.raises(ValueError):
        LB.plasma_frequency_rad_s(-1.0, 9.1e-31)


def test_momentum_bridge_arithmetic():
    assert LB.momentum_bridge_k(10.0, 5.0, 2.0, sign=1) == 17.0
    assert LB.momentum_bridge_k(10.0, 5.0, 2.0, sign=-1) == 13.0
    with pytest.raises(ValueError):
        LB.momentum_bridge_k(1.0, 1.0, 1.0, sign=0)


# --------------------------------------------------- witness layer rules

def _layer(**overrides):
    layer = {
        "layer_id": "DWL_0001", "sample_id": "FORMATION_SAMPLE_A",
        "medium_type": "plant_surface_film",
        "epsilon_d_estimate": 1.33, "loss_tangent_estimate": 0.0,
        "surface_conductivity_estimate": 0.0,
        "water_film_state": "unknown",
        "molecular_fingerprint_status": "unknown",
        "mineral_particle_status": "unknown",
        "Raman_available": False, "SERS_possible": True,
        "FTIR_available": False, "time_since_event_days": 3,
        "control_sample_id": "OFF_FORMATION_A",
        "claim_status": "MEASUREMENT_TARGET",
    }
    layer.update(overrides)
    return layer


def test_witness_layer_required_fields_enforced():
    assert LB.validate_witness_layer(_layer()) == []
    broken = _layer()
    del broken["control_sample_id"]
    assert any("control_sample_id" in p
               for p in LB.validate_witness_layer(broken))


def test_residue_is_witness_not_conclusion():
    problems = LB.validate_witness_layer(
        _layer(claim_status="DIELECTRIC_WITNESS_VALIDATION"))
    assert any("never carry a validation" in p for p in problems)
    assert "VALIDATION" not in "DIELECTRIC_WITNESS_LAYER_HYPOTHESIS"


def test_model_runs_with_and_without_layer():
    without = LB.bridge_run(carrier_hz=1.683456e6)
    with_layer = LB.bridge_run(carrier_hz=1.683456e6,
                               witness_layer=_layer())
    assert without["witness_layer_present"] is False
    assert with_layer["witness_layer_present"] is True
    assert without["label"] in LB.OUTPUT_LABELS
    assert with_layer["label"] in LB.OUTPUT_LABELS


def test_changing_only_epsilon_d_changes_factor_and_residual():
    base = LB.bridge_run(carrier_hz=1.683456e6,
                         witness_layer=_layer(epsilon_d_estimate=1.0))
    shifted = LB.bridge_run(carrier_hz=1.683456e6,
                            witness_layer=_layer(
                                epsilon_d_estimate=4.0 / 3.0))
    assert base["spp_factor"] != shifted["spp_factor"]
    assert base["spp_residual_vs_air"] == 0.0
    assert shifted["spp_residual_vs_air"] != 0.0


def test_changing_only_loss_changes_damping_status():
    low = LB.bridge_run(carrier_hz=1.683456e6,
                        witness_layer=_layer(loss_tangent_estimate=0.0))
    lossy = LB.bridge_run(carrier_hz=1.683456e6,
                          witness_layer=_layer(loss_tangent_estimate=0.05))
    assert low["damping_status"] == "LOW_LOSS_LAYER"
    assert lossy["damping_status"] == "LOSSY_LAYER_DAMPING_EXPECTED"
    assert low["spp_factor"] == lossy["spp_factor"]


def test_run_matrix_changes_one_variable_at_a_time():
    runs = LB.witness_run_matrix()
    assert [r["run_id"] for r in runs] == [
        f"RUN_DWL_000{i}" for i in range(1, 7)]
    assert runs[0]["result"]["witness_layer_present"] is False
    assert runs[1]["result"]["spp_residual_vs_air"] != 0.0
    assert runs[2]["result"]["damping_status"] == (
        "LOSSY_LAYER_DAMPING_EXPECTED")
    # runs 4-6 change flags only; SPP factor stays at the baseline
    for run in runs[3:]:
        assert run["result"]["spp_factor"] == runs[0]["result"]["spp_factor"]


def test_residue_block_defaults_are_honest_unknowns():
    block = LB.residue_dielectric_block()
    assert block["sample_status"] == "none"
    assert block["Raman_fingerprint_available"] is False
    assert "not causal proof" in block["interpretation_rule"]
    with pytest.raises(ValueError, match="unknown residue-block"):
        LB.residue_dielectric_block(lift_measured=True)


def test_sidebands_use_envelope_not_a_merged_family():
    run = LB.bridge_run(carrier_hz=1.683456e6)
    assert run["predicted_sidebands_hz"] == [
        1.683456e6 + n * 4096.0 for n in (-2, -1, 1, 2)]
    match = LB.nearest_family_match(20098.13)
    assert match["rule"] == "FAMILIES_NEVER_MERGE_WITHOUT_CORRECTION_RULE"
    assert match["nearest_rgcs_key"] == "RGCS_4096_X5"


# ------------------------------------ SSPP corrugated-waveguide lane

def test_sspp_period_is_the_37_cell_sector_pitch():
    d = LB.sspp_period_m(0.288, 37)
    assert math.isclose(d, 24.453478e-3, abs_tol=1e-8)
    assert math.isclose(LB.sspp_beta_max_per_m(d), math.pi / d)


def test_sspp_well_formed_threshold_is_half_period():
    d = LB.sspp_period_m(0.288, 37)
    assert LB.sspp_well_formed(d / 2.0 + 1e-6, d) is True
    assert LB.sspp_well_formed(d / 2.0 - 1e-6, d) is False
    assert LB.sspp_well_formed(d / 2.0, d) is False


def test_sspp_quarter_wave_asymptote():
    h = 0.020
    assert math.isclose(LB.sspp_plasma_frequency_hz(h),
                        LB.C_M_PER_S / (4.0 * h))
    # groove dielectric lowers the asymptote by sqrt(eps_g)
    assert math.isclose(LB.sspp_plasma_frequency_hz(h, epsilon_g=4.0),
                        LB.C_M_PER_S / (8.0 * h))
    with pytest.raises(ValueError):
        LB.sspp_plasma_frequency_hz(-0.01)


def test_sspp_dielectric_layer_toggles_witness_sensitivity():
    baseline = LB.sspp_lane()
    layered = LB.sspp_lane(epsilon_a=4.0 / 3.0, t_layer_m=1e-6)
    assert baseline["sensitivity_status"] == "BASELINE_NO_LAYER"
    assert layered["sensitivity_status"] == "WITNESS_SENSITIVE"
    filled = LB.sspp_lane(epsilon_g=2.0)
    assert filled["f_p_hz"] != baseline["f_p_hz"]


def test_sspp_thin_layer_mode_is_never_causal_proof():
    lane = LB.sspp_lane(groove_depth_m=0.014)
    assert lane["claim"] == "THIN_LAYER_MODE_HYPOTHESIS_NOT_CAUSAL_PROOF"
    assert lane["label"] in LB.OUTPUT_LABELS
    assert lane["well_formed"] is True      # 14 mm > 12.23 mm = d/2
    assert lane["source"] == "Erementchouk, Joy, Mazumder 2016"


def test_sspp_anchor_is_in_the_ledger():
    from rgcs_workbench.public_cage import physics_spine as PS
    rows = {r["id"]: r for r in PS.load_ledger_json()}
    assert "Erementchouk" in rows["P018"]["identifier_or_url"]
    assert rows["P018"]["claim_boundary"]


# ------------------------------------------------- ledger and claim scans

def test_source_ledger_has_the_spp_pdf_with_hash():
    records = {r["record_id"]: r for r in AS.load_public_records()}
    entry = records["ARC-0005"]
    assert entry["source_type"] == "PDF_SOURCE"
    assert "21-Justin.pdf" in entry["title"]
    assert len(entry["raw_file_hash"]) == 64
    assert "no formation-causality claim" in entry["claim_boundary"]


def test_no_force_thrust_torque_or_lift_callable_exists():
    import inspect
    for name, obj in inspect.getmembers(LB, callable):
        for banned in ("force", "thrust", "torque", "lift", "newton"):
            assert banned not in name.lower(), name


def test_new_doc_and_module_scan_clean():
    targets = [ROOT / "docs" / "research" / "longitudinal_mode_bridge.md",
               ROOT / "rgcs_workbench" / "public_cage"
               / "longitudinal_bridge.py"]
    report = CF.firewall_report(CF.scan_paths(targets))
    assert report["clean"], report
