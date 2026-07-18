"""P05/P06 (A18-A29): optical screening, water physics, preregistered
experiments, spacetime metrology, energy audit, and the two firewalls.

The relativistic code is validated against two published measurements
(Pound-Rebka and the GPS clock correction) so it is checked against the
world, not against itself.
"""
from __future__ import annotations

import math

import pytest


# --- A20 water ----------------------------------------------------------

def test_water_debye_peak_is_near_19_ghz_not_2_45():
    from cspc.experiments import water_loss_peak_hz
    peak = water_loss_peak_hz()
    assert 1.8e10 < peak < 2.1e10          # ~19 GHz
    assert peak / 2.45e9 > 5               # far above the ISM band


def test_2g45_is_corrected_quantitatively_not_just_asserted():
    from cspc.experiments import water_2g45_correction
    c = water_2g45_correction()
    assert c["is_a_resonance"] is False
    assert c["status"] == "CORRECTED"
    assert 0.1 < c["loss_at_2g45_relative_to_peak"] < 0.5
    assert "relaxation" in c["correction"].lower()


def test_debye_loss_is_maximal_at_omega_tau_equals_one():
    from cspc.experiments import debye_water, water_loss_peak_hz
    peak = water_loss_peak_hz()
    at_peak = debye_water(peak)["eps_imag"]
    assert abs(debye_water(peak)["omega_tau"] - 1.0) < 1e-9
    for f in (peak / 4, peak / 2, peak * 2, peak * 4):
        assert debye_water(f)["eps_imag"] < at_peak


# --- A18 optical --------------------------------------------------------

def test_optical_candidate_has_no_implemented_coupling_mechanism():
    from cspc.experiments import optical_candidate_screening
    s = optical_candidate_screening()
    assert s["status"] == "UNSUPPORTED"
    assert s["implemented_here"] is False
    assert s["firewall"] == "OPTICAL_FREQUENCY_TO_PHOTON_CONVERSION"
    assert 30 < s["octaves_between"] < 40


def test_acousto_optic_reality_is_sidebands_not_conversion():
    from cspc.experiments import optical_candidate_screening
    s = optical_candidate_screening()
    assert "sideband" in s["what_acousto_optics_actually_does"].lower()


# --- A21/A24 preregistration --------------------------------------------

def test_fold_experiment_has_mandatory_neighbour_controls():
    from cspc.experiments import low_frequency_fold_experiment
    p = low_frequency_fold_experiment()
    assert len(p.control_hz) >= 5
    vals = {float(c) for c in p.control_hz}
    assert 18.0 in vals and 20.48 in vals


def test_experiments_are_plans_with_no_apparatus_or_data():
    from cspc.experiments import compile_experiments
    c = compile_experiments()
    assert c["apparatus_status"] == "NOT BUILT"
    assert c["data_status"] == "NO DATA COLLECTED"
    assert c["physical_status"] == "UNTESTED"
    for p in c["experiments"].values():
        assert "PLAN ONLY" in p["claim_boundary"]


def test_preregistration_fixes_stopping_rule_and_blinding():
    from cspc.experiments import REGISTERED_EXPERIMENTS
    for f in REGISTERED_EXPERIMENTS.values():
        p = f()
        assert "no interim peeking" in p.stopping_rule or \
            "no extension" in p.stopping_rule
        assert "blind" in p.blinding.lower()
        assert p.correction


def test_optical_plan_treats_stock_laser_as_a_control_not_the_target():
    from cspc.experiments import optical_detuning_experiment
    p = optical_detuning_experiment()
    assert p.target_hz[0] != p.control_hz[0]
    assert any("thermal control" in s for s in p.safety)


# --- A25 operational definitions ----------------------------------------

def test_phase_and_proper_time_are_defined_separately():
    from cspc.spacetime import OPERATIONAL_DEFINITIONS
    d = OPERATIONAL_DEFINITIONS
    assert d["phase"]["resonator_can_change_it"].startswith("YES")
    assert d["transport"]["resonator_can_change_it"].startswith("no")
    assert d["coordinate_time"]["measured_by"] == "nothing; it is " \
                                                  "bookkeeping"


