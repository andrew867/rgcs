"""P06 — crystal carrier search: exact audit, target fitting, LEE null, power."""

from __future__ import annotations

from fractions import Fraction

import pytest

from r11 import carrier as C


# --- the audited arithmetic, exact --------------------------------------

def test_f_crystal_is_exact_rational_not_float():
    assert C.F_CRYSTAL_N7_HZ == Fraction("13772.28")
    assert C.F_CRYSTAL_N7_HZ == Fraction(344307, 25)


def test_two_thirds_of_the_mode_is_exactly_9181_52():
    assert C.F_TIMES_TWO_THIRDS == Fraction("9181.52")
    assert C.F_CRYSTAL_N7_HZ * Fraction(2, 3) == Fraction(229538, 25)


def test_residual_to_grouped_9192_is_exactly_10_48():
    assert C.RESIDUAL_TO_9192 == Fraction("10.48")
    assert C.RESIDUAL_TO_9192 == Fraction(262, 25)
    assert C.GROUPED_9192 - C.F_TIMES_TWO_THIRDS == C.RESIDUAL_TO_9192


def test_sixty_three_sixths_is_exactly_ten_and_a_half():
    assert C.SIXTY_THREE_SIXTHS == Fraction(21, 2)
    assert C.SIXTY_THREE_SIXTHS == Fraction("10.5")
    # exact rational: 63/6 reduces, it does not round
    assert C.SIXTY_THREE_SIXTHS.denominator == 2


def test_corrected_sum_is_exactly_9192_02_and_overshoots_by_0_02():
    assert C.CORRECTED_SUM == Fraction("9192.02")
    assert C.CORRECTED_SUM - C.GROUPED_9192 == Fraction("0.02")
    # the correction overshoots: 10.50 applied to a 10.48 gap
    assert C.SIXTY_THREE_SIXTHS - C.RESIDUAL_TO_9192 == Fraction("0.02")


def test_exact_base_for_9192_is_exactly_13788():
    assert C.EXACT_BASE_FOR_9192 == 13788
    assert C.EXACT_BASE_FOR_9192.denominator == 1
    assert Fraction(9192) * Fraction(3, 2) == 13788


# --- the pack discrepancy, computed and stated --------------------------

def test_13788_minus_13772_28_is_15_72_above_not_0_03_below():
    # computed here, exactly: 13788.00 - 13772.28 = 15.72 Hz
    assert C.BASE_DIFFERENCE == Fraction("15.72")
    assert C.BASE_DIFFERENCE == Fraction(393, 25)
    # the exact base sits ABOVE the finest computed mode
    assert C.BASE_DIFFERENCE > 0
    # and it is nowhere near the pack's "0.03 Hz below"
    assert abs(C.BASE_DIFFERENCE) > Fraction("0.03") * 100


def test_audit_reports_the_pack_discrepancy_rather_than_fudging_it():
    a = C.audit_high_priority_candidate()
    assert a["base_difference_hz"] == "15.72"
    assert a["base_difference_exact"] == "393/25"
    assert a["base_difference_sign"] == "EXACT_BASE_IS_ABOVE_COMPUTED_MODE"
    assert "0.03" in a["pack_discrepancy"]
    assert "15.72" in a["pack_discrepancy"]


def test_audit_chain_reproduces_end_to_end():
    a = C.audit_high_priority_candidate()
    assert a["f_crystal_hz"] == "13772.28"
    assert a["times_two_thirds_hz"] == "9181.52"
    assert a["residual_to_9192_hz"] == "10.48"
    assert a["sixty_three_sixths"] == "21/2"
    assert a["corrected_sum_hz"] == "9192.02"
    assert a["exact_base_for_9192_hz"] == "13788"
    assert a["sixty_three_sixths_is_exact"] is True
    assert a["target_fitted"] is True


def test_observed_relative_residual_is_about_0_114_percent():
    assert C.OBSERVED_REL_RESIDUAL == pytest.approx(0.00114012184, abs=1e-11)
    assert Fraction(C.RESIDUAL_TO_9192, C.GROUPED_9192) == Fraction(131, 114900)


# --- the grid -----------------------------------------------------------

