"""P02 (A04-A07): coordinates, powers-of-eight ladder, frozen
simplicity metric, matched nulls, corpus decoder.

The load-bearing tests here are the metric-freeze pin (a metric edited
after seeing results is not a test) and the two controls that validate
the metric detects rational structure without merely detecting "tidy
frequency table".
"""
from __future__ import annotations

from fractions import Fraction

import pytest


# --- A04 coordinates ----------------------------------------------------

def test_coordinate_round_trip_is_exact_over_broad_range():
    """Property: decompose->reconstruct is exact for many magnitudes,
    radices and references. A float implementation would drift."""
    from cspc.coordinates import decompose
    freqs = ["0.03565219230949878692626953125", "8", "18.25392246246337890625",
             "4096", "20480", "32768", "2450000000", "562949953421312",
             "1", "7", "99991", "1/3", "22/7"]
    for ref in ("SRC_2_45_GHZ", "F_4096", "F_8", "F_1HZ"):
        for radix in (2, 8, 10):
            for f in freqs:
                c = decompose(f, ref, radix)
                assert c.exact_round_trip, (f, ref, radix)
                assert 1 <= c.residual < radix


def test_compose_inverts_decompose():
    from cspc.coordinates import compose, decompose
    c = decompose("20480", "F_4096", 2)
    assert compose(c.reference_hz, 2, c.level, c.residual) == \
        Fraction(20480)


def test_exact_ladder_rungs_are_flagged_exact():
    from cspc.coordinates import decompose
    # 2.45e9 / 8^9 sits exactly on a rung
    c = decompose("18.25392246246337890625", "SRC_2_45_GHZ", 8)
    assert c.is_exact_power and c.level == -9


def test_decompose_rejects_bad_input():
    from cspc.coordinates import CoordinateError, decompose
    with pytest.raises(CoordinateError):
        decompose("100", "F_4096", 7)          # illegal radix
    with pytest.raises(CoordinateError):
        decompose("0", "F_4096", 8)            # non-positive


# --- A05 ladder naming (CSPC-CORR-003) ----------------------------------

def test_eighth_power_level_is_reported_as_three_octaves_each():
    from cspc.coordinates import decode_to_ladder, eight_ladder
    rungs = eight_ladder(levels=11)
    assert rungs[11].octaves_below_reference == 33
    assert Fraction(8) ** 11 == Fraction(2) ** 33
    d = decode_to_ladder("0.28521753847599029541015625")
    assert d["nearest_fold_level"] == 11
    assert d["octaves_below_reference"] == 33
    assert "not 11" in d["note"]


def test_ladder_rung_decimals_match_the_register():
    from cspc.coordinates import eight_ladder
    rungs = {r.level: r.exact_decimal for r in eight_ladder(levels=11)}
    assert rungs[9] == "18.25392246246337890625"
    assert rungs[5] == "74768.06640625"


def test_inexact_hit_is_not_rounded_into_a_rung():
    from cspc.coordinates import decode_to_ladder
    d = decode_to_ladder("19.0")
    assert d["exact_rung"] is False
    assert d["residual_ratio"] != 1


# --- A06 frozen metric --------------------------------------------------

def test_metric_is_frozen_and_pinned():
    """If the metric is edited, this fingerprint changes and the test
    fails — which is the point. A metric tuned after seeing results is
    not a test."""
    from cspc.nulls import METRIC_SPEC, metric_fingerprint
    assert "no free parameters" in METRIC_SPEC.lower()
    assert "frozen" in METRIC_SPEC.lower()
    assert metric_fingerprint() == \
        "e2456bca5110ed845dbd84ca25868df8c8d40c860105eec51e6f9fb6b92280b6"


def test_simplicity_orders_simple_ratios_below_complex_ones():
    from cspc.nulls import simplicity
    octave = simplicity(880, 440)          # 2/1
    fifth = simplicity(660, 440)           # 3/2
    ugly = simplicity(Fraction(440777, 1000), 440)
    assert octave < fifth < ugly


