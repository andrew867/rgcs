"""P18 — heterodyne detection of a cavity, as a readout MODEL.

Heterodyne detection beats a signal against a local oscillator (LO) held
at an offset frequency, and reads the resulting **intermediate frequency**
(IF) tone. The IF band carries the signal's amplitude and phase intact,
which is the whole point of the technique: a fast, high-frequency signal
becomes a slow IF tone that a modest front-end can digitise without
throwing away the quadrature information a homodyne receiver would keep
only for a single phase.

This module builds that chain as an **analytic model** and nothing more.

**The mix.** A signal at angular frequency ``w_s`` multiplied by an LO at
``w_lo`` produces sum and difference components. The difference sits at
the IF ``w_if = |w_s - w_lo|`` and preserves both the amplitude and the
phase of the original tone; the sum sits at ``w_s + w_lo``. Both are real
sidebands of the product, and the presence of the second one is the
*image*: a heterodyne receiver folds an image band onto the same IF, and
pretending the image is not there is how a heterodyne noise budget is
quietly understated.

**The standard-quantum-limit penalty, as a budget not a floor.** Because
the image band contributes its own half-quantum of vacuum fluctuation, an
ideal heterodyne receiver carries *twice* the added noise of an ideal
homodyne one -- the textbook 3 dB heterodyne penalty. This module carries
that as an ``ANALYTIC_MODEL`` noise budget: :func:`heterodyne_penalty_db`
returns 3 dB because the modelled floors are in the ratio two-to-one, and
it is emphatically **not** a measured noise floor of any receiver.

**The cavity.** A resonator responds to a probe with a Lorentzian
lineshape: :func:`cavity_response` returns the complex transmission of a
cavity of linewidth ``kappa`` at detuning ``detuning``. Its power
transmission is a Lorentzian of full width at half maximum exactly equal
to ``kappa``, and its phase rolls through ``pi`` as the probe is swept
across resonance. The dispersive (phase) quadrature of that response is an
antisymmetric error signal with a zero crossing exactly on resonance --
the Pound-Drever-Hall-style discriminant a lock would ride.

**No promotion.** A computed heterodyne spectrum is a model output, not a
reading off an instrument. :func:`refuse_model_readout_as_measured`
refuses that promotion. Nothing here is measured: no oscillator is built,
no cavity is probed, no photocurrent is digitised, and the verdict is
``HETERODYNE_CAVITY_READOUT_MODEL``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict and claim vocabulary -----------------------------------------

#: The standing verdict for this module.
VERDICT = "HETERODYNE_CAVITY_READOUT_MODEL"

ANALYTIC_MODEL = "ANALYTIC_MODEL"
NUMERICAL_SIMULATION = "NUMERICAL_SIMULATION"
BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Numerical tolerance for the modelled identities reported here.
MODEL_TOL = 1e-9


class HeterodyneError(RuntimeError):
    """Raised when a heterodyne/cavity statement exceeds the model.

    Covers the structural guards (mismatched arrays, a non-positive
    linewidth) and the load-bearing refusal
    :func:`refuse_model_readout_as_measured`.
    """


# --- the two receiver schemes ---------------------------------------------

class Scheme(Enum):
    """A coherent-detection scheme, by how many quadratures it reads."""

    HOMODYNE = "homodyne"       # one quadrature, no image band
    HETERODYNE = "heterodyne"   # both quadratures, an image band


# --- tone projection (a shared helper) ------------------------------------

def tone_amplitude(x: np.ndarray, t: np.ndarray, w: float) -> complex:
    """Complex amplitude of the tone at angular frequency ``w`` in ``x``.

    For ``x = A*cos(w*t + phi)`` sampled over an integer number of cycles
    this returns ``A*exp(1j*phi)`` -- amplitude ``A`` and phase ``phi`` --
    because the counter-rotating term averages to zero. For a single
    complex exponential ``(A)*exp(1j*(w*t + phi))`` it returns the same,
    which is how the IF tone of a complex mix is read back.
    """
    xa = np.asarray(x)
    ta = np.asarray(t, dtype=float)
    if xa.shape != ta.shape:
        raise HeterodyneError("signal and time base must have the same shape")
    if xa.size == 0:
        raise HeterodyneError("an empty record carries no tone")
    return 2.0 * np.mean(xa * np.exp(-1j * float(w) * ta))


# --- the heterodyne mix ----------------------------------------------------

@dataclass(frozen=True)
class MixResult:
    """The product of a signal with a local oscillator.

    ``mixed`` is the complex (I/Q) product ``signal * exp(-1j*w_lo*t)``,
    whose difference component sits at the signed IF ``w_s - w_lo`` and
    carries the signal's amplitude and phase. ``real_mixed`` is the
    real-LO product ``signal * cos(w_lo*t)``, which exposes BOTH sidebands
    -- the difference at ``|w_s - w_lo|`` and the image sum at
    ``w_s + w_lo`` -- each at half the signal amplitude.
    """

    t: np.ndarray
    w_lo: float
    lo_phase: float
    mixed: np.ndarray
    real_mixed: np.ndarray

    def if_tone(self, w_if_signed: float) -> complex:
        """Complex amplitude of the IF tone at signed IF ``w_s - w_lo``.

        Reads back ``A*exp(1j*phi)`` for an input ``A*cos(w_s*t + phi)``:
        the difference component of a complex mix is a single complex
        exponential, and projecting it recovers amplitude and phase.
        """
        return 2.0 * np.mean(self.mixed * np.exp(-1j * float(w_if_signed)
                                                  * self.t))

    def sideband_amplitude(self, w: float) -> complex:
        """Complex amplitude of the real-mix sideband at angular ``w``."""
        return tone_amplitude(self.real_mixed, self.t, w)


def heterodyne_mix(signal: np.ndarray, t: np.ndarray, w_lo: float,
                   lo_phase: float = 0.0) -> MixResult:
    """Beat ``signal`` against a local oscillator at ``w_lo``.

    Returns a :class:`MixResult` holding both the complex I/Q product
    (used to read the IF amplitude and phase) and the real-LO product
    (used to see both sidebands, i.e. the image). No filtering is applied:
    the sum and difference components are both present, and it is the
    caller who projects onto whichever the model is about.
    """
    sig = np.asarray(signal, dtype=float)
    ta = np.asarray(t, dtype=float)
    if sig.shape != ta.shape:
        raise HeterodyneError("signal and time base must have the same shape")
    if sig.size == 0:
        raise HeterodyneError("nothing to mix: the record is empty")
    w = float(w_lo)
    phase = float(lo_phase)
    lo_complex = np.exp(-1j * (w * ta + phase))
    lo_real = np.cos(w * ta + phase)
    return MixResult(
        t=ta,
        w_lo=w,
        lo_phase=phase,
        mixed=sig * lo_complex,
        real_mixed=sig * lo_real,
    )


def intermediate_frequency(w_s: float, w_lo: float) -> float:
    """``w_if = |w_s - w_lo|``. The IF is the magnitude of the difference."""
    return abs(float(w_s) - float(w_lo))


def image_frequency(w_s: float, w_lo: float) -> float:
    """``w_image = w_s + w_lo``. The sum sideband a real mix also produces."""
    return abs(float(w_s) + float(w_lo))


# --- the standard-quantum-limit noise budget (a MODEL) --------------------

def added_noise_quanta(scheme: Scheme) -> float:
    """Added noise quanta referred to the input, as a model figure.

    A homodyne receiver reads a single quadrature and adds nothing beyond
    the vacuum it already measures. A heterodyne receiver reads both
    quadratures at once and pays a half-quantum of extra vacuum noise from
    the image band. These are the textbook ideal-receiver figures, carried
    as a model, not a measurement.
    """
    if scheme is Scheme.HOMODYNE:
        return 0.0
    if scheme is Scheme.HETERODYNE:
        return 0.5
    raise HeterodyneError(f"unknown detection scheme {scheme!r}")


def noise_floor(scheme: Scheme, zero_point_quanta: float = 0.5) -> float:
    """Modelled noise floor: the vacuum half-quantum plus the added noise.

    Homodyne -> ``0.5``; heterodyne -> ``1.0``. The ratio is the 3 dB
    penalty, and it is an ``ANALYTIC_MODEL`` budget, not a measured floor.
    """
    zpf = float(zero_point_quanta)
    if zpf <= 0.0:
        raise HeterodyneError("the zero-point noise must be positive")
    return zpf + added_noise_quanta(scheme)


def heterodyne_penalty_db(zero_point_quanta: float = 0.5) -> float:
    """The modelled heterodyne-over-homodyne noise penalty, in decibels.

    Returns ``10*log10(2) ~= 3.0103`` dB because the modelled heterodyne
    floor is exactly twice the homodyne one. This is a noise BUDGET, not a
    measured noise floor of any receiver.
    """
    ratio = (noise_floor(Scheme.HETERODYNE, zero_point_quanta)
             / noise_floor(Scheme.HOMODYNE, zero_point_quanta))
    return float(10.0 * np.log10(ratio))


def noise_budget() -> dict:
    """The full modelled noise budget, both schemes, with the penalty."""
    hom = noise_floor(Scheme.HOMODYNE)
    het = noise_floor(Scheme.HETERODYNE)
    return {
        "homodyne_floor_quanta": hom,
        "heterodyne_floor_quanta": het,
        "ratio": het / hom,
        "penalty_db": heterodyne_penalty_db(),
        "penalty_is_3db": abs(heterodyne_penalty_db()
                              - 10.0 * float(np.log10(2.0))) <= MODEL_TOL,
        "claim_class": ANALYTIC_MODEL,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "note": ("the 3 dB penalty is the ideal image-band half-quantum "
                 "carried as a model budget; no receiver noise floor was "
                 "measured"),
    }


# --- the cavity: a Lorentzian resonator -----------------------------------

def cavity_response(detuning: float | np.ndarray,
                    kappa: float) -> complex | np.ndarray:
    """Complex transmission of a Lorentzian cavity of linewidth ``kappa``.

    ``t(Delta) = (kappa/2) / (kappa/2 + 1j*Delta)``. Its power transmission
    ``|t|**2`` is a Lorentzian with full width at half maximum exactly
    ``kappa`` (half-maximum at ``Delta = +/- kappa/2``). Its phase is
    ``-arctan(Delta/(kappa/2))``, which runs from ``+pi/2`` far below
    resonance through ``0`` on resonance to ``-pi/2`` far above -- a total
    roll of ``pi`` across the line.
    """
    k = float(kappa)
    if k <= 0.0:
        raise HeterodyneError("the linewidth kappa must be positive")
    hwhm = k / 2.0
    delta = np.asarray(detuning, dtype=float)
    resp = hwhm / (hwhm + 1j * delta)
    if resp.ndim == 0:
        return complex(resp)
    return resp


def cavity_transmission_power(detuning: float | np.ndarray,
                              kappa: float) -> float | np.ndarray:
    """``|t(Delta)|**2``: the Lorentzian power transmission."""
    return np.abs(cavity_response(detuning, kappa)) ** 2


def cavity_fwhm(kappa: float) -> float:
    """The full width at half maximum of the power transmission: ``kappa``."""
    k = float(kappa)
    if k <= 0.0:
        raise HeterodyneError("the linewidth kappa must be positive")
    return k


def pdh_error_signal(detuning: float | np.ndarray,
                     kappa: float) -> float | np.ndarray:
    """The dispersive (phase) quadrature error signal.

    ``e(Delta) = Im[t(Delta)] = -(kappa/2)*Delta / ((kappa/2)**2 +
    Delta**2)``. This is antisymmetric in the detuning, so it has a zero
    crossing exactly on resonance (``Delta = 0``), and its slope there is
    ``-2/kappa`` -- negative, so the signal is a restoring discriminant a
    lock can ride. It is a model of the Pound-Drever-Hall error signal,
    not a demodulated photocurrent.
    """
    k = float(kappa)
    if k <= 0.0:
        raise HeterodyneError("the linewidth kappa must be positive")
    hwhm = k / 2.0
    delta = np.asarray(detuning, dtype=float)
    err = -hwhm * delta / (hwhm ** 2 + delta ** 2)
    if err.ndim == 0:
        return float(err)
    return err


def pdh_slope_on_resonance(kappa: float) -> float:
    """``de/dDelta`` at resonance: ``-2/kappa``. Negative, hence restoring."""
    k = float(kappa)
    if k <= 0.0:
        raise HeterodyneError("the linewidth kappa must be positive")
    return -2.0 / k


# --- the load-bearing refusal ---------------------------------------------

def refuse_model_readout_as_measured(
        claim: str = "the heterodyne spectrum is a cavity readout") -> None:
    """A computed spectrum is not a measured cavity readout. Always raises.

    Every array in this module is produced by evaluating an analytic
    expression: a mix is a multiplication, a lineshape is a Lorentzian, an
    error signal is its imaginary part. None of it is a demodulated
    photocurrent from a probed resonator. Reading a model output as an
    instrument reading is the promotion this refusal blocks.
    """
    raise HeterodyneError(
        f"refused: {claim!r}. The IF tone, the sideband powers, the "
        f"Lorentzian transmission and the Pound-Drever-Hall error signal "
        f"here are all evaluated from closed-form expressions -- an "
        f"{ANALYTIC_MODEL}. No local oscillator was built, no cavity was "
        f"probed, and no photocurrent was digitised, so there is no "
        f"measured readout to promote. A modelled spectrum acquires the "
        f"standing of a measurement only when an apparatus produces it, "
        f"which did not happen here. {VERDICT}.")


# --- report ----------------------------------------------------------------

def heterodyne_report() -> dict:
    """The standing statement of what this module is and is not."""
    return {
        "what_this_is": (
            "an analytic model of heterodyne detection of a cavity: the "
            "mix to an intermediate frequency that preserves amplitude and "
            "phase, both sidebands (the image), the 3 dB standard-quantum-"
            "limit noise budget, a Lorentzian cavity response, and a "
            "Pound-Drever-Hall-style error signal"),
        "if_identity": "w_if = |w_s - w_lo|",
        "image_identity": "w_image = w_s + w_lo",
        "noise_budget": noise_budget(),
        "cavity_identity": "t(Delta) = (kappa/2)/(kappa/2 + 1j*Delta)",
        "cavity_fwhm_equals_kappa": True,
        "cavity_phase_roll_rad": float(np.pi),
        "pdh_zero_crossing_on_resonance": True,
        "pdh_slope_sign": "negative (restoring)",
        "refusals": ["refuse_model_readout_as_measured"],
        "claim_class": ANALYTIC_MODEL,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any heterodyne spectrum was measured, that any "
            "cavity was probed, or that any noise floor was recorded. The "
            "IF tone, the sidebands, the Lorentzian transmission and the "
            "error signal are all closed-form model outputs; the 3 dB "
            "penalty is an ideal-receiver budget, not a measured floor. No "
            "local oscillator, cavity or photodetector was operated, and a "
            "computed spectrum is not a cavity readout."),
    }


__all__ = [
    "VERDICT", "ANALYTIC_MODEL", "NUMERICAL_SIMULATION",
    "BLOCKED_MISSING_INPUT", "MEASURED_HERE", "PHYSICAL_VALIDATION",
    "MODEL_TOL", "HeterodyneError", "Scheme",
    "tone_amplitude", "MixResult", "heterodyne_mix",
    "intermediate_frequency", "image_frequency",
    "added_noise_quanta", "noise_floor", "heterodyne_penalty_db",
    "noise_budget", "cavity_response", "cavity_transmission_power",
    "cavity_fwhm", "pdh_error_signal", "pdh_slope_on_resonance",
    "refuse_model_readout_as_measured", "heterodyne_report",
]
