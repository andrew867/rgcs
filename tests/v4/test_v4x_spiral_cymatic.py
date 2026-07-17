"""G01/G02: spiral-cone + cymatic disk tests (gates G16-G19)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs2_core import cymatic_disk as cd, spiral_cone as sc


# --- spiral mathematics (gate G16) -----------------------------------------

def test_curvature_invariant_exact_vs_numeric():
    """S005: kappa * r = 1/sqrt(1+a^2), numerically verified."""
    for a in (0.1, 0.2, 0.35):
        th = np.linspace(0.5, 6 * math.pi, 8000)
        kr = sc.numeric_curvature_times_r(50.0, a, th)
        want = sc.curvature_invariant(a)
        assert np.allclose(kr[100:-100], want, rtol=1e-4), a


def test_focus_eigenvalues_and_scale_ratios():
    """S004: eigenvalues exactly -a +/- i; S006: per-turn ratios for
    phi, 2, e, 8 recovered by a_for_ratio."""
    for a in (0.05, 0.3):
        ev = sc.focus_eigenvalues(a)
        assert ev[0] == pytest.approx(-a - 1j, abs=1e-12)
        assert ev[1] == pytest.approx(-a + 1j, abs=1e-12)
    for ratio in ((1 + math.sqrt(5)) / 2, 2.0, math.e, 8.0):
        a = sc.a_for_ratio(ratio)
        assert 1.0 / sc.per_turn_ratio(a) == pytest.approx(
            ratio, rel=1e-12)
    with pytest.raises(ValueError):
        sc.a_for_ratio(0.5)


def test_spiral_cone_path_and_pinched_variant():
    """S003 + gate G17: plain and pinched-twisted variants."""
    plain = sc.spiral_cone_path(40.0, 0.15, 80.0, 1.5, 5.0)
    assert plain[0, 2] == pytest.approx(0.0, abs=1e-9)
    assert plain[-1, 2] < 80.0 and plain[-1, 2] > 60.0
    r = np.hypot(plain[:, 0], plain[:, 1])
    assert r[0] > r[-1] > 0                        # contracting
    pinched = sc.spiral_cone_path(40.0, 0.15, 80.0, 1.5, 5.0,
                                  twist_pinch=0.6)
    assert not np.allclose(plain, pinched)         # variant distinct
    rp = np.hypot(pinched[:, 0], pinched[:, 1])
    assert rp[-1] < r[-1]                          # pinched tighter


def test_wavelength_surface_and_one_pointed_translation():
    """S002 + S007."""
    lam = sc.wavelength_surface(np.array([343.0, 3430.0]))
    assert lam[0] == pytest.approx(1000.0)         # 1 m at 343 Hz
    assert lam[1] == pytest.approx(100.0)
    with pytest.raises(ValueError):
        sc.wavelength_surface(np.array([0.0]))
    t = np.linspace(0, 60, 4000)
    w = sc.one_pointed_spinning_waveform(0.2, t)
    assert w["converges_to_origin"]


def test_uniform_field_metric_equals_arclength_fraction():
    """S008 acceptance control (V4X-D-005).

    The justification for the arc-length weighting is NOT that it makes
    the >5x test pass. It is that a UNIFORM field's concentration must
    equal the fraction of ARC LENGTH inside the inner radius -- an
    independent analytic target the metric cannot fit to.

    The original unweighted metric failed this badly: it reported 0.695
    for a uniform field because 69.5% of the theta-uniform SAMPLES fall
    in the inner 10% radius, while only 9.3% of the arc length does. It
    was measuring the sampling grid."""
    path = sc.spiral_cone_path(40.0, 0.2, 80.0, 1.5, 6.0)
    r = np.hypot(path[:, 0], path[:, 1])
    inner = r <= 0.1 * r.max()
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    ds = np.zeros(len(path))
    ds[:-1] += 0.5 * seg
    ds[1:] += 0.5 * seg
    arclen_fraction = ds[inner].sum() / ds.sum()
    got = sc.cusp_response_metric(path, np.ones_like(r))
    assert got == pytest.approx(arclen_fraction, rel=1e-9)
    # and the sampling density is genuinely misleading: this is the
    # trap the weighting exists to avoid
    assert inner.mean() > 6 * arclen_fraction


def test_cusp_overlap_and_merit():
    """S008/S009/S010."""
    path = sc.spiral_cone_path(40.0, 0.2, 80.0, 1.5, 6.0)
    r = np.hypot(path[:, 0], path[:, 1])
    concentrated = np.exp(-r / 2.0)
    uniform = np.ones_like(r)
    # direction of effect against a matched control on the same path
    assert sc.cusp_response_metric(path, concentrated) > \
        5 * sc.cusp_response_metric(path, uniform)
    # ...and the magnitude is FINITE: a singularity would diverge
    ratio = sc.cusp_response_metric(path, concentrated) \
        / sc.cusp_response_metric(path, uniform)
    assert 5.0 < ratio < 100.0, "finite focusing, not a singularity"
    assert sc.mode_overlap(uniform, uniform) == pytest.approx(1.0)
    assert abs(sc.mode_overlap(np.sin(r), np.cos(r))) < 0.9
    merit = sc.geometry_merit(0.3, 0.8, 100.0)
    assert merit["classification"] == "ENGINEERING_PROTOTYPE"
    assert "no physical significance" in merit["note"]


def test_fabrication_exports_wellformed():
    """S011/S024 + control S019."""
    scad = sc.openscad_text(40.0, 0.15, 80.0, 1.5, 5.0,
                            twist_pinch=0.5)
    assert "linear_extrude" in scad and "polygon" in scad
    assert "pinch = 0.5" in scad
    spiral = sc.log_spiral(40.0, 0.15, np.linspace(0, 10 * np.pi,
                                                   400))
    dxf = sc.dxf_polyline_text(spiral)
    assert dxf.startswith("0\nSECTION") and dxf.rstrip().endswith(
        "EOF")
    stl = sc.stl_text_from_path(
        sc.spiral_cone_path(40.0, 0.15, 80.0, 1.5, 3.0, n=50))
    assert stl.startswith("solid") and "facet normal" in stl
    arch = sc.archimedean_control(40.0, 5.0)
    assert np.hypot(*arch[-1]).item() < 1e-9      # ends at centre


# --- cymatic disk (gates G18/G19) --------------------------------------------

def test_clamped_plate_lambda_anchor():
    """Literature anchor: lambda_01 = 3.1962 (clamped circular
    plate); ordering of higher roots."""
    l01 = cd.clamped_plate_lambdas(0, 1)[0]
    assert l01 == pytest.approx(3.1962, abs=2e-3)
    l11 = cd.clamped_plate_lambdas(1, 1)[0]
    assert l11 == pytest.approx(4.6109, abs=5e-3)
    l0 = cd.clamped_plate_lambdas(0, 3)
    assert l0[0] < l0[1] < l0[2]


def test_copper_loading_shifts_frequency():
    bare = cd.composite_plate(0.05, 1.6e-3)
    loaded = cd.composite_plate(0.05, 1.6e-3, 35e-6, 1.0)
    f_bare = cd.plate_mode_hz(bare, 0, 1)
    f_load = cd.plate_mode_hz(loaded, 0, 1)
    assert f_bare > 0 and f_load != f_bare
    with pytest.raises(ValueError):
        cd.composite_plate(0.05, 1.6e-3, 35e-6, 1.5)


def test_chladni_pattern_nodal_structure():
    plate = cd.composite_plate(0.05, 1.6e-3)
    pat = cd.chladni_pattern(plate, 2, 1)
    # n=2: four azimuthal sign changes -> nodal diameters exist
    assert pat["nodal_mask"].any()
    W = pat["w"]
    assert np.nanmax(W) > 0 > np.nanmin(W)


def test_structural_vs_electrical_separation():
    """Gate G19."""
    rep = cd.resonance_separation_report()
    assert rep["structural_f01_hz"] < 20e3          # kHz family
    assert rep["electrical_f_lc_hz"] > 1e6          # MHz family
    assert rep["separated"]
    assert "DISTINCT families" in rep["note"]


def test_design_for_target_and_exports():
    """S023 + S024 + G18-adjacent wellformedness."""
    d = cd.design_for_target(4096.0)
    assert d["achieved_hz"] == pytest.approx(4096.0, rel=1e-6)
    g = cd.gerber_spiral_text(10, 90.0, 20.0)
    assert g.startswith("%FSLAX46Y46*%") and g.rstrip().endswith(
        "M02*")
    assert "D02*" in g and "D01*" in g
    drl = cd.drill_text([(0.0, 0.0), (10.0, 0.0)])
    assert drl.startswith("M48") and "M30" in drl
    assert len(cd.bom()) >= 5
    ctrl = cd.control_set(0.05)
    assert {c["id"] for c in ctrl} == {"S016", "S017", "S018",
                                       "S019", "S020", "S021"}
