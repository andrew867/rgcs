"""P21 — forward source geocoder: pin / cell / region / alias set.

Covers: always produces a pin or region (never a bare refusal); a lone
calibrated family gives a calibrated point; the un-narrowed ensemble gives an
alias set; foreign-body vectors are typed out of scope and NOT force-decoded;
candidate != measured raises; determinism; schema conformance; and the T05
frozen-profile integration path (stubbed, with an optional real path).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas.icosahedron import build_icosahedron
from cwatlas.r1082 import claims as r1082_claims
from cwatlas.r1082 import geocode_forward as G
from cwatlas.r1082.claims import R1082ClaimError
from cwatlas.r1082.route_core import RouteError

SCHEMA_DIR = Path(__file__).resolve().parents[3] / "cwatlas" / "r1082" / "schemas"

#: Opaque, public/synthetic source-vector ids (no private narrative).
PUBLIC_VECTORS = ("165876523", "01|65|87|65|23", "1234567890", "0000000000",
                  "9999999999", "50|00|50|00|50")


@pytest.fixture(scope="module")
def ico():
    return build_icosahedron()


@pytest.fixture(scope="module")
def result_validator():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SCHEMA_DIR / "candidate_map_result.schema.json").read_text("utf-8"))
    return jsonschema.Draft202012Validator(schema)


# -- always a pin or region, never a bare refusal ---------------------------

@pytest.mark.parametrize("vector", PUBLIC_VECTORS)
def test_always_produces_pin_or_region(vector, ico):
    # Under a single-family calibration every eligible vector yields a point.
    sf = G.single_family_stub()
    res = G.geocode(vector, sf, shell=3, ico=ico)
    assert res.in_scope is True
    assert res.result_type in {
        "CANDIDATE_CALIBRATED_POINT", "CANDIDATE_REGION",
        "CANDIDATE_ALIAS_SET", "UNDERDETERMINED"}
    assert res.candidates, "the app must produce pins or regions, never nothing"


def test_single_family_gives_calibrated_point(ico):
    sf = G.single_family_stub("F1_CANONICAL_DIRECT_BE")
    res = G.geocode("165876523", sf, shell=3, ico=ico)
    assert res.result_type == "CANDIDATE_CALIBRATED_POINT"
    assert len(res.candidates) == 1
    assert res.calibration_available is True
    assert res.region is not None
    assert res.region["area_m2"] > 0.0            # never invented precision
    c = res.candidates[0]
    assert -90.0 <= c.latitude_deg <= 90.0
    assert -180.0 <= c.longitude_deg <= 180.0


def test_underdetermined_ensemble_gives_alias_set(ico):
    # The un-narrowed four-family ensemble does not agree -> an alias set (or a
    # diffuse UNDERDETERMINED region), never a single false pin.
    allp = G.default_frozen_stub()
    res = G.geocode("165876523", allp, shell=3, ico=ico)
    assert res.result_type in {"CANDIDATE_ALIAS_SET", "UNDERDETERMINED"}
    assert res.receipt["distinct_candidate_count"] >= 2
    assert res.region is not None and res.region["area_m2"] > 0.0


def test_uncalibrated_is_region_or_alias_not_calibrated_point(ico):
    res = G.geocode("165876523", None, shell=3, ico=ico)
    assert res.calibration_available is False
    # No calibration: never a calibrated point.
    assert res.result_type != "CANDIDATE_CALIBRATED_POINT"
    assert res.result_type in {"CANDIDATE_REGION", "CANDIDATE_ALIAS_SET",
                               "UNDERDETERMINED"}


# -- body-scope firewall ----------------------------------------------------

@pytest.mark.parametrize("body", ["MARS", "LUNA", "EUROPA", "TITAN"])
def test_foreign_body_typed_out_of_scope_not_force_decoded(body, ico):
    sf = G.single_family_stub()
    res = G.geocode("165876523", sf, shell=3, body=body, ico=ico)
    assert res.in_scope is False
    assert res.result_type == "INVALID"
    assert res.candidates == ()                     # NOT force-decoded
    assert "FOREIGN_BODY_OUT_OF_SCOPE" in res.reason
    assert res.receipt["force_decoded"] is False


@pytest.mark.parametrize("body", ["EARTH", "TERRA", "earth", "terra"])
def test_earth_terra_in_scope(body, ico):
    res = G.geocode("165876523", G.single_family_stub(), shell=3, body=body,
                    ico=ico)
    assert res.in_scope is True
    assert res.candidates


# -- shell supplies radius (no altitude missing) ----------------------------

@pytest.mark.parametrize("shell", range(0, 9))
def test_shell_supplies_radius_no_altitude_missing(shell, ico):
    res = G.geocode("165876523", G.single_family_stub(), shell=shell, ico=ico)
    assert res.radius_m is not None
    assert res.receipt["shell_supplies_radius"] is True
    assert res.receipt["altitude_missing"] is False
    for c in res.candidates:
        assert c.shell == shell


def test_bad_shell_refused(ico):
    with pytest.raises(RouteError):
        G.geocode("165876523", G.single_family_stub(), shell=9, ico=ico)


# -- malformed vector is a typed INVALID, still not a bare refusal -----------

def test_malformed_vector_is_typed_invalid(ico):
    res = G.geocode("not-a-vector", G.single_family_stub(), shell=3, ico=ico)
    assert res.result_type == "INVALID"
    assert res.in_scope is True
    assert "INVALID_SOURCE_VECTOR" in res.reason


# -- candidate != measured --------------------------------------------------

def test_candidate_is_not_measured_raises(ico):
    res = G.geocode("165876523", G.single_family_stub(), shell=3, ico=ico)
    assert res.is_candidate() is True
    with pytest.raises(R1082ClaimError):
        res.assert_not_measured()
    with pytest.raises(R1082ClaimError):
        res.to_serializable(as_measured=True)
    # The strongest evidence a candidate can carry is CALIBRATED_CANDIDATE.
    assert res.receipt["max_evidence"] == "CALIBRATED_CANDIDATE"
    assert res.map_result.evidence_class not in r1082_claims.MEASUREMENT_EVIDENCE


# -- determinism ------------------------------------------------------------

def test_determinism(ico):
    sf = G.single_family_stub()
    a = G.geocode("165876523", sf, shell=3, ico=ico)
    b = G.geocode("165876523", sf, shell=3, ico=ico)
    assert a.result_type == b.result_type
    assert a.candidates[0].latitude_deg == b.candidates[0].latitude_deg
    assert a.candidates[0].longitude_deg == b.candidates[0].longitude_deg
    assert a.receipt["receipt_hash"] == b.receipt["receipt_hash"]


# -- schema conformance -----------------------------------------------------

def test_schema_conformance_point_and_alias(result_validator, ico):
    point = G.geocode("165876523", G.single_family_stub(), shell=3, ico=ico)
    alias = G.geocode("165876523", G.default_frozen_stub(), shell=3, ico=ico)
    foreign = G.geocode("165876523", G.single_family_stub(), shell=3,
                        body="MARS", ico=ico)
    for res in (point, alias, foreign):
        result_validator.validate(res.to_serializable())


# -- report seals the claims ------------------------------------------------

def test_report_seals_claims():
    r = G.geocode_forward_report()
    assert r["phase_id"] == "P21"
    assert r["tranche"] == "T06"
    assert r["foreign_body_force_decoded"] is False
    assert r["shell_supplies_radius"] is True
    assert r["max_evidence"] == "CALIBRATED_CANDIDATE"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"


# -- T05 frozen-ensemble integration (stub always; real path if importable) --

def test_stub_shape_is_injectable(ico):
    sf = G.single_family_stub()
    assert sf.is_stub is True
    assert sf.retained_family_names
    assert sf.orientation_matrix().shape == (3, 3)
    names = G._frozen_family_names(sf)
    assert names == sf.retained_family_names


def test_t05_integration_path_or_stub(ico):
    # If the real T05 calibration is importable, decode under the REAL frozen
    # profile; else the stub path above proves the geocoder runs standalone.
    real = None
    try:
        from cwatlas.r1082 import calibration_fit, calibration_freeze
        fit = calibration_fit.fit_all()
        real = calibration_freeze.freeze_calibration(fit)
    except Exception:  # noqa: BLE001 - T05 absent or mid-build
        real = None
    if real is None:
        pytest.skip("tranche T05 not importable yet; stub path exercised")
    res = G.geocode("165876523", real, shell=3, ico=ico)
    assert res.in_scope is True
    assert res.candidates
    # A real frozen profile is duck-typed to the same shape the stub exposes.
    assert G._frozen_family_names(real)
    assert G._frozen_orientation(real).shape == (3, 3)
    # load_frozen_profile() picks up the real profile when T05 is present.
    loaded = G.load_frozen_profile()
    assert G.geocode("165876523", loaded, shell=3, ico=ico).candidates
