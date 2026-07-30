"""R10.9 acceptance — Earth V1 preservation, V2 build, holdout firewall.

The heavy fit/verification battery ran once and is frozen in
``docs/r109/evidence/R10_9_EARTH_V2_OPERATOR.json``; these tests verify
the preserved V1 chain exactly (fast) and the recorded V2 evidence
structurally, plus a live small-scale V1 reproduction.
"""

from __future__ import annotations

import json
import pathlib

import pytest

np = pytest.importorskip("numpy")

from r109 import earth_v2 as e2

EV = pathlib.Path(__file__).resolve().parents[2] / "docs" / "r109" / "evidence"


def test_v1_archive_preserved():
    assert (e2.V1_DIR / "EARTH_ALIGNMENT_CANDIDATE.json").is_file()
    assert (e2.V1_DIR / "operator" / "WARP_STEPS.json.gz").is_file()
    cand = json.loads((e2.V1_DIR / "EARTH_ALIGNMENT_CANDIDATE.json")
                      .read_text(encoding="utf-8"))
    assert cand["status"] == "CALIBRATED_CANDIDATE_NOT_VALIDATED"
    assert cand["warp"]["total_steps"] == 627


def test_v1_chain_reproduces_stonehenge_exactly():
    steps = e2.load_v1_steps()
    p = e2.prewarp_unit(165876523, 12)
    la, lo = e2.latlon(e2.apply_steps([p], steps)[0])
    assert abs(la - 51.17881944444445) < 1e-9
    assert abs(lo - -1.8262805555555555) < 1e-9


def test_v1_chain_reproduces_orange_triplet_exactly():
    steps = e2.load_v1_steps()
    archived = {
        165892743: (49.87628265441528, -2.6955552559494955),
        165892763: (49.861909310527366, -2.743510303776852),
        165892783: (49.81001006143685, -2.9159021881089444),
    }
    for raw, exp in archived.items():
        la, lo = e2.latlon(e2.apply_steps([e2.prewarp_unit(raw, 12)], steps)[0])
        assert abs(la - exp[0]) < 1e-9 and abs(lo - exp[1]) < 1e-9


def test_v2_anchor_set_uses_direct_montreal_not_superseded():
    anchors = {a.name: a for a in e2.v2_anchors()}
    assert "MONTREAL_DIRECT" in anchors
    assert "165879243" in anchors["MONTREAL_DIRECT"].provenance
    # the superseded transcription is not an anchor
    assert not any("168729543" in a.provenance for a in anchors.values())
    # Newfoundland and the corrupted collision never appear
    assert not any("1658274383" in a.provenance or "1658792343" in a.provenance
                   for a in anchors.values())


def test_v2_operator_evidence_recorded_honestly():
    rec = json.loads((EV / "R10_9_EARTH_V2_OPERATOR.json")
                     .read_text(encoding="utf-8"))
    assert rec["profile_id"] == "EARTH_ALIGNMENT_V2_MONTREAL_DIRECT"
    assert rec["claim_status"] == "CALIBRATED_CANDIDATE_NOT_VALIDATED"
    assert rec["converged"] is True
    # anchors mapped exactly
    for a in rec["anchors"]:
        assert a["final_residual_deg"] < 1e-5
    # the no-fold failure is REPORTED, not hidden
    assert rec["mesh_verification_L6"]["orientation_reversals"] > 0
    assert rec["v1_mesh_verification_L6"]["orientation_reversals"] == 0
    # holdout preserved: decoded under both, never fitted
    assert rec["holdout_167854923_v1"][0] == pytest.approx(41.7300, abs=1e-3)
    assert rec["holdout_167854923_v2"][0] == pytest.approx(41.7114, abs=1e-3)


def test_blind_holdout_never_in_v2_anchors():
    assert not any("167854923" in a.provenance for a in e2.v2_anchors())


def test_face12_convention_receipt():
    # direct Montréal pre-warp lies near Stonehenge pre-warp on face 12
    # (the recorded tension driving the V2 no-fold failure)
    sp = e2.prewarp_unit(165876523, 12)
    mp = e2.prewarp_unit(165879243, 12)
    ang = np.degrees(np.arccos(np.clip(np.dot(sp, mp), -1, 1)))
    assert 0.05 < ang < 1.0
