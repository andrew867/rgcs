"""RCW P03/P05 locks — claim classes, corpus registry, honest projection.

Training equalities stay training; corrections keep their raw
provenance; the projection layer always reports UNDERDETERMINED with
its assumptions listed; nothing promotes a fitted profile into
validation.
"""

import pytest

import rgcs_coordinate as rc
from rgcs_coordinate.domain import claims
from rgcs_coordinate.provenance import corpus


# --- claim classes -----------------------------------------------------

def test_standing_claims_block():
    assert claims.STANDING_CLAIMS["SOURCE_ORIGIN_VALIDATED"] == "no"
    assert claims.STANDING_CLAIMS[
        "STONEHENGE_INDEPENDENTLY_DECODED"].startswith("no")
    assert claims.STANDING_CLAIMS[
        "OCTAL_PACKET_STRUCTURE_RECOVERED"] == "yes"
    assert "underdetermined" in claims.STANDING_CLAIMS[
        "PHYSICAL_PROJECTION"]
    assert claims.ACTIVE_LONG_ORIGIN_EPOCH_REFERENCE == "BA_130"


def test_promotion_refused():
    with pytest.raises(claims.ClaimBoundaryError, match="never a promotion"):
        claims.refuse_promotion(claims.ClaimClass.TRAINING_EQUALITY,
                                claims.ClaimClass.EXACT_STRUCTURAL)


# --- corpus ------------------------------------------------------------

def test_corpus_validates_against_arithmetic():
    report = corpus.validate_corpus()
    assert report["valid"], report["failures"]
    assert report["vectors_checked"] == 4


def test_corpus_training_labels_and_correction():
    training = corpus.training_vectors()
    assert [v.raw_decimal for v in training] == ["165876523"]
    corrected = [v for v in corpus.vectors() if v.corrected]
    assert len(corrected) == 1
    v = corrected[0]
    assert v.raw_decimal == "165892763"
    assert v.raw_extracted_shell == 3 and v.active_shell == 7
    assert v.correction_class == \
        "OPERATOR_CORRECTION_TRANSCRIPTION_OR_PACKET_ERROR"


def test_corpus_validation_catches_bad_fixture():
    doc = corpus.load_corpus()
    doc["vectors"][0]["face"] = 9
    report = corpus.validate_corpus(doc)
    assert not report["valid"]
    assert any("face" in f for f in report["failures"])


def test_corpus_excludes_private_provenance():
    doc = corpus.load_corpus()
    assert "private" not in str(doc.get("chronology", {})).lower() \
        or "excluded" in str(doc["chronology"]).lower()
    assert doc["holdouts"]["status"] == "none published"


# --- registries --------------------------------------------------------

def test_codec_and_profile_registries():
    codecs = rc.list_codecs()
    assert [c["codec_id"] for c in codecs] == ["federation-terra-30"]
    assert codecs[0]["physical_projection"] == "UNDERDETERMINED"
    codecs[0]["codec_id"] = "mutated"           # copies only
    assert rc.list_codecs()[0]["codec_id"] == "federation-terra-30"

    profiles = rc.list_body_profiles()
    assert [p["profile_id"] for p in profiles] == ["earth-r1085a"]
    assert "YELLOW" in profiles[0]["status"]
    assert profiles[0]["long_origin_epoch_reference"] == "BA_130"


# --- honest projection -------------------------------------------------

def test_project_coordinate_is_underdetermined_with_assumptions():
    result = rc.project_coordinate(165876523)
    assert result["status"] == "UNDERDETERMINED"
    assert result["claim_class"] == "UNDERDETERMINED"
    assert len(result["assumptions"]) >= 5
    assert result["claims"]["source_origin_validated"] is False
    if result["backend"]["status"] == "OK":       # repo checkout
        cand = result["candidate"]
        assert cand["claim_class"] == "DERIVED_CANDIDATE"
        assert "TRAINING_CALIBRATED" in cand["label"]
    else:
        assert result["backend"]["status"] == "PROFILE_BACKEND_UNAVAILABLE"


def test_inverse_project_reports_aliasing_not_uniqueness():
    result = rc.inverse_project(51.1789, -1.8262, 10.8164)
    assert result["status"] == "UNDERDETERMINED"
    if result["backend"]["status"] == "OK":
        cand = result["candidate"]
        assert "NOT_PROVEN" in cand["uniqueness"]
        assert cand["word"] == 165876523      # regression fixture, labelled
    # and either way the claims block is present
    assert result["claims"]["stonehenge_independently_decoded"] is False


def test_unknown_profile_and_codec_refused():
    with pytest.raises(KeyError, match="unsupported body profile"):
        rc.project_coordinate(165876523, profile="mars-fantasy")
    with pytest.raises(KeyError, match="unsupported codec"):
        rc.decode_coordinate(165876523, codec="base-100")
