"""P16 — Floquet analysis of a periodically driven oscillator.

A parametric oscillator obeys the Mathieu equation

    ``x'' + (delta + epsilon*cos(2*t)) x = 0``,

a stiffness that is modulated in time rather than a force that is applied.
Because the modulation is periodic, the whole of the dynamics is carried
by one object: the **monodromy matrix**, the map that advances the state
``(x, x')`` across a single drive period. Everything else here is read off
from it.

Three facts are load-bearing.

**(a) The monodromy is symplectic.** The equation is Hamiltonian with
``H = p**2/2 + (delta + epsilon*cos(2t)) x**2/2``, so the period map
preserves phase-space area: ``det(M) == 1`` exactly (to integration
precision). :func:`floquet_monodromy` integrates it and the determinant is
tested.

**(b) Stability is the modulus of a Floquet multiplier.** The eigenvalues
``mu`` of ``M`` are the Floquet multipliers, and ``det(M) == 1`` forces
``mu_1*mu_2 == 1``. Inside a parametric-resonance tongue — near
``delta = n**2``, with the principal tongue at ``delta = 1`` — one
multiplier has ``|mu| > 1`` and the motion grows; outside, the multipliers
sit on the unit circle, ``|mu| == 1``, and the motion is bounded. That
contrast is tested both ways.

**(c) Multipliers define quasi-energies, and a drive squeezes.** Writing
``mu = exp(-i*eps_F*T)`` defines a quasi-energy ``eps_F`` modulo the drive
frequency ``omega = 2*pi/T``; :func:`quasi_energies` returns them, real and
in ``+/-`` pairs for the stable case because the monodromy is symplectic.
Above the parametric threshold the drive amplifies one quadrature and
deamplifies the conjugate one — a phase-sensitive gain, the same squeezing
a degenerate parametric amplifier produces — and :func:`parametric_gain`
reports both quadrature gains, whose product is one.

Nothing here is measured. No oscillator is built, no drive is applied, and
no instability, quasi-energy or gain is observed on any hardware; every
number is a numerical monodromy or a closed-form gain of a declared model,
and :func:`refuse_model_instability_as_measured` refuses to read a
computed tongue as an observed instability.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim class, provenance ------------------------------------

#: The standing verdict for this module.
VERDICT = "FLOQUET_PARAMETRIC_MODEL_ANALYTIC"

#: What this module's own output is: an analytic Floquet model, with the
#: monodromy evaluated to numerical precision.
CLAIM_CLASS = "ANALYTIC_MODEL"

#: The claim classes a statement in this module is allowed to declare.
CLAIM_CLASSES = (
    "EXACT_IDENTITY",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "BLOCKED_MISSING_INPUT",
)

EVIDENCE_CLASS = "DERIVED_MATHEMATICS"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Default drive angular frequency of the ``cos(2t)`` modulation.
DEFAULT_DRIVE = 2.0

#: Default resolution of the one-period integration.
DEFAULT_STEPS = 4000

#: Tolerance on ``det(M) == 1`` and on the unit-circle test.
UNIT_TOL = 1e-6


class FloquetError(RuntimeError):
    """Raised when a Floquet claim exceeds the model.

    Covers the structural refusals (a non-positive drive frequency, too
    coarse an integration grid, a matrix that is not a valid monodromy)
    and the load-bearing refusal
    :func:`refuse_model_instability_as_measured`, which will not let a
    computed parametric-resonance tongue be reported as an observed
    instability in real hardware.
    """


def _finite(value: float, what: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise FloquetError(f"{what} must be finite")
    return x


def _positive(value: float, what: str) -> float:
    x = _finite(value, what)
    if x <= 0.0:
        raise FloquetError(f"{what} must be positive")
    return x


def _steps(n_steps: int) -> int:
    n = int(n_steps)
    if n < 2:
        raise FloquetError("an integration grid needs at least two points")
    return n


# --- (1) the monodromy matrix --------------------------------------------

def drive_period(omega_drive: float = DEFAULT_DRIVE) -> float:
    """``T = 2*pi/omega_drive``: the period of the ``cos(omega_drive*t)`` drive.

    For the canonical ``cos(2t)`` modulation this is ``pi``.
    """
    return 2.0 * math.pi / _positive(omega_drive, "the drive frequency")


def _stiffness(t: float, delta: float, epsilon: float,
               omega_drive: float) -> float:
    """The time-dependent stiffness ``delta + epsilon*cos(omega_drive*t)``."""
    return delta + epsilon * math.cos(omega_drive * t)


def _integrate_period(delta: float, epsilon: float, omega_drive: float,
                      x0: float, v0: float, n_steps: int) -> tuple:
    """RK4-advance ``(x, v)`` across one drive period from one initial state.

    The system is ``x' = v``, ``v' = -(delta + epsilon*cos(omega t)) x``.
    """
    T = drive_period(omega_drive)
    n = _steps(n_steps)
    h = T / n
    x, v = float(x0), float(v0)
    t = 0.0

    def deriv(tt, xx, vv):
        return vv, -_stiffness(tt, delta, epsilon, omega_drive) * xx

    for _ in range(n):
        k1x, k1v = deriv(t, x, v)
        k2x, k2v = deriv(t + h / 2, x + h / 2 * k1x, v + h / 2 * k1v)
        k3x, k3v = deriv(t + h / 2, x + h / 2 * k2x, v + h / 2 * k2v)
        k4x, k4v = deriv(t + h, x + h * k3x, v + h * k3v)
        x += h / 6 * (k1x + 2 * k2x + 2 * k3x + k4x)
        v += h / 6 * (k1v + 2 * k2v + 2 * k3v + k4v)
        t += h
    return x, v


def floquet_monodromy(delta: float, epsilon: float,
                      omega_drive: float = DEFAULT_DRIVE,
                      n_steps: int = DEFAULT_STEPS) -> np.ndarray:
    """The one-period state-transition (monodromy) matrix of the drive.

    Advances the two fundamental solutions — from ``(x, v) = (1, 0)`` and
    ``(0, 1)`` — across one drive period; their endpoints are the columns
    of ``M``. Because the equation is Hamiltonian the map is symplectic,
    so ``det(M) == 1`` to integration precision.
    """
    d = _finite(delta, "delta")
    e = _finite(epsilon, "epsilon")
    w = _positive(omega_drive, "the drive frequency")
    x1, v1 = _integrate_period(d, e, w, 1.0, 0.0, n_steps)
    x2, v2 = _integrate_period(d, e, w, 0.0, 1.0, n_steps)
    return np.array([[x1, x2], [v1, v2]], dtype=float)


def _as_monodromy(monodromy) -> np.ndarray:
    m = np.asarray(monodromy, dtype=float)
    if m.shape != (2, 2):
        raise FloquetError("a monodromy matrix must be 2x2")
    if not np.all(np.isfinite(m)):
        raise FloquetError("a monodromy matrix must be finite")
    return m


def symplectic_defect(monodromy) -> float:
    """``|det(M) - 1|``: how far the map is from area-preserving."""
    m = _as_monodromy(monodromy)
    return abs(float(np.linalg.det(m)) - 1.0)


def is_symplectic(monodromy, tol: float = UNIT_TOL) -> bool:
    """True when ``det(M) == 1`` to ``tol`` — the Hamiltonian signature."""
    return symplectic_defect(monodromy) <= tol


# --- (2) Floquet multipliers and stability -------------------------------

def floquet_multipliers(monodromy) -> np.ndarray:
    """The eigenvalues ``mu`` of the monodromy: the Floquet multipliers.

    With ``det(M) == 1`` they satisfy ``mu_1*mu_2 == 1``, so they are
    either a conjugate pair on the unit circle (stable) or a reciprocal
    real pair straddling it (unstable).
    """
    m = _as_monodromy(monodromy)
    return np.linalg.eigvals(m)


def spectral_radius(monodromy) -> float:
    """``max|mu|``: the growth factor per drive period."""
    return float(np.max(np.abs(floquet_multipliers(monodromy))))


def is_stable(monodromy, tol: float = UNIT_TOL) -> bool:
    """Stable when every multiplier sits on or inside the unit circle.

    Equivalent, for a symplectic 2x2, to ``|trace(M)| <= 2``: a smaller
    trace keeps the multipliers on the unit circle, a larger one pushes
    one of them out.
    """
    return spectral_radius(monodromy) <= 1.0 + tol


@dataclass(frozen=True)
class StabilityResult:
    """The stability verdict for one ``(delta, epsilon)`` point."""

    delta: float
    epsilon: float
    trace: float
    multipliers: tuple[complex, complex]
    spectral_radius: float
    symplectic_defect: float
    stable: bool

    def as_dict(self) -> dict:
        return {
            "delta": self.delta,
            "epsilon": self.epsilon,
            "trace": self.trace,
            "multiplier_moduli": [abs(m) for m in self.multipliers],
            "spectral_radius": self.spectral_radius,
            "symplectic_defect": self.symplectic_defect,
            "stable": self.stable,
            "measured_here": MEASURED_HERE,
        }


def stability_at(delta: float, epsilon: float,
                 omega_drive: float = DEFAULT_DRIVE,
                 n_steps: int = DEFAULT_STEPS) -> StabilityResult:
    """Integrate the monodromy at one point and classify its stability."""
    m = floquet_monodromy(delta, epsilon, omega_drive, n_steps)
    mu = floquet_multipliers(m)
    return StabilityResult(
        delta=_finite(delta, "delta"),
        epsilon=_finite(epsilon, "epsilon"),
        trace=float(np.trace(m)),
        multipliers=(complex(mu[0]), complex(mu[1])),
        spectral_radius=float(np.max(np.abs(mu))),
        symplectic_defect=symplectic_defect(m),
        stable=is_stable(m),
    )


#: The principal parametric-resonance tongue touches the axis at delta = 1.
PRINCIPAL_TONGUE_DELTA = 1.0


def principal_tongue_contrast(epsilon: float = 0.4,
                              inside_delta: float = PRINCIPAL_TONGUE_DELTA,
                              outside_delta: float = 2.0,
                              omega_drive: float = DEFAULT_DRIVE,
                              n_steps: int = DEFAULT_STEPS) -> dict:
    """The load-bearing contrast: unstable inside the tongue, stable outside.

    At ``delta = 1`` the principal tongue reaches down to zero drive, so
    any ``epsilon > 0`` gives a multiplier with ``|mu| > 1``. A detuned
    point well away from a tongue keeps both multipliers on the unit
    circle.
    """
    inside = stability_at(inside_delta, epsilon, omega_drive, n_steps)
    outside = stability_at(outside_delta, epsilon, omega_drive, n_steps)
    return {
        "epsilon": _finite(epsilon, "epsilon"),
        "inside": inside.as_dict(),
        "outside": outside.as_dict(),
        "inside_is_unstable": bool(not inside.stable
                                   and inside.spectral_radius > 1.0),
        "outside_is_stable": bool(outside.stable),
        "verdict": VERDICT,
        "measured_here": MEASURED_HERE,
    }


# --- (3) quasi-energies ---------------------------------------------------

def quasi_energies(monodromy, T: float) -> np.ndarray:
    """Quasi-energies from ``mu = exp(-i*eps_F*T)``: ``eps_F = i*log(mu)/T``.

    Real and in ``+/-`` pairs for the stable case, because a symplectic
    monodromy with multipliers on the unit circle has ``mu_2 = conj(mu_1)
    = 1/mu_1``. They are defined only modulo the drive frequency
    ``omega = 2*pi/T``. Complex quasi-energies (a non-zero imaginary part)
    signal an unstable, growing solution.
    """
    period = _positive(T, "the period")
    mu = floquet_multipliers(monodromy)
    return np.array([1j * np.log(m) / period for m in mu])


def drive_frequency_from_period(T: float) -> float:
    """``omega = 2*pi/T``: the modulus of the quasi-energy Brillouin zone."""
    return 2.0 * math.pi / _positive(T, "the period")


# --- (4) parametric amplification / degenerate gain ----------------------

def _gain_transfer(pump: float, detuning: float, length: float
                   ) -> np.ndarray:
    """Quadrature transfer matrix of a degenerate parametric amplifier.

    In the rotating frame the quadratures obey
    ``d/dt (X, Y) = A (X, Y)`` with ``A = [[pump, detuning],
    [-detuning, -pump]]``, so ``A**2 = (pump**2 - detuning**2) I`` and the
    matrix exponential is a closed form. Above threshold
    (``pump > |detuning|``) it stretches one quadrature and squeezes the
    conjugate; below threshold it merely rotates.
    """
    p = _finite(pump, "the pump")
    d = _finite(detuning, "the detuning")
    L = _finite(length, "the interaction length")
    A = np.array([[p, d], [-d, -p]], dtype=float)
    s2 = p * p - d * d
    if s2 > 0.0:
        s = math.sqrt(s2)
        return math.cosh(s * L) * np.eye(2) + (math.sinh(s * L) / s) * A
    if s2 < 0.0:
        w = math.sqrt(-s2)
        return math.cos(w * L) * np.eye(2) + (math.sin(w * L) / w) * A
    return np.eye(2) + L * A


@dataclass(frozen=True)
class ParametricGain:
    """Phase-sensitive gain of a degenerate parametric drive.

    ``amplified`` and ``deamplified`` are the larger and smaller quadrature
    gains (the singular values of the transfer matrix); their product is
    one because the drive is symplectic. ``above_threshold`` is
    ``pump > |detuning|``.
    """

    pump: float
    detuning: float
    length: float
    amplified: float
    deamplified: float
    above_threshold: bool

    @property
    def phase_sensitive(self) -> bool:
        """True when the two quadratures are treated differently."""
        return abs(self.amplified - self.deamplified) > 1e-9

    def as_dict(self) -> dict:
        return {
            "pump": self.pump,
            "detuning": self.detuning,
            "length": self.length,
            "amplified": self.amplified,
            "deamplified": self.deamplified,
            "gain_product": self.amplified * self.deamplified,
            "above_threshold": self.above_threshold,
            "phase_sensitive": self.phase_sensitive,
            "measured_here": MEASURED_HERE,
        }


def parametric_gain(pump: float, detuning: float = 0.0,
                    length: float = 1.0) -> ParametricGain:
    """Quadrature gains of a degenerate parametric amplifier.

    Above threshold (``pump > |detuning|``) one quadrature is amplified
    (gain ``> 1``) and the conjugate one deamplified (gain ``< 1``), the
    two multiplying to one — the phase-sensitive gain of squeezing. Below
    threshold the drive cannot overcome the detuning and there is no net
    amplification.
    """
    p = _finite(pump, "the pump")
    d = _finite(detuning, "the detuning")
    L = _positive(length, "the interaction length")
    m = _gain_transfer(p, d, L)
    sv = np.linalg.svd(m, compute_uv=False)
    amplified = float(np.max(sv))
    deamplified = float(np.min(sv))
    return ParametricGain(
        pump=p, detuning=d, length=L,
        amplified=amplified, deamplified=deamplified,
        above_threshold=bool(abs(p) > abs(d)))


# --- (5) the required refusal --------------------------------------------

def refuse_model_instability_as_measured(delta: float = 1.0,
                                         epsilon: float = 0.4,
                                         context: str = "") -> None:
    """Refuse reading a computed parametric tongue as an observed instability.

    Raises unconditionally. A multiplier with ``|mu| > 1`` from
    :func:`floquet_monodromy` is a property of the model equation; an
    observed instability is a growing amplitude on an actual driven
    oscillator, with a measured growth rate, a noise floor and a threshold
    calibration — none of which exist here.
    """
    tail = f" ({context})" if context else ""
    raise FloquetError(
        f"refusing to report a computed parametric-resonance tongue "
        f"(delta={float(delta):.4g}, epsilon={float(epsilon):.4g}){tail} "
        f"as an observed instability. A Floquet multiplier with |mu| > 1 "
        f"is an eigenvalue of a numerically integrated monodromy matrix: "
        f"no oscillator is built, no parametric drive is applied, and no "
        f"growing amplitude is recorded against a noise floor. A measured "
        f"instability is a growth rate with an uncertainty and a "
        f"calibrated threshold; this is {CLAIM_CLASS}, and "
        f"{PHYSICAL_VALIDATION}.")


# --- report --------------------------------------------------------------

def floquet_report(verdict: str = VERDICT) -> dict:
    """The standing statement of what this module computes and disclaims."""
    contrast = principal_tongue_contrast()
    T = drive_period()
    stable = floquet_monodromy(2.0, 0.2)
    qe = quasi_energies(stable, T)
    gain = parametric_gain(1.0, 0.0)
    return {
        "claim_class": CLAIM_CLASS,
        "claim_classes": list(CLAIM_CLASSES),
        "what_this_is": (
            "a Floquet model of the Mathieu / parametric oscillator: its "
            "symplectic monodromy, the parametric-resonance tongues read "
            "from the Floquet multipliers, the quasi-energies those "
            "multipliers define, and the phase-sensitive gain a "
            "parametric drive produces"),
        "equation": "x'' + (delta + epsilon*cos(2t)) x = 0",
        "drive_period": T,
        "monodromy_is_symplectic": "det(M) == 1",
        "symplectic_defect": symplectic_defect(stable),
        "principal_tongue_contrast": contrast,
        "quasi_energies": {
            "definition": "mu = exp(-i*eps_F*T)",
            "brillouin_zone": drive_frequency_from_period(T),
            "values_real_part": [float(np.real(z)) for z in qe],
            "values_imag_part": [float(np.imag(z)) for z in qe],
            "real_and_plus_minus_paired_for_stable_case": bool(
                max(abs(np.imag(z)) for z in qe) < UNIT_TOL
                and abs(float(np.real(qe[0] + qe[1]))) < UNIT_TOL),
        },
        "parametric_gain": gain.as_dict(),
        "squeezing_note": (
            "above threshold the drive amplifies one quadrature and "
            "deamplifies the conjugate one, the two gains multiplying to "
            "one — the phase-sensitive gain of squeezing"),
        "evidence_class": EVIDENCE_CLASS,
        "hardware_status": (
            "DEFERRED — no oscillator built, no parametric drive applied, "
            "no instability or gain observed"),
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any oscillator was built, any parametric "
            "drive was applied, or any instability, quasi-energy or gain "
            "was observed on hardware. Every monodromy is a numerical "
            "integration of a declared Mathieu equation in dimensionless "
            "units, every multiplier is its eigenvalue, and every gain is "
            "a closed-form quadrature transfer of the same model. A "
            "multiplier with |mu| > 1 is a model tongue, not a measured "
            "growing amplitude, and refuse_model_instability_as_measured "
            "refuses that promotion. No threshold was calibrated and no "
            "noise floor was measured."),
        "verdict": verdict,
    }


__all__ = [
    "VERDICT", "CLAIM_CLASS", "CLAIM_CLASSES", "EVIDENCE_CLASS",
    "MEASURED_HERE", "PHYSICAL_VALIDATION", "DEFAULT_DRIVE",
    "DEFAULT_STEPS", "UNIT_TOL",
    "FloquetError",
    "drive_period", "floquet_monodromy", "symplectic_defect",
    "is_symplectic", "floquet_multipliers", "spectral_radius", "is_stable",
    "StabilityResult", "stability_at", "PRINCIPAL_TONGUE_DELTA",
    "principal_tongue_contrast",
    "quasi_energies", "drive_frequency_from_period",
    "ParametricGain", "parametric_gain",
    "refuse_model_instability_as_measured",
    "floquet_report",
]
