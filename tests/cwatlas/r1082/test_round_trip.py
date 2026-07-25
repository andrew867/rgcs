"""P23 — profile-specific round trip and nearest-encodable point.

Covers: canonical exact route<->point<->route identity per family; the
source-style calibrated round trip separated from the canonical one; arbitrary
points return the nearest encodable point with an explicit quantization error
(no false exactness); pole / dateline / cell-boundary / shell / epoch cases;
the shell supplies the radius (altitude never missing); determinism.
"""

from __future__ import annotations

import math
import random

import numpy as np
import pytest

from cwatlas.icosahedron import build_icosahedron
from cwatlas.r1082 import geocode_forward as G
from cwatlas.r1082 import local_coord as L
from cwatlas.r1082 import round_trip as RT
from cwatlas.r1082 import spatialization as S
from cwatlas.r1082.claims import R1082ClaimError


@pytest.fixture(scope="module")
def ico():
    return build_icosahedron()


# -- canonical exact round trip (codec identity) ----------------------------

def test_canonical_exact_round_trip_per_family(ico):
    rng = random.Random(20260725)
    for fam in S.FAMILIES:
        for _ in range(60):
            route = tuple(rng.randrange(100) for _ in range(5))
            rt = RT.canonical_exact_round_trip(route, fam, ico=ico)
            assert rt.matches() is True
            assert rt.exact is True
            assert rt.quantization_error <= RT.EXACT_TOL
            assert rt.result_type == "CANONICAL_EXACT_POINT"


# -- source-style calibrated round trip, separated from canonical -----------

def test_source_style_round_trip_is_calibrated_not_canonical(ico):
    sf = G.single_family_stub("F1_CANONICAL_DIRECT_BE")
    for shell in (0, 3, 6, 8):
        rt = RT.source_style_round_trip(
            (1, 65, 87, 65, 23), "F1_CANONICAL_DIRECT_BE", sf, shell=shell,
            ico=ico)
        assert rt.matches() is True                     # orthonormal preserves cell
        assert rt.result_type == "CANDIDATE_CALIBRATED_POINT"
        assert rt.kind == "SOURCE_STYLE_CALIBRATED"
        assert rt.shell == shell
        assert rt.radius_m is not None


# -- arbitrary points: nearest encodable, no false exactness ----------------

def test_arbitrary_points_nearest_encodable(ico):
    sf = G.single_family_stub()
    rng = random.Random(99)
    for _ in range(80):
        lat = rng.uniform(-89.0, 89.0)
        lon = rng.uniform(-179.0, 179.0)
        ne = RT.nearest_encodable_point(lat, lon, "F1_CANONICAL_DIRECT_BE", sf,
                                        shell=3, ico=ico)
        assert len(ne.route) == 5
        assert ne.quantization_error >= 0.0
        # If not exact, exactness must NOT be claimed.
        if ne.quantization_error > RT.EXACT_TOL:
            assert ne.exact is False


def test_pole_and_dateline(ico):
    sf = G.single_family_stub()
    for lat, lon in [(89.9, 0.0), (-89.9, 0.0), (0.0, 180.0), (0.0, -180.0),
                     (45.0, 179.999)]:
        ne = RT.nearest_encodable_point(lat, lon, "F1_CANONICAL_DIRECT_BE", sf,
                                        shell=3, ico=ico)
        assert len(ne.route) == 5
        assert math.isfinite(ne.quantization_error)
        assert -90.0 <= ne.nearest_latitude_deg <= 90.0


def test_cell_boundary_returns_interval_not_false_exact(ico):
    # A point on a terminal-cell vertex is reported as a boundary interval
    # (a region), not a crisp false-exact point.
    fam = S.FAMILIES[0]
    route = (7, 7, 7, 7, 7)
    centroid = L.forward(route, fam, ico=ico)
    from cwatlas.addressing import encode_path
    from cwatlas.localize import localize_cell
    addr = encode_path(ico, centroid, L.PATH_DEPTH)
    corner = localize_cell(ico, addr.face_id, addr.path).cell.a
    lat, lon = G.unit_to_geocentric_latlon(corner)
    ne = RT.nearest_encodable_point(lat, lon, fam, None, shell=3, ico=ico)
    assert ne.on_edge is True
    assert ne.interval is not None


# -- shell supplies the radius; altitude never missing ----------------------

@pytest.mark.parametrize("shell", range(0, 9))
def test_shell_supplies_radius(shell):
    r = RT.assert_shell_supplies_radius(shell)
    assert r is not None


def test_refuse_altitude_missing_when_shell_present():
    with pytest.raises(R1082ClaimError):
        RT.refuse_altitude_missing(3)


# -- determinism ------------------------------------------------------------

def test_determinism(ico):
    sf = G.single_family_stub()
    a = RT.nearest_encodable_point(12.3, 45.6, "F1_CANONICAL_DIRECT_BE", sf,
                                   shell=3, ico=ico)
    b = RT.nearest_encodable_point(12.3, 45.6, "F1_CANONICAL_DIRECT_BE", sf,
                                   shell=3, ico=ico)
    assert a.route == b.route
    assert a.quantization_error == b.quantization_error
    assert a.nearest_latitude_deg == b.nearest_latitude_deg


def test_report_seals_claims():
    r = RT.round_trip_report()
    assert r["phase_id"] == "P23"
    assert r["tranche"] == "T06"
    assert r["canonical_exact_vs_calibrated_separated"] is True
    assert r["nearest_encodable_when_quantized"] is True
    assert r["region_near_boundary_not_false_exact"] is True
    assert r["shell_supplies_radius"] is True
    assert r["altitude_missing_when_shell_present"] == "REFUSED"
    assert r["measured_here"] == "nothing"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
