"""v4.7 PMWR: crystal translation lane, Phryll guards, benches, ingest
freeze, and the adversarial campaign (rows R20-R29, R34, R36).

The adversarial tests are attacks that MUST fail to get through:
perfect memory, universal key, free energy, Phryll-by-sensor-change,
pyramid-as-mechanism, and post-hoc rewriting of the operator note.
"""
from __future__ import annotations

import math

import pytest


# --- geometry (R20/R24) ------------------------------------------------------

def test_pyramid_ratios_reproduce_the_pack_csv():
    from pmwr.crystal import pyramid_ratio
    r = pyramid_ratio(51.843)
    assert abs(r["h_over_half_base"] - 1.272737633428312) < 1e-12
    assert abs(r["full_base_over_height"] - 1.571415779238567) < 1e-12
    r60 = pyramid_ratio(60.0)
    assert abs(r60["h_over_half_base"] - math.sqrt(3)) < 1e-12


def test_pyramid_audit_refuses_the_mechanism_reading():
    from pmwr.crystal import pyramid_ratio_audit
    a = pyramid_ratio_audit()
    assert a["evidence_class"] == "GEOMETRY_IDENTITY"
    assert "not a physics constant" in a["not_a_mechanism"]
    assert "ANTHROPOGENIC_STRUCTURE" in a["not_a_mechanism"]
    # all seven candidate angles present, including emitter controls
    assert len(a["angles"]) == 7
    assert "emitter_60" in a["angles"]


def test_pi_over_2_proximity_is_reported_not_promoted():
    from pmwr.crystal import pyramid_ratio_audit
    a = pyramid_ratio_audit()
    best = a["angles"][a["closest_to_pi_over_2"]]
    assert best["abs_diff_from_pi_over_2"] < 1e-3   # yes, it is close
    # and the audit still calls it an observation about a chosen angle
    assert "chosen angle" in a["observation"]


def test_geometry_reversal_control_swaps_terminations():
    from pmwr.crystal import CrystalGeometry
    g = CrystalGeometry("VOGEL-1", 110.0, 51.843, 60.0, 0.0, 6, 6,
                        taper=True)
    assert g.asymmetric
    r = g.reversed()
    assert r.top_termination_deg == 60.0
    assert r.bottom_termination_deg == 51.843


# --- excitation and energy (R22/R23/R27) ----------------------------------------

def test_self_oscillation_requires_loop_and_energy_source():
    import pmwr
    from pmwr.crystal import ExcitationPlan
    with pytest.raises(pmwr.ClaimBoundaryError):
        ExcitationPlan("X", "ACTIVE_FEEDBACK", 32768.0, 0.1)
    ok = ExcitationPlan("X", "ACTIVE_FEEDBACK", 32768.0, 0.1,
                        feedback_loop_closed=True,
                        energy_source="bench supply 12V")
    assert ok.energy_source


def test_energy_ledger_flags_overunity_as_accounting_error():
    from pmwr.crystal import energy_ledger
    bad = energy_ledger({"drive": 1.0}, {"acoustic": 0.5, "heat": 0.7})
    assert bad["verdict"] == "ACCOUNTING_ERROR"
    assert "never reported as free energy" in bad["note"]
    good = energy_ledger({"drive": 1.0}, {"acoustic": 0.2, "heat": 0.7})
    assert good["verdict"] == "CONSISTENT"


def test_energy_ledger_requires_an_input_source():
    import pmwr
    from pmwr.crystal import energy_ledger
    with pytest.raises(pmwr.ClaimBoundaryError):
        energy_ledger({}, {"acoustic": 0.1})


def test_translation_entries_are_hypotheses_with_named_mechanisms():
    import pmwr
    from pmwr.crystal import translation_matrix_entry
    e = translation_matrix_entry("ELECTRICAL", 4096.0, "ACOUSTIC",
                                 4096.0, "piezoelectric_converse")
    assert e["status"] == "OPERATIONAL_HYPOTHESIS"
    none = translation_matrix_entry("ELECTRICAL", 4096.0, "OPTICAL",
                                    2 ** 49, "NONE_PROPOSED")
    assert none["status"] == "UNSUPPORTED"
    with pytest.raises(pmwr.ClaimBoundaryError):
        translation_matrix_entry("A", 1, "B", 2, "phryll_flow")


# --- Phryll registry (R25/R26/R28) ------------------------------------------------

def test_latent_entry_rejects_off_ladder_states():
    import pmwr
    from pmwr.crystal import LatentEntry
    with pytest.raises(pmwr.ClaimBoundaryError):
        LatentEntry("L1", "glow", state="CONFIRMED")


def test_promotion_cannot_skip_rungs():
    import pmwr
    from pmwr.crystal import LatentEntry, promote_latent
    e = LatentEntry("L1", "residual hum")
    with pytest.raises(pmwr.ClaimBoundaryError):
        promote_latent(e, "REPLICATED_ANOMALY", {"x": 1})


def test_residual_requires_all_channels_and_sham_control():
    """The core gate: a sensor change with unmeasured channels or no
    sham control can NEVER become a residual."""
    import pmwr
    from pmwr.crystal import (LatentEntry, OUTPUT_CHANNELS,
                              output_matrix_template, promote_latent)
    e = promote_latent(LatentEntry("L1", "hum"),
                       "OPERATIONAL_HYPOTHESIS",
                       {"definition": "preregistered"})
    partial = output_matrix_template()
    partial["electrical"] = 0.0
    with pytest.raises(pmwr.ClaimBoundaryError):
        promote_latent(e, "UNEXPLAINED_INSTRUMENT_RESIDUAL",
                       {"output_matrix": partial,
                        "sham_control_run": True})
    full = {ch: 0.0 for ch in OUTPUT_CHANNELS}
    with pytest.raises(pmwr.ClaimBoundaryError):
        promote_latent(e, "UNEXPLAINED_INSTRUMENT_RESIDUAL",
                       {"output_matrix": full,
                        "sham_control_run": False})
    ok = promote_latent(e, "UNEXPLAINED_INSTRUMENT_RESIDUAL",
                        {"output_matrix": full,
                         "sham_control_run": True})
    assert ok.state == "UNEXPLAINED_INSTRUMENT_RESIDUAL"


