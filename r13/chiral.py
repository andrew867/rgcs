"""P12 — chiral phonons, as an analytic model.

At the corners of a hexagonal Brillouin zone (the valleys ``K`` and
``K'``) two degenerate lattice modes combine into circular polarizations

    e_± = (e_x ± i e_y) / sqrt(2)

that rotate rather than oscillate along a line. A mode that rotates
carries angular momentum, and this module states the small algebra that
follows:

* **Per-mode angular momentum l_z = ± hbar.** A left- or right-circular
  mode carries ``+hbar`` or ``-hbar`` of phonon angular momentum about
  the propagation axis (up to a lattice form factor); a linearly
  polarized mode carries none. :func:`phonon_angular_momentum` returns
  it, and left and right are exactly equal and opposite.
* **The circular basis is orthonormal and diagonalises the rotation
  generator.** ``e_+`` and ``e_-`` are orthonormal under the Hermitian
  inner product, and each is an eigenvector of the 2-D rotation generator
  ``L = [[0, -i], [i, 0]]`` with eigenvalue ``+1`` and ``-1``
  respectively — which is exactly the statement that they carry definite
  angular momentum.
* **Chirality flips at K versus K'.** The two valleys are time-reversal
  partners, so the same branch carries opposite pseudo-angular-momentum
  at ``K`` and ``K'``. A model that gave them the same sign would break
  time-reversal symmetry by hand.
* **A circular drive addresses one valley.** A circularly polarized drive
  couples to one chirality; :func:`valley_selection` returns which
  valley, and it flips when the drive helicity flips.

The firewall: :func:`refuse_model_chirality_as_measured` refuses to read
any of these computed quantities as a measured circular-dichroism or
phonon-Hall signal. A per-mode angular momentum computed from an
eigenvector is algebra on a declared polarization; an observed chirality
is a bench result — a helicity-resolved cross-section, a measured
dichroic contrast, or a transverse phonon-Hall current. Nothing here is
measured: no lattice exists, no phonon is excited, and every number is a
closed form on a chosen polarization.
"""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim class, constants -------------------------------------

#: The standing verdict for this module.
DEFAULT_VERDICT = "CHIRAL_PHONON_MODEL_ANALYTIC"

#: What this module's output is: closed-form algebra on a declared
#: polarization vector. Not a simulation, not a measurement.
CLAIM_CLASS = "ANALYTIC_MODEL"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Reduced Planck constant, SI (CODATA). Sets the unit of the per-mode
#: angular momentum; no angular momentum here is measured.
HBAR_J_S = 1.054571817e-34

#: Tolerance for orthonormality and eigenvalue checks.
CHIRAL_TOL = 1e-12

#: The 2-D rotation generator (Hermitian), whose eigenvectors are the two
#: circular polarizations with eigenvalues +1 and -1.
ROTATION_GENERATOR = np.array([[0.0, -1.0j], [1.0j, 0.0]], dtype=complex)


class ChiralError(RuntimeError):
    """Raised when a chirality claim exceeds what the model licenses.

    Covers the structural refusals (a null or non-finite polarization, an
    unknown valley or helicity) and the load-bearing firewall
    :func:`refuse_model_chirality_as_measured`, which refuses to read a
    computed phonon angular momentum as a measured circular-dichroism or
    phonon-Hall signal.
    """


class Helicity(Enum):
    """The sense of circular rotation. LINEAR carries no chirality."""

    LEFT = "LEFT"       # e_+, l_z = +hbar
    RIGHT = "RIGHT"     # e_-, l_z = -hbar
    LINEAR = "LINEAR"   # l_z = 0


class Valley(Enum):
    """The two inequivalent zone corners; time-reversal partners."""

    K = "K"
    K_PRIME = "K_PRIME"


def _polarization(vec) -> np.ndarray:
    """Validate a 2-D complex polarization vector."""
    v = np.asarray(vec, dtype=complex).reshape(-1)
    if v.shape[0] != 2:
        raise ChiralError("a polarization is a 2-D vector (x, y)")
    if not np.all(np.isfinite(v)):
        raise ChiralError("a polarization must be finite")
    norm = float(np.sqrt(np.real(np.vdot(v, v))))
    if norm <= 0.0:
        raise ChiralError("a polarization cannot be the zero vector")
    return v


# --- the circular polarization basis -------------------------------------

def circular_basis() -> tuple[np.ndarray, np.ndarray]:
    """``(e_+, e_-)`` with ``e_± = (e_x ± i e_y)/sqrt(2)``.

    These are orthonormal under the Hermitian inner product and are the
    eigenvectors of :data:`ROTATION_GENERATOR` with eigenvalues ``+1`` and
    ``-1``.
    """
    root2 = math.sqrt(2.0)
    e_plus = np.array([1.0, 1.0j], dtype=complex) / root2
    e_minus = np.array([1.0, -1.0j], dtype=complex) / root2
    return e_plus, e_minus


