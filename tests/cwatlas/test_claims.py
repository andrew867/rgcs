"""CW Atlas governance core: claim taxonomy and forbidden promotions."""

from __future__ import annotations

import pytest

from cwatlas import claims as C


def test_taxonomy_has_the_seven_classes():
    assert len(list(C.ClaimClass)) == 7
    assert C.ClaimClass.CANONICAL_ROUND_TRIP in C.ClaimClass
    assert C.ClaimClass.CALIBRATED_MAPPING in C.EVIDENCE_GATED_CLASSES


def test_source_ceiling_is_mathematical_translation():
    assert C.MAX_SOURCE_CLASS is C.ClaimClass.MATHEMATICAL_TRANSLATION
    assert C.MAX_SOURCE_CLASS not in C.EVIDENCE_GATED_CLASSES


def test_a_claim_needs_a_justification():
    with pytest.raises(C.ClaimError):
        C.Claim("x", C.ClaimClass.MATHEMATICAL_TRANSLATION, "")


def test_pin_without_crs_or_epoch_is_refused():
    with pytest.raises(C.ClaimError):
        C.refuse_pin_without_crs_epoch(crs=None, epoch=None)
    with pytest.raises(C.ClaimError):
        C.refuse_pin_without_crs_epoch(crs="WGS84", epoch=None)
    # a pin WITH crs + epoch is allowed (no raise)
    C.refuse_pin_without_crs_epoch(crs="WGS84", epoch=2025.0)


@pytest.mark.parametrize("name", [
    "source_as_geographic", "alias_as_unique", "close_match_as_intent",
    "synthetic_codec_as_source_meaning", "pin_without_crs_epoch",
    "control_claim", "patent_as_craft_validation", "site_decoded",
])
def test_every_forbidden_promotion_raises(name):
    with pytest.raises(C.ClaimError):
        C.FORBIDDEN_PROMOTIONS[name]()


def test_there_are_eight_forbidden_promotions():
    assert len(C.FORBIDDEN_PROMOTIONS) == 8


def test_report_claims_nothing_and_seals_source_semantics():
    r = C.claims_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["max_source_class"] == "MATHEMATICAL_TRANSLATION"