def test_replication_gate_demands_independence():
    import pmwr
    from pmwr.crystal import LatentEntry, OUTPUT_CHANNELS, promote_latent
    e = LatentEntry("L1", "hum", "UNEXPLAINED_INSTRUMENT_RESIDUAL")
    with pytest.raises(pmwr.ClaimBoundaryError):
        promote_latent(e, "REPLICATED_ANOMALY",
                       {"independent_replication": False})


# --- benches (R21/R28/R29) ---------------------------------------------------------

def test_benches_are_plans_with_hardware_absent():
    from pmwr.benches import compile_benches
    c = compile_benches()
    assert c["apparatus_status"] == "NOT BUILT"
    assert c["physical_status"] == "UNTESTED"
    assert "R29" in c["claim_boundary"]
    assert c["n_benches"] >= 3


def test_directional_bench_tests_both_orientations_blind():
    from pmwr.benches import directional_transfer_bench
    p = directional_transfer_bench()
    assert "orientation" in p.question.lower()
    assert "blind" in p.blinding.lower()
    assert "no extension" in p.stopping_rule


def test_null_set_carries_the_source_mandated_controls():
    from pmwr.benches import NULL_SET
    joined = " ".join(NULL_SET)
    for req in ("reversed", "sham-drive", "fused silica",
                "feedback loop open", "fixture without crystal"):
        assert req in joined


def test_sham_bench_encodes_the_power_not_engaged_episode():
    from pmwr.benches import sham_drive_bench
    from pmwr.ingest import SHAM_EPISODE
    p = sham_drive_bench()
    assert "double-blind" in p.blinding
    assert "power was not engaged" in SHAM_EPISODE


# --- ingest freeze (R36 + A77/A78 attacks) --------------------------------------------

def test_operator_note_is_verbatim_and_hash_pinned():
    from pmwr.ingest import OPERATOR_NOTE, operator_note_fingerprint
    assert operator_note_fingerprint() == (
        "fff2f47e7c690eeda59fc6cc2d8e968d32a94f891155473aa65dbc592cb223d9")
    assert OPERATOR_NOTE.startswith("The crystal is a phase "
                                    "translation device.")
    assert "Phryll" in OPERATOR_NOTE


def test_evaluation_contract_is_frozen():
    from pmwr.ingest import EVALUATION_SPEC, evaluation_fingerprint
    assert "Frozen" in EVALUATION_SPEC
    assert evaluation_fingerprint() == (
        "09660bbf84637c55b0098df1eaa863da48f366b8a307d26870ecd8b6bebbbe3b")


def test_novelty_boundary_does_not_claim_textbook_material():
    from pmwr.ingest import NOVELTY_BOUNDARY
    textbook = " ".join(NOVELTY_BOUNDARY["textbook_not_novel"])
    assert "phase-locked loops" in textbook
    assert "GPS practice" in textbook
    assert len(NOVELTY_BOUNDARY["programme_specific"]) >= 3


def test_excluded_miracle_claims_are_labelled_not_investigable():
    from pmwr.ingest import SOURCE_ELEMENTS
    miracle = [t for c, t in SOURCE_ELEMENTS if "antigravity" in c][0]
    assert "DEVICE_MIRACLES" in miracle


# --- adversarial campaign (A76-A78) ------------------------------------------------

def test_attack_universal_key_no_privileged_frequency():
    """A77: nothing in PMWR may assert 4096 Hz is privileged."""
    import pathlib

    import pmwr
    pkg = pathlib.Path(pmwr.__file__).parent
    for p in pkg.glob("*.py"):
        low = p.read_text(encoding="utf-8").lower()
        assert "privileged by nature" not in low.replace(
            "not privileged by nature", "")


def test_attack_software_cannot_emit_physical_evidence():
    import pmwr
    with pytest.raises(pmwr.ClaimBoundaryError):
        pmwr.require_non_physical("CALIBRATED_MEASUREMENT")
    with pytest.raises(pmwr.ClaimBoundaryError):
        pmwr.require_non_physical("REPLICATED_ANOMALY")


def test_attack_phryll_interpretation_of_a_sensor_change():
    """A78: a bare sensor delta with nothing else measured cannot walk
    even one rung past hypothesis."""
    import pmwr
    from pmwr.crystal import LatentEntry, promote_latent
    e = LatentEntry("L-GLOW", "meter moved", "OPERATIONAL_HYPOTHESIS")
    with pytest.raises(pmwr.ClaimBoundaryError) as exc:
        promote_latent(e, "UNEXPLAINED_INSTRUMENT_RESIDUAL",
                       {"output_matrix": {"electrical": 0.1},
                        "sham_control_run": True})
    assert "unmeasured ordinary channels" in str(exc.value)


def test_attack_closure_cannot_be_sold_as_ambiguity_free():
    from pmwr.recovery import closure_delay_ambiguity
    c = closure_delay_ambiguity(["4096"], 10.0)
    assert c["aliases_within_max_delay"] > 1
    assert "CLOSURE_REMOVES_AMBIGUITY" in c["statement"]
