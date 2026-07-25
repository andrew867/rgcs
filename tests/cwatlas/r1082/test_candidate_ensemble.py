"""P20 — candidate map ensemble and agreement surface.

Schema conformance, one layer per profile combination, the agreement surface,
distinct anchor rendering, exports, determinism, and the negatives
(uncertainty never collapsed, candidate != measured, famous-place reward
refused).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cwatlas.r1082 import (
    calibration_fit,
    calibration_freeze,
    candidate_ensemble as E,
    claims,
    wilkes,
)

SCHEMA_DIR = (Path(__file__).resolve().parents[3]
              / "cwatlas" / "r1082" / "schemas")


@pytest.fixture(scope="module")
def frozen():
    return calibration_freeze.freeze_calibration(calibration_fit.fit_all())


@pytest.fixture(scope="module")
def result(frozen):
    return E.build_candidate_map((7, 7, 7, 7, 7), frozen)


@pytest.fixture(scope="module")
def map_validator():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(
        (SCHEMA_DIR / "candidate_map_result.schema.json").read_text("utf-8"))
    return jsonschema.Draft202012Validator(schema)


def test_result_conforms_to_schema(result, map_validator):
    map_validator.validate(result.to_result_dict())
    doc = result.to_result_dict()
    assert doc["profile_id"] == "EARTH_ROOT_D_V1"
    assert doc["result_type"] in {"CANDIDATE_ALIAS_SET",
                                  "CANDIDATE_CALIBRATED_POINT"}


def test_one_layer_per_profile_combination(result):
    ens = wilkes.default_ensemble()
    n_families = 4                       # all retained
    n_wilkes = len(ens.profiles)         # 3
    n_epochs = len(E.DEFAULT_EPOCH_PROFILES)   # 3
    assert len(result.members) == n_families * n_wilkes * n_epochs


def test_agreement_surface_has_multiple_clusters(result):
    # Retained families disagree, so the surface shows >1 cluster and the
    # result is an alias set (uncertainty is NOT collapsed to one pin).
    s = result.surface
    assert s.cluster_count > 1
    assert result.result_type == "CANDIDATE_ALIAS_SET"
    assert s.dispersion_rad > 0.0
    assert any(v > 0.0 for v in s.per_component_variance)


def test_f1_f3_land_in_same_cluster(result):
    # F1 and F3 map identically, so their members share a cluster.
    surface = result.surface
    fam_of = [m.family_name for m in result.members]
    # find a cluster containing an F1 member; it must also contain an F3 member.
    for cluster in surface.clusters:
        fams = {fam_of[i] for i in cluster}
        if "F1_CANONICAL_DIRECT_BE" in fams:
            assert "F3_CANONICAL_ROOTREL_BE" in fams


def test_training_anchors_rendered_distinctly(result):
    assert len(result.training_anchors) == 2
    for a in result.training_anchors:
        assert a.is_training_anchor is True
    for m in result.members:
        assert m.is_training_anchor is False
    names = {a.family_name for a in result.training_anchors}
    assert "WILKES_FIXED_ROOT" in names
    assert "STONEHENGE_PRIVATE_001" in names


def test_exports_geojson_kml_json(result):
    gj = result.to_geojson()
    assert gj["type"] == "FeatureCollection"
    # candidate members + two training anchors.
    assert len(gj["features"]) == len(result.members) + 2
    kml = result.to_kml()
    assert kml.startswith("<?xml")
    assert "TRAINING_ANCHOR" in kml
    parsed = json.loads(result.to_json())
    assert parsed["result_type"] == result.result_type


def test_determinism(frozen):
    r1 = E.build_candidate_map((7, 7, 7, 7, 7), frozen)
    r2 = E.build_candidate_map((7, 7, 7, 7, 7), frozen)
    assert r1.to_json() == r2.to_json()
    assert r1.freeze_hash == r2.freeze_hash


# -- negatives --------------------------------------------------------------

def test_negative_uncertainty_never_collapsed(result):
    unc = result.to_result_dict()["uncertainty"]
    assert unc["collapsed_to_point"] is False
    assert unc["agreement_surface"]["collapsed_to_point"] is False


def test_negative_candidate_is_not_measured():
    with pytest.raises(claims.R1082ClaimError):
        E.refuse_candidate_as_measured()


def test_negative_famous_place_reward_refused():
    with pytest.raises(claims.R1082ClaimError):
        E.refuse_famous_place_reward()


def test_report_seals_claims():
    r = E.candidate_ensemble_report()
    assert r["phase_id"] == "P20"
    assert r["result_type"] in {"CANDIDATE_ALIAS_SET",
                                "CANDIDATE_CALIBRATED_POINT"}
    assert r["uncertainty_collapsed_to_point"] is False
    assert r["training_anchors_rendered_distinctly"] is True
    assert r["famous_place_proximity_rewarded"] is False
    assert r["evidence_class"] == "CALIBRATED_CANDIDATE"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
