"""P08 — R7 bench hardware, priority, hazards, dual-use policy."""

from __future__ import annotations

import pytest

import r7
from r7 import benchr7 as B


# --- 1. the experiment registry --------------------------------------

EXPECTED_IDS = {
    "CLOCK_LINK_BASELINE",
    "CLOCK_LINK_INDEPENDENT",
    "CRYSTAL_ALIGNMENT",
    "NONCONTACT_EXCITATION",
    "DIRECTIONAL_FIELD_MAP",
    "FORCE_NULL",
}


def test_the_r7_experiment_set_is_present():
    assert set(B.EXPERIMENTS) == EXPECTED_IDS


def test_registry_keys_match_experiment_ids():
    for key, e in B.EXPERIMENTS.items():
        assert key == e.id


def test_every_experiment_is_fully_specified():
    for e in B.EXPERIMENTS.values():
        assert len(e.tests) > 40, e.id
        assert len(e.hardware) >= 3, e.id
        assert e.safety_class in B.SAFETY_CLASSES, e.id
        assert isinstance(e.hobbyist_achievable, bool), e.id
        assert e.claim_ceiling, e.id
        assert len(e.score_rationale) > 40, e.id


def test_cost_bands_are_ordered_and_positive():
    for e in B.EXPERIMENTS.values():
        assert 0 < e.cost_low_usd <= e.cost_high_usd, e.id
        assert e.cost_low_usd <= e.cost_mid_usd <= e.cost_high_usd, e.id


def test_cost_basis_is_labelled_catalogue_class():
    for e in B.EXPERIMENTS.values():
        assert "catalogue-class" in e.as_record()["cost_basis"], e.id


def test_geometric_mean_is_used_for_the_midpoint():
    """An arithmetic mean of a wide band sits too near the top of it."""
    e = B.EXPERIMENTS["FORCE_NULL"]
    arithmetic = (e.cost_low_usd + e.cost_high_usd) / 2.0
    assert e.cost_mid_usd < arithmetic


def test_invalid_experiments_are_rejected():
    kw = dict(id="X", tests="t", hardware=("a",), cost_low_usd=1.0,
              cost_high_usd=2.0, safety_class="BENIGN_LOW_VOLTAGE",
              hobbyist_achievable=True, information_score=1.0,
              score_rationale="r", claim_ceiling="c")
    with pytest.raises(ValueError):
        B.Experiment(**{**kw, "safety_class": "TOTALLY_SAFE"})
    with pytest.raises(ValueError):
        B.Experiment(**{**kw, "information_score": 99.0})
    with pytest.raises(ValueError):
        B.Experiment(**{**kw, "cost_low_usd": 10.0,
                        "cost_high_usd": 2.0})


def test_the_clock_experiments_are_hobbyist_achievable():
    assert B.EXPERIMENTS["CLOCK_LINK_BASELINE"].hobbyist_achievable
    assert B.EXPERIMENTS["CLOCK_LINK_INDEPENDENT"].hobbyist_achievable


def test_the_expensive_experiments_are_not():
    for k in ("CRYSTAL_ALIGNMENT", "NONCONTACT_EXCITATION",
              "FORCE_NULL"):
        assert not B.EXPERIMENTS[k].hobbyist_achievable, k


def test_baseline_is_the_cheapest_experiment():
    cheapest = min(B.EXPERIMENTS.values(), key=lambda e: e.cost_mid_usd)
    assert cheapest.id == "CLOCK_LINK_BASELINE"


# --- 2. readiness -----------------------------------------------------

def test_readiness_reports_not_ready():
    r = B.readiness()
    assert r["ready_for_bench"] is False
    assert r["status"] == "SOFTWARE_COMPLETE_PHYSICALLY_UNTESTED"
    assert r["gates_open"] < r["gates_total"]


def test_hardware_gates_are_shut_because_r7_owns_no_hardware():
    missing = B.readiness()["gates_missing"]
    for gate in ("CALIBRATION_PLAN", "SAFETY_REVIEW",
                 "OPERATOR_COMPETENCE"):
        assert gate in missing, gate


