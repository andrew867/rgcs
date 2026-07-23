"""P05 — the 1604/1644 cues: near-miss residual, look-elsewhere null, power."""

from __future__ import annotations

import math

import pytest

from r10 import cue1604 as C


# --- the cues: spoken digits are kept distinct from the integer ---------

def test_spoken_digits_are_a_field_distinct_from_the_value():
    assert C.CUE_1604.spoken_text == "1-6-0-4"
    assert C.CUE_1604.spoken_digits == (1, 6, 0, 4)
    assert C.CUE_1604.parsed_value == 1604
    # a digit readback is only an interpretation, not identical to the int
    assert C.CUE_1604.spoken_digits != C.CUE_1604.parsed_value


def test_base10_reading_of_the_digits_is_one_interpretation():
    assert C.CUE_1604.digits_match_value()
    assert C.CUE_1644.digits_match_value()


# --- exact / near residuals --------------------------------------------

def test_925_root3_value():
    assert C.k_root3 == pytest.approx(1602.146997001211, abs=1e-9)
    assert 925 * math.sqrt(3) == C.k_root3


def test_residual_hz_is_about_1p853():
    r = C.root3_residual()
    assert r["residual_hz"] == pytest.approx(1.853002998788497, abs=1e-9)


def test_relative_residual_both_normalisations():
    r = C.root3_residual()
    # relative to the target 1604 (the written formula)
    assert r["relative_residual"] == pytest.approx(0.0011552387773, abs=1e-10)
    # relative to 925*sqrt(3) itself (~0.115657489747%)
    assert r["relative_residual_vs_root3"] == pytest.approx(
        0.00115657489747, abs=1e-12)
    # a ~0.12% match is a near-miss, never an identity
    assert r["verdict"] == "APPROXIMATE_NOT_EXACT"
    assert not r["are_equal"]
    assert r["k_root3_is_exact"] is False


def test_difference_is_exactly_40_with_no_meaning():
    d = C.difference()
    assert d["difference"] == 40
    assert d["is_exact"] is True
    assert d["meaning_assigned"] is False


# --- POWER: a planted exact grid target is recovered -------------------

def test_power_search_recovers_a_planted_exact_expression():
    p = C.power_check()
    assert p["detected"] is True
    assert p["recovered"]["relative_residual"] < 1e-12
    assert p["recovered"]["a"] == 30 and p["recovered"]["b"] == 5


def test_best_grid_hit_finds_the_exact_a_sqrt_b():
    hit = C.best_grid_hit(30 * math.sqrt(5))
    assert hit["relative_residual"] == pytest.approx(0.0, abs=1e-12)


# --- NULL: the 1604 near-miss is no better than chance -----------------

def test_lookelsewhere_pvalue_is_not_tiny():
    lee = C.lookelsewhere_pvalue()
    # with the preregistered grid, a random target is matched essentially
    # always -> p is large, not tiny
    assert lee["p_value"] > 0.5
    assert lee["verdict"] == "NO_BETTER_THAN_CHANCE"
    # the p-value is reported alongside the residual, never suppressed
    assert 0.0 <= lee["p_value"] <= 1.0


def test_lookelsewhere_is_deterministic_under_the_fixed_seed():
    assert (C.lookelsewhere_pvalue()["p_value"]
            == C.lookelsewhere_pvalue()["p_value"])


# --- REFUSALS -----------------------------------------------------------

def test_refuse_exact_claim_raises():
    with pytest.raises(C.CueError):
        C.refuse_exact_claim()


def test_refuse_meaning_for_difference_raises():
    with pytest.raises(C.CueError):
        C.refuse_meaning_for_difference("an interval")


# --- report -------------------------------------------------------------

def test_report_measures_nothing_and_claims_no_physical_validation():
    rep = C.cue1604_report()
    assert rep["measured_here"] == "nothing"
    assert rep["evidence_class"] == "DERIVED_MATHEMATICS"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["verdict"] == "APPROXIMATE_NOT_EXACT"
    assert rep["lookelsewhere"]["verdict"] == "NO_BETTER_THAN_CHANCE"
    assert "does not say" in rep["what_this_does_not_say"]
