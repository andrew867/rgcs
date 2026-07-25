"""P51 — Search-space accounting.

POWER: the total is the product over named dimensions; a raw match is read
against the size of the space (a hit in a huge space is expected by chance, a
rare hit in a small space is surprising). Negative: a candidate reported without
a search-space count is refused; invalid dimensions are refused. Deterministic.
"""

from __future__ import annotations

import pytest

from cwatlas import search_space as S
from cwatlas.claims import ClaimError


# --- POWER: counting ----------------------------------------------------------

def test_total_is_product_of_dimensions():
    space = S.count_search_space(codecs=4, frames=3, depths=8, catalogue=5,
                                 transforms=6)
    assert space.total() == 4 * 3 * 8 * 5 * 6


def test_match_in_huge_space_is_not_surprising():
    space = S.count_search_space(codecs=4, frames=3, depths=8, catalogue=5,
                                 transforms=6, anchors=100)
    interp = S.interpret_match(space, per_comparison_p=1e-4)
    # A large space inflates the family-wise chance of a hit.
    assert interp.surprising_after_accounting is False
    assert interp.expected_chance_hits > 1.0


def test_rare_match_in_small_space_is_surprising():
    space = S.count_search_space(codecs=2, frames=1)
    interp = S.interpret_match(space, per_comparison_p=1e-6)
    assert interp.surprising_after_accounting is True
    assert interp.adjusted_p < interp.alpha


# --- Negative: match without search space -------------------------------------

def test_refuse_match_without_search_space_dict():
    with pytest.raises(ClaimError):
        S.refuse_match_without_search_space({"name": "cand", "score": 0.9})


def test_refuse_match_without_search_space_object():
    class Bare:
        score = 0.9
    with pytest.raises(ClaimError):
        S.refuse_match_without_search_space(Bare())


def test_candidate_with_attached_space_passes():
    space = S.count_search_space(codecs=4, frames=3)
    cand = S.attach_search_space({"name": "cand"}, space)
    assert cand["search_space_total"] == 12
    # Now it does not trip the refusal.
    S.refuse_match_without_search_space(cand)


# --- Negative: malformed inputs ----------------------------------------------

def test_zero_dimension_refused():
    with pytest.raises(S.SearchSpaceError):
        S.count_search_space(codecs=0, frames=3)


def test_negative_dimension_refused():
    with pytest.raises(S.SearchSpaceError):
        S.count_search_space(codecs=-1)


def test_empty_space_refused():
    with pytest.raises(S.SearchSpaceError):
        S.SearchSpace({})


def test_bad_per_comparison_p_refused():
    space = S.count_search_space(codecs=4)
    with pytest.raises(S.SearchSpaceError):
        S.interpret_match(space, per_comparison_p=1.5)


# --- Determinism --------------------------------------------------------------

def test_total_is_deterministic():
    a = S.count_search_space(codecs=4, frames=3, depths=8).total()
    b = S.count_search_space(codecs=4, frames=3, depths=8).total()
    assert a == b == 96


def test_report_declares_boundary():
    r = S.search_space_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["measured_here"] == "nothing"
    assert r["search_space_total"] > 0
    assert r["tranche"] == "T07"
