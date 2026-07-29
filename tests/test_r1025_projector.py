"""R10.25 — Earth projector recovery. Tests pin the NEGATIVE result.

A negative result needs tests as much as a positive one: the ways this
run could have produced a false recovery are exactly the things that
must stay refused.
"""

import math

import pytest

from r1016.quarantine import QuarantineError
from r1025 import authority, hedra, nodes
from r1025.projector import HARD_ANCHORS, evaluate, Candidate, fields
from r1025.search import _p_map_ok, eligible_hedra


# --- hedron families -------------------------------------------------

def test_every_family_tiles_the_sphere_exactly():
    for name, h in hedra.families().items():
        if h.root != "face_centre":
            continue
        tot = 0.0
        for f in range(h.face_count):
            tri = [v / (v @ v) ** 0.5 for v in h.face_triangle(f)]

            def ang(u, v, w):
                import numpy as np
                n1, n2 = np.cross(u, v), np.cross(u, w)
                c = n1 @ n2 / ((n1 @ n1) ** 0.5 * (n2 @ n2) ** 0.5)
                return math.acos(max(-1.0, min(1.0, c)))
            a, b, c = tri
            tot += ang(a, b, c) + ang(b, c, a) + ang(c, a, b) - math.pi
        assert abs(tot - 4 * math.pi) < 1e-6, name


def test_families_too_large_or_too_small_are_rejected_on_arithmetic():
    keep, rejected = eligible_hedra()
    names = {r["hedron_family"] for r in rejected}
    assert any("DODECAHEDRON" in n for n in names)   # 60 > 32 = 2**5
    assert any("TETRAHEDRON" in n for n in names)    # 4 cannot index F5=5
    assert all(4 < hedra.families()[k].face_count <= 32 for k in keep)


# --- the honesty budget ----------------------------------------------

def test_false_hit_probability_matches_closed_form():
    assert _p_map_ok(1, 4) == 1.0
    assert abs(_p_map_ok(2, 4) - 0.625) < 1e-12       # 1/16 + 9/16
    assert abs(_p_map_ok(3, 4) - 0.25) < 1e-9
    assert _p_map_ok(24, 4) < 1e-13


def test_per_level_is_weaker_than_uniform_at_every_depth():
    """PER_LEVEL gives each level a free map from only 3 pairs, so it
    cannot be reported alongside UNIFORM as if they were comparable."""
    for depth in (2, 3, 6):
        uniform = _p_map_ok(3 * depth, 4)
        per_level = _p_map_ok(3, 4) ** depth
        assert per_level > uniform


def test_depth_six_is_required_to_separate_erie_and_toronto():
    ico = hedra.families()["ICOSAHEDRON_20_FACE_CENTRE"]
    erie = next(a for a in HARD_ANCHORS if a.name == "ERIE")
    tor = next(a for a in HARD_ANCHORS if a.name == "TORONTO")
    la1, lo1, la2, lo2 = map(math.radians,
                             (erie.lat, erie.lon, tor.lat, tor.lon))
    sep = 6371.0 * 2 * math.asin(math.sqrt(
        math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2)
        * math.sin((lo2 - lo1) / 2) ** 2))
    assert 175 < sep < 182
    assert erie.f5 == tor.f5          # same root face
    assert ico.cell_edge_km(5) > sep  # level 5 too coarse
    assert ico.cell_edge_km(6) < sep  # level 6 is the first that resolves


# --- what must stay refused ------------------------------------------

def test_projector_refuses_quarantined_vectors():
    from r1025.projector import Anchor
    bad = Anchor("MONTREAL", 165879243, 45.5, -73.5)
    ico = hedra.families()["ICOSAHEDRON_20_FACE_CENTRE"]
    import numpy as np
    cand = Candidate("ICOSAHEDRON_20_FACE_CENTRE", "IDENTITY", "right",
                     "south_up", 0, 4, "UNIFORM")
    with pytest.raises(QuarantineError):
        evaluate(cand, ico, np.eye(3), (bad,), 2)


def test_place_name_buckets_are_refused():
    with pytest.raises(ValueError, match="INVALID RUN"):
        authority.assert_no_place_name_scoring(["NW_PENNSYLVANIA_LAKE_ERIE"])
    assert authority.signature_class("NW_PENNSYLVANIA_LAKE_ERIE") == \
        "F5_5_SHARED_ROOT_PREFIX_CLASS"


def test_lunar_holdout_stays_unbucketed():
    assert "167854923" in authority.UNBUCKETED


def test_anchor_result_is_not_reported_as_geometrically_tested():
    assert authority.ANCHOR_RESULT_STATUS == \
        "SELF_CONSISTENT_NOT_GEOMETRICALLY_TESTED"
    assert len({a.f5 for a in HARD_ANCHORS}) == 2   # why it cannot corroborate


# --- Agent 01 --------------------------------------------------------

def test_compression_nodes_are_stress_antinodes():
    L = 100.0
    for n in (1, 2, 3, 5):
        for x in nodes.compression_nodes_mm(L, n):
            # displacement cos(n pi x/L) == 0 exactly at these points
            assert abs(math.cos(n * math.pi * x / L)) < 1e-12
            # strain sin(n pi x/L) is at its extremum
            assert abs(abs(math.sin(n * math.pi * x / L)) - 1.0) < 1e-12


def test_scale_a_fundamental_node_is_mid_length():
    exact = nodes.compression_nodes_mm(nodes.SCALE_A_LENGTH_MM, 1)[0]
    assert exact == nodes.SCALE_A_LENGTH_MM / 2
    # the report rounds to 4 dp for presentation only
    r = nodes.scale_a_report()
    assert abs(r["rows"][0]["recommended_mount_mm"] - exact) < 5e-5


def test_scale_a_half_wave_speed_reproduces_the_r1015a_shear_speed():
    """Independent arithmetic cross-check: 2*L*f must equal 3800 m/s."""
    assert abs(nodes.half_wave_speed_m_s(
        nodes.SCALE_A_LENGTH_MM, nodes.SCALE_A_SHEAR_HZ) - 3800.0) < 1e-9


def test_phase_conjugation_node_is_not_claimed_as_solved():
    r = nodes.scale_a_report()
    assert r["phase_conjugation_node"].startswith("NOT_SOLVED")
    assert r["not_a_measurement"] is True
