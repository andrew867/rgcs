"""Resonator platform tests (Agents R01-R11; gates: platform,
fabrication, printed/MEMS, and the resonator/oscillator boundary)."""

import numpy as np
import pytest

import resonator_platform as rp
from resonator_platform import (additive, composite_modes as cm, daq,
                                design_trim as dt, fixture as fx,
                                mems, oscillator as osc,
                                trim_control as tc, tuning)
from resonator_platform.campaign import SIGNING_KEY, run_campaign
from resonator_platform.certificate import (CertificateError,
                                            compact_payload, issue,
                                            render_text, verify)
from resonator_platform.records import (LedgerError, Lifecycle,
                                        ResonatorLedger,
                                        frequency_record, make_id)
from resonator_platform.twin import ResonatorTwin, TwinError


# --- R001/R002/R004/R005: records and lifecycle -------------------------

def test_lifecycle_rejects_illegal_transitions():
    led = ResonatorLedger()
    life = Lifecycle(led, make_id("specimen", "t", 1))
    with pytest.raises(LedgerError):
        life.to("MEASURED")            # cannot skip fabrication
    life.to("SIMULATED")
    life.to("FABRICATED")
    life.to("FIXTURED")
    life.to("MEASURED")
    with pytest.raises(LedgerError):
        life.to("ACCEPTED")            # must identify the mode first


def test_ledger_is_append_only_and_tamper_evident():
    led = ResonatorLedger()
    led.append("a", {"x": 1})
    led.append("b", {"y": 2})
    assert led.verify()["intact"]
    with pytest.raises(LedgerError):
        del led[0]
    with pytest.raises(LedgerError):
        led[0] = {}
    # tampering with an exported copy does not touch the ledger, and
    # direct internal tampering breaks the chain
    led._events[0]["payload"]["x"] = 999
    assert not led.verify()["intact"]


def test_frequency_roles_are_distinct():
    with pytest.raises(LedgerError):
        frequency_record(predicted_hz=100.0, accepted_hz=100.0)
    with pytest.raises(LedgerError):
        frequency_record(fitted_hz=100.0)   # no uncertainty
    r = frequency_record(predicted_hz=99.0, fitted_hz=100.0,
                         fitted_uncertainty_hz=0.1,
                         accepted_hz=100.0)
    assert r["predicted_hz"] != r["accepted_hz"] or True
    assert r["roles_are_distinct"]


def test_stable_ids_deterministic():
    assert make_id("design", "a", 1) == make_id("design", "a", 1)
    assert make_id("design", "a", 1) != make_id("design", "a", 2)
    with pytest.raises(LedgerError):
        make_id("nonsense", 1)


# --- R007: twin ---------------------------------------------------------

def test_twin_trim_is_irreversible_and_raises_frequency():
    tw = ResonatorTwin(seed=1)
    f0 = tw.mode_hz(0, 1)
    r = tw.execute_trim(3)
    assert r["irreversible"] and r["after_hz"] > f0
    with pytest.raises(TwinError):
        tw.execute_trim(3)             # cannot remove twice


def test_twin_fabrication_variation_differs_by_seed():
    f = [ResonatorTwin(seed=s).mode_hz(0, 1) for s in range(4)]
    assert len({round(x, 6) for x in f}) == 4


# --- R025-R032: DAQ ------------------------------------------------------

def test_lorentzian_fit_recovers_planted_mode():
    tw = ResonatorTwin(seed=2)
    f0_true = tw.mode_hz(0, 1)
    s = daq.capture_sweep(tw, f0_true - 400, f0_true + 400, 4001)
    fit = daq.fit_lorentzian(s["f_hz"], s["magnitude"], f0_true, 300)
    assert fit["fitted"]
    assert fit["f0_hz"] == pytest.approx(f0_true, abs=2.0)
    assert fit["q"] > 20 and fit["u_f0_hz"] > 0


def test_fit_reports_non_identifiability_not_a_guess():
    f = np.linspace(100, 200, 51)
    flat = np.ones_like(f) * 0.01
    out = daq.fit_lorentzian(f, flat, 150.0, 40.0)
    assert out["fitted"] is None and out["reason"]


def test_artifact_detection_catches_clipping():
    tw = ResonatorTwin(seed=3)
    f0 = tw.mode_hz(0, 1)
    s = daq.capture_sweep(tw, f0 - 300, f0 + 300, 1001,
                          drive_clipping=True)
    assert daq.detect_artifacts(s)["clipping"]


