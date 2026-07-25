"""P54 — prospective known-destination challenge protocol.

POWER: a sealed decode of an unseen target that scores within tolerance after
the truth is revealed promotes to CALIBRATED_MAPPING. Negative: a reveal at or
before the commit epoch (retrospective) is refused; an opening that does not
reproduce the commitment (prediction altered after the truth) is refused; a
missed challenge stays an OPERATOR_HYPOTHESIS. Deterministic.
"""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas import calibration as C
from cwatlas import challenge as CH
from cwatlas.claims import ClaimClass, ClaimError


def _linear_calibration(n=12, dim=3, seed=3):
    rng = np.random.default_rng(seed)
    A = rng.uniform(-0.4, 0.4, size=(2, dim))
    b = np.array([12.0, -40.0])
    anchors = []
    for i in range(n):
        v = rng.uniform(-1.0, 1.0, size=dim)
        lat, lon = (A @ v + b).tolist()
        anchors.append(C.Anchor(tuple(v), (float(lat), float(lon)),
                                label=f"sealed-{i}"))
    true = C.AffineTransform(tuple(tuple(r) for r in A), (12.0, -40.0), dim)
    sealed = C.SealedAnchorSet(anchors)
    cal = C.fit_calibration(sealed, holdout=2)
    return true, cal


# --- POWER: a passed prospective challenge promotes ---------------------------

def test_sealed_challenge_passes_and_promotes():
    true, cal = _linear_calibration()
    proto = CH.ChallengeProtocol()
    v_new = (0.12, -0.34, 0.56)
    seal, predicted = CH.seal_from_calibration(
        proto, cal, "target-A", v_new, salt="s1", commit_epoch=2026.10)
    revealed = true.apply(v_new)  # truth revealed only now
    out = proto.reveal_and_score("target-A", predicted, "s1", revealed,
                                 tolerance_m=100.0, reveal_epoch=2026.20)
    assert out.passed is True
    assert out.promoted is True
    assert out.commitment_verified is True
    assert out.claim_class == ClaimClass.CALIBRATED_MAPPING.value


def test_seal_hides_prediction_behind_commitment():
    proto = CH.ChallengeProtocol()
    seal = proto.seal("t", (10.0, 20.0), salt="salt", commit_epoch=2026.0)
    assert seal.commitment != "10.0,20.0"
    assert len(seal.commitment) == 64  # sha256 hex
    assert seal.unseen is True


# --- Negative: retrospective / temporal order --------------------------------

def test_reveal_before_commit_is_retrospective_refused():
    proto = CH.ChallengeProtocol()
    proto.seal("t", (10.0, 20.0), salt="salt", commit_epoch=2026.50)
    with pytest.raises(CH.SealError):
        proto.reveal_and_score("t", (10.0, 20.0), "salt", (10.0, 20.0),
                               tolerance_m=100.0, reveal_epoch=2026.50)


def test_refuse_retrospective_challenge_raises():
    with pytest.raises(ClaimError):
        CH.refuse_retrospective_challenge()


def test_seen_target_cannot_be_sealed():
    proto = CH.ChallengeProtocol()
    with pytest.raises(CH.ChallengeError):
        proto.seal("t", (10.0, 20.0), salt="s", commit_epoch=2026.0,
                   unseen=False)


def test_calibration_alone_is_not_calibrated_mapping():
    _true, cal = _linear_calibration()
    # A frozen retrospective fit is at most OPERATOR_HYPOTHESIS.
    assert cal.claim_class == ClaimClass.OPERATOR_HYPOTHESIS.value


# --- Negative: commitment tampering ------------------------------------------

def test_altered_prediction_breaks_commitment():
    true, cal = _linear_calibration()
    proto = CH.ChallengeProtocol()
    v_new = (0.1, 0.2, 0.3)
    seal, predicted = CH.seal_from_calibration(
        proto, cal, "t", v_new, salt="s", commit_epoch=2026.0)
    revealed = true.apply(v_new)
    # Operator tries to open with a different (post-hoc) prediction.
    with pytest.raises(CH.SealError):
        proto.reveal_and_score("t", (revealed[0], revealed[1]), "s", revealed,
                               tolerance_m=100.0, reveal_epoch=2026.1)


def test_wrong_salt_breaks_commitment():
    proto = CH.ChallengeProtocol()
    proto.seal("t", (10.0, 20.0), salt="right", commit_epoch=2026.0)
    with pytest.raises(CH.SealError):
        proto.reveal_and_score("t", (10.0, 20.0), "wrong", (10.0, 20.0),
                               tolerance_m=100.0, reveal_epoch=2026.1)


# --- Negative: missed challenge / malformed ----------------------------------

def test_missed_challenge_stays_hypothesis():
    proto = CH.ChallengeProtocol()
    proto.seal("t", (10.0, 20.0), salt="s", commit_epoch=2026.0)
    out = proto.reveal_and_score("t", (10.0, 20.0), "s", (60.0, 120.0),
                                 tolerance_m=10.0, reveal_epoch=2026.1)
    assert out.passed is False
    assert out.promoted is False
    assert out.claim_class == ClaimClass.OPERATOR_HYPOTHESIS.value


def test_double_seal_refused():
    proto = CH.ChallengeProtocol()
    proto.seal("t", (10.0, 20.0), salt="s", commit_epoch=2026.0)
    with pytest.raises(CH.ChallengeError):
        proto.seal("t", (11.0, 21.0), salt="s2", commit_epoch=2026.05)


def test_bad_tolerance_refused():
    proto = CH.ChallengeProtocol()
    proto.seal("t", (10.0, 20.0), salt="s", commit_epoch=2026.0)
    with pytest.raises(CH.ChallengeError):
        proto.reveal_and_score("t", (10.0, 20.0), "s", (10.0, 20.0),
                               tolerance_m=0.0, reveal_epoch=2026.1)


def test_empty_salt_refused():
    proto = CH.ChallengeProtocol()
    with pytest.raises(CH.ChallengeError):
        proto.seal("t", (10.0, 20.0), salt="", commit_epoch=2026.0)


# --- Determinism --------------------------------------------------------------

def test_commitment_is_deterministic():
    a = CH.ChallengeProtocol().seal("t", (1.0, 2.0), "s", 2026.0)
    b = CH.ChallengeProtocol().seal("t", (1.0, 2.0), "s", 2026.0)
    assert a.commitment == b.commitment


def test_report_declares_boundary():
    r = CH.challenge_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["only_path_to_calibrated_mapping"] is True
    assert r["retrospective_fit_promotes"] is False
