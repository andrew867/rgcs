"""Agent 10: reference systems — cavity (exact), tuning fork
(sym/antisym + common-mode rejection), and the V.9 avoided-crossing
anchor against the FROZEN v3 coupled-mode model."""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core import fem, refsystems as rs

E, NU, RHO = 210e9, 0.3, 7850.0

gmsh_ok = True
try:
    import subprocess

    from rscs2_core.crystal110 import _gmsh_cmd
    subprocess.run(_gmsh_cmd() + ["--version"], capture_output=True,
                   timeout=60, check=True)
except Exception:
    gmsh_ok = False
needs_gmsh = pytest.mark.skipif(not gmsh_ok, reason="gmsh unavailable")


def test_cavity_exact_reference():
    """G17: rigid-wall rectangular cavity vs EXACT closed form."""
    lengths = (0.5, 0.4, 0.3)
    ana = rs.cavity_modes_analytic(lengths)[:6]
    out = rs.cavity_modes_fem(lengths, (8, 7, 6), n_modes=8)
    k0 = out["n_constant_modes"]
    assert k0 == 1                       # exactly one constant-pressure mode
    femf = out["frequencies_hz"][k0:k0 + 6]
    assert np.allclose(femf, ana, rtol=5e-4)
    # degeneracy bookkeeping: no accidental extra near-zero modes
    assert out["frequencies_hz"][k0] > 300.0


def test_cavity_degeneracy_in_cube():
    """A cubic cavity has an exactly 3-fold degenerate first mode
    (100/010/001) — symmetry-protected, correctly resolved."""
    out = rs.cavity_modes_fem((0.3, 0.3, 0.3), (6, 6, 6), n_modes=6)
    k0 = out["n_constant_modes"]
    f = out["frequencies_hz"][k0:k0 + 3]
    ana = rs.SOUND_SPEED_AIR_M_S / (2 * 0.3)
    assert np.allclose(f, ana, rtol=5e-4)
    assert (f.max() - f.min()) / f.mean() < 1e-3   # 3-fold degenerate


def _fork_pair(tip_sigma_kg_m2=0.0):
    """Base-FIXED fork (clamped z=0): two cantilever prongs coupled only
    through the shared base block -> a WEAKLY coupled in-plane pair
    (S0 ~ 9 Hz on ~1238 Hz), the regime the two-mode model describes.
    (A free fork couples the symmetric mode into base flexure and splits
    the pair by kHz — strong coupling, diagnosed during Agent 10.)
    Returns the identified in-plane pair as
    [(mode_index, f_hz, tipA_x, tipB_x, base_cm_ratio), ...]."""
    fk = rs.fork_mesh("evidence/v4/agent10/scratch", cl_mm=4.0)
    prob = fem.assemble_isotropic(fk["mesh"], E, NU, RHO)
    dims = fk["dims"]
    top = dims["base_h_m"] + dims["prong_len_m"]
    if tip_sigma_kg_m2 > 0.0:
        # prong A only: x < prong width
        prob = fem.add_surface_mass(
            prob, lambda x: np.isclose(x[2], top)
            & (x[0] < dims["prong_w_m"] + 1e-9), tip_sigma_kg_m2)
    fixed = prob.basis.get_dofs(
        lambda x: np.isclose(x[2], 0.0)).flatten()
    sol = fem.solve_modes(prob, 8, fixed_dofs=fixed)
    locs = prob.basis.doflocs
    xdofs = fem.component_dofs(prob.basis, 0)
    tipA = xdofs[(np.abs(locs[2, xdofs] - top) < 1e-6)
                 & (locs[0, xdofs] < dims["prong_w_m"] + 1e-9)]
    tipB = xdofs[(np.abs(locs[2, xdofs] - top) < 1e-6)
                 & (locs[0, xdofs] > dims["base_w_m"]
                    - dims["prong_w_m"] - 1e-9)]
    base = xdofs[(locs[2, xdofs] > dims["base_h_m"] * 0.1)
                 & (locs[2, xdofs] < dims["base_h_m"] * 0.9)]
    pair = []
    for i in range(sol["modes"].shape[1]):
        mode = sol["modes"][:, i]
        a, b = np.mean(mode[tipA]), np.mean(mode[tipB])
        tip = max(abs(a), abs(b))
        if tip > 1.0:            # in-plane (x-dominated) prong mode
            pair.append((i, sol["frequencies_hz"][i], a, b,
                         float(np.abs(mode[base]).mean() / tip)))
        if len(pair) == 2:
            break
    assert len(pair) == 2, "in-plane prong pair not found in 8 modes"
    return fk, sol, pair


