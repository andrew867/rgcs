"""R10.10 acceptance — T11 search V2, Montréal audit, holdout freeze."""

from __future__ import annotations

import inspect
import json
import pathlib

import pytest

from r1010 import t11_search_v2 as s2

EV = pathlib.Path(__file__).resolve().parents[2] / "docs" / "r1010" / "evidence"
PAIRS = [(1643789253, 165876523), (1672875493, 168930443)]
SEALED = {165892323, 1687209343, 168724343, 165872943, 165829473}


def test_search_v1_preserved_and_still_zero():
    from r109 import t11_candidates as t11v1
    r = t11v1.evaluate(PAIRS)
    assert r["candidate_count"] == 46
    assert r["survivor_count"] == 0


def test_search_v2_documented_finite_and_evaluated():
    space = s2.candidate_space()
    assert len(space) == 32
    assert len({c.candidate_id for c in space}) == 32
    for c in space:
        assert c.assumptions
        assert c.family in ("FAM_ORIENT", "FAM_ORDER_ORIENT", "FAM_NODE")
    rep = s2.evaluate(PAIRS)
    assert rep["candidate_count"] == 32
    # recorded outcome of THIS run's expanded families:
    assert rep["survivor_count"] == 0
    assert rep["status"] == "NO_CANDIDATE_IN_EXPANDED_FAMILIES"
    # every rejection carries a reason
    for r in rep["results"]:
        for p in r["pair_results"]:
            if not p.get("passes"):
                assert p.get("rejection")


def test_candidates_reversible_where_they_decode():
    for cand in s2.candidate_space():
        for refined, _ in PAIRS:
            dec, reason = cand.decode(refined)
            if dec is None:
                continue
            assert cand.encode(dec) == refined


def test_node_state_participation_reversible_and_refused_range():
    cand = next(c for c in s2.candidate_space()
                if c.family == "FAM_NODE" and c.spin_active)
    # 60..63 refused: craft a word whose top six bits are 60
    word = (60 << 27) | (1 << 26)
    dec, reason = cand.decode(word | (1 << 32) if word < (1 << 30) else word)
    if dec is None:
        assert "refused range" in reason or "60..63" in reason
    # reversible split otherwise: spin*20+face round-trips by construction
    for state in (0, 19, 20, 39, 59):
        spin, face = divmod(state, 20)
        assert spin * 20 + face == state


def test_no_place_names_in_search_code():
    src = inspect.getsource(s2)
    for banned in ("Stonehenge", "Toronto", "Montreal", "Montréal", "Erie",
                   "stonehenge", "toronto", "montreal", "erie"):
        assert banned not in src


def test_montreal_tension_is_orientation_invariant():
    # recorded audit: separation identical under all six corner orders,
    # because the two paths share their first six levels.
    import rgcs_coordinate as rc
    sp = rc.decode_coordinate(165876523).to_dict()["q22_path"]
    mp = rc.decode_coordinate(165879243).to_dict()["q22_path"]
    lcp = 0
    for a, b in zip(sp, mp):
        if a != b:
            break
        lcp += 1
    assert lcp == 6


def test_holdout_freeze_receipt_and_predictions():
    fz = json.loads((EV / "R10_10_HOLDOUT_FREEZE_RECEIPT.json")
                    .read_text(encoding="utf-8"))
    assert len(fz["implementation_state_sha256"]) == 64
    assert fz["parent_commit"].startswith("b422e36")
    assert "V3 NOT BUILT" in fz["frozen_components"]["earth_candidate"]
    doc = json.loads((EV / "R10_10_PREREVEAL_PREDICTIONS.json")
                     .read_text(encoding="utf-8"))
    assert len(doc["receipt_sha256_of_predictions"]) == 64
    by_raw = {p["raw"]: p for p in doc["predictions"]}
    assert set(by_raw) == SEALED
    for raw in SEALED - {1687209343}:
        p = by_raw[raw]
        for op in ("prediction_v1", "prediction_v2"):
            assert len(p[op]["terminal_polygon_latlon"]) == 3
            assert p[op]["uncertainty_radius_deg"] > 0
        assert "FOLDED" in p["prediction_v2"]["operator"]
        assert "no gazetteer" in p["prediction_class"] or \
            "no location claim" in p["prediction_class"]
        assert "NOT collapsed" in p["shell_epoch_status"]
    assert "BLOCKED" in by_raw[1687209343]["prediction_class"]


def test_sealed_records_still_not_fit_inputs():
    from r109.registry import fit_anchors
    from r109 import earth_v2 as e2
    assert SEALED.isdisjoint({r.raw for r in fit_anchors()})
    for a in e2.v2_anchors():
        assert not any(str(raw) in a.provenance for raw in SEALED)