def test_definition_firewalls_block_the_tempting_chain():
    from cspc.spacetime import DEFINITION_FIREWALLS
    pairs = {(a, b) for a, b, _ in DEFINITION_FIREWALLS}
    assert ("phase", "proper_time") in pairs
    assert ("delay", "transport") in pairs


# --- A26 relativistic metrology (validated externally) -------------------

def test_pound_rebka_reproduced():
    """22.5 m tower: published fractional shift ~2.45e-15."""
    from cspc.spacetime import gravitational_redshift_uniform
    got = gravitational_redshift_uniform(22.5)
    assert abs(got - 2.45e-15) / 2.45e-15 < 0.01


def test_gps_clock_offset_reproduced():
    """Published: +45.7 gravitational, -7.2 velocity, net ~+38.5
    us/day."""
    from cspc.spacetime import satellite_clock_offset
    d = satellite_clock_offset(26_560_000.0).to_dict()
    assert abs(d["gravitational_part"] * 86400e6 - 45.7) < 0.5
    assert abs(d["velocity_part"] * 86400e6 + 7.2) < 0.5
    assert abs(d["microseconds_per_day"] - 38.5) < 0.5


def test_resonator_is_a_metric_instrument_not_a_controller():
    from cspc.spacetime import resonator_as_clock_sensitivity
    r = resonator_as_clock_sensitivity(1e-18)
    assert r["capability"] == "MEASUREMENT of the metric"
    assert "generation" in r["not_capability"]
    # an optical clock at 1e-18 resolves centimetres
    assert 1e-3 < r["smallest_resolvable_height_m"] < 1e-1


# --- A27 energy audit ---------------------------------------------------

def test_laboratory_energy_implies_absurdly_small_curvature():
    from cspc.spacetime import energy_audit
    a = energy_audit(100.0, 3600.0)
    assert a["verdict"] == "NEGLIGIBLE"
    # r_s below a proton radius by >20 orders of magnitude
    assert a["orders_of_magnitude_below_proton"] > 20
    # and even below the Planck length
    assert a["ratio_to_planck_length"] < 1.0


def test_energy_audit_scales_correctly():
    from cspc.spacetime import energy_audit
    a = energy_audit(100.0, 3600.0)
    b = energy_audit(200.0, 3600.0)
    assert abs(b["schwarzschild_radius_m"] /
               a["schwarzschild_radius_m"] - 2.0) < 1e-9


# --- A28 time-crystal firewall ------------------------------------------

def test_period_doubling_alone_is_ordinary_nonlinear_dynamics():
    from cspc.spacetime import classify_temporal_observation
    r = classify_temporal_observation(2.0, many_body=False,
                                      robust_to_perturbation=False)
    assert r["classification"] == "ORDINARY_NONLINEAR_SUBHARMONIC"
    assert r["implies_time_travel"] is False


def test_time_crystal_candidate_requires_many_body_rigidity():
    from cspc.spacetime import classify_temporal_observation
    r = classify_temporal_observation(2.0, many_body=True,
                                      robust_to_perturbation=True)
    assert r["classification"] == "TIME_CRYSTAL_CANDIDATE"
    assert r["implies_time_travel"] is False       # still not travel


def test_time_crystal_facts_deny_perpetual_motion_and_travel():
    from cspc.spacetime import TIME_CRYSTAL_FACTS
    nots = " ".join(TIME_CRYSTAL_FACTS["what_it_is_not"]).lower()
    assert "perpetual motion" in nots and "time travel" in nots


# --- A29 travel falsification map ---------------------------------------

def test_every_travel_claim_defaults_unsupported_with_required_evidence():
    from cspc.spacetime import falsification_map
    m = falsification_map()
    assert m["n_supported"] == 0
    assert m["n_claims"] >= 5
    for c in m["claims"]:
        assert c["status"] == "UNSUPPORTED"
        assert c["required_evidence"].strip()
        assert c["why_current_work_does_not_support_it"].strip()


def test_clock_sensitivity_claim_is_refused_by_the_metrology_firewall():
    from cspc.spacetime import TRAVEL_CLAIMS
    c = [t for t in TRAVEL_CLAIMS if t.id == "TRV-004"][0]
    assert "thermometer does not heat the room" in \
        c.why_current_work_does_not_support_it
