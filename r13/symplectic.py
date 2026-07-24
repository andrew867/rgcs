"""P13 — phase-space rotation, squeezing and shear as symplectic maps.

This is the unifying transform layer under R13. Rotation, squeezing and
shear all live in the same group, the 2x2 real symplectic group
``Sp(2, R)``: a real 2x2 matrix ``M`` is symplectic exactly when

    M^T J M = J,   J = [[0, 1], [-1, 0]],

and every such ``M`` has determinant one, so every such ``M`` preserves
the phase-space area. Writing the three transforms in one algebra is what
makes it possible to say cleanly what they share -- the area -- and,
more importantly, what they do **not**.

**The load-bearing distinction is rotation versus squeeze.** They are the
same size of matrix and the same determinant, and there the resemblance
stops. This is the identical distinction :func:`r11.modemix.rotation_versus_squeeze`
draws between a Hermitian rotation and a Bogoliubov squeeze, carried into
the covariance language here:

* a **rotation** ``[[cos, -sin], [sin, cos]]`` is orthogonal as well as
  symplectic. It is a passive phase shift: it conserves energy, it
  preserves the quadratic form ``x**2 + p**2``, and acting on a
  covariance matrix it preserves ``trace(cov)`` -- the sum of the two
  quadrature variances -- exactly. It relabels the quadratures and
  changes neither variance's total.
* a **squeeze** ``diag(e^r, e^-r)`` is symplectic but **not** orthogonal.
  It is active and parametric: it amplifies one quadrature variance by
  ``e^(2r)`` and deamplifies the other by ``e^(-2r)``. It does **not**
  preserve ``trace(cov)``; it preserves only ``det(cov)``, the product of
  the variances -- the uncertainty product. Amplifying one quadrature at
  the expense of the other requires parametric gain, which is not
  something a passive phase rotation can do.

* a **shear** ``[[1, s], [0, 1]]`` is symplectic too, and like the
  squeeze it is not orthogonal and does not preserve the trace; it adds a
  multiple of one quadrature to the other.

Because ``det(M) == 1`` for every symplectic map, all three -- and any
product of them -- preserve ``det(cov)``. That single invariant is the
phase-space-area / uncertainty-product statement, and it is the one thing
the whole group agrees on.

Two refusals are load-bearing. :func:`refuse_squeeze_as_rotation` refuses
reading parametric quadrature gain as a passive phase shift: they differ
in exactly the invariant above. :func:`refuse_symplectic_model_as_measurement`
refuses reading any of this arithmetic as a bench result. Nothing here is
measured: no field, no cavity, no homodyne detector exists. Every number
is arithmetic on a declared 2x2 matrix.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim class, tolerances ------------------------------------

#: The standing verdict for this module.
VERDICT = "SYMPLECTIC_TRANSFORMS_ROTATION_SQUEEZE_SHEAR"

#: What this module's output is: arithmetic on a declared model. No
#: apparatus is operated anywhere in it.
CLAIM_CLASS = "ANALYTIC_MODEL"

#: The typed claim vocabulary, exact strings, shared across R13.
CLAIM_CLASSES = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "BLOCKED_MISSING_INPUT",
    "BENCH_MEASUREMENT",
)

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The symplectic form J of Sp(2, R).
J = np.array([[0.0, 1.0], [-1.0, 0.0]], dtype=float)

#: Absolute tolerance on the symplectic identity M^T J M == J and on the
#: determinant being one.
SYMPLECTIC_TOL = 1e-9

#: Absolute tolerance on invariant-preservation checks on a covariance.
INVARIANT_TOL = 1e-9


class SymplecticError(RuntimeError):
    """Raised when a symplectic claim exceeds what the algebra licenses.

    Covers the structural guards (a non-2x2 matrix, a non-symmetric
    covariance) and the two load-bearing refusals:
    :func:`refuse_squeeze_as_rotation` and
    :func:`refuse_symplectic_model_as_measurement`.
    """


# --- validation helpers --------------------------------------------------

def _as_2x2(matrix, what: str) -> np.ndarray:
    """Coerce to a finite real 2x2 matrix, or refuse it."""
    m = np.asarray(matrix, dtype=float)
    if m.shape != (2, 2):
        raise SymplecticError(f"{what} must be a 2x2 matrix, got {m.shape}")
    if not np.all(np.isfinite(m)):
        raise SymplecticError(f"{what} must be finite")
    return m


def _as_covariance(cov) -> np.ndarray:
    """A finite, symmetric 2x2 covariance matrix.

    A covariance matrix is symmetric by construction; an asymmetric 2x2
    is not a covariance and its "variances" would not mean anything.
    """
    c = _as_2x2(cov, "a covariance")
    if not np.allclose(c, c.T, atol=INVARIANT_TOL, rtol=0.0):
        raise SymplecticError(
            "a covariance matrix must be symmetric: an asymmetric 2x2 is "
            "not a covariance and has no well-defined quadrature variances")
    return c


def _finite(value: float, what: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise SymplecticError(f"{what} must be finite")
    return x


# --- (1) the symplectic test ---------------------------------------------

def symplectic_defect(matrix) -> float:
    """``max|M^T J M - J|``: zero for a symplectic matrix."""
    m = _as_2x2(matrix, "a matrix")
    return float(np.max(np.abs(m.T @ J @ m - J)))


def is_symplectic(matrix, tol: float = SYMPLECTIC_TOL) -> bool:
    """True iff ``M^T J M == J`` to tolerance.

    This is the definition of ``Sp(2, R)``: it is what makes ``M`` a
    canonical transformation of the ``(x, p)`` phase plane. A matrix that
    fails it does not preserve the Poisson bracket and is not a phase-space
    map at all.
    """
    return symplectic_defect(matrix) <= float(tol)


def is_orthogonal(matrix, tol: float = SYMPLECTIC_TOL) -> bool:
    """True iff ``M^T M == I`` to tolerance.

    Orthogonality is what separates a passive rotation (orthogonal AND
    symplectic) from an active squeeze or shear (symplectic, NOT
    orthogonal). It is the algebraic face of "conserves energy".
    """
    m = _as_2x2(matrix, "a matrix")
    return bool(np.max(np.abs(m.T @ m - np.eye(2))) <= float(tol))


# --- (2) the three generators --------------------------------------------

def rotation(theta: float) -> np.ndarray:
    """``[[cos t, -sin t], [sin t, cos t]]``: orthogonal and symplectic.

    A passive phase-space rotation by angle ``theta``. It is energy
    conserving: orthogonal, so it preserves ``x**2 + p**2``, and
    symplectic, so it preserves the phase-space area as well. It has
    nothing parametric in it; it relabels the quadratures.
    """
    t = _finite(theta, "the rotation angle")
    c, s = math.cos(t), math.sin(t)
    return np.array([[c, -s], [s, c]], dtype=float)


def squeeze(r: float) -> np.ndarray:
    """``diag(e^r, e^-r)``: symplectic, determinant one, NOT orthogonal.

    An active, parametric squeeze of rapidity ``r``. It stretches the
    ``x`` quadrature by ``e^r`` and compresses the ``p`` quadrature by
    ``e^-r``, so acting on variances it multiplies them by ``e^(2r)`` and
    ``e^(-2r)`` respectively. The product is preserved and the sum is not:
    that is the whole difference from a rotation.
    """
    rho = _finite(r, "the squeezing parameter")
    return np.array([[math.exp(rho), 0.0], [0.0, math.exp(-rho)]],
                    dtype=float)


def shear(s: float) -> np.ndarray:
    """``[[1, s], [0, 1]]``: symplectic, determinant one, NOT orthogonal.

    A shear adds ``s`` times the second quadrature to the first. It is a
    symplectic map -- it preserves the phase-space area -- but like the
    squeeze it is not orthogonal and does not preserve the variance sum.
    """
    return np.array([[1.0, _finite(s, "the shear")], [0.0, 1.0]],
                    dtype=float)


def compose(*maps) -> np.ndarray:
    """The product of symplectic maps, left-to-right, itself symplectic.

    ``compose(A, B, C)`` returns ``A @ B @ C``. The symplectic group is
    closed under multiplication, so the product of symplectic matrices is
    symplectic; this helper exists so that closure can be exercised.
    """
    if not maps:
        raise SymplecticError("compose needs at least one map")
    out = np.eye(2)
    for m in maps:
        out = out @ _as_2x2(m, "a map")
    return out


# --- (3) how a covariance evolves, and what is preserved -----------------

def variance_evolution(matrix, cov) -> np.ndarray:
    """Congruence action of a symplectic map on a covariance: ``M cov M^T``.

    This is how a Gaussian state's covariance transforms under the linear
    map ``M``. The two diagonal entries are the quadrature variances and
    the off-diagonal is their covariance.
    """
    m = _as_2x2(matrix, "a map")
    c = _as_covariance(cov)
    return m @ c @ m.T


def quadrature_variances(cov) -> tuple[float, float]:
    """The two quadrature variances ``(var_x, var_p)`` from the diagonal."""
    c = _as_covariance(cov)
    return (float(c[0, 0]), float(c[1, 1]))


def preserves_trace(matrix, cov, tol: float = INVARIANT_TOL) -> bool:
    """True iff ``M`` leaves ``trace(cov)`` -- the variance sum -- fixed.

    True for a rotation and false for a generic squeeze or shear. The
    variance sum is the ``x**2 + p**2`` invariant, preserved exactly by an
    orthogonal map and by nothing else in the group.
    """
    c = _as_covariance(cov)
    evolved = variance_evolution(matrix, c)
    return bool(abs(np.trace(evolved) - np.trace(c)) <= float(tol))


def preserves_det(matrix, cov, tol: float = INVARIANT_TOL) -> bool:
    """True iff ``M`` leaves ``det(cov)`` -- the uncertainty product -- fixed.

    True for **every** symplectic map, because ``det(M cov M^T) =
    det(M)**2 det(cov)`` and ``det(M) == 1``. This is the phase-space-area
    invariant that the whole group shares.
    """
    c = _as_covariance(cov)
    evolved = variance_evolution(matrix, c)
    return bool(abs(np.linalg.det(evolved) - np.linalg.det(c)) <= float(tol))


def rotation_versus_squeeze(theta: float = 0.4, r: float = 0.4,
                            cov=None) -> dict:
    """The distinction stated on one covariance: rotation vs squeeze.

    Reuses the distinction of :func:`r11.modemix.rotation_versus_squeeze`
    in the covariance language: both maps are symplectic with determinant
    one, both preserve ``det(cov)``, and there the similarity stops. The
    rotation preserves ``trace(cov)`` and leaves the variance sum
    untouched; the squeeze does not -- it drives one variance up and the
    other down while holding the product. Reading the second as the first
    is what :func:`refuse_squeeze_as_rotation` refuses.
    """
    if cov is None:
        cov = np.array([[1.0, 0.0], [0.0, 1.0]], dtype=float)
    c = _as_covariance(cov)
    rot = rotation(theta)
    sqz = squeeze(r)
    rot_cov = variance_evolution(rot, c)
    sqz_cov = variance_evolution(sqz, c)
    vx0, vp0 = quadrature_variances(c)
    rvx, rvp = quadrature_variances(rot_cov)
    svx, svp = quadrature_variances(sqz_cov)
    return {
        "angle": float(theta),
        "squeezing_parameter": float(r),
        "rotation_is_orthogonal": is_orthogonal(rot),
        "squeeze_is_orthogonal": is_orthogonal(sqz),
        "rotation_determinant": float(np.linalg.det(rot)),
        "squeeze_determinant": float(np.linalg.det(sqz)),
        "input_variances": [vx0, vp0],
        "rotation_variances": [rvx, rvp],
        "squeeze_variances": [svx, svp],
        "rotation_preserves_trace": preserves_trace(rot, c),
        "squeeze_preserves_trace": preserves_trace(sqz, c),
        "rotation_preserves_det": preserves_det(rot, c),
        "squeeze_preserves_det": preserves_det(sqz, c),
        "squeeze_amplifies_one_deamplifies_other": bool(
            (svx > vx0 + INVARIANT_TOL and svp < vp0 - INVARIANT_TOL)
            or (svp > vp0 + INVARIANT_TOL and svx < vx0 - INVARIANT_TOL)),
        "note": ("a rotation is a passive phase shift that conserves the "
                 "variance sum; a squeeze is parametric gain that trades "
                 "one quadrature variance for the other at fixed product. "
                 "Same determinant, different invariant, different physics"),
        "measured_here": MEASURED_HERE,
    }


# --- (4) the load-bearing refusals ---------------------------------------

def refuse_squeeze_as_rotation(r: float = 0.4) -> None:
    """Refuse reading a parametric squeeze as a passive phase rotation.

    Always raises. A rotation is orthogonal and preserves the variance
    sum ``x**2 + p**2``; a squeeze is not orthogonal and preserves only
    the variance product. Calling a squeeze a rotation claims that
    parametric quadrature gain is a passive phase shift, which no energy
    ledger permits: the squeeze amplifies one quadrature at the expense of
    the other and demands a pump, and the rotation demands nothing.
    """
    rho = _finite(r, "the squeezing parameter")
    sqz = squeeze(rho)
    raise SymplecticError(
        f"a squeeze diag(e^{rho:g}, e^-{rho:g}) is not a rotation. Both are "
        f"symplectic with determinant one, so both preserve det(cov); that "
        f"is where the resemblance ends. The squeeze is NOT orthogonal "
        f"(M^T M != I, defect "
        f"{float(np.max(np.abs(sqz.T @ sqz - np.eye(2)))):.6g}), it does not "
        f"preserve trace(cov), and it multiplies the two quadrature "
        f"variances by e^(2r) and e^(-2r) -- active, parametric gain that "
        f"requires a pump. A rotation is orthogonal, preserves x**2 + p**2, "
        f"and creates nothing. Reading one as the other confuses a passive "
        f"phase shift with parametric amplification. {VERDICT}")


def refuse_symplectic_model_as_measurement(
        claim: str = "a squeezed state was produced") -> None:
    """Refuse reading this symplectic arithmetic as a bench result.

    Always raises. A symplectic matrix and its action on a covariance are
    linear algebra on a declared model. No field mode, no optical
    parametric amplifier, no homodyne detector and no squeezed light
    exists in this repository, so no variance here was measured below any
    shot-noise reference.
    """
    raise SymplecticError(
        f"refused: {claim!r} is a BENCH_MEASUREMENT claim and this module "
        f"contains none. Sp(2, R) maps, their determinants, and the "
        f"covariance congruence M cov M^T are arithmetic on declared 2x2 "
        f"matrices. Nothing was squeezed, rotated, sheared or detected; no "
        f"apparatus was operated, and a modelled quadrature variance is not "
        f"a measured one. {VERDICT}")


# --- (5) the transform catalogue -----------------------------------------

class Transform(Enum):
    """The three symplectic generators, typed by what they conserve."""

    ROTATION = "ROTATION"
    SQUEEZE = "SQUEEZE"
    SHEAR = "SHEAR"


@dataclass(frozen=True)
class TransformFact:
    """What one generator is, and what it does and does not preserve."""

    transform: Transform
    is_orthogonal: bool
    preserves_variance_sum: bool
    preserves_variance_product: bool
    description: str


TRANSFORM_FACTS: dict[Transform, TransformFact] = {
    Transform.ROTATION: TransformFact(
        Transform.ROTATION, True, True, True,
        "a passive phase-space rotation; orthogonal and symplectic, "
        "energy-conserving, relabels the quadratures without amplifying "
        "either"),
    Transform.SQUEEZE: TransformFact(
        Transform.SQUEEZE, False, False, True,
        "an active parametric squeeze; symplectic but not orthogonal, "
        "amplifies one quadrature variance and deamplifies the other at "
        "fixed product"),
    Transform.SHEAR: TransformFact(
        Transform.SHEAR, False, False, True,
        "a symplectic shear; not orthogonal, adds a multiple of one "
        "quadrature to the other, preserves the phase-space area only"),
}


def transform_fact(transform: Transform) -> TransformFact:
    """The typed facts for one generator."""
    if transform not in TRANSFORM_FACTS:
        raise SymplecticError(f"no facts registered for {transform!r}")
    return TRANSFORM_FACTS[transform]


# --- (6) report ----------------------------------------------------------

def symplectic_report() -> dict:
    """The standing statement of what this module is and is not."""
    rvs = rotation_versus_squeeze()
    return {
        "claim_class": CLAIM_CLASS,
        "what_this_is": (
            "the 2x2 real symplectic group Sp(2, R) and its three "
            "generators -- rotation, squeeze and shear -- with the "
            "covariance congruence M cov M^T and the invariants each map "
            "does and does not preserve"),
        "symplectic_form": J.tolist(),
        "definition": "M is symplectic iff M^T J M == J; then det(M) == 1",
        "generators": {t.value: transform_fact(t).description
                       for t in Transform},
        "rotation_versus_squeeze": rvs,
        "invariants": {
            "shared_by_whole_group": "det(cov), the phase-space area / "
                                     "uncertainty product",
            "rotation_only": "trace(cov), the variance sum x**2 + p**2",
        },
        "firewalls": [
            "a squeeze is not a rotation: parametric quadrature gain is "
            "not a passive phase shift -- refuse_squeeze_as_rotation",
            "a symplectic map and its action on a covariance are "
            "arithmetic, not a bench result -- "
            "refuse_symplectic_model_as_measurement",
        ],
        "verdict": VERDICT,
        "claim_classes": list(CLAIM_CLASSES),
        "evidence_class": "DERIVED_MATHEMATICS",
        "hardware_status": (
            "DEFERRED -- no field mode, cavity, parametric amplifier or "
            "homodyne detector has been built or operated"),
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any state was rotated, squeezed or sheared, "
            "that any quadrature variance was measured, or that squeezing "
            "was observed below any shot-noise reference. Every matrix is a "
            "declared 2x2 and every variance is arithmetic on a declared "
            "covariance. It does not say a squeeze is a rotation: they "
            "share a determinant and an area invariant, and they differ in "
            "orthogonality, in the variance sum, and in whether they need a "
            "pump. It does not say algebraic membership in Sp(2, R) makes "
            "two physical systems the same mechanism."),
    }


__all__ = [
    "VERDICT", "CLAIM_CLASS", "CLAIM_CLASSES", "MEASURED_HERE",
    "PHYSICAL_VALIDATION", "J", "SYMPLECTIC_TOL", "INVARIANT_TOL",
    "SymplecticError",
    "symplectic_defect", "is_symplectic", "is_orthogonal",
    "rotation", "squeeze", "shear", "compose",
    "variance_evolution", "quadrature_variances",
    "preserves_trace", "preserves_det", "rotation_versus_squeeze",
    "refuse_squeeze_as_rotation", "refuse_symplectic_model_as_measurement",
    "Transform", "TransformFact", "TRANSFORM_FACTS", "transform_fact",
    "symplectic_report",
]
