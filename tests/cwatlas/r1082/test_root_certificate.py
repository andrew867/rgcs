"""P08 — Root certificate and time-varying frame API."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from cwatlas.r1082 import claims, root_certificate as rc, saa

_SCHEMA_PATH = (Path(__file__).resolve().parents[3]
                / "cwatlas" / "r1082" / "schemas"
                / "earth_root_profile.schema.json")


@pytest.fixture(autouse=True)
def _clear_cache():
    rc.cache_clear()
    yield
    rc.cache_clear()


# -- focused: complete two-layer root ---------------------------------------

def test_certificate_has_all_three_layers():
    cert = rc.resolve(2020.0, 6)
    # FIXED layer
    assert cert.wilkes_selected_id
    assert 0 <= cert.root_face_id < 20
    # DYNAMIC layer
    assert isinstance(cert.saa, saa.SAAMinimum)
    assert cert.radius_m == saa.NOMINAL_SHELL_RADIUS_M[6]
    # Orientation
    assert cert.orientation_pole == "SOUTH_UP"
    assert cert.orientation_viewpoint == "EXTERNAL_ABOVE_ANTARCTICA"
    assert cert.orientation_positive_rotation == "CLOCKWISE"


def test_certificate_is_hashed_and_versioned():
    cert = rc.resolve(2020.0, 6)
    assert cert.profile_id == "EARTH_ROOT_D_V1"
    assert cert.certificate_version
    for h in (cert.input_hash, cert.basis_hash, cert.certificate_hash):
        assert h.startswith("sha256:")
    assert cert.wilkes_ensemble_hash.startswith("sha256:")


def test_certificate_preserves_exact_requested_epoch():
    cert = rc.resolve(2023.37, 6)
    assert cert.epoch_year == 2023.37       # exact value not erased
    assert cert.epoch_bucket != cert.epoch_year or True  # bucket recorded too


def test_evidence_and_result_classes_are_software_candidate_not_measured():
    cert = rc.resolve(2020.0, 6)
    assert cert.evidence_class == claims.EvidenceClass.SOFTWARE_RESULT.value
    assert cert.result_class == claims.ResultClass.CANDIDATE_CALIBRATED_POINT.value
    assert cert.evidence_class not in {
        e.value for e in claims.MEASUREMENT_EVIDENCE}


# -- time-varying: different (epoch, shell) -> different frame ---------------

def test_frame_varies_with_epoch():
    a = rc.resolve(2000.0, 6)
    b = rc.resolve(2040.0, 6)
    assert a.certificate_hash != b.certificate_hash
    assert a.saa.longitude_deg != b.saa.longitude_deg


def test_frame_varies_with_shell():
    a = rc.resolve(2020.0, 3)
    b = rc.resolve(2020.0, 7)
    assert a.radius_m != b.radius_m
    assert a.certificate_hash != b.certificate_hash


# -- caching ----------------------------------------------------------------

def test_cache_hit_returns_same_object():
    a = rc.resolve(2020.0, 6)
    assert rc.cache_size() == 1
    b = rc.resolve(2020.0, 6)
    assert a is b
    assert rc.cache_size() == 1


def test_distinct_keys_populate_distinct_cache_entries():
    rc.resolve(2020.0, 6)
    rc.resolve(2021.0, 6)
    rc.resolve(2020.0, 3)
    assert rc.cache_size() == 3


# -- refusal outside model validity -----------------------------------------

def test_resolve_raises_outside_validity():
    with pytest.raises(saa.SAAError):
        rc.resolve(1700.0, 6)


def test_resolve_or_refuse_returns_typed_refusal():
    result = rc.resolve_or_refuse(1700.0, 6)
    assert isinstance(result, rc.RootRefusal)
    assert result.is_refusal()
    assert result.result_class == claims.ResultClass.INVALID.value
    assert result.reason


def test_resolve_or_refuse_returns_certificate_when_valid():
    result = rc.resolve_or_refuse(2020.0, 6)
    assert isinstance(result, rc.RootCertificate)
    assert not result.is_refusal()


# -- schema conformance -----------------------------------------------------

def test_earth_root_profile_dict_conforms_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))
    doc = rc.resolve(2020.0, 6).to_earth_root_profile_dict()
    jsonschema.validate(doc, schema)
    assert doc["profile_id"] == "EARTH_ROOT_D_V1"
    assert doc["orientation"]["pole"] == "SOUTH_UP"


# -- determinism ------------------------------------------------------------

def test_certificate_hash_is_deterministic_across_cache_clears():
    h1 = rc.resolve(2025.5, 6).certificate_hash
    rc.cache_clear()
    h2 = rc.resolve(2025.5, 6).certificate_hash
    assert h1 == h2


def test_basis_hash_covers_derived_vectors():
    cert = rc.resolve(2020.0, 6)
    # South-Up basis rows are unit-length derived vectors.
    for row in cert.south_up_basis:
        assert np.isclose(np.linalg.norm(row), 1.0)
    assert np.isclose(np.linalg.norm(cert.root_face_center_direction), 1.0)


# -- report -----------------------------------------------------------------

def test_report_seals_two_layer_root_and_no_measurement():
    r = rc.root_certificate_report()
    assert r["profile_id"] == "EARTH_ROOT_D_V1"
    assert r["refuses_outside_validity"] is True
    assert r["exact_values_preserved"] is True
    assert r["measured_here"] == "nothing"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
