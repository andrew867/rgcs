"""P37b — the decoder holdout / blinding protocol: a deterministic split,
a tamper-evident commitment, no-peeking enforcement, and a planted-data
power check that makes a holdout null meaningful."""

from __future__ import annotations

import pytest

from r13 import holdout as H


# --- the split is deterministic, disjoint, complete, and ~the ratio ------

def test_split_is_deterministic():
    ids = H.synthetic_ids(200)
    a = H.make_split(ids, 0.3, salt="S")
    b = H.make_split(ids, 0.3, salt="S")
    assert a == b
    assert a.train == b.train and a.holdout == b.holdout


def test_split_is_disjoint_and_covers_all_items():
    ids = H.synthetic_ids(200)
    split = H.make_split(ids, 0.3, salt="S")
    assert split.is_disjoint()
    assert set(split.train) & set(split.holdout) == set()
    assert split.covers(ids)
    assert set(split.train) | set(split.holdout) == set(ids)


def test_holdout_fraction_is_approximately_requested():
    ids = H.synthetic_ids(1000)
    for frac in (0.2, 0.3, 0.5):
        split = H.make_split(ids, frac, salt="RATIO")
        assert abs(split.actual_holdout_fraction() - frac) < 0.06


def test_a_degenerate_split_is_refused():
    with pytest.raises(H.HoldoutError):
        H.make_split(["only_one"], 0.3)
    with pytest.raises(H.HoldoutError):
        H.make_split(H.synthetic_ids(10), 1.5)


# --- blinding: the commitment is tamper-evident (POWER both ways) --------

def test_commitment_matches_the_true_holdout_and_rejects_a_tampered_one():
    planted = H.PlantedDataset(ids=H.synthetic_ids(200), salt="P")
    holdout_labeled = planted.holdout_labeled()
    commitment = H.commit_holdout(holdout_labeled)
    # the true holdout matches
    assert H.verify_commitment(holdout_labeled, commitment) is True
    # a holdout with one label altered does NOT match
    tampered = ((holdout_labeled[0][0],
                 (holdout_labeled[0][1] + 1) % planted.num_classes),
                ) + tuple(holdout_labeled[1:])
    assert H.verify_commitment(tampered, commitment) is False
    # a different holdout (dropping an item) does NOT match
    assert H.verify_commitment(holdout_labeled[1:], commitment) is False


def test_commitment_is_order_independent():
    planted = H.PlantedDataset(ids=H.synthetic_ids(50), salt="P")
    holdout_labeled = planted.holdout_labeled()
    reordered = tuple(reversed(holdout_labeled))
    assert H.commit_holdout(holdout_labeled) == H.commit_holdout(reordered)


# --- no peeking -----------------------------------------------------------

def test_refuse_holdout_in_training_raises_on_a_leak():
    train = ("A", "B", "C")
    holdout = ("C", "D")            # C leaked into training
    with pytest.raises(H.HoldoutError):
        H.refuse_holdout_in_training(train, holdout)
    # a clean disjoint pair does not raise
    H.refuse_holdout_in_training(("A", "B"), ("C", "D"))


def test_refuse_decode_before_commit_raises_until_committed():
    planted = H.PlantedDataset(ids=H.synthetic_ids(40), salt="P")
    protocol = H.HoldoutProtocol(planted.holdout_labeled())
    assert protocol.committed is False
    with pytest.raises(H.HoldoutError):
        H.refuse_decode_before_commit(protocol)
    # after committing, decoding is permitted
    protocol.commit()
    assert protocol.committed is True
    H.refuse_decode_before_commit(protocol)


# --- power on planted data, and scoring uses only committed labels -------

def test_power_check_detects_the_planted_signal():
    planted = H.PlantedDataset(ids=H.synthetic_ids(300), salt="POWER")
    good = H.power_check(H.planted_decoder(planted), planted)
    assert good["detected"] is True
    assert good["train_accuracy"] == pytest.approx(1.0)
    # a null decoder that ignores the id is NOT detected
    null = H.power_check(H.constant_decoder(0), planted)
    assert null["detected"] is False
    assert null["train_accuracy"] < H.POWER_DETECTION_THRESHOLD


def test_scoring_on_holdout_uses_only_the_committed_labels():
    planted = H.PlantedDataset(ids=H.synthetic_ids(300), salt="SCORE")
    holdout_labeled = planted.holdout_labeled()
    commitment = H.commit_holdout(holdout_labeled)
    decoder = H.planted_decoder(planted)
    # scoring against the committed labels works and is perfect here
    result = H.score_holdout(decoder, holdout_labeled, commitment)
    assert result["labels_match_commitment"] is True
    assert result["accuracy"] == pytest.approx(1.0)
    # scoring against relabelled holdout labels is refused
    tampered = ((holdout_labeled[0][0],
                 (holdout_labeled[0][1] + 1) % planted.num_classes),
                ) + tuple(holdout_labeled[1:])
    with pytest.raises(H.HoldoutError):
        H.score_holdout(decoder, tampered, commitment)


def test_refuse_overfit_as_generalization_raises():
    with pytest.raises(H.HoldoutError):
        H.refuse_overfit_as_generalization(1.0, holdout_score=0.14)


# --- the report ----------------------------------------------------------

def test_report_states_the_verdict_and_measures_nothing():
    rep = H.holdout_report()
    assert rep["verdict"] == "DECODER_HOLDOUT_PROTOCOL_BLINDED"
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["claim_class"] == "REPOSITORY_COMPUTATIONAL_RESULT"
    assert rep["split_is_disjoint"] is True
    assert rep["split_covers_all_items"] is True
    assert rep["true_holdout_matches_commitment"] is True
    assert rep["tampered_holdout_matches_commitment"] is False
    assert rep["power_planted_decoder_detected"] is True
    assert rep["power_null_decoder_detected"] is False
    assert "what_this_does_not_say" in rep


def test_holdout_module_imports_from_r13():
    from r13 import holdout          # noqa: F401
    assert holdout.VERDICT == "DECODER_HOLDOUT_PROTOCOL_BLINDED"
