"""P11 — angle reconstruction: precision window, controls, missing archive.

The reconstruction is allowed to succeed at what it can do -- reproducing
51.843 at period precision -- and is then held to what it cannot: the
documentary evidence is absent, so authorship is refused.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction

import pytest

from r11 import anglerecon as A


# --- the precision table ------------------------------------------------

def test_precision_table_covers_every_listed_precision_and_mode():
    table = A.precision_table()
    assert A.SIG_DIGITS == (3, 4, 5, 6, 7, 8, 10)
    assert len(table) == len(A.SIG_DIGITS) * 2
    assert {r["sig_digits"] for r in table} == set(A.SIG_DIGITS)
    assert {r["mode"] for r in table} == {"ROUND_HALF_EVEN", "TRUNCATE"}


def test_expression_reproduces_51_843_only_between_five_and_eight_digits():
    assert A.reproducing_sig_digits(A.RoundingMode.ROUND_HALF_EVEN) == (
        5, 6, 7, 8)
    assert A.reproducing_sig_digits(A.RoundingMode.TRUNCATE) == (5, 6, 7, 8)
    rows = {(r["sig_digits"], r["mode"]): r for r in A.precision_table()}
    # too coarse: the third decimal has not been resolved yet
    assert rows[(3, "ROUND_HALF_EVEN")]["value"] == "51.8"
    assert rows[(3, "ROUND_HALF_EVEN")]["reproduces_quoted"] is False
    assert rows[(4, "ROUND_HALF_EVEN")]["value"] == "51.84"
    # the window
    assert rows[(5, "ROUND_HALF_EVEN")]["value"] == "51.843"
    assert rows[(8, "TRUNCATE")]["reproduces_quoted"] is True
    # too fine: the true value is 51.84300034, which is not 51.843
    assert rows[(10, "ROUND_HALF_EVEN")]["value"] == "51.84300034"
    assert rows[(10, "ROUND_HALF_EVEN")]["reproduces_quoted"] is False
    assert rows[(10, "TRUNCATE")]["value"] == "51.84300033"


def test_evaluate_at_precision_modes_differ_where_they_should():
    v = A.RECONSTRUCTION_DEG
    assert A.evaluate_at_precision(v, 10,
                                   A.RoundingMode.ROUND_HALF_EVEN) == Decimal(
        "51.84300034")
    assert A.evaluate_at_precision(v, 10,
                                   A.RoundingMode.TRUNCATE) == Decimal(
        "51.84300033")
    # a string mode name is accepted, an invented one is not
    assert A.evaluate_at_precision(v, 5, "TRUNCATE") == Decimal("51.843")
    with pytest.raises(A.AngleReconError):
        A.evaluate_at_precision(v, 5, "ROUND_TO_TASTE")
    with pytest.raises(A.AngleReconError):
        A.evaluate_at_precision(v, 0)


def test_reconstruction_value_matches_the_registered_relation():
    assert float(A.RECONSTRUCTION_DEG) == pytest.approx(51.843000336255706,
                                                        abs=1e-12)
    assert float(A.UNCORRECTED_DEG) == pytest.approx(51.827292372987756,
                                                     abs=1e-12)
    assert float(A.QUOTED_TARGET - A.RECONSTRUCTION_DEG) == pytest.approx(
        -3.362557e-07, rel=1e-6)


# --- historical constant approximations ---------------------------------

def test_historical_approximations_are_period_values_not_tuned_ones():
    assert A.HISTORICAL_PHI == ("1.618", "1.6180", "1.61803")
    assert A.HISTORICAL_PI == ("3.14", "3.1416", "3.14159")
    table = A.historical_substitution_table()
    assert len(table) == 9


def test_51_843_survives_five_figure_pi_and_fails_at_three_figure_pi():
    summary = A.survives_historical_constants()
    assert summary["n_combinations"] == 9
    # six of nine reproduce: every phi, but only pi to five figures
    assert summary["n_reproducing"] == 6
    assert ("1.618", "3.1416") in [tuple(x) for x in summary["reproducing"]]
    assert ("1.61803", "3.14159") in [tuple(x)
                                      for x in summary["reproducing"]]
    failing = [tuple(x) for x in summary["failing"]]
    assert all(pi == "3.14" for _phi, pi in failing)
    assert len(failing) == 3
    assert summary["sensitive_constant"] == "pi"


def test_three_figure_pi_moves_the_answer_by_far_more_than_the_residual():
    rows = {(r["phi_approx"], r["pi_approx"]): r
            for r in A.historical_substitution_table()}
    coarse = rows[("1.618", "3.14")]
    assert coarse["reproduces_quoted"] is False
    assert coarse["value"] == pytest.approx(51.868987, abs=1e-5)
    # 0.026 degrees off: about eighty thousand times the pi/200 residual
    assert abs(coarse["residual_to_quoted_deg"]) > 0.02
    fine = rows[("1.61803", "3.14159")]
    assert fine["reproduces_quoted"] is True
    assert fine["value"] == pytest.approx(51.843009, abs=1e-5)


# --- the wrong-mode control ---------------------------------------------

def test_a_degree_radian_mode_error_does_not_produce_51_843():
    ctrl = A.wrong_mode_control()
    errors = {r["mode_error"]: r for r in ctrl["mode_errors"]}
    assert set(errors) == {"RADIANS_LABELLED_DEGREES",
                           "DEGREES_CONVERTED_AGAIN"}
    # radians read as degrees: 0.92, not 51.843
    assert errors["RADIANS_LABELLED_DEGREES"]["value"] == pytest.approx(
        0.920264857, abs=1e-6)
    # degrees converted a second time: 2969.5
    assert errors["DEGREES_CONVERTED_AGAIN"]["value"] == pytest.approx(
        2969.500824, abs=1e-4)
    assert ctrl["closest_abs_difference_deg"] > 50.0
    assert ctrl["any_reproduces_quoted"] is False
    assert ctrl["control_passed"] is True


# --- the slide-rule band ------------------------------------------------

def test_a_slide_rule_cannot_single_out_this_expression():
    band = A.slide_rule_band()
    assert band["sig_figs"] == 3
    assert band["half_width_deg"] == 0.05
    assert band["band_deg"] == pytest.approx([51.793, 51.893], abs=1e-9)
    names = [n for n, _v in band["indistinguishable_inside_band"]]
    # the corrected and uncorrected expressions read identically
    assert "atan(sqrt(phi))" in names
    assert "atan(sqrt(phi)) + pi/200" in names
    assert "51.83" in names
    assert "51.86" in names
    assert "51 deg 51 min 51 sec" in names
    # 360/7 is the one thing a slide rule COULD have ruled out
    assert "360/7" not in names
    assert band["n_indistinguishable"] >= 4
    assert band["can_single_out_expression"] is False
    assert band["resolution_verdict"] == "CANNOT_SINGLE_OUT"


# --- the alternatives table ---------------------------------------------

def test_alternatives_include_360_over_7_and_the_dms_cut_value():
    rows = {r["label"]: r for r in A.alternatives_table()}
    assert "360/7" in rows
    assert rows["360/7"]["value_deg"] == pytest.approx(51.428571428,
                                                       abs=1e-8)
    assert rows["360/7"]["residual_to_quoted_deg"] == pytest.approx(
        0.414428571, abs=1e-8)

    dms = rows["51 deg 51 min 51 sec"]
    assert dms["value_deg"] == pytest.approx(51.8641666667, abs=1e-9)
    assert dms["residual_to_quoted_deg"] == pytest.approx(-0.0211666667,
                                                          abs=1e-9)

    plain = rows["atan(sqrt(phi))"]
    assert plain["value_deg"] == pytest.approx(51.827292372987756, abs=1e-12)
    assert plain["residual_to_quoted_deg"] == pytest.approx(0.015707627012,
                                                            abs=1e-11)


def test_every_frozen_denominator_appears_and_200_wins():
    from r11.picorrection import FROZEN_DENOMINATORS
    rows = A.alternatives_table()
    labels = {r["label"] for r in rows}
    for k in FROZEN_DENOMINATORS:
        assert f"atan(sqrt(phi)) + pi/{k}" in labels
    # sorted by absolute residual, so the winner is first
    assert rows[0]["label"] == "atan(sqrt(phi)) + pi/200"
    # and the runner-up is nearly two thousand times worse
    assert (rows[1]["abs_residual_deg"]
            > 1000 * rows[0]["abs_residual_deg"])
    assert rows[1]["label"] == "atan(sqrt(phi)) + pi/192"


def test_only_pi_over_200_lands_inside_the_quoted_slack():
    inside = [r for r in A.alternatives_table()
              if r["family"] == "PI_CORRECTION"
              and r["abs_residual_deg"] <= 0.0005]
    assert len(inside) == 1
    assert inside[0]["label"] == "atan(sqrt(phi)) + pi/200"


# --- 51.843 and 51 deg 51 min 51 sec are different numbers --------------

def test_the_dms_cut_value_is_a_different_number_not_a_rounding():
    cmp = A.dms_cut_comparison()
    assert cmp["same_number"] is False
    assert cmp["do_not_conflate"] is True
    assert cmp["dms_degrees"] == pytest.approx(51.8641666667, abs=1e-9)
    assert cmp["difference_deg"] == pytest.approx(0.0211666667, abs=1e-9)
    assert cmp["difference_arcsec"] == pytest.approx(76.2, abs=1e-6)
    assert cmp["dms_exact_fraction"] == "62237/1200"
    assert A.DMS_CUT_DEG == Fraction(62237, 1200)
    assert cmp["quoted_decimal_provenance"] == "a decimal the source specified"


def test_dms_conversion_is_exact_rational():
    assert A.dms_to_degrees(51, 51, 51) == Fraction(62237, 1200)
    assert A.dms_to_degrees(90, 0, 0) == Fraction(90)
    with pytest.raises(A.AngleReconError):
        A.dms_to_degrees(51, 51.0, 51)


# --- the historical evidence, which is the actual result ----------------

def test_historical_evidence_status_is_blocked_missing_data():
    assert A.historical_evidence_status() == "BLOCKED_MISSING_DATA"


def test_no_class_of_documentary_evidence_was_located():
    rec = A.historical_evidence_record()
    assert len(rec) == 6
    assert {r["evidence_class"] for r in rec} == {
        "patent", "paper", "notebook", "correspondence",
        "calculator_manual", "interview"}
    assert all(r["status"] == "NOT_LOCATED" for r in rec)
    assert all(r["located_in_this_environment"] is False for r in rec)


def test_refuse_authorship_claim_raises():
    with pytest.raises(A.AngleReconError, match="POSSIBLE, not that it was"):
        A.refuse_authorship_claim()
    with pytest.raises(A.AngleReconError, match="BLOCKED_MISSING_DATA"):
        A.refuse_authorship_claim("a period designer",
                                  evidence="the numbers match to 7 digits")


# --- the report ----------------------------------------------------------

def test_report_verdict_and_standing_fields():
    rep = A.anglerecon_report()
    assert rep["verdict"] == "HISTORICAL_DERIVATION_NOT_ESTABLISHED"
    assert rep["claim_class"] == "BLOCKED_MISSING_DATA"
    assert rep["numeric_claim_class"] == "RETROSPECTIVE_NUMERIC_MATCH"
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["historical_evidence_status"] == "BLOCKED_MISSING_DATA"
    assert rep["reproducing_sig_digits_half_even"] == [5, 6, 7, 8]
    assert rep["wrong_mode_control"]["control_passed"] is True
    assert rep["slide_rule"]["can_single_out_expression"] is False
    assert rep["best_alternative"]["label"] == "atan(sqrt(phi)) + pi/200"
    assert "refuse_authorship_claim" in rep["refusals"]


def test_what_this_does_not_say_separates_possible_from_performed():
    text = A.anglerecon_report()["what_this_does_not_say"]
    assert "POSSIBLE" in text
    assert "BLOCKED_MISSING_DATA" in text
    assert "0.021" in text                      # the dms cut value gap
    assert "authorship" in text
