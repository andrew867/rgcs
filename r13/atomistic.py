"""P08 — a small atomistic lattice-dynamics (phonon) model.

This is a **mass-and-spring dynamical-matrix** model of a 1-D lattice, not
a first-principles calculation. Atoms sit in a periodic chain, connected
to their nearest neighbours by harmonic springs; the equations of motion,
Fourier-transformed to wavevector ``k``, give a Hermitian **dynamical
matrix** ``D(k)`` whose eigenvalues are the squared phonon frequencies.
Diagonalizing ``D(k)`` over the Brillouin zone gives the dispersion.

The two textbook cases are implemented and tested against their closed
forms:

* **Monatomic chain** (one mass ``m``, spring ``K``, spacing ``a``):
  ``omega(k) = 2 sqrt(K/m) |sin(k a / 2)|``, a single acoustic branch
  with ``omega(0) = 0`` -- the acoustic sum rule / translational
  invariance, since a rigid shift of the whole chain costs no energy.
* **Diatomic chain** (masses ``m1, m2``, spring ``K``): an acoustic and an
  optical branch separated by a gap. At the zone boundary ``k = pi/a`` the
  branch edges are ``sqrt(2K/m2)`` (top of acoustic) and ``sqrt(2K/m1)``
  (bottom of optical) for ``m1 < m2``; the acoustic branch tends to zero
  as ``k -> 0``.

**The acoustic sum rule is enforced, not assumed.** The rows of the
force-constant matrix must sum to zero: a uniform translation of every
atom produces no restoring force, so ``omega = 0`` at ``k = 0`` for the
acoustic branch. :func:`enforce_acoustic_sum_rule` sets each on-site term
to minus the sum of its couplings and :func:`acoustic_sum_rule_holds`
checks it.

**This is a toy force-constant model.** The springs here are chosen
constants; they are NOT the interatomic force constants of real
alpha-quartz. A real quartz phonon spectrum needs force constants from a
DFT/DFPT calculation, which this module does not perform and which is
carried as a ``BLOCKED_MISSING_INPUT`` receipt -- the Euphonic phase P31
handles that lane separately. :func:`refuse_toy_model_as_real_spectrum`
refuses to read any frequency here as a real quartz phonon mode. The
default verdict is ``ATOMISTIC_PHONON_MODEL_ANALYTIC``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

# --- verdict, claim classes ----------------------------------------------

DEFAULT_VERDICT = "ATOMISTIC_PHONON_MODEL_ANALYTIC"

#: What this module computes: an analytic lattice-dynamics model.
CLAIM_CLASS = "ANALYTIC_MODEL"

#: The claim classes a statement in this module may declare.
CLAIM_CLASSES = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "CONVENTIONAL_LITERATURE",
    "DERIVED_ARITHMETIC",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "SOURCE_CLAIM",
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_INPUT",
)

#: Tolerance for Hermiticity and the acoustic sum rule (floating precision).
PHONON_TOL = 1e-9


class AtomisticError(RuntimeError):
    """Raised when a lattice-dynamics claim exceeds what the model licenses.

    Covers the structural refusals (non-positive mass or spring, a
    non-square force-constant matrix) and the load-bearing governance
    refusal :func:`refuse_toy_model_as_real_spectrum`.
    """


def _positive(value: float, what: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise AtomisticError(f"{what} must be finite")
    if x <= 0.0:
        raise AtomisticError(f"{what} must be positive")
    return x


# --- the general dynamical-matrix builder --------------------------------

def dynamical_matrix(k: float, masses, springs, a: float = 1.0) -> np.ndarray:
    """The Hermitian dynamical matrix ``D(k)`` of a 1-D chain.

    ``masses`` is a length-``N`` basis of atomic masses; ``springs`` is a
    length-``N`` list of nearest-neighbour force constants, where
    ``springs[i]`` couples atom ``i`` to atom ``(i+1) mod N``. The single
    wrap-around spring (``i = N-1`` back to atom ``0``) crosses the cell
    boundary and carries the Bloch phase ``exp(i k a)``.

    Each spring contributes a positive-semidefinite term, so ``D(k)`` is
    Hermitian with real, non-negative eigenvalues -- the squared phonon
    frequencies. ``N = 1`` reproduces the monatomic chain and ``N = 2``
    the diatomic chain.
    """
    m = np.asarray(masses, dtype=float)
    kappa = np.asarray(springs, dtype=float)
    if m.ndim != 1 or m.size < 1:
        raise AtomisticError("masses must be a non-empty 1-D sequence")
    if kappa.shape != m.shape:
        raise AtomisticError("there must be one spring per atom in the basis")
    if np.any(m <= 0.0):
        raise AtomisticError("every mass must be positive")
    if np.any(kappa <= 0.0):
        raise AtomisticError("every spring constant must be positive")
    aa = _positive(a, "the lattice constant a")
    n = m.size
    D = np.zeros((n, n), dtype=complex)
    for i in range(n):
        j = (i + 1) % n
        crosses = (i + 1) >= n              # the wrap spring crosses the cell
        R = aa if crosses else 0.0
        phase = complex(math.cos(k * R), math.sin(k * R))   # exp(i k R)
        kij = kappa[i]
        norm = math.sqrt(m[i] * m[j])
        D[i, i] += kij / m[i]
        D[j, j] += kij / m[j]
        D[i, j] += -kij * phase.conjugate() / norm          # exp(-i k R)
        D[j, i] += -kij * phase / norm                      # exp(+i k R)
    return D


def dispersion(k: float, masses, springs, a: float = 1.0) -> np.ndarray:
    """Phonon frequencies ``omega`` at wavevector ``k``, ascending.

    Diagonalizes the Hermitian ``D(k)`` and returns the square roots of its
    (real, non-negative) eigenvalues. Tiny negative eigenvalues from
    floating error are clipped to zero before the square root.
    """
    D = dynamical_matrix(k, masses, springs, a)
    evals = np.linalg.eigvalsh(D)
    return np.sqrt(np.clip(evals, 0.0, None))


# --- the 1-D chain -------------------------------------------------------

@dataclass(frozen=True)
class Chain1D:
    """A 1-D chain of atoms with nearest-neighbour springs.

    ``masses`` is the per-cell basis (length ``N``); ``springs`` are the
    ``N`` nearest-neighbour force constants; ``a`` is the lattice constant.
    Use :meth:`monatomic` and :meth:`diatomic` for the two textbook cases.
    """

    masses: tuple[float, ...]
    springs: tuple[float, ...]
    a: float = 1.0

    def __post_init__(self) -> None:
        if len(self.masses) != len(self.springs):
            raise AtomisticError("one spring per atom in the basis")
        if len(self.masses) < 1:
            raise AtomisticError("a chain needs at least one atom")
        for mval in self.masses:
            _positive(mval, "a mass")
        for kval in self.springs:
            _positive(kval, "a spring constant")
        _positive(self.a, "the lattice constant a")

    @classmethod
    def monatomic(cls, m: float = 1.0, K: float = 1.0,
                  a: float = 1.0) -> "Chain1D":
        """A single-mass chain: one atom, one spring per cell."""
        return cls(masses=(m,), springs=(K,), a=a)

    @classmethod
    def diatomic(cls, m1: float = 1.0, m2: float = 2.0, K: float = 1.0,
                 a: float = 1.0) -> "Chain1D":
        """A two-mass chain: two atoms, two equal springs per cell."""
        return cls(masses=(m1, m2), springs=(K, K), a=a)

    def dynamical_matrix(self, k: float) -> np.ndarray:
        """The Hermitian dynamical matrix ``D(k)`` of this chain."""
        return dynamical_matrix(k, self.masses, self.springs, self.a)

    def dispersion(self, k: float) -> np.ndarray:
        """The phonon frequencies at ``k``, ascending, by diagonalization."""
        return dispersion(k, self.masses, self.springs, self.a)


# --- analytic dispersions ------------------------------------------------

def monatomic_dispersion(k: float, m: float = 1.0, K: float = 1.0,
                         a: float = 1.0) -> float:
    """``omega(k) = 2 sqrt(K/m) |sin(k a / 2)|`` for the monatomic chain."""
    mm = _positive(m, "the mass m")
    KK = _positive(K, "the spring K")
    aa = _positive(a, "the lattice constant a")
    return 2.0 * math.sqrt(KK / mm) * abs(math.sin(k * aa / 2.0))


def diatomic_dispersion(k: float, m1: float = 1.0, m2: float = 2.0,
                        K: float = 1.0, a: float = 1.0) -> tuple[float, float]:
    """``(acoustic, optical)`` branches of the diatomic chain, analytic.

    ``omega^2 = K (1/m1 + 1/m2) -/+ K sqrt((1/m1 + 1/m2)^2
    - 4 sin^2(k a / 2)/(m1 m2))``, the standard two-branch result.
    """
    mm1 = _positive(m1, "the mass m1")
    mm2 = _positive(m2, "the mass m2")
    KK = _positive(K, "the spring K")
    aa = _positive(a, "the lattice constant a")
    s = math.sin(k * aa / 2.0)
    inv = 1.0 / mm1 + 1.0 / mm2
    disc = inv * inv - 4.0 * s * s / (mm1 * mm2)
    root = math.sqrt(max(disc, 0.0))
    w2_ac = KK * (inv - root)
    w2_op = KK * (inv + root)
    return math.sqrt(max(w2_ac, 0.0)), math.sqrt(max(w2_op, 0.0))


def diatomic_zone_boundary_edges(m1: float = 1.0, m2: float = 2.0,
                                 K: float = 1.0) -> tuple[float, float]:
    """The analytic zone-boundary edges ``(sqrt(2K/m2), sqrt(2K/m1))``.

    For ``m1 < m2`` these are the top of the acoustic branch and the
    bottom of the optical branch at ``k = pi/a``; the gap between them is
    the phonon band gap.
    """
    mm1 = _positive(m1, "the mass m1")
    mm2 = _positive(m2, "the mass m2")
    KK = _positive(K, "the spring K")
    lower = math.sqrt(2.0 * KK / max(mm1, mm2))
    upper = math.sqrt(2.0 * KK / min(mm1, mm2))
    return lower, upper


# --- the acoustic sum rule -----------------------------------------------

def enforce_acoustic_sum_rule(force_constants) -> np.ndarray:
    """Set each on-site term so every row of the matrix sums to zero.

    The acoustic sum rule states ``Phi_ii = - sum_{j != i} Phi_ij``: a
    rigid translation of every atom (a uniform displacement vector) must
    produce no net force, which is what makes the acoustic branch reach
    ``omega = 0`` at ``k = 0``. This zeroes the existing diagonal and
    replaces it with minus the row sum of the off-diagonal couplings.
    """
    phi = np.array(force_constants, dtype=float)
    if phi.ndim != 2 or phi.shape[0] != phi.shape[1]:
        raise AtomisticError("the force-constant matrix must be square")
    off = phi.copy()
    np.fill_diagonal(off, 0.0)
    corrected = off.copy()
    np.fill_diagonal(corrected, -off.sum(axis=1))
    return corrected


def acoustic_sum_rule_holds(force_constants, tol: float = PHONON_TOL) -> bool:
    """True iff every row of the force-constant matrix sums to zero."""
    phi = np.asarray(force_constants, dtype=float)
    if phi.ndim != 2 or phi.shape[0] != phi.shape[1]:
        raise AtomisticError("the force-constant matrix must be square")
    return bool(np.all(np.abs(phi.sum(axis=1)) <= tol))


# --- the load-bearing refusal --------------------------------------------

#: Real quartz force constants are a blocked input, not a missing feature.
REAL_FORCE_CONSTANTS_STATUS = {
    "status": "BLOCKED_MISSING_INPUT",
    "why": ("the interatomic force constants of real alpha-quartz require a "
            "DFT/DFPT calculation (or a fitted interatomic potential) that "
            "this module does not perform; the springs here are chosen "
            "toy constants"),
    "handled_elsewhere": ("the Euphonic phase P31 handles real force "
                          "constants and the quartz phonon spectrum in a "
                          "separate lane"),
}


def refuse_toy_model_as_real_spectrum(*_a, **_k) -> None:
    """A toy spring model is not the real quartz phonon spectrum.

    The dynamical matrix here is built from chosen spring constants, not
    from the interatomic force constants of alpha-quartz. Its frequencies
    are ANALYTIC_MODEL evaluations of a mass-and-spring chain; they are not
    DFT/DFPT results and not a measured phonon dispersion. Reading any
    frequency here as a real quartz phonon mode is refused.
    """
    raise AtomisticError(
        "refused: this is a toy mass-and-spring dynamical-matrix model with "
        "chosen spring constants, not a DFT/DFPT calculation and not a "
        "measured spectrum. Its frequencies are ANALYTIC_MODEL evaluations "
        "of a 1-D chain; a real alpha-quartz phonon spectrum needs "
        "interatomic force constants that are BLOCKED_MISSING_INPUT here "
        "and handled by the Euphonic phase P31. "
        "PHYSICAL_VALIDATION_NOT_CLAIMED.")


# --- the report ----------------------------------------------------------

def atomistic_report() -> dict:
    mono = Chain1D.monatomic(m=1.0, K=1.0, a=1.0)
    di = Chain1D.diatomic(m1=1.0, m2=2.0, K=1.0, a=1.0)
    return {
        "what_this_is": (
            "a small atomistic lattice-dynamics (phonon) model: a "
            "mass-and-spring dynamical matrix D(k) for a 1-D chain, "
            "diagonalized to give the dispersion; the monatomic and "
            "diatomic textbook cases with the acoustic sum rule enforced"),
        "model_type": "mass-and-spring dynamical matrix (NOT DFT/DFPT)",
        "monatomic_dispersion": "omega(k) = 2 sqrt(K/m) |sin(k a / 2)|",
        "diatomic_branches": ("acoustic + optical, gap at the zone boundary; "
                              "edges sqrt(2K/m2) and sqrt(2K/m1)"),
        "acoustic_sum_rule": (
            "force-constant rows sum to zero, so a rigid translation costs "
            "no energy and omega(0) = 0 on the acoustic branch"),
        "monatomic_omega_at_zone_boundary": float(
            mono.dispersion(math.pi)[0]),
        "diatomic_omega_at_gamma": [float(x) for x in di.dispersion(0.0)],
        "real_force_constants": REAL_FORCE_CONSTANTS_STATUS,
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say these frequencies are the phonon modes of real "
            "alpha-quartz: the springs are chosen toy constants, not "
            "interatomic force constants from a DFT/DFPT calculation, which "
            "are BLOCKED_MISSING_INPUT here and handled by the Euphonic "
            "phase P31. Nothing is measured; every frequency is an "
            "ANALYTIC_MODEL evaluation of a mass-and-spring chain, and a "
            "toy force-constant model is not a real phonon spectrum."),
    }
