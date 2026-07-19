"""P03 — exact common-phase closure in multi-tone DDS.

The theorem is exact arithmetic over the rationals, so the tests are
exact too: no ``pytest.approx`` on any closure value. A float
implementation would agree to ten digits and hide the entire effect,
which is precisely the failure the paper is about.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from r8 import dds


CANON = (4096, 20480, 40960)
F100M = 10 ** 8
F2_26 = 2 ** 26


# --- synthesis quantum ------------------------------------------------

def test_quantum_is_exact_rational():
    q = dds.synthesis_quantum(F100M, 32)
    assert q == Fraction(10 ** 8, 2 ** 32)
    assert q == Fraction(5 ** 8, 2 ** 24)   # reduced form


def test_quantum_rejects_bad_inputs():
    with pytest.raises(ValueError):
        dds.synthesis_quantum(F100M, 0)
    with pytest.raises(ValueError):
        dds.synthesis_quantum(0, 32)


def test_binary_reference_has_dyadic_quantum():
    q = dds.synthesis_quantum(F2_26, 32)
    assert q == Fraction(1, 2 ** 6)
    assert q.numerator == 1


# --- exact representability -------------------------------------------

def test_decimal_reference_cannot_represent_dyadic_tones():
    for f in CANON:
        assert not dds.is_exactly_representable(f, F100M, 32)


def test_binary_reference_represents_them_all():
    for f in CANON:
        assert dds.is_exactly_representable(f, F2_26, 32)


def test_the_obstruction_is_the_factor_of_five():
    """100 MHz = 2^8 * 5^8; no power of two cancels 5^8."""
    assert 10 ** 8 == 2 ** 8 * 5 ** 8
    for n in range(8, 65):
        assert not dds.is_exactly_representable(4096, F100M, n)


# --- tuning words -----------------------------------------------------

def test_canonical_tuning_words():
    words = tuple(dds.tuning_word(f, F100M, 32) for f in CANON)
    assert words == (175922, 879609, 1759219)


def test_binary_tuning_words_match_the_contract():
    words = tuple(dds.tuning_word(f, F2_26, 32) for f in CANON)
    assert words == (262144, 1310720, 2621440)


def test_truncate_and_round_can_differ():
    r = dds.tuning_word(4096, F100M, 32, "ROUND")
    t = dds.tuning_word(4096, F100M, 32, "TRUNCATE")
    assert r == 175922 and t == 175921


def test_unknown_policy_rejected():
    with pytest.raises(ValueError):
        dds.tuning_word(4096, F100M, 32, "NEAREST_EVEN")


# --- the theorem ------------------------------------------------------

def test_closure_matches_the_contract_value_exactly():
    """T_q = 2^24 / 5^8 s, as an exact Fraction."""
    words = tuple(dds.tuning_word(f, F100M, 32) for f in CANON)
    t = dds.common_closure(words, F100M, 32)
    assert t == Fraction(2 ** 24, 5 ** 8)
    assert t == Fraction(16777216, 390625)
    assert float(t) == 42.94967296


def test_ideal_closure_is_one_over_4096():
    assert dds.ideal_closure(CANON) == Fraction(1, 4096)


def test_degradation_factor_is_not_the_tidy_integer():
    """The exact ratio is 2^36/5^8 = 175921.8604..., NOT 175922.

    This test exists because the first version of it asserted the
    integer, which is wrong in the direction that looks tidier. The
    near-collision is structural, not coincidental: the ratio IS the
    unrounded tuning word of the fundamental, and 175922 is that
    word's rounding. Two different quantities, one of which is a
    frequency-setting integer and the other a dimensionless ratio.
    """
    rep = dds.analyze(CANON, F100M, 32)
    ratio = (Fraction(rep.quantized_closure_s)
             / Fraction(rep.ideal_closure_s))
    assert ratio == Fraction(2 ** 36, 5 ** 8)
    assert ratio != 175922
    assert ratio.denominator != 1
    assert float(ratio) == pytest.approx(175921.86044416)


def test_degradation_equals_unrounded_fundamental_word():
    """The corollary: ratio = W_fund / gcd(K_i)."""
    d = dds.degradation_factor(CANON, F100M, 32)
    assert d["closed_form_matches"]
    assert not d["is_integer"]
    assert Fraction(d["unrounded_fundamental_word"]) == \
        Fraction(2 ** 36, 5 ** 8)


@pytest.mark.parametrize("tones,ref,bits", [
    ((4096, 20480, 40960), 10 ** 8, 32),
    ((1000, 3000), 10 ** 8, 32),
    ((440, 880, 1320), 10 ** 8, 24),
    ((4096, 20480, 40960), 2 ** 26, 32),
])
def test_corollary_holds_across_configurations(tones, ref, bits):
    assert dds.degradation_factor(tones, ref, bits)["closed_form_matches"]


def test_binary_reference_preserves_ideal_closure_exactly():
    rep = dds.analyze(CANON, F2_26, 32)
    assert rep.closure_preserved
    assert Fraction(rep.quantized_closure_s) == Fraction(1, 4096)
    assert rep.all_exact
    assert Fraction(rep.max_frequency_error_hz) == 0


def test_theorem_against_brute_force_on_a_small_case():
    """Independent check of T = q/(p*gcd K) by direct search.

    Small enough to enumerate, which is the only honest way to
    validate a closed form.
    """
    ref, n = 48, 4          # quantum = 48/16 = 3 Hz
    words = (2, 3)          # tones 6 Hz and 9 Hz
    t = dds.common_closure(words, ref, n)
    # brute force: smallest k/den with both f_i*T integral
    realized = [dds.realized_frequency(w, ref, n) for w in words]
    # collect ALL closing candidates and take the minimum. Taking the
    # first hit in iteration order finds T=1 before T=1/3 and would
    # have silently "confirmed" a wrong closed form.
    closing = [
        Fraction(num, den)
        for den in (1, 2, 3, 4, 6, 12)
        for num in range(1, 40)
        if all((f * Fraction(num, den)).denominator == 1
               for f in realized)
    ]
    assert min(closing) == t == Fraction(1, 3)


def test_gcd_of_words_shortens_closure():
    """Common factor in the tuning words divides the closure."""
    a = dds.common_closure((2, 4), F100M, 32)
    b = dds.common_closure((2, 3), F100M, 32)
    assert a == b / 2


def test_closure_refuses_degenerate_input():
    with pytest.raises(dds.DDSRefused):
        dds.common_closure((), F100M, 32)
    with pytest.raises(dds.DDSRefused):
        dds.common_closure((0, 4), F100M, 32)
    with pytest.raises(dds.DDSRefused):
        dds.ideal_closure(())


# --- corollary 1: resolution does not buy exactness -------------------

def test_no_accumulator_width_recovers_exactness():
    rep = dds.resolution_does_not_help(CANON, F100M)
    assert not rep["any_width_exact"]
    assert not any(r["closure_preserved"] for r in rep["rows"])


def test_frequency_error_falls_monotonically_with_width():
    rep = dds.resolution_does_not_help(CANON, F100M)
    errs = [Fraction(r["max_frequency_error_hz"]) for r in rep["rows"]]
    assert all(a > b for a, b in zip(errs, errs[1:]))


# --- the headline: anti-correlation -----------------------------------

def test_accuracy_and_closure_are_anticorrelated():
    """Widening the accumulator improves the quoted specification and
    destroys the unquoted one."""
    rep = dds.accuracy_closure_tradeoff(CANON, F100M)
    assert rep["anticorrelated"]
    assert rep["frequency_error_improvement"] > 1e10
    assert rep["closure_degradation"] > 1e10


def test_closure_degrades_monotonically_with_width():
    rep = dds.accuracy_closure_tradeoff(CANON, F100M)
    ratios = [r["closure_ratio"] for r in rep["rows"]]
    assert all(a < b for a, b in zip(ratios, ratios[1:]))


def test_binary_reference_is_immune_to_the_tradeoff():
    """The anti-correlation is a property of the reference, not of DDS."""
    rep = dds.accuracy_closure_tradeoff(CANON, F2_26)
    assert all(r["all_exact"] for r in rep["rows"])
    assert all(r["closure_ratio"] == 1.0 for r in rep["rows"])


# --- reference selection ----------------------------------------------

def test_usable_dyadic_reference_respects_nyquist():
    """The bug this test exists for: without an oversampling floor the
    search returns a 2 Hz reference for a 40960 Hz tone, which is
    arithmetically exact and physically impossible."""
    e = dds.exact_reference_exists(CANON)
    assert e["all_exact"]
    assert e["reference_hz"] >= max(CANON) * 10
    assert e["oversample_achieved"] >= 10


def test_oversample_below_nyquist_is_refused():
    with pytest.raises(ValueError):
        dds.exact_reference_exists(CANON, min_oversample=1)


def test_higher_oversample_demands_a_bigger_reference():
    a = dds.exact_reference_exists(CANON, min_oversample=10)
    b = dds.exact_reference_exists(CANON, min_oversample=1000)
    assert b["reference_hz"] > a["reference_hz"]


def test_2_26_is_a_valid_choice_for_the_canonical_set():
    assert dds.is_exactly_representable(4096, F2_26, 32)
    rep = dds.analyze(CANON, F2_26, 32)
    assert rep.closure_preserved


# --- report integrity -------------------------------------------------

def test_report_round_trips_and_carries_no_floats_for_exact_values():
    rep = dds.analyze(CANON, F100M, 32).as_record()
    for key in ("ideal_closure_s", "quantized_closure_s", "quantum_hz",
                "max_frequency_error_hz"):
        Fraction(rep[key])          # must parse exactly
    assert isinstance(rep["tuning_words"], list)


def test_note_explains_the_cause_as_arithmetic():
    rep = dds.analyze(CANON, F100M, 32)
    assert "arithmetic, not noise" in rep.note