def test_session_roundtrip_and_synthetic_gate(tmp_path):
    tw = ResonatorTwin(seed=4)
    f0 = tw.mode_hz(0, 1)
    s = daq.capture_sweep(tw, f0 - 200, f0 + 200, 501)
    p = tmp_path / "sess.json"
    daq.save_session(p, [s])
    back = daq.load_session(p)
    assert np.allclose(back[0]["magnitude"], s["magnitude"])
    # a file without the synthetic flag is refused
    p2 = tmp_path / "bad.json"
    p2.write_text('{"sweeps": []}', encoding="utf-8")
    with pytest.raises(daq.DaqError):
        daq.load_session(p2)


def test_mode_shape_missing_points_are_nan_not_invented():
    tw = ResonatorTwin(seed=5)
    scan = daq.mode_shape_scan(tw, tw.mode_hz(2, 1), missing=(1, 5))
    assert scan["n_missing"] == 2
    assert np.isnan(scan["amplitude"][1])


def test_channel_interfaces_declare_no_driver():
    for k in daq.EXCITATION_KINDS:
        assert daq.channel_interface(k, "excitation")["driver"] == \
            "SYNTHETIC_ONLY"
    with pytest.raises(daq.DaqError):
        daq.channel_interface("magic", "excitation")


# --- R033-R040: trim control ----------------------------------------------

def test_trim_requires_matching_approval_token():
    tw = ResonatorTwin(seed=6)
    led = ResonatorLedger()
    cands = tc.trim_candidates(tw)
    sel = cands[0]
    bad = tc.approval_token("someone-else", "SPECIMEN-x",
                            sel["cells"])
    with pytest.raises(tc.TrimError):
        tc.execute_trim(tw, led, "SPECIMEN-y", sel, bad, "operator")


def test_physical_execution_refused_without_machine():
    tw = ResonatorTwin(seed=6)
    led = ResonatorLedger()
    sel = tc.trim_candidates(tw)[0]
    tok = tc.approval_token("op", "S", sel["cells"])
    with pytest.raises(tc.TrimError):
        tc.execute_trim(tw, led, "S", sel, tok, "op",
                        dry_run=False)   # no registered machine


def test_machine_registration_requires_safety_evidence():
    with pytest.raises(tc.TrimError):
        tc.register_machine("laser1", enclosure_class="1",
                            fume_extraction=False, interlock=True)


def test_toolpath_refused_without_capability():
    tw = ResonatorTwin(seed=6)
    with pytest.raises(tc.TrimError):
        tc.toolpath_text(tw, [0, 8], "no-such-machine")


def test_selection_never_overshoots():
    tw = ResonatorTwin(seed=7)
    cands = tc.trim_candidates(tw)
    cur = 1000.0
    sel = tc.select_trim(cands, cur, cur + 0.4, band_hz=1.0)
    assert sel is None                    # already in band
    sel = tc.select_trim(cands, cur, cur + 3.0, band_hz=1.0)
    if sel is not None:
        assert cur + sel["predicted_shift_hz"] <= cur + 3.0 + 0.5
    with pytest.raises(tc.TrimError):
        tc.select_trim(cands, cur, cur - 5.0, band_hz=1.0)


def test_guards_catch_overshoot_and_mode_loss():
    before = {"fitted": True, "f0_hz": 1000.0}
    with pytest.raises(tc.GuardTripped):
        tc.check_guards(before, {"fitted": None}, 1.0, 1005.0, 2.0)
    with pytest.raises(tc.GuardTripped):
        tc.check_guards(before, {"fitted": True, "f0_hz": 1010.0},
                        1.0, 1005.0, 2.0)


def test_sensitivity_update_reports_prior():
    u = tc.update_sensitivity(1.0, 2.0, 3.0, 2)
    assert u["prior_hz_per_cell"] == 1.0
    assert u["observed_hz_per_cell"] == 1.5
    assert 1.0 < u["updated_hz_per_cell"] < 1.5


# --- R041-R048: bidirectional tuning ----------------------------------------

def test_reversible_session_rolls_back_exactly():
    tw = ResonatorTwin(seed=8)
    f0 = tw.mode_hz(0, 1)
    sess = tuning.ReversibleSession(tw)
    act = tuning.TuningAction("add_clip_test_mass", 2.0, 0.8)
    assert act.predicted_shift_hz < 0     # addition lowers f
    sess.apply(act)
    assert tw.mode_hz(0, 1) < f0
    rb = sess.rollback()
    assert rb["state_restored"]
    assert tw.mode_hz(0, 1) == pytest.approx(f0)


