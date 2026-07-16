"""Staged piezoelectric coupled-field model (Agent 06, RSCS2-E.5).

Linear piezoelectricity in stress-charge (e-) form, quasi-static
electric field (IEEE 176):

    sigma = C : S - e^T . E        D = e : S + eps . E        E = -grad(phi)

Weak/block form (symmetric indefinite saddle system):

    [ K_uu   K_up ] [u  ]   [f]
    [ K_up^T -K_pp] [phi] = [q]

    K_uu(v,u)   = int S(v) : C : S(u)
    K_up(v,phi) = int e_kij S_ij(v) d_k(phi)
    K_pp(p,phi) = int d_k(p) eps_kl d_l(phi)

Modal problems eliminate phi (no free charge) by static condensation:

    K_eff = K_uu + K_up Kpp_free^-1 K_up^T     (piezoelectric stiffening)

Electrode cases (RSCS2-B.5 electrical boundaries):
  * SHORT-circuit: phi = 0 on both electrode surfaces (Dirichlet), the
    remaining phi DoFs condensed -> less stiffening, lower frequencies.
  * OPEN-circuit: one ground node only (gauge fix), everything else
    charge-free -> maximum stiffening, f_open >= f_short.
  * Effective coupling per mode: k_eff^2 = (f_o^2 - f_s^2) / f_o^2.

Validation battery (tests/v4/test_rscs2_piezo.py): zero-e exact
reduction to elastic FEM; block symmetry + reciprocity; single-element
energy patch vs closed-form tensor arithmetic; electrode antisymmetry;
open >= short; convergence; frame invariance. No accuracy claim beyond
the supplied material tensors and boundary conditions.
"""

from __future__ import annotations

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import eigsh, spsolve
from skfem import Basis, BilinearForm, ElementTetP2, ElementVector, MeshTet
from skfem.helpers import ddot, dot, grad, sym_grad

from .fem import ElasticProblem, RIGID_MODE_TOL_HZ
from .quartz import quartz_dielectric_f_m, quartz_piezo_tensor_c_m2

__all__ = ["PiezoProblem", "assemble_piezo", "solve_piezo_modes",
           "coupling_factor", "static_potential_response"]


class PiezoProblem:
    """Assembled coupled blocks over a shared tetrahedral mesh."""

    def __init__(self, mesh: MeshTet, c_full: np.ndarray,
                 e_full: np.ndarray, eps: np.ndarray,
                 density_kg_m3: float):
        c = np.asarray(c_full, float)
        e = np.asarray(e_full, float)
        ep = np.asarray(eps, float)
        if c.shape != (3, 3, 3, 3) or e.shape != (3, 3, 3) \
                or ep.shape != (3, 3):
            raise ValueError("tensor shapes: C(3,3,3,3) e(3,3,3) eps(3,3)")
        if np.any(np.linalg.eigvalsh(ep) <= 0):
            raise ValueError("dielectric tensor must be SPD")
        self.mesh = mesh
        self.u_basis = Basis(mesh, ElementVector(ElementTetP2()))
        self.p_basis = Basis(mesh, ElementTetP2())
        self.density_kg_m3 = float(density_kg_m3)

        @BilinearForm
        def kuu(u, v, w):
            sigma = np.einsum("ijkl,kl...->ij...", c, sym_grad(u))
            return ddot(sigma, sym_grad(v))

        @BilinearForm
        def muu(u, v, w):
            return density_kg_m3 * dot(u, v)

        @BilinearForm
        def kup(phi, v, w):
            # trial: scalar phi; test: vector v.
            # e_kij S_ij(v) d_k(phi)
            s_v = sym_grad(v)
            return np.einsum("kij,k...,ij...->...", e, grad(phi), s_v)

        @BilinearForm
        def kpp(phi, p, w):
            return np.einsum("k...,kl,l...->...", grad(p), ep, grad(phi))

        self.Kuu = kuu.assemble(self.u_basis)
        self.M = muu.assemble(self.u_basis)
        # rectangular block: rows = u test space, cols = phi trial space
        self.Kup = BilinearForm.assemble(kup, self.p_basis, self.u_basis)
        self.Kpp = kpp.assemble(self.p_basis)
        self.c_full, self.e_full, self.eps = c, e, ep

    # -- electrode helpers ------------------------------------------

    def electrode_dofs(self, predicate) -> np.ndarray:
        return self.p_basis.get_dofs(predicate).flatten()

    def condensed_stiffness(self, grounded_phi: np.ndarray) -> sp.csr_matrix:
        """K_eff = Kuu + Kup_f Kpp_ff^-1 Kup_f^T with the given phi DoFs
        grounded (Dirichlet 0). At least one DoF must be grounded (gauge).
        """
        npd = self.p_basis.N
        grounded = np.unique(np.asarray(grounded_phi, dtype=int))
        if grounded.size == 0:
            raise ValueError("ground at least one phi DoF (gauge)")
        free = np.setdiff1d(np.arange(npd), grounded)
        Kpp_ff = self.Kpp[free][:, free].tocsc()
        Kup_f = self.Kup[:, free].tocsc()
        X = spsolve(Kpp_ff, Kup_f.T.toarray())      # dense RHS block
        Keff = self.Kuu + sp.csr_matrix(Kup_f @ X)
        return Keff.tocsr()


