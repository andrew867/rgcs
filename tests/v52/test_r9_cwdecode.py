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
    resid = res["SEGMENT_RESIDUAL_PREFIX"]
    assert resid.observed == 5
    assert resid.null_mean > 4.0
    assert not resid.significant


def test_residual_prefix_test_has_power():
    """It must be capable of firing, or it proves nothing."""
    planted = [123456789011, 123456789012, 123456789013,
               123456789014, 123456789015]
    res = {x.test: x for x in D.segment_analysis(planted)}
    assert res["SEGMENT_RESIDUAL_PREFIX"].observed >= 10


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


def test_bit_stage_reproduces_the_r7_result():
    """Independent route to R7's zero informative bits."""
    res = D.bit_analysis()[0]
    assert res.observed == 0
    assert not res.informative


def test_three_framings_agree():
    """Convergence across framings that could have disagreed."""
    r = D.report()
    assert "could have disagreed and did not" in r["convergence_note"]
    assert r["content_findings"] == []


def test_vectors_are_not_more_structured_than_matched_random():
    """The prefix null mean sits at or above the observed value."""
    res = {x.test: x for x in D.segment_analysis()}
    assert res["SEGMENT_RESIDUAL_PREFIX"].null_mean >= 4.0


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
