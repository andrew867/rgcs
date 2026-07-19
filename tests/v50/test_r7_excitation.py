"""P05 — non-contact excitation and self-oscillation firewall."""

from __future__ import annotations

import math

import pytest

import r7
from r7 import excitation as EX


# --- loop gain --------------------------------------------------------

def test_loop_gain_rejects_bad_inputs():
    with pytest.raises(ValueError):
        EX.LoopGain(0.0, 1.0, 0.0)
    with pytest.raises(ValueError):
        EX.LoopGain(1e6, -1.0, 0.0)


def test_loop_gain_cartesian_components():
    g = EX.LoopGain(1e6, 2.0, 0.0)
    assert g.real == pytest.approx(2.0)
    assert g.imag == pytest.approx(0.0, abs=1e-12)
    assert g.as_record()["evidence_class"] == "SYNTHETIC_MODEL"


def test_phase_error_is_measured_from_the_nearest_multiple_of_2pi():
    assert EX.phase_error_rad(0.0) == pytest.approx(0.0)
    assert EX.phase_error_rad(2 * math.pi) == pytest.approx(0.0,
                                                            abs=1e-12)
    assert EX.phase_error_rad(-4 * math.pi) == pytest.approx(0.0,
                                                             abs=1e-12)
    assert EX.phase_error_rad(math.pi) == pytest.approx(math.pi)


# --- Barkhausen needs BOTH -------------------------------------------

def test_barkhausen_satisfied_needs_both():
    r = EX.barkhausen_check(1.5, 0.0)
    assert r["gain_condition_met"] is True
    assert r["phase_condition_met"] is True
    assert r["oscillates"] is True
    assert r["conditions_required"] == "BOTH"


def test_gain_alone_does_not_oscillate():
    """|A*beta| = 50 is useless at 90 degrees of phase error."""
    r = EX.barkhausen_check(50.0, math.pi / 2)
    assert r["gain_condition_met"] is True
    assert r["phase_condition_met"] is False
    assert r["oscillates"] is False
    assert "phase" in r["note"]


def test_phase_alone_does_not_oscillate():
    """Perfect phase with |A*beta| = 0.9 still decays."""
    r = EX.barkhausen_check(0.9, 0.0)
    assert r["gain_condition_met"] is False
    assert r["phase_condition_met"] is True
    assert r["oscillates"] is False


def test_neither_condition_met():
    r = EX.barkhausen_check(0.1, math.pi)
    assert r["oscillates"] is False
    assert "neither" in r["note"]


def test_unity_gain_is_the_boundary():
    assert EX.barkhausen_check(1.0, 0.0)["oscillates"] is True
    assert EX.barkhausen_check(0.999999, 0.0)["oscillates"] is False


def test_barkhausen_rejects_bad_inputs():
    with pytest.raises(ValueError):
        EX.barkhausen_check(-1.0, 0.0)
    with pytest.raises(ValueError):
        EX.barkhausen_check(1.0, 0.0, phase_tol_rad=-0.1)


# --- the condition registry ------------------------------------------

EXPECTED_CONDITIONS = {
    "HANDHELD_STRAIN_AND_CHARGE",
    "FREE_SUSPENSION",
    "SOFT_SUPPORT",
    "ELECTROSTATIC_DRIVE",
    "MAGNETIC_COIL_DRIVE",
    "ACOUSTIC_AIRBORNE",
    "ULTRASONIC_NONCONTACT",
    "OPTICAL_PHOTOTHERMAL_OR_RADIATION_PRESSURE",
    "ACTIVE_ELECTRICAL_FEEDBACK",
    "ACTIVE_ACOUSTIC_FEEDBACK",
    "SHAM",
}


def test_every_contract_condition_is_present():
    assert set(EX.EXCITATION_CONDITIONS) == EXPECTED_CONDITIONS
    assert EX.condition_registry()["n_conditions"] == 11


def test_only_active_conditions_can_close_a_loop():
    closers = EX.condition_registry()["can_close_a_loop"]
    assert closers == ["ACTIVE_ACOUSTIC_FEEDBACK",
                       "ACTIVE_ELECTRICAL_FEEDBACK"]
    for name in closers:
        assert name.startswith("ACTIVE_")


def test_passive_conditions_supply_no_energy():
    for name in ("FREE_SUSPENSION", "SOFT_SUPPORT", "SHAM"):
        c = EX.EXCITATION_CONDITIONS[name]
        assert c.supplies_energy is False
        assert c.can_close_loop is False
        assert c.coupling_efficiency == 0.0


def test_every_condition_states_a_coupling_basis():
    for name, c in EX.EXCITATION_CONDITIONS.items():
        assert c.coupling_basis, name
        assert c.note, name


