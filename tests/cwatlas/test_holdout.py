"""P49 — No-look-ahead sealed-holdout framework.

POWER: a deterministic split is disjoint and covers all ids; the true holdout
matches its seal and a tampered one does not; a decoder graded once on the
sealed labels returns a score. Negative: a decode before the seal is refused, a
second scoring is refused, a holdout leaked into training is refused, and
mismatched labels are refused. Deterministic.
"""

from __future__ import annotations

import pytest

from cwatlas import holdout as H
from cwatlas.claims import ClaimError


def _labeled(ids, num_classes=7):
    import hashlib
    return tuple(
        (i, int(hashlib.sha256(f"L\x1f{i}".encode()).hexdigest(), 16) % num_classes)
        for i in ids
    )


# --- POWER: split + seal machinery -------------------------------------------

def test_split_is_disjoint_and_covers_all():
    ids = H.synthetic_ids(200)
    split = H.make_split(ids, holdout_fraction=0.3)
    assert split.is_disjoint()
    assert split.covers(ids)
    assert 0.2 < split.actual_holdout_fraction() < 0.4


def test_true_holdout_matches_seal_tampered_does_not():
    ids = H.synthetic_ids(100)
    split = H.make_split(ids)
    labeled = _labeled(split.holdout)
    seal = H.seal_holdout(labeled)
    assert H.verify_seal(labeled, seal) is True
    tampered = ((labeled[0][0], (labeled[0][1] + 1) % 7),) + tuple(labeled[1:])
    assert H.verify_seal(tampered, seal) is False


def test_score_once_returns_result_on_sealed_holdout():
    ids = H.synthetic_ids(100)
    split = H.make_split(ids)
    labeled = _labeled(split.holdout)
    proto = H.SealedHoldout(labeled)
    proto.do_seal()
    # A perfect decoder that knows the labels recovers them all.
    lut = dict(labeled)
    res = proto.score_once(lambda i: lut[i])
    assert res.accuracy == 1.0
    assert res.labels_match_seal is True
    assert res.holdout_size == len(labeled)


# --- Negative: no look-ahead --------------------------------------------------

def test_refuse_decode_before_seal():
    ids = H.synthetic_ids(50)
    labeled = _labeled(H.make_split(ids).holdout)
    proto = H.SealedHoldout(labeled)  # not sealed yet
    with pytest.raises(ClaimError):
        proto.score_once(lambda i: 0)


def test_refuse_decode_before_seal_helper_raises():
    proto = H.SealedHoldout((("A", 1), ("B", 2)))
    with pytest.raises(H.SealError):
        H.refuse_decode_before_seal(proto)


def test_refuse_multiple_scoring():
    ids = H.synthetic_ids(60)
    labeled = _labeled(H.make_split(ids).holdout)
    proto = H.SealedHoldout(labeled)
    proto.do_seal()
    proto.score_once(lambda i: 0)  # first scoring allowed
    with pytest.raises(H.HoldoutError):
        proto.score_once(lambda i: 0)  # second scoring refused


def test_refuse_holdout_in_training():
    split = H.make_split(H.synthetic_ids(40))
    leaked_train = split.train + (split.holdout[0],)
    with pytest.raises(H.HoldoutError):
        H.refuse_holdout_in_training(leaked_train, split.holdout)


def test_clean_split_passes_leak_check():
    split = H.make_split(H.synthetic_ids(40))
    # disjoint split raises nothing
    H.refuse_holdout_in_training(split.train, split.holdout)


def test_score_refuses_mismatched_labels():
    ids = H.synthetic_ids(50)
    labeled = _labeled(H.make_split(ids).holdout)
    proto = H.SealedHoldout(labeled)
    proto.do_seal()
    # Mutate the holdout labels after sealing -> scoring must refuse.
    proto.holdout_labeled = ((labeled[0][0], (labeled[0][1] + 1) % 7),) \
        + tuple(labeled[1:])
    with pytest.raises(H.HoldoutError):
        proto.score_once(lambda i: 0)


# --- Negative: malformed splits ----------------------------------------------

def test_split_needs_two_items():
    with pytest.raises(H.HoldoutError):
        H.make_split(["only-one"])


def test_bad_fraction_refused():
    with pytest.raises(H.HoldoutError):
        H.make_split(H.synthetic_ids(20), holdout_fraction=1.5)


def test_empty_holdout_seal_refused():
    with pytest.raises(H.HoldoutError):
        H.seal_holdout([])


# --- Determinism --------------------------------------------------------------

def test_split_is_deterministic():
    ids = H.synthetic_ids(120)
    a = H.make_split(ids, holdout_fraction=0.25, salt="S")
    b = H.make_split(ids, holdout_fraction=0.25, salt="S")
    assert a == b


def test_seal_is_deterministic_and_salt_sensitive():
    labeled = _labeled(H.synthetic_ids(30))
    assert H.seal_holdout(labeled, "s1") == H.seal_holdout(labeled, "s1")
    assert H.seal_holdout(labeled, "s1") != H.seal_holdout(labeled, "s2")


def test_report_declares_boundary():
    r = H.holdout_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["measured_here"] == "nothing"
    assert r["true_holdout_matches_seal"] is True
    assert r["tampered_holdout_matches_seal"] is False
    assert r["tranche"] == "T07"
