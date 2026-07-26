"""R10.8.4 mandatory tests — recursive interleaved XYZ hedron decoder."""

import math
from fractions import Fraction

import numpy as np
import pytest

from cwatlas.r1084 import cw_face_codebook as cb
from cwatlas.r1084 import cw_gravity_gradient as grav
from cwatlas.r1084 import cw_radial_refinement as radial
from cwatlas.r1084 import cw_surface_refinement as surf
from cwatlas.r1084 import cw_recursive_decoder as dec
from cwatlas.r1084 import cw_recursive_encoder as enc
from cwatlas.r1084.cw_hedron_state import (PhysicalMeshFaceID, SourceFaceID)
from cwatlas.r1084.cw_recursive_xyz import (
    CWPartialLevel, REJECTED_MODELS, parse_levels, reconstruct)

F = Fraction


# ---------------------------------------------------------------- parser
def test_exact_triplet_parsing_stonehenge():
    levels, partial = parse_levels("165876523")
    assert [lv.as_tuple() for lv in levels] == [(1, 6, 5), (8, 7, 6),
                                                (5, 2, 3)]
    assert partial is None


def test_exact_triplet_parsing_nearby():
    levels, _ = parse_levels("165877623")
    assert [lv.as_tuple() for lv in levels] == [(1, 6, 5), (8, 7, 7),
                                                (6, 2, 3)]


def test_orange_slice_recursive_paths():
    paths = {v: [lv.as_tuple() for lv in parse_levels(v)[0]]
             for v in ("165892743", "165892763", "165892783")}
    for p in paths.values():
        assert p[0] == (1, 6, 5) and p[1] == (8, 9, 2)
    l3 = [paths[v][2] for v in ("165892743", "165892763", "165892783")]
    assert [t[0] for t in l3] == [7, 7, 7]          # X fixed
    assert [t[1] for t in l3] == [4, 6, 8]          # Y progresses
    assert [t[2] for t in l3] == [3, 3, 3]          # Z fixed


def test_partial_final_levels_not_padded_not_rejected():
    levels, partial = parse_levels("16782953437")   # corrected vector
    assert [lv.as_tuple() for lv in levels] == [(1, 6, 7), (8, 2, 9),
                                                (5, 3, 4)]
    assert partial == CWPartialLevel(x_digit=3, y_digit=7)
    assert partial.axes_present == ("X", "Y")
    levels, partial = parse_levels("1678523973")
    assert partial == CWPartialLevel(x_digit=3)
    assert reconstruct(levels, partial) == "1678523973"


def test_rejected_models_registry():
    for name in ("FIVE_BASE100_TOKENS_FOLD_MOD20", "DIRECT_XYZ_TO_LATLON",
                 "COMPLETED_DECIMAL_FRACTIONS", "SHELL_FROM_FINAL_DIGIT",
                 "FIXED_NINE_DIGIT_MAX_LENGTH", "CONTIGUOUS_XYZ_BLOCKS"):
        assert name in REJECTED_MODELS
    # no direct-to-latlon or flattening API exists on the decoder module
    for banned in ("xyz_to_latlon", "flatten", "to_decimal_fractions",
                   "shell_from_last_digit"):
        assert not hasattr(dec, banned)


# ------------------------------------------------------------ containment
def test_surface_child_contains_and_folding():
    tri = surf.root_triangle()
    up, rec = surf.refine(tri, 1, 6)
    assert rec["kind"] == "UP" and up.orientation == +1
    assert tri.contains_triangle(up)
    down, rec2 = surf.refine(up, 7, 4)      # 7+4=11 -> DOWN, folded
    assert rec2["kind"] == "DOWN" and down.orientation == -1
    assert up.contains_triangle(down)
    assert tri.contains_triangle(down)


def test_all_100_digit_pairs_are_bijective_children():
    tri = surf.root_triangle()
    seen = set()
    for x in range(10):
        for y in range(10):
            child, rec = surf.refine(tri, x, y)
            assert tri.contains_triangle(child)
            seen.add((rec["kind"],) + tuple(rec["lattice"]))
    assert len(seen) == 100                  # bijection: no two pairs share


def test_radial_child_contained_and_no_last_digit_shell():
    st = radial.root_state()
    child, _ = radial.refine(st, 5)
    assert st.interval.contains_interval(child.interval)
    g, _ = radial.refine(child, 6)
    assert child.interval.contains_interval(g.interval)
    assert g.interval.thickness == st.interval.thickness / 100


def test_removing_final_digits_returns_parent_state():
    t_full = dec.decode("165876523", mesh_face=4)
    t_parent = dec.decode("165876", mesh_face=4)
    # parent's final region equals the level-2 state of the full decode
    lvl2_poly = t_full.levels[1]["surface_polygon_latlon"]
    assert t_parent.region.polygon_latlon == pytest.approx(
        [c for p in lvl2_poly for c in p]) or \
        t_parent.region.polygon_latlon == lvl2_poly


