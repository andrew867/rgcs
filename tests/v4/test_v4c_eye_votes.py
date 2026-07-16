"""Agent M9: eye vote layer tests (gates J1-J3)."""
from __future__ import annotations

import pytest

from rscs2_core import eye_votes as ev


def _vote(vid, app="APPLICABLE", **kw):
    qty, cap, units = ev.VOTE_CATALOGUE[vid]
    args = dict(vote_id=vid, applicability=app, quantity=qty,
                units=units, data_source="test", value=None,
                uncertainty=None,
                control_result="control ok" if app == "APPLICABLE"
                else None,
                classification="CORE_VALIDATED"
                if app == "APPLICABLE" else "NOT_APPLICABLE",
                reason=None if app == "APPLICABLE" else "gated")
    args.update(kw)
    return ev.EyeVote(**args)


def test_quartz_applicability_map():
    """Gate J1: every catalogue vote is APPLICABLE, NOT_APPLICABLE, or
    INTERFACE_ONLY with reasons; magnetic votes are NOT_APPLICABLE;
    optical votes without a solved field are INTERFACE_ONLY."""
    app = ev.quartz_vote_applicability()
    assert set(app) == set(ev.VOTE_CATALOGUE)
    assert app["torsional_mode_energy"]["applicability"] == \
        "APPLICABLE"
    assert app["mechanical_circulation"]["applicability"] == \
        "APPLICABLE"
    for vid in ("chirality_density", "chiral_phonon_am",
                "magnetoelectric_quadrature"):
        assert app[vid]["applicability"] == "NOT_APPLICABLE", vid
        assert app[vid]["reason"]
    for vid in ("optical_sam", "optical_oam", "topological_charge"):
        assert app[vid]["applicability"] == "INTERFACE_ONLY", vid
    # with a solved optical field, optical votes become APPLICABLE
    app2 = ev.quartz_vote_applicability(solved_optical_field=True)
    assert app2["optical_sam"]["applicability"] == "APPLICABLE"


def test_not_applicable_votes_never_count():
    """Gate J1/J3: exclusion from the count is structural."""
    votes = [_vote("torsional_mode_energy"),
             _vote("mechanical_circulation"),
             _vote("ordinary_nodal_structure"),
             _vote("chirality_density", app="NOT_APPLICABLE"),
             _vote("magnetoelectric_quadrature",
                   app="NOT_APPLICABLE"),
             _vote("optical_sam", app="INTERFACE_ONLY")]
    out = ev.consensus_from_votes("CONVENTIONAL_NODE_EXPLAINS_RESULT",
                                  votes)
    assert out["n_applicable_votes"] == 3
    assert out["n_excluded_votes"] == 3
    assert out["verdict"] == "CONVENTIONAL_NODE_EXPLAINS_RESULT"
    assert set(out["excluded_reasons"]) == {
        "chirality_density", "magnetoelectric_quadrature",
        "optical_sam"}


def test_insufficient_resolution_downgrade_and_no_upgrade():
    """Gate J2: too few applicable votes -> INSUFFICIENT_RESOLUTION;
    the vote layer can never upgrade toward STABLE."""
    few = [_vote("torsional_mode_energy"),
           _vote("chirality_density", app="NOT_APPLICABLE")]
    out = ev.consensus_from_votes("NO_STABLE_CANDIDATE", few)
    assert out["verdict"] == "INSUFFICIENT_RESOLUTION"
    # 20 NOT_APPLICABLE votes cannot manufacture stability
    many_na = [_vote("chirality_density", app="NOT_APPLICABLE")] * 5
    out2 = ev.consensus_from_votes("NO_STABLE_CANDIDATE",
                                   many_na + few)
    assert out2["verdict"] == "INSUFFICIENT_RESOLUTION"
    assert out2["verdict"] != "STABLE_CANDIDATE_REGION"
    # release policy is explicit (J2)
    assert "PASSES the release" in out["release_policy"]


def test_vote_constructor_enforcement():
    with pytest.raises(ValueError, match="unregistered vote"):
        _vote.__wrapped__ if False else ev.EyeVote(
            "made_up_vote", "APPLICABLE", "q", "u", "d", None, None,
            "c", "CORE_VALIDATED", None)
    with pytest.raises(ValueError, match="control"):
        _vote("torsional_mode_energy", control_result=None)
    with pytest.raises(ValueError, match="null values"):
        _vote("chirality_density", app="NOT_APPLICABLE", value=1.0)


def test_deterministic_verdict():
    votes = [_vote("torsional_mode_energy"),
             _vote("mechanical_circulation"),
             _vote("ordinary_nodal_structure"),
             _vote("mesh_fixture_sensitivity")]
    a = ev.consensus_from_votes("NO_STABLE_CANDIDATE", votes)
    b = ev.consensus_from_votes("NO_STABLE_CANDIDATE", votes)
    assert a == b
    assert a["deterministic"]