def test_null_draw_is_deterministic_and_denominator_matched():
    """Regression for CSPC-D-003: nulls must match the observed set's
    arithmetic granularity, not just its magnitude range. An unmatched
    null made every corpus look 'simpler than chance', including
    deliberate controls."""
    from cspc.nulls import matched_null_draw
    obs = [Fraction(32768), Fraction(65536), Fraction(4194304)]
    a = matched_null_draw(obs, seed=7)
    b = matched_null_draw(obs, seed=7)
    assert a == b                                  # deterministic
    assert all(x.denominator == 1 for x in a)      # integers stay integers
    obs2 = [Fraction(2048, 100), Fraction(4096, 100)]
    assert all(x.denominator <= 100 for x in matched_null_draw(obs2, 7))


def test_permutation_test_reports_effect_size_and_ci_not_just_p():
    from cspc.nulls import permutation_test
    r = permutation_test([Fraction(880), Fraction(660), Fraction(440)],
                         Fraction(440), n_null=100, seed=1)
    d = r.to_dict()
    for key in ("p_value", "effect_size", "ci95_low", "ci95_high",
                "null_sd", "metric_fingerprint"):
        assert key in d
    assert r.evidence_class == "NUMERICAL_SIMULATION"


def test_null_not_rejected_is_a_first_class_result():
    from cspc.nulls import permutation_test
    r = permutation_test([Fraction(1000003), Fraction(1000033),
                          Fraction(1000037)], Fraction(7), n_null=100,
                         seed=3)
    if r.p_value > 0.05:
        assert "NULL NOT REJECTED" in r.interpretation


def test_multiple_comparison_corrections_are_applied():
    from cspc.nulls import family_report
    pv = {f"t{i}": 0.04 for i in range(10)}
    rep = family_report(pv)
    assert rep["n_tests"] == 10
    # 10 tests at p=0.04 must not all survive FWER
    assert not rep["any_survives_fwer"]
    assert all(v["p_adjusted"] >= v["p_raw"]
               for v in rep["holm"].values())


# --- A07 corpus validation ----------------------------------------------

def test_positive_control_rational_ratios_are_detected():
    """Just intonation is small-integer by definition; if the metric
    misses it the metric is broken."""
    from cspc.corpus import JUST_INTONATION, analyse
    r = analyse("JUST_INTONATION", JUST_INTONATION, Fraction(4096),
                "F_4096", n_null=200)
    assert r.result.p_value < 0.05
    assert r.result.effect_size < 0


def test_irrational_control_is_not_detected_as_simple():
    """Equal temperament is 2^(n/12) — irrational by construction. A
    rational-ratio metric must NOT rank it simple, or it is merely
    detecting 'is a frequency table'."""
    from cspc.corpus import EQUAL_TEMPERAMENT, analyse
    r = analyse("EQUAL_TEMPERAMENT", EQUAL_TEMPERAMENT, Fraction(4096),
                "F_4096", n_null=200)
    assert r.result.p_value > 0.05


def test_own_candidates_are_flagged_circular():
    """The programme's register is built from 2.45 GHz / 4096 / powers
    of two, so scoring simple against them is construction, not
    discovery."""
    from cspc.corpus import analyse, cspc_candidates
    r = analyse("CSPC_CANDIDATES", cspc_candidates(),
                Fraction(2450000000), "SRC_2_45_GHZ", n_null=100)
    assert r.circularity_warning is not None
    assert "CIRCULAR" in r.circularity_warning


def test_panel_is_corrected_and_carries_claim_boundary():
    from cspc.corpus import run_panel
    rep = run_panel(n_null=60)
    assert rep["n_tests"] >= 16
    assert "family" in rep and "holm" in rep["family"]
    assert "nothing here is evidence" in rep["claim_boundary"].lower()
    assert rep["evidence_class"] == "NUMERICAL_SIMULATION"


def test_panel_is_deterministic_by_seed():
    from cspc.corpus import run_panel
    a = run_panel(n_null=40, seed=99)
    b = run_panel(n_null=40, seed=99)
    assert [r["p_value"] for r in a["results"]] == \
           [r["p_value"] for r in b["results"]]
