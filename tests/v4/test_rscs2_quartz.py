"""Agent 04: orientation-aware anisotropic alpha-quartz validation.

Bond rotations (identity/inverse/composition/known-angle/symmetry),
batched Christoffel vs the FROZEN v3 module, free anisotropic crystal
modes (rigid count, convergence, frame invariance), and the degeneracy
taxonomy (numerical vs symmetry-protected vs section-induced splitting).
"""
from __future__ import annotations

import numpy as np
import pytest

from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                  alpha_quartz_stiffness_pa, wave_speeds)
from rscs_core.propagation import voigt_to_tensor
from rscs2_core import fem, quartz as qz

C_FULL = voigt_to_tensor(alpha_quartz_stiffness_pa())
RHO = ALPHA_QUARTZ_DENSITY_KG_M3


# --- material record --------------------------------------------------

def test_material_record_and_tensor_symmetries():
    rec = qz.material_record()
    assert rec["density_kg_m3"] == RHO
    # stiffness minor+major symmetries
    assert np.allclose(C_FULL, C_FULL.transpose(1, 0, 2, 3))
    assert np.allclose(C_FULL, C_FULL.transpose(0, 1, 3, 2))
    assert np.allclose(C_FULL, C_FULL.transpose(2, 3, 0, 1))
    # piezo symmetric in (i,j); row 3 (k=z) identically zero for class 32
    e = qz.quartz_piezo_tensor_c_m2()
    assert np.allclose(e, e.transpose(0, 2, 1))
    assert np.allclose(e[2], 0.0)
    # dielectric SPD
    eps = qz.quartz_dielectric_f_m()
    assert np.all(np.linalg.eigvalsh(eps) > 0)
    # elastic energy positivity: random strains
    rng = np.random.default_rng(4)
    for _ in range(20):
        s = rng.normal(size=(3, 3))
        s = 0.5 * (s + s.T)
        w = np.einsum("ij,ijkl,kl", s, C_FULL, s)
        assert w > 0


# --- rotations --------------------------------------------------------

def test_rotation_identity_inverse_composition():
    r1 = qz.euler_zxz_matrix(31.0, 47.0, 13.0)
    r2 = qz.euler_zxz_matrix(-12.0, 78.0, 101.0)
    c1 = qz.rotate_stiffness(C_FULL, r1)
    # identity
    assert np.allclose(qz.rotate_stiffness(C_FULL, np.eye(3)), C_FULL)
    # inverse round-trip
    back = qz.rotate_stiffness(c1, r1.T)
    assert np.allclose(back, C_FULL, atol=1e-6 * np.abs(C_FULL).max())
    # composition: R2 (R1 C) == (R2 R1) C
    a = qz.rotate_stiffness(c1, r2)
    b = qz.rotate_stiffness(C_FULL, r2 @ r1)
    assert np.allclose(a, b, atol=1e-6 * np.abs(C_FULL).max())
    # symmetries preserved
    assert np.allclose(c1, c1.transpose(2, 3, 0, 1),
                       atol=1e-6 * np.abs(C_FULL).max())
    # energy positivity preserved
    rng = np.random.default_rng(7)
    s = rng.normal(size=(3, 3)); s = 0.5 * (s + s.T)
    assert np.einsum("ij,ijkl,kl", s, c1, s) > 0
    # rejects improper rotation
    with pytest.raises(ValueError):
        qz.rotate_stiffness(C_FULL, -np.eye(3))


def test_trigonal_symmetry_and_known_rotation():
    # class 32: 120-degree rotation about Z leaves C invariant
    r120 = qz.euler_zxz_matrix(120.0, 0.0, 0.0)
    assert np.allclose(qz.rotate_stiffness(C_FULL, r120), C_FULL,
                       atol=1e-6 * np.abs(C_FULL).max())
    # 2-fold about X (the a-axis) also a symmetry of class 32
    rx180 = qz.euler_zxz_matrix(0.0, 180.0, 0.0)
    assert np.allclose(qz.rotate_stiffness(C_FULL, rx180), C_FULL,
                       atol=1e-6 * np.abs(C_FULL).max())
    # 90-degree case: rotating the CRYSTAL by R, the lab-frame speed along
    # lab direction m equals the crystal-frame speed along R^T m
    r = qz.euler_zxz_matrix(0.0, 90.0, 0.0)     # x-rotation by 90 deg
    c_rot = qz.rotate_stiffness(C_FULL, r)
    m = np.array([0.0, 0.0, 1.0])               # lab Z
    v_lab = qz.christoffel_speeds(c_rot, RHO, m)["speeds_m_s"][0]
    v_ref = wave_speeds(r.T @ m)                # frozen module, crystal frame
    assert v_lab[0] == pytest.approx(v_ref["v_quasi_long_m_s"], rel=1e-9)


# --- Christoffel anchors ---------------------------------------------

def test_christoffel_matches_frozen_v3_on_sweep():
    rng = np.random.default_rng(11)
    dirs = rng.normal(size=(40, 3))
    dirs = np.vstack([np.eye(3), dirs])          # axes + random off-axis
    out = qz.christoffel_speeds(C_FULL, RHO, dirs)
    for k, d in enumerate(dirs):
        ref = wave_speeds(d)
        assert out["speeds_m_s"][k, 0] == pytest.approx(
            ref["v_quasi_long_m_s"], rel=1e-9)
        assert out["speeds_m_s"][k, 2] == pytest.approx(
            ref["v_quasi_shear2_m_s"], rel=1e-9)
    # polarizations are unit orthonormal triads
    p = out["polarizations"][0]
    assert np.allclose(p.T @ p, np.eye(3), atol=1e-9)


