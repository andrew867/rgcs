"""P44 -- alias ranking, regions, and heatmaps: no invented precision."""

from __future__ import annotations

import math

import pytest

from cwatlas import claims
from cwatlas.alias_regions import (
    AliasRegionError,
    RANKING_RULE,
    alias_heatmap,
    alias_regions_report,
    collapse_region_to_point,
    description_length_bits,
    rank_aliases,
    region_for_uncertainty,
    resolve_alias_set,
)
from cwatlas.decode_legacy import search_legacy


def _alias_set():
    return search_legacy("123456789").alias_set


# --- POWER: ranking by predeclared rule; region area scales with sigma -------

def test_rank_orders_by_score_then_description_length():
    ranked = rank_aliases(_alias_set())
    assert len(ranked) >= 2
    # Ranks are 1..N and scores are non-increasing.
    assert [r.rank for r in ranked] == list(range(1, len(ranked) + 1))
    scores = [r.score for r in ranked]
    assert scores == sorted(scores, reverse=True)
    # Higher-score TRIPLET9 outranks the lossy SHELL9 legacy candidate.
    assert ranked[0].codec_id == "CW-TRIPLET9-1"


def test_description_length_bits_matches_log2():
    assert description_length_bits(1_000_000_000) == pytest.approx(
        math.log2(1_000_000_000))
    assert description_length_bits(0) == math.inf
    assert description_length_bits(-1) == math.inf


def test_region_area_scales_with_uncertainty():
    small = region_for_uncertainty(
        (45.0, -75.0), input_sigma_m=10.0, quantization_m=1.0, cell_size_m=10.0)
    large = region_for_uncertainty(
        (45.0, -75.0), input_sigma_m=100.0, quantization_m=1.0, cell_size_m=10.0)
    assert large.area_m2 > small.area_m2
    # Search-space accounting grows with the larger region.
    assert large.search_space_count >= small.search_space_count


def test_heatmap_weights_normalize_and_account_search_space():
    ranked = rank_aliases(_alias_set())
    hm = alias_heatmap(
        ranked, (45.0, -75.0),
        per_alias_sigma_m=100.0, quantization_m=1.0, cell_size_m=10.0)
    assert not hm.is_empty()
    assert sum(c.weight for c in hm.cells) == pytest.approx(1.0)
    assert hm.total_area_m2 > 0.0
    assert hm.search_space_total > 0


def test_resolve_alias_set_returns_ranked_and_heatmap():
    ranked, hm = resolve_alias_set(
        _alias_set(), (0.0, 0.0),
        per_alias_sigma_m=50.0, quantization_m=1.0, cell_size_m=5.0)
    assert len(ranked) >= 2
    assert hm is not None
    assert len(hm.cells) == len(ranked)


# --- Negative: invented precision is refused --------------------------------

def test_collapse_region_to_point_refused_without_justification():
    region = region_for_uncertainty(
        (45.0, -75.0), input_sigma_m=100.0, quantization_m=1.0, cell_size_m=10.0)
    with pytest.raises(claims.ClaimError):
        collapse_region_to_point(region, justification="")


def test_collapse_region_to_point_allowed_with_justification():
    region = region_for_uncertainty(
        (45.0, -75.0), input_sigma_m=100.0, quantization_m=1.0, cell_size_m=10.0)
    point = collapse_region_to_point(
        region, justification="operator-confirmed survey monument")
    assert point["latitude_deg"] == 45.0
    assert point["justification"]


def test_empty_alias_set_yields_no_heatmap():
    empty = search_legacy("hello").alias_set  # no candidates
    ranked, hm = resolve_alias_set(
        empty, (0.0, 0.0),
        per_alias_sigma_m=50.0, quantization_m=1.0, cell_size_m=5.0)
    assert ranked == ()
    assert hm is None


def test_bad_per_alias_sigma_refused():
    ranked = rank_aliases(_alias_set())
    with pytest.raises(AliasRegionError):
        alias_heatmap(ranked, (0.0, 0.0), per_alias_sigma_m=0.0,
                      quantization_m=1.0, cell_size_m=5.0)


def test_rank_aliases_rejects_non_alias_set():
    with pytest.raises(AliasRegionError):
        rank_aliases(object())  # type: ignore[arg-type]


# --- Determinism -------------------------------------------------------------

def test_ranking_is_deterministic():
    a = rank_aliases(_alias_set())
    b = rank_aliases(_alias_set())
    assert [r.to_dict() for r in a] == [r.to_dict() for r in b]


def test_report_declares_rule_and_no_geographic_semantics():
    rep = alias_regions_report()
    assert rep["ranking_rule"] == RANKING_RULE
    assert rep["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert rep["phase_id"] == "P44"
