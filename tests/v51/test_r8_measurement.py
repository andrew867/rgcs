"""P11 — the clock-link measurement programme.

The tests that matter here are the ones that would catch the module
quietly becoming encouraging: a tier that claims to resolve a metre, a
procedure that stops putting the instrument floor first, an analysis
plan that stops calling itself frozen, or a record that escapes
without its evidence class. Capability is checked by *computing* it
from :mod:`r7.clocklink`, never by asserting a transcribed number.
"""

from __future__ import annotations

import math

import pytest

from r7 import clocklink
from r8 import measurement


# --- bill of materials -------------------------------------------------

def test_three_tiers_exist_and_are_ordered_by_cost():
    assert measurement.TIERS == ("MINIMAL", "STANDARD", "GOOD")
    totals = [measurement.tier_cost(t)["total_usd"]
              for t in measurement.TIERS]
    assert all(a < b for a, b in zip(totals, totals[1:]))


def test_tier_totals_are_summed_not_asserted():
    for tier in measurement.TIERS:
        rec = measurement.tier_cost(tier)
        recomputed = sum(it["qty"] * it["unit_usd"]
                         for it in rec["items"])
        assert rec["total_usd"] == recomputed


def test_tier_totals_land_near_their_nominal_budgets():
    for tier in measurement.TIERS:
        rec = measurement.tier_cost(tier)
        assert rec["within_nominal_budget"]
        assert rec["total_usd"] >= rec["nominal_budget_usd"] * 0.5


def test_prices_are_labelled_estimates_not_quotes():
    for tier in measurement.TIERS:
        basis = measurement.bill_of_materials(tier)["price_basis"]
        assert "NOT_A_QUOTE" in basis
        assert "estimate" in basis.lower()


def test_every_line_item_states_its_role():
    for tier in measurement.TIERS:
        for item in measurement.BOM[tier]["items"]:
            assert item["role"].strip()
            assert item["part"].strip()


@pytest.mark.parametrize("tier", measurement.TIERS)
def test_bom_capability_is_computed_from_r7_not_transcribed(tier):
    """Every resolvable/unresolvable entry must reproduce r7 exactly."""
    spec = measurement.BOM[tier]
    rec = measurement.bill_of_materials(tier)
    for height, row in rec["heights"].items():
        expected = clocklink.height_resolution(
            spec["oscillator"], link=spec["link"],
            target_height_m=height)
        assert row["resolvable"] == expected.resolvable
        assert row["status"] == expected.status
        assert row["combined_floor"] == expected.combined_floor


@pytest.mark.parametrize("tier", measurement.TIERS)
def test_can_and_cannot_partition_the_swept_heights(tier):
    rec = measurement.bill_of_materials(tier)
    can = set(rec["can_resolve_m"])
    cannot = set(rec["cannot_resolve_m"])
    assert not can & cannot
    assert can | cannot == set(measurement.DEFAULT_TARGET_HEIGHTS_M)


def test_minimal_tier_cannot_resolve_one_metre():
    """The R7 flicker-floor result, restated at the cheap end.

    Not a budgeting observation: a TCXO pair's flicker floor sits
    above the 1.09e-16 fractional shift of one metre, so no
    integration time reaches it. The status string must say exactly
    that rather than merely 'not yet'.
    """
    rec = measurement.bill_of_materials("MINIMAL")
    assert not rec["resolves_one_metre"]
    assert 1.0 in rec["cannot_resolve_m"]
    row = rec["heights"][1.0]
    assert row["status"] == "UNRESOLVABLE_AT_ANY_INTEGRATION_TIME"
    assert row["tau_required_s"] is None
    assert row["combined_floor"] > row["target_fractional"]


def test_no_tier_at_all_resolves_one_metre():
    """Including the fifteen-thousand-dollar one."""
    rep = measurement.bom_report()
    assert rep["tiers_resolving_one_metre"] == []
    for tier in measurement.TIERS:
        assert not rep["tiers"][tier]["resolves_one_metre"]


def test_minimum_resolvable_height_inverts_the_r7_floor():
    for tier in measurement.TIERS:
        spec = measurement.BOM[tier]
        h = measurement.minimum_resolvable_height_m(tier)
        floor = clocklink.height_resolution(
            spec["oscillator"], link=spec["link"]).combined_floor
        # the height whose fractional shift equals the floor
        assert clocklink.height_fractional_shift(h) == pytest.approx(
            floor, rel=1e-12)


def test_minimum_resolvable_height_falls_with_tier():
    hs = [measurement.minimum_resolvable_height_m(t)
          for t in measurement.TIERS]
    assert all(a > b for a, b in zip(hs, hs[1:]))


