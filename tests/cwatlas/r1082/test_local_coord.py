"""P16 — barycentric local coordinate and profile-specific inverse."""

from __future__ import annotations

import random

import numpy as np
import pytest

from cwatlas.r1082 import local_coord as L
from cwatlas.r1082 import spatialization as S
from cwatlas.r1082.partition import build_partition


def _ico():
    return build_partition().ico


def test_route_point_route_round_trip_per_family():
    # POWER: for every family, forward then inverse recovers the exact route
    # and the nearest encodable point IS the forward point (exact).
    ico = _ico()
    rng = random.Random(4242)
    for fam in S.FAMILIES:
        for _ in range(150):
            route = tuple(rng.randrange(100) for _ in range(5))
            point = L.forward(route, fam, ico=ico)
            inv = L.inverse(point, fam, ico=ico)
            assert inv.route == route
            assert inv.exact is True
            assert inv.residual <= L._EXACT_TOL
            assert np.allclose(inv.nearest_point, point)


def test_inverse_accepts_family_by_name():
    ico = _ico()
    route = (1, 65, 87, 65, 23)
    point = L.forward(route, "F1_CANONICAL_DIRECT_BE", ico=ico)
    inv = L.inverse(point, "F1_CANONICAL_DIRECT_BE", ico=ico)
    assert inv.route == route
    assert inv.family_name == "F1_CANONICAL_DIRECT_BE"
    assert inv.result_class == "CANDIDATE_CALIBRATED_POINT"


def test_planted_recovery_power():
    # Recovery power: every planted (route, point) inverts to its route.
    ico = _ico()
    for fam in S.FAMILIES:
        recovered = 0
        planted = S.planted_mappings(fam, ico=ico)
        for route, point in planted:
            inv = L.inverse(point, fam, ico=ico)
            if inv.route == route and inv.exact:
                recovered += 1
        assert recovered == len(planted)


def test_negative_exactness_not_claimed_where_quantized():
    # A point that is NOT an encodable centroid must not be reported exact; the
    # inverse returns the nearest encodable point instead of inventing one.
    ico = _ico()
    fam = S.FAMILIES[0]
    route = (12, 34, 56, 78, 90)
    point = L.forward(route, fam, ico=ico)
    perturbed = point + np.array([2e-3, -1e-3, 0.0])
    perturbed = perturbed / np.linalg.norm(perturbed)
    inv = L.inverse(perturbed, fam, ico=ico)
    assert inv.exact is False               # exactness NOT claimed
    assert inv.residual > L._EXACT_TOL
    # The reported point is a real encodable centroid (round-trips exactly).
    back = L.inverse(inv.nearest_point, fam, ico=ico)
    assert back.route == inv.route and back.exact is True


def test_local_barycentric_interior_and_boundary():
    ico = _ico()
    # An interior route centroid is interior (no boundary interval).
    route = (7, 7, 7, 7, 7)
    point = L.forward(route, S.FAMILIES[0], ico=ico)
    lc = L.local_barycentric(point, ico=ico)
    assert abs(sum(lc.bary) - 1.0) < 1e-9
    # A point placed on a cell vertex reports a boundary interval (region, not
    # invented precision).
    from cwatlas.addressing import encode_path
    from cwatlas.localize import localize_cell
    addr = encode_path(ico, point, L.PATH_DEPTH)
    corner = localize_cell(ico, addr.face_id, addr.path).cell.a
    lc_edge = L.local_barycentric(corner, ico=ico)
    assert lc_edge.on_edge is True
    assert lc_edge.interval is not None


def test_determinism():
    ico = _ico()
    route = (50, 0, 50, 0, 50)
    fam = S.FAMILIES[3]
    p1 = L.forward(route, fam, ico=ico)
    p2 = L.forward(route, fam, ico=ico)
    assert np.array_equal(p1, p2)
    i1 = L.inverse(p1, fam, ico=ico)
    i2 = L.inverse(p2, fam, ico=ico)
    assert i1.route == i2.route
    assert i1.face_id == i2.face_id and i1.path == i2.path
    assert i1.exact == i2.exact and i1.residual == i2.residual
    assert np.array_equal(i1.nearest_point, i2.nearest_point)


def test_report_seals_claims():
    r = L.local_coord_report()
    assert r["phase"] == "P16"
    assert r["local_coordinate"] == "BARYCENTRIC"
    assert r["nearest_encodable_when_quantized"] is True
    assert r["evidence_class"] == "CALIBRATED_CANDIDATE"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
