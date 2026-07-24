"""P09 — atomistic force constants to a continuum elastic model.

The atomistic picture and the continuum picture of a solid are not rivals;
one is the long-wavelength limit of the other. A lattice is a set of
masses joined by force constants, and its normal modes have a dispersion
``omega(k)`` that curves and folds at the Brillouin-zone edge. A continuum
is an elastic body with a stiffness tensor, and its acoustic waves have a
straight dispersion ``omega = c*k``. **Homogenization** is the statement
that the second is the ``k -> 0`` slope of the first: on wavelengths long
compared with the lattice spacing the discrete chain cannot be told apart
from the elastic rod, and the continuum sound speed is exactly the initial
slope of the atomistic branch.

Three homogenizations are carried here, each with its own load-bearing
identity.

* **The acoustic limit.** A monatomic 1-D chain with force constant ``K``,
  mass ``m`` and spacing ``a`` has ``omega(k) = 2 sqrt(K/m) |sin(k a/2)|``.
  Its slope at ``k = 0`` is ``a sqrt(K/m)``, and that is the continuum
  sound speed :func:`sound_speed_from_chain`. :func:`long_wavelength_slope`
  extracts the slope of an arbitrary dispersion at the zone centre, and the
  two agree — the continuum wave speed is not assumed, it is read off the
  atomistic branch.

* **Effective stiffness.** A periodic composite of two alternating springs
  ``K1`` and ``K2`` homogenizes to the harmonic (series-spring) mean
  ``2/(1/K1 + 1/K2)``. The soft spring dominates, as a series combination
  must, and an identical pair recovers its own constant.

* **The elastic tensor.** :class:`ContinuumElastic` carries a 6x6 Voigt
  stiffness in the trigonal (class 32) symmetry pattern of alpha-quartz.
  The *pattern* — which entries are zero, which are equal, which are
  negatives of each other, and ``C66 = (C11 - C12)/2`` — is exact crystal
  symmetry. The *magnitudes* are conventional literature placeholders,
  marked ``CONVENTIONAL_LITERATURE``, not fitted to any measurement here.
  Given a direction ``n`` and a density ``rho`` the Christoffel matrix
  ``Gamma_ik = C_ijkl n_j n_l / rho`` has three non-negative eigenvalues
  whose square roots are the three acoustic velocities of that direction.

**The bridge is a model, not a measurement.** Homogenizing a toy chain or
a literature stiffness tensor produces continuum parameters that describe
the model, not a specimen. :func:`refuse_homogenized_as_measured` refuses
to read any homogenized modulus, sound speed or velocity as a bench
result. Nothing here is measured: no crystal exists, no wave is launched,
and every number is arithmetic on a declared model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Callable

import numpy as np

# --- verdict, claim classes, tolerances ---------------------------------

DEFAULT_VERDICT = "ATOMISTIC_TO_CONTINUUM_HOMOGENIZED_ANALYTIC"

#: What this module's own output is. The homogenization arithmetic and the
#: acoustic-limit identities are an ANALYTIC_MODEL; the quartz stiffness
#: magnitudes are conventional literature, carried as a placeholder.
CLAIM_CLASS = "ANALYTIC_MODEL"

#: The stiffness magnitudes are not fitted or measured here.
STIFFNESS_PROVENANCE = "CONVENTIONAL_LITERATURE"

PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Relative tolerance on the acoustic-limit identity (chain slope vs c).
ACOUSTIC_TOL = 1e-6


class HomogenizeError(RuntimeError):
    """Raised when a homogenization claim exceeds what the model licenses.

    Covers the structural refusals (a non-positive force constant or mass,
    a stiffness matrix that is not 6x6 or not symmetric, a null direction)
    and the load-bearing governance refusal
    :func:`refuse_homogenized_as_measured`.
    """


def _positive(value: float, what: str) -> float:
    """Coerce to float and refuse anything non-positive or non-finite."""
    x = float(value)
    if not math.isfinite(x):
        raise HomogenizeError(f"{what} must be finite")
    if x <= 0.0:
        raise HomogenizeError(f"{what} must be positive")
    return x


# --- (1) the acoustic limit ----------------------------------------------

def sound_speed_from_chain(K: float, m: float, a: float) -> float:
    """Continuum sound speed of a monatomic 1-D chain: ``c = a sqrt(K/m)``.

    This is the ``k -> 0`` slope of the chain dispersion
    ``omega(k) = 2 sqrt(K/m) |sin(k a/2)|``. It is the speed at which a
    long-wavelength acoustic disturbance travels down the chain, and it is
    what the continuum elastic rod of the same linear density and modulus
    reproduces.
    """
    kk = _positive(K, "the force constant K")
    mm = _positive(m, "the mass m")
    aa = _positive(a, "the lattice spacing a")
    return aa * math.sqrt(kk / mm)


def chain_dispersion(K: float, m: float, a: float) -> Callable[[float], float]:
    """The monatomic-chain branch ``omega(k) = 2 sqrt(K/m) |sin(k a/2)|``.

    Returned as a callable of the wavenumber ``k`` so it can be handed to
    :func:`long_wavelength_slope` without the slope routine knowing where
    the dispersion came from.
    """
    kk = _positive(K, "the force constant K")
    mm = _positive(m, "the mass m")
    aa = _positive(a, "the lattice spacing a")
    omega_max = 2.0 * math.sqrt(kk / mm)

    def omega(k: float) -> float:
        return omega_max * abs(math.sin(0.5 * float(k) * aa))

    return omega


def long_wavelength_slope(omega_func: Callable[[float], float],
                          k0: float = 1e-3) -> float:
    """The zone-centre slope ``d(omega)/dk`` at ``k -> 0`` of a dispersion.

    ``omega_func`` is any acoustic branch with ``omega(0) = 0``. Because
    ``omega(k)/k = c (1 - alpha k^2 + ...)`` for such a branch, the finite
    ratio at a small ``k`` still carries an ``O(k^2)`` error; a Richardson
    step across ``k0`` and ``2 k0`` cancels that leading term, so the slope
    is returned to high accuracy rather than merely approximated.
    """
    k = _positive(k0, "the probe wavenumber k0")
    if abs(float(omega_func(0.0))) > 1e-12:
        raise HomogenizeError(
            "long_wavelength_slope expects an ACOUSTIC branch with "
            "omega(0) == 0; a branch with a gap at k == 0 is optical and "
            "has no continuum sound speed")
    s1 = float(omega_func(k)) / k
    s2 = float(omega_func(2.0 * k)) / (2.0 * k)
    return (4.0 * s1 - s2) / 3.0


# --- (2) effective stiffness of a periodic composite ---------------------

def effective_stiffness_series(K1: float, K2: float) -> float:
    """Homogenized modulus of two alternating springs: ``2/(1/K1 + 1/K2)``.

    A period holds one ``K1`` and one ``K2`` in series, and springs in
    series add compliances, not stiffnesses. The harmonic mean is the
    result: it is dominated by the softer spring, equals the closed form
    ``2 K1 K2 / (K1 + K2)``, and collapses to ``K`` when ``K1 == K2``. A
    naive arithmetic mean would over-stiffen the composite, which is the
    error this homogenization exists to avoid.
    """
    a = _positive(K1, "the first spring constant K1")
    b = _positive(K2, "the second spring constant K2")
    return 2.0 / (1.0 / a + 1.0 / b)


# --- (3) the continuum elastic tensor ------------------------------------

class VoigtSymmetry(Enum):
    """The crystal symmetry class a Voigt stiffness pattern encodes."""

    TRIGONAL_32 = "trigonal_32"


#: Conventional literature stiffness constants of alpha-quartz (class 32),
#: in GPa. These are CONVENTIONAL_LITERATURE placeholder magnitudes used to
#: populate the symmetry pattern; they are not fitted or measured here, and
#: the module never claims them as a specimen's constants.
QUARTZ_C11 = 86.74
QUARTZ_C12 = 6.99
QUARTZ_C13 = 11.91
QUARTZ_C14 = -17.91
QUARTZ_C33 = 107.2
QUARTZ_C44 = 57.94

#: Conventional literature density of alpha-quartz, kg/m^3 (placeholder).
QUARTZ_DENSITY = 2648.0


def trigonal_voigt(c11: float, c12: float, c13: float, c14: float,
                   c33: float, c44: float) -> np.ndarray:
    """Assemble the 6x6 Voigt stiffness of a trigonal (class 32) crystal.

    The pattern is fixed by symmetry and is the whole point: ``C66`` is not
    free but equals ``(C11 - C12)/2``; ``C[3,3] == C[4,4]``; ``C[0,3]`` and
    ``C[1,3]`` are equal and opposite; ``C[4,5] == C[0,3]``; and every
    other off-block entry is zero. The six arguments are the only
    independent constants.
    """
    c66 = 0.5 * (float(c11) - float(c12))
    c = np.zeros((6, 6), dtype=float)
    c11, c12, c13 = float(c11), float(c12), float(c13)
    c14, c33, c44 = float(c14), float(c33), float(c44)
    c[0, 0] = c[1, 1] = c11
    c[0, 1] = c[1, 0] = c12
    c[0, 2] = c[2, 0] = c[1, 2] = c[2, 1] = c13
    c[2, 2] = c33
    c[3, 3] = c[4, 4] = c44
    c[5, 5] = c66
    c[0, 3] = c[3, 0] = c14
    c[1, 3] = c[3, 1] = -c14
    c[4, 5] = c[5, 4] = c14
    return c


@dataclass(frozen=True)
class ContinuumElastic:
    """A continuum elastic body: a 6x6 Voigt stiffness and a density.

    The stiffness carries a declared ``symmetry`` and a declared
    ``provenance``. The default constructor enforces that the matrix is
    square 6x6 and symmetric; :meth:`alpha_quartz` builds the trigonal
    literature placeholder. Every magnitude is a model number in the
    stated units, not a measurement.
    """

    C: np.ndarray
    density: float
    symmetry: VoigtSymmetry = VoigtSymmetry.TRIGONAL_32
    stiffness_units: str = "GPa"
    provenance: str = STIFFNESS_PROVENANCE

    def __post_init__(self) -> None:
        C = np.asarray(self.C, dtype=float)
        if C.shape != (6, 6):
            raise HomogenizeError(
                "a Voigt stiffness must be a 6x6 matrix")
        if not np.allclose(C, C.T):
            raise HomogenizeError(
                "a Voigt stiffness must be symmetric; an asymmetric C "
                "violates the strain-energy quadratic form")
        _positive(self.density, "the density")
        object.__setattr__(self, "C", C)

    @classmethod
    def alpha_quartz(cls) -> "ContinuumElastic":
        """The trigonal (class 32) literature placeholder for alpha-quartz.

        The symmetry pattern is exact; the magnitudes are
        ``CONVENTIONAL_LITERATURE`` and are not a measurement of any
        specimen.
        """
        return cls(
            C=trigonal_voigt(QUARTZ_C11, QUARTZ_C12, QUARTZ_C13,
                             QUARTZ_C14, QUARTZ_C33, QUARTZ_C44),
            density=QUARTZ_DENSITY,
            symmetry=VoigtSymmetry.TRIGONAL_32,
            stiffness_units="GPa",
            provenance=STIFFNESS_PROVENANCE,
        )

    def is_symmetric(self) -> bool:
        return bool(np.allclose(self.C, self.C.T))

    def trigonal_structure_ok(self, tol: float = 1e-12) -> bool:
        """Does ``C`` satisfy the trigonal (class 32) zero/equality pattern?

        Checks the equalities (``C11==C22``, the three ``C13`` copies,
        ``C44==C55``), the antisymmetric pair (``C[0,3] == -C[1,3]`` and
        ``C[4,5] == C[0,3]``), the constrained ``C66 == (C11-C12)/2``, and
        that every entry outside the pattern is zero.
        """
        C = self.C
        allowed = {(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5),
                   (0, 1), (1, 0), (0, 2), (2, 0), (1, 2), (2, 1),
                   (0, 3), (3, 0), (1, 3), (3, 1), (4, 5), (5, 4)}
        for i in range(6):
            for j in range(6):
                if (i, j) not in allowed and abs(C[i, j]) > tol:
                    return False
        checks = (
            abs(C[0, 0] - C[1, 1]) <= tol,
            abs(C[0, 2] - C[1, 2]) <= tol,
            abs(C[0, 2] - C[2, 0]) <= tol,
            abs(C[3, 3] - C[4, 4]) <= tol,
            abs(C[0, 3] + C[1, 3]) <= tol,
            abs(C[4, 5] - C[0, 3]) <= tol,
            abs(C[5, 5] - 0.5 * (C[0, 0] - C[0, 1])) <= tol,
        )
        return all(checks)


# --- (4) the Christoffel equation ----------------------------------------

#: Voigt contraction: a symmetric index pair (i, j) -> a single 0..5 index.
_VOIGT: dict[tuple[int, int], int] = {
    (0, 0): 0, (1, 1): 1, (2, 2): 2,
    (1, 2): 3, (2, 1): 3,
    (0, 2): 4, (2, 0): 4,
    (0, 1): 5, (1, 0): 5,
}


def voigt_to_full(C: np.ndarray) -> np.ndarray:
    """Expand a 6x6 Voigt stiffness to the full ``c_ijkl`` (3x3x3x3)."""
    C = np.asarray(C, dtype=float)
    if C.shape != (6, 6):
        raise HomogenizeError("a Voigt stiffness must be 6x6")
    full = np.zeros((3, 3, 3, 3), dtype=float)
    for i in range(3):
        for j in range(3):
            for k in range(3):
                for m in range(3):
                    full[i, j, k, m] = C[_VOIGT[(i, j)], _VOIGT[(k, m)]]
    return full


def christoffel_matrix(C: np.ndarray, n, rho: float) -> np.ndarray:
    """``Gamma_ik = c_ijkl n_j n_l / rho`` for a propagation direction ``n``.

    ``n`` is normalised first; a null direction is refused. ``Gamma`` is
    symmetric by the symmetry of ``c_ijkl``, so its eigenvalues are real
    and, for a physically stable stiffness, non-negative.
    """
    rr = _positive(rho, "the density rho")
    nv = np.asarray(n, dtype=float)
    if nv.shape != (3,):
        raise HomogenizeError("the direction n must be a 3-vector")
    norm = float(np.linalg.norm(nv))
    if norm <= 0.0:
        raise HomogenizeError(
            "the propagation direction cannot be the null vector")
    nv = nv / norm
    full = voigt_to_full(C)
    gamma = np.einsum("ijkl,j,l->ik", full, nv, nv) / rr
    return 0.5 * (gamma + gamma.T)


def christoffel_velocities(C: np.ndarray, n, rho: float) -> np.ndarray:
    """The three acoustic phase velocities along ``n``.

    The eigenvalues of the Christoffel matrix are ``rho v^2`` for the three
    modes — one quasi-longitudinal and two quasi-transverse. They are real
    (``Gamma`` is symmetric) and non-negative (the stiffness is stable), and
    their square roots are returned ascending. A negative eigenvalue would
    signal a mechanically unstable stiffness and is clipped to zero after a
    tolerance check rather than silently square-rooted into a NaN.

    Units follow the inputs: with ``C`` in Pa, ``rho`` in kg/m^3, the
    velocities are m/s; with ``C`` in GPa they are scaled accordingly and
    are model numbers, not a measured wave speed.
    """
    gamma = christoffel_matrix(C, n, rho)
    lam = np.linalg.eigvalsh(gamma)
    if float(lam.min()) < -1e-9 * max(1.0, float(np.max(np.abs(lam)))):
        raise HomogenizeError(
            "the Christoffel matrix has a negative eigenvalue: the "
            "stiffness is mechanically unstable along this direction and "
            "has no real acoustic velocity")
    return np.sqrt(np.clip(lam, 0.0, None))


# --- (5) the load-bearing refusal ----------------------------------------

def refuse_homogenized_as_measured(
        quantity: str = "a homogenized continuum parameter") -> None:
    """A homogenized modulus, speed or velocity is a model output. Raises.

    Homogenization maps a toy atomistic chain or a literature stiffness
    tensor to continuum parameters. Those parameters describe the model
    that was homogenized, not a crystal on a bench: no specimen was cut,
    no wave was launched, no velocity was timed. Reading the continuum
    sound speed, the effective stiffness or a Christoffel velocity as a
    measurement is exactly the promotion this module refuses.
    """
    raise HomogenizeError(
        f"refused: {quantity!r} is a HOMOGENIZED MODEL output, not a "
        f"measurement. The continuum parameters here are the long-"
        f"wavelength limit of a declared force-constant chain or a "
        f"CONVENTIONAL_LITERATURE stiffness tensor; they are not fitted "
        f"to data and no specimen was cut, driven or timed. A sound speed "
        f"read off an atomistic slope and a sound speed measured on quartz "
        f"are different objects. {PHYSICAL_VALIDATION}.")


# --- (6) the report ------------------------------------------------------

def homogenize_report() -> dict:
    return {
        "what_this_is": (
            "long-wavelength homogenization from an atomistic force-"
            "constant picture to a continuum elastic model: the chain "
            "acoustic limit, the series-spring effective stiffness of a "
            "periodic composite, and a trigonal Voigt stiffness tensor "
            "with its Christoffel acoustic velocities"),
        "load_bearing_identity": (
            "the continuum sound speed c = a sqrt(K/m) is the k -> 0 slope "
            "of the atomistic dispersion omega(k) = 2 sqrt(K/m)|sin(ka/2)|; "
            "the slope is read off the branch, not assumed"),
        "effective_stiffness_rule": (
            "two alternating springs homogenize to the harmonic mean "
            "2/(1/K1 + 1/K2) = 2 K1 K2/(K1+K2), dominated by the softer "
            "spring, recovering K when K1 == K2"),
        "elastic_tensor": {
            "symmetry": VoigtSymmetry.TRIGONAL_32.value,
            "independent_constants": ["C11", "C12", "C13", "C14",
                                      "C33", "C44"],
            "constrained": "C66 == (C11 - C12)/2",
            "magnitudes_provenance": STIFFNESS_PROVENANCE,
        },
        "christoffel": (
            "Gamma_ik = C_ijkl n_j n_l / rho; three real non-negative "
            "eigenvalues rho*v^2 give three acoustic modes per direction"),
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say any crystal exists, that any wave was launched "
            "or timed, or that any modulus, sound speed or Christoffel "
            "velocity was measured. The quartz stiffness magnitudes are "
            "CONVENTIONAL_LITERATURE placeholders populating an exact "
            "symmetry pattern, not a specimen's fitted constants. The "
            "bridge from lattice to continuum is a homogenization of a "
            "declared model, and a homogenized parameter is never a bench "
            "measurement."),
    }