def test_gate_vocabulary_is_r6s():
    """The gates did not get easier between programmes."""
    from r6.bench import READINESS_GATES as R6_GATES
    assert B.READINESS_GATES == R6_GATES


def test_every_gate_has_evidence_or_an_absence_note():
    a = B.current_assessment()
    for gate in B.READINESS_GATES:
        assert gate in a.evidence, gate
    for gate in a.missing():
        note = a.evidence[gate]
        assert note.startswith(("ABSENT", "PARTIAL")), gate


def test_nothing_owned_and_nothing_measured():
    r = B.readiness()
    assert r["instruments_owned"] == 0
    assert r["calibration_certificates_held"] == 0
    assert r["measurements_taken"] == 0


def test_readiness_statement_disclaims_the_physical_world():
    assert "says nothing whatsoever about the physical world" in \
        B.readiness()["statement"]


def test_assessment_record_round_trips():
    rec = B.current_assessment().as_record()
    assert rec["ready"] is False
    assert set(rec["gates_open"]) | set(rec["missing"]) == \
        set(B.READINESS_GATES)


# --- 3. priority ------------------------------------------------------

def test_clock_link_baseline_ranks_first():
    """The R6 closing recommendation, carried forward and justified."""
    rank = B.priority_ranking()
    assert rank["ranking"][0] == "CLOCK_LINK_BASELINE"
    assert rank["top"] == "CLOCK_LINK_BASELINE"


def test_independent_comparison_ranks_second():
    assert B.priority_ranking()["ranking"][1] == \
        "CLOCK_LINK_INDEPENDENT"


def test_force_null_ranks_last():
    assert B.priority_ranking()["ranking"][-1] == "FORCE_NULL"


def test_ranking_covers_every_experiment_exactly_once():
    order = B.priority_ranking()["ranking"]
    assert sorted(order) == sorted(EXPECTED_IDS)
    assert len(set(order)) == len(order)


def test_ranking_is_monotonic_in_the_metric():
    rows = B.priority_ranking()["rows"]
    values = [r["information_per_kilodollar"] for r in rows]
    assert values == sorted(values, reverse=True)
    assert [r["rank"] for r in rows] == list(range(1, len(rows) + 1))


def test_the_margin_is_large_enough_to_be_robust():
    rank = B.priority_ranking()
    assert rank["margin_over_second"] > 3.0
    assert rank["margin_over_last"] > 50.0


def test_metric_is_recomputable_by_hand():
    e = B.EXPERIMENTS["CLOCK_LINK_BASELINE"]
    expected = e.information_score / (
        (e.cost_low_usd * e.cost_high_usd) ** 0.5 / 1000.0)
    assert e.information_per_kilodollar == pytest.approx(expected)


def test_ranking_is_deterministic_across_calls():
    assert B.priority_ranking()["ranking"] == \
        B.priority_ranking()["ranking"]


def test_ranking_declares_its_inputs_are_judgements():
    rank = B.priority_ranking()
    assert rank["metric_inputs_are_judgements"] is True
    assert "robustness" in rank


def test_justification_names_the_sequencing_argument():
    rank = B.priority_ranking()
    assert "CLOCK_LINK_INDEPENDENT" in rank["justification"]
    assert "interpret" in rank["justification"]
    assert "not the only ordering" in rank["sequencing_note"]


def test_ranking_says_none_have_been_run():
    assert B.priority_ranking()["none_of_these_have_been_run"] is True


def test_ties_break_on_id_not_on_insertion_order():
    """No Python hash and no dict order in the sort key."""
    import inspect
    src = inspect.getsource(B.priority_ranking)
    assert 'r["id"]' in src
    assert "hash(" not in src


# --- 4. hazards -------------------------------------------------------

def test_r7_hazards_are_present():
    for h in ("HIGH_VOLTAGE_PULSE", "RF_EMISSION", "OPTICAL",
              "ULTRASONIC", "MECHANICAL_FRACTURE",
              "MAINS_CONSTRUCTION"):
        assert h in B.HAZARDS, h


def test_biological_exposure_is_refused_entirely():
    bio = B.HAZARDS["BIOLOGICAL_EXPOSURE"]
    assert bio["status"] == "REFUSED_ENTIRELY"
    assert bio["control"] == "none offered"


