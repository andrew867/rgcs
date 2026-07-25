"""P47 — Selection-bias firewall: look-everywhere inflation corrected.

POWER: a genuinely tight match in a small search space is significant.
Negative: inflating the search space (many candidates x catalogue) raises the
adjusted probability toward chance; a catalogue match is refused as evidence
without a prospective test. Deterministic.
"""

from __future__ import annotations

import pytest

from cwatlas import catalogue_firewall as F
from cwatlas.claims import ClaimClass, ClaimError


CAT = F.build_synthetic_catalogue()
# A candidate that sits exactly on the first catalogue entry.
ON_ENTRY = CAT[0].point


# --- POWER / correction behaviour --------------------------------------------

def test_reports_search_space_size():
    res = F.score_candidate(ON_ENTRY, CAT, match_radius_m=1_000.0,
                            n_candidates=10)
    assert res.search_space_size == 10 * len(CAT)


def test_selection_bias_inflation_raises_adjusted_p():
    small = F.score_candidate(ON_ENTRY, CAT, match_radius_m=50_000.0,
                              n_candidates=1)
    large = F.score_candidate(ON_ENTRY, CAT, match_radius_m=50_000.0,
                              n_candidates=100_000)
    # Same nominal per-comparison probability, larger search space.
    assert small.per_comparison_p == large.per_comparison_p
    assert large.adjusted_p > small.adjusted_p
    assert large.expected_chance_hits > small.expected_chance_hits


def test_tight_match_small_space_is_significant():
    res = F.score_candidate(ON_ENTRY, CAT, match_radius_m=100.0,
                            n_candidates=1, alpha=0.05)
    assert res.significant_after_correction is True


def test_huge_search_space_kills_significance():
    res = F.score_candidate(ON_ENTRY, CAT, match_radius_m=200_000.0,
                            n_candidates=1_000_000, alpha=0.05)
    assert res.significant_after_correction is False
    assert res.claim_class == ClaimClass.MATHEMATICAL_TRANSLATION.value


def test_hit_count_detects_on_entry():
    res = F.score_candidate(ON_ENTRY, CAT, match_radius_m=1_000.0)
    assert res.hit_count >= 1


# --- Negative: no catalogue match as evidence without prospective test --------

def test_match_is_not_evidence_without_prospective_test():
    res = F.score_candidate(ON_ENTRY, CAT, match_radius_m=100.0,
                            n_candidates=1, prospective_test_passed=False)
    assert res.is_evidence is False
    with pytest.raises(ClaimError):
        F.assert_catalogue_match_is_evidence(res)


def test_significant_without_prospective_is_only_hypothesis():
    res = F.score_candidate(ON_ENTRY, CAT, match_radius_m=100.0,
                            n_candidates=1, prospective_test_passed=False)
    assert res.significant_after_correction is True
    assert res.claim_class == ClaimClass.OPERATOR_HYPOTHESIS.value


def test_evidence_requires_significance_and_prospective():
    res = F.score_candidate(ON_ENTRY, CAT, match_radius_m=100.0,
                            n_candidates=1, prospective_test_passed=True)
    assert res.is_evidence is True
    assert res.claim_class == ClaimClass.CALIBRATED_MAPPING.value
    F.assert_catalogue_match_is_evidence(res)  # does not raise


def test_refuse_catalogue_match_as_evidence_raises():
    with pytest.raises(ClaimError):
        F.refuse_catalogue_match_as_evidence()


# --- Negative: malformed inputs ----------------------------------------------

def test_empty_catalogue_refused():
    with pytest.raises(F.FirewallError):
        F.score_candidate(ON_ENTRY, (), match_radius_m=100.0)


def test_bad_radius_refused():
    with pytest.raises(F.FirewallError):
        F.score_candidate(ON_ENTRY, CAT, match_radius_m=0.0)


def test_bad_n_candidates_refused():
    with pytest.raises(F.FirewallError):
        F.score_candidate(ON_ENTRY, CAT, match_radius_m=100.0, n_candidates=0)


# --- Determinism --------------------------------------------------------------

def test_scoring_is_deterministic():
    a = F.score_candidate(ON_ENTRY, CAT, match_radius_m=100.0, n_candidates=7)
    b = F.score_candidate(ON_ENTRY, CAT, match_radius_m=100.0, n_candidates=7)
    assert a == b


def test_report_declares_boundary():
    r = F.catalogue_firewall_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["look_everywhere_corrected"] is True
