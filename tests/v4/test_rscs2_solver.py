"""CPU solver validation: the M3 gate benchmarks (closes V4-D-001).

Steel cantilever/rod cases against `rscs2_core.reference` closed forms;
alpha-quartz constrained bar against the FROZEN v3 Christoffel speed
(conservative extension, RSCS2-V.6). Marked slow-ish but all run < ~2 min.
"""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core import fem, reference as ref

E, NU, RHO = 210e9, 0.3, 7850.0
L, W, T = 0.1, 0.01, 0.01


def _cantilever_f1(divisions):
    mesh = fem.box_mesh((L, W, T), divisions)
    prob = fem.assemble_isotropic(mesh, E, NU, RHO)
    fixed = prob.dofs_on(lambda x: np.isclose(x[0], 0.0))
    out = fem.solve_modes(prob, 4, fixed_dofs=fixed)
    assert out["n_rigid_modes"] == 0
    assert np.all(out["residuals"] < 1e-6)
    return out["elastic_frequencies_hz"][0]


def test_cantilever_eb_benchmark():
    """RSCS2-V.2: first flexural frequency within 0.5% of Euler-Bernoulli
    (3D elasticity sits slightly BELOW EB for L/t=10 — correct physics)."""
    f_ana = ref.euler_bernoulli_cantilever_hz(E, RHO, L, W, T, 1)
    f_fem = _cantilever_f1((20, 2, 2))
    assert abs(f_fem - f_ana) / f_ana < 0.005
    assert f_fem < f_ana * 1.001  # never stiffer than EB at convergence


def test_mesh_convergence():
    """RSCS2-V.8: error vs EB decreases monotonically under refinement."""
    f_ana = ref.euler_bernoulli_cantilever_hz(E, RHO, L, W, T, 1)
    errs = [abs(_cantilever_f1(d) - f_ana) / f_ana
            for d in ((6, 1, 1), (12, 2, 2), (24, 3, 3))]
    assert errs[0] > errs[1] > errs[2]
    assert errs[-1] < 0.005


def test_static_tip_deflection():
    """Cantilever static patch test: FL^3/(3EI) within 1%."""
    out = fem.static_tip_deflection(E, NU, RHO, (L, W, T), (24, 2, 3))
    err = abs(out["delta_fem_m"] - out["delta_analytic_m"]) / \
        out["delta_analytic_m"]
    assert err < 0.01


def test_free_body_rigid_modes_and_mass_patch():
    """Patch tests: a free body has exactly 6 near-zero rigid modes, and
    the consistent mass matrix carries the exact total mass rho*V (the
    guard that catches the V4-D-001 ddot-mass bug class)."""
    mesh = fem.box_mesh((0.2, 0.02, 0.02), (12, 2, 2))
    prob = fem.assemble_isotropic(mesh, E, NU, RHO)
    assert prob.total_mass_kg() == pytest.approx(RHO * 0.2 * 0.02 * 0.02,
                                                 rel=1e-9)
    out = fem.solve_modes(prob, 10)
    assert out["n_rigid_modes"] == 6
    assert out["elastic_frequencies_hz"][0] > 100.0


def test_v4_d001_regression_ddot_mass_is_wrong():
    """The buggy ddot-based mass must NOT equal the true mass — pins the
    root cause of V4-D-001 so a regression is unmistakable."""
    from skfem import Basis, BilinearForm, ElementTetP2, ElementVector
    from skfem.helpers import ddot
    mesh = fem.box_mesh((L, W, T), (6, 1, 1))
    basis = Basis(mesh, ElementVector(ElementTetP2()))

    @BilinearForm
    def bad_mass(u, v, w):
        return RHO * ddot(u, v)     # the V4-D-001 bug

    M_bad = bad_mass.assemble(basis)
    u = np.zeros(basis.N)
    u[fem.component_dofs(basis, 0)] = 1.0
    true_mass = RHO * L * W * T
    assert abs(float(u @ (M_bad @ u)) - true_mass) / true_mass > 0.5


def test_isotropic_constrained_bar_pwave():
    """Laterally-constrained isotropic bar: plane-wave ladder with the
    P-wave modulus, f_n = n * sqrt((lam+2mu)/rho) / (2 Lz)."""
    lam, mu = ref.lame_from_e_nu(E, NU)
    lz = 0.05
    mesh = fem.box_mesh((0.005, 0.005, lz), (2, 2, 30))
    prob = fem.assemble_isotropic(mesh, E, NU, RHO)
    lateral = np.concatenate([fem.component_dofs(prob.basis, 0),
                              fem.component_dofs(prob.basis, 1)])
    out = fem.solve_modes(prob, 4, fixed_dofs=lateral)
    v_p = np.sqrt((lam + 2 * mu) / RHO)
    f = out["frequencies_hz"]
    assert out["n_rigid_modes"] == 1          # z-translation remains
    for n, fn in enumerate(out["elastic_frequencies_hz"][:3], start=1):
        assert fn == pytest.approx(n * v_p / (2 * lz), rel=1e-3)


