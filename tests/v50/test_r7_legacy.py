"""P09 — publication gate and the open-legacy decision."""

from __future__ import annotations

import pytest

import r7
from r7 import legacy as L


RATIONALE = ("Decision unresolved pending patent-agent consultation; "
             "preserve both other paths.")


def _rc() -> L.DecisionRecord:
    return L.private_rc_decision("Andrew Green", "2026-07-18",
                                 RATIONALE)


# --- the gate ---------------------------------------------------------

def test_publication_refused_without_any_decision():
    with pytest.raises(L.PublicationRefused) as e:
        L.authorize_publication(None)
    assert "does not automatically make the repository public" in \
        str(e.value)


def test_standalone_refusal_cites_the_commit_collapse():
    with pytest.raises(L.PublicationRefused) as e:
        L.refuse_publication_without_decision()
    assert "COMMIT_DATE_IS_LEGAL_PRIORITY" in str(e.value)


def test_private_rc_authorizes_nothing():
    out = L.authorize_publication(_rc())
    assert out["authorized"] is False
    assert out["status"] == "PRIVATE_RC_NOTHING_PUBLISHED"


def test_private_rc_is_the_only_reversible_path():
    assert _rc().as_record()["reversible"] is True
    for p in L.IRREVERSIBLE_PATHS:
        assert p != "PRIVATE_RC"
    assert set(L.IRREVERSIBLE_PATHS) == {
        "FILE_THEN_PUBLISH", "DEFENSIVE_PUBLICATION"}


def test_incomplete_defensive_publication_is_refused():
    d = L.DecisionRecord(
        path="DEFENSIVE_PUBLICATION", signed_by="A",
        signed_at="2026-07-18", rationale=RATIONALE,
        evidence={"complete_enabling_disclosure": True})
    with pytest.raises(L.PublicationRefused) as e:
        L.authorize_publication(d)
    assert "missing required evidence" in str(e.value)
    assert "immutable_timestamp_and_hash" in str(e.value)


def test_complete_defensive_publication_is_authorized():
    ev = {r: True for r in
          L.PATH_REQUIREMENTS["DEFENSIVE_PUBLICATION"]}
    d = L.DecisionRecord(
        path="DEFENSIVE_PUBLICATION", signed_by="A",
        signed_at="2026-07-18", rationale=RATIONALE, evidence=ev)
    assert L.authorize_publication(d)["authorized"] is True


# --- record integrity -------------------------------------------------

def test_unknown_path_rejected():
    with pytest.raises(ValueError):
        L.DecisionRecord("PUBLISH_EVERYTHING", "A", "t", RATIONALE)


def test_unsigned_record_rejected():
    with pytest.raises(ValueError):
        L.DecisionRecord("PRIVATE_RC", "   ", "t", RATIONALE)


def test_unexplained_record_rejected():
    with pytest.raises(ValueError):
        L.DecisionRecord("PRIVATE_RC", "A", "t", "because")


def test_file_then_publish_requires_a_patent_agent():
    """The module cannot substitute for a registered agent."""
    with pytest.raises(ValueError) as e:
        L.DecisionRecord("FILE_THEN_PUBLISH", "A", "t", RATIONALE,
                         legal_advice_obtained=False)
    assert "registered patent agent" in str(e.value)


def test_digest_is_content_sensitive():
    a = _rc()
    b = L.private_rc_decision("Andrew Green", "2026-07-19", RATIONALE)
    assert a.digest() != b.digest()
    assert len(a.digest()) == 64


def test_digest_is_stable():
    assert _rc().digest() == _rc().digest()


def test_all_three_paths_have_requirements():
    for p in r7.PUBLICATION_PATHS:
        assert L.PATH_REQUIREMENTS[p]


# --- the commit distinction -------------------------------------------

def test_commit_is_not_a_filing():
    c = L.commit_is_not_a_filing()
    assert c["status"] == "NOT_LEGAL_ADVICE"
    assert any("patent filing" in x
               for x in c["git_commit_does_not_provide"])
    assert any("legal advice" in x
               for x in c["git_commit_does_not_provide"])


def test_private_repo_discloses_nothing():
    c = L.commit_is_not_a_filing()
    assert "discloses nothing" in c["why_it_matters"]
    assert "same instant" in c["why_it_matters"]


def test_commit_does_provide_a_date():
    c = L.commit_is_not_a_filing()
    assert any("date" in x for x in c["git_commit_provides"])


# --- comparison -------------------------------------------------------

def test_defensive_publication_forecloses_own_patenting():
    cmp = L.path_comparison()
    assert cmp["DEFENSIVE_PUBLICATION"]["preserves_patent_rights"] \
        is False
    assert "own ability to patent" in \
        cmp["DEFENSIVE_PUBLICATION"]["forecloses"]


def test_private_rc_forecloses_nothing():
    cmp = L.path_comparison()
    assert cmp["PRIVATE_RC"]["forecloses"] == "nothing"
    assert cmp["PRIVATE_RC"]["reversible"] is True


def test_comparison_states_the_options_are_asymmetric():
    cmp = L.path_comparison()
    assert "not symmetric" in cmp["ordering_note"]
    assert "reversible option" in cmp["ordering_note"]


def test_comparison_carries_a_disclaimer():
    assert "not legal advice" in L.path_comparison()["disclaimer"]
