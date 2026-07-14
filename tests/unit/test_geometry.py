"""Unit tests: rgcs_core.geometry (RGCS-M.1..M.7, M.30..M.41)."""

from __future__ import annotations

import math

import pytest

from rgcs_core.geometry import (CrystalGeometry, polygon_area_mm2,
                                apothem_mm, termination_height_mm,
                                crystal_geometry,
                                solve_diameter_scale_for_mass,
                                SpiralGeometry, spiral_pitch_parameter,
                                spiral_curve, spiral_path_length_3d_mm,
                                spiral_metrics, metric_center_mm,
                                node_prior_mm, female_to_male_frame_mm,
                                node_positions, node_alignment_factor,
                                angle_audit)

G5 = CrystalGeometry(length_mm=154.052734375, wide_diameter_mm=31.6,
                     narrow_diameter_mm=26.9)


def test_polygon_area_hexagon_across_vertices():
    # Regular hexagon across vertices D: A = (6/8) D^2 sin(60 deg).
    a = polygon_area_mm2(2.0, 6)
    assert a == pytest.approx(0.75 * 4.0 * math.sin(math.pi / 3))


def test_polygon_area_modes_consistent():
    # across_flats D equals across_vertices D * cos(pi/N).
    d_v = 10.0
    for n in (3, 5, 6, 8, 12):
        d_f = d_v * math.cos(math.pi / n)
        assert polygon_area_mm2(d_v, n, "across_vertices") == pytest.approx(
            polygon_area_mm2(d_f, n, "across_flats"), rel=1e-12)


def test_apothem_across_flats_is_half_diameter():
    assert apothem_mm(10.0, 6, "across_flats") == 5.0


def test_termination_height_conventions():
    r = 10.0
    assert termination_height_mm(r, 45.0, "face_slope") == pytest.approx(r)
    assert termination_height_mm(r, 45.0, "axis_to_face") == pytest.approx(r)
    assert termination_height_mm(r, 90.0, "apex_included") == pytest.approx(r)


def test_crystal_geometry_summary_consistent():
    out = crystal_geometry(G5)
    assert out["shaft_length_mm"] == pytest.approx(
        G5.length_mm - out["female_height_mm"] - out["male_height_mm"])
    assert out["mass_g"] == pytest.approx(out["volume_cm3"] * 2.65)
    assert out["metric_center_mm"] == pytest.approx(G5.length_mm / 2)
    # Node prior is the shaft midpoint (RGCS-M.39).
    expected = (G5.length_mm + out["female_height_mm"]
                - out["male_height_mm"]) / 2.0
    assert out["node_prior_female_frame_mm"] == pytest.approx(expected)
    # The deleted estimator must not resurface (D-01).
    assert "geometry_balance_node_mm" not in out


def test_density_inverse_round_trip():
    scaled = G5.model_copy(update={
        "wide_diameter_mm": G5.wide_diameter_mm * 1.1,
        "narrow_diameter_mm": G5.narrow_diameter_mm * 1.1})
    target_mass = crystal_geometry(scaled)["mass_g"]
    sol = solve_diameter_scale_for_mass(G5, target_mass)
    assert sol["diameter_scale"] == pytest.approx(1.1, rel=1e-6)
    assert sol["predicted_mass_g"] == pytest.approx(target_mass, rel=1e-9)


def test_spiral_pitch_and_curve():
    assert spiral_pitch_parameter(math.e) == pytest.approx(1 / (2 * math.pi))
    g = SpiralGeometry()
    c = spiral_curve(g, samples=256)
    assert c["r"][0] == pytest.approx(g.outer_radius_mm)
    # After T turns the radius contracts by q^-T.
    assert c["r"][-1] == pytest.approx(
        g.outer_radius_mm * g.q_per_turn ** (-g.turns), rel=1e-9)
    assert c["z"][0] == pytest.approx(0.0)
    assert (c["chi"] >= 0).all() and (c["chi"] < 2 * math.pi).all()


def test_spiral_3d_length_converges_and_exceeds_planar():
    g = SpiralGeometry()
    m = spiral_metrics(g)
    conv = spiral_path_length_3d_mm(g)
    assert conv["converged"]
    assert m["path_length_3d_mm"] == pytest.approx(conv["length_mm"],
                                                   rel=1e-5)
    # 3D length must exceed the planar length (there is a climb).
    assert m["path_length_3d_mm"] > m["planar_arc_length_mm"]
    # Per-turn lengths contract roughly like 1/q per turn (RGCS-M.37).
    per = m["per_turn_length_mm"]
    assert len(per) == int(g.turns)
    for k in range(len(per) - 1):
        assert per[k + 1] < per[k]
    assert sum(per) == pytest.approx(m["path_length_3d_mm"], rel=1e-3)
    # Prior definitions.
    assert m["compact_radius_prior_mm"] == pytest.approx(
        m["path_length_3d_mm"] / (2 * math.pi * g.turns))


def test_spiral_retired_closed_form_is_labeled_with_error():
    m = spiral_metrics(SpiralGeometry())
    assert "retired_closed_form_rel_error" in m
    assert abs(m["retired_closed_form_rel_error"]) < 0.05


def test_node_frames_and_precedence():
    L, hf, hm = 154.052734, 17.415434, 14.812763
    xg = node_prior_mm(L, hf, hm)
    assert female_to_male_frame_mm(xg, L) == pytest.approx(L - xg)
    out = node_positions(L, hf, hm)
    assert out["selected_source"] == "geometry_prior"
    assert out["measured_node_mm"] is None
    out2 = node_positions(L, hf, hm, measured_from_female_mm=80.0)
    assert out2["selected_node_mm"] == 80.0
    assert out2["selected_source"] == "measured"
    assert out["metric_center_mm"] == pytest.approx(metric_center_mm(L))


def test_node_alignment_factor():
    r = node_alignment_factor(80.0, 78.0, 2.0)
    assert r["xi"] == pytest.approx(1.0)
    assert r["node_alignment_factor"] == pytest.approx(math.exp(-1.0))


def test_angle_audit_no_golden_ratio_equality():
    out = angle_audit()
    # The mismatch is quantified and nonzero (RG-16).
    assert out["delta_atan_sqrt_phi_deg"] != 0.0
    assert abs(out["delta_atan_sqrt_phi_deg"]) == pytest.approx(0.015708,
                                                                abs=1e-5)
