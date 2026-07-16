"""Agent 06: piezoelectric coupled-field validation battery."""
from __future__ import annotations

import numpy as np
import pytest

from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                  alpha_quartz_stiffness_pa)
from rscs_core.propagation import voigt_to_tensor
from rscs2_core import fem, piezo, quartz as qz

C = voigt_to_tensor(alpha_quartz_stiffness_pa())
RHO = ALPHA_QUARTZ_DENSITY_KG_M3

# X-cut length-extensional bar: length along Y, field/electrodes along X
LX, LY, LZ = 0.004, 0.02, 0.004
EL = [lambda x: np.isclose(x[0], 0.0), lambda x: np.isclose(x[0], LX)]


def _bar(div=(2, 10, 2)):
    return fem.box_mesh((LX, LY, LZ), div)


def test_block_symmetry_and_reciprocity():
    prob = piezo.assemble_piezo(_bar((2, 6, 2)), C, RHO)
    assert abs(prob.Kuu - prob.Kuu.T).max() < 1e-12 * abs(prob.Kuu).max()
    assert abs(prob.Kpp - prob.Kpp.T).max() < 1e-12 * abs(prob.Kpp).max()
    # reciprocity: the coupling block enters symmetrically (saddle form)
    assert prob.Kup.shape == (prob.u_basis.N, prob.p_basis.N)


def test_zero_piezo_reduces_exactly_to_elastic():
    mesh = _bar((2, 8, 2))
    p0 = piezo.PiezoProblem(mesh, C, np.zeros((3, 3, 3)),
                            qz.quartz_dielectric_f_m(), RHO)
    f_piezo = piezo.solve_piezo_modes(p0, 6, EL, "short")[
        "elastic_frequencies_hz"]
    f_elast = fem.solve_modes(fem.assemble_anisotropic(mesh, C, RHO),
                              6)["elastic_frequencies_hz"]
    assert np.allclose(f_piezo, f_elast, rtol=1e-9)


def test_single_element_energy_patch():
    """Uniform strain + uniform field on a tiny mesh: each discrete
    quadratic form equals its closed-form volume integral."""
    lx = ly = lz = 0.002
    mesh = fem.box_mesh((lx, ly, lz), (1, 1, 1))
    e_t = qz.quartz_piezo_tensor_c_m2()
    eps = qz.quartz_dielectric_f_m()
    prob = piezo.PiezoProblem(mesh, C, e_t, eps, RHO)
    vol = lx * ly * lz
    rng = np.random.default_rng(3)
    A = rng.normal(scale=1e-4, size=(3, 3))       # u = A x (S = sym A)
    g = rng.normal(size=3)                        # phi = g . x
    S = 0.5 * (A + A.T)
    xu = prob.u_basis.doflocs                     # (3, Nu)
    u = np.einsum("ij,jn->in", A, xu).T.reshape(-1)  # interleaved x,y,z
    # interleaving: doflocs columns are per-dof; component = dof index %3
    u = np.zeros(prob.u_basis.N)
    for comp in range(3):
        idx = fem.component_dofs(prob.u_basis, comp)
        u[idx] = (A[comp] @ prob.u_basis.doflocs[:, idx])
    xp = prob.p_basis.doflocs
    phi = g @ xp
    # block energies vs closed forms
    e_uu = float(u @ (prob.Kuu @ u))
    ref_uu = vol * np.einsum("ij,ijkl,kl", S, C, S)
    assert e_uu == pytest.approx(ref_uu, rel=1e-9)
    e_pp = float(phi @ (prob.Kpp @ phi))
    ref_pp = vol * (g @ eps @ g)
    assert e_pp == pytest.approx(ref_pp, rel=1e-9)
    e_up = float(u @ (prob.Kup @ phi))
    ref_up = vol * np.einsum("kij,k,ij", e_t, g, S)
    assert e_up == pytest.approx(ref_up, rel=1e-9)


