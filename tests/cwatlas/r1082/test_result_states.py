"""P04 -- the result-class state machine and the evidence firewall."""

from __future__ import annotations

import pytest

from cwatlas.r1082 import claims
from cwatlas.r1082 import result_states as RS
from cwatlas.r1082.claims import EvidenceClass, ResultClass

CRS = "EARTH_ROOT_D_V1"
EPOCH = 2020.5


def test_seven_result_classes_have_evidence_and_codes():
    for rc in ResultClass:
        ev = RS.evidence_for(rc)
        assert isinstance(ev, EvidenceClass)
        assert rc.value in RS.result_states_report()["api_codes"]


def test_canonical_exact_point_is_derived_mathematics():
    r = RS.classify(valid=True, candidate_count=1, calibration_available=True,
                    canonical_exact=True, crs=CRS, epoch=EPOCH)
    assert r.result_class is ResultClass.CANONICAL_EXACT_POINT
    assert r.evidence_class is EvidenceClass.DERIVED_MATHEMATICS
    assert not r.is_candidate()


def test_single_candidate_with_calibration_is_calibrated_point():
    r = RS.classify(valid=True, candidate_count=1, calibration_available=True,
                    crs=CRS, epoch=EPOCH)
    assert r.result_class is ResultClass.CANDIDATE_CALIBRATED_POINT
    assert r.evidence_class is EvidenceClass.CALIBRATED_CANDIDATE


def test_single_candidate_without_calibration_falls_to_region():
    r = RS.classify(valid=True, candidate_count=1, calibration_available=False,
                    crs=CRS, epoch=EPOCH)
    assert r.result_class is ResultClass.CANDIDATE_REGION  # no invented pin


def test_small_set_is_alias_set_large_set_underdetermined():
    small = RS.classify(valid=True, candidate_count=3,
                        calibration_available=True, crs=CRS, epoch=EPOCH)
    assert small.result_class is ResultClass.CANDIDATE_ALIAS_SET
    big = RS.classify(valid=True, candidate_count=99,
                      calibration_available=True, crs=CRS, epoch=EPOCH)
    assert big.result_class is ResultClass.UNDERDETERMINED


def test_missing_crs_or_epoch_requires_calibration():
    r = RS.classify(valid=True, candidate_count=1, calibration_available=True,
                    crs=None, epoch=None)
    assert r.result_class is ResultClass.CALIBRATION_REQUIRED
    assert r.api_code == "E_CALIBRATION_REQUIRED"


def test_invalid_and_zero_candidates():
    assert RS.classify(valid=False, candidate_count=0,
                       calibration_available=False).result_class \
        is ResultClass.INVALID
    assert RS.classify(valid=True, candidate_count=0,
                       calibration_available=False, crs=CRS,
                       epoch=EPOCH).result_class is ResultClass.UNDERDETERMINED


def test_no_candidate_class_is_measurement_evidence():
    # The firewall: no result class carries MEASURED or REPLICATED evidence.
    for rc in ResultClass:
        assert RS.evidence_for(rc) not in claims.MEASUREMENT_EVIDENCE


def test_candidate_cannot_be_serialized_as_measured():
    r = RS.classify(valid=True, candidate_count=1, calibration_available=True,
                    crs=CRS, epoch=EPOCH)
    assert r.is_candidate()
    with pytest.raises(claims.R1082ClaimError):
        r.assert_not_measured()
    with pytest.raises(claims.R1082ClaimError):
        r.to_serializable(as_measured=True)
    # A non-measured serialization is fine and stays a software result.
    payload = r.to_serializable()
    assert payload["evidence_class"] == "CALIBRATED_CANDIDATE"
    assert payload["measured_here"] == "nothing"


def test_migration_from_legacy_no_unique_decode():
    # The old bare refusal becomes a bounded region / alias set / underdetermined,
    # never breaking the firewall.
    region = RS.migrate_no_unique_decode(candidate_count=1,
                                         calibration_available=False,
                                         crs=CRS, epoch=EPOCH)
    assert region.result_class is ResultClass.CANDIDATE_REGION
    aliases = RS.migrate_no_unique_decode(candidate_count=4,
                                          calibration_available=True,
                                          crs=CRS, epoch=EPOCH)
    assert aliases.result_class is ResultClass.CANDIDATE_ALIAS_SET
    for r in (region, aliases):
        assert r.evidence_class not in claims.MEASUREMENT_EVIDENCE


def test_classify_is_deterministic():
    kw = dict(valid=True, candidate_count=3, calibration_available=True,
              crs=CRS, epoch=EPOCH)
    assert RS.classify(**kw).to_serializable() == RS.classify(**kw).to_serializable()


def test_report_seals_origin_and_effects():
    r = RS.result_states_report()
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["measured_here"] == "nothing"
    assert r["legacy_migrated_from"] == "NO_UNIQUE_GEOGRAPHIC_DECODE"