def linear_polarization(angle_rad: float = 0.0) -> np.ndarray:
    """A real (linear) polarization at ``angle_rad`` from the x axis."""
    a = float(angle_rad)
    if not math.isfinite(a):
        raise ChiralError("the polarization angle must be finite")
    return np.array([math.cos(a), math.sin(a)], dtype=complex)


def rotation_eigenvalue(vec) -> complex:
    """The eigenvalue of :data:`ROTATION_GENERATOR` on ``vec``, or raise.

    ``e_+`` returns ``+1`` and ``e_-`` returns ``-1``. A vector that is
    not an eigenvector of the generator (e.g. a linear polarization) has
    no single eigenvalue and is refused.
    """
    v = _polarization(vec)
    lv = ROTATION_GENERATOR @ v
    # Solve L v = lambda v in the least-squares sense, then verify.
    denom = complex(np.vdot(v, v))
    lam = complex(np.vdot(v, lv)) / denom
    if not np.allclose(lv, lam * v, atol=1e-9, rtol=0.0):
        raise ChiralError(
            "this polarization is not an eigenvector of the rotation "
            "generator, so it has no definite angular momentum; only the "
            "circular polarizations e_+ and e_- do")
    return lam


# --- phonon angular momentum ---------------------------------------------

def phonon_angular_momentum(polarization, hbar: float = HBAR_J_S) -> float:
    """Per-mode angular momentum ``l_z`` about the propagation axis.

    For a normalized polarization ``v`` the angular momentum is
    ``l_z = hbar * Im(2 * conj(v_x) * v_y)`` — the expectation of the
    rotation generator scaled by ``hbar``. A left-circular mode ``e_+``
    gives ``+hbar``, a right-circular mode ``e_-`` gives ``-hbar``, and any
    linear polarization gives ``0``. The form factor is taken as one here;
    a real lattice carries a mode-dependent factor in ``[-1, 1]``.
    """
    v = _polarization(polarization)
    h = float(hbar)
    if not math.isfinite(h) or h <= 0.0:
        raise ChiralError("hbar must be positive and finite")
    norm2 = float(np.real(np.vdot(v, v)))
    # <v| L |v> / <v|v> for L = [[0,-i],[i,0]] is 2*Im(conj(v_x) v_y).
    expectation = float(np.real(np.vdot(v, ROTATION_GENERATOR @ v))) / norm2
    return h * expectation


def helicity_of(polarization, hbar: float = HBAR_J_S) -> Helicity:
    """Classify a polarization by the sign of its angular momentum."""
    lz = phonon_angular_momentum(polarization, hbar)
    if abs(lz) < CHIRAL_TOL * hbar:
        return Helicity.LINEAR
    return Helicity.LEFT if lz > 0.0 else Helicity.RIGHT


# --- chirality at K versus K' --------------------------------------------

def valley_pseudo_angular_momentum(valley: Valley,
                                   hbar: float = HBAR_J_S) -> float:
    """The pseudo-angular-momentum a chiral branch carries at ``valley``.

    ``K`` carries ``+hbar`` and ``K'`` carries ``-hbar`` for the same
    branch: the two valleys are time-reversal partners, so their
    chiralities are locked equal and opposite. The magnitude is the same
    ``hbar`` unit as :func:`phonon_angular_momentum`.
    """
    if not isinstance(valley, Valley):
        raise ChiralError("a valley must be a Valley member")
    h = float(hbar)
    if not math.isfinite(h) or h <= 0.0:
        raise ChiralError("hbar must be positive and finite")
    return h if valley is Valley.K else -h


def chirality_flips_between_valleys(hbar: float = HBAR_J_S) -> dict:
    """State the K/K' chirality lock as a computed, checkable result."""
    lk = valley_pseudo_angular_momentum(Valley.K, hbar)
    lkp = valley_pseudo_angular_momentum(Valley.K_PRIME, hbar)
    return {
        "l_at_K": lk,
        "l_at_K_prime": lkp,
        "equal_and_opposite": bool(abs(lk + lkp) < CHIRAL_TOL * hbar
                                   and lk != 0.0),
        "note": ("K and K' are time-reversal partners, so the same branch "
                 "carries opposite pseudo-angular-momentum at the two "
                 "valleys; a common sign would break time-reversal by "
                 "hand"),
        "verdict": DEFAULT_VERDICT,
        "measured_here": MEASURED_HERE,
    }