def test_coupling_orders_span_many_decades():
    orders = [c.coupling_order for c in EX.EXCITATION_CONDITIONS.values()
              if c.coupling_efficiency > 0]
    assert max(orders) - min(orders) >= 6


def test_optical_drive_is_the_weakest():
    weakest = min(
        (c for c in EX.EXCITATION_CONDITIONS.values()
         if c.coupling_efficiency > 0),
        key=lambda c: c.coupling_efficiency)
    assert weakest.name == "OPTICAL_PHOTOTHERMAL_OR_RADIATION_PRESSURE"


def test_air_to_quartz_impedance_mismatch_is_four_orders():
    reg = EX.condition_registry()
    assert reg["acoustic_impedance_ratio_air_to_quartz"] > 1e4
    assert reg["airborne_intensity_transmission"] < 1e-3


# --- classification ---------------------------------------------------

def test_active_feedback_with_both_conditions_self_oscillates():
    r = EX.classify("ACTIVE_ELECTRICAL_FEEDBACK", 2.0, 0.0, False)
    assert r["status"] == "ACTIVE_SELF_OSCILLATION"
    assert "amplifier" in r["reason"]


def test_active_feedback_with_only_gain_is_a_forced_response():
    r = EX.classify("ACTIVE_ELECTRICAL_FEEDBACK", 2.0, math.pi / 2,
                    False)
    assert r["status"] == "FORCED_RESPONSE"


def test_a_passive_condition_meeting_both_conditions_is_refused():
    r = EX.classify("FREE_SUSPENSION", 2.0, 0.0, False)
    assert r["status"] == "PASSIVE_SELF_OSCILLATION_CLAIM_REFUSED"


def test_free_suspension_with_no_drive_rings_down():
    r = EX.classify("FREE_SUSPENSION", 0.0, 0.0, False)
    assert r["status"] == "RINGDOWN"


def test_non_contact_drives_give_a_forced_response():
    for name in ("ELECTROSTATIC_DRIVE", "MAGNETIC_COIL_DRIVE",
                 "ACOUSTIC_AIRBORNE", "ULTRASONIC_NONCONTACT",
                 "OPTICAL_PHOTOTHERMAL_OR_RADIATION_PRESSURE"):
        r = EX.classify(name, 0.2, 0.0, False)
        assert r["status"] == "FORCED_RESPONSE", name


def test_sham_with_nothing_applied_rings_down():
    assert EX.classify("SHAM", 0.0, 0.0, False)["status"] == "RINGDOWN"


def test_classify_rejects_an_unknown_condition():
    with pytest.raises(ValueError):
        EX.classify("TELEKINESIS", 1.0, 0.0, False)


def test_every_status_is_a_declared_status():
    for name in EX.EXCITATION_CONDITIONS:
        for gain in (0.0, 0.5, 2.0):
            for phase in (0.0, math.pi / 2):
                for contact in (True, False):
                    r = EX.classify(name, gain, phase, contact)
                    assert r["status"] in r7.EXCITATION_STATUSES


# --- the hand-held condition -----------------------------------------

def test_handheld_never_reaches_active_self_oscillation():
    """The whole point. A passive specimen in a hand cannot get there."""
    for gain in (0.0, 0.5, 0.999, 1.0, 2.0, 100.0):
        for phase in (0.0, 0.5, math.pi / 2, math.pi, 2 * math.pi):
            for contact in (True, False):
                r = EX.classify("HANDHELD_STRAIN_AND_CHARGE", gain,
                                phase, contact)
                assert r["status"] != "ACTIVE_SELF_OSCILLATION"


def test_handheld_with_contact_is_contact_loading_dominant():
    r = EX.classify("HANDHELD_STRAIN_AND_CHARGE", 0.3, 0.0, True)
    assert r["status"] == "CONTACT_LOADING_DOMINANT"


def test_handheld_without_contact_is_a_forced_response():
    r = EX.classify("HANDHELD_STRAIN_AND_CHARGE", 0.3, 0.0, False)
    assert r["status"] == "FORCED_RESPONSE"


def test_handheld_analysis_lists_supported_and_unsupported_statuses():
    hh = EX.handheld_analysis()
    assert "CONTACT_LOADING_DOMINANT" in \
        hh["statuses_this_condition_can_support"]
    assert "FORCED_RESPONSE" in \
        hh["statuses_this_condition_can_support"]
    assert hh["statuses_this_condition_cannot_support"] == \
        ["ACTIVE_SELF_OSCILLATION"]


def test_handheld_analysis_names_all_three_energy_inputs():
    inputs = EX.handheld_analysis()["energy_inputs"]
    assert set(inputs) == {"physiological_tremor",
                           "triboelectric_and_contact_charge",
                           "thermal_drift"}
    assert inputs["physiological_tremor"]["band_hz"] == [8.0, 12.0]


