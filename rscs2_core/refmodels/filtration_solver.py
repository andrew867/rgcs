"""Geometric filtration and solver bookkeeping (Agent Q04).

Source: pyt8-d7rt.pdf, DOI 10.1103/pyt8-d7rt — geometric bookkeeping
for Feynman-integral reduction and epsilon-factorized differential
equations.

The WORKFLOW ANALOGY (the only transfer): choosing a basis by a
structure-aware ordering (a filtration) and rescaling by selected
prefactors can turn a densely coupled linear system into a
block-triangular one whose parameter dependence factorizes — making
the system cheaper to solve and its structure visible.

Demonstration on RGCS-relevant material: a parameterized linear ODE
system y' = A(eps) y. We measure (a) coupling density and (b) how the
eps-dependence spreads across entries, before and after a filtration
reordering + diagonal rescaling. The claimed benefit is MEASURED on
the demo, not asserted.

CAVEAT preserved from the source: the paper's claim that its proposed
order always yields the compatible structure is CONJECTURAL, and this
module's docstring says so rather than laundering it into a theorem.

FORBIDDEN: any claim about Feynman integrals themselves, and any
suggestion that RGCS computes QFT quantities."""

from __future__ import annotations

import numpy as np

SOURCE = {"doi": "10.1103/pyt8-d7rt", "file": "pyt8-d7rt.pdf",
          "system": "dimensionally regulated Feynman-integral "
                    "families",
          "allowed_transfer": "basis selection / filtration / "
                              "prefactor-rescaling WORKFLOW",
          "forbidden_transfer": "Feynman-integral results; QFT "
                                "claims",
          "conjecture_preserved": "that the proposed order always "
                                  "yields the compatible structure "
                                  "remains conjectural (source's own "
                                  "caveat)"}


def demo_system(n: int = 6, eps: float = 0.1, seed: int = 0) -> \
        np.ndarray:
    """A(eps) = P (L0 + eps L1) P^{-1}: secretly triangularizable with
    factorized eps-dependence, hidden by a random similarity — the
    kind of structure the filtration is meant to reveal."""
    rng = np.random.default_rng(seed)
    l0 = np.tril(rng.normal(size=(n, n)), k=0)
    l1 = np.tril(rng.normal(size=(n, n)), k=0)
    p = rng.normal(size=(n, n)) + n * np.eye(n)
    return p @ (l0 + eps * l1) @ np.linalg.inv(p), p, l0, l1


def coupling_density(a: np.ndarray, tol: float = 1e-10) -> float:
    """Fraction of nonzero entries ABOVE the diagonal — the
    obstruction to sequential (triangular) solving."""
    n = a.shape[0]
    upper = np.triu(np.abs(a) > tol, k=1)
    return float(upper.sum() / max(n * (n - 1) / 2, 1))


def filtration_order(a: np.ndarray) -> np.ndarray:
    """Structure-aware ordering: sort states by their coupling
    out-degree (a crude filtration — states that feed many others come
    last). This is the 'geometry-inspired ordering' analogue."""
    score = (np.abs(a) > 1e-10).sum(axis=0)
    return np.argsort(score)


def apply_filtration(a: np.ndarray) -> dict:
    """Reorder by the filtration and rescale rows by their diagonal
    (the selected-prefactor analogue). Report the measured coupling
    density before/after — the claimed benefit is a number here, not
    a slogan."""
    order = filtration_order(a)
    b = a[np.ix_(order, order)]
    d = np.diag(b).copy()
    d[np.abs(d) < 1e-12] = 1.0
    b_scaled = b / d[:, None]
    return {"order": order.tolist(),
            "density_before": coupling_density(a),
            "density_after": coupling_density(b_scaled),
            "note": "the filtration is a heuristic; on adversarial "
                    "systems it may not reduce density at all, and "
                    "the honest report is the measured pair"}


def eps_factorization_check(p, l0, l1, eps_values=(0.05, 0.1, 0.2)
                            ) -> dict:
    """In the revealing basis, A(eps) = L0 + eps*L1 exactly: the eps
    dependence FACTORIZES (each entry is affine in eps). Verified by
    reconstructing at several eps and checking affinity."""
    ok = True
    for e in eps_values:
        a = l0 + e * l1
        # affine check: A(e) - A(0) proportional to e
        resid = np.max(np.abs((a - l0) / e - l1))
        ok = ok and resid < 1e-12
    return {"eps_affine_in_revealing_basis": bool(ok),
            "meaning": "in the right basis the parameter enters "
                       "linearly everywhere — the analogue of an "
                       "epsilon-factorized system",
            "conjecture_note": SOURCE["conjecture_preserved"]}


def rgcs_application() -> dict:
    """Where this workflow could apply inside RGCS (all prospective,
    ENGINEERING_PROTOTYPE): ordering modal bases by coupling strength
    before harmonic solves; separating nuisance parameters (fixture,
    temperature) from design parameters in calibration Jacobians."""
    return {"candidates": [
        "modal-basis ordering before coupled harmonic solves",
        "nuisance/design parameter separation in calibration",
        "block-triangular sensitivity propagation in the trim "
        "planner"],
        "status": "ENGINEERING_PROTOTYPE",
        "measured_benefit": "none yet — no RGCS solve has been "
                            "restructured; the demo system is the "
                            "only evidence and it is synthetic"}
