"""P16 — honest, time-disciplined external-corpus comparison."""

from __future__ import annotations

from datetime import datetime, timedelta

import pytest

from r10 import extcompare as X


SESSION = datetime(2026, 1, 1, 12, 0, 0)
DAY = timedelta(days=1)


def _item(id_, pub, features, access=None):
    return X.CorpusItem(id_, pub, access, frozenset(features))


# --- temporal classification -------------------------------------------

def test_classify_before_session_is_prior_exposure_possible():
    before = _item("b", SESSION - timedelta(days=30), {"a", "b"})
    assert X.classify_temporal(before, SESSION, window=DAY) is \
        X.TemporalClass.PRIOR_EXPOSURE_POSSIBLE


def test_classify_around_session_is_contemporaneous():
    around = _item("c", SESSION + timedelta(hours=3), {"a", "b"})
    assert X.classify_temporal(around, SESSION, window=DAY) is \
        X.TemporalClass.CONTEMPORANEOUS


def test_classify_after_session_is_post_session():
    after = _item("d", SESSION + timedelta(days=30), {"a", "b"})
    assert X.classify_temporal(after, SESSION, window=DAY) is \
        X.TemporalClass.POST_SESSION


def test_plausible_exposure_needs_access_before_session():
    seen = _item("s", SESSION - timedelta(days=10), {"a"},
                 access=SESSION - timedelta(days=5))
    unseen = _item("u", SESSION - timedelta(days=10), {"a"},
                   access=SESSION + timedelta(days=5))
    assert X.plausible_exposure(seen, SESSION)
    assert not X.plausible_exposure(unseen, SESSION)
    # a post-session item is never prior exposure, whatever the access
    later = _item("l", SESSION + timedelta(days=1), {"a"})
    assert not X.plausible_exposure(later, SESSION)


# --- the refusal -------------------------------------------------------

def test_post_session_item_cannot_be_prospective():
    after = _item("d", SESSION + timedelta(days=30), {"a", "b"})
    with pytest.raises(X.CompareError):
        X.refuse_prospective_from_post_session(after, SESSION)


def test_prior_item_does_not_trigger_the_refusal():
    before = _item("b", SESSION - timedelta(days=30), {"a", "b"})
    # returns None, does not raise
    assert X.refuse_prospective_from_post_session(before, SESSION) is None


def test_build_comparison_refuses_post_session_target():
    session_feats = {"quantum", "coherence", "lattice"}
    after = _item("post", SESSION + timedelta(days=5), session_feats)
    nulls = [_item(f"n{i}", SESSION, {f"x{i}", f"y{i}"}) for i in range(20)]
    with pytest.raises(X.CompareError):
        X.build_comparison("cmp", SESSION, session_feats, after, nulls,
                           "public_corpus", session_time=SESSION)


# --- overlap metric ----------------------------------------------------

def test_jaccard_bounds_and_exact_overlap():
    assert X.jaccard({"a", "b"}, {"a", "b"}) == 1.0
    assert X.jaccard({"a"}, {"b"}) == 0.0
    assert X.jaccard(set(), set()) == 0.0
    assert X.exact_overlap({"a", "b"}, {"b", "a"})
    assert not X.exact_overlap({"a", "b"}, {"a"})


# --- null vs power -----------------------------------------------------

def _distinctive_session():
    return {f"tok{i}" for i in range(30)}


def _unrelated_nulls():
    return [X.CorpusItem(f"n{j}", SESSION, SESSION,
                         frozenset(f"u{j}_{i}" for i in range(30)))
            for j in range(40)]


def test_null_unrelated_overlap_is_not_significant():
    session = _distinctive_session()
    nulls = _unrelated_nulls()
    # an unrelated target: its overlap looks like the null itself
    target = X.CorpusItem("t", SESSION, SESSION,
                          frozenset(f"other_{i}" for i in range(30)))
    observed = X.jaccard(session, target.text_features)
    res = X.semantic_null(session, nulls, observed)
    assert observed == 0.0
    assert not res["flagged"]
    assert res["p_corrected"] > X.ALPHA


def test_power_planted_near_duplicate_is_flagged():
    session = _distinctive_session()
    nulls = _unrelated_nulls()
    res = X.planted_power_check(session, nulls, noise_fraction=0.1)
    assert res["planted_overlap"] > 0.8
    assert res["flagged"]
    assert res["p_corrected"] < X.ALPHA


# --- multiplicity ------------------------------------------------------

def test_multiplicity_correction_reduces_significance():
    p = 0.01
    assert X.multiplicity_correct(p, 1) == pytest.approx(0.01)
    assert X.multiplicity_correct(p, 10) == pytest.approx(0.10)
    assert X.multiplicity_correct(p, 10) > X.multiplicity_correct(p, 1)
    # correction is capped at 1.0
    assert X.multiplicity_correct(0.5, 1000) == 1.0
    with pytest.raises(X.CompareError):
        X.multiplicity_correct(0.01, 0)


def test_more_comparisons_can_erase_a_flag():
    session = _distinctive_session()
    nulls = _unrelated_nulls()
    res = X.planted_power_check(session, nulls, noise_fraction=0.1)
    observed = res["planted_overlap"]
    tight = X.semantic_null(session, nulls, observed, n_comparisons=1)
    loose = X.semantic_null(session, nulls, observed, n_comparisons=10_000)
    assert tight["flagged"]
    assert not loose["flagged"]
    assert loose["p_corrected"] >= tight["p_corrected"]


# --- independence ------------------------------------------------------

def test_independence_penalises_common_vocabulary():
    common = {"the", "energy", "signal"}
    session = {"the", "energy", "signal", "rare_a", "rare_b"}
    # overlap entirely of common words -> low independence
    all_common = {"the", "energy", "signal"}
    assert X.independence_score(session, all_common, common) == \
        pytest.approx(0.0)
    # overlap of distinctive tokens -> high independence
    distinctive = {"rare_a", "rare_b"}
    assert X.independence_score(session, distinctive, common) == \
        pytest.approx(1.0)
    # no overlap at all -> nothing to confound
    assert X.independence_score(session, {"zzz"}, common) == 1.0


# --- the record and the report -----------------------------------------

def test_build_comparison_records_a_prior_exposure():
    session = _distinctive_session()
    target = X.CorpusItem("prior", SESSION - timedelta(days=10),
                          SESSION - timedelta(days=8), frozenset(session))
    nulls = _unrelated_nulls()
    rec = X.build_comparison("cmp1", SESSION, session, target, nulls,
                             "public_corpus", session_time=SESSION)
    assert rec.prior_exposure
    assert rec.exact_overlap
    assert "REFUSED" in rec.result
    assert rec.session_hash == X.session_hash(session)


def test_report_measures_nothing():
    r = X.extcompare_report()
    assert r["measured_here"] == "nothing"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == "COMPARISON_IS_NOT_PROSPECTIVE_EVIDENCE"
    assert "prospective" in r["what_this_does_not_say"].lower()