def test_contact_destroys_q_by_orders_of_magnitude():
    hh = EX.handheld_analysis()
    assert hh["q_hand_held"] < hh["q_free_suspension"]
    assert hh["q_reduction_orders_of_magnitude"] >= 3.0
    assert hh["ringdown_tau_handheld_s"] < hh["ringdown_tau_free_s"]


def test_the_discriminating_experiment_predicts_opposite_signs():
    text = EX.handheld_analysis()["discriminating_experiment"]
    assert "RISE" in text
    assert "falls" in text


# --- the central refusal ---------------------------------------------

def test_passive_self_oscillation_is_refused():
    with pytest.raises(EX.ExcitationRefused):
        EX.refuse_passive_self_oscillation()


def test_the_refusal_explains_ringdown_and_the_energy_inputs():
    with pytest.raises(EX.ExcitationRefused) as exc:
        EX.refuse_passive_self_oscillation()
    msg = str(exc.value)
    assert "ring down" in msg
    assert "tremor" in msg
    assert "triboelectric" in msg
    assert "thermal drift" in msg


def test_a_passive_resonator_cannot_self_oscillate():
    assert EX.passive_resonator_can_self_oscillate() is False


# --- ringdown ---------------------------------------------------------

def test_ringdown_starts_at_unity_and_decays_monotonically():
    assert EX.ringdown(1e5, 1e6, 0.0) == pytest.approx(1.0)
    prev = 1.0
    for i in range(1, 20):
        a = EX.ringdown(1e5, 1e6, i * 1e-3)
        assert a < prev
        prev = a
    assert prev < 1.0


def test_higher_q_decays_more_slowly():
    t = 1e-3
    assert EX.ringdown(1e6, 1e6, t) > EX.ringdown(1e2, 1e6, t)


def test_ringdown_matches_the_closed_form():
    assert EX.ringdown(1000.0, 1e6, 1e-4) == \
        pytest.approx(math.exp(-math.pi * 1e6 * 1e-4 / 1000.0))


def test_time_to_decay_scales_linearly_with_q():
    t1 = EX.time_to_decay(1e4, 1e6, 0.5)
    t2 = EX.time_to_decay(2e4, 1e6, 0.5)
    assert t2 == pytest.approx(2.0 * t1)


def test_time_to_decay_inverts_ringdown():
    t = EX.time_to_decay(5e4, 1e6, 0.1)
    assert EX.ringdown(5e4, 1e6, t) == pytest.approx(0.1)


def test_ringdown_and_time_to_decay_reject_bad_inputs():
    with pytest.raises(ValueError):
        EX.ringdown(0.0, 1e6, 1.0)
    with pytest.raises(ValueError):
        EX.ringdown(1e5, 0.0, 1.0)
    with pytest.raises(ValueError):
        EX.ringdown(1e5, 1e6, -1.0)
    with pytest.raises(ValueError):
        EX.time_to_decay(1e5, 1e6, 0.0)
    with pytest.raises(ValueError):
        EX.time_to_decay(1e5, 1e6, 1.0)
    with pytest.raises(ValueError):
        EX.time_to_decay(-1.0, 1e6, 0.5)


# --- house rules ------------------------------------------------------

def test_no_forbidden_state_appears_in_the_module():
    with open(EX.__file__, encoding="utf-8") as fh:
        text = fh.read()
    for state in r7.FORBIDDEN_STATES:
        assert state not in text, state


def test_every_returned_dict_carries_an_evidence_class():
    records = [
        EX.LoopGain(1e6, 1.0, 0.0).as_record(),
        EX.barkhausen_check(1.0, 0.0),
        EX.condition_registry(),
        EX.EXCITATION_CONDITIONS["SHAM"].as_record(),
        EX.classify("SHAM", 0.0, 0.0, False),
        EX.handheld_analysis(),
        EX.status_report(),
    ]
    for rec in records:
        assert rec["evidence_class"] in ("SYNTHETIC_MODEL",
                                         "DERIVED_ARITHMETIC")


def test_status_report_is_deterministic_and_refuses_the_claim():
    rep = EX.status_report()
    assert rep == EX.status_report()
    assert rep["status"] == "PASSIVE_SELF_OSCILLATION_CLAIM_REFUSED"
    assert rep["gain_only_oscillates"] is False
    assert rep["phase_only_oscillates"] is False


def test_the_module_says_nothing_is_bench_data():
    assert "Nothing here is bench data" in EX.__doc__
    assert "No crystal has been" in EX.handheld_analysis()["provenance"]