def test_best_tier_reaches_only_hillside_scale():
    """Roughly 130 m, computed. Not a bench, not a building."""
    h = measurement.minimum_resolvable_height_m("GOOD")
    assert 100.0 < h < 200.0
    assert h > 1.0


def test_a_height_a_tier_can_resolve_is_actually_resolvable():
    """The positive direction, so the tests are not all refusals."""
    rec = measurement.bill_of_materials("GOOD")
    assert rec["can_resolve_m"], "GOOD must resolve something"
    for h in rec["can_resolve_m"]:
        assert h > measurement.minimum_resolvable_height_m("GOOD")
        assert rec["heights"][h]["tau_required_s"] is not None


# --- procedure ---------------------------------------------------------

def test_step_one_is_the_common_source_split():
    proc = measurement.procedure()
    assert proc["first_step"] == "COMMON_SOURCE_SPLIT"
    assert proc["steps"][0]["index"] == 1
    assert proc["steps"][0]["prerequisite"] is None


def test_common_source_split_is_first_for_every_tier():
    for tier in measurement.TIERS:
        assert measurement.procedure(tier)["first_step"] == \
            "COMMON_SOURCE_SPLIT"


def test_steps_are_contiguously_indexed_in_order():
    idx = [s.index for s in measurement.PROCEDURE]
    assert idx == list(range(1, len(idx) + 1))


def test_every_prerequisite_precedes_its_step():
    for step in measurement.PROCEDURE:
        if step.prerequisite is not None:
            assert step.prerequisite < step.index


def test_every_step_names_a_specific_number_it_produces():
    for step in measurement.PROCEDURE:
        assert step.produces.strip()
        assert step.measures.strip()
        assert step.rules_out.strip()
        assert step.duration_h > 0


def test_configurations_are_drawn_from_the_r7_vocabulary():
    for step in measurement.PROCEDURE:
        assert step.configuration in clocklink.CONFIGURATIONS


def test_procedure_order_follows_the_r7_configuration_order():
    """R7 declared the order; P11 may subset it but not reorder it."""
    ours = [s.configuration for s in measurement.PROCEDURE]
    ranks = [clocklink.CONFIGURATIONS.index(c) for c in ours]
    assert ranks == sorted(ranks)


def test_sham_follows_the_exposed_arm():
    by_cfg = {s.configuration: s.index for s in measurement.PROCEDURE}
    assert by_cfg["SHAM_INSERTION"] > by_cfg["APPARATUS_IN_TRANSFER_PATH"]


def test_tier_filtering_drops_steps_the_tier_cannot_run():
    minimal = measurement.procedure("MINIMAL")
    assert minimal["n_steps"] < len(measurement.PROCEDURE)
    assert "REAL_HEIGHT_COMPARISON" in minimal["excluded_for_tier"]
    assert measurement.procedure("GOOD")["n_steps"] == \
        len(measurement.PROCEDURE)


def test_total_duration_is_summed_from_the_steps():
    proc = measurement.procedure()
    assert proc["total_duration_h"] == sum(
        s.duration_h for s in measurement.PROCEDURE)
    assert proc["total_duration_days"] == pytest.approx(
        proc["total_duration_h"] / 24.0)


def test_unknown_tier_is_rejected():
    with pytest.raises(ValueError):
        measurement.procedure("PLATINUM")
    with pytest.raises(ValueError):
        measurement.bill_of_materials("FREE")


# --- expected floor ----------------------------------------------------

def test_instrument_floor_falls_as_one_over_tau():
    """White PM, not white FM: slope -1, and that is how you tell."""
    a = measurement._instrument_adev(60e-12, 1.0)
    b = measurement._instrument_adev(60e-12, 100.0)
    assert b == pytest.approx(a / 100.0)


def test_instrument_floor_rejects_nonpositive_tau():
    with pytest.raises(ValueError):
        measurement._instrument_adev(1e-12, 0.0)


@pytest.mark.parametrize("tier", measurement.TIERS)
def test_expected_floor_names_a_dominant_term_at_every_tau(tier):
    rep = measurement.expected_floor(tier)
    for row in rep["rows"]:
        assert row["dominant_term"] in row["terms"]
        assert row["dominant_value"] == max(row["terms"].values())
        assert row["total_adev"] >= row["dominant_value"]


def test_minimal_tier_is_instrument_limited_at_one_second():
    """A 100 ns counter buries a TCXO pair; that is the point of it."""
    rep = measurement.expected_floor("MINIMAL")
    assert rep["instrument_limited_at_1s"]
    assert rep["rows"][0]["dominant_term"] == "COUNTER_WHITE_PM"


