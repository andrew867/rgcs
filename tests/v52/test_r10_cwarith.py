"""P08/P09 — CW arithmetic and the null hierarchy.

The arithmetic tests are easy and would pass on any correct
implementation. The load-bearing tests are the ones about the NULL:
that both nulls are implemented, that they disagree, and that the
verdict follows the defensible one.
"""

from __future__ import annotations

import pytest

from r10 import cwarith as A


# --- exactness ---------------------------------------------------------

def test_the_offered_relations_are_exactly_true():
    """They are. That was never in question."""
    assert all(A.verify_all().values())
    assert A.verify((1496, 20), 1516)
    assert A.verify((1496, 20, 644), 2160)


def test_verification_is_exact_not_approximate():
    assert not A.verify((1496, 20), 1517)
    assert not A.verify((1496, 21), 1516)


def test_alternate_branch_misses_by_one():
    b = A.alternate_branch()
    assert b["yields"] == 2161
    assert not b["reaches_target"]
    assert b["off_by"] == 1
    assert "not a second independent confirmation" in b["note"]


# --- independence ------------------------------------------------------

def test_three_relations_are_two_facts():
    """Given 1516=1496+20 and 2160=1516+644, the third follows."""
    c = A.independent_relation_count()
    assert c["offered"] == 3
    assert c["independent"] == 2
    assert c["implied"][0]["status"] == "IMPLIED_BY_OTHERS"
    assert "inflates the apparent weight" in c["note"]


# --- the closure finding -----------------------------------------------

def test_the_set_is_exactly_a_partial_sum_closure():
    """The single most important fact in this module."""
    c = A.is_partial_sum_closure(A.CW_INTEGER_SET)
    assert c["is_closure"]
    a, b, cc = c["generators"]
    assert sorted([a, b, cc, a + b, a + b + cc]) == sorted(A.CW_INTEGER_SET)


def test_closure_detector_rejects_a_non_closure():
    """Control: it must not call everything a closure."""
    assert not A.is_partial_sum_closure([2, 3, 5, 7, 11])["is_closure"]
    assert not A.is_partial_sum_closure([1, 10, 100, 1000, 10000])["is_closure"]


def test_closure_detector_finds_a_planted_closure():
    a, b, c = 37, 41, 53
    planted = [a, b, c, a + b, a + b + c]
    found = A.is_partial_sum_closure(planted)
    assert found["is_closure"]
    assert sorted(found["generators"]) == sorted([a, b, c])


# --- the two nulls -----------------------------------------------------

def test_relation_counting_is_correct():
    assert A.count_relations([1, 2, 3]) == 1          # 1+2=3
    assert A.count_relations([1, 2, 4, 8]) == 0
    assert A.count_relations(A.CW_INTEGER_SET) == 3


def test_naive_null_makes_the_relations_look_remarkable():
    n = A.naive_null(trials=20_000)
    assert n["p_value"] < 1e-3
    assert "strawman" in n["why_wrong"] or "wrong" in n["why_wrong"]


def test_selection_process_null_makes_them_certain():
    """Every partial-sum closure has these relations."""
    s = A.selection_process_null(trials=2_000)
    assert s["p_value"] == 1.0


def test_the_two_nulls_disagree_by_orders_of_magnitude():
    """This gap IS the finding: choosing the null chooses the answer."""
    h = A.null_hierarchy()
    assert h["naive_null"]["p_value"] < 1e-3
    assert h["selection_process_null"]["p_value"] == 1.0
    assert h["p_value_ratio"] > 1_000
    assert "Choosing the null is choosing the answer" in h["lesson"] or \
        "choosing the answer" in h["lesson"]


def test_verdict_is_explained_by_construction():
    h = A.null_hierarchy()
    assert h["verdict"] == "EXPLAINED_BY_CONSTRUCTION"


def test_verdict_flips_for_a_set_that_is_not_a_closure():
    """The verdict must be capable of coming out the other way, or it
    is not a test of anything."""
    assert not A.is_partial_sum_closure([3, 5, 7, 11, 13])["is_closure"]


# --- description length ------------------------------------------------

def test_mdl_shows_the_set_is_redundant():
    m = A.mdl_score()
    assert m.compresses
    assert m.saved_bits > 0


def test_mdl_does_not_compress_an_incompressible_set():
    m = A.mdl_score([3, 5, 7, 11, 13])
    assert not m.compresses
    assert m.saved_bits == 0


# --- claim discipline --------------------------------------------------

def test_the_negative_is_not_overstated():
    """'Explained by construction' is not 'meaningless'."""
    w = A.null_hierarchy()["what_this_does_not_say"]
    assert "does not say the numbers are meaningless" in w
    assert "remain so" in w or "exactly true" in w


def test_semantic_decoding_is_refused():
    with pytest.raises(A.SemanticDecodeRefused) as e:
        A.refuse_semantic_decoding()
    assert "semantically empty" in str(e.value)


def test_source_authentication_is_refused():
    with pytest.raises(A.SemanticDecodeRefused) as e:
        A.refuse_source_authentication()
    assert "does not authenticate a source" in str(e.value)
    assert "terrestrial" in str(e.value)


def test_relation_statuses_include_post_hoc():
    assert "POST_HOC" in A.RELATION_STATUS
    assert "PRE_REGISTERED" in A.RELATION_STATUS