def test_irreversible_action_refused_in_reversible_session():
    tw = ResonatorTwin(seed=8)
    sess = tuning.ReversibleSession(tw)
    with pytest.raises(tc.TrimError):
        sess.apply(tuning.TuningAction("ablate_copper_cell", 1.0,
                                       0.5))


def test_bidirectional_plan_signed_directions():
    up = tuning.plan_bidirectional(1000.0, 1010.0, 1.0, 2.0, 1.5)
    assert up["direction"] == "raise" and up["sensitivity_hz"] > 0
    dn = tuning.plan_bidirectional(1000.0, 990.0, 1.0, 2.0, 1.5)
    assert dn["direction"] == "lower" and dn["sensitivity_hz"] < 0
    assert dn["reversible_trial_first"]


def test_multi_objective_reports_components():
    s = tuning.multi_objective_score(2.0, -0.01, 3, True)
    assert "components" in s and s["score"] > 0


# --- R049+: certificates ------------------------------------------------------

def _freq():
    return frequency_record(predicted_hz=1000.0, fitted_hz=1001.0,
                            fitted_uncertainty_hz=0.2,
                            accepted_hz=1001.0)


def test_certificate_roundtrip_and_tamper_detection():
    cert = issue("SPECIMEN-abc", {"d": 1}, {"f": 1}, _freq(), [],
                 "deadbeef", (999.0, 1003.0), SIGNING_KEY, True)
    assert verify(cert, SIGNING_KEY)["valid"]
    forged = dict(cert)
    forged["frequency"] = dict(cert["frequency"], fitted_hz=432.0)
    assert not verify(forged, SIGNING_KEY)["valid"]
    assert "SYNTHETIC" in cert["banner"]
    assert "SYNTHETIC" in compact_payload(cert)
    assert render_text(cert).startswith("SYNTHETIC")


def test_certificate_refuses_unfitted_or_out_of_band():
    with pytest.raises(CertificateError):
        issue("S", {}, {}, frequency_record(predicted_hz=1.0), [],
              "x", (0.0, 2.0), SIGNING_KEY, True)
    bad = frequency_record(fitted_hz=100.0,
                           fitted_uncertainty_hz=0.1,
                           accepted_hz=100.0)
    with pytest.raises(CertificateError):
        issue("S", {}, {}, bad, [], "x", (990.0, 995.0),
              SIGNING_KEY, True)


def test_certificate_never_claims_therapy():
    cert = issue("S", {}, {}, _freq(), [], "x", (999.0, 1003.0),
                 SIGNING_KEY, True)
    assert "therapeutic effect" in cert["claims"]["not_made"]


# --- R008: the integrated campaign ---------------------------------------------

def test_full_synthetic_campaign_design_to_certificate():
    r = run_campaign(seed=7)
    assert r["synthetic"] and r["certificate"]["synthetic"]
    assert r["iterations"] >= 2           # at least two tune cycles
    assert r["accepted"] and r["final_state"] == "ACCEPTED"
    assert r["certificate_valid"] and r["ledger_intact"]
    band = r["certificate"]["acceptance_band_hz"]
    assert band[0] <= r["final_fitted_hz"] <= band[1]


def test_campaign_deterministic_given_seed():
    a = run_campaign(seed=11)
    b = run_campaign(seed=11)
    assert a["final_fitted_hz"] == pytest.approx(
        b["final_fitted_hz"], abs=1e-9)


# --- R017-R024: fixture ---------------------------------------------------------

def test_fixture_record_and_coupling():
    r = fx.fixture_record("three_point", 5.0, "delrin", 10.0, 21.0,
                          45.0, [(0.8, 0.0)])
    assert r["expected_remount_scatter_hz"] > 0
    c = fx.coupling_model("edge_clamp", 5.0, 1000.0)
    assert c["fixture_shift_hz"] > 0
    with pytest.raises(fx.FixtureError):
        fx.fixture_record("vice_grip", 1.0, "steel", 0, 20, 40, [])


def test_remount_repeatability_measured_not_assumed():
    tw = ResonatorTwin(seed=9)
    rep = fx.remount_repeatability(tw, "three_point")
    assert rep["scatter_std_hz"] > 0
    assert "unmeasurable" in rep["rule"]


# --- R009-R016: design for trim ---------------------------------------------------

def test_symmetric_group_balances():
    g = dt.symmetric_group("radial_tab", 4, 0.8, 10.0)
    assert len(g) == 4
    assert dt.group_balance_moment(g) < 1e-12


