"""CPU reference FEM solver (RGCS v4, RSCS2-S.1/E.1/E.2/E.3).

The numerical authority (DV4-004): scikit-fem assembly + scipy sparse
generalized eigensolve. Validated against the analytic benchmarks in
`rscs2_core.reference` (see tests/v4/test_rscs2_solver.py):

  * cantilever Euler-Bernoulli frequency  (RSCS2-V.2)
  * mesh convergence                       (RSCS2-V.8)
  * static tip deflection FL^3/(3EI)
  * rigid-body / mass patch tests
  * alpha-quartz Christoffel ladder        (RSCS2-V.6, conservative
    extension: reproduces the frozen rgcs_core.anisotropy wave speed)

V4-D-001 ROOT CAUSE (closed): the original prototype mass form used
``ddot(u, v)`` — the DOUBLE contraction helper for matrix-valued fields —
on vector-valued displacement fields. The einsum contracted the wrong
axes and inflated the mass matrix ~480x, driving all frequencies down by
a mesh-dependent factor. The correct vector mass density is
``rho * dot(u, v)``. A mass patch test (total mass == rho*V) guards this
class of bug permanently.

Component DOF ordering for ElementVector is INTERLEAVED (x,y,z per node),
verified empirically by the constrained-bar plane-wave test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.sparse.linalg import eigsh
from skfem import (Basis, BilinearForm, ElementTetP2, ElementVector,
                   LinearForm, MeshTet, condense, solve)
from skfem.helpers import ddot, dot, sym_grad
from skfem.models.elasticity import linear_elasticity

__all__ = ["box_mesh", "ElasticProblem", "assemble_isotropic",
           "assemble_anisotropic", "solve_modes", "component_dofs",
           "add_elastic_support", "add_surface_mass",
           "harmonic_response", "save_modes", "load_modes",
           "RIGID_MODE_TOL_HZ"]

#: Modes below this frequency on a free body are classified rigid-body.
RIGID_MODE_TOL_HZ = 1.0


def box_mesh(lengths_m: tuple[float, float, float],
             divisions: tuple[int, int, int]) -> MeshTet:
    """Structured tetrahedral box mesh [0,Lx]x[0,Ly]x[0,Lz]."""
    lx, ly, lz = lengths_m
    nx, ny, nz = divisions
    for name, v in (("Lx", lx), ("Ly", ly), ("Lz", lz)):
        if not (np.isfinite(v) and v > 0):
            raise ValueError(f"{name} must be positive and finite")
    if min(nx, ny, nz) < 1:
        raise ValueError("divisions must be >= 1")
    return MeshTet.init_tensor(np.linspace(0, lx, nx + 1),
                               np.linspace(0, ly, ny + 1),
                               np.linspace(0, lz, nz + 1))


@dataclass(frozen=True)
class ElasticProblem:
    """Assembled generalized eigenproblem K u = omega^2 M u."""
    mesh: MeshTet
    basis: Basis
    K: object          # scipy sparse
    M: object          # scipy sparse
    density_kg_m3: float

    @property
    def ndof(self) -> int:
        return self.basis.N

    def dofs_on(self, predicate: Callable) -> np.ndarray:
        """All DOF indices on facets/nodes satisfying predicate(x)."""
        return self.basis.get_dofs(predicate).flatten()

    def total_mass_kg(self) -> float:
        """Mass patch test value: u^T M u for a unit x-translation field
        equals rho * V for a correct consistent mass matrix (the guard
        that would have caught V4-D-001)."""
        u = np.zeros(self.ndof)
        u[component_dofs(self.basis, 0)] = 1.0
        return float(u @ (self.M @ u))


def _vector_basis(mesh: MeshTet) -> Basis:
    return Basis(mesh, ElementVector(ElementTetP2()))


def _mass_form(rho: float) -> BilinearForm:
    @BilinearForm
    def mass(u, v, w):
        # VECTOR fields: dot, NEVER ddot (V4-D-001).
        return rho * dot(u, v)
    return mass


def assemble_isotropic(mesh: MeshTet, youngs_pa: float, poisson: float,
                       density_kg_m3: float) -> ElasticProblem:
    """Isotropic linear elasticity (RSCS2-E.1/E.2): K from the tested
    skfem `linear_elasticity` model, consistent mass M = rho <u,v>."""
    if not (0 < poisson < 0.5):
        raise ValueError("poisson must be in (0, 0.5)")
    lam = youngs_pa * poisson / ((1 + poisson) * (1 - 2 * poisson))
    mu = youngs_pa / (2 * (1 + poisson))
    basis = _vector_basis(mesh)
    K = linear_elasticity(lam, mu).assemble(basis)
    M = _mass_form(density_kg_m3).assemble(basis)
    return ElasticProblem(mesh, basis, K, M, density_kg_m3)


def assemble_anisotropic(mesh: MeshTet, c_full_pa: np.ndarray,
                         density_kg_m3: float) -> ElasticProblem:
    """Anisotropic linear elasticity (RSCS2-E.1/E.3): sigma_ij =
    C_ijkl eps_kl with a full 3x3x3x3 stiffness tensor (expand a Voigt
    matrix with the frozen `rscs_core.propagation.voigt_to_tensor`)."""
    c = np.asarray(c_full_pa, dtype=float)
    if c.shape != (3, 3, 3, 3) or not np.all(np.isfinite(c)):
        raise ValueError("c_full_pa must be a finite 3x3x3x3 tensor")

    @BilinearForm
    def aniso(u, v, w):
        sigma = np.einsum("ijkl,kl...->ij...", c, sym_grad(u))
        return ddot(sigma, sym_grad(v))

    basis = _vector_basis(mesh)
    K = aniso.assemble(basis)
    M = _mass_form(density_kg_m3).assemble(basis)
    return ElasticProblem(mesh, basis, K, M, density_kg_m3)


def component_dofs(basis: Basis, component: int) -> np.ndarray:
    """DOF indices of one displacement component (0=x, 1=y, 2=z).
    ElementVector DOFs are interleaved per node (empirically verified by
    the plane-wave constrained-bar test)."""
    if component not in (0, 1, 2):
        raise ValueError("component must be 0, 1 or 2")
    return np.arange(basis.N)[np.arange(basis.N) % 3 == component]


def solve_modes(problem: ElasticProblem, n_modes: int,
                fixed_dofs: np.ndarray | None = None) -> dict:
    """Solve K u = omega^2 M u for the lowest ``n_modes`` (RSCS2-S.1).

    Free bodies (no fixed_dofs) include rigid-body modes; they are
    detected (< RIGID_MODE_TOL_HZ) and reported separately, never mixed
    silently into the elastic spectrum (RSCS2-S.2). Modes are
    mass-orthonormalized by eigsh; residuals are reported per mode
    (RSCS2-S.4)."""
    if n_modes < 1:
        raise ValueError("n_modes must be >= 1")
    K, M = problem.K, problem.M
    if fixed_dofs is not None and len(fixed_dofs):
        Kc, Mc = condense(K, M, D=np.asarray(fixed_dofs), expand=False)
    else:
        Kc, Mc = K, M
    k = min(n_modes, Kc.shape[0] - 2)
    # deterministic ARPACK start vector (V4-D-003): the default random
    # v0 makes eigenpairs jitter ~1e-10 between calls, breaking
    # bit-reproducible artifacts
    v0 = np.full(Kc.shape[0], 1.0 / np.sqrt(Kc.shape[0]))
    vals, vecs = eigsh(Kc, k=k, M=Mc, sigma=0.0, which="LM", v0=v0)
    order = np.argsort(vals)
    vals, vecs = vals[order], vecs[:, order]
    freqs = np.sqrt(np.clip(vals, 0.0, None)) / (2 * np.pi)
    rigid = freqs < RIGID_MODE_TOL_HZ
    # residuals ||K u - w^2 M u|| / ||w^2 M u|| — meaningful only for
    # ELASTIC modes (for rigid modes both terms ~0: reported as NaN)
    residuals = np.full(k, np.nan)
    for i in range(k):
        if rigid[i]:
            continue
        lhs = Kc @ vecs[:, i] - vals[i] * (Mc @ vecs[:, i])
        denom = np.linalg.norm(vals[i] * (Mc @ vecs[:, i]))
        residuals[i] = np.linalg.norm(lhs) / denom if denom > 0 else np.inf
    # mass-orthonormality check (RSCS2-S.3): eigsh returns M-orthonormal
    # vectors; verify and report the worst off-diagonal
    gram = vecs.T @ (Mc @ vecs)
    ortho_err = float(np.max(np.abs(gram - np.eye(k))))
    if fixed_dofs is not None and len(fixed_dofs):
        # expand condensed eigenvectors to full DOF space (zeros at the
        # fixed dofs) so modes are indexable by basis.doflocs
        full = np.zeros((K.shape[0], k))
        free = np.setdiff1d(np.arange(K.shape[0]),
                            np.asarray(fixed_dofs))
        full[free, :] = vecs
        vecs = full
    return {
        "frequencies_hz": freqs,
        "elastic_frequencies_hz": freqs[~rigid],
        "n_rigid_modes": int(np.sum(rigid)),
        "modes": vecs,
        "residuals": residuals,
        "orthonormality_error": ortho_err,
        "ndof": Kc.shape[0],
    }


def add_elastic_support(problem: ElasticProblem,
                        facet_predicate: Callable,
                        stiffness_pa_per_m: float) -> ElasticProblem:
    """RSCS2-B.3 elastic support (Robin BC): distributed springs of
    stiffness k [Pa/m] on the selected facets, added to K.
    k -> infinity approaches the fixed BC; k -> 0 recovers free."""
    from skfem import FacetBasis
    if not (np.isfinite(stiffness_pa_per_m) and stiffness_pa_per_m >= 0):
        raise ValueError("stiffness must be finite and >= 0")
    fb = FacetBasis(problem.mesh, ElementVector(ElementTetP2()),
                    facets=problem.mesh.facets_satisfying(facet_predicate))

    @BilinearForm
    def spring(u, v, w):
        return stiffness_pa_per_m * dot(u, v)

    Ks = spring.assemble(fb)
    return ElasticProblem(problem.mesh, problem.basis, problem.K + Ks,
                          problem.M, problem.density_kg_m3)


def add_surface_mass(problem: ElasticProblem, facet_predicate: Callable,
                     areal_density_kg_m2: float) -> ElasticProblem:
    """RSCS2-B.4 mass loading (hand-loading-equivalent): an added areal
    mass density [kg/m^2] on the selected facets, added to M. Every
    eigenfrequency is non-increasing under added mass (Rayleigh)."""
    from skfem import FacetBasis
    if not (np.isfinite(areal_density_kg_m2) and areal_density_kg_m2 >= 0):
        raise ValueError("areal density must be finite and >= 0")
    fb = FacetBasis(problem.mesh, ElementVector(ElementTetP2()),
                    facets=problem.mesh.facets_satisfying(facet_predicate))

    @BilinearForm
    def addmass(u, v, w):
        return areal_density_kg_m2 * dot(u, v)

    Ma = addmass.assemble(fb)
    return ElasticProblem(problem.mesh, problem.basis, problem.K,
                          problem.M + Ma, problem.density_kg_m3)


def harmonic_response(problem: ElasticProblem, force: np.ndarray,
                      freqs_hz: np.ndarray,
                      fixed_dofs: np.ndarray | None = None,
                      damping_ratio: float = 0.0) -> dict:
    """Driven harmonic response (RSCS2-S.5): solve
    (K - omega^2 M + i*omega*C) u = f per frequency, C = 2*zeta*sqrt(KM)
    approximated as stiffness-proportional Rayleigh damping when zeta>0.
    Returns the displacement amplitude at each frequency (|u| max)."""
    from scipy.sparse.linalg import spsolve
    K, M = problem.K, problem.M
    f = np.asarray(force, dtype=complex)
    if fixed_dofs is not None and len(fixed_dofs):
        D = np.asarray(fixed_dofs)
        keep = np.setdiff1d(np.arange(problem.ndof), D)
        K = K[keep][:, keep]
        M = M[keep][:, keep]
        f = f[keep]
    amps = np.zeros(len(freqs_hz))
    for i, fz in enumerate(np.asarray(freqs_hz, dtype=float)):
        w = 2 * np.pi * fz
        A = (K - w ** 2 * M).astype(complex)
        if damping_ratio > 0:
            A = A + 1j * damping_ratio * w * K / (2 * np.pi)
        u = spsolve(A.tocsc(), f)
        amps[i] = float(np.max(np.abs(u)))
    return {"freqs_hz": np.asarray(freqs_hz, dtype=float),
            "amplitude_max": amps}


def save_modes(result: dict, path) -> None:
    """Deterministic serialization of a solve_modes result (.npz)."""
    np.savez_compressed(
        path,
        frequencies_hz=result["frequencies_hz"],
        modes=result["modes"],
        residuals=result["residuals"],
        n_rigid_modes=np.array([result["n_rigid_modes"]]),
        ndof=np.array([result["ndof"]]),
    )


def load_modes(path) -> dict:
    """Round-trip loader for save_modes output."""
    with np.load(path) as z:
        return {
            "frequencies_hz": z["frequencies_hz"],
            "modes": z["modes"],
            "residuals": z["residuals"],
            "n_rigid_modes": int(z["n_rigid_modes"][0]),
            "ndof": int(z["ndof"][0]),
        }


def static_tip_deflection(youngs_pa: float, poisson: float,
                          density_kg_m3: float,
                          lengths_m: tuple[float, float, float],
                          divisions: tuple[int, int, int],
                          force_n: float = 1.0) -> dict:
    """Cantilever static patch test: distributed -z traction on the free
    end face; returns FEM tip deflection and the analytic FL^3/(3EI)."""
    from skfem import FacetBasis
    lx, ly, lz = lengths_m
    mesh = box_mesh(lengths_m, divisions)
    prob = assemble_isotropic(mesh, youngs_pa, poisson, density_kg_m3)
    fixed = prob.dofs_on(lambda x: np.isclose(x[0], 0.0))
    fb = FacetBasis(mesh, ElementVector(ElementTetP2()),
                    facets=mesh.facets_satisfying(
                        lambda x: np.isclose(x[0], lx)))

    @LinearForm
    def tipload(v, w):
        return -(force_n / (ly * lz)) * v[2]

    f = tipload.assemble(fb)
    x = solve(*condense(prob.K, f, D=fixed))
    zdofs = component_dofs(prob.basis, 2)
    tip_z = zdofs[np.isclose(prob.basis.doflocs[0][zdofs], lx)]
    delta_fem = -float(np.mean(x[tip_z]))
    inertia = ly * lz ** 3 / 12.0
    delta_ana = force_n * lx ** 3 / (3.0 * youngs_pa * inertia)
    return {"delta_fem_m": delta_fem, "delta_analytic_m": delta_ana}
