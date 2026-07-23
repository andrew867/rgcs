"""P11 — pi-correction registry: frozen set, mixed units, input precision.

The load-bearing tests are the ones that can embarrass the relation: that
the denominator set cannot grow, that the units do not line up, that the
seven-digit agreement is finer than the input's own precision, and that
dozens of equally simple corrections sit inside the same interval.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from r11 import picorrection as P


# --- the frozen denominator set ----------------------------------------

def test_frozen_denominators_are_the_declared_fifteen():
    assert P.FROZEN_DENOMINATORS == (
        50, 60, 72, 90, 100, 120, 144, 180, 192, 200, 240, 256, 360, 512,
        1000)
    assert len(P.FROZEN_DENOMINATORS) == 15
    # frozen means ordered and de-duplicated, so the hash is meaningful
    assert len(set(P.FROZEN_DENOMINATORS)) == 15
    assert P.FROZEN_SEARCH_SPACE_SIZE == 8 * 15


def test_refuse_new_denominator_raises_for_201():
    # the red-team attack: observe the residual, then add the denominator
    # that cancels it
    with pytest.raises(P.PiCorrectionError, match="not in the frozen"):
        P.refuse_new_denominator(201)
    with pytest.raises(P.PiCorrectionError):
        P.refuse_new_denominator(199, justification="it fits better")
    with pytest.raises(P.PiCorrectionError):
        P.refuse_new_denominator(103)


def test_frozen_denominator_is_accepted_and_labelled_not_added():
    rec = P.refuse_new_denominator(200)
    assert rec["status"] == "FROZEN_BEFORE_SCORING"
    assert rec["denominator"] == 200
    assert rec["frozen_set_hash"] == P.FROZEN_SET_HASH
    assert P.is_frozen_denominator(200) is True
    assert P.is_frozen_denominator(201) is False


def test_a_relation_cannot_be_built_on_an_unfrozen_denominator():
    with pytest.raises(P.PiCorrectionError, match="frozen"):
        P.PiRelation(
            relation_id="X", base_closed_form="atan(sqrt(phi))",
            numerator_constant="pi", denominator=201,
            target_closed_form="51.843", target_quoted_str="51.843",
            n_operations=4, n_constants=3)


# --- C1 and C2 residuals reproduce --------------------------------------

def test_c1_constants_reproduce_to_the_published_digits():
    base = P.RELATION_C1.base_deg()
    corr = P.RELATION_C1.correction_deg()
    pred = P.RELATION_C1.predicted_deg()
    assert float(base) == pytest.approx(51.827292372987756, abs=1e-12)
    assert str(base).startswith("51.8272923729877525065")
    assert float(corr) == pytest.approx(0.015707963267948967, abs=1e-18)
    assert float(pred) == pytest.approx(51.843000336255706, abs=1e-12)


def test_c1_residual_is_minus_3_36e_07_degrees():
    resid = P.RELATION_C1.exact_residual()
    assert float(resid) == pytest.approx(-3.362557e-07, rel=1e-6)
    # signed: the expression overshoots the quoted value
    assert resid < 0
    assert str(resid).startswith("-3.36255701472724")
    rel = P.RELATION_C1.relative_residual()
    assert float(rel) == pytest.approx(-6.4859e-09, rel=1e-3)


def test_c2_reproduces_and_is_twenty_five_times_worse_than_c1():
    pred = P.RELATION_C2.predicted_deg()
    target = P.RELATION_C2.target_deg()
    assert float(pred) == pytest.approx(19.471212238275278, abs=1e-12)
    assert float(target) == pytest.approx(19.471220634490692, abs=1e-12)
    resid = P.RELATION_C2.exact_residual()
    assert float(resid) == pytest.approx(8.396215e-06, rel=1e-6)
    assert abs(float(resid)) > 20 * abs(float(P.RELATION_C1.exact_residual()))


def test_atan_one_over_sqrt8_is_computed_not_assumed():
    v = P.atan_one_over_sqrt8_deg()
    assert str(v).startswith("19.4712206344906913")
    # and it is a different constant from atan(sqrt(phi))
    assert v != P.RELATION_C1.base_deg()


def test_complexity_is_operations_plus_constants():
    assert P.RELATION_C1.complexity() == 7          # 4 ops + 3 constants
    assert P.RELATION_C2.complexity() == 9          # 4 ops + 5 constants
    assert P.description_length(P.RELATION_C1) == 7
    # the longer expression is the more expensive one
    assert P.RELATION_C2.complexity() > P.RELATION_C1.complexity()


# --- units: mixed, and load-bearing -------------------------------------

def test_unit_validity_is_mixed_for_both_registered_relations():
    assert P.unit_validity(P.RELATION_C1) == "UNIT_CATEGORY_MIXED"
    assert P.unit_validity(P.RELATION_C2) == "UNIT_CATEGORY_MIXED"
    assert (P.UnitValidity.UNIT_CATEGORY_MIXED.value
            == "UNIT_CATEGORY_MIXED")


def test_pi_over_200_as_radians_is_nine_tenths_of_a_degree():
    a = P.unit_analysis(P.RELATION_C1)
    # the bare number that the relation actually adds
    assert a["correction_bare_number"] == pytest.approx(
        0.015707963267948967, abs=1e-18)
    # what it would be if the units were honoured: 180/200 = 0.9 exactly
    assert a["correction_if_read_as_radians_deg"] == pytest.approx(0.9,
                                                                   abs=1e-12)
    assert a["value_if_units_were_honoured_deg"] == pytest.approx(
        52.727292372987756, abs=1e-9)
    # honouring the units misses the target by nearly a degree
    assert abs(a["residual_if_units_were_honoured_deg"]) > 0.88
    b = P.unit_analysis(P.RELATION_C2)
    assert b["correction_if_read_as_radians_deg"] == pytest.approx(0.18,
                                                                   abs=1e-12)


def test_refuse_unit_confusion_raises():
    with pytest.raises(P.PiCorrectionError, match="dimensionally"):
        P.refuse_unit_confusion(P.RELATION_C1, claimed_consistent=True)
    with pytest.raises(P.PiCorrectionError):
        P.refuse_unit_confusion(P.RELATION_C2, claimed_consistent=False)


# --- the decisive test: input precision ---------------------------------

def test_input_precision_slack_of_51_843_is_half_a_thousandth():
    assert P.input_precision_slack("51.843") == 0.0005
    assert P.input_precision_slack_exact("51.843") == Decimal("0.0005")
    assert P.quoted_decimals("51.843") == 3
    # more quoted decimals, less slack
    assert P.input_precision_slack("51.8430") == 0.00005
    assert P.input_precision_slack("51.84") == 0.005
    assert P.input_precision_slack("52") == 0.5


def test_input_precision_slack_refuses_a_hidden_precision():
    with pytest.raises(P.PiCorrectionError):
        P.input_precision_slack(51.843)               # not a string
    with pytest.raises(P.PiCorrectionError, match="exponent"):
        P.input_precision_slack("5.1843e1")


def test_many_corrections_land_inside_the_input_slack():
    c = P.candidates_within_slack("51.843", 0.0005)
    # pi/200 is one of a crowd, not a distinguished member
    assert c["count"] >= 20
    assert c["contains_pi_over_200"] is True
    assert len(c["distinct_constants"]) >= 5
    # every member reproduces 51.843 as well as 51.843 can be read
    for m in c["members"]:
        assert abs(m["residual_deg"]) <= 0.0005
    corrections = {m["correction"] for m in c["members"]}
    assert "pi/200" in corrections
    # the crowd is not all one constant
    assert any(m["constant"] == "phi" for m in c["members"])
    assert any(m["constant"] == "e" for m in c["members"])
    assert any(m["constant"] == "sqrt2" for m in c["members"])


def test_agreement_is_far_finer_than_the_input_precision():
    audit = P.precision_audit(P.RELATION_C1)
    assert audit["input_precision_slack"] == 0.0005
    assert audit["abs_residual_deg"] == pytest.approx(3.362557e-07,
                                                      rel=1e-6)
    # roughly fifteen hundred times finer than the number's own precision
    assert audit["agreement_finer_than_input_by_factor"] > 1000
    assert audit["extra_precision_is_informative"] is False
    assert audit["candidates_within_slack"] >= 20
    assert audit["claim_class"] == "RETROSPECTIVE_NUMERIC_MATCH"


def test_c2_has_no_quoted_slack_to_hide_in():
    audit = P.precision_audit(P.RELATION_C2)
    assert audit["target_is_quoted_decimal"] is False
    assert audit["input_precision_slack"] is None


# --- POWER: the scan can single out a planted relation ------------------

def test_power_control_recovers_a_planted_exact_relation():
    power = P.power_check()
    assert power["planted_correction"] == "pi/144"
    assert power["recovered_correction"] == "pi/144"
    assert power["recovered_equals_planted"] is True
    assert power["abs_residual_deg"] < 1e-30
    assert power["detected"] is True


def test_the_scan_finds_pi_over_200_for_the_quoted_target():
    hit = P.best_frozen_correction("51.843")
    assert hit["correction"] == "pi/200"
    assert hit["abs_residual_deg"] == pytest.approx(3.362557e-07, rel=1e-6)
    assert hit["search_space_size"] == P.FROZEN_SEARCH_SPACE_SIZE


# --- prospective use: freeze first --------------------------------------

_FIVE = (
    "the next quoted slope will lie within 0.0005 deg of atan(sqrt(phi))"
    " + pi/200",
    "no second independent angle will need a different denominator",
    "the denominator will remain 200 for every further quoted slope",
    "no quoted slope will require a numerator constant outside the "
    "frozen set",
    "each further slope will be quoted to at least three decimals",
)


def test_freeze_and_reveal_round_trip():
    rec = P.freeze_predictions(_FIVE, set_id="TEST_ROUNDTRIP")
    assert rec.set_id == "TEST_ROUNDTRIP"
    assert len(rec.predictions) == 5
    assert len(rec.prereg_hash) == 64
    assert rec.frozen_at_unix > 0
    assert P.is_frozen("TEST_ROUNDTRIP") is True

    out = P.reveal("TEST_ROUNDTRIP", _FIVE)
    assert out["prereg_hash"] == rec.prereg_hash
    assert out["hash_verified"] is True
    assert out["n_predictions"] == 5
    assert out["outcome_status"] == "AWAITING_OUTCOME"
    assert out["claim_class"] == "PROSPECTIVE_PREDICTION"


def test_reveal_refuses_a_set_that_was_never_frozen():
    with pytest.raises(P.PiCorrectionError, match="never frozen"):
        P.reveal("TEST_NEVER_FROZEN")


def test_reveal_refuses_predictions_edited_after_the_freeze():
    P.freeze_predictions(_FIVE, set_id="TEST_TAMPER")
    edited = list(_FIVE)
    edited[0] = "the next quoted slope will be whatever it turns out to be"
    with pytest.raises(P.PiCorrectionError, match="do not hash"):
        P.reveal("TEST_TAMPER", edited)


def test_freeze_requires_at_least_five_predictions():
    with pytest.raises(P.PiCorrectionError, match="at least 5"):
        P.freeze_predictions(_FIVE[:4], set_id="TEST_TOO_FEW")
    with pytest.raises(P.PiCorrectionError):
        P.freeze_predictions("one long string", set_id="TEST_STRING")
    with pytest.raises(P.PiCorrectionError, match="[Dd]uplicate"):
        P.freeze_predictions((_FIVE[0],) * 5, set_id="TEST_DUPES")


def test_a_freeze_cannot_be_rewritten():
    P.freeze_predictions(_FIVE, set_id="TEST_ONCE")
    with pytest.raises(P.PiCorrectionError, match="already frozen"):
        P.freeze_predictions(_FIVE, set_id="TEST_ONCE")


def test_refuse_unfrozen_prediction_raises():
    with pytest.raises(P.PiCorrectionError, match="never frozen"):
        P.refuse_unfrozen_prediction("51.843 was predicted all along",
                                     set_id="TEST_UNFROZEN")


def test_refuse_claim_upgrade_raises():
    with pytest.raises(P.PiCorrectionError, match="may not be reported"):
        P.refuse_claim_upgrade(P.RELATION_C1,
                               "SOURCE_ESTABLISHED_PHYSICS")


# --- the per-relation and module reports --------------------------------

@pytest.mark.parametrize("relation", P.REGISTERED_RELATIONS)
def test_relation_report_carries_every_required_field(relation):
    r = P.relation_report(relation)
    for key in ("exact_residual", "relative_residual", "search_space_size",
                "complexity", "preregistered_or_retrospective",
                "unit_validity", "historical_plausibility",
                "physical_mechanism_status"):
        assert key in r
    assert r["unit_validity"] == "UNIT_CATEGORY_MIXED"
    assert r["preregistered_or_retrospective"] == "RETROSPECTIVE"
    assert r["physical_mechanism_status"] == "UNSUPPORTED"
    assert r["claim_class"] == "RETROSPECTIVE_NUMERIC_MATCH"
    assert r["verdict"] == "PI_CORRECTION_REGISTRY_RETROSPECTIVE_ONLY"
    assert r["search_space_size"] == 120


def test_report_verdict_and_claim_class():
    rep = P.picorrection_report()
    assert rep["verdict"] == "PI_CORRECTION_REGISTRY_RETROSPECTIVE_ONLY"
    assert rep["claim_class"] == "RETROSPECTIVE_NUMERIC_MATCH"
    assert rep["max_claim_class"] == "RETROSPECTIVE_NUMERIC_MATCH"
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["physical_mechanism_status"] == "UNSUPPORTED"
    assert len(rep["relations"]) == 2
    assert rep["candidates_within_slack"] >= 20
    assert rep["power_control"]["detected"] is True
    assert rep["frozen_denominators"] == list(P.FROZEN_DENOMINATORS)
    assert "refuse_new_denominator" in rep["refusals"]


def test_what_this_does_not_say_names_the_three_defects():
    text = P.picorrection_report()["what_this_does_not_say"]
    assert "UNSUPPORTED" in text                    # no mechanism
    assert "0.0005" in text                         # input precision
    assert "UNIT_CATEGORY_MIXED" in text            # units
    assert "RETROSPECTIVE_NUMERIC_MATCH" in text    # the cap


def test_claim_class_vocabulary_is_the_repository_vocabulary():
    names = {c.value for c in P.ClaimClass}
    assert names == {
        "EXACT_IDENTITY", "SOURCE_ESTABLISHED_PHYSICS",
        "REPOSITORY_COMPUTATIONAL_RESULT", "ENGINEERING_CANDIDATE",
        "RETROSPECTIVE_NUMERIC_MATCH", "PROSPECTIVE_PREDICTION",
        "BENCH_MEASUREMENT", "UNSUPPORTED", "BLOCKED_MISSING_DATA"}
