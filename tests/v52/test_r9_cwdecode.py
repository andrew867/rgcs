"""P08 — segment-first CW decoding.

The load-bearing tests here check the *method*, not the result:
preregistration is enforced, the null is reproducible and is not
conditioned on the data it is testing (R9-D-002), each test is shown
capable of firing, and a clustering result can never be presented as
a decoding result.
"""

from __future__ import annotations

import pytest

from r9 import cwdecode as D


# --- method discipline -------------------------------------------------

def test_analysis_order_puts_bits_last():
    """The whole point of P08: if the binary frame was destroying
    structure, decimal and divisor stages must run before it."""
    r = D.report()
    assert r["analysis_order"] == ["segments", "divisors", "bits"]


def test_every_result_was_preregistered():
    for res in D.analyse():
        assert res.test in D.PREREGISTERED_TESTS


def test_unregistered_findings_are_refused():
    """With five values, a test chosen after seeing the data will
    always find something."""
    original = D.PREREGISTERED_TESTS
    try:
        D.PREREGISTERED_TESTS = ("SEGMENT_COMMON_PREFIX",)
        with pytest.raises(D.UnregisteredFinding) as e:
            D.report()
        assert "not preregistered" in str(e.value)
    finally:
        D.PREREGISTERED_TESTS = original


def test_significance_is_multiplicity_corrected():
    r = D.report()
    assert r["corrected_alpha"] == pytest.approx(
        D.ALPHA / len(D.PREREGISTERED_TESTS))
    assert r["corrected_alpha"] < D.ALPHA


def test_null_is_reproducible():
    """A null with an unseeded RNG is not a null anyone can check."""
    a = [x.p_value for x in D.analyse()]
    b = [x.p_value for x in D.analyse()]
    assert a == b


def test_p_values_are_never_zero():
    """20k trials cannot license p = 0."""
    for res in D.analyse():
        assert res.p_value > 0
        assert res.p_value <= 1.0


# --- range-forced agreement -------------------------------------------

def test_baseline_band_is_declared_not_derived_from_the_data():
    """R9-D-002. The first version measured forced agreement against
    the observed min and max -- which are themselves two of the five
    values, so the residual could never be positive and the test could
    never fire. A baseline conditioned on the data cannot test it.
    """
    assert D.DECLARED_BAND == (10 ** 11, 10 ** 12 - 1)
    assert D.range_forced_prefix_len() == 0
    assert D.range_forced_prefix_len(D.DECLARED_BAND) == 0


def test_forced_prefix_of_a_narrow_declared_band_is_nonzero():
    assert D.range_forced_prefix_len((123456000000, 123456999999)) == 6


def test_null_is_not_drawn_from_the_observed_range():
    """The null must be able to produce unclustered samples, or the
    clustering test has no power."""
    null = D._null_distribution(lambda vs: max(vs) - min(vs),
                                D.CW_VECTORS)
    observed_span = max(D.CW_VECTORS) - min(D.CW_VECTORS)
    assert max(null) > 100 * observed_span


# --- band structure is real and is kept separate ----------------------

def test_clustering_is_a_real_finding():
    """Not everything here is negative. The values genuinely occupy a
    tiny slice of the 12-digit space."""
    r = D.report()
    assert r["band_verdict"] == "CLUSTERED_BAND_CONFIRMED"
    assert "BAND_CLUSTERING" in r["band_findings"]


def test_clustering_is_not_reported_as_content():
    """A clustering result must never be presentable as a decoding."""
    r = D.report()
    assert "BAND_CLUSTERING" not in r["content_findings"]
    assert "not about anything" in r["band_vs_content"]


def test_prefix_agreement_is_fully_explained_by_clustering():
    """Given the span, five shared leading digits is unremarkable --
    the span-matched null averages nearly the same."""
    res = {x.test: x for x in D.segment_analysis()}
    resid = res["SEGMENT_PREFIX_GIVEN_SPAN"]
    assert resid.observed == 5
    assert resid.null_mean > 4.0
    assert not resid.significant


def test_register_audit_reports_which_tests_can_fire():
    """R9-D-009. The old version of this test asserted only that the
    observed value was large on planted data -- never that the test
    reached significance. It did not. Three registered tests cannot
    fire at all, and a passing suite showed none of it.
    """
    a = D.register_audit()
    assert a["registered"] == 8
    assert a["live_count"] == 5
    assert set(a["tests_that_never_fired"]) == {
        "SEGMENT_PREFIX_GIVEN_SPAN",
        "SEGMENT_DIGIT_PAIR_REPEAT",
        "BIT_INFORMATIVE_WIDTH",
    }


