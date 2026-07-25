"""P50 — Planted-signal recovery and power tests.

POWER: the decoder that knows the planting rule recovers the planted mapping on
TRAIN (signal detected). Null: a noise decoder stays at chance (no recovery), so
a null result is meaningful. Negative: a method with no power on planted data is
refused as vacuous. Deterministic.
"""

from __future__ import annotations

import pytest

from cwatlas import power as P
from cwatlas.claims import ClaimError
from cwatlas.holdout import synthetic_ids


def _planted(n=240, seed_salt="TEST_PLANT"):
    return P.PlantedDataset(ids=synthetic_ids(n), salt=seed_salt)


# --- POWER: planted signal recovered -----------------------------------------

def test_planted_decoder_recovers_signal():
    planted = _planted()
    res = P.power_test(P.planted_decoder(planted), planted)
    assert res.train_recovery == 1.0
    assert res.detected is True
    assert res.train_recovery > res.chance_rate


def test_evaluate_method_null_is_meaningful_with_power():
    planted = _planted()
    report = P.evaluate_method(P.planted_decoder(planted), planted)
    assert report.method_has_power is True
    assert report.null_is_meaningful is True


# --- Null control: pure noise does not recover -------------------------------

def test_noise_decoder_stays_at_chance():
    planted = _planted()
    ctrl = P.null_control(P.noise_decoder(num_classes=planted.num_classes), planted)
    assert ctrl.is_null is True
    assert abs(ctrl.train_recovery - ctrl.chance_rate) <= ctrl.margin


def test_noise_decoder_not_detected_as_power():
    planted = _planted()
    res = P.power_test(P.noise_decoder(num_classes=planted.num_classes), planted)
    assert res.detected is False


def test_constant_decoder_has_no_power():
    planted = _planted()
    res = P.power_test(P.constant_decoder(0), planted)
    assert res.detected is False


# --- Negative: vacuous method refused ----------------------------------------

def test_refuse_vacuous_method():
    planted = _planted()
    res = P.power_test(P.noise_decoder(num_classes=planted.num_classes), planted)
    with pytest.raises(ClaimError):
        P.refuse_vacuous_method(res)


def test_refuse_vacuous_method_allows_powered_method():
    planted = _planted()
    res = P.power_test(P.planted_decoder(planted), planted)
    # A method with power does not trip the refusal.
    P.refuse_vacuous_method(res)


def test_bad_num_classes_refused():
    with pytest.raises(P.PowerError):
        P.planted_label("X", num_classes=1)


def test_power_test_requires_planted_dataset():
    with pytest.raises(P.PowerError):
        P.power_test(lambda i: 0, object())


# --- Determinism --------------------------------------------------------------

def test_planted_label_is_deterministic():
    assert P.planted_label("ITEM_0007", "S") == P.planted_label("ITEM_0007", "S")
    # Determinism (same input -> same output) is the guarantee, over many ids.
    ids = synthetic_ids(50)
    once = [P.planted_label(i, "S") for i in ids]
    twice = [P.planted_label(i, "S") for i in ids]
    assert once == twice


def test_power_test_is_deterministic():
    planted = _planted()
    a = P.power_test(P.planted_decoder(planted), planted)
    b = P.power_test(P.planted_decoder(planted), planted)
    assert a == b


def test_report_declares_boundary():
    r = P.power_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["measured_here"] == "nothing"
    assert r["power_detected"] is True
    assert r["null_is_null"] is True
    assert r["tranche"] == "T07"
