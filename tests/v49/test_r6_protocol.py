"""P13 - open protocol, conformance suite and governance."""

from __future__ import annotations

import pytest

from r6 import FORBIDDEN_COLLAPSES, PROTOCOL_MATURITY
from r6 import protocol as P


def _evidence(**kw) -> dict:
    """Evidence sufficient for every rung, before the caller breaks one."""
    base = dict(
        author=P.AUTHOR_ID,
        public_specification=True,
        versioned_change_process=True,
        issue_and_correction_log=True,
        test_vectors=True,
        conformance_suite=True,
        deprecation_policy=True,
        reference_implementation_public=True,
        conformance_suite_passes=True,
        second_implementor="Second Lab",
        second_implementation_passes_conformance=True,
        cross_implementation_conformance={
            "implementations": ["reference", "Second Lab"],
            "vectors_agreed": len(P.TEST_VECTORS),
            "vectors_total": len(P.TEST_VECTORS),
        },
        security_review_by="An Auditor",
        security_review_findings_published=True,
        governance_body="An Independent Body",
        no_single_vendor_lock=True,
        patent_and_licensing_review=True,
        independent_adopters=("A", "B", "C"),
        recognized_standards_body_publication=True,
    )
    base.update(kw)
    return base


def _climb(evidence: dict) -> str:
    level = PROTOCOL_MATURITY[0]
    while True:
        rep = P.advance(level, evidence)
        if not rep["advanced"]:
            return level
        level = rep["to"]


# --- version -----------------------------------------------------------

def test_version_rejects_a_maturity_off_the_ladder():
    with pytest.raises(ValueError):
        P.ProtocolVersion(0, 1, 0, "WORLD_STANDARD")


def test_version_for_this_repository_uses_current_maturity():
    v = P.ProtocolVersion.for_this_repository()
    assert v.maturity == P.current_maturity()
    assert v.maturity in str(v)


def test_version_rung_matches_the_ladder_index():
    v = P.ProtocolVersion(0, 1, 0, "DRAFT_PROTOCOL")
    assert v.rung == PROTOCOL_MATURITY.index("DRAFT_PROTOCOL")


# --- current maturity --------------------------------------------------

def test_current_maturity_is_on_the_ladder():
    assert P.current_maturity() in PROTOCOL_MATURITY


def test_current_maturity_cannot_exceed_draft_protocol():
    """One implementation, one author: the rungs above are unreachable."""
    assert PROTOCOL_MATURITY.index(P.current_maturity()) <= \
        PROTOCOL_MATURITY.index("DRAFT_PROTOCOL")
    assert P.current_maturity() in ("EXPERIMENTAL_SCHEMA",
                                   "DRAFT_PROTOCOL")


def test_the_declared_ceiling_is_draft_protocol():
    assert P.MAX_SUPPORTABLE_MATURITY == "DRAFT_PROTOCOL"


def test_repository_evidence_has_no_second_party():
    ev = P.repository_evidence()
    assert ev["second_implementor"] is None
    assert ev["governance_body"] is None
    assert ev["security_review_by"] is None
    assert tuple(ev["independent_adopters"]) == ()


# --- advance: every rung gated on its own evidence ---------------------

def test_full_evidence_climbs_the_whole_ladder():
    assert _climb(_evidence()) == PROTOCOL_MATURITY[-1]


def test_draft_protocol_requires_a_public_specification():
    rep = P.advance("EXPERIMENTAL_SCHEMA",
                    _evidence(public_specification=False))
    assert not rep["advanced"]
    assert any("public_specification" in m for m in rep["missing"])


def test_draft_protocol_requires_test_vectors():
    rep = P.advance("EXPERIMENTAL_SCHEMA", _evidence(test_vectors=False))
    assert not rep["advanced"]


def test_reference_implementation_requires_public_source():
    rep = P.advance("DRAFT_PROTOCOL",
                    _evidence(reference_implementation_public=False))
    assert not rep["advanced"]


def test_second_implementation_requires_a_second_implementor():
    rep = P.advance("REFERENCE_IMPLEMENTATION",
                    _evidence(second_implementor=None))
    assert not rep["advanced"]
    assert any("second_implementor" in m for m in rep["missing"])


def test_second_implementation_refuses_the_author_as_implementor():
    """Writing it twice yourself is not a second implementation."""
    rep = P.advance("REFERENCE_IMPLEMENTATION",
                    _evidence(second_implementor=P.AUTHOR_ID))
    assert not rep["advanced"]
    assert any("names the author" in m for m in rep["missing"])


def test_interoperability_requires_cross_implementation_agreement():
    rep = P.advance("SECOND_INDEPENDENT_IMPLEMENTATION",
                    _evidence(cross_implementation_conformance=None))
    assert not rep["advanced"]
    assert any("cross_implementation" in m for m in rep["missing"])