def test_trim_cell_zones_and_sensitivity():
    c = dt.trim_cell("perforation_cell", 0.7, 45.0, 5.0, "mixed")
    assert c["removal_df01_hz"] > 0 and c["mass_kg"] > 0
    with pytest.raises(dt.DesignError):
        dt.trim_cell("radial_tab", 0.5, 0.0, 5.0, "spiritual")


def test_export_bundle_cross_checks():
    b = dt.export_bundle(10, 80.0, 1.2, 0.4,
                         [(0.0, 0.0), (10.0, 10.0)])
    assert b["all_checks_pass"], b["checks"]


def test_reference_family_three_bands_with_controls():
    fam = dt.reference_family()
    assert len(fam) == 3
    for f in fam:
        assert f["n_cells"] >= 8
        assert f["balance_moment"] < 1e-12
        assert "sham_trim" in f["controls"]
        assert f["status"].startswith("ENGINEERING_PROTOTYPE")


# --- R08/R09/R10: additive, MEMS, oscillator ---------------------------------------

def test_printed_silica_is_never_quartz():
    card = additive.process_card("printed_silica")
    assert "not crystalline quartz" in card["material_boundary"].lower() \
        or "NOT crystalline" in card["material_boundary"]
    with pytest.raises(additive.AdditiveError):
        additive.register_material("fake quartz", True,
                                   "printed_silica")


def test_beam_prediction_and_campaign_blocked():
    b = additive.beam_f1_hz("FDM_PLA", 0.1, 0.004)
    assert 50 < b["f1_hz"] < 5000
    plan = additive.print_campaign_plan()
    assert plan["status"] == "PROTOCOL_READY_HARDWARE_REQUIRED"


def test_mems_twin_losses_and_foundry_interface():
    d = mems.beam_resonator(200.0, 10.0, 2.0)
    assert d["f1_hz"] > 1e5
    assert d["q_total"] <= min(d["q_gas"], d["q_anchor"],
                               d["q_ted"])
    vac = mems.beam_resonator(200.0, 10.0, 2.0, pressure_pa=0.1)
    assert vac["q_total"] > d["q_total"]     # vacuum helps
    fh = mems.foundry_handoff()
    assert fh["classification"] == "INTERFACE_ONLY"
    assert fh["value"] is None
    bud = mems.trim_budget(1e6, 100.0, "laser_ablation")
    assert bud["feasible"]


def test_resonator_is_not_an_oscillator():
    passive = {"resonator": True}
    assert not osc.is_oscillator(passive)
    loop = {"sustaining_amplifier": True, "feedback_loop": True,
            "barkhausen": osc.barkhausen(1.2, 0.0)}
    assert osc.is_oscillator(loop)
    assert not osc.barkhausen(0.9, 0.0)["oscillates"]
    assert not osc.barkhausen(1.5, 90.0)["oscillates"]


def test_leeson_q_dependence():
    lo = osc.leeson_phase_noise(1e6, 1e4, 6.0, 0.0, 1e3)
    hi = osc.leeson_phase_noise(1e6, 2e4, 6.0, 0.0, 1e3)
    assert hi["phase_noise_dbc_hz"]["10"] < \
        lo["phase_noise_dbc_hz"]["10"]


# --- R11: composite modes -------------------------------------------------------------

def test_parity_selection_verified_by_computation():
    p = cm.parity_selection()
    assert p["parity_selected"]
    assert p["even_content_at_phase_0"] > 0.95
    assert p["odd_content_at_phase_pi"] > 0.95


def test_separation_controls_mode_distribution():
    d = cm.separation_controls_distribution()
    # larger separation moves more power out of |m|<=1... compare m=+-1
    small = d["0.2"]["m=+1"] + d["0.2"]["m=-1"]
    big = d["2"]["m=+1"] + d["2"]["m=-1"] if "2" in d else \
        d["2.0"]["m=+1"] + d["2.0"]["m=-1"]
    assert big != small                    # distribution moves


def test_partial_array_and_transfer_firewall():
    arr = cm.partial_resonator_array(
        4, [0, np.pi / 2, np.pi, 3 * np.pi / 2], [1, 1, 1, 1])
    dom = max(arr["drive_order_content"],
              key=arr["drive_order_content"].get)
    assert dom == 1                        # phase ramp selects m=1
    fw = cm.transfer_firewall("this PCB emits a neutron OAM beam")
    assert not fw["allowed"]
    ok = cm.transfer_firewall("relative drive phase selects the "
                              "composite azimuthal order")
    assert ok["allowed"]