def test_thick_beam_timoshenko():
    """RSCS2-V.3 solver validation: a THICK cantilever (L/t=5) bends in z
    at the Timoshenko-corrected frequency, distinctly below EB. Also pins
    per-axis mode ordering (weak-axis y-bend is mode 1)."""
    lam, mu = ref.lame_from_e_nu(E, NU)
    lx, wy, tz = 0.1, 0.01, 0.02
    mesh = fem.box_mesh((lx, wy, tz), (24, 2, 4))
    prob = fem.assemble_isotropic(mesh, E, NU, RHO)
    fixed = prob.dofs_on(lambda x: np.isclose(x[0], 0.0))
    out = fem.solve_modes(prob, 4, fixed_dofs=fixed)
    f = out["elastic_frequencies_hz"]
    f_tim_z = ref.timoshenko_cantilever_hz(E, mu, RHO, lx, wy, tz, n=1)
    f_eb_z = ref.euler_bernoulli_cantilever_hz(E, RHO, lx, wy, tz, 1)
    assert f[1] == pytest.approx(f_tim_z, rel=0.01)   # +0.03% observed
    assert f[1] < f_eb_z * 0.99                       # clearly below EB
    # weak axis first (bends in the 0.01 m direction)
    f_tim_y = ref.timoshenko_cantilever_hz(E, mu, RHO, lx, tz, wy, n=1)
    assert f[0] == pytest.approx(f_tim_y, rel=0.02)


def test_orthonormality_harmonic_and_serialization(tmp_path):
    """RSCS2-S.3/S.5 + deterministic serialization: modes are
    M-orthonormal; the driven FRF peaks at the first eigenfrequency;
    save/load round-trips exactly."""
    mesh = fem.box_mesh((L, W, T), (12, 2, 2))
    prob = fem.assemble_isotropic(mesh, E, NU, RHO)
    fixed = prob.dofs_on(lambda x: np.isclose(x[0], 0.0))
    out = fem.solve_modes(prob, 4, fixed_dofs=fixed)
    assert out["orthonormality_error"] < 1e-8
    f1 = out["elastic_frequencies_hz"][0]
    # FRF: unit tip force in z, sweep around f1 -> resonant peak at f1
    force = np.zeros(prob.ndof)
    zdofs = fem.component_dofs(prob.basis, 2)
    tip = zdofs[np.isclose(prob.basis.doflocs[0][zdofs], L)]
    force[tip] = 1.0
    sweep = np.array([0.8 * f1, 0.95 * f1, 0.999 * f1, 1.2 * f1])
    frf = fem.harmonic_response(prob, force, sweep, fixed_dofs=fixed)
    assert np.argmax(frf["amplitude_max"]) == 2      # nearest f1 wins
    # serialization round-trip
    p = tmp_path / "modes.npz"
    fem.save_modes(out, p)
    back = fem.load_modes(p)
    assert np.array_equal(back["frequencies_hz"], out["frequencies_hz"])
    assert np.array_equal(back["modes"], out["modes"])
    assert back["n_rigid_modes"] == out["n_rigid_modes"]


def test_christoffel_anchor_quartz():
    """RSCS2-V.6 (conservative extension, DV4-009): a laterally-constrained
    alpha-quartz bar along Z reproduces the FROZEN v3 Christoffel
    quasi-longitudinal speed as an exact harmonic ladder f_n = n vZ/(2L)."""
    from rgcs_core.anisotropy import (ALPHA_QUARTZ_DENSITY_KG_M3,
                                      alpha_quartz_stiffness_pa,
                                      wave_speeds)
    from rscs_core.propagation import voigt_to_tensor
    c_full = voigt_to_tensor(alpha_quartz_stiffness_pa())
    v_z = wave_speeds(np.array([0.0, 0.0, 1.0]))["v_quasi_long_m_s"]
    lz = 0.05
    mesh = fem.box_mesh((0.005, 0.005, lz), (2, 2, 40))
    prob = fem.assemble_anisotropic(mesh, c_full,
                                    ALPHA_QUARTZ_DENSITY_KG_M3)
    lateral = np.concatenate([fem.component_dofs(prob.basis, 0),
                              fem.component_dofs(prob.basis, 1)])
    out = fem.solve_modes(prob, 5, fixed_dofs=lateral)
    assert out["n_rigid_modes"] == 1
    for n, fn in enumerate(out["elastic_frequencies_hz"][:4], start=1):
        assert fn == pytest.approx(n * v_z / (2 * lz), rel=1e-3)