def test_interoperability_refuses_one_implementation_agreeing_with_itself():
    rep = P.advance("SECOND_INDEPENDENT_IMPLEMENTATION",
                    _evidence(cross_implementation_conformance={
                        "implementations": ["reference"],
                        "vectors_agreed": len(P.TEST_VECTORS),
                        "vectors_total": len(P.TEST_VECTORS)}))
    assert not rep["advanced"]


def test_interoperability_refuses_a_partial_vector_comparison():
    rep = P.advance("SECOND_INDEPENDENT_IMPLEMENTATION",
                    _evidence(cross_implementation_conformance={
                        "implementations": ["reference", "other"],
                        "vectors_agreed": 1, "vectors_total": 1}))
    assert not rep["advanced"]


def test_interoperability_refuses_disagreeing_vectors():
    n = len(P.TEST_VECTORS)
    rep = P.advance("SECOND_INDEPENDENT_IMPLEMENTATION",
                    _evidence(cross_implementation_conformance={
                        "implementations": ["reference", "other"],
                        "vectors_agreed": n - 1, "vectors_total": n}))
    assert not rep["advanced"]
    assert any("disagree" in m for m in rep["missing"])


def test_security_review_requires_an_independent_reviewer():
    rep = P.advance("INTEROPERABILITY_DEMONSTRATED",
                    _evidence(security_review_by=P.AUTHOR_ID))
    assert not rep["advanced"]
    assert any("names the author" in m for m in rep["missing"])


def test_open_governance_requires_a_body_that_is_not_the_author():
    rep = P.advance("SECURITY_REVIEWED",
                    _evidence(governance_body=P.AUTHOR_ID))
    assert not rep["advanced"]
    assert any("names the author" in m for m in rep["missing"])


def test_open_governance_requires_no_single_vendor_lock():
    rep = P.advance("SECURITY_REVIEWED",
                    _evidence(no_single_vendor_lock=False))
    assert not rep["advanced"]


def test_candidate_standard_rechecks_every_earlier_rung():
    """'All of the above' is implemented as all of the above."""
    rep = P.advance("OPEN_GOVERNANCE",
                    _evidence(second_implementor=None,
                              governance_body=None,
                              independent_adopters=("X",)))
    assert not rep["advanced"]
    assert any("second_implementor" in m for m in rep["missing"])
    assert any("governance_body" in m for m in rep["missing"])


def test_candidate_standard_requires_an_independent_adopter():
    rep = P.advance("OPEN_GOVERNANCE", _evidence(independent_adopters=()))
    assert not rep["advanced"]


def test_self_adoption_is_not_adoption():
    rep = P.advance("OPEN_GOVERNANCE",
                    _evidence(independent_adopters=(P.AUTHOR_ID,)))
    assert not rep["advanced"]
    assert any("Self-adoption" in m for m in rep["missing"])


def test_advance_rejects_a_rung_off_the_ladder():
    with pytest.raises(ValueError):
        P.advance("WORLD_STANDARD", _evidence())


def test_advance_at_the_top_stays_at_the_top():
    rep = P.advance(PROTOCOL_MATURITY[-1], _evidence())
    assert not rep["advanced"]
    assert rep["to"] == PROTOCOL_MATURITY[-1]


# --- authorship never advances maturity --------------------------------

def test_authorship_never_advances_maturity():
    for rung in PROTOCOL_MATURITY[:-1]:
        with pytest.raises(P.ProtocolRefused):
            P.advance(rung, _evidence(author_declares_standard=True))


def test_self_certification_is_refused():
    with pytest.raises(P.ProtocolRefused):
        P.advance("DRAFT_PROTOCOL", _evidence(self_certified=True))


def test_publication_is_not_standardization():
    with pytest.raises(P.ProtocolRefused):
        P.advance("EXPERIMENTAL_SCHEMA",
                  _evidence(published_therefore_standard=True))


def test_refuse_authority_by_authorship_cites_the_collapse():
    with pytest.raises(P.ProtocolRefused) as e:
        P.refuse_authority_by_authorship()
    assert FORBIDDEN_COLLAPSES["PUBLICATION_IS_STANDARDIZATION"] in \
        str(e.value)


def test_author_aliases_are_also_refused():
    rep = P.advance("REFERENCE_IMPLEMENTATION",
                    _evidence(second_implementor="the same person",
                              author_aliases=("the same person",)))
    assert not rep["advanced"]


# --- conformance vectors -----------------------------------------------

def test_there_are_vectors_for_every_declared_record_type():
    targets = " ".join(v.target for v in P.TEST_VECTORS)
    assert "chain_hash" in targets
    assert "KeyPath" in targets
    assert "Barycentric" in targets
    assert "ProbabilisticPayload.state" in targets