@needs_gmsh
def test_fork_symmetric_antisymmetric_and_cmr():
    """G15: the base-fixed fork has a weakly split in-plane prong pair;
    classify sym/antisym by signed prong-tip x-motion; the ANTISYMMETRIC
    (tuning-fork) mode shows common-mode rejection: far smaller net
    base x-motion than the symmetric mode."""
    _, sol, pair = _fork_pair()
    assert sol["n_rigid_modes"] == 0            # fully clamped base
    kinds = {("sym" if a * b > 0 else "antisym"): (f_hz, cm)
             for _, f_hz, a, b, cm in pair}
    assert set(kinds) == {"sym", "antisym"}     # one of each
    f_sym, cm_sym = kinds["sym"]
    f_anti, cm_anti = kinds["antisym"]
    assert cm_anti < 0.35 * cm_sym              # common-mode rejection
    # weak coupling: split resolved but small vs the pair mean
    split = abs(f_anti - f_sym)
    fbar = 0.5 * (f_anti + f_sym)
    assert 1e-4 < split / fbar < 0.05


@needs_gmsh
def test_v9_avoided_crossing_anchor_frozen_model():
    """RSCS2-V.9 (conservative extension, DV4-009): detuning one prong
    with tip mass traces an avoided crossing whose splitting follows the
    FROZEN v3 two-mode model S = sqrt(Delta^2 + S0^2)
    (rgcs_core.coupled_modes / RSCS-O.4 / RGCS-M.24)."""
    from rgcs_core.coupled_modes.static import coupled_two_mode
    fk0, _, pair0 = _fork_pair(0.0)
    f0 = np.sort([p[1] for p in pair0])
    s0 = f0[1] - f0[0]
    fbar = f0.mean()
    g = s0 / 2.0                                  # frozen-model coupling
    dims = fk0["dims"]
    m_prong = RHO * dims["prong_w_m"] * dims["thickness_m"] \
        * dims["prong_len_m"]
    m_eff = 0.2427 * m_prong    # cantilever Rayleigh effective mass
    splits_fem, splits_frozen = [], []
    for sigma in (0.5, 1.0, 2.0):
        _, _, pair = _fork_pair(sigma)
        fpair = np.sort([p[1] for p in pair])
        splits_fem.append(fpair[1] - fpair[0])
        # detuned isolated-prong frequency by the Rayleigh mass formula
        # (validated in test_mass_loading_b4)
        dm = sigma * dims["prong_w_m"] * dims["thickness_m"]
        fa = fbar * np.sqrt(m_eff / (m_eff + dm))
        # FROZEN two-mode hybridization (RSCS-O.4 / RGCS-M.24)
        two = coupled_two_mode(fa, fbar, g)
        splits_frozen.append(two["upper_hybrid_hz"]
                             - two["lower_hybrid_hz"])
    splits_fem = np.array(splits_fem)
    splits_frozen = np.array(splits_frozen)
    # splitting grows with detuning (avoided crossing, not numerical)
    assert np.all(np.diff(splits_fem) > 0)
    assert splits_fem[-1] > 1.3 * s0
    # frozen-model prediction tracks FEM within 15% at every detuning
    assert np.all(np.abs(splits_fem - splits_frozen)
                  / splits_fem < 0.15)
