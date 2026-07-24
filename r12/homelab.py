"""R12 — home-lab experiments: mode, phase, ringdown and isotropy.

Four experiments are **designed and preregistered here, and none of them
is run**. There is no bench in this repository: no signal generator, no
amplifier, no resonator, no lock-in, no digitiser, no rotation stage and
no thermometer. This module follows the shape of :mod:`r11.rotfield`: it
enumerates the four experiments as a typed :class:`Experiment`, gives
each an :class:`ExperimentPlan` with its aim, drive, observables, sample
rate and anti-aliasing, its declared controls, its null model, its
falsification criterion and its cost tier, and carries every plan at
status ``BLOCKED_MISSING_DATA``. :func:`refuse_bench_claim` refuses to
let any of it be read as a result.

**Two estimators are real, and they are exercised on synthetic data.**

*Ringdown.* The quality factor of a decaying resonance is

    Q = pi * f0 * tau       (amplitude decay time tau)
      = f0 / FWHM           (Lorentzian full width at half maximum)

and the two are the same number because ``FWHM = 1/(pi*tau)`` for a
damped oscillator. :func:`ringdown_q_from_tau` and
:func:`ringdown_q_from_fwhm` compute both, :func:`fwhm_from_tau` relates
them, and :func:`estimate_ringdown_tau` recovers ``tau`` from a synthetic
exponentially-decaying ringdown by fitting the log of its analytic
envelope. Recovering a planted ``tau`` within tolerance is a
``REPOSITORY_COMPUTATIONAL_RESULT`` on numbers this module generated — it
is not a measurement of any resonator, and there is no ``f0``, ``tau`` or
``Q`` of any physical object anywhere in it.

*Isotropy.* An isotropy test compares a response across orientations.
:func:`isotropy_pvalue` runs a rotation-shuffle permutation null: it
pools the responses, reassigns them to angle bins at random many times,
and asks how often the shuffled orientation dependence is at least as
large as the observed one. Isotropic synthetic data give ``p`` that is
not small (the null holds); a planted ``cos(2*theta)`` anisotropy gives
``p`` small (the null is rejected). The demonstrations
:func:`isotropy_null_demo` and :func:`isotropy_power_demo` carry those
two cases.

**The isotropy firewall.** Alpha quartz is an anisotropic crystal — its
elastic, optical and piezoelectric properties depend on direction by its
very symmetry. So a real quartz specimen is *expected* to show
orientation dependence, and finding it is the **null hypothesis, not a
discovery**. :func:`refuse_anisotropy_as_anomaly` refuses to let observed
anisotropy in an anisotropic crystal be reported as an anomaly: the
surprising result would be isotropy, and even that would be a
measurement this module has not made.

**Controls are a precondition, not an afterthought.** Each experiment
declares the controls it cannot report a result without, and
:func:`refuse_result_without_controls` refuses a result while any
declared control is absent. Declaring a control is not running it, and
none has been run.

Nothing here is measured, driven, digitised or rotated.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

import numpy as np

# --- verdict, claim vocabulary, tolerances -------------------------------

#: The standing verdict for this module.
VERDICT = "HOME_LAB_EXPERIMENTS_PREREGISTERED_NOT_RUN"

#: The typed claim vocabulary, exact strings, shared across the release.
CLAIM_CLASSES: tuple[str, ...] = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "RETROSPECTIVE_NUMERIC_MATCH",
    "PROSPECTIVE_PREDICTION",
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_DATA",
)

REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
PROSPECTIVE_PREDICTION = "PROSPECTIVE_PREDICTION"
BENCH_MEASUREMENT = "BENCH_MEASUREMENT"
BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"

#: The claim class of the module as a whole: designed, not run.
CLAIM_CLASS = PROSPECTIVE_PREDICTION

EVIDENCE_CLASS = "ANALYTIC_MODEL"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: p at or below this is "small": the isotropy null is rejected. It is a
#: reporting threshold for the demonstrations, not a discovery threshold
#: for any bench, because there is no bench.
ALPHA_SIGNIFICANCE = 0.05


class HomeLabError(RuntimeError):
    """Raised when a home-lab experiment is asked for more than it has.

    Covers the structural guards (a non-positive decay time, a plan with
    no controls, a degenerate isotropy dataset) and the three
    load-bearing refusals: :func:`refuse_result_without_controls`,
    :func:`refuse_anisotropy_as_anomaly` and :func:`refuse_bench_claim`.
    """


# --- (0) small guards -----------------------------------------------------

def _positive(value: object, what: str) -> float:
    try:
        x = float(value)                             # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise HomeLabError(f"cannot read {value!r} as {what}") from None
    if not math.isfinite(x):
        raise HomeLabError(f"{what} must be finite, got {value!r}")
    if x <= 0.0:
        raise HomeLabError(f"{what} must be positive, got {x!r}")
    return x


# --- (1) the ringdown estimator ------------------------------------------

def fwhm_from_tau(tau: float) -> float:
    """``FWHM = 1/(pi*tau)``: the resonance width for a decay time ``tau``.

    A damped oscillator ``exp(-t/tau)*cos(2*pi*f0*t)`` has a Lorentzian
    line whose full width at half maximum is ``1/(pi*tau)``. This is the
    bridge that makes the two Q formulas one formula.
    """
    return 1.0 / (math.pi * _positive(tau, "the decay time tau"))


def tau_from_fwhm(fwhm: float) -> float:
    """``tau = 1/(pi*FWHM)``, the inverse of :func:`fwhm_from_tau`."""
    return 1.0 / (math.pi * _positive(fwhm, "the FWHM"))


def ringdown_q_from_tau(f0: float, tau: float) -> float:
    """``Q = pi * f0 * tau``, the ringdown form of the quality factor."""
    return math.pi * _positive(f0, "the frequency f0") * _positive(
        tau, "the decay time tau")


def ringdown_q_from_fwhm(f0: float, fwhm: float) -> float:
    """``Q = f0 / FWHM``, the spectral form of the quality factor.

    Equal to :func:`ringdown_q_from_tau` on a consistent resonance,
    because ``FWHM = 1/(pi*tau)`` makes ``f0/FWHM = pi*f0*tau``.
    """
    return _positive(f0, "the frequency f0") / _positive(fwhm, "the FWHM")


def synthetic_ringdown(f0: float = 1000.0, tau: float = 0.05,
                       sample_rate_hz: float = 48000.0,
                       duration_s: float | None = None,
                       amplitude: float = 1.0, phase: float = 0.0,
                       noise: float = 0.0, seed: int = 0) -> dict:
    """A synthetic decaying ringdown ``A*exp(-t/tau)*cos(2*pi*f0*t + phi)``.

    Every number in it is generated here from the arguments; nothing is
    recorded from any device. Optional Gaussian noise is added so the
    estimator can be exercised away from the noiseless ideal, and the
    sample rate is required to satisfy Nyquist for ``f0``.
    """
    f = _positive(f0, "the frequency f0")
    decay = _positive(tau, "the decay time tau")
    fs = _positive(sample_rate_hz, "the sample rate")
    if fs <= 2.0 * f:
        raise HomeLabError(
            f"the sample rate {fs:g} Hz does not satisfy Nyquist for a "
            f"{f:g} Hz signal (needs > {2.0 * f:g} Hz); a ringdown "
            f"sampled below Nyquist aliases, and the recovered tau would "
            f"be an artifact of the sampling")
    span = 6.0 * decay if duration_s is None else _positive(
        duration_s, "the duration")
    n = int(round(span * fs))
    if n < 8:
        raise HomeLabError("a ringdown needs at least eight samples")
    t = np.arange(n, dtype=float) / fs
    envelope = float(amplitude) * np.exp(-t / decay)
    signal = envelope * np.cos(2.0 * math.pi * f * t + float(phase))
    if noise:
        rng = np.random.default_rng(int(seed))
        signal = signal + float(noise) * rng.standard_normal(n)
    return {
        "t_s": t,
        "signal": signal,
        "true_tau_s": decay,
        "true_f0_hz": f,
        "true_q": ringdown_q_from_tau(f, decay),
        "sample_rate_hz": fs,
        "measured_here": MEASURED_HERE,
    }


def _analytic_envelope(signal: np.ndarray) -> np.ndarray:
    """The amplitude envelope via the Hilbert transform, using numpy FFT.

    ``|signal + i*Hilbert(signal)|`` recovers the slowly varying envelope
    of a narrowband oscillation without peak-picking. Implemented with
    the FFT so the module carries no dependency beyond numpy.
    """
    x = np.asarray(signal, dtype=float)
    n = x.size
    spectrum = np.fft.fft(x)
    weights = np.zeros(n)
    if n % 2 == 0:
        weights[0] = weights[n // 2] = 1.0
        weights[1:n // 2] = 2.0
    else:
        weights[0] = 1.0
        weights[1:(n + 1) // 2] = 2.0
    analytic = np.fft.ifft(spectrum * weights)
    return np.abs(analytic)


def estimate_ringdown_tau(t_s: object, signal: object,
                          envelope_floor: float = 0.05) -> float:
    """Recover the decay time ``tau`` from a ringdown by a log-linear fit.

    The analytic envelope is taken, a small margin is trimmed from each
    end (the FFT Hilbert transform rings at the edges of a finite
    record), the result is restricted to the region above
    ``envelope_floor`` of its peak (where the exponential dominates the
    noise), and ``log(envelope)`` is fitted against time. The slope is
    ``-1/tau``, so ``tau = -1/slope``. This is a genuine estimator run on
    data, not an algebraic restatement of the input.
    """
    t = np.asarray(t_s, dtype=float)
    x = np.asarray(signal, dtype=float)
    if t.shape != x.shape or t.ndim != 1:
        raise HomeLabError("t_s and signal must be matching 1-D arrays")
    if t.size < 8:
        raise HomeLabError("estimating tau needs at least eight samples")
    full_envelope = _analytic_envelope(x)
    # Trim the Hilbert edge transient: 2% of the record, at least one
    # sample, from each end, while always leaving a fittable interior.
    margin = min(max(1, int(round(0.02 * t.size))), (t.size - 4) // 2)
    interior = slice(margin, t.size - margin)
    t = t[interior]
    envelope = full_envelope[interior]
    peak = float(np.max(envelope))
    if peak <= 0.0:
        raise HomeLabError("a flat-zero signal has no ringdown to fit")
    floor = _positive(envelope_floor, "the envelope floor")
    if not floor < 1.0:
        raise HomeLabError("the envelope floor must lie in (0, 1)")
    keep = envelope >= floor * peak
    if int(np.count_nonzero(keep)) < 4:
        raise HomeLabError(
            "too little of the envelope is above the floor to fit a decay; "
            "the signal decays too fast for this sampling or is dominated "
            "by noise")
    slope, _intercept = np.polyfit(t[keep], np.log(envelope[keep]), 1)
    if slope >= 0.0:
        raise HomeLabError(
            "the fitted envelope does not decay (non-negative slope); this "
            "is not a ringdown")
    return float(-1.0 / slope)


def estimate_ringdown_q(t_s: object, signal: object, f0: float,
                        envelope_floor: float = 0.05) -> dict:
    """Estimate ``tau`` and hence ``Q = pi*f0*tau`` from a ringdown."""
    tau = estimate_ringdown_tau(t_s, signal, envelope_floor)
    f = _positive(f0, "the frequency f0")
    return {
        "estimated_tau_s": tau,
        "estimated_q": ringdown_q_from_tau(f, tau),
        "fwhm_hz": fwhm_from_tau(tau),
        "q_from_fwhm": ringdown_q_from_fwhm(f, fwhm_from_tau(tau)),
        "f0_hz": f,
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "measured_here": MEASURED_HERE,
        "note": ("an estimator run on synthetic data generated in this "
                 "module; not a measurement of any resonator"),
    }


def ringdown_recovery_demo(f0: float = 1000.0, tau: float = 0.05,
                           sample_rate_hz: float = 48000.0,
                           noise: float = 0.0, seed: int = 0) -> dict:
    """Plant a ``tau``, synthesise a ringdown, and recover it.

    The POWER demonstration for the ringdown estimator, and the check
    that the two Q formulas agree. It says only that the arithmetic and
    the estimator are correct on numbers this module made up.
    """
    data = synthetic_ringdown(f0, tau, sample_rate_hz, noise=noise,
                              seed=seed)
    estimate = estimate_ringdown_q(data["t_s"], data["signal"], f0)
    q_tau = ringdown_q_from_tau(f0, tau)
    q_fwhm = ringdown_q_from_fwhm(f0, fwhm_from_tau(tau))
    return {
        "true_tau_s": tau,
        "estimated_tau_s": estimate["estimated_tau_s"],
        "tau_relative_error": abs(estimate["estimated_tau_s"] - tau) / tau,
        "true_q": q_tau,
        "estimated_q": estimate["estimated_q"],
        "q_from_tau": q_tau,
        "q_from_fwhm": q_fwhm,
        "q_formulas_agree": abs(q_tau - q_fwhm) <= 1e-9 * q_tau,
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "measured_here": MEASURED_HERE,
    }


# --- (2) the isotropy permutation test -----------------------------------

def _isotropy_groups(responses_by_angle: object
                     ) -> tuple[tuple[float, ...], list[np.ndarray]]:
    """Validate and order an ``angle -> responses`` mapping."""
    try:
        items = dict(responses_by_angle)             # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise HomeLabError(
            "responses_by_angle must be a mapping of angle (radians) to a "
            "sequence of responses at that angle") from None
    if len(items) < 2:
        raise HomeLabError(
            "an isotropy test compares responses across orientations; it "
            "needs at least two angles")
    angles = tuple(sorted(float(a) for a in items))
    groups: list[np.ndarray] = []
    for angle in angles:
        arr = np.asarray(items[angle], dtype=float).reshape(-1)
        if arr.size < 1:
            raise HomeLabError(f"angle {angle!r} carries no responses")
        if not np.all(np.isfinite(arr)):
            raise HomeLabError(f"angle {angle!r} carries a non-finite value")
        groups.append(arr)
    if sum(g.size for g in groups) < 4:
        raise HomeLabError(
            "too few responses in total to permute meaningfully")
    return angles, groups


def _anisotropy_statistic(groups: list[np.ndarray]) -> float:
    """Spread of the per-angle mean responses: variance of the means.

    Orientation dependence of any shape shows up as scatter in the
    per-angle means, so this one statistic detects a general anisotropy,
    including the planted ``cos(2*theta)`` case. A rotation-shuffle that
    breaks the angle association leaves the pooled responses untouched
    and this statistic near zero.
    """
    means = np.array([float(g.mean()) for g in groups])
    return float(means.var())


def isotropy_pvalue(responses_by_angle: object, trials: int = 2000,
                    seed: int = 0) -> dict:
    """A rotation-shuffle permutation p-value for orientation dependence.

    The observed statistic is the variance of the per-angle mean
    responses. The null distribution is built by pooling every response,
    reshuffling the pool into the same angle bin sizes ``trials`` times,
    and recomputing the statistic each time. ``p`` is the fraction of
    shuffles (including the observed arrangement) whose statistic is at
    least as large as the observed one.

    Under isotropy the observed arrangement is nothing special and ``p``
    is not small. Under a real orientation dependence the observed
    statistic sits in the tail and ``p`` is small. A small ``p`` here is
    a statement about the *synthetic* data supplied; it is not a
    detection, because nothing was measured.
    """
    angles, groups = _isotropy_groups(responses_by_angle)
    n_trials = int(trials)
    if n_trials < 1:
        raise HomeLabError("a permutation null needs at least one trial")
    observed = _anisotropy_statistic(groups)
    pooled = np.concatenate(groups)
    sizes = [g.size for g in groups]
    rng = np.random.default_rng(int(seed))
    tolerance = 1e-12 * (observed + 1.0)
    at_least = 1                                      # the observed arrangement
    for _ in range(n_trials):
        shuffled = rng.permutation(pooled)
        cut, parts = 0, []
        for size in sizes:
            parts.append(shuffled[cut:cut + size])
            cut += size
        if _anisotropy_statistic(parts) >= observed - tolerance:
            at_least += 1
    p_value = at_least / (n_trials + 1)
    return {
        "p_value": float(p_value),
        "observed_statistic": observed,
        "n_angles": len(angles),
        "n_responses": int(pooled.size),
        "trials": n_trials,
        "seed": int(seed),
        "significant_at_alpha": bool(p_value <= ALPHA_SIGNIFICANCE),
        "alpha": ALPHA_SIGNIFICANCE,
        "null_model": ("rotation-shuffle: responses reassigned to angle "
                       "bins at random, preserving the pooled distribution "
                       "and the bin sizes"),
        "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        "measured_here": MEASURED_HERE,
    }


def synthetic_isotropic_responses(n_angles: int = 12, repeats: int = 60,
                                  baseline: float = 1.0, noise: float = 1.0,
                                  seed: int = 1) -> dict:
    """Isotropic synthetic responses: no orientation dependence at all.

    The mean response is the same at every angle; only noise differs. The
    NULL case for :func:`isotropy_pvalue`.
    """
    n = int(n_angles)
    m = int(repeats)
    if n < 2 or m < 1:
        raise HomeLabError("need at least two angles and one repeat")
    rng = np.random.default_rng(int(seed))
    scale = _positive(noise, "the noise level")
    out = {}
    for i in range(n):
        theta = math.pi * i / n                       # 0 .. pi, orientation
        out[theta] = baseline + scale * rng.standard_normal(m)
    return out


def synthetic_anisotropic_responses(n_angles: int = 12, repeats: int = 60,
                                    baseline: float = 1.0,
                                    amplitude: float = 0.6, noise: float = 1.0,
                                    seed: int = 2) -> dict:
    """Anisotropic synthetic responses with a planted ``cos(2*theta)``.

    The mean response is ``baseline + amplitude*cos(2*theta)``, the
    two-fold orientation dependence of an anisotropic medium. The POWER
    case for :func:`isotropy_pvalue`.
    """
    n = int(n_angles)
    m = int(repeats)
    if n < 2 or m < 1:
        raise HomeLabError("need at least two angles and one repeat")
    rng = np.random.default_rng(int(seed))
    scale = _positive(noise, "the noise level")
    amp = float(amplitude)
    out = {}
    for i in range(n):
        theta = math.pi * i / n
        mean = baseline + amp * math.cos(2.0 * theta)
        out[theta] = mean + scale * rng.standard_normal(m)
    return out


def isotropy_null_demo(trials: int = 2000, seed: int = 1) -> dict:
    """Isotropic data -> p not small. The NULL demonstration."""
    data = synthetic_isotropic_responses(seed=seed)
    return isotropy_pvalue(data, trials=trials, seed=seed + 100)


def isotropy_power_demo(trials: int = 2000, seed: int = 2) -> dict:
    """Planted cos(2*theta) -> p small. The POWER demonstration."""
    data = synthetic_anisotropic_responses(seed=seed)
    return isotropy_pvalue(data, trials=trials, seed=seed + 200)


# --- (3) the four experiments --------------------------------------------

class Experiment(Enum):
    """The four home-lab experiments. Designed, preregistered, not run."""

    MODE_SURVEY = "MODE_SURVEY"
    PHASE_RELATION = "PHASE_RELATION"
    RINGDOWN_Q = "RINGDOWN_Q"
    ISOTROPY = "ISOTROPY"


class CostTier(Enum):
    """A rough cost tier for the apparatus an experiment would need.

    Ordinal, not a budget: it ranks the four against each other so the
    plan says which is cheap to attempt and which is not, without
    pretending to a currency figure that does not exist.
    """

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Control(Enum):
    """The nulls the home-lab experiments lean on.

    Each removes one thing a claim would depend on while leaving the rest
    of the apparatus as close to identical as possible. A result that
    survives its declared controls is interesting; one that does not
    survive a single one of them has been explained.
    """

    NO_DRIVE_BASELINE = "NO_DRIVE_BASELINE"
    DUMMY_INERT_BLANK = "DUMMY_INERT_BLANK"
    TEMPERATURE_LOGGED = "TEMPERATURE_LOGGED"
    OFF_RESONANCE_DRIVE = "OFF_RESONANCE_DRIVE"
    INSTRUMENT_LOOPBACK = "INSTRUMENT_LOOPBACK"
    MECHANICAL_ISOLATION = "MECHANICAL_ISOLATION"
    ROTATION_STAGE_REPEATABILITY = "ROTATION_STAGE_REPEATABILITY"
    RANDOMISED_ANGLE_ORDER = "RANDOMISED_ANGLE_ORDER"


CONTROL_REASONS: dict[Control, str] = {
    Control.NO_DRIVE_BASELINE:
        "record with the drive off: any structure that survives is "
        "pickup, ground loop or environment, not a driven response",
    Control.DUMMY_INERT_BLANK:
        "replace the specimen with an inert blank of the same size and "
        "mounting: a signal that survives is the apparatus, not the "
        "specimen",
    Control.TEMPERATURE_LOGGED:
        "log temperature throughout: quartz frequency and Q drift with "
        "temperature, and an unlogged thermal drift is the most common "
        "false positive available",
    Control.OFF_RESONANCE_DRIVE:
        "drive off resonance at the same amplitude: separates the "
        "resonant response from a broadband electrical artifact",
    Control.INSTRUMENT_LOOPBACK:
        "connect the generator output straight to the digitiser input: "
        "measures the instrument chain's own transfer function and phase, "
        "which must be subtracted before any specimen phase is claimed",
    Control.MECHANICAL_ISOLATION:
        "record on and off a vibration isolator: mechanical shock from "
        "the room couples to a resonator without any drive being involved",
    Control.ROTATION_STAGE_REPEATABILITY:
        "return to the same angle repeatedly: an orientation dependence "
        "smaller than the stage's return error is not an orientation "
        "dependence",
    Control.RANDOMISED_ANGLE_ORDER:
        "visit orientations in randomised order: prevents a monotone "
        "drift in time from masquerading as a dependence on angle",
}


@dataclass(frozen=True)
class ExperimentPlan:
    """One preregistered experiment, with everything a result would need.

    Every field is required and non-trivial: an experiment without a null
    model cannot be falsified, one without controls cannot be trusted,
    and one without a falsification criterion is not an experiment but a
    demonstration. ``status`` is fixed at ``BLOCKED_MISSING_DATA`` because
    no bench exists in this repository.
    """

    experiment: Experiment
    aim: str
    drive: str
    observables: tuple[str, ...]
    sample_rate_hz: float
    anti_aliasing: str
    controls: tuple[Control, ...]
    null_model: str
    falsification_criterion: str
    cost_tier: CostTier
    status: str = BLOCKED_MISSING_DATA

    def __post_init__(self) -> None:
        if not isinstance(self.experiment, Experiment):
            raise HomeLabError("a plan must name an Experiment member")
        if not isinstance(self.cost_tier, CostTier):
            raise HomeLabError("a plan must name a CostTier member")
        for name in ("aim", "drive", "anti_aliasing", "null_model",
                     "falsification_criterion"):
            if not str(getattr(self, name)).strip():
                raise HomeLabError(f"a plan needs a non-empty {name}")
        if not self.observables:
            raise HomeLabError(
                "a plan needs at least one observable; an experiment that "
                "records nothing measures nothing")
        if not self.controls:
            raise HomeLabError(
                "a plan needs at least one declared control; an experiment "
                "with no null to run against cannot produce a result")
        if len(set(self.controls)) != len(self.controls):
            raise HomeLabError("a plan repeats a control")
        for control in self.controls:
            if not isinstance(control, Control):
                raise HomeLabError("every control must be a Control member")
        if self.sample_rate_hz <= 0.0 or not math.isfinite(
                self.sample_rate_hz):
            raise HomeLabError("the sample rate must be finite and positive")
        if self.status != BLOCKED_MISSING_DATA:
            raise HomeLabError(
                f"a home-lab plan may only carry status "
                f"{BLOCKED_MISSING_DATA}: no bench exists in this "
                f"repository, so no experiment here has been run")

    def as_dict(self) -> dict:
        return {
            "experiment": self.experiment.value,
            "aim": self.aim,
            "drive": self.drive,
            "observables": list(self.observables),
            "sample_rate_hz": self.sample_rate_hz,
            "anti_aliasing": self.anti_aliasing,
            "controls": [c.value for c in self.controls],
            "control_reasons": {c.value: CONTROL_REASONS[c]
                                for c in self.controls},
            "null_model": self.null_model,
            "falsification_criterion": self.falsification_criterion,
            "cost_tier": self.cost_tier.value,
            "status": self.status,
            "measured_here": MEASURED_HERE,
        }


EXPERIMENT_PLANS: dict[Experiment, ExperimentPlan] = {
    Experiment.MODE_SURVEY: ExperimentPlan(
        experiment=Experiment.MODE_SURVEY,
        aim=("map the resonances of a specimen across a frequency band "
             "and catalogue each as a candidate mode, without assigning "
             "any of them a mechanism"),
        drive=("a slow stepped or swept sine from a signal generator "
               "through a series resistor, amplitude held constant across "
               "the band"),
        observables=("drive_frequency_hz", "response_amplitude",
                     "response_phase", "temperature_c"),
        sample_rate_hz=192000.0,
        anti_aliasing=("analogue low-pass below the Nyquist frequency "
                       "ahead of the digitiser, plus a settle time at "
                       "each step so the sweep does not smear peaks"),
        controls=(Control.NO_DRIVE_BASELINE, Control.DUMMY_INERT_BLANK,
                  Control.TEMPERATURE_LOGGED, Control.INSTRUMENT_LOOPBACK),
        null_model=("the resonance count and positions expected from the "
                    "instrument chain and mount alone, measured on the "
                    "inert blank"),
        falsification_criterion=("a catalogued peak that also appears, at "
                                 "the same frequency and amplitude, on the "
                                 "inert blank is an instrument peak and is "
                                 "struck from the specimen catalogue"),
        cost_tier=CostTier.LOW,
    ),
    Experiment.PHASE_RELATION: ExperimentPlan(
        experiment=Experiment.PHASE_RELATION,
        aim=("measure the phase of the response relative to the drive "
             "across a resonance, after removing the instrument chain's "
             "own phase"),
        drive=("a single-frequency sine stepped finely through one "
               "resonance, with a phase reference taken from the "
               "generator's sync output"),
        observables=("drive_frequency_hz", "response_phase",
                     "reference_phase", "loopback_phase", "temperature_c"),
        sample_rate_hz=192000.0,
        anti_aliasing=("matched analogue filters on the reference and "
                       "response channels so the two paths share a delay, "
                       "and a loopback measurement of that delay"),
        controls=(Control.INSTRUMENT_LOOPBACK, Control.OFF_RESONANCE_DRIVE,
                  Control.TEMPERATURE_LOGGED, Control.NO_DRIVE_BASELINE),
        null_model=("the phase-versus-frequency curve of the instrument "
                    "chain measured in loopback, which any specimen phase "
                    "must be referenced against"),
        falsification_criterion=("a specimen phase excursion no larger "
                                 "than the loopback phase excursion over "
                                 "the same band is instrument phase, not "
                                 "specimen phase"),
        cost_tier=CostTier.MEDIUM,
    ),
    Experiment.RINGDOWN_Q: ExperimentPlan(
        experiment=Experiment.RINGDOWN_Q,
        aim=("estimate the quality factor of a resonance from its "
             "amplitude decay time after the drive is cut, via "
             "Q = pi*f0*tau, and cross-check against Q = f0/FWHM"),
        drive=("a tone burst at the resonance, gated off abruptly, "
               "followed by recording of the free decay"),
        observables=("ringdown_waveform", "f0_hz", "decay_time_tau_s",
                     "fwhm_hz", "temperature_c"),
        sample_rate_hz=48000.0,
        anti_aliasing=("an analogue anti-alias filter below Nyquist and a "
                       "sample rate at least ten times f0 so the envelope "
                       "is well resolved through the decay"),
        controls=(Control.OFF_RESONANCE_DRIVE, Control.MECHANICAL_ISOLATION,
                  Control.TEMPERATURE_LOGGED, Control.DUMMY_INERT_BLANK),
        null_model=("the apparent decay of the instrument and mount alone, "
                    "measured on the inert blank and off resonance, which "
                    "sets the longest tau attributable to the fixture"),
        falsification_criterion=("a recovered tau that does not exceed the "
                                 "fixture's own decay time, or that changes "
                                 "with drive amplitude, is not the "
                                 "specimen's Q"),
        cost_tier=CostTier.MEDIUM,
    ),
    Experiment.ISOTROPY: ExperimentPlan(
        experiment=Experiment.ISOTROPY,
        aim=("test whether a chosen response depends on the specimen's "
             "orientation, comparing across angles with a rotation-shuffle "
             "permutation null"),
        drive=("a fixed single-frequency drive held constant while the "
               "specimen is rotated on a stage to a set of orientations, "
               "each visited several times"),
        observables=("orientation_angle_rad", "response_amplitude",
                     "response_phase", "temperature_c"),
        sample_rate_hz=192000.0,
        anti_aliasing=("the drive fixed well inside the pass-band and an "
                       "analogue anti-alias filter below Nyquist, so "
                       "orientation is the only variable between records"),
        controls=(Control.ROTATION_STAGE_REPEATABILITY,
                  Control.RANDOMISED_ANGLE_ORDER, Control.TEMPERATURE_LOGGED,
                  Control.DUMMY_INERT_BLANK),
        null_model=("the rotation-shuffle permutation null of "
                    "isotropy_pvalue: responses reassigned to angle bins "
                    "at random, preserving the pooled distribution"),
        falsification_criterion=("an orientation dependence with a "
                                 "permutation p above alpha, or one no "
                                 "larger than the rotation stage's return "
                                 "error, is consistent with isotropy of "
                                 "the measurement (note: an anisotropic "
                                 "crystal is EXPECTED to be anisotropic)"),
        cost_tier=CostTier.HIGH,
    ),
}


def experiment_plan(experiment: Experiment) -> ExperimentPlan:
    """The plan for one experiment."""
    if not isinstance(experiment, Experiment):
        raise HomeLabError("an experiment must be an Experiment member")
    return EXPERIMENT_PLANS[experiment]


# --- (4) the load-bearing refusals ---------------------------------------

def _as_controls(ran: object) -> tuple[Control, ...]:
    """Coerce a declaration of run controls to :class:`Control` members."""
    if ran is None:
        return ()
    if isinstance(ran, (Control, str)):
        ran = (ran,)
    try:
        items = list(ran)                             # type: ignore[arg-type]
    except TypeError:
        raise HomeLabError(
            f"cannot read {ran!r} as a collection of controls") from None
    out: list[Control] = []
    for item in items:
        if isinstance(item, Control):
            out.append(item)
            continue
        try:
            out.append(Control(str(item)))
        except ValueError:
            raise HomeLabError(
                f"{item!r} is not a declared control; the controls are "
                f"{', '.join(c.value for c in Control)}") from None
    return tuple(out)


def missing_controls(plan: ExperimentPlan, ran: object) -> tuple[Control, ...]:
    """Which of a plan's declared controls are absent from ``ran``."""
    if not isinstance(plan, ExperimentPlan):
        raise HomeLabError("missing_controls needs an ExperimentPlan")
    have = set(_as_controls(ran))
    return tuple(c for c in plan.controls if c not in have)