def test_good_tier_is_not_instrument_limited_at_one_second():
    rep = measurement.expected_floor("GOOD")
    assert not rep["instrument_limited_at_1s"]
    assert rep["rows"][0]["dominant_term"].startswith("OSCILLATOR")


def test_crossover_time_falls_as_the_counter_improves():
    xs = [measurement.expected_floor(t)["instrument_crossover_tau_s"]
          for t in measurement.TIERS]
    assert all(a > b for a, b in zip(xs, xs[1:]))


def test_asymptotic_floor_matches_the_r7_quadrature_sum():
    for tier in measurement.TIERS:
        spec = measurement.BOM[tier]
        rep = measurement.expected_floor(tier)
        r = clocklink.height_resolution(spec["oscillator"],
                                        link=spec["link"])
        assert rep["asymptotic_floor"] == pytest.approx(
            r.combined_floor, rel=1e-12)


def test_oscillator_white_fm_matches_the_r7_adev_model():
    """The pair terms must be r7's model, times sqrt(2) for two units."""
    tier = "STANDARD"
    spec = measurement.BOM[tier]
    osc = clocklink.OSCILLATORS[spec["oscillator"]]
    rep = measurement.expected_floor(tier)
    for row in rep["rows"]:
        modelled = clocklink.adev_model(
            osc["adev_1s"] * math.sqrt(2),
            osc["flicker_floor"] * math.sqrt(2), row["tau_s"])
        assert modelled == pytest.approx(
            max(row["terms"]["OSCILLATOR_WHITE_FM"],
                row["terms"]["OSCILLATOR_FLICKER_FLOOR"]), rel=1e-12)


def test_floor_report_covers_every_tier():
    rep = measurement.floor_report()
    assert set(rep["tiers"]) == set(measurement.TIERS)


# --- analysis plan -----------------------------------------------------

def test_analysis_plan_freeze_is_internal_not_preregistration():
    """R8-D-004: the freeze is in-repository only.

    This test previously asserted `plan["frozen"] is True`, which read
    as an external commitment nobody had made. The freeze is real but
    local, and the record must say which.
    """
    plan = measurement.analysis_plan()
    assert plan["freeze_status"] == "INTERNAL_ANALYSIS_FREEZE"
    assert plan["externally_preregistered"] is False
    assert plan["frozen_before_data"] is True
    assert "FROZEN" in plan["freeze_statement"]
    assert "no third-party registration" in plan["freeze_caveat"]


def test_no_key_implies_external_preregistration():
    """Guard against the misleading key returning."""
    plan = measurement.analysis_plan()
    assert "frozen" not in plan


def test_freeze_statement_gives_the_reason():
    plan = measurement.analysis_plan()
    assert "no measurement has been taken" in \
        plan["freeze_statement"].lower()
    assert plan["why_frozen"].strip()


def test_all_three_estimators_are_specified():
    est = measurement.analysis_plan()["estimators"]
    assert set(est) == {"ADEV", "MDEV", "TDEV"}
    # ADEV must admit what it cannot do
    assert "cannot separate" in est["ADEV"]["limitation"]
    assert "white PM" in est["MDEV"]["discriminates"]


def test_tau_range_is_capped_at_a_fifth_of_the_run():
    tr = measurement.analysis_plan()["tau_range"]
    assert tr["tau_max_s"] == pytest.approx(tr["run_duration_s"] / 5.0)
    assert tr["tau0_s"] > 0
    assert tr["tau_max_s"] > tr["tau0_s"]


def test_stopping_rule_forbids_stopping_on_the_result():
    rule = measurement.analysis_plan()["stopping_rule"]
    assert "may NOT be stopped" in rule["forbidden"]
    assert "looks good" in rule["forbidden"]
    assert "Optional stopping" in rule["forbidden"]


def test_stopping_rule_covers_every_procedure_step():
    durations = measurement.analysis_plan()[
        "stopping_rule"]["scheduled_durations_h"]
    for step in measurement.PROCEDURE:
        assert durations[step.configuration] == step.duration_h


def test_pass_criteria_preregister_a_null():
    crit = measurement.analysis_plan()["pass_criteria"]
    assert "NULL" in crit["expected_outcome"]
    assert "publishing that null" in crit["expected_outcome"]
    assert "10" in crit["instrument_separation"]