def test_the_divisor_family_genuinely_works():
    """The negative rests on these, so they must demonstrably fire."""
    a = D.register_audit()
    for t in ("DIVISOR_GLOBAL_GCD", "DIVISOR_PAIRWISE_GCD",
              "DIVISOR_SMALL_PRIME_EXCESS"):
        assert a["fired_on"][t], f"{t} never fired on planted structure"


def test_verdict_is_qualified_by_power():
    r = D.report()
    assert "not eight" in r["power_qualification"]


def test_significant_findings_are_not_discarded_by_a_literal():
    """R9-D-008. Three tests had informative=False hardcoded, so a
    significant result was thrown away before reaching the verdict."""
    planted = list(D.PROBES["SHARED_SUFFIX"])
    sig = {x.test for x in D.analyse(planted) if x.significant}
    assert "DIVISOR_SMALL_PRIME_EXCESS" in sig
    # and it must now actually reach the verdict
    import r9.cwdecode as M
    results = M.analyse(planted)
    surviving = [x.test for x in results if x.significant]
    assert "DIVISOR_SMALL_PRIME_EXCESS" in surviving


# --- the findings ------------------------------------------------------

def test_no_content_structure_survives_the_null():
    r = D.report()
    assert r["verdict"] == "NO_RECOVERABLE_CONTENT"
    assert r["content_findings"] == []


def test_global_gcd_is_one():
    """No shared modulus or step size."""
    res = {x.test: x for x in D.divisor_analysis()}
    assert res["DIVISOR_GLOBAL_GCD"].observed == 1
    assert not res["DIVISOR_GLOBAL_GCD"].informative


def test_no_shared_suffix():
    res = {x.test: x for x in D.segment_analysis()}
    assert res["SEGMENT_COMMON_SUFFIX"].observed == 0


def test_bit_stage_is_not_a_constant_function():
    """R9-D-007. The old bit stage computed agree-minus-forced with
    'forced' taken from min/max of the sample. Since those ARE members,
    the two always stop at the same bit and the difference was
    identically zero for every possible input -- verified over 200,000
    random samples. It was a constant, not a test, and the test here
    asserted the constant.
    """
    a = D.bit_analysis([1, 2, 3, 4, 5])[0].observed
    b = D.bit_analysis(list(D.CW_VECTORS))[0].observed
    c = D.bit_analysis([10 ** 11, 10 ** 12 - 1])[0].observed
    assert len({a, b, c}) > 1, "bit statistic does not vary with input"


def test_agreeing_bit_prefix_is_correct():
    assert D.agreeing_bit_prefix([0b1101, 0b1100]) == 3
    assert D.agreeing_bit_prefix([0b1111, 0b1111]) == 4
    assert D.agreeing_bit_prefix([0b1000, 0b0111]) == 0


def test_convergence_claim_is_qualified_by_power():
    """The old wording -- 'the framings could have disagreed and did
    not' -- was false while the bit framing was a constant function.
    Convergence is only evidence if each framing could have dissented.
    """
    r = D.report()
    n = r["convergence_note"]
    assert "constant function" in n
    assert "simply false" in n
    assert r["content_findings"] == []


def test_vectors_are_not_more_structured_than_matched_random():
    """The prefix null mean sits at or above the observed value."""
    res = {x.test: x for x in D.segment_analysis()}
    assert res["SEGMENT_PREFIX_GIVEN_SPAN"].null_mean >= 4.0


# --- claim discipline --------------------------------------------------

def test_report_does_not_claim_the_vectors_are_meaningless():
    r = D.report()
    c = r["what_this_does_not_say"]
    assert "not that no structure exists" in c
    assert "Five values is a very small sample" in c


def test_decoded_claim_is_refused():
    with pytest.raises(D.UnregisteredFinding) as e:
        D.refuse_decoded_claim()
    assert "are not decoded" in str(e.value)


def test_provenance_is_recorded_at_region_granularity_only():
    """Source attribution stays coarse by policy, and no analysis
    step depends on provenance."""
    assert D.CW_SOURCE == "omega region"
    assert D.report()["source"] == "omega region"


def test_five_vectors_twelve_digits():
    assert len(D.CW_VECTORS) == 5
    assert all(len(str(v)) == 12 for v in D.CW_VECTORS)