def test_orientation_sweep_surfaces():
    sweep = qz.orientation_sweep(n_theta=13, n_phi=25)
    vql = sweep["v_qL"]
    assert vql.shape == (13, 25)
    # Z-axis pole equals the frozen axial value everywhere on the pole ring
    vz = wave_speeds(np.array([0, 0, 1.0]))["v_quasi_long_m_s"]
    assert np.allclose(vql[0, :], vz, rtol=1e-9)
    # speeds inside the physical bracket set by the frozen axis values
    assert vql.min() > 4000 and vql.max() < 9000
    # 3-fold azimuthal symmetry of the qL surface (trigonal)
    mid = vql[6, :-1]                            # theta ~ 90 deg ring
    third = (len(mid)) // 3
    assert np.allclose(mid, np.roll(mid, third), rtol=1e-6)


# --- free anisotropic crystal modes -----------------------------------

def _free_quartz_modes(divisions, r=None, lengths=(0.02, 0.02, 0.05)):
    c = C_FULL if r is None else qz.rotate_stiffness(C_FULL, r)
    mesh = fem.box_mesh(lengths, divisions)
    prob = fem.assemble_anisotropic(mesh, c, RHO)
    return fem.solve_modes(prob, 12)


def test_free_quartz_rigid_modes_and_convergence():
    coarse = _free_quartz_modes((3, 3, 8))
    fine = _free_quartz_modes((4, 4, 12))
    for out in (coarse, fine):
        assert out["n_rigid_modes"] == 6
        assert np.all(out["elastic_frequencies_hz"] > 0)
        elastic_res = out["residuals"][~np.isnan(out["residuals"])]
        assert np.all(elastic_res < 1e-6)
    # convergence: fine within 2% of coarse and BELOW it (P2 upper bound)
    fc = coarse["elastic_frequencies_hz"][:4]
    ff = fine["elastic_frequencies_hz"][:4]
    assert np.all(ff <= fc * 1.0001)
    assert np.all(np.abs(ff - fc) / fc < 0.02)


def test_frame_invariance_rotating_body_and_material():
    """Rotating the MATERIAL by R while keeping the body fixed must give
    the same spectrum as keeping the material and rotating the body --
    for a body shape that is invariant under R (cube), the spectrum must
    be identical under material rotation by a body-symmetry R=90 deg Z."""
    r = qz.euler_zxz_matrix(90.0, 0.0, 0.0)      # cube symmetric under Rz90
    base = _free_quartz_modes((4, 4, 4), lengths=(0.02, 0.02, 0.02))
    rot = _free_quartz_modes((4, 4, 4), r=r, lengths=(0.02, 0.02, 0.02))
    f0 = base["elastic_frequencies_hz"][:6]
    f1 = rot["elastic_frequencies_hz"][:6]
    # NOTE: Rz(90) is NOT a symmetry of trigonal quartz, but the cube +
    # rotated material == rotated (cube + material) == same physics in a
    # rotated lab frame -> identical spectrum (frame invariance).
    assert np.allclose(f1, f0, rtol=2e-3)


def test_orientation_changes_spectrum():
    """A NON-symmetry rotation must measurably shift the free spectrum of
    an elongated body (orientation sensitivity, the physical effect)."""
    base = _free_quartz_modes((3, 3, 8))
    rot = _free_quartz_modes((3, 3, 8),
                             r=qz.euler_zxz_matrix(0.0, 90.0, 0.0))
    f0 = base["elastic_frequencies_hz"][:4]
    f1 = rot["elastic_frequencies_hz"][:4]
    assert np.max(np.abs(f1 - f0) / f0) > 0.02   # >2% shift somewhere


# --- degeneracy taxonomy (V.9 groundwork) ------------------------------

def test_degeneracy_taxonomy():
    """Distinguish: (a) symmetry-protected degeneracy -- ISOTROPIC square
    beam flexural pairs stay degenerate as the mesh refines; (b)
    section-induced splitting -- rectangular beam pair splits and the
    split PERSISTS under refinement; (c) numerical degeneracy -- the
    isotropic-square split shrinks with refinement (pure discretization).
    """
    E, NU, RHO_S = 210e9, 0.3, 7850.0

    def flex_pair(w, t, div):
        mesh = fem.box_mesh((0.1, w, t), div)
        prob = fem.assemble_isotropic(mesh, E, NU, RHO_S)
        fixed = prob.dofs_on(lambda x: np.isclose(x[0], 0.0))
        f = fem.solve_modes(prob, 3,
                            fixed_dofs=fixed)["elastic_frequencies_hz"]
        return f[0], f[1]

    # (a)+(c): square section -- split is numerical, shrinks on refinement
    s1 = np.abs(np.subtract(*flex_pair(0.01, 0.01, (12, 2, 2))))
    s2 = np.abs(np.subtract(*flex_pair(0.01, 0.01, (16, 3, 3))))
    assert s2 < s1                       # numerical degeneracy tightens
    assert s2 < 2.0                      # Hz; near-degenerate
    # (b): rectangular section -- physical split, persists (ratio ~ t2/t1)
    r1 = flex_pair(0.01, 0.012, (12, 2, 2))
    r2 = flex_pair(0.01, 0.012, (16, 3, 3))
    split1 = abs(r1[1] - r1[0]); split2 = abs(r2[1] - r2[0])
    assert split1 > 50 and split2 > 50   # far above numerical scale
    assert abs(split2 - split1) / split1 < 0.1   # persistent under refine
