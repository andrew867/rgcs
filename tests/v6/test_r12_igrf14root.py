"""R12 — IGRF-14 magnetic-root certificate: the mandatory epoch, the
coefficient-set labels, the secular-variation drift (POWER), and the
blocked coefficient grid."""

from __future__ import annotations

import pytest

from r11.earthface import MagneticScalar
from r12 import igrf14root as I


# --- the epoch is mandatory --------------------------------------------

def test_refuse_root_without_epoch_always_raises():
    with pytest.raises(I.Igrf14Error, match="MANDATORY"):
        I.refuse_root_without_epoch()


def test_certificate_construction_refuses_a_missing_epoch():
    with pytest.raises(I.Igrf14Error):
        I.Igrf14Certificate(
            epoch_decimal_year=None,
            coefficient_set=I.CoefficientSet.DEFINITIVE,
            gradient_scalar=MagneticScalar.TOTAL_INTENSITY,
            sign_rule="BOTH_SIGNS_RETAINED",
            handedness="RIGHT",
            uncertainty_nT=150.0,
        )


def test_a_fully_declared_certificate_is_constructible():
    cert = I.default_certificate(2020.0)
    assert cert.epoch_decimal_year == 2020.0
    assert cert.coefficient_set is I.CoefficientSet.DEFINITIVE


# --- epoch validity classification -------------------------------------

@pytest.mark.parametrize("year,expected", [
    (1905.0, I.EpochValidity.DEFINITIVE),
    (2020.0, I.EpochValidity.DEFINITIVE),
    (2028.0, I.EpochValidity.EXTRAPOLATED),
    (1850.0, I.EpochValidity.OUT_OF_RANGE),
])
def test_epoch_validity_classifies_the_span(year, expected):
    assert I.epoch_validity(year) is expected


def test_the_provisional_epoch_is_provisional():
    assert I.epoch_validity(2025.0) is I.EpochValidity.PROVISIONAL
    assert I.epoch_validity(2023.0) is I.EpochValidity.PROVISIONAL


def test_coefficient_set_for_refuses_out_of_range():
    with pytest.raises(I.Igrf14Error):
        I.coefficient_set_for(1850.0)


# --- the extrapolation label refusal -----------------------------------

def test_refuse_extrapolated_as_definitive_raises_in_forecast_window():
    with pytest.raises(I.Igrf14Error, match="DEFINITIVE"):
        I.refuse_extrapolated_as_definitive(
            2028.0, declared=I.CoefficientSet.DEFINITIVE)


def test_refuse_extrapolated_as_definitive_accepts_a_matched_label():
    rec = I.refuse_extrapolated_as_definitive(
        2028.0, declared=I.CoefficientSet.EXTRAPOLATED)
    assert rec["consistent"] is True
    assert rec["actual"] == "EXTRAPOLATED"


def test_certificate_refuses_definitive_label_in_forecast_window():
    with pytest.raises(I.Igrf14Error):
        I.Igrf14Certificate(
            epoch_decimal_year=2028.0,
            coefficient_set=I.CoefficientSet.DEFINITIVE,
            gradient_scalar=MagneticScalar.TOTAL_INTENSITY,
            sign_rule="BOTH_SIGNS_RETAINED",
            handedness="RIGHT",
            uncertainty_nT=200.0,
        )


# --- secular variation: the epoch is load-bearing (POWER) --------------

def test_drift_is_zero_for_equal_epochs():
    d = I.drift_between(2020.0, 2020.0, sv_nT_per_year=50.0)
    assert d["drift_nT"] == 0.0
    assert d["epochs_equal"] is True
    assert d["root_ambiguous_without_epoch"] is False


def test_drift_is_nonzero_over_ten_years_with_nonzero_sv():
    """POWER: a real secular variation over a real span moves the root."""
    d = I.drift_between(2010.0, 2020.0, sv_nT_per_year=50.0)
    assert d["delta_years"] == 10.0
    assert d["drift_nT"] == pytest.approx(500.0)
    assert d["root_ambiguous_without_epoch"] is True
    assert d["ambiguity_nT_if_epoch_omitted"] == pytest.approx(500.0)


def test_zero_sv_gives_no_drift_even_over_a_span():
    d = I.drift_between(2010.0, 2020.0, sv_nT_per_year=0.0)
    assert d["drift_nT"] == 0.0
    assert d["root_ambiguous_without_epoch"] is False


# --- the blocked coefficient grid --------------------------------------

def test_grid_status_is_blocked_missing_data():
    assert I.GRID_STATUS == "BLOCKED_MISSING_DATA"


def test_magnetic_root_returns_a_candidate_not_a_root():
    cert = I.default_certificate(2020.0)
    out = I.magnetic_root(cert)
    assert out["root_status"] == "ROOT_CANDIDATE_REQUIRES_REAL_COEFFICIENTS"
    assert out["identified"] is False
    assert out["latitude_deg"] is None
    assert out["grid_status"] == "BLOCKED_MISSING_DATA"


def test_supplied_numbers_do_not_become_igrf_coefficients():
    cert = I.default_certificate(2020.0)
    out = I.magnetic_root(cert, coefficients=[1.0, 2.0, 3.0])
    assert out["identified"] is False
    assert out["root_status"] == "ROOT_CANDIDATE_REQUIRES_REAL_COEFFICIENTS"


def test_refuse_root_identification_always_raises():
    with pytest.raises(I.Igrf14Error, match="BLOCKED_MISSING_DATA"):
        I.refuse_root_identification(latitude_deg=34.8, longitude_deg=-111.7)


def test_refuse_root_identification_raises_with_no_coordinates_too():
    with pytest.raises(I.Igrf14Error):
        I.refuse_root_identification()


# --- reuse of R11: Earth is a legitimate dynamo body -------------------

def test_earth_is_a_dynamo_body_so_the_method_is_legitimate():
    rec = I.require_dynamo_body("EARTH")
    assert rec["field_class"] == "INTRINSIC_DYNAMO_FIELD"
    assert rec["earth_method_legitimate_here"] is True


def test_the_earth_model_is_refused_on_a_non_dynamo_body():
    with pytest.raises(I.Igrf14Error):
        I.require_dynamo_body("MARS")


# --- the certificate certifies as epoch-bound, never timeless ----------

def test_certificate_certifies_as_epoch_bound_not_timeless():
    cert = I.default_certificate(2020.0)
    rec = I.certify_epoch_bound(cert)
    assert rec["timeless"] is False
    assert rec["epoch_bound"] is True
    assert "epoch" in rec["r11_timeless_refusal"].lower()


def test_refuse_timeless_igrf_root_raises():
    cert = I.default_certificate(2020.0)
    with pytest.raises(I.Igrf14Error):
        I.refuse_timeless_igrf_root(cert)


# --- report ------------------------------------------------------------

def test_report_carries_verdict_and_claim_discipline():
    r = I.igrf14root_report()
    assert r["verdict"] == "IGRF14_ROOT_CERTIFICATE_EPOCH_BOUND_GRID_BLOCKED"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "SOURCE_ESTABLISHED_PHYSICS"
    assert r["grid_status"] == "BLOCKED_MISSING_DATA"
    assert "what_this_does_not_say" in r