def test_grid_covers_every_base_rational_and_operation():
    ops = {e.op for e in C.GRID}
    assert ops == set(C.CarrierOp)
    assert {e.base_id for e in C.GRID} == {b for b, _ in C.REGISTERED_BASES}
    assert {e.rational for e in C.GRID} == set(C.SUPPLIED_RATIONALS)
    # beats against the full Cs-133 frequency and each grouped number
    refs = {e.beat_ref for e in C.GRID if e.beat_ref is not None}
    assert refs == {C.CS133_HZ, 9192, 631, 770}
    # a search this wide is why the null below matters
    assert C.grid_size() > 1000


def test_the_candidate_expression_is_a_grid_member():
    assert C.CANDIDATE_A_EXPRESSION.value() == Fraction("9181.52")
    assert C.CANDIDATE_A_EXPRESSION.text() == "13772.28 * 2/3"
    assert any(e.value() == Fraction("9181.52") for e in C.GRID)


def test_best_grid_hit_on_9192_finds_the_candidate_with_10_48_residual():
    hit = C.best_grid_hit(9192)
    assert hit["residual_exact"] == "262/25"
    assert hit["relative_residual"] == pytest.approx(0.00114012184, abs=1e-11)
    assert hit["is_exact_hit"] is False


# --- POWER: a planted exact grid expression is recovered ----------------

def test_power_search_recovers_a_planted_exact_expression():
    p = C.power_check()
    assert p["detected"] is True
    assert p["recovered"]["relative_residual"] == 0.0
    assert p["recovered"]["is_exact_hit"] is True
    assert p["recovered_value_equals_planted"] is True


def test_planted_target_is_exactly_a_grid_value():
    assert C.PLANTED_TARGET_HZ == Fraction(15360)
    assert C.best_grid_hit(C.PLANTED_TARGET_HZ)["relative_residual"] == 0.0


# --- NULL: the 9192 match is no better than chance ----------------------

def test_lookelsewhere_pvalue_for_9192_is_not_small():
    lee = C.lookelsewhere_pvalue()
    # Threshold justified as the conventional 0.05: a p above it means the
    # observed match is reproduced by chance more than 1 draw in 20, so it
    # cannot be evidence. The grid of >2000 expressions gives p ~ 0.35.
    assert lee["p_value"] > 0.05
    assert lee["p_value"] > 0.2
    assert lee["verdict"] == "NO_BETTER_THAN_CHANCE"
    assert 0.0 <= lee["p_value"] <= 1.0
    assert lee["grid_size"] == C.grid_size()


def test_lookelsewhere_is_deterministic_under_the_fixed_seed():
    assert (C.lookelsewhere_pvalue(n_samples=300)["p_value"]
            == C.lookelsewhere_pvalue(n_samples=300)["p_value"])


def test_a_tighter_tolerance_lowers_the_hit_rate():
    loose = C.lookelsewhere_pvalue(n_samples=400, tol_rel=1e-3)["p_value"]
    tight = C.lookelsewhere_pvalue(n_samples=400, tol_rel=1e-7)["p_value"]
    assert tight < loose


# --- description length: long expressions buy less ----------------------

def test_description_length_ranks_simple_below_convoluted():
    simple = C.CarrierExpression(
        "F_4096", Fraction(4096), Fraction(3, 4),
        C.CarrierOp.LITERAL_MULTIPLIER)
    convoluted = C.CarrierExpression(
        "N7_FIRST_MODE", C.F_CRYSTAL_N7_HZ, Fraction(5, 6),
        C.CarrierOp.BEAT_CS133_FULL, 7, False, C.CS133_HZ)
    assert C.description_length(simple) < C.description_length(convoluted)


def test_a_harmonic_order_costs_more_than_none():
    plain = C.CarrierExpression(
        "F_4096", Fraction(4096), Fraction(2, 3),
        C.CarrierOp.LITERAL_MULTIPLIER)
    overlaid = C.CarrierExpression(
        "F_4096", Fraction(4096), Fraction(2, 3),
        C.CarrierOp.LITERAL_MULTIPLIER, 7, False)
    assert C.description_length(overlaid) > C.description_length(plain)