def refuse_result_without_controls(plan: ExperimentPlan,
                                   ran: object = ()) -> tuple[Control, ...]:
    """Refuse a result while any of a plan's declared controls is absent.

    Returns the plan's controls when every one is present in ``ran`` — and
    that is all it returns. Having the controls present is a precondition
    for a result, not a result: no experiment here has been run, and
    :func:`refuse_bench_claim` still refuses every number.
    """
    missing = missing_controls(plan, ran)
    if missing:
        why = "; ".join(f"{c.value}: {CONTROL_REASONS[c]}" for c in missing)
        raise HomeLabError(
            f"refused: the {plan.experiment.value} experiment declares "
            f"{len(plan.controls)} controls and {len(missing)} of them are "
            f"absent ({', '.join(c.value for c in missing)}). {why}. A "
            f"result reported before its declared controls have been run "
            f"is a result whose most likely explanations have not been "
            f"ruled out. {VERDICT}")
    return plan.controls


def refuse_anisotropy_as_anomaly(
        crystal: str = "alpha quartz",
        claim: str = "the observed orientation dependence is an anomaly"
) -> None:
    """Anisotropy in an anisotropic crystal is the null. This ALWAYS raises.

    Alpha quartz is a trigonal, class-32 crystal: its elastic stiffness
    tensor, its refractive indices and its piezoelectric coefficients all
    depend on direction by the symmetry of the lattice. A specimen that
    shows orientation dependence is therefore behaving exactly as an
    anisotropic crystal must, and finding that dependence confirms the
    null hypothesis rather than refuting it. The result that would be
    surprising is *isotropy* — and even that would be a measurement this
    module has not made.
    """
    raise HomeLabError(
        f"refused: {claim!r} for {crystal!r}. {crystal} is an ANISOTROPIC "
        f"crystal — trigonal, class 32 — whose elastic, optical and "
        f"piezoelectric properties depend on direction by the symmetry of "
        f"the lattice, so an orientation-dependent response is precisely "
        f"what an anisotropic crystal is REQUIRED to show. Observing it "
        f"confirms the null hypothesis (the specimen is anisotropic, as "
        f"expected); it does not establish an anomaly. The result that "
        f"would need explaining is ISOTROPY, and no orientation-resolved "
        f"measurement has been made here in any case. {VERDICT}")