def test_adding_one_triplet_reduces_uncertainty():
    a = dec.decode("165876", mesh_face=4).region.uncertainty
    b = dec.decode("165876523", mesh_face=4).region.uncertainty
    assert b.surface_max_radius_km < a.surface_max_radius_km / 5
    assert b.radial_thickness_km == pytest.approx(
        a.radial_thickness_km / 10)


# --------------------------------------------------------------- geometry
def test_codebooks_bijective_and_typed_faces_distinct():
    books = cb.build_codebooks(4, np.array([1.0, 0.0, 0.0]))
    assert set(books) == set(cb.CODEBOOK_IDS)
    for order in books.values():
        assert sorted(order) == list(range(20))
    assert SourceFaceID(17) != PhysicalMeshFaceID(17)
    with pytest.raises(ValueError):
        SourceFaceID(20)


def test_encoder_round_trip_known_point():
    # encode a point, decode it back, point must lie in the decoded cell
    lat, lon, r = -20.0, 140.0, 6371.0
    for face in range(20):
        try:
            raw = enc.encode_point(lat, lon, r, mesh_face=face, levels=3)
        except ValueError:
            continue
        t = dec.decode(raw, mesh_face=face)
        verts = dec.face_vertices_earth(face, (0, 1, 2), np.eye(3))
        u, v = dec.point_chart_coords(verts, enc._latlon_unit(lat, lon))
        assert t.region.surface.contains(u, v)
        assert t.region.radial.interval.contains_radius(r)
        return
    raise AssertionError("no face contained the test point")


# ---------------------------------------------------------------- gravity
def test_gravity_baseline_and_gradient():
    g0 = grav.g_of_r(6371.0)
    assert g0 == pytest.approx(9.82, abs=0.02)          # m/s^2
    row = grav.shell_row("S", 6371.0, 7645.2)
    exact = row["abs_gravity_change_m_s2"]
    approx = row["gravity_change_midpoint_approx_m_s2"]
    assert exact > 0 and abs(exact - approx) / exact < 0.02
    assert row["radial_gradient_mid_s2"] < 0            # decreases outward
    assert row["fractional_gravity_change"] == pytest.approx(
        exact / row["g_midpoint_m_s2"])


def test_gravity_dimensional_consistency():
    # dg ~ 2 g dr / r first order
    r, dr = 7000.0, 7.0
    row = grav.shell_row("S", r, r + dr)
    expect = 2 * grav.g_of_r(r + dr / 2) * (dr / (r + dr / 2))
    assert row["abs_gravity_change_m_s2"] == pytest.approx(expect,
                                                           rel=1e-3)


# ----------------------------------------------------------- known vectors
def test_stonehenge_trace_structure():
    t = dec.decode("165876523", mesh_face=4)
    assert len(t.levels) == 3
    assert t.levels[0]["instruction"] == (1, 6, 5)
    assert t.levels[2]["instruction"] == (5, 2, 3)
    assert t.region.uncertainty.axis_depths == (3, 3, 3)
    d1 = t.levels[0]["surface_diameter_km"]
    d3 = t.levels[2]["surface_diameter_km"]
    assert d3 == pytest.approx(d1 / 100, rel=0.05)      # 10x per level


def test_orange_slice_level3_cells_share_prefix_cell():
    traces = {v: dec.decode(v, mesh_face=4)
              for v in ("165892743", "165892763", "165892783")}
    lvl2 = {tuple(map(tuple, t.levels[1]["surface_polygon_latlon"]))
            for t in traces.values()}
    assert len(lvl2) == 1        # identical first two refinement levels
    r3 = {t.levels[2]["radial"]["interval_km"] for t in traces.values()}
    assert len(r3) == 1          # identical radial intervals at level 3
    kinds = [t.levels[2]["surface"]["kind"] for t in traces.values()]
    assert kinds == ["DOWN", "DOWN", "DOWN"]  # 7+4,7+6,7+8 all fold


def test_variable_length_vector_preserved_exactly():
    t = dec.decode("16782953437", mesh_face=4)
    assert t.raw == "16782953437"
    assert t.region.uncertainty.axis_depths == (4, 4, 3)
    assert t.region.uncertainty.partial_level_axes == ("X", "Y")
    assert "no Z digit" in t.levels[-1]["radial"]["note"]


def test_compensation_profiles_preserve_containment():
    for prof in dec.COMPENSATION_PROFILES:
        t = dec.decode("165876523", mesh_face=4, compensation=prof)
        assert t.region is not None   # decode() asserts containment inline