def test_mains_work_requires_a_qualified_person():
    assert B.HAZARDS["MAINS_CONSTRUCTION"]["status"] == \
        "REFUSED_UNLESS_QUALIFIED"


def test_every_hazard_has_a_description_control_and_status():
    for name, h in B.HAZARDS.items():
        assert len(h["description"]) > 20, name
        assert h["control"], name
        assert h["status"], name


def test_refused_hazards_are_surfaced_in_readiness():
    refused = B.readiness()["hazards_refused"]
    assert "BIOLOGICAL_EXPOSURE" in refused
    assert "MAINS_CONSTRUCTION" in refused


def test_vacuum_hazard_is_declared_because_force_null_needs_vacuum():
    assert "VACUUM_IMPLOSION" in B.HAZARDS
    assert B.EXPERIMENTS["FORCE_NULL"].safety_class == \
        "CONTROLLED_VACUUM"


def test_the_hazard_table_is_not_called_a_safety_review():
    assert "self-assessment" in \
        B.current_assessment().evidence["SAFETY_REVIEW"]


# --- 5. dual use ------------------------------------------------------

def test_permitted_topics_match_core_10():
    p = B.dual_use_policy()["may_discuss"]
    for topic in ("CLOCKS", "NAVIGATION", "QUARTZ_PHYSICS",
                  "SIGNAL_PROCESSING", "OPEN_METROLOGY",
                  "SCIENTIFIC_NULLS", "LOW_POWER_APPARATUS"):
        assert topic in p, topic


def test_prohibited_optimizations_match_core_10():
    q = B.dual_use_policy()["must_not_optimize"]
    for item in ("WEAPON_GUIDANCE", "TARGETING",
                 "EMITTER_GEOLOCATION_FOR_ATTACK",
                 "ELECTRONIC_WARFARE", "HIGH_POWER_DIRECTED_ENERGY",
                 "HAZARDOUS_BIOLOGICAL_EXPOSURE",
                 "UNCONTROLLED_LASERS_RF_VOLTAGE_VACUUM_OR_PRESSURE"):
        assert item in q, item


def test_weaponization_assistance_is_refused():
    with pytest.raises(B.BenchRefused) as e:
        B.refuse_weaponization_assistance(purpose="defensive research")
    msg = str(e.value)
    assert "weapon guidance" in msg
    assert "unconditional" in msg
    assert "does not depend on who is asking" in msg


def test_military_relevance_is_context_not_endorsement():
    d = B.dual_use_policy()
    assert "prior context" in d["military_relevance"]
    assert "not an endorsement" in d["military_relevance"]


def test_policy_points_at_its_own_enforcement():
    d = B.dual_use_policy()
    assert "refuse_weaponization_assistance" in d["enforcement"]
    assert "watt-scale or below" in d["power_ceiling_note"]


# --- 6. honest stop ---------------------------------------------------

def test_honest_stop_produced_no_measurement():
    s = B.honest_stop()
    assert s["measurements_taken"] == 0
    assert s["instruments_owned"] == 0
    assert s["ready_for_bench"] is False
    assert "It produced no measurement" in s["statement"]


def test_honest_stop_lists_what_was_not_produced():
    s = B.honest_stop()
    for item in ("any measurement", "any calibrated instrument",
                 "any force reading", "any independent replication"):
        assert item in s["not_produced"], item


def test_next_real_step_is_the_clock_link_baseline():
    s = B.honest_stop()
    assert s["next_real_step"].startswith("CLOCK_LINK_BASELINE")
    assert "splitter" in s["next_real_step"]


def test_a_negative_baseline_is_a_result_not_a_failure():
    s = B.honest_stop()
    assert "a result, not" in s["what_would_end_the_programme"]


# --- 7. programme hygiene --------------------------------------------

def test_no_forbidden_state_strings_appear():
    import inspect
    src = inspect.getsource(B)
    for s in r7.FORBIDDEN_STATES:
        assert s not in src, s


def test_module_is_not_named_bench():
    """It must not collide with or shadow r6.bench."""
    import r6.bench
    assert B.__name__ == "r7.benchr7"
    assert B is not r6.bench
