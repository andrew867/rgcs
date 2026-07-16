"""Agent M3: torsion / curves / circulation / optical AM / chiral
phonon tests (gates D1-D7)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs2_core import (chiral_phonon as cp, circulation as circ,
                        curves, fem, optical_am as oam,
                        torsion_mech as tm)
from rscs2_core.quantity_registry import (IdentityError, QUANTITIES,
                                          assert_identity,
                                          compare_geometric,
                                          get_quantity, has_solver)


# --- registry (gate D1) -------------------------------------------------

def test_twelve_distinct_quantities_with_metadata():
    assert len(QUANTITIES) == 12
    for q in QUANTITIES.values():
        assert q.si_units and q.dimensions
        assert q.state_block
        assert q.classification_ceiling
        assert q.forbidden_aliases


def test_identity_forbidden_but_geometric_comparison_allowed():
    with pytest.raises(IdentityError, match="forbidden"):
        assert_identity("angular_momentum.optical.orbital",
                        "circulation.mechanical.displacement")
    with pytest.raises(IdentityError, match="forbidden"):
        assert_identity("toroidal_moment.magnetic",
                        "torsion.historical.spacetime_claim")
    rec = compare_geometric("angular_momentum.optical.orbital",
                            "circulation.mechanical.displacement")
    assert rec["kind"] == "GEOMETRIC_COMPARISON_ONLY"
    assert rec["physical_identity"] is False


def test_forbidden_aliases_and_no_historical_solver():
    q = get_quantity("torsion.mechanical.twist_rate")
    with pytest.raises(IdentityError, match="alias"):
        q.check_alias("spacetime twist rate")
    hist = get_quantity("torsion.historical.spacetime_claim")
    assert hist.classification_ceiling == "SOURCE_HYPOTHESIS"
    assert not has_solver("torsion.historical.spacetime_claim")
    assert has_solver("torsion.mechanical.twist_rate")


# --- curves (gate D3) ----------------------------------------------------

def test_helix_curvature_and_torsion_exact():
    R, pitch = 0.02, 0.01
    pts = curves.helix(R, pitch, turns=4, n=4001)
    fr = curves.frenet_frames(pts)
    want = curves.helix_exact(R, pitch)
    mid = slice(200, -200)          # away from finite-diff ends
    assert np.allclose(fr["curvature_per_m"][mid],
                       want["curvature_per_m"], rtol=1e-3)
    assert np.allclose(fr["torsion_per_m"][mid],
                       want["torsion_per_m"], rtol=1e-3)
    # left-handed helix flips torsion sign only
    fr2 = curves.frenet_frames(curves.helix(R, pitch, 4, 4001,
                                            handedness=-1))
    assert np.allclose(fr2["torsion_per_m"][mid],
                       -want["torsion_per_m"], rtol=1e-3)
    assert np.allclose(fr2["curvature_per_m"][mid],
                       want["curvature_per_m"], rtol=1e-3)


def test_planar_curve_zero_torsion_and_line_degenerate():
    t = np.linspace(0, 2 * np.pi, 2001)
    ellipse = np.stack([0.03 * np.cos(t), 0.01 * np.sin(t),
                        np.zeros_like(t)], axis=1)
    fr = curves.frenet_frames(ellipse)
    mid = slice(100, -100)
    assert np.nanmax(np.abs(fr["torsion_per_m"][mid])) < 1e-6
    line = np.stack([t, 2 * t, 3 * t], axis=1)
    frl = curves.frenet_frames(line)
    # interior (endpoint one-sided differences carry O(h) noise)
    interior = slice(2, -2)
    assert frl["degenerate_curvature"][interior].all()
    assert np.isnan(frl["torsion_per_m"][interior]).all()  # no fabricated value


# --- mechanical torsion (gate D2) ---------------------------------------

def test_saint_venant_twist_rate_exact():
    got = tm.saint_venant_twist_rate(10.0, 79e9, 0.005)
    J = math.pi * 0.005 ** 4 / 2
    assert got == pytest.approx(10.0 / (79e9 * J), rel=1e-12)


def test_square_bar_torsional_ladder_vs_fem():
    """Gate D2: FEM torsional fundamental vs the Saint-Venant closed
    form for a free-free square bar. Warping-theory coefficient is
    itself ~1%-class; require 5%."""
    E, NU, RHO = 210e9, 0.3, 7850.0
    G = E / (2 * (1 + NU))
    a, L = 0.01, 0.12
    mesh = fem.box_mesh((a, a, L), (3, 3, 24))
    prob = fem.assemble_isotropic(mesh, E, NU, RHO)
    sol = fem.solve_modes(prob, 14)
    ident = tm.identify_torsional_mode(prob, sol, L)
    ana = tm.square_bar_torsional_ladder_hz(G, RHO, a, L, 1)
    assert ident["overlap"] > 0.8          # clearly torsional
    assert ident["frequency_hz"] == pytest.approx(ana, rel=0.05)
    env = tm.torsion_benchmark_result(ident["frequency_hz"], ana)
    assert env["classification"] == "CORE_VALIDATED"
    # twist profile of the fundamental: half-cosine -> ends opposite
    nr = sol["n_rigid_modes"]
    prof = tm.twist_profile(
        prob, sol["modes"][:, nr + ident["mode_index_elastic"]], L)
    assert prof["theta_rad"][0] * prof["theta_rad"][-1] < 0
    # zero-torque null: no twist -> zero rate
    quiet = tm.twist_profile(prob, np.zeros(prob.ndof), L)
    assert np.allclose(quiet["twist_rate_rad_m"], 0.0)
    # a UNIFORM torque is orthogonal to the free-free torsional modes
    # (cos profile integrates to zero) — physically correct null
    ov_flat = np.abs(tm.torque_mode_overlap(prob, sol, L)[nr:])
    assert ov_flat[ident["mode_index_elastic"]] < 1e-12
    # a cos(pi z/L)-profiled torque couples dominantly to the
    # torsional fundamental
    ov = tm.torque_mode_overlap(
        prob, sol, L,
        axial_profile=lambda z: np.cos(np.pi * z / L))
    el = np.abs(ov[nr:])
    assert int(np.argmax(el)) == ident["mode_index_elastic"]


# --- circulation (gate D4-adjacent) --------------------------------------

def test_circulation_stokes_and_orientation():
    omega = 3.0

    def rigid_rotation(p):
        p = np.atleast_2d(p)
        return np.stack([-omega * p[:, 1], omega * p[:, 0],
                         np.zeros(len(p))], axis=1)

    out = circ.stokes_consistency(rigid_rotation, (0, 0, 0), 0.05)
    # analytic: circulation = 2*omega*pi*r^2; curl_z = 2*omega
    want = 2 * omega * math.pi * 0.05 ** 2
    assert out["line_integral"] == pytest.approx(want, rel=1e-3)
    assert out["rel_gap"] < 0.02
    assert "NOT" in out["note"]           # no automatic vortex claim
    # orientation reversal flips the line integral sign
    loop = circ.circle_loop((0, 0, 0), 0.05)[::-1]
    rev = circ.loop_circulation(rigid_rotation, loop)
    assert rev == pytest.approx(-want, rel=1e-3)
    # irrotational field -> zero circulation
    grad = lambda p: np.tile([1.0, 2.0, 0.0], (len(np.atleast_2d(p)), 1))
    assert abs(circ.loop_circulation(grad,
               circ.circle_loop((0, 0, 0), 0.05))) < 1e-12


# --- optical AM (gates D5, D6) -------------------------------------------

GX = np.linspace(-2e-3, 2e-3, 161)
GY = np.linspace(-2e-3, 2e-3, 161)
OMEGA = 2 * math.pi * 4.7e14


def test_plane_wave_nulls_and_circular_sam():
    ex, ey = oam.plane_wave(GX, GY, jones=(1.0, 0.0))
    assert np.allclose(oam.helicity_density(ex, ey), 0.0)     # linear
    assert np.allclose(oam.sam_density_z(ex, ey, OMEGA), 0.0)
    exc, eyc = oam.plane_wave(GX, GY,
                              jones=(1 / math.sqrt(2),
                                     1j / math.sqrt(2)))
    h = oam.helicity_density(exc, eyc)
    assert np.allclose(h, 1.0, atol=1e-12)                    # RCP
    s = oam.sam_density_z(exc, eyc, OMEGA)
    assert np.all(s > 0)
    exm, eym = oam.plane_wave(GX, GY,
                              jones=(1 / math.sqrt(2),
                                     -1j / math.sqrt(2)))
    assert np.allclose(oam.helicity_density(exm, eym), -1.0,
                       atol=1e-12)


def test_vortex_charges_and_null_beam():
    """Gate D5: charges +1, -1, 0; intensity null without winding is
    NOT a vortex."""
    for ell in (+1, -1, +2):
        f = oam.lg_beam(GX, GY, ell, 0.8e-3)
        assert oam.topological_charge(f, GX, GY, 0.6e-3) == ell
    gauss = oam.lg_beam(GX, GY, 0, 0.8e-3)
    assert oam.topological_charge(gauss, GX, GY, 0.6e-3) == 0
    # central intensity null WITHOUT phase winding (odd-symmetric
    # real superposition): charge must be 0
    dark = (oam.lg_beam(GX, GY, +1, 0.8e-3)
            + oam.lg_beam(GX, GY, -1, 0.8e-3))
    assert abs(dark[80, 80]) < 1e-12
    assert oam.topological_charge(dark, GX, GY, 0.6e-3) == 0


def test_oam_density_sign_origin_shift_and_sam_separation():
    """Gate D6: SAM and OAM are independent; extrinsic OAM depends on
    the declared origin."""
    f = oam.lg_beam(GX, GY, +1, 0.8e-3)
    lz = oam.oam_density_z(f, GX, GY, OMEGA)
    assert lz.sum() > 0
    lz_m = oam.oam_density_z(oam.lg_beam(GX, GY, -1, 0.8e-3),
                             GX, GY, OMEGA)
    assert lz_m.sum() < 0
    # a scalar vortex carries OAM with zero SAM (uniform x-pol)
    ex, ey = f, np.zeros_like(f)
    assert np.allclose(oam.sam_density_z(ex, ey, OMEGA), 0.0)
    # a displaced REAL gaussian has zero OAM about ANY origin (no
    # transverse momentum) — correct physics, asserted:
    g_real = oam.lg_beam(GX - 0.5e-3, GY, 0, 0.5e-3)
    assert abs(oam.oam_density_z(g_real, GX, GY, OMEGA,
                                 origin_m=(0, 0)).sum()) < 1e-30
    # intrinsic OAM: a displaced beam with ZERO net transverse
    # momentum has origin-INDEPENDENT total OAM (Berry) — asserted:
    g_disp = oam.lg_beam(GX - 0.5e-3, GY, +1, 0.5e-3)
    li0 = oam.oam_density_z(g_disp, GX, GY, OMEGA,
                            origin_m=(0, 0)).sum()
    li1 = oam.oam_density_z(g_disp, GX, GY, OMEGA,
                            origin_m=(0.5e-3, 0)).sum()
    assert np.isclose(li0, li1, rtol=1e-6, atol=0.0)
    # extrinsic OAM: with a transverse phase ramp (net transverse
    # momentum), the total OAM DOES depend on the declared origin
    X, _ = np.meshgrid(GX, GY, indexing="ij")
    tilted = g_disp * np.exp(1j * 2e4 * X)
    le0 = oam.oam_density_z(tilted, GX, GY, OMEGA,
                            origin_m=(0, 0)).sum()
    le1 = oam.oam_density_z(tilted, GX, GY, OMEGA,
                            origin_m=(0, 0.5e-3)).sum()
    assert not np.isclose(le0, le1, rtol=1e-3, atol=0.0)
    # canonical vs Poynting-style outputs are distinct objects
    az = oam.poynting_azimuthal(f, GX, GY)
    assert az.shape == lz.shape and not np.allclose(az, lz)


def test_transverse_spin_locking():
    out_p = oam.transverse_spin_evanescent(1.2e7, 0.7e7, OMEGA)
    out_m = oam.transverse_spin_evanescent(-1.2e7, 0.7e7, OMEGA)
    assert out_p["s_y"] * out_m["s_y"] < 0     # locked to propagation
    assert out_p["quantity_id"].endswith("transverse_spin")


# --- chiral phonon (gate D7) ---------------------------------------------

def test_chiral_phonon_phase_and_field_reversal():
    w = 2 * math.pi * 5e12
    t = np.linspace(0, 20 * 2 * math.pi / w, 4000)
    plus = cp.trajectory(1.0, w, +math.pi / 2, t)
    minus = cp.trajectory(1.0, w, -math.pi / 2, t)
    assert plus["lz_cycle_mean"] > 0 > minus["lz_cycle_mean"]
    assert plus["lz_cycle_mean"] == pytest.approx(
        cp.angular_momentum(1.0, w, math.pi / 2), rel=1e-6)
    for ph in (0.0, math.pi):
        lin = cp.trajectory(1.0, w, ph, t)
        assert abs(lin["lz_cycle_mean"]) < 1e-9 * w
    env = cp.zeeman_splitting_interface("reference.chiral_phonon",
                                        2.0, 1.0, 1.0, w,
                                        math.pi / 2)
    env2 = cp.zeeman_splitting_interface("reference.chiral_phonon",
                                         2.0, -1.0, 1.0, w,
                                         math.pi / 2)
    assert env["value"]["delta_e_units_of_g"] == \
        -env2["value"]["delta_e_units_of_g"]   # field reversal


def test_chiral_phonon_quartz_not_applicable_and_no_default_g():
    out = cp.zeeman_splitting_interface("material.alpha_quartz", 2.0,
                                        1.0, 1.0, 1e12, math.pi / 2)
    assert out["classification"] == "NOT_APPLICABLE"
    assert out["value"] is None
    nog = cp.zeeman_splitting_interface("reference.chiral_phonon",
                                        None, 1.0, 1.0, 1e12,
                                        math.pi / 2)
    assert nog["reason_code"] == "MATERIAL_G_FACTOR_ABSENT"