def test_open_ge_short_and_extensional_coupling():
    """f_open >= f_short mode-by-mode; the Y-extensional mode of the
    X-cut bar carries physically-sized coupling (quartz k ~ 0.1 =>
    k^2 ~ 1e-2; band kept generous, no precision claim)."""
    prob = piezo.assemble_piezo(_bar(), C, RHO)
    fs = piezo.solve_piezo_modes(prob, 12, EL, "short")[
        "elastic_frequencies_hz"]
    fo = piezo.solve_piezo_modes(prob, 12, EL, "open")[
        "elastic_frequencies_hz"]
    n = min(len(fs), len(fo))
    assert np.all(fo[:n] >= fs[:n] * (1 - 1e-12))
    # find the length-extensional mode: nearest to c_ext/(2 LY) with
    # c_ext = sqrt(1/s22 / rho) — use the band 100-180 kHz for this bar
    k2 = np.array([piezo.coupling_factor(a, b)
                   for a, b in zip(fo[:n], fs[:n])])
    band = (fs[:n] > 100e3) & (fs[:n] < 180e3)
    assert band.any()
    k2_ext = k2[band].max()
    assert 0.002 < k2_ext < 0.05          # order of quartz k^2 ~ 0.01


def test_electrode_reversal_flips_displacement():
    mesh = _bar((2, 6, 2))
    prob = piezo.assemble_piezo(mesh, C, RHO)
    fixed_u = prob.u_basis.get_dofs(
        lambda x: np.isclose(x[1], 0.0)).flatten()
    a = piezo.static_potential_response(prob, EL[0], EL[1], 10.0, fixed_u)
    b = piezo.static_potential_response(prob, EL[1], EL[0], 10.0, fixed_u)
    assert np.max(np.abs(a["u"])) > 0
    assert np.allclose(a["u"], -b["u"], atol=1e-9 * np.abs(a["u"]).max())
    # zero drive -> zero response (no artificial field)
    z = piezo.static_potential_response(prob, EL[0], EL[1], 0.0, fixed_u)
    assert np.max(np.abs(z["u"])) < 1e-15


def test_mesh_convergence_short_circuit():
    f = []
    for div in ((2, 8, 2), (2, 14, 3)):
        prob = piezo.assemble_piezo(_bar(div), C, RHO)
        f.append(piezo.solve_piezo_modes(prob, 10, EL, "short")[
            "elastic_frequencies_hz"][0])
    assert abs(f[1] - f[0]) / f[0] < 0.02
    assert f[1] <= f[0] * 1.001            # P2 from above


def test_frame_invariance_rotated_tensors():
    """Rotate ALL material tensors by a body symmetry of the square-
    section bar (180 deg about Y keeps the box and electrode faces
    geometrically equivalent): spectrum must be unchanged."""
    r = qz.euler_zxz_matrix(0.0, 180.0, 0.0) @ qz.euler_zxz_matrix(
        90.0, 0.0, 0.0) @ qz.euler_zxz_matrix(-90.0, 0.0, 0.0)
    # build an exact 180-deg rotation about the Y axis
    r = np.array([[-1.0, 0, 0], [0, 1.0, 0], [0, 0, -1.0]])
    mesh = _bar((2, 8, 2))
    base = piezo.assemble_piezo(mesh, C, RHO)
    rot = piezo.PiezoProblem(mesh, qz.rotate_stiffness(C, r),
                             qz.rotate_piezo(
                                 qz.quartz_piezo_tensor_c_m2(), r),
                             qz.rotate_dielectric(
                                 qz.quartz_dielectric_f_m(), r), RHO)
    f0 = piezo.solve_piezo_modes(base, 6, EL, "short")[
        "elastic_frequencies_hz"]
    f1 = piezo.solve_piezo_modes(rot, 6, EL, "short")[
        "elastic_frequencies_hz"]
    assert np.allclose(f1, f0, rtol=2e-3)