def valley_selection(drive_helicity: Helicity) -> Valley:
    """Which valley a circularly polarized drive addresses.

    A left-circular drive addresses ``K`` and a right-circular drive
    addresses ``K'``, so the addressed valley flips with the drive
    helicity. A linear drive has no definite helicity and addresses
    neither valley selectively, which is refused rather than guessed.
    """
    if not isinstance(drive_helicity, Helicity):
        raise ChiralError("the drive helicity must be a Helicity member")
    if drive_helicity is Helicity.LINEAR:
        raise ChiralError(
            "a linearly polarized drive carries no net helicity and does "
            "not select a valley; it is an equal superposition of both "
            "chiralities")
    return Valley.K if drive_helicity is Helicity.LEFT else Valley.K_PRIME


# --- the load-bearing refusal --------------------------------------------

def refuse_model_chirality_as_measured(
        l_z: float | None = None,
        claim: str = "the computed phonon angular momentum is a measured "
                     "circular-dichroism or phonon-Hall signal") -> None:
    """Refuse reading a computed chirality as a measured signal.

    Always raises. A per-mode angular momentum computed here is algebra on
    a declared polarization eigenvector — an ANALYTIC_MODEL — with no
    lattice, no excited phonon, no detector and no uncertainty budget. A
    measured chirality is a bench result: a helicity-resolved scattering
    cross-section, a circular-dichroism contrast, or a transverse
    phonon-Hall current, each with a calibration and a null model. The one
    does not become the other by sharing the symbol ``l_z``.
    """
    said = f" Claim: {claim!r}." if claim else ""
    where = "" if l_z is None else f" (l_z = {l_z})"
    raise ChiralError(
        f"refusing to read a modelled phonon angular momentum{where} as a "
        f"measured circular-dichroism or phonon-Hall signal.{said} The "
        f"quantity here is a closed form on a declared circular "
        f"polarization — an ANALYTIC_MODEL — with no lattice, no excited "
        f"mode, no helicity-resolved detector and no calibration. A "
        f"measured chirality is a BENCH_MEASUREMENT: a helicity-resolved "
        f"cross-section, a dichroic contrast, or a transverse phonon-Hall "
        f"current, each against a null model. Computing an eigenvector's "
        f"angular momentum is not observing one, and nothing here is "
        f"measured.")


# --- report --------------------------------------------------------------

def chiral_report(verdict: str = DEFAULT_VERDICT) -> dict:
    """One statement of what this module computes and, loudly, disclaims."""
    e_plus, e_minus = circular_basis()
    return {
        "claim_class": CLAIM_CLASS,
        "what_this_is": (
            "the closed-form theory of chiral phonons at a hexagonal zone "
            "corner: the circular basis e_± = (e_x ± i e_y)/sqrt(2), its "
            "per-mode angular momentum l_z = ± hbar, the K/K' chirality "
            "lock, and the circular-drive valley selection rule"),
        "circular_basis": {
            "e_plus": [complex(z) for z in e_plus.tolist()],
            "e_minus": [complex(z) for z in e_minus.tolist()],
            "orthonormal": True,
            "rotation_eigenvalues": {"e_plus": "+1", "e_minus": "-1"},
        },
        "angular_momentum": {
            "e_plus_l_z_over_hbar":
                phonon_angular_momentum(e_plus) / HBAR_J_S,
            "e_minus_l_z_over_hbar":
                phonon_angular_momentum(e_minus) / HBAR_J_S,
            "linear_l_z_over_hbar":
                phonon_angular_momentum(linear_polarization()) / HBAR_J_S,
        },
        "valley_chirality": chirality_flips_between_valleys(),
        "selection_rule": {
            "left_drive_addresses": valley_selection(Helicity.LEFT).value,
            "right_drive_addresses": valley_selection(Helicity.RIGHT).value,
        },
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any lattice, phonon or valley exists, that a "
            "mode was excited, or that any angular momentum, dichroism or "
            "Hall current was measured. Every polarization is a declared "
            "vector and l_z is a closed form on it; the lattice form "
            "factor is taken as one. It does not say that a computed l_z "
            "is an observed circular-dichroism or phonon-Hall signal — "
            "that is a bench measurement with a helicity-resolved "
            "detector and a null model, and refuse_model_chirality_as_"
            "measured refuses the identification. It does not say the "
            "K/K' chirality lock was observed; it is imposed by "
            "time-reversal symmetry in the model, not measured."),
        "verdict": verdict,
    }


__all__ = [
    "DEFAULT_VERDICT", "CLAIM_CLASS", "MEASURED_HERE", "PHYSICAL_VALIDATION",
    "HBAR_J_S", "CHIRAL_TOL", "ROTATION_GENERATOR",
    "ChiralError", "Helicity", "Valley",
    "circular_basis", "linear_polarization", "rotation_eigenvalue",
    "phonon_angular_momentum", "helicity_of",
    "valley_pseudo_angular_momentum", "chirality_flips_between_valleys",
    "valley_selection",
    "refuse_model_chirality_as_measured",
    "chiral_report",
]