def assemble_piezo(mesh: MeshTet, c_full, density_kg_m3: float,
                   e_full=None, eps=None) -> PiezoProblem:
    """Quartz defaults for the electrical tensors (Agent 04 record)."""
    e = quartz_piezo_tensor_c_m2() if e_full is None else e_full
    ep = quartz_dielectric_f_m() if eps is None else eps
    return PiezoProblem(mesh, c_full, e, ep, density_kg_m3)


def solve_piezo_modes(prob: PiezoProblem, n_modes: int,
                      electrodes, condition: str = "short",
                      fixed_u=None) -> dict:
    """Coupled modes with electrode condition 'short' (phi=0 on ALL
    electrode surfaces) or 'open' (single gauge node only)."""
    all_el = np.concatenate([prob.electrode_dofs(p) for p in electrodes]) \
        if electrodes else np.array([], dtype=int)
    if condition == "short":
        if all_el.size == 0:
            raise ValueError("short circuit needs electrode surfaces")
        grounded = all_el
    elif condition == "open":
        # gauge: ground exactly one DoF (first electrode DoF or DoF 0)
        grounded = np.array([all_el[0] if all_el.size else 0])
    else:
        raise ValueError("condition must be 'short' or 'open'")
    Keff = prob.condensed_stiffness(grounded)
    M = prob.M
    if fixed_u is not None and len(fixed_u):
        keep = np.setdiff1d(np.arange(prob.u_basis.N), fixed_u)
        Keff = Keff[keep][:, keep]
        M = M[keep][:, keep]
    k = min(n_modes, Keff.shape[0] - 2)
    v0 = np.full(Keff.shape[0], 1.0 / np.sqrt(Keff.shape[0]))  # V4-D-003
    vals, vecs = eigsh(Keff, k=k, M=M, sigma=0.0, which="LM", v0=v0)
    order = np.argsort(vals)
    freqs = np.sqrt(np.clip(vals[order], 0, None)) / (2 * np.pi)
    rigid = freqs < RIGID_MODE_TOL_HZ
    return {"frequencies_hz": freqs,
            "elastic_frequencies_hz": freqs[~rigid],
            "n_rigid_modes": int(rigid.sum()),
            "modes": vecs[:, order]}


def coupling_factor(f_open_hz: float, f_short_hz: float) -> float:
    """Effective electromechanical coupling
    k_eff^2 = (f_o^2 - f_s^2)/f_o^2 (IEEE 176 resonance definition)."""
    fo2, fs2 = f_open_hz ** 2, f_short_hz ** 2
    if fo2 <= 0:
        raise ValueError("f_open must be positive")
    return (fo2 - fs2) / fo2


def static_potential_response(prob: PiezoProblem, electrode_plus,
                              electrode_minus, volts: float,
                              fixed_u) -> dict:
    """Static drive: phi = +V/2, -V/2 on the electrodes; solve the full
    saddle system for displacement + potential. Used for the electrode-
    reversal sign test and field visualization."""
    nu_, np_ = prob.u_basis.N, prob.p_basis.N
    dp = prob.electrode_dofs(electrode_plus)
    dm = prob.electrode_dofs(electrode_minus)
    K = sp.bmat([[prob.Kuu, prob.Kup], [prob.Kup.T, -prob.Kpp]],
                format="csr")
    rhs = np.zeros(nu_ + np_)
    x = np.zeros(nu_ + np_)
    x[nu_ + dp] = volts / 2.0
    x[nu_ + dm] = -volts / 2.0
    fixed = np.concatenate([np.asarray(fixed_u, dtype=int),
                            nu_ + dp, nu_ + dm])
    free = np.setdiff1d(np.arange(nu_ + np_), fixed)
    rhs_f = rhs[free] - K[free][:, fixed] @ x[fixed]
    x[free] = spsolve(K[free][:, free].tocsc(), rhs_f)
    return {"u": x[:nu_], "phi": x[nu_:]}
