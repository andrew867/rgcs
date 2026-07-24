"""P15 — quasi-phase-matching (QPM) and its dynamic generalization.

Second-order frequency conversion accumulates only while the driving
polarization and the wave it generates stay in step. The bookkeeping is a
single phase mismatch,

    ``Delta_k = k_out - k_in - k_grating``

and everything here follows from what that number does to a coupled
amplitude integrated along the propagation coordinate ``z``.

Three facts are load-bearing, and this module holds them apart.

**(a) Perfect matching grows as L-squared; mismatch oscillates.** For a
uniform coupling in the undepleted limit the converted amplitude is
``a_out(L) = i*kappa * integral_0^L exp(i*Delta_k*z) dz``, whose modulus
is ``kappa*L*|sinc(Delta_k*L/2)|``. So the conversion efficiency is
``(kappa*L)**2 * sinc**2(Delta_k*L/2)``: maximal at ``Delta_k = 0``, where
it rises as ``L**2``, and identically zero at ``Delta_k*L/2 = n*pi``,
where a full coherence cycle has cancelled itself. :func:`conversion_
efficiency` is that expression and :func:`refuse_model_conversion_as_
measured` refuses to read the number it returns as a measured harmonic.

**(b) A sign-flipping grating restores growth.** A coupling whose sign
reverses every coherence length, period ``Lambda = 2*pi/Delta_k``, carries
a Fourier component ``exp(-i*Delta_k*z)`` that cancels the running phase,
leaving a secular (linear-in-L) term. :func:`qpm_effective_coupling`
accumulates the amplitude for an arbitrary grating; with the matched
period it grows with ``L`` and without any grating it stays bounded by
``2*kappa/|Delta_k|`` and merely oscillates. That contrast is the whole
point of a grating and is tested both ways.

**(c) A dynamic (chirped) grating trades peak for bandwidth.** A grating
whose local period varies along ``z`` phase-matches whichever residual
mismatch is momentarily stationary, so instead of one narrow ``sinc**2``
acceptance peak it accepts a band set by the swept range.
:func:`dynamic_qpm` integrates the coupled amplitude through a
``z``-dependent mismatch, and a chirped grating is shown to broaden the
acceptance bandwidth relative to a fixed one.

The underlying dynamics are the coupled-amplitude equations
``da_out/dz = i*kappa*a_in*exp(i*Delta_k*z)`` and its partner, which
conserve ``|a_in|**2 + |a_out|**2`` — the Manley-Rowe / photon-number
relation: one mode grows exactly as the other depletes, in the undepleted
limit and the fully depleted one alike.

Nothing here is measured. No crystal is poled, no beam is launched, and no
efficiency, harmonic or parametric output is observed; every number is a
numerical integration of a declared model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim class, provenance ------------------------------------

#: The standing verdict for this module.
VERDICT = "DYNAMIC_QUASI_PHASE_MATCHING_MODEL"

#: What this module's own output is: numerically integrated coupled-mode
#: models, not a measured conversion.
CLAIM_CLASS = "NUMERICAL_SIMULATION"

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

#: Default resolution of the propagation-coordinate integrals.
DEFAULT_STEPS = 4000


class QPMError(RuntimeError):
    """Raised when a quasi-phase-matching claim exceeds the model.

    Covers the structural refusals (a non-positive length, a non-positive
    grating period, too coarse an integration grid) and the load-bearing
    refusal :func:`refuse_model_conversion_as_measured`, which will not
    let a computed conversion efficiency be reported as a measured
    second-harmonic or parametric output.
    """


def _positive(value: float, what: str) -> float:
    """Coerce to float and refuse anything non-finite or non-positive."""
    x = float(value)
    if not math.isfinite(x):
        raise QPMError(f"{what} must be finite")
    if x <= 0.0:
        raise QPMError(f"{what} must be positive")
    return x


def _finite(value: float, what: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise QPMError(f"{what} must be finite")
    return x


def _steps(n_steps: int) -> int:
    n = int(n_steps)
    if n < 2:
        raise QPMError("an integration grid needs at least two points")
    return n


# --- (1) the sinc-squared conversion efficiency --------------------------

def sinc_squared(x: float) -> float:
    """``(sin(x)/x)**2``, with the removable value ``1`` taken at ``x = 0``.

    This is the unnormalized sinc; it is ``1`` at the origin and zero at
    every non-zero multiple of ``pi``.
    """
    z = _finite(x, "the sinc argument")
    if abs(z) < 1e-15:
        return 1.0
    s = math.sin(z) / z
    return s * s


def conversion_efficiency(dk: float, L: float, kappa: float = 1.0) -> float:
    """Undepleted conversion efficiency ``(kappa*L)**2 * sinc**2(dk*L/2)``.

    Maximal at perfect phase matching ``dk = 0``, where it grows as
    ``L**2``, and identically zero when ``dk*L/2`` is a non-zero multiple
    of ``pi`` — one full coherence cycle has cancelled the conversion.
    """
    length = _positive(L, "the interaction length")
    k = _finite(kappa, "the coupling")
    arg = _finite(dk, "the phase mismatch") * length / 2.0
    return (k * length) ** 2 * sinc_squared(arg)


def coherence_length(dk: float) -> float:
    """``pi/|dk|``: the length after which uniform conversion first cancels.

    Infinite at perfect phase matching, where the conversion never turns
    over.
    """
    d = abs(_finite(dk, "the phase mismatch"))
    if d == 0.0:
        return math.inf
    return math.pi / d


# --- (2) accumulated coupling under an arbitrary grating -----------------

def _grid(length: float, n_steps: int) -> np.ndarray:
    return np.linspace(0.0, length, _steps(n_steps) + 1)


def _grating_sign(z: np.ndarray, period: float | None) -> np.ndarray:
    """A unit coupling (``period is None``) or a +/-1 square-wave grating."""
    if period is None:
        return np.ones_like(z)
    p = _positive(period, "the grating period")
    return np.sign(np.sin(2.0 * math.pi * z / p))


def qpm_effective_coupling(dk: float, period: float | None, L: float,
                           kappa: float = 1.0,
                           n_steps: int = DEFAULT_STEPS) -> complex:
    """Accumulated converted amplitude under a sign-flipping grating.

    In the undepleted limit the converted amplitude is
    ``a_out(L) = i*kappa * integral_0^L g(z)*exp(i*dk*z) dz`` with
    ``g(z)`` the grating: a unit coupling when ``period is None``, or a
    ``+/-1`` square wave of the given spatial period. With the *matched*
    period ``Lambda = 2*pi/dk`` the running phase is cancelled and the
    modulus grows linearly with ``L`` (secular growth); with no grating it
    is bounded by ``2*kappa/|dk|`` and only oscillates.

    Returns the complex ``a_out(L)``.
    """
    length = _positive(L, "the interaction length")
    d = _finite(dk, "the phase mismatch")
    k = _finite(kappa, "the coupling")
    z = _grid(length, n_steps)
    integrand = _grating_sign(z, period) * np.exp(1j * d * z)
    return 1j * k * np.trapezoid(integrand, z)


def matched_period(dk: float) -> float:
    """``Lambda = 2*pi/dk``: the grating period that restores growth."""
    d = _finite(dk, "the phase mismatch")
    if d == 0.0:
        raise QPMError(
            "a matched grating is undefined at perfect phase matching: "
            "dk = 0 needs no grating, its period would be infinite")
    return 2.0 * math.pi / abs(d)


def secular_growth_contrast(dk: float = 0.5, L: float = 40.0,
                            kappa: float = 1.0,
                            n_steps: int = DEFAULT_STEPS) -> dict:
    """The load-bearing contrast: matched grating grows, uniform is bounded.

    Compares the accumulated conversion at ``L`` and at ``2*L`` with the
    matched grating against a uniform coupling. The matched grating roughly
    doubles when the length doubles (secular growth); the uniform coupling
    stays under its ``2*kappa/|dk|`` bound and does not.
    """
    d = _finite(dk, "the phase mismatch")
    if d == 0.0:
        raise QPMError("this contrast needs a non-zero mismatch to fight")
    length = _positive(L, "the interaction length")
    period = matched_period(d)
    m_l = abs(qpm_effective_coupling(d, period, length, kappa, n_steps))
    m_2l = abs(qpm_effective_coupling(d, period, 2.0 * length, kappa,
                                      n_steps))
    u_l = abs(qpm_effective_coupling(d, None, length, kappa, n_steps))
    u_2l = abs(qpm_effective_coupling(d, None, 2.0 * length, kappa,
                                      n_steps))
    uniform_bound = 2.0 * abs(kappa) / abs(d)
    return {
        "dk": d,
        "L": length,
        "matched_period": period,
        "matched_at_L": m_l,
        "matched_at_2L": m_2l,
        "matched_growth_ratio": (m_2l / m_l if m_l > 0 else math.inf),
        "matched_grows_with_length": bool(m_2l > 1.5 * m_l),
        "uniform_at_L": u_l,
        "uniform_at_2L": u_2l,
        "uniform_bound": uniform_bound,
        "uniform_stays_bounded": bool(
            u_l <= uniform_bound * 1.01 and u_2l <= uniform_bound * 1.01),
        "matched_beats_uniform": bool(m_2l > u_2l),
        "verdict": VERDICT,
        "measured_here": MEASURED_HERE,
    }


# --- (3) the coupled-amplitude equations and Manley-Rowe -----------------

def _rhs(z: float, a_in: complex, a_out: complex, dk: float,
         kappa: float) -> tuple[complex, complex]:
    """``da_in/dz`` and ``da_out/dz`` for the coupled-mode equations."""
    phase = np.exp(1j * dk * z)
    d_out = 1j * kappa * a_in * phase
    d_in = 1j * kappa * a_out * np.conj(phase)
    return d_in, d_out


@dataclass(frozen=True)
class CoupledModeState:
    """The endpoint of a coupled-amplitude integration.

    Every quantity is dimensionless model output; ``a_in`` and ``a_out``
    are complex amplitudes and ``photon_number`` is ``|a_in|**2 +
    |a_out|**2``, the conserved Manley-Rowe invariant.
    """

    a_in: complex
    a_out: complex
    photon_number_initial: float
    photon_number_final: float

    @property
    def manley_rowe_defect(self) -> float:
        """How far the photon number drifted over the integration."""
        return abs(self.photon_number_final - self.photon_number_initial)


def coupled_mode_solve(dk: float, L: float, kappa: float = 1.0,
                       a_in0: complex = 1.0, a_out0: complex = 0.0,
                       n_steps: int = DEFAULT_STEPS) -> CoupledModeState:
    """Integrate the fully coupled amplitude equations by RK4.

    ``da_out/dz = i*kappa*a_in*exp(i*dk*z)`` and
    ``da_in/dz = i*kappa*a_out*exp(-i*dk*z)``. These conserve
    ``|a_in|**2 + |a_out|**2``: the photon number the pump loses is exactly
    the photon number the harmonic gains, in the undepleted and the
    depleted regime alike.
    """
    length = _positive(L, "the interaction length")
    d = _finite(dk, "the phase mismatch")
    k = _finite(kappa, "the coupling")
    n = _steps(n_steps)
    h = length / n
    a_in = complex(a_in0)
    a_out = complex(a_out0)
    n0 = abs(a_in) ** 2 + abs(a_out) ** 2
    z = 0.0
    for _ in range(n):
        k1i, k1o = _rhs(z, a_in, a_out, d, k)
        k2i, k2o = _rhs(z + h / 2, a_in + h / 2 * k1i,
                        a_out + h / 2 * k1o, d, k)
        k3i, k3o = _rhs(z + h / 2, a_in + h / 2 * k2i,
                        a_out + h / 2 * k2o, d, k)
        k4i, k4o = _rhs(z + h, a_in + h * k3i, a_out + h * k3o, d, k)
        a_in += h / 6 * (k1i + 2 * k2i + 2 * k3i + k4i)
        a_out += h / 6 * (k1o + 2 * k2o + 2 * k3o + k4o)
        z += h
    n1 = abs(a_in) ** 2 + abs(a_out) ** 2
    return CoupledModeState(a_in, a_out, n0, n1)


def undepleted_conversion(dk: float, L: float, kappa: float = 1.0,
                          n_steps: int = DEFAULT_STEPS) -> complex:
    """The converted amplitude with the pump held fixed (undepleted limit).

    ``a_out(L) = i*kappa * integral_0^L exp(i*dk*z) dz``. Its squared
    modulus is exactly ``conversion_efficiency(dk, L, kappa)``, which is
    how the numerical integration and the closed ``sinc**2`` form are tied
    together.
    """
    return qpm_effective_coupling(dk, None, L, kappa, n_steps)


# --- (4) the dynamic (chirped) grating -----------------------------------

def _cumulative_phase(dk_values: np.ndarray, z: np.ndarray) -> np.ndarray:
    """Trapezoidal running integral ``integral_0^z dk(z') dz'``."""
    phase = np.zeros_like(z)
    dz = np.diff(z)
    incr = 0.5 * (dk_values[1:] + dk_values[:-1]) * dz
    phase[1:] = np.cumsum(incr)
    return phase


def dynamic_qpm(dk_of_z, L: float, kappa: float = 1.0,
                n_steps: int = DEFAULT_STEPS) -> complex:
    """Converted amplitude for a ``z``-dependent residual mismatch.

    Integrates ``a_out(L) = i*kappa * integral_0^L
    exp(i*integral_0^z dk(z') dz') dz`` in the undepleted limit, where
    ``dk_of_z`` is the residual mismatch left after a (possibly chirped)
    grating. A grating whose local period sweeps makes ``dk(z)`` pass
    through zero for a whole band of inputs, which is what broadens the
    acceptance.

    Returns the complex ``a_out(L)``.
    """
    if not callable(dk_of_z):
        raise QPMError("dk_of_z must be a callable z -> residual mismatch")
    length = _positive(L, "the interaction length")
    k = _finite(kappa, "the coupling")
    z = _grid(length, n_steps)
    dk_values = np.array([_finite(dk_of_z(float(zi)), "dk(z)") for zi in z])
    phase = _cumulative_phase(dk_values, z)
    return 1j * k * np.trapezoid(np.exp(1j * phase), z)


def fixed_grating_mismatch(detuning: float):
    """Residual mismatch of a *fixed* grating: a constant ``detuning``.

    A fixed grating cancels exactly one mismatch, so the residual is the
    constant offset from that value and the conversion follows the narrow
    ``sinc**2`` acceptance.
    """
    d = _finite(detuning, "the detuning")
    return lambda z: d


def chirped_grating_mismatch(detuning: float, chirp: float, L: float):
    """Residual mismatch of a *chirped* grating swept about mid-length.

    The grating vector varies linearly along ``z``, so the residual
    mismatch is ``detuning + chirp*(z - L/2)`` and passes through zero
    somewhere in ``[0, L]`` for every ``detuning`` in a band of width
    ``|chirp|*L`` — a broad, flat-topped acceptance.
    """
    d = _finite(detuning, "the detuning")
    c = _finite(chirp, "the chirp rate")
    length = _positive(L, "the interaction length")
    return lambda z: d + c * (z - length / 2.0)


def acceptance_bandwidth(mismatch_factory, L: float, detunings=None,
                         kappa: float = 1.0, n_steps: int = DEFAULT_STEPS,
                         span: float = 12.0, n_points: int = 241) -> dict:
    """Half-maximum acceptance width of a grating over an input detuning.

    ``mismatch_factory(detuning)`` returns the residual-mismatch callable
    for that input detuning. The conversion ``|a_out|**2`` is swept over a
    symmetric grid of detunings and the full width at half maximum is
    measured. A chirped grating returns a larger width than a fixed one.
    """
    length = _positive(L, "the interaction length")
    if detunings is None:
        if n_points < 3:
            raise QPMError("a bandwidth sweep needs at least three points")
        detunings = np.linspace(-abs(span) / 2.0, abs(span) / 2.0,
                                int(n_points))
    grid = np.asarray(detunings, dtype=float)
    if grid.size < 3:
        raise QPMError("a bandwidth sweep needs at least three detunings")
    conv = np.array([
        abs(dynamic_qpm(mismatch_factory(float(d)), length, kappa,
                        n_steps)) ** 2 for d in grid])
    peak = float(conv.max())
    if peak <= 0.0:
        raise QPMError("no conversion anywhere on the sweep")
    above = grid[conv >= peak / 2.0]
    fwhm = float(above.max() - above.min()) if above.size else 0.0
    return {
        "detunings": grid.tolist(),
        "conversion": conv.tolist(),
        "peak": peak,
        "fwhm": fwhm,
        "measured_here": MEASURED_HERE,
    }


def chirped_broadens_bandwidth(L: float = 10.0, chirp: float = 0.8,
                               kappa: float = 1.0,
                               n_steps: int = DEFAULT_STEPS) -> dict:
    """Compare fixed and chirped acceptance bandwidths on the same length.

    The chirped grating sweeps its grating vector along the crystal, so it
    accepts a band of mismatches while the fixed grating accepts only the
    narrow ``sinc**2`` peak. The chirped FWHM is the larger.
    """
    fixed = acceptance_bandwidth(fixed_grating_mismatch, L, kappa=kappa,
                                 n_steps=n_steps)
    chirped = acceptance_bandwidth(
        lambda d: chirped_grating_mismatch(d, chirp, L), L, kappa=kappa,
        n_steps=n_steps)
    return {
        "L": _positive(L, "the interaction length"),
        "chirp": _finite(chirp, "the chirp rate"),
        "fixed_fwhm": fixed["fwhm"],
        "chirped_fwhm": chirped["fwhm"],
        "chirped_broadens": bool(chirped["fwhm"] > fixed["fwhm"]),
        "broadening_ratio": (chirped["fwhm"] / fixed["fwhm"]
                             if fixed["fwhm"] > 0 else math.inf),
        "verdict": VERDICT,
        "measured_here": MEASURED_HERE,
    }


# --- (5) the required refusal --------------------------------------------

def refuse_model_conversion_as_measured(dk: float = 0.0, L: float = 1.0,
                                        context: str = "") -> None:
    """Refuse reading a computed conversion efficiency as a measurement.

    Raises unconditionally. :func:`conversion_efficiency` and the
    coupled-mode integrators return numbers from a declared model; a
    second-harmonic or parametric output is a photon count at a detector,
    obtained from a poled crystal, a pump, a filter and a calibrated
    photodiode — none of which exist here.
    """
    tail = f" ({context})" if context else ""
    eff = conversion_efficiency(dk, L) if L > 0 else float("nan")
    raise QPMError(
        f"refusing to report a modelled conversion efficiency "
        f"(~{eff:.4g} at dk={float(dk):.4g}, L={float(L):.4g}){tail} as a "
        f"measured second-harmonic or parametric output. The number is a "
        f"numerical integral of a coupled-amplitude model: no crystal is "
        f"poled, no pump is launched, no filter or photodiode is present, "
        f"and nothing is calibrated. A measured conversion is a detected "
        f"photon count with an uncertainty and a null; this is "
        f"{CLAIM_CLASS}, and {PHYSICAL_VALIDATION}.")


# --- report --------------------------------------------------------------

def qpm_report(verdict: str = VERDICT) -> dict:
    """The standing statement of what this module computes and disclaims."""
    contrast = secular_growth_contrast()
    bandwidth = chirped_broadens_bandwidth()
    depleted = coupled_mode_solve(0.0, 3.0, kappa=1.0)
    return {
        "claim_class": CLAIM_CLASS,
        "claim_classes": list(CLAIM_CLASSES),
        "what_this_is": (
            "a coupled-amplitude model of quasi-phase-matching: the "
            "sinc-squared acceptance of uniform conversion, the secular "
            "growth a matched sign-flipping grating restores, the "
            "Manley-Rowe photon-number balance of the coupled equations, "
            "and the bandwidth a chirped grating buys"),
        "phase_mismatch": "Delta_k = k_out - k_in - k_grating",
        "conversion_efficiency": "(kappa*L)**2 * sinc**2(Delta_k*L/2)",
        "efficiency_at_perfect_matching_grows_as": "L**2",
        "efficiency_zeros_at": "Delta_k*L/2 = n*pi",
        "secular_growth_contrast": contrast,
        "manley_rowe": {
            "invariant": "|a_in|**2 + |a_out|**2",
            "photon_number_initial": depleted.photon_number_initial,
            "photon_number_final": depleted.photon_number_final,
            "defect": depleted.manley_rowe_defect,
            "note": ("the pump depletes exactly as the harmonic grows; "
                     "the total photon number is conserved"),
        },
        "dynamic_qpm": bandwidth,
        "evidence_class": EVIDENCE_CLASS,
        "hardware_status": (
            "DEFERRED — no crystal poled, no beam launched, no harmonic "
            "or parametric output detected"),
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any crystal was poled, any pump beam existed, "
            "or any second-harmonic or parametric output was generated or "
            "measured. Every efficiency, amplitude, growth ratio and "
            "bandwidth is a numerical integration of a declared "
            "coupled-amplitude model in dimensionless units. It does not "
            "say a matched or chirped grating was fabricated, that a "
            "poling period was etched, or that any acceptance bandwidth "
            "was observed on a bench. The Manley-Rowe balance is a "
            "property of the model equations, not a measured energy "
            "ledger, and a computed conversion is refused as a "
            "measurement by refuse_model_conversion_as_measured."),
        "verdict": verdict,
    }


__all__ = [
    "VERDICT", "CLAIM_CLASS", "CLAIM_CLASSES", "EVIDENCE_CLASS",
    "MEASURED_HERE", "PHYSICAL_VALIDATION", "DEFAULT_STEPS",
    "QPMError",
    "sinc_squared", "conversion_efficiency", "coherence_length",
    "qpm_effective_coupling", "matched_period", "secular_growth_contrast",
    "CoupledModeState", "coupled_mode_solve", "undepleted_conversion",
    "dynamic_qpm", "fixed_grating_mismatch", "chirped_grating_mismatch",
    "acceptance_bandwidth", "chirped_broadens_bandwidth",
    "refuse_model_conversion_as_measured",
    "qpm_report",
]
