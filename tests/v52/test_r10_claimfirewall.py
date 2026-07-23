"""P03 — harm/medical/human-classification/financial claim firewall."""

from __future__ import annotations

import pytest

from r10 import claimfirewall as CF


def _claim(cat=CF.Quarantine.HARM_BIOLOGICAL):
    return CF.quarantine("c1", cat, "OMEGA_REGION_SOURCE",
                         "a source claim recorded verbatim",
                         rationale="quarantined per the harm firewall")


def test_a_claim_is_recorded_but_never_endorsed():
    c = _claim()
    assert c.evidence_status == "QUARANTINED"
    assert c.publication_class == "PRIVATE_ONLY"
    rec = c.public_record()
    assert rec["endorsed"] is False
    assert rec["verdict"] == "UNSUPPORTED"
    # the public record does not reproduce the claim text
    assert "recorded verbatim" not in str(rec)


def test_a_bad_evidence_status_is_refused_at_construction():
    with pytest.raises(CF.ClaimFirewallError):
        CF.QuarantinedClaim("c", CF.Quarantine.MEDICAL, "OMEGA_REGION_SOURCE",
                            "x", evidence_status="MEASURED")


@pytest.mark.parametrize("target", [
    "MEASURED", "REPLICATED", "SOFTWARE_VERIFIED",
    "PROSPECTIVE_PREDICTION", "CONFIRMED", "IDENTIFIED",
])
def test_promotion_to_an_evidentiary_status_is_refused(target):
    with pytest.raises(CF.ClaimFirewallError):
        CF.refuse_promotion(_claim(), target)


def test_the_only_survivable_statuses_are_non_endorsing():
    # these do not assert the claim is true, so they are allowed
    for ok in ("UNSUPPORTED", "CONTRADICTED", "UNRESOLVED"):
        CF.refuse_promotion(_claim(), ok)  # must not raise


def test_person_classification_is_always_refused():
    with pytest.raises(CF.ClaimFirewallError):
        CF.refuse_person_classification("anyone")


def test_biological_inference_from_a_group_is_refused():
    with pytest.raises(CF.ClaimFirewallError):
        CF.refuse_biological_inference_from_group("any group")


def test_pathogen_or_genetic_targeting_is_refused():
    with pytest.raises(CF.ClaimFirewallError):
        CF.refuse_pathogen_or_genetic_targeting()


def test_medical_advice_from_a_source_message_is_refused():
    with pytest.raises(CF.ClaimFirewallError):
        CF.refuse_medical_advice()


def test_public_accusation_is_refused():
    with pytest.raises(CF.ClaimFirewallError):
        CF.refuse_public_accusation()


def test_financial_action_is_refused():
    with pytest.raises(CF.ClaimFirewallError):
        CF.refuse_financial_action()


def test_every_quarantine_category_is_representable():
    for cat in CF.Quarantine:
        c = CF.quarantine("c", cat, "OMEGA_REGION_SOURCE", "x")
        assert c.category is cat


def test_report_asserts_nothing_and_endorses_nothing():
    r = CF.claimfirewall_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "UNSUPPORTED"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert set(q.value for q in CF.Quarantine) <= set(r["quarantine_categories"])