def test_pass_criteria_quote_the_computed_tier_floor():
    """The expected outcome must carry this tier's own number."""
    for tier in measurement.TIERS:
        plan = measurement.analysis_plan(tier)
        h = measurement.minimum_resolvable_height_m(tier)
        assert f"{h:,.4g}" in plan["pass_criteria"]["expected_outcome"]


def test_outlier_policy_forbids_purely_statistical_removal():
    plan = measurement.analysis_plan()
    assert "never on statistical grounds" in plan["outlier_policy"]


def test_analysis_plan_rejects_unknown_tier():
    with pytest.raises(ValueError):
        measurement.analysis_plan("DELUXE")


# --- refusal -----------------------------------------------------------

def test_refuse_measured_claim_raises():
    with pytest.raises(measurement.MeasurementRefused):
        measurement.refuse_measured_claim()


def test_refuse_measured_claim_raises_whatever_it_is_handed():
    with pytest.raises(measurement.MeasurementRefused):
        measurement.refuse_measured_claim(
            "sigma_y", 1e-13, tau=100.0, tier="GOOD")


def test_refusal_names_the_closed_evidence_classes():
    with pytest.raises(measurement.MeasurementRefused) as exc:
        measurement.refuse_measured_claim()
    msg = str(exc.value)
    assert "BENCH_MEASUREMENT" in msg
    assert "INDEPENDENT_REPLICATION" in msg


# --- operator workbench ------------------------------------------------

def test_workbench_has_every_section_and_none_is_empty():
    wb = measurement.operator_workbench()
    assert list(wb["sections"]) == [
        "A_BEFORE_POWER_ON", "B_WARMUP", "C_ENVIRONMENTAL_LOGGING",
        "D_SHAM_AND_BLANK_CONDITIONS", "E_DURING_THE_RUN",
        "F_END_OF_BLOCK", "G_ANALYSIS"]
    for items in wb["sections"].values():
        assert items and all(i.strip() for i in items)


def test_workbench_logs_temperature_and_supply_voltage():
    env = " ".join(
        measurement.operator_workbench()[
            "sections"]["C_ENVIRONMENTAL_LOGGING"]).lower()
    assert "temperature" in env
    assert "supply voltage" in env
    assert "cadence" in env


def test_workbench_specifies_both_sham_and_blank():
    sham = " ".join(
        measurement.operator_workbench()[
            "sections"]["D_SHAM_AND_BLANK_CONDITIONS"])
    assert "BLANK" in sham and "SHAM" in sham
    assert "interleaved" in sham


def test_workbench_quotes_the_tier_crossover_time():
    for tier in measurement.TIERS:
        wb = measurement.operator_workbench(tier)
        tau = measurement.expected_floor(tier)[
            "instrument_crossover_tau_s"]
        run = " ".join(wb["sections"]["E_DURING_THE_RUN"])
        assert f"{tau:.3g}" in run


def test_workbench_bench_time_matches_the_tier_procedure():
    for tier in measurement.TIERS:
        wb = measurement.operator_workbench(tier)
        proc = measurement.procedure(tier)
        assert wb["total_bench_time_days"] == pytest.approx(
            proc["total_duration_days"])


def test_workbench_defers_mains_work_to_a_qualified_person():
    wb = measurement.operator_workbench()
    assert "qualified person" in wb["competence_note"]


# --- evidence discipline -----------------------------------------------

def _every_record():
    yield measurement.tier_cost("MINIMAL")
    yield measurement.bill_of_materials("STANDARD")
    yield measurement.bom_report()
    yield measurement.procedure()
    yield measurement.procedure("GOOD")
    yield measurement.expected_floor("GOOD")
    yield measurement.floor_report()
    yield measurement.analysis_plan()
    yield measurement.operator_workbench()
    yield measurement.programme_summary()
    yield measurement.PROCEDURE[0].as_record()


def test_every_returned_record_carries_an_evidence_class():
    for rec in _every_record():
        assert rec["evidence_class"] in ("SYNTHETIC_MODEL",
                                         "DERIVED_ARITHMETIC")


def test_every_returned_record_states_no_measurement_was_taken():
    for rec in _every_record():
        stmt = rec["no_measurement_statement"]
        assert stmt == measurement.NO_MEASUREMENT
        assert "No measurement has been taken" in stmt


def test_programme_summary_reports_untested_status():
    summary = measurement.programme_summary()
    assert summary["status"] == \
        "PROGRAMME_SPECIFIED_PHYSICALLY_UNTESTED"
    assert summary["analysis_plan_freeze"] == "INTERNAL_ANALYSIS_FREEZE"
    assert summary["externally_preregistered"] is False
