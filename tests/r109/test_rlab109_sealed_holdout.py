"""R10.9 sealed-holdout intake (2026-07-27) — firewalls and receipts."""

from __future__ import annotations

import json
import pathlib

import pytest

from r109 import sealed_holdout as sh
from r109.registry import fit_anchors

EV = pathlib.Path(__file__).resolve().parents[2] / "docs" / "r109" / "evidence"
SEALED = {165892323, 1687209343, 168724343, 165872943, 165829473}


def test_records_sealed_and_hashed():
    assert {r.raw for r in sh.RECORDS} == SEALED
    reg = sh.registry_dict()
    assert reg["intake_sha256"] == sh.intake_sha256()
    for rec in reg["records"]:
        assert len(rec["raw_sha256"]) == 64
        assert rec["evidence_class"] == "SOURCE_REPORTED"
    # external receipt file honestly recorded as not found
    assert "NOT FOUND" in reg["external_receipt_status"]


def test_sealed_records_never_training_inputs():
    for raw in SEALED:
        with pytest.raises(sh.SealedHoldoutError):
            sh.assert_not_training_input(raw, "T11 interleave selection")
        with pytest.raises(sh.SealedHoldoutError):
            sh.assert_not_training_input(raw, "Earth V2 fitting")
    # not in the vector-registry fit set
    assert SEALED.isdisjoint({r.raw for r in fit_anchors()})
    # not among Earth V2 anchors
    from r109 import earth_v2 as e2
    for a in e2.v2_anchors():
        assert not any(str(raw) in a.provenance for raw in SEALED)
    # not among the T11 training pairs
    import inspect
    from tests.r109 import test_rlab109_t11_headers_shells as tmod
    flat = {v for pair in tmod.PAIRS for v in pair}
    assert SEALED.isdisjoint(flat)


def test_pair_relationship_not_assumed():
    reg = sh.registry_dict()
    pair = [r for r in reg["records"] if r["batch"] == "pair"]
    assert len(pair) == 2
    for r in pair:
        assert "UNKNOWN" in r["source_note"]


def test_structural_observation_preserved():
    obs = sh.STRUCTURAL_OBSERVATION
    assert obs["all_decimal_terminals"] == 3
    assert obs["uniform"] is False
    assert set(obs["decodable_s3_values"].values()) == {3, 7, 1}


def test_prereveal_predictions_receipt():
    doc = json.loads((EV / "R10_9_PREREVEAL_PREDICTIONS.json")
                     .read_text(encoding="utf-8"))
    assert doc["intake_id"] == sh.INTAKE_ID
    assert "no_retune_pledge" in doc
    by_raw = {p["raw"]: p for p in doc["predictions"]}
    assert set(by_raw) == SEALED
    # every decodable vector has BOTH frozen-operator predictions
    for raw in SEALED - {1687209343}:
        p = by_raw[raw]
        assert p["family"] == "T10"
        assert len(p["prediction_v1_latlon"]) == 2
        assert len(p["prediction_v2_latlon"]) == 2
        assert "no label" in p["claim_status"] or "no location claim" in p["claim_status"]
    # the T11 value has NO prediction (interleave unresolved)
    assert by_raw[1687209343]["family"] == "T11"
    assert "NOT_DECODABLE" in by_raw[1687209343]["status"]
    assert len(doc["receipt_sha256_of_predictions"]) == 64
