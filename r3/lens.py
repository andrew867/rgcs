"""P01 (A04-A11) — the anisotropic phase lens as an inverse problem.

The "lens" is a linear forward operator L mapping source mode
amplitudes to observed phases/amplitudes through an anisotropic
medium. Everything the R3 inverse-problem contract demands is
mechanical here:

- the forward model is explicit and calibrated (a matrix, not vibes);
- observability is a computed property (rank/conditioning of L);
- inversion is Tikhonov-regularized with the residual/solution
  trade-off reported, never a bare pseudo-inverse;
- the adjoint passes the dot-product test to machine precision, so
  gradients are trustworthy;
- model discrepancy is a declared term, not silently absorbed.

Directionality note (A11): a REAL lens matrix generally differs from
its transpose. L != L^T means forward and reverse transfer differ —
that is ordinary anisotropy and reciprocity-breaking by geometry, not
evidence of exotic one-way physics.
"""

from __future__ import annotations

import numpy as np

from . import ClaimBoundaryError


def make_lens(n_modes: int, n_obs: int, anisotropy: float = 0.5,
              seed: int = 20260718) -> np.ndarray:
    """A deterministic synthetic anisotropic lens operator."""
    rng = np.random.default_rng(seed)
    base = rng.standard_normal((n_obs, n_modes))
    skew = rng.standard_normal((n_obs, n_modes)) * anisotropy
    return base + skew


def observability(L: np.ndarray, cond_limit: float = 1e8) -> dict:
    """A06: what the observation geometry can actually see."""
    sv = np.linalg.svd(L, compute_uv=False)
    rank = int(np.sum(sv > sv[0] * 1e-12))
    cond = float(sv[0] / sv[-1]) if sv[-1] > 0 else np.inf
    return {"n_modes": L.shape[1], "n_obs": L.shape[0],
            "rank": rank, "condition_number": cond,
            "fully_observable": rank == L.shape[1] and
            cond < cond_limit,
            "null_space_dim": L.shape[1] - rank,
            "evidence_class": "NUMERICAL_SIMULATION"}


def invert(L: np.ndarray, y: np.ndarray, lam: float = 1e-3) -> dict:
    """A07: Tikhonov inversion min ||Lx - y||^2 + lam*||x||^2."""
    if lam <= 0:
        raise ClaimBoundaryError(
            "unregularized inversion refused: lam must be positive so "
            "the null space cannot masquerade as signal")
    n = L.shape[1]
    A = L.conj().T @ L + lam * np.eye(n)
    x = np.linalg.solve(A, L.conj().T @ y)
    resid = float(np.linalg.norm(L @ x - y))
    return {"estimate": x, "residual_norm": resid,
            "solution_norm": float(np.linalg.norm(x)),
            "lambda": lam,
            "note": "estimate is the regularized minimizer, biased "
                    "toward small norm by construction",
            "evidence_class": "NUMERICAL_SIMULATION"}


def adjoint_test(L: np.ndarray, seed: int = 7) -> dict:
    """A08: <Lx, y> == <x, L*y> to machine precision, or the gradient
    machinery is wrong."""
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(L.shape[1])
    y = rng.standard_normal(L.shape[0])
    lhs = float(np.dot(L @ x, y))
    rhs = float(np.dot(x, L.T @ y))
    rel = abs(lhs - rhs) / max(abs(lhs), 1e-30)
    return {"lhs": lhs, "rhs": rhs, "relative_error": rel,
            "passes": rel < 1e-12}


def discrepancy_budget(calibration_residual: float,
                       noise_sigma: float) -> dict:
    """A09: the declared model-error term. A fit better than the
    discrepancy budget is overfitting, not brilliance."""
    floor = float(np.hypot(calibration_residual, noise_sigma))
    return {"calibration_residual": calibration_residual,
            "noise_sigma": noise_sigma,
            "residual_floor": floor,
            "note": "residuals below the floor indicate overfitting "
                    "or an inverse crime, not a better model"}


def directionality(L: np.ndarray) -> dict:
    """A11: forward-vs-reverse asymmetry, honestly labelled."""
    asym = float(np.linalg.norm(L - L.T) / np.linalg.norm(L)) \
        if L.shape[0] == L.shape[1] else None
    return {"transpose_asymmetry": asym,
            "meaning": "L != L^T is ordinary geometric anisotropy; it "
                       "is NOT evidence of exotic one-way physics, "
                       "and it vanishes under the reversed-orientation "
                       "control unless the medium itself is chiral",
            "evidence_class": "NUMERICAL_SIMULATION"}
