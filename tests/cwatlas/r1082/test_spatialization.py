"""P15 — recursive eight-way spatialization families (bounded ensemble)."""

from __future__ import annotations

import random

import numpy as np
import pytest

from cwatlas.r1082 import spatialization as S
from cwatlas.r1082.partition import build_partition


def test_family_ensemble_is_bounded_and_counted():
    # Exactly four families (architecture spec), all distinct, all invertible.
    assert S.FAMILY_COUNT == 4 == len(S.FAMILIES)
    names = [f.name for f in S.FAMILIES]
    assert len(set(names)) == 4
    for f in S.FAMILIES:
        d = f.descriptor()
        assert d["invertible"] is True
        assert d["uses_hash_or_catalogue"] is False
        assert d["path_depth"] == S.PATH_DEPTH
        assert d["route_space"] == S.TOKEN_BASE ** S.ROUTE_TOKENS


def test_route_address_round_trip_power_per_family():
    rng = random.Random(20260725)
    for fam in S.FAMILIES:
        for _ in range(400):
            route = tuple(rng.randrange(100) for _ in range(5))
            face_id, path = fam.address_of_route(route)
            assert 0 <= face_id < S.FACE_COUNT
            assert len(path) == S.PATH_DEPTH
            assert all(0 <= d < S.OCTAL_BASE for d in path)
            assert fam.route_of_address(face_id, path) == route


def test_map_route_produces_deterministic_cell_and_centroid():
    ico = build_partition().ico
    fam = S.FAMILIES[0]
    route = (1, 65, 87, 65, 23)
    a = fam.map_route(route, ico=ico)
    b = fam.map_route(route, ico=ico)
    assert a.face_id == b.face_id and a.path == b.path
    assert np.allclose(a.centroid, b.centroid)
    assert a.polygon.shape == (3, 3)
    assert np.isclose(np.linalg.norm(a.centroid), 1.0)
    assert a.depth == S.PATH_DEPTH


def test_families_generally_disagree():
    # The ensemble is a real ensemble: families map a route to different cells.
    ico = build_partition().ico
    route = (1, 65, 87, 65, 23)
    faces_paths = {(fam.map_route(route, ico=ico).face_id,
                    fam.map_route(route, ico=ico).path)
                   for fam in S.FAMILIES}
    assert len(faces_paths) >= 2  # at least two distinct spatializations


def test_planted_mappings_present_for_recovery_measurement():
    fam = S.FAMILIES[2]
    planted = S.planted_mappings(fam)
    assert len(planted) == len(S.PLANTED_ROUTES)
    for route, point in planted:
        assert len(route) == 5
        assert np.isclose(np.linalg.norm(point), 1.0)


def test_negative_malformed_route_refused():
    fam = S.FAMILIES[0]
    with pytest.raises(S.SpatializationError):
        fam.address_of_route((1, 2, 3))  # wrong token count
    with pytest.raises(S.SpatializationError):
        fam.address_of_route((1, 2, 3, 4, 100))  # token out of range
    with pytest.raises(S.SpatializationError):
        fam.address_of_route((1, 2, 3, 4, True))  # bool is not a token


def test_negative_unknown_family_refused():
    with pytest.raises(S.SpatializationError):
        S.get_family("F9_DOES_NOT_EXIST")


def test_report_seals_candidate_ceiling():
    r = S.spatialization_report()
    assert r["phase"] == "P15"
    assert r["family_count"] == 4
    assert r["uses_hash_or_catalogue"] is False
    assert r["evidence_class"] == "CALIBRATED_CANDIDATE"
    assert r["max_evidence"] == "CALIBRATED_CANDIDATE"
    assert r["measured_here"] == "nothing"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
