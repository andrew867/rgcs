"""P14 — a two-channel (I/Q) quadrature field and a transducer model.

Both quadratures of a narrow-band signal are the phase-space coordinates
of the symplectic layer next door: measuring a signal's amplitude and
phase together means measuring ``I`` and ``Q``, and this module builds
the standard I/Q demodulator that does it, plus a linear transducer that
carries a mechanical quadrature into an electrical one.

**I/Q demodulation.** A tone ``s(t) = A cos(w t + phi)`` mixed against a
cosine and a sine reference at the same frequency, then low-passed, gives

    I = <s(t) * cos(w t)> = A cos(phi) / 2,
    Q = -<s(t) * sin(w t)> = A sin(phi) / 2,

because the averages of ``cos^2`` and ``sin^2`` over whole periods are
``1/2`` and the average of ``sin*cos`` is zero. The **complex amplitude**
is then ``a = I + iQ``, whose magnitude is ``A/2`` and whose argument is
``phi``, so ``A = 2|a|`` and ``phi = arg(a)`` recover the tone exactly.

**Quadrature variances and a squeezing readout.** Given a covariance in
``(I, Q)`` the two diagonal entries are the quadrature variances, and one
of them sitting below a symmetric reference is the algebraic signature of
squeezing. It is a **model** readout, not an observed squeezed state, and
:func:`refuse_model_squeezing_as_observed` refuses the confusion.

**The transducer.** A :class:`Transducer` maps a mechanical quadrature to
an electrical one with a ``gain`` and an added ``noise_psd``. The output
variance is ``gain**2 * input_variance + noise_power``: the gain scales
the signal, and the added noise raises the variance by exactly the
added-noise term. The SNR degradation is exactly that added noise
referred back to the input, and nothing else.

**A bridge needs a certificate.** A transducer that carries energy from a
mechanical domain into an electrical one is a cross-domain coupling, and
under the R12/R13 rule such a transfer is refused without a coupling
certificate. :func:`refuse_transduction_without_certificate` is that
refusal; a certificate here is a licence to model, never a bench result.

Nothing is measured. No coil, electrode, mixer, filter, transducer or
squeezed source exists; every number is arithmetic on a declared model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim class, tolerances ------------------------------------

#: The standing verdict for this module.
VERDICT = "TWO_CHANNEL_QUADRATURE_TRANSDUCTION_MODEL"

#: What this module's output is: numerical processing of a declared,
#: synthetic signal. No apparatus is operated in it.
CLAIM_CLASS = "NUMERICAL_SIMULATION"

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

#: Relative tolerance when a recovered amplitude/phase is checked against
#: the synthetic tone it was built from.
DEMOD_TOL = 1e-9


class QuadFieldError(RuntimeError):
    """Raised when a quadrature/transducer claim exceeds the model.

    Covers the structural guards (a non-positive frequency, mismatched
    time and signal, a non-positive gain) and the two load-bearing
    refusals: :func:`refuse_model_squeezing_as_observed` and
    :func:`refuse_transduction_without_certificate`.
    """


# --- helpers -------------------------------------------------------------

def _finite(value: float, what: str) -> float:
    x = float(value)
    if not math.isfinite(x):
        raise QuadFieldError(f"{what} must be finite")
    return x


def _positive(value: float, what: str) -> float:
    x = _finite(value, what)
    if x <= 0.0:
        raise QuadFieldError(f"{what} must be positive")
    return x


# --- (1) I/Q demodulation ------------------------------------------------

def synth_tone(amplitude: float, phase: float, w_ref: float,
               t) -> np.ndarray:
    """A synthetic tone ``A cos(w t + phi)`` sampled at times ``t``.

    A declared signal generator: the tone the demodulator is tested
    against. Nothing is emitted; this is arithmetic on a numpy array.
    """
    a = _finite(amplitude, "the amplitude")
    phi = _finite(phase, "the phase")
    w = _positive(w_ref, "the reference angular frequency")
    time = np.asarray(t, dtype=float)
    return a * np.cos(w * time + phi)


@dataclass(frozen=True)
class IQResult:
    """The outcome of an I/Q demodulation: the two quadratures.

    ``i`` and ``q`` are ``A cos(phi)/2`` and ``A sin(phi)/2``. The complex
    amplitude ``a = I + iQ`` has magnitude ``A/2`` and argument ``phi``.
    """

    i: float
    q: float

    @property
    def amplitude_component(self) -> complex:
        """The complex amplitude ``a = I + iQ``."""
        return complex(self.i, self.q)

    @property
    def magnitude(self) -> float:
        """``|a| = A/2`` for a demodulated tone of amplitude ``A``."""
        return float(math.hypot(self.i, self.q))

    @property
    def phase(self) -> float:
        """``arg(a) = phi``, in radians."""
        return float(math.atan2(self.q, self.i))

    @property
    def recovered_amplitude(self) -> float:
        """``A = 2|a|``: the tone amplitude the quadratures encode."""
        return 2.0 * self.magnitude

    @property
    def recovered_power(self) -> float:
        """``A**2/2``: the average power of the recovered tone."""
        a = self.recovered_amplitude
        return 0.5 * a * a

    def as_dict(self) -> dict:
        return {
            "i": self.i,
            "q": self.q,
            "magnitude": self.magnitude,
            "phase": self.phase,
            "recovered_amplitude": self.recovered_amplitude,
            "recovered_power": self.recovered_power,
            "measured_here": MEASURED_HERE,
        }


def iq_demodulate(signal, t, w_ref: float) -> IQResult:
    """Demodulate a signal into its in-phase and quadrature components.

    Mixes ``signal`` against ``cos(w t)`` and ``sin(w t)`` at the
    reference angular frequency ``w_ref`` and low-passes by averaging over
    the record:

        I = mean(signal * cos(w t)) = A cos(phi) / 2,
        Q = -mean(signal * sin(w t)) = A sin(phi) / 2

    for a tone ``A cos(w t + phi)`` sampled over whole periods. The sign
    on ``Q`` is the convention that makes ``a = I + iQ`` carry the tone's
    own phase ``phi`` rather than its negative.
    """
    w = _positive(w_ref, "the reference angular frequency")
    s = np.asarray(signal, dtype=float)
    time = np.asarray(t, dtype=float)
    if s.shape != time.shape:
        raise QuadFieldError(
            f"signal and time must have the same shape, got {s.shape} and "
            f"{time.shape}")
    if s.size < 2:
        raise QuadFieldError("a demodulation needs at least two samples")
    i = float(np.mean(s * np.cos(w * time)))
    q = float(-np.mean(s * np.sin(w * time)))
    return IQResult(i, q)


def demodulation_check(amplitude: float = 3.0, phase: float = 0.6,
                       w_ref: float = 2.0 * math.pi * 100.0,
                       periods: int = 50, samples_per_period: int = 64
                       ) -> dict:
    """Round-trip: synthesise a tone, demodulate it, recover A and phi.

    The record spans a whole number of drive periods so the ``cos^2`` and
    ``sin^2`` averages are exactly ``1/2`` and the ``sin*cos`` average is
    exactly zero, which is what makes the recovery exact rather than
    approximate.
    """
    a = _finite(amplitude, "the amplitude")
    phi = _finite(phase, "the phase")
    w = _positive(w_ref, "the reference angular frequency")
    n_per = int(periods)
    n_pp = int(samples_per_period)
    if n_per < 1 or n_pp < 2:
        raise QuadFieldError(
            "need at least one period and two samples per period")
    period = 2.0 * math.pi / w
    n = n_per * n_pp
    t = np.linspace(0.0, n_per * period, n, endpoint=False)
    signal = synth_tone(a, phi, w, t)
    result = iq_demodulate(signal, t, w)
    return {
        "amplitude_in": a,
        "phase_in": phi,
        "i": result.i,
        "q": result.q,
        "expected_i": 0.5 * a * math.cos(phi),
        "expected_q": 0.5 * a * math.sin(phi),
        "recovered_amplitude": result.recovered_amplitude,
        "recovered_phase": result.phase,
        "recovered_power": result.recovered_power,
        "expected_power": 0.5 * a * a,
        "amplitude_recovered": bool(
            abs(result.recovered_amplitude - a) <= DEMOD_TOL * max(1.0, a)),
        "phase_recovered": bool(abs(result.phase - phi) <= DEMOD_TOL),
        "measured_here": MEASURED_HERE,
    }


# --- (2) quadrature variances and the squeezing readout ------------------

def _as_iq_covariance(cov) -> np.ndarray:
    """A finite, symmetric 2x2 covariance in the (I, Q) plane."""
    c = np.asarray(cov, dtype=float)
    if c.shape != (2, 2):
        raise QuadFieldError(f"an (I,Q) covariance must be 2x2, got {c.shape}")
    if not np.all(np.isfinite(c)):
        raise QuadFieldError("an (I,Q) covariance must be finite")
    if not np.allclose(c, c.T, atol=1e-12, rtol=0.0):
        raise QuadFieldError(
            "an (I,Q) covariance must be symmetric; an asymmetric 2x2 has "
            "no well-defined quadrature variances")
    return c


def quadrature_variances(cov) -> tuple[float, float]:
    """The ``(var_I, var_Q)`` quadrature variances from the diagonal."""
    c = _as_iq_covariance(cov)
    return (float(c[0, 0]), float(c[1, 1]))


def squeezing_readout(cov, reference: float = 1.0) -> dict:
    """Report both quadrature variances and whether one is below reference.

    A variance below the symmetric reference is the algebraic indicator of
    squeezing in that quadrature. This is a MODEL readout of a declared
    covariance; it is not a measured squeezed state, and
    :func:`refuse_model_squeezing_as_observed` refuses that reading.
    """
    ref = _positive(reference, "the symmetric reference variance")
    var_i, var_q = quadrature_variances(cov)
    if var_i < 0.0 or var_q < 0.0:
        raise QuadFieldError("a variance cannot be negative")
    below = []
    if var_i < ref:
        below.append("I")
    if var_q < ref:
        below.append("Q")
    return {
        "var_i": var_i,
        "var_q": var_q,
        "reference": ref,
        "quadrature_below_reference": below,
        "squeezing_indicated": bool(below),
        "uncertainty_product": float(var_i * var_q),
        "note": ("a variance below the symmetric reference is the "
                 "algebraic signature of squeezing; here it is a readout "
                 "of a declared covariance, not a measured squeezed state"),
        "claim_class": "ANALYTIC_MODEL",
        "measured_here": MEASURED_HERE,
    }


def refuse_model_squeezing_as_observed(
        claim: str = "a squeezed state was observed") -> None:
    """Refuse reading a modelled variance dip as an observed squeezed state.

    Always raises. A quadrature variance below a reference in a declared
    covariance is arithmetic; an observed squeezed state needs a source, a
    calibrated shot-noise reference, a homodyne detector and a measured
    variance below it. None of those exists here, so the readout indicates
    squeezing in a model and establishes nothing on a bench.
    """
    raise QuadFieldError(
        f"refused: {claim!r} is a BENCH_MEASUREMENT claim. A variance below "
        f"the symmetric reference in this module is a property of a declared "
        f"(I,Q) covariance, not a reading from a homodyne detector against a "
        f"calibrated shot-noise level. No squeezed light or motional "
        f"squeezed state was generated or measured; the readout is a model "
        f"indicator, and a model indicator is not an observation. {VERDICT}")


# --- (3) the transducer --------------------------------------------------

class TransducerDomain(Enum):
    """The physical domains a transducer bridges. Units differ across all."""

    MECHANICAL = "MECHANICAL"
    ELECTRICAL = "ELECTRICAL"


@dataclass(frozen=True)
class Transducer:
    """A linear transducer: mechanical quadrature in, electrical out.

    ``gain`` scales the input quadrature and ``noise_psd`` is the variance
    of the noise the transducer adds at its output, referred to the output
    (an added noise power). The output variance of a signal with input
    variance ``v`` is ``gain**2 * v + noise_psd``.

    ``certified`` records whether a coupling certificate licenses the
    mechanical-to-electrical transfer. It defaults to ``False``: the
    default is refusal, matching the R12/R13 bridge rule, and
    :func:`refuse_transduction_without_certificate` enforces it.
    """

    gain: float
    noise_psd: float
    source_domain: TransducerDomain = TransducerDomain.MECHANICAL
    target_domain: TransducerDomain = TransducerDomain.ELECTRICAL
    certified: bool = False

    def __post_init__(self) -> None:
        if not math.isfinite(float(self.gain)) or float(self.gain) <= 0.0:
            raise QuadFieldError("the transducer gain must be finite and "
                                 "positive")
        if not math.isfinite(float(self.noise_psd)) or float(self.noise_psd) \
                < 0.0:
            raise QuadFieldError("the added noise power must be finite and "
                                 "non-negative")

    def transduce(self, signal) -> np.ndarray:
        """Scale an input quadrature by the gain (the deterministic part)."""
        return float(self.gain) * np.asarray(signal, dtype=float)

    def output_variance(self, input_variance: float) -> float:
        """``gain**2 * input_variance + noise_psd``.

        The gain multiplies the signal variance by ``gain**2`` and the
        added noise raises the total by exactly ``noise_psd``.
        """
        v = _finite(input_variance, "the input variance")
        if v < 0.0:
            raise QuadFieldError("a variance cannot be negative")
        return float(self.gain) ** 2 * v + float(self.noise_psd)

    def added_variance(self) -> float:
        """The excess output variance the transducer contributes: ``noise_psd``."""
        return float(self.noise_psd)

    def referred_input_noise(self) -> float:
        """The added noise referred to the input: ``noise_psd / gain**2``.

        This is the input-equivalent noise the transducer injects, and it
        is exactly what degrades the SNR when the input already carries
        noise of its own.
        """
        return float(self.noise_psd) / float(self.gain) ** 2

    def output_snr(self, signal_variance: float,
                   input_noise_variance: float) -> float:
        """Output SNR ``= gain**2 S / (gain**2 N_in + noise_psd)``."""
        s = _finite(signal_variance, "the signal variance")
        n_in = _finite(input_noise_variance, "the input noise variance")
        if s < 0.0 or n_in < 0.0:
            raise QuadFieldError("a variance cannot be negative")
        denom = float(self.gain) ** 2 * n_in + float(self.noise_psd)
        if denom <= 0.0:
            raise QuadFieldError(
                "output SNR is undefined with no noise anywhere")
        return float(self.gain) ** 2 * s / denom

    def snr_degradation(self, signal_variance: float,
                        input_noise_variance: float) -> dict:
        """How much the transducer degrades the SNR, and why.

        The input SNR is ``S / N_in`` and the output SNR is
        ``S / (N_in + noise_psd/gain**2)``. The ratio is therefore

            SNR_in / SNR_out = 1 + (noise_psd/gain**2) / N_in,

        so the *excess* is exactly the added noise referred to the input,
        divided by the input noise -- the added-noise term and nothing
        else. The gain cancels out of the SNR itself and survives only
        through the referred noise.
        """
        s = _positive(signal_variance, "the signal variance")
        n_in = _positive(input_noise_variance, "the input noise variance")
        snr_in = s / n_in
        snr_out = self.output_snr(s, n_in)
        referred = self.referred_input_noise()
        return {
            "snr_in": float(snr_in),
            "snr_out": float(snr_out),
            "degradation_factor": float(snr_in / snr_out),
            "excess_from_added_noise": float(referred / n_in),
            "referred_input_noise": float(referred),
            "gain_cancels_from_snr": True,
            "note": ("the SNR degradation is exactly the added noise "
                     "referred to the input divided by the input noise; "
                     "the gain scales signal and noise together and drops "
                     "out"),
            "measured_here": MEASURED_HERE,
        }

    def as_dict(self) -> dict:
        return {
            "gain": float(self.gain),
            "noise_psd": float(self.noise_psd),
            "source_domain": self.source_domain.value,
            "target_domain": self.target_domain.value,
            "certified": self.certified,
            "referred_input_noise": self.referred_input_noise(),
            "measured_here": MEASURED_HERE,
        }


def refuse_transduction_without_certificate(
        transducer: Transducer | None = None,
        claim: str = "a mechanical quadrature was read out electrically",
        ) -> None:
    """Refuse a cross-domain transduction that carries no certificate.

    Raises whenever the transducer is uncertified (or absent). A
    transducer that carries energy from the mechanical domain into the
    electrical one is a cross-domain coupling, and under the R12/R13
    bridge rule such a transfer is refused by default: it is licensed only
    by a coupling certificate that declares the operator, the units, the
    constitutive law, the overlap, the energy path and a falsifying
    measurement. Even a complete certificate is a licence to model, not
    evidence, so this never returns a bench result.
    """
    certified = bool(getattr(transducer, "certified", False))
    if certified:
        raise QuadFieldError(
            f"{claim!r} runs through a certificate, which licenses the "
            f"mechanical->electrical MODEL only. A certificate is a licence "
            f"to model, not a measurement: no bench operated the transducer "
            f"here, and the coupling remains AWAITING_FALSIFICATION until a "
            f"falsifying measurement is performed, which this repository "
            f"cannot do. {VERDICT}")
    raise QuadFieldError(
        f"refused: {claim!r} bridges the MECHANICAL and ELECTRICAL domains "
        f"with no coupling certificate. The default for a cross-domain "
        f"transfer is refusal (R12/R13): a mechanical quadrature and an "
        f"electrical one carry different units and different constitutive "
        f"laws, and mapping one to the other requires a certificate "
        f"declaring the coupling operator, the overlap, the energy path, "
        f"and a measurement able to falsify it. None is supplied. {VERDICT}")


# --- (4) report ----------------------------------------------------------

def quadfield_report() -> dict:
    """The standing statement of what this module is and is not."""
    demod = demodulation_check()
    return {
        "claim_class": CLAIM_CLASS,
        "what_this_is": (
            "a two-channel I/Q quadrature demodulator, a complex-amplitude "
            "readout, a quadrature-variance squeezing indicator, and a "
            "linear mechanical->electrical transducer model with gain and "
            "added noise"),
        "iq_demodulation": {
            "definition": ("I = mean(s*cos(w t)) = A cos(phi)/2; "
                           "Q = -mean(s*sin(w t)) = A sin(phi)/2"),
            "complex_amplitude": "a = I + iQ, |a| = A/2, arg(a) = phi",
            "amplitude_recovered": demod["amplitude_recovered"],
            "phase_recovered": demod["phase_recovered"],
        },
        "transducer": {
            "output_variance": "gain**2 * input_variance + noise_psd",
            "snr_degradation": "1 + (noise_psd/gain**2)/N_in, "
                               "the added noise referred to the input",
        },
        "firewalls": [
            "a modelled quadrature-variance dip is not an observed "
            "squeezed state -- refuse_model_squeezing_as_observed",
            "a mechanical->electrical transduction is refused without a "
            "coupling certificate, and a certificate is a licence to model "
            "not a bench result -- refuse_transduction_without_certificate",
        ],
        "verdict": VERDICT,
        "claim_classes": list(CLAIM_CLASSES),
        "evidence_class": "DERIVED_MATHEMATICS",
        "hardware_status": (
            "DEFERRED -- no coil, electrode, mixer, low-pass filter, "
            "transducer or squeezed source has been built or operated"),
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any signal was received, mixed, filtered or "
            "demodulated on a bench, that any quadrature variance was "
            "measured, or that squeezing was observed below a calibrated "
            "shot-noise reference. It does not say any transducer was "
            "built or that a mechanical quadrature was read out "
            "electrically: that transfer is a cross-domain coupling refused "
            "without a certificate, and a certificate licenses a model, not "
            "a measurement. Every tone, covariance and transducer parameter "
            "is a declared number, and every result is arithmetic on it."),
    }


__all__ = [
    "VERDICT", "CLAIM_CLASS", "CLAIM_CLASSES", "MEASURED_HERE",
    "PHYSICAL_VALIDATION", "DEMOD_TOL", "QuadFieldError",
    "synth_tone", "IQResult", "iq_demodulate", "demodulation_check",
    "quadrature_variances", "squeezing_readout",
    "refuse_model_squeezing_as_observed",
    "TransducerDomain", "Transducer",
    "refuse_transduction_without_certificate",
    "quadfield_report",
]