def test_vector_ids_are_unique():
    ids = [v.vector_id for v in P.TEST_VECTORS]
    assert len(set(ids)) == len(ids)


def test_all_vectors_pass_against_the_real_implementation():
    rep = P.run_conformance()
    assert rep["ok"], [r for r in rep["results"] if not r["passed"]]
    assert rep["passed"] == len(P.TEST_VECTORS)
    assert rep["failed"] == 0


def test_vectors_are_deterministic():
    a = P.run_conformance()["results"]
    b = P.run_conformance()["results"]
    assert [r["actual"] for r in a] == [r["actual"] for r in b]


def test_expected_values_are_literals_not_recomputed():
    """A vector that recomputes its own expectation catches nothing."""
    chain = [v for v in P.TEST_VECTORS
             if v.target.endswith("chain_hash")][0]
    assert isinstance(chain.expected, str)
    assert len(chain.expected) == 64
    key = [v for v in P.TEST_VECTORS if "KeyPath" in v.target][0]
    assert key.expected == [16789503, [1, 2, 4095]]
    bary = [v for v in P.TEST_VECTORS if "Barycentric" in v.target][0]
    assert bary.expected == ["1/10", "1/5", "3/10", "2/5"]


def test_a_regressed_implementation_fails_the_suite():
    """The point of a conformance vector."""
    class _BrokenKeyPath:
        def __init__(self, keys):
            self.keys = tuple(keys)

        def as_int(self):
            return 0                      # regression

        @classmethod
        def from_int(cls, v, depth):
            return cls((0,) * depth)

    class _Mailbox:
        KeyPath = _BrokenKeyPath
        Barycentric = None

    class _Impl:
        name = "broken"
        witness = None
        mailbox = _Mailbox

    rep = P.run_conformance(_Impl())
    assert not rep["ok"]
    assert rep["failed"] >= 1


def test_a_crashing_implementation_fails_rather_than_raising():
    class _Impl:
        name = "crashing"
        witness = None
        mailbox = None

    rep = P.run_conformance(_Impl())
    assert not rep["ok"]
    assert all(r["detail"] for r in rep["results"] if not r["passed"])


def test_conformance_is_not_interoperability():
    assert "not interoperability" in P.run_conformance()["note"]


# --- governance --------------------------------------------------------

def test_governance_reports_a_single_implementation():
    g = P.governance_status()
    assert g["single_implementation"] is True
    assert g["implementations"] == 1
    assert g["independent_implementations"] == 0


def test_governance_reports_a_single_author():
    g = P.governance_status()
    assert g["single_author"] is True
    assert g["authors"] == 1


def test_governance_reports_no_independent_body():
    g = P.governance_status()
    assert g["independent_governance_body"] is None
    assert g["has_independent_governance_body"] is False
    assert g["governance_process"] == "NONE"


def test_governance_reports_no_adoption():
    g = P.governance_status()
    assert g["adopters"] == 0
    assert g["independent_adopters"] == 0
    assert g["adoption"] == "NONE"


def test_governance_reports_reviews_not_performed():
    g = P.governance_status()
    for k in ("security_review", "privacy_review", "patent_review",
              "licensing_review"):
        assert g[k] == "NOT_PERFORMED"


def test_governance_admits_single_vendor_lock():
    assert P.governance_status()["single_vendor_lock"] is True


def test_governance_does_not_claim_interoperability():
    g = P.governance_status()
    assert g["interoperability_demonstrated"] is False
    assert g["cross_implementation_test_vectors_compared"] == 0


def test_governance_summary_is_not_flattering():
    s = P.governance_status()["summary"]
    assert "is not a standard" in s
    assert "governed by nobody" in s


def test_governance_maturity_agrees_with_current_maturity():
    assert P.governance_status()["maturity"] == P.current_maturity()


# --- documented process ------------------------------------------------

def test_deprecation_policy_protects_test_vectors():
    t = P.deprecation_policy()
    assert "TEST_VECTORS" in t
    assert "never edited to match new behaviour" in t


def test_deprecation_policy_never_weakens_a_refusal():
    assert "never deprecated toward a weaker position" in \
        P.deprecation_policy()


def test_change_process_classifies_vector_changes_as_breaking():
    t = P.change_process()
    assert "breaking" in t
    assert "TEST_VECTORS" in t


def test_change_process_admits_review_is_not_independent():
    assert "not simulate a committee" in P.change_process()


def test_protocol_report_is_assembled_from_the_real_functions():
    rep = P.protocol_report()
    assert rep["maturity"] == P.current_maturity()
    assert rep["conformance"]["ok"]
    assert rep["governance"]["single_author"] is True
    assert not rep["next_rung_report"]["advanced"]
