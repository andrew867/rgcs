"""Miami/Bermuda calibration -- exact candidate, null control, no fitting."""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from rgcs_terra_release import miami_bermuda_calibration as M


def test_the_mandated_candidate_arithmetic():
    candidate = F(236805, 142)
    known = 1667.5412705026051
    abs_error_km = abs(float(candidate) - known)
    assert M.CANDIDATE == candidate
    assert abs_error_km == pytest.approx(0.0995745678, abs=1e-9)
    assert M.candidate_error()["abs_error_km"] == pytest.approx(
        abs_error_km)


def test_the_error_is_reported_not_zeroed():
    """A ~100 m miss stays a ~100 m miss; nothing rounds it away."""
    r = M.candidate_error()
    assert r["abs_error_km"] > 0.09
    assert r["claim"] == "MODEL_OUTPUT"


def test_frame_disagreement_is_visible():
    """The projector's sphere and the geodesic reference differ by >5 km,
    and the candidate is only a near-hit against the GEODESIC frame."""
    fr = M.frame_comparison()
    assert fr["frames_agree"] is False
    assert fr["err_vs_geodesic_km"] < 0.1
    assert fr["err_vs_sphere_km"] > 5.0


def test_null_control_finds_the_candidate_and_counts_rivals():
    n = M.null_control()
    assert n["hit_count"] >= 1
    frs = [h["fraction"] for h in n["hits"]]
    assert "236805/142" in frs
    # every reported hit honours the declared tolerance
    assert all(h["abs_err_km"] <= n["tolerance_km"] for h in n["hits"])


def test_legal_branches_enforce_the_30_bit_lane():
    b1 = {x["branch"]: x for x in M.legal_branches("1680769543")}
    assert b1["payload_only"]["legal"] is True
    assert b1["whole_wire"]["legal"] is False        # 1680769543 >= 2^30
    b2 = {x["branch"]: x for x in M.legal_branches("168593073")}
    assert b2["whole_wire"]["legal"] is True         # fits


def test_malformed_wires_are_refused_not_guessed():
    out = M.legal_branches("99123")
    assert out[0]["legal"] is False


def test_vectors_map_through_the_existing_projector_unfitted():
    r = M.map_vector("1680769543")
    assert r["target_fitted"] is False
    assert r["projector"].startswith("r1053")
    legal = [b for b in r["branches"] if b.get("legal")]
    assert legal and all("lat" in b and "km_to_miami" in b for b in legal)


def test_no_branch_lands_near_the_labelled_vertex():
    """The honest negative: no legal parse of either candidate lands
    within 500 km of Miami or Bermuda, so the label stays a candidate."""
    for wire in M.VECTOR_CANDIDATES:
        for b in M.map_vector(wire)["branches"]:
            if b.get("legal"):
                assert min(b["km_to_miami"], b["km_to_bermuda"]) > 500.0


def test_label_is_candidate_not_confirmed():
    assert M.VECTOR_CANDIDATES["1680769543"] == \
        "BERMUDA_FLORIDA_VERTEX_VECTOR_CANDIDATE"