def refuse_bench_claim(claim: str = "a home-lab experiment was run",
                       experiment: Experiment | str | None = None) -> None:
    """Refuse any measured reading from these experiments. Always raises.

    Nothing in this module has been driven, gated, rotated, digitised or
    recorded. Every plan carries status ``BLOCKED_MISSING_DATA``, and the
    ringdown and isotropy numbers here are computations on synthetic data
    the module generated, not readings from any instrument.
    """
    named = ""
    if experiment is not None:
        name = getattr(experiment, "value", experiment)
        named = f" for {name}"
    raise HomeLabError(
        f"refused: {claim!r}{named} is a {BENCH_MEASUREMENT} claim and no "
        f"bench exists here. There is no signal generator, amplifier, "
        f"resonator, lock-in, digitiser, rotation stage or thermometer in "
        f"this repository; all four experiment plans carry status "
        f"{BLOCKED_MISSING_DATA}. The ringdown Q recovered here and the "
        f"isotropy p-values here are computations on SYNTHETIC data "
        f"generated inside this module, not measurements of any specimen. "
        f"{VERDICT}")


# --- (5) report ------------------------------------------------------------

def homelab_report() -> dict:
    """The standing statement of what this module is and is not."""
    recovery = ringdown_recovery_demo()
    null_demo = isotropy_null_demo()
    power_demo = isotropy_power_demo()
    return {
        "what_this_is": (
            "four home-lab experiments — a mode survey, a phase relation, "
            "a ringdown Q and an isotropy test — designed and "
            "preregistered with aims, drives, observables, sample rates, "
            "declared controls, null models, falsification criteria and "
            "cost tiers, together with two estimators exercised on "
            "synthetic data"),
        "experiments": {e.value: experiment_plan(e).as_dict()
                        for e in Experiment},
        "all_blocked": all(experiment_plan(e).status == BLOCKED_MISSING_DATA
                           for e in Experiment),
        "n_experiments": len(Experiment),
        "controls": {c.value: CONTROL_REASONS[c] for c in Control},
        "ringdown": {
            "q_from_tau": "Q = pi * f0 * tau",
            "q_from_fwhm": "Q = f0 / FWHM, with FWHM = 1/(pi*tau)",
            "recovery_demo": recovery,
            "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        },
        "isotropy": {
            "null_p_value": null_demo["p_value"],
            "null_significant": null_demo["significant_at_alpha"],
            "power_p_value": power_demo["p_value"],
            "power_significant": power_demo["significant_at_alpha"],
            "alpha": ALPHA_SIGNIFICANCE,
            "claim_class": REPOSITORY_COMPUTATIONAL_RESULT,
        },
        "refusals": [
            "refuse_result_without_controls",
            "refuse_anisotropy_as_anomaly",
            "refuse_bench_claim",
        ],
        "firewalls": [
            "every experiment requires all of its declared controls "
            "before any result, and none has been run",
            "alpha quartz is anisotropic, so orientation dependence in it "
            "is the null hypothesis, not an anomaly",
            "the ringdown Q and the isotropy p-values are computations on "
            "synthetic data, not measurements",
            "a sample rate below Nyquist aliases, and a tau recovered from "
            "aliased data is an artifact of the sampling",
        ],
        "hardware_status": (
            "BLOCKED_MISSING_DATA - no generator, amplifier, resonator, "
            "lock-in, digitiser, rotation stage or thermometer exists "
            "here"),
        "claim_class": CLAIM_CLASS,
        "claim_classes": list(CLAIM_CLASSES),
        "evidence_class": EVIDENCE_CLASS,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_would_change_this": (
            "a built bench with a calibrated drive, an instrumented "
            "specimen and its inert blank, the loopback and off-resonance "
            "controls actually recorded, temperature logged throughout, "
            "and each experiment run against its declared null with its "
            "falsification criterion applied before any Q or p-value is "
            "reported as a measurement"),
        "what_this_does_not_say": (
            "It does not say any experiment was run: there is no signal "
            "generator, amplifier, resonator, lock-in, digitiser, "
            "rotation stage or thermometer in this repository, and every "
            "plan carries status BLOCKED_MISSING_DATA. The ringdown Q "
            "recovered here and the isotropy p-values here are "
            "computations on SYNTHETIC data generated inside this module, "
            "not readings from any instrument, so no f0, tau, Q or "
            "orientation dependence of any physical specimen is claimed. "
            "It does not say that anisotropy would be an anomaly: alpha "
            "quartz is an anisotropic crystal, so orientation dependence "
            "in it is the expected null, and the surprising result would "
            "be isotropy. It does not say the declared controls were run: "
            "they are declared, and declaring a control is not running "
            "it."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "CLAIM_CLASS", "CLAIM_CLASSES",
    "REPOSITORY_COMPUTATIONAL_RESULT", "PROSPECTIVE_PREDICTION",
    "BENCH_MEASUREMENT", "BLOCKED_MISSING_DATA", "EVIDENCE_CLASS",
    "MEASURED_HERE", "PHYSICAL_VALIDATION", "ALPHA_SIGNIFICANCE",
    "HomeLabError",
    "fwhm_from_tau", "tau_from_fwhm", "ringdown_q_from_tau",
    "ringdown_q_from_fwhm", "synthetic_ringdown", "estimate_ringdown_tau",
    "estimate_ringdown_q", "ringdown_recovery_demo",
    "isotropy_pvalue", "synthetic_isotropic_responses",
    "synthetic_anisotropic_responses", "isotropy_null_demo",
    "isotropy_power_demo",
    "Experiment", "CostTier", "Control", "CONTROL_REASONS",
    "ExperimentPlan", "EXPERIMENT_PLANS", "experiment_plan",
    "missing_controls", "refuse_result_without_controls",
    "refuse_anisotropy_as_anomaly", "refuse_bench_claim",
    "homelab_report",
]
