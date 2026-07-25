"""P05 — Wilkes fixed-anchor profile registry (the FIXED spatial layer)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from cwatlas.r1082 import wilkes

_SCHEMA_PATH = (Path(__file__).resolve().parents[3]
                / "cwatlas" / "r1082" / "schemas"
                / "earth_root_profile.schema.json")


def _schema() -> dict:
    return json.loads(_SCHEMA_PATH.read_text(encoding="utf-8"))


# -- focused ----------------------------------------------------------------

def test_default_ensemble_has_multiple_candidates():
    ens = wilkes.default_ensemble()
    assert len(ens.profiles) >= 2  # multiple defensible candidates (P05 §2)
    assert ens.selected_id in {p.candidate_id for p in ens.profiles}


def test_centroid_is_in_wilkes_land_region_southern_hemisphere():
    p = wilkes.default_ensemble().selected()
    assert p.centroid_lat_deg < 0.0            # Southern Hemisphere
    assert -80.0 < p.centroid_lat_deg < -55.0  # Wilkes Land latitudes
    assert 120.0 < p.centroid_lon_deg < 150.0  # Wilkes Land longitudes


def test_selected_centroid_binds_to_root_face_center():
    ens = wilkes.default_ensemble()
    face_id = ens.root_face_id()
    assert 0 <= face_id < 20
    d = ens.root_face_center_direction()
    assert np.isclose(np.linalg.norm(d), 1.0)


def test_evidence_class_is_operator_selection_not_measured():
    p = wilkes.default_ensemble().selected()
    assert p.selection_basis == "OPERATOR_SELECTION"


# -- negative: uncertainty never collapsed to a point -----------------------

def test_point_uncertainty_is_refused():
    with pytest.raises(wilkes.WilkesError):
        wilkes.WilkesProfile(
            candidate_id="ZERO", centroid_lat_deg=-66.5, centroid_lon_deg=135.0,
            cov_deg2=((0.0, 0.0), (0.0, 0.0)))


def test_non_positive_definite_covariance_is_refused():
    with pytest.raises(wilkes.WilkesError):
        wilkes.WilkesProfile(
            candidate_id="NEG", centroid_lat_deg=-66.5, centroid_lon_deg=135.0,
            cov_deg2=((1.0, 0.0), (0.0, -1.0)))


def test_asymmetric_covariance_is_refused():
    with pytest.raises(wilkes.WilkesError):
        wilkes.WilkesProfile(
            candidate_id="ASYM", centroid_lat_deg=-66.5, centroid_lon_deg=135.0,
            cov_deg2=((4.0, 1.0), (2.0, 9.0)))


def test_every_default_profile_has_nonzero_uncertainty_area():
    for p in wilkes.default_ensemble().profiles:
        assert p.uncertainty_area_deg2() > 0.0


def test_refuse_helper_raises():
    with pytest.raises(wilkes.WilkesError):
        wilkes.refuse_point_uncertainty()


# -- ensemble integrity -----------------------------------------------------

def test_duplicate_candidate_ids_refused():
    p = wilkes.WilkesProfile("DUP", -66.5, 135.0, ((4.0, 0.0), (0.0, 9.0)))
    q = wilkes.WilkesProfile("DUP", -67.0, 136.0, ((4.0, 0.0), (0.0, 9.0)))
    with pytest.raises(wilkes.WilkesError):
        wilkes.WilkesEnsemble(profiles=(p, q), selected_id="DUP")


def test_unknown_selected_id_refused():
    p = wilkes.WilkesProfile("A", -66.5, 135.0, ((4.0, 0.0), (0.0, 9.0)))
    with pytest.raises(wilkes.WilkesError):
        wilkes.WilkesEnsemble(profiles=(p,), selected_id="MISSING")


# -- schema conformance -----------------------------------------------------

def test_fixed_anchor_conforms_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    fa_schema = _schema()["properties"]["fixed_anchor"]
    for p in wilkes.default_ensemble().profiles:
        jsonschema.validate(p.to_fixed_anchor_dict(), fa_schema)


def test_fixed_anchor_declares_uncertainty_not_collapsed():
    fa = wilkes.default_ensemble().selected().to_fixed_anchor_dict()
    assert fa["uncertainty"]["collapsed_to_point"] is False
    assert fa["uncertainty"]["area_deg2"] > 0.0


# -- determinism ------------------------------------------------------------

def test_ensemble_hash_is_deterministic():
    assert (wilkes.default_ensemble().ensemble_hash()
            == wilkes.default_ensemble().ensemble_hash())


def test_profile_hash_is_deterministic():
    p = wilkes.default_ensemble().selected()
    assert p.profile_hash() == p.profile_hash()


# -- report -----------------------------------------------------------------

def test_report_seals_no_measurement():
    r = wilkes.wilkes_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["uncertainty_collapsed_to_point"] is False
    assert "verdict" in r
