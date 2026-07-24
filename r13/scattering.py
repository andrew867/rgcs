"""P32 — synthetic INS / IXS scattering predictions from the phonon model.

Inelastic neutron scattering (INS) and inelastic X-ray scattering (IXS) are
EXTERNAL VALIDATION lanes: a facility fires a beam at a sample, measures the
momentum transfer ``Q`` and energy transfer ``hbar omega`` of scattered
particles, and reconstructs the dynamic structure factor ``S(Q, omega)``.
We have **no facility, no beam time, and no sample**. What this module
produces is the *prospective signature* -- what such a measurement COULD
see -- computed from a synthetic phonon model. It is a
``PROSPECTIVE_PREDICTION``, never a bench result.

Four textbook pieces of scattering physics are implemented against their
closed forms, so each prediction is falsifiable in principle:

* **Kinematics.** The scattering triangle ``k_i - k_f = Q`` with energy
  conservation ``hbar omega = E_i - E_f``. :func:`scattering_kinematics`
  does the bookkeeping and :func:`conserves` checks that a named excitation
  balances both momentum and energy.
* **Bragg (elastic).** Peaks land where ``Q = G``, a reciprocal-lattice
  vector, and Bragg's law ``2 d sin(theta) = n lambda`` holds
  (:func:`bragg_condition`, :func:`braggs_law_holds`).
* **One-phonon inelastic ``S(Q, omega)``.** Peaks at the phonon
  frequencies with intensity ``propto (Q . e)^2 / omega`` times the Bose
  factor, weighted by the phonon polarization ``e``; the ``(Q . e)``
  selection rule zeroes transverse-forbidden geometries
  (:func:`one_phonon_sqw`).
* **Detailed balance.** ``S(Q, omega) / S(-Q, -omega) = exp(hbar omega /
  k_B T)`` (:func:`detailed_balance_ratio`).

Real beam-time data is ``BLOCKED_MISSING_INPUT``.
:func:`refuse_synthetic_sqw_as_beamtime_data` refuses to pass a synthetic
``S(Q, omega)`` off as facility data, and :func:`refuse_prediction_as_detection`
refuses to read a prediction as a detection. The default verdict is
``SYNTHETIC_INS_IXS_PREDICTION_PROSPECTIVE``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim classes ----------------------------------------------

DEFAULT_VERDICT = "SYNTHETIC_INS_IXS_PREDICTION_PROSPECTIVE"

#: What this module produces: prospective, facility-measurable signatures.
CLAIM_CLASS = "PROSPECTIVE_PREDICTION"

#: The claim classes a statement in this module may declare, verbatim.
CLAIM_CLASSES = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "CONVENTIONAL_LITERATURE",
    "DERIVED_ARITHMETIC",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "PROSPECTIVE_PREDICTION",
    "SOURCE_CLAIM",
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_INPUT",
)

#: Numerical tolerance for the kinematic and lattice identities.
SCATTER_TOL = 1e-9


class ScatteringError(RuntimeError):
    """Raised when a scattering claim exceeds what the prediction licenses.

    Covers the structural refusals (a non-3-vector, a non-positive energy or
    temperature) and the governance refusals
    :func:`refuse_synthetic_sqw_as_beamtime_data` and
    :func:`refuse_prediction_as_detection`.
    """


class Probe(Enum):
    """The scattering probe -- a massive neutron or a massless X-ray photon."""

    NEUTRON = "NEUTRON"          # E = hbar^2 k^2 / 2m
    XRAY = "XRAY"                # E = hbar c k


def _vec3(x, what: str) -> np.ndarray:
    v = np.asarray(x, dtype=float)
    if v.shape != (3,):
        raise ScatteringError(f"{what} must be a 3-vector")
    if not np.all(np.isfinite(v)):
        raise ScatteringError(f"{what} must be finite")
    return v


def _positive(value: float, what: str) -> float:
    x = float(value)
    if not math.isfinite(x) or x <= 0.0:
        raise ScatteringError(f"{what} must be a positive finite number")
    return x


# --- the blocked-input receipt -------------------------------------------

#: Real INS / IXS spectra come from a facility that does not exist here.
REAL_BEAMTIME_STATUS = {
    "status": "BLOCKED_MISSING_INPUT",
    "why": ("a measured S(Q, omega) requires a neutron or synchrotron / XFEL "
            "facility, allocated beam time, a mounted sample, and detector "
            "calibration; none of these exist in this environment"),
    "external_lane": ("INS and IXS are EXTERNAL VALIDATION lanes; this module "
                      "supplies only the prospective signature a facility "
                      "could measure, not the measurement"),
}


# --- kinematics: the scattering triangle ---------------------------------

@dataclass(frozen=True)
class ScatteringEvent:
    """One synthetic scattering event: incident and final wavevectors.

    ``Q = k_i - k_f`` is the momentum transfer (in units of the wavevector)
    and ``hbar_omega`` is the energy transfer ``E_i - E_f``. Positive
    ``hbar_omega`` is energy loss by the probe -- the Stokes side, where an
    excitation is created.
    """

    k_i: tuple[float, float, float]
    k_f: tuple[float, float, float]
    probe: Probe
    Q: tuple[float, float, float]
    hbar_omega: float

    def Q_vec(self) -> np.ndarray:
        return np.asarray(self.Q, dtype=float)


def _probe_energy(k: np.ndarray, probe: Probe, mass: float, hbar: float,
                  c: float) -> float:
    kk = float(k @ k)
    if probe is Probe.NEUTRON:
        return hbar * hbar * kk / (2.0 * mass)
    if probe is Probe.XRAY:
        return hbar * c * math.sqrt(kk)
    raise ScatteringError(f"unknown probe {probe!r}")


def scattering_kinematics(k_i, k_f, *, probe: Probe = Probe.NEUTRON,
                          mass: float = 1.0, hbar: float = 1.0,
                          c: float = 1.0) -> ScatteringEvent:
    """The momentum and energy transfer of a scattering event.

    ``Q = k_i - k_f`` (momentum conservation, with the crystal absorbing the
    recoil) and ``hbar omega = E(k_i) - E(k_f)`` (energy conservation). The
    probe energy is ``hbar^2 k^2 / 2m`` for a neutron and ``hbar c k`` for an
    X-ray photon. Units are reduced by default (``hbar = m = c = 1``).
    """
    ki = _vec3(k_i, "k_i")
    kf = _vec3(k_f, "k_f")
    _positive(mass, "the mass")
    _positive(hbar, "hbar")
    _positive(c, "c")
    Q = ki - kf
    e_i = _probe_energy(ki, probe, mass, hbar, c)
    e_f = _probe_energy(kf, probe, mass, hbar, c)
    return ScatteringEvent(
        k_i=tuple(ki), k_f=tuple(kf), probe=probe,
        Q=tuple(Q), hbar_omega=e_i - e_f)


def conserves(event: ScatteringEvent, G, excitation_q, excitation_omega,
              tol: float = SCATTER_TOL) -> bool:
    """True iff a named excitation balances both momentum and energy.

    Momentum: the excitation carries ``Q - G`` (the reduced wavevector, with
    ``G`` the reciprocal-lattice vector the crystal supplies). Energy: the
    excitation carries ``hbar omega``. Both must match the event to within
    ``tol`` for the event to conserve against that excitation.
    """
    G = _vec3(G, "G")
    q = _vec3(excitation_q, "the excitation wavevector")
    mom_ok = bool(np.all(np.abs((event.Q_vec() - G) - q) <= tol))
    en_ok = abs(event.hbar_omega - float(excitation_omega)) <= tol
    return mom_ok and en_ok


def scattering_triangle_closes(event: ScatteringEvent,
                               tol: float = SCATTER_TOL) -> bool:
    """Check the law of cosines for the ``k_i - k_f = Q`` triangle.

    ``|Q|^2 = |k_i|^2 + |k_f|^2 - 2 |k_i| |k_f| cos(2 theta)``, where
    ``2 theta`` is the angle between the incident and final wavevectors.
    """
    ki = np.asarray(event.k_i, dtype=float)
    kf = np.asarray(event.k_f, dtype=float)
    Q = event.Q_vec()
    lhs = float(Q @ Q)
    rhs = float(ki @ ki) + float(kf @ kf) - 2.0 * float(ki @ kf)
    return abs(lhs - rhs) <= tol * (1.0 + abs(rhs))


# --- Bragg elastic scattering --------------------------------------------

def reciprocal_vector(hkl, a: float = 1.0) -> np.ndarray:
    """A cubic reciprocal-lattice vector ``G = (2 pi / a) (h, k, l)``."""
    _positive(a, "the lattice constant a")
    v = np.asarray(hkl, dtype=float)
    if v.shape != (3,):
        raise ScatteringError("hkl must be a 3-vector of Miller indices")
    return (2.0 * math.pi / a) * v


def d_spacing(hkl, a: float = 1.0) -> float:
    """Cubic interplanar spacing ``d = a / sqrt(h^2 + k^2 + l^2)``."""
    _positive(a, "the lattice constant a")
    v = np.asarray(hkl, dtype=float)
    norm = math.sqrt(float(v @ v))
    if norm <= 0.0:
        raise ScatteringError("hkl must be non-zero for a d-spacing")
    return a / norm


def bragg_condition(Q, G, tol: float = 1e-6) -> bool:
    """True iff the momentum transfer ``Q`` lands on the reciprocal point ``G``.

    Elastic Bragg peaks occur exactly when ``Q = G``; away from a
    reciprocal-lattice point there is no elastic peak.
    """
    Qv = _vec3(Q, "Q")
    Gv = _vec3(G, "G")
    return bool(np.all(np.abs(Qv - Gv) <= tol))


def bragg_angle(hkl, a: float, wavelength: float, n: int = 1) -> float:
    """The Bragg angle ``theta`` from ``sin theta = n lambda / (2 d)``.

    Raises if the reflection is kinematically forbidden
    (``n lambda / 2 d > 1``).
    """
    _positive(wavelength, "the wavelength")
    if n < 1:
        raise ScatteringError("the Bragg order n must be a positive integer")
    d = d_spacing(hkl, a)
    s = n * wavelength / (2.0 * d)
    if s > 1.0:
        raise ScatteringError(
            f"reflection {tuple(hkl)} order {n} is forbidden at "
            f"lambda={wavelength}: sin(theta)={s} > 1")
    return math.asin(s)


def braggs_law_holds(hkl, a: float, wavelength: float, n: int = 1,
                     tol: float = SCATTER_TOL) -> bool:
    """True iff ``2 d sin(theta) = n lambda`` for the computed Bragg angle."""
    d = d_spacing(hkl, a)
    theta = bragg_angle(hkl, a, wavelength, n)
    return abs(2.0 * d * math.sin(theta) - n * wavelength) <= tol


# --- a synthetic phonon model with Cartesian polarizations ----------------

@dataclass(frozen=True)
class PhononMode:
    """One phonon mode: a frequency and a Cartesian polarization vector.

    ``polarization`` is a (not necessarily unit) 3-vector ``e``; the
    one-phonon intensity is weighted by ``(Q . e)^2``, so a mode whose
    polarization is perpendicular to ``Q`` is scattering-forbidden.
    """

    omega: float
    polarization: tuple[float, float, float]

    def e_vec(self) -> np.ndarray:
        return np.asarray(self.polarization, dtype=float)


@dataclass(frozen=True)
class PhononModel:
    """A synthetic set of phonon modes for a prospective ``S(Q, omega)``."""

    modes: tuple[PhononMode, ...]

    def __post_init__(self) -> None:
        if len(self.modes) < 1:
            raise ScatteringError("a phonon model needs at least one mode")
        for m in self.modes:
            _positive(m.omega, "a phonon frequency")
            _vec3(m.polarization, "a polarization vector")

    def frequencies(self) -> np.ndarray:
        return np.array([m.omega for m in self.modes], dtype=float)

    @classmethod
    def synthetic(cls) -> "PhononModel":
        """A longitudinal-x, transverse-y, transverse-z three-mode model."""
        return cls(modes=(
            PhononMode(1.0, (1.0, 0.0, 0.0)),      # longitudinal along x
            PhononMode(2.0, (0.0, 1.0, 0.0)),      # transverse along y
            PhononMode(3.0, (0.0, 0.0, 1.0)),      # transverse along z
        ))


def bose_factor(omega: float, temperature: float, hbar: float = 1.0,
                kB: float = 1.0) -> float:
    """The Bose-Einstein occupation ``n(omega) = 1 / (exp(hbar w / kT) - 1)``."""
    _positive(omega, "the frequency")
    _positive(temperature, "the temperature")
    x = hbar * omega / (kB * temperature)
    return 1.0 / math.expm1(x)


# --- one-phonon inelastic S(Q, omega) ------------------------------------

def one_phonon_sqw(model: PhononModel, Q, temperature: float = 300.0, *,
                   hbar: float = 1.0, kB: float = 1.0, stokes: bool = True):
    """The one-phonon dynamic structure factor from the synthetic model.

    Returns ``(omegas, intensities)``: for each mode a peak at ``+omega``
    (Stokes, phonon creation) or ``-omega`` (anti-Stokes, phonon
    annihilation), with intensity

        ``S propto (Q . e)^2 / omega  *  thermal``

    where ``thermal`` is ``n(omega) + 1`` on the Stokes side and ``n(omega)``
    on the anti-Stokes side. The ``(Q . e)`` factor is the polarization
    selection rule: a mode with ``e`` perpendicular to ``Q`` is
    scattering-forbidden and its intensity is exactly zero.
    """
    if not isinstance(model, PhononModel):
        raise ScatteringError("one_phonon_sqw needs a PhononModel")
    Qv = _vec3(Q, "Q")
    _positive(temperature, "the temperature")
    omegas = np.empty(len(model.modes), dtype=float)
    intens = np.empty(len(model.modes), dtype=float)
    for i, m in enumerate(model.modes):
        qe = float(Qv @ m.e_vec())
        n = bose_factor(m.omega, temperature, hbar, kB)
        thermal = (n + 1.0) if stokes else n
        omegas[i] = m.omega if stokes else -m.omega
        intens[i] = qe * qe / m.omega * thermal
    return omegas, intens


def detailed_balance_ratio(model: PhononModel, Q, mode_index: int,
                           temperature: float, *, hbar: float = 1.0,
                           kB: float = 1.0) -> float:
    """``S(Q, omega) / S(-Q, -omega)`` for one mode -- should be ``exp(hw/kT)``.

    Stokes intensity at ``(Q, +omega)`` carries ``n + 1``; anti-Stokes at
    ``(-Q, -omega)`` carries ``n``. Because ``(Q . e)^2 = (-Q . e)^2``, the
    ratio is ``(n + 1) / n = exp(hbar omega / k_B T)`` -- the detailed-balance
    relation between phonon creation and annihilation.
    """
    if not isinstance(model, PhononModel):
        raise ScatteringError("detailed_balance_ratio needs a PhononModel")
    if not 0 <= mode_index < len(model.modes):
        raise ScatteringError("mode_index out of range")
    Qv = _vec3(Q, "Q")
    m = model.modes[mode_index]
    qe2 = float(Qv @ m.e_vec()) ** 2
    if qe2 <= 0.0:
        raise ScatteringError(
            "the detailed-balance ratio is undefined for a "
            "scattering-forbidden geometry (Q . e = 0)")
    n = bose_factor(m.omega, temperature, hbar, kB)
    s_stokes = qe2 / m.omega * (n + 1.0)
    s_anti = qe2 / m.omega * n
    return s_stokes / s_anti


# --- the load-bearing refusals -------------------------------------------

def refuse_synthetic_sqw_as_beamtime_data(*_a, **_k) -> None:
    """A synthetic ``S(Q, omega)`` is a prediction, not facility data.

    The structure factor here is computed from a synthetic phonon model; it
    is a ``PROSPECTIVE_PREDICTION`` of what an INS or IXS facility could
    measure. It is not a measured spectrum: real beam-time data requires a
    facility, allocated beam time, and a sample, all BLOCKED_MISSING_INPUT.
    """
    raise ScatteringError(
        "refused: this S(Q, omega) is a PROSPECTIVE_PREDICTION computed from "
        "a synthetic phonon model, not measured beam-time data. A real INS / "
        "IXS spectrum needs a neutron or X-ray facility, allocated beam time, "
        "and a sample -- all BLOCKED_MISSING_INPUT here. "
        "PHYSICAL_VALIDATION_NOT_CLAIMED.")


def refuse_prediction_as_detection(*_a, **_k) -> None:
    """A prospective prediction is not a detection.

    Predicting where peaks would appear if a facility measured this model is
    not the same as detecting them. No measurement has been performed, so no
    detection may be claimed.
    """
    raise ScatteringError(
        "refused: a prospective prediction of scattering signatures is not a "
        "detection. Nothing has been measured; predicting where a facility "
        "would see peaks does not detect them. The prediction is "
        "PROSPECTIVE_PREDICTION; a detection would be a BENCH_MEASUREMENT "
        "that is BLOCKED_MISSING_INPUT. PHYSICAL_VALIDATION_NOT_CLAIMED.")


# --- the report ----------------------------------------------------------

def scattering_report() -> dict:
    model = PhononModel.synthetic()
    return {
        "what_this_is": (
            "synthetic inelastic-neutron (INS) and inelastic-X-ray (IXS) "
            "scattering predictions from a phonon model: kinematics of the "
            "scattering triangle, Bragg elastic peaks, the one-phonon "
            "S(Q, omega) with the (Q . e) selection rule, and detailed "
            "balance -- prospective signatures a facility could measure"),
        "kinematics": "Q = k_i - k_f, hbar omega = E_i - E_f",
        "bragg": "peaks at Q = G; Bragg's law 2 d sin(theta) = n lambda",
        "one_phonon_intensity": "propto (Q . e)^2 / omega * Bose factor",
        "detailed_balance": "S(Q, omega) / S(-Q, -omega) = exp(hbar w / kT)",
        "synthetic_model_frequencies": [float(x) for x in model.frequencies()],
        "real_beamtime": REAL_BEAMTIME_STATUS,
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say any peak here has been observed, that the "
            "synthetic S(Q, omega) is facility data, or that a predicted "
            "signature is a detection. INS and IXS are EXTERNAL VALIDATION "
            "lanes; there is no facility, no beam time, and no sample here, "
            "so real scattering data is BLOCKED_MISSING_INPUT. Every "
            "quantity is a PROSPECTIVE_PREDICTION from a synthetic phonon "
            "model, and a prediction is not a measurement."),
    }