def test_description_length_accepts_expression_text():
    assert (C.description_length("4096 * 3/4")
            < C.description_length("|13772.28 * 5/6 - 9192631770| / 7"))


# --- target fitting: labelled, or refused -------------------------------

def test_is_target_fitted_records_post_hoc_selection():
    assert C.is_target_fitted(True) is True
    assert C.is_target_fitted(False) is False


def test_refuse_carrier_selected_after_target_raises():
    with pytest.raises(C.CarrierError):
        C.refuse_carrier_selected_after_target()


def test_refuse_still_raises_even_when_the_label_is_applied():
    with pytest.raises(C.CarrierError):
        C.refuse_carrier_selected_after_target(label_applied=True)


def test_a_post_hoc_candidate_is_flagged_target_fitted():
    cands = C.search_carriers(9192, top_n=3,
                              selected_after_seeing_target=True)
    assert cands and all(c["target_fitted"] is True for c in cands)
    # a candidate never travels without its price tags
    for c in cands:
        assert c["residual_exact"]
        assert c["description_length"] > 0
        assert 0.0 <= c["lookelsewhere_p"] <= 1.0
        assert c["verdict"] == "CRYSTAL_CARRIER_CANDIDATE_ARITHMETIC_ONLY"


def test_a_prospective_candidate_is_not_flagged_target_fitted():
    cands = C.search_carriers(9192, top_n=1,
                              selected_after_seeing_target=False,
                              lookelsewhere_p=0.35)
    assert cands[0]["target_fitted"] is False


def test_search_rejects_a_nonpositive_target():
    with pytest.raises(C.CarrierError):
        C.search_carriers(0, top_n=1, lookelsewhere_p=0.35)


# --- report -------------------------------------------------------------

def test_report_measures_nothing_and_claims_no_physical_validation():
    rep = C.carrier_report()
    assert rep["measured_here"] == "nothing"
    assert rep["evidence_class"] == "DERIVED_MATHEMATICS"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["verdict"] == "CRYSTAL_CARRIER_CANDIDATE_ARITHMETIC_ONLY"
    assert rep["verdict"] == C.DEFAULT_VERDICT
    assert "does not say" in rep["what_this_does_not_say"]
    assert rep["public_alias"] == "CRYSTAL_CARRIER_CANDIDATE_A"


def test_report_carries_the_null_the_power_and_the_fitted_flag():
    rep = C.carrier_report()
    assert rep["lookelsewhere"]["verdict"] == "NO_BETTER_THAN_CHANCE"
    assert rep["power"]["detected"] is True
    assert rep["candidate"]["target_fitted"] is True
    assert rep["candidate"]["residual_exact"] == "262/25"
    assert "15.72" in rep["what_this_does_not_say"]


# --- R11 delta: the mandatory "0.03 Hz below" correction ---------------

def test_the_003_hz_below_candidate_is_13772_25_not_13788():
    """Mandatory delta correction. 13788 is NOT 0.03 Hz below the
    computed mode; 13772.25 is."""
    from fractions import Fraction
    assert C.NEAR_MODE_DIFFERENCE == Fraction(3, 100)          # exactly 0.03
    assert C.NEAR_MODE_CANDIDATE_HZ == Fraction(1377225, 100)  # 13772.25
    # and the old claim stays refuted, with its true value retained
    assert C.BASE_DIFFERENCE == Fraction(393, 25)              # 15.72
    assert C.BASE_DIFFERENCE != Fraction(3, 100)


def test_audit_carries_both_the_refutation_and_the_resolution():
    a = C.audit_high_priority_candidate()
    assert a["near_mode_candidate_hz"].startswith("13772.25")
    assert a["near_mode_difference_hz"].startswith("0.03")
    assert a["base_difference_hz"].startswith("15.72")
    assert a["base_difference_sign"] == "EXACT_BASE_IS_ABOVE_COMPUTED_MODE"
    assert a["pack_discrepancy_status"] == \
        "RESOLVED_CORRECTED_CANDIDATE_REGISTERED"
    # a 0.03 Hz step from a computed mode is rounding, not a carrier
    assert "rounding" in a["near_mode_note"]
