"""P11 — the ordinary-explanation firewall, as code.

Before an apparent anomaly may be called an
``UNEXPLAINED_INSTRUMENT_RESIDUAL`` it has to survive a battery of
*ordinary-explanation attacks*. Each attack is a detector for one mundane
mechanism that routinely masquerades as a discovery:

* **raw-data defect** -- NaN / inf samples or a zero-filled dropout run;
* **clock error / jitter** -- the sample instants wander off the ideal grid;
* **calibration drift** -- a slow multiplicative gain trend across the record;
* **clipping** -- samples pile up flat on a rail;
* **aliasing** -- an out-of-band tone folds below Nyquist and impersonates a
  low-frequency feature (read back through :mod:`r13.daq`);
* **spectral leakage** -- an off-bin tone smears into sidelobes under a
  rectangular window and collapses under a Hann window;
* **environmental coupling** -- the signal tracks an environment monitor;
* **fixture effect** -- the feature is already present in a blank-fixture
  record with no specimen mounted;
* **cross-talk** -- a scaled copy of a neighbouring channel's drive leaks in;
* **specimen mismatch** -- the dominant feature sits outside the band the
  declared specimen should occupy;
* **model inadequacy** -- the "anomaly" is captured by an obvious extension
  of the declared model (a missing harmonic or a polynomial baseline).

Each attack takes a candidate signal plus a typed :class:`AttackContext`
and returns a typed :class:`AttackResult`. An attack that lacks the context
it needs is *not applicable* and does not fire; it is still recorded, so no
failed attempt is discarded. :func:`run_all_attacks` returns the ordinary
explanations that fired -- **any** one of them means the residual is not
unexplained.

The firewall is not vacuous. A signal that is a clean, on-bin, stationary,
uncoupled tone -- a deliberately genuine-looking residual above the
uncertainty budget -- passes **every** attack and only then reaches the
``UNEXPLAINED_INSTRUMENT_RESIDUAL`` ceiling. A residual below the combined
uncertainty budget is not anomalous at all. And no residual is ever
promoted past that ceiling: an unexplained instrument residual is not new
physics, and :func:`refuse_residual_before_attacks` refuses to apply the
label before the battery has run.

Nothing here is measured. Every fixture is a seeded synthetic waveform; the
strongest class this module reaches is ``SOFTWARE_IMPLEMENTED`` and no
apparatus is operated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13 import daq as _daq
from r15 import claims

# --- verdict and standing claim vocabulary -------------------------------

#: The standing verdict for this module.
VERDICT = "ORDINARY_EXPLANATION_FIREWALL_IMPLEMENTED"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The class of the firewall machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED
#: The ceiling an unreplicated residual may reach -- never new physics.
RESIDUAL_CEILING = claims.ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL

# --- detector thresholds (module constants, deterministic) ---------------

#: Fraction of samples that must sit exactly on the peak rail to read as
#: clipping. A clean tone touches its peak once; a clipped one plateaus.
CLIP_FRACTION_THRESHOLD = 0.02
#: Fraction of samples in a contiguous constant run that reads as a dropout.
DROPOUT_RUN_FRACTION = 0.02
#: Timing jitter, as a fraction of one sample period, above which the clock
#: is deemed in error (after removing a constant offset and linear rate).
CLOCK_JITTER_FRACTION = 0.05
#: Fractional gain change end-to-start above which calibration has drifted.
CALIBRATION_DRIFT_TOLERANCE = 0.25
#: Near-main-lobe sidelobe level (relative to the peak) under a rectangular
#: window above which leakage is suspected...
LEAKAGE_SIDELOBE_THRESHOLD = 0.05
#: ...confirmed when a Hann window suppresses that sidelobe by this factor.
LEAKAGE_HANN_DROP_FACTOR = 3.0
#: |Pearson r| against a reference channel above which coupling is deemed
#: real (environment, cross-talk, fixture).
COUPLING_CORRELATION_THRESHOLD = 0.5
#: Fraction of variance an augmented model must explain to read as model
#: inadequacy rather than a genuine residual.
MODEL_INADEQUACY_R2 = 0.5
#: Default coverage factor (k) for the uncertainty budget.
DEFAULT_COVERAGE_FACTOR = 2.0


class OrdinaryExplanationError(RuntimeError):
    """Raised on a firewall refusal or an ill-formed attack input.

    Covers the structural guards (an empty signal, a malformed context) and
    the load-bearing refusal :func:`refuse_residual_before_attacks`.
    """


# --- the attack vocabulary ------------------------------------------------

class AttackName(Enum):
    """The eleven ordinary-explanation attacks."""

    RAW_DATA_DEFECT = "raw_data_defect"
    CLOCK_ERROR = "clock_error"
    CALIBRATION_DRIFT = "calibration_drift"
    CLIPPING = "clipping"
    ALIASING = "aliasing"
    SPECTRAL_LEAKAGE = "spectral_leakage"
    ENVIRONMENTAL_COUPLING = "environmental_coupling"
    FIXTURE_EFFECT = "fixture_effect"
    CROSS_TALK = "cross_talk"
    SPECIMEN_MISMATCH = "specimen_mismatch"
    MODEL_INADEQUACY = "model_inadequacy"


#: The ordinary claim class each attack assigns when it fires. Each is an
#: ordinary-explanation class in the R15 taxonomy -- never a measurement,
#: never new physics.
ATTACK_CLAIM_CLASS: dict[AttackName, claims.ClaimClass] = {
    AttackName.RAW_DATA_DEFECT: claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
    AttackName.CLOCK_ERROR: claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
    AttackName.CALIBRATION_DRIFT: claims.ClaimClass.CALIBRATION_ERROR,
    AttackName.CLIPPING: claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
    AttackName.ALIASING: claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
    AttackName.SPECTRAL_LEAKAGE: claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
    AttackName.ENVIRONMENTAL_COUPLING: claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
    AttackName.FIXTURE_EFFECT: claims.ClaimClass.FIXTURE_EFFECT,
    AttackName.CROSS_TALK: claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
    AttackName.SPECIMEN_MISMATCH: claims.ClaimClass.KNOWN_ORDINARY_EFFECT,
    AttackName.MODEL_INADEQUACY: claims.ClaimClass.MODEL_ERROR,
}


# --- residual classifications --------------------------------------------

class ResidualClass(Enum):
    """The outcome of running a candidate residual through the firewall."""

    #: Within the combined uncertainty budget -- not anomalous at all.
    NOISE_WITHIN_UNCERTAINTY = "NOISE_WITHIN_UNCERTAINTY"
    #: At least one ordinary-explanation attack fired.
    ORDINARY_EXPLANATION_FOUND = "ORDINARY_EXPLANATION_FOUND"
    #: Above budget and survived every attack -- the ceiling, never physics.
    UNEXPLAINED_INSTRUMENT_RESIDUAL = "UNEXPLAINED_INSTRUMENT_RESIDUAL"


# --- the attack context ---------------------------------------------------

@dataclass(frozen=True)
class AttackContext:
    """Everything the attacks may consult about a candidate signal.

    Every reference is optional. An attack whose reference is absent is
    *not applicable*: it records that it could not run rather than firing.
    This keeps the battery honest -- a clean signal offered the full context
    must survive every attack for the firewall to be non-vacuous.
    """

    sample_rate_hz: float = 1.0
    #: The combined 1-sigma uncertainty for the quantity, and its coverage.
    combined_uncertainty: float = 0.0
    coverage_factor: float = DEFAULT_COVERAGE_FACTOR
    #: Actual sample instants (seconds); compared to the ideal grid.
    timebase: np.ndarray | None = None
    #: Presence enables the calibration-drift attack; may hold ``drift_tol``.
    calibration_reference: dict | None = None
    #: The true source frequency suspected of aliasing below Nyquist.
    suspect_tone_hz: float | None = None
    #: An environment monitor channel (temperature, line hum, vibration).
    environment: np.ndarray | None = None
    #: A neighbouring channel's drive, suspected of cross-talk.
    aggressor: np.ndarray | None = None
    #: A blank-fixture record taken with no specimen mounted.
    fixture_reference: np.ndarray | None = None
    #: The band the declared specimen's feature should occupy.
    expected_feature_hz: float | None = None
    specimen_tol_hz: float = 0.0
    #: The declared model's prediction and its fundamental frequency.
    model_prediction: np.ndarray | None = None
    model_fundamental_hz: float | None = None
    correlation_threshold: float = COUPLING_CORRELATION_THRESHOLD
    #: Identifiers carried onto the residual record.
    residual_id: str = "residual"
    observation_ids: tuple = ()

    def coverage(self) -> float:
        return abs(self.combined_uncertainty) * float(self.coverage_factor)


# --- the attack result ----------------------------------------------------

@dataclass(frozen=True)
class AttackResult:
    """The outcome of a single attack against a candidate signal.

    ``applicable`` records whether the attack had the context it needed;
    ``explained`` is True only when an ordinary cause was actually found.
    An inapplicable or non-firing attack is still returned and recorded, so
    failed explanations are preserved.
    """

    name: AttackName
    applicable: bool
    explained: bool
    statistic: float
    threshold: float
    detail: str
    claim_class: claims.ClaimClass = claims.ClaimClass.KNOWN_ORDINARY_EFFECT

    def as_dict(self) -> dict:
        return {
            "attack": self.name.value,
            "applicable": bool(self.applicable),
            "explained": bool(self.explained),
            "statistic": float(self.statistic),
            "threshold": float(self.threshold),
            "detail": self.detail,
            "claim_class": self.claim_class.value,
        }


# --- small numeric helpers ------------------------------------------------

def _as_signal(signal) -> np.ndarray:
    x = np.asarray(signal, dtype=float)
    if x.ndim != 1 or x.size < 2:
        raise OrdinaryExplanationError(
            "a candidate signal must be a 1-D array of at least two samples")
    return x


def _pearson(a: np.ndarray, b: np.ndarray) -> float:
    """|Pearson r| between two equal-length real records, 0 on degeneracy."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    n = min(a.size, b.size)
    if n < 2:
        return 0.0
    a = a[:n] - a[:n].mean()
    b = b[:n] - b[:n].mean()
    da = float(np.sqrt(np.sum(a * a)))
    db = float(np.sqrt(np.sum(b * b)))
    if da == 0.0 or db == 0.0:
        return 0.0
    return float(abs(np.sum(a * b) / (da * db)))


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x)))) if x.size else 0.0


def _finite(x: np.ndarray) -> np.ndarray:
    return x[np.isfinite(x)]


# --- the eleven attacks ---------------------------------------------------
# Each attack is a pure function ``(signal, context) -> AttackResult``.

def attack_raw_data_defect(signal, context: AttackContext) -> AttackResult:
    """Catch NaN/inf samples or a zero-filled dropout run."""
    x = np.asarray(signal, dtype=float)
    n_nonfinite = int(np.sum(~np.isfinite(x)))
    # longest contiguous constant run (a zero-filled / stuck dropout)
    run = best = 1
    finite = np.isfinite(x)
    for i in range(1, x.size):
        if finite[i] and finite[i - 1] and x[i] == x[i - 1]:
            run += 1
            best = max(best, run)
        else:
            run = 1
    run_frac = best / x.size
    explained = (n_nonfinite > 0) or (run_frac >= DROPOUT_RUN_FRACTION)
    stat = max(n_nonfinite / x.size, run_frac)
    return AttackResult(
        AttackName.RAW_DATA_DEFECT, True, explained, stat,
        DROPOUT_RUN_FRACTION,
        (f"{n_nonfinite} non-finite sample(s); longest constant run "
         f"{best}/{x.size} = {run_frac:.3f}"),
        ATTACK_CLAIM_CLASS[AttackName.RAW_DATA_DEFECT])


def attack_clock_error(signal, context: AttackContext) -> AttackResult:
    """Catch sample instants that wander off the ideal uniform grid."""
    tb = context.timebase
    if tb is None:
        return AttackResult(
            AttackName.CLOCK_ERROR, False, False, 0.0, CLOCK_JITTER_FRACTION,
            "no timebase supplied; clock jitter not checkable",
            ATTACK_CLAIM_CLASS[AttackName.CLOCK_ERROR])
    tb = np.asarray(tb, dtype=float)
    n = tb.size
    idx = np.arange(n, dtype=float)
    # remove a constant offset and a linear rate; what remains is jitter
    a, b = np.polyfit(idx, tb, 1)
    resid = tb - (a * idx + b)
    period = 1.0 / float(context.sample_rate_hz)
    jitter_frac = float(np.max(np.abs(resid))) / period if period else 0.0
    explained = jitter_frac > CLOCK_JITTER_FRACTION
    return AttackResult(
        AttackName.CLOCK_ERROR, True, explained, jitter_frac,
        CLOCK_JITTER_FRACTION,
        f"peak timing jitter {jitter_frac:.3f} of a sample period",
        ATTACK_CLAIM_CLASS[AttackName.CLOCK_ERROR])


def attack_calibration_drift(signal, context: AttackContext) -> AttackResult:
    """Catch a slow multiplicative gain trend across the record."""
    if context.calibration_reference is None:
        return AttackResult(
            AttackName.CALIBRATION_DRIFT, False, False, 0.0,
            CALIBRATION_DRIFT_TOLERANCE,
            "no calibration reference; gain drift not checkable",
            ATTACK_CLAIM_CLASS[AttackName.CALIBRATION_DRIFT])
    tol = float(context.calibration_reference.get(
        "drift_tol", CALIBRATION_DRIFT_TOLERANCE))
    x = _finite(np.asarray(signal, dtype=float))
    third = max(1, x.size // 3)
    r0 = _rms(x[:third])
    r1 = _rms(x[-third:])
    if r0 == 0.0:
        drift = 0.0
    else:
        drift = abs(r1 - r0) / r0
    explained = drift > tol
    return AttackResult(
        AttackName.CALIBRATION_DRIFT, True, explained, drift, tol,
        f"end/start RMS gain change {drift:.3f}",
        ATTACK_CLAIM_CLASS[AttackName.CALIBRATION_DRIFT])


def attack_clipping(signal, context: AttackContext) -> AttackResult:
    """Catch samples piling up flat on a rail."""
    x = _finite(np.asarray(signal, dtype=float))
    if x.size == 0 or np.ptp(x) == 0.0:
        return AttackResult(
            AttackName.CLIPPING, True, False, 0.0, CLIP_FRACTION_THRESHOLD,
            "flat or empty signal; no rail to detect",
            ATTACK_CLAIM_CLASS[AttackName.CLIPPING])
    hi = float(x.max())
    lo = float(x.min())
    frac_hi = float(np.mean(np.isclose(x, hi, rtol=1e-9, atol=1e-12)))
    frac_lo = float(np.mean(np.isclose(x, lo, rtol=1e-9, atol=1e-12)))
    frac = max(frac_hi, frac_lo)
    explained = frac >= CLIP_FRACTION_THRESHOLD
    return AttackResult(
        AttackName.CLIPPING, True, explained, frac, CLIP_FRACTION_THRESHOLD,
        f"fraction of samples on a rail {frac:.3f}",
        ATTACK_CLAIM_CLASS[AttackName.CLIPPING])


def attack_aliasing(signal, context: AttackContext) -> AttackResult:
    """Catch an out-of-band tone folded below Nyquist (via r13.daq)."""
    fs = float(context.sample_rate_hz)
    suspect = context.suspect_tone_hz
    nyquist = fs / 2.0
    if suspect is None or float(suspect) <= nyquist:
        return AttackResult(
            AttackName.ALIASING, False, False, 0.0, 0.0,
            "no above-Nyquist suspect tone; aliasing not checkable",
            ATTACK_CLAIM_CLASS[AttackName.ALIASING])
    x = _finite(np.asarray(signal, dtype=float))
    predicted = _daq.alias_frequency(float(suspect), fs)
    observed = _daq.dominant_frequency(x, fs)
    bin_hz = fs / x.size
    match = abs(observed - predicted)
    explained = match <= 2.0 * bin_hz
    return AttackResult(
        AttackName.ALIASING, True, explained, match, 2.0 * bin_hz,
        (f"suspect {float(suspect):.1f} Hz folds to {predicted:.1f} Hz; "
         f"dominant tone at {observed:.1f} Hz"),
        ATTACK_CLAIM_CLASS[AttackName.ALIASING])


def attack_spectral_leakage(signal, context: AttackContext) -> AttackResult:
    """Catch an off-bin tone smeared into sidelobes under a boxcar window."""
    x = _finite(np.asarray(signal, dtype=float))
    n = x.size
    xc = x - x.mean()
    rect = np.abs(np.fft.rfft(xc))
    hann = np.abs(np.fft.rfft(xc * np.hanning(n)))
    m = int(np.argmax(hann))
    if rect[m] == 0.0 or hann[m] == 0.0:
        return AttackResult(
            AttackName.SPECTRAL_LEAKAGE, True, False, 0.0,
            LEAKAGE_SIDELOBE_THRESHOLD, "no spectral peak to test",
            ATTACK_CLAIM_CLASS[AttackName.SPECTRAL_LEAKAGE])
    k = 8
    lo, hi = max(0, m - k), min(rect.size, m + k + 1)
    # near-lobe band excludes the boxcar main lobe (+/-1) and the wider
    # Hann main lobe (+/-2) so a genuine adjacent tone is not called leakage
    rect_band = [i for i in range(lo, hi) if abs(i - m) > 1]
    hann_band = [i for i in range(lo, hi) if abs(i - m) > 2]
    rect_side = max((rect[i] for i in rect_band), default=0.0) / rect[m]
    hann_side = max((hann[i] for i in hann_band), default=0.0) / hann[m]
    explained = (rect_side > LEAKAGE_SIDELOBE_THRESHOLD and
                 rect_side >= LEAKAGE_HANN_DROP_FACTOR * hann_side)
    return AttackResult(
        AttackName.SPECTRAL_LEAKAGE, True, explained, rect_side,
        LEAKAGE_SIDELOBE_THRESHOLD,
        (f"boxcar sidelobe {rect_side:.3f} of peak, Hann sidelobe "
         f"{hann_side:.3f}; collapses under a window"),
        ATTACK_CLAIM_CLASS[AttackName.SPECTRAL_LEAKAGE])


def attack_environmental_coupling(signal,
                                  context: AttackContext) -> AttackResult:
    """Catch a signal that tracks an environment monitor channel."""
    if context.environment is None:
        return AttackResult(
            AttackName.ENVIRONMENTAL_COUPLING, False, False, 0.0,
            context.correlation_threshold,
            "no environment channel; coupling not checkable",
            ATTACK_CLAIM_CLASS[AttackName.ENVIRONMENTAL_COUPLING])
    r = _pearson(np.asarray(signal, dtype=float),
                 np.asarray(context.environment, dtype=float))
    explained = r > context.correlation_threshold
    return AttackResult(
        AttackName.ENVIRONMENTAL_COUPLING, True, explained, r,
        context.correlation_threshold,
        f"|r| with environment monitor {r:.3f}",
        ATTACK_CLAIM_CLASS[AttackName.ENVIRONMENTAL_COUPLING])


def attack_fixture_effect(signal, context: AttackContext) -> AttackResult:
    """Catch a feature already present in a blank-fixture record."""
    if context.fixture_reference is None:
        return AttackResult(
            AttackName.FIXTURE_EFFECT, False, False, 0.0,
            context.correlation_threshold,
            "no blank-fixture record; fixture effect not checkable",
            ATTACK_CLAIM_CLASS[AttackName.FIXTURE_EFFECT])
    r = _pearson(np.asarray(signal, dtype=float),
                 np.asarray(context.fixture_reference, dtype=float))
    explained = r > context.correlation_threshold
    return AttackResult(
        AttackName.FIXTURE_EFFECT, True, explained, r,
        context.correlation_threshold,
        f"|r| with blank fixture {r:.3f}",
        ATTACK_CLAIM_CLASS[AttackName.FIXTURE_EFFECT])


def attack_cross_talk(signal, context: AttackContext) -> AttackResult:
    """Catch a scaled copy of a neighbouring channel's drive leaking in."""
    if context.aggressor is None:
        return AttackResult(
            AttackName.CROSS_TALK, False, False, 0.0,
            context.correlation_threshold,
            "no aggressor channel; cross-talk not checkable",
            ATTACK_CLAIM_CLASS[AttackName.CROSS_TALK])
    r = _pearson(np.asarray(signal, dtype=float),
                 np.asarray(context.aggressor, dtype=float))
    explained = r > context.correlation_threshold
    return AttackResult(
        AttackName.CROSS_TALK, True, explained, r,
        context.correlation_threshold,
        f"|r| with aggressor channel {r:.3f}",
        ATTACK_CLAIM_CLASS[AttackName.CROSS_TALK])


def attack_specimen_mismatch(signal, context: AttackContext) -> AttackResult:
    """Catch a dominant feature outside the declared specimen's band."""
    if context.expected_feature_hz is None:
        return AttackResult(
            AttackName.SPECIMEN_MISMATCH, False, False, 0.0, 0.0,
            "no expected specimen band; mismatch not checkable",
            ATTACK_CLAIM_CLASS[AttackName.SPECIMEN_MISMATCH])
    fs = float(context.sample_rate_hz)
    x = _finite(np.asarray(signal, dtype=float))
    observed = _daq.dominant_frequency(x, fs)
    expected = float(context.expected_feature_hz)
    bin_hz = fs / x.size
    tol = max(float(context.specimen_tol_hz), 2.0 * bin_hz)
    offset = abs(observed - expected)
    explained = offset > tol
    return AttackResult(
        AttackName.SPECIMEN_MISMATCH, True, explained, offset, tol,
        (f"dominant tone {observed:.1f} Hz vs declared specimen band "
         f"{expected:.1f}+/-{tol:.1f} Hz"),
        ATTACK_CLAIM_CLASS[AttackName.SPECIMEN_MISMATCH])


def attack_model_inadequacy(signal, context: AttackContext) -> AttackResult:
    """Catch an 'anomaly' captured by an obvious extension of the model."""
    if context.model_prediction is None or \
            context.model_fundamental_hz is None:
        return AttackResult(
            AttackName.MODEL_INADEQUACY, False, False, 0.0,
            MODEL_INADEQUACY_R2,
            "no model prediction / fundamental; inadequacy not checkable",
            ATTACK_CLAIM_CLASS[AttackName.MODEL_INADEQUACY])
    fs = float(context.sample_rate_hz)
    x = np.asarray(signal, dtype=float)
    model = np.asarray(context.model_prediction, dtype=float)
    n = min(x.size, model.size)
    resid = x[:n] - model[:n]
    good = np.isfinite(resid)
    resid = resid[good]
    if resid.size < 4:
        return AttackResult(
            AttackName.MODEL_INADEQUACY, True, False, 0.0, MODEL_INADEQUACY_R2,
            "residual too short to fit an augmented model",
            ATTACK_CLAIM_CLASS[AttackName.MODEL_INADEQUACY])
    t = np.arange(n, dtype=float)[good] / fs
    f0 = float(context.model_fundamental_hz)
    # an obvious augmentation: a polynomial baseline plus the next two
    # harmonics of the declared fundamental
    cols = [np.ones_like(t), t, t * t]
    for h in (2, 3):
        cols.append(np.sin(2 * np.pi * h * f0 * t))
        cols.append(np.cos(2 * np.pi * h * f0 * t))
    design = np.vstack(cols).T
    coef, *_ = np.linalg.lstsq(design, resid, rcond=None)
    pred = design @ coef
    ss_tot = float(np.sum((resid - resid.mean()) ** 2))
    ss_res = float(np.sum((resid - pred) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 0.0
    explained = r2 > MODEL_INADEQUACY_R2
    return AttackResult(
        AttackName.MODEL_INADEQUACY, True, explained, r2, MODEL_INADEQUACY_R2,
        f"augmented model (baseline + harmonics) captures R^2={r2:.3f}",
        ATTACK_CLAIM_CLASS[AttackName.MODEL_INADEQUACY])


#: The attack battery, in a fixed order. No attack has exclusive authority:
#: the firewall's verdict is a union over all of them.
ATTACKS: dict[AttackName, object] = {
    AttackName.RAW_DATA_DEFECT: attack_raw_data_defect,
    AttackName.CLOCK_ERROR: attack_clock_error,
    AttackName.CALIBRATION_DRIFT: attack_calibration_drift,
    AttackName.CLIPPING: attack_clipping,
    AttackName.ALIASING: attack_aliasing,
    AttackName.SPECTRAL_LEAKAGE: attack_spectral_leakage,
    AttackName.ENVIRONMENTAL_COUPLING: attack_environmental_coupling,
    AttackName.FIXTURE_EFFECT: attack_fixture_effect,
    AttackName.CROSS_TALK: attack_cross_talk,
    AttackName.SPECIMEN_MISMATCH: attack_specimen_mismatch,
    AttackName.MODEL_INADEQUACY: attack_model_inadequacy,
}


# --- running the battery --------------------------------------------------

def run_battery(signal, context: AttackContext) -> list[AttackResult]:
    """Run **every** attack and return **all** results, in fixed order.

    Both firing and non-firing (and inapplicable) attacks are returned, so
    failed explanations are preserved rather than discarded.
    """
    x = _as_signal(signal)
    return [ATTACKS[name](x, context) for name in ATTACKS]


def run_all_attacks(signal, context: AttackContext) -> list[AttackResult]:
    """Return the ordinary explanations that fired against ``signal``.

    A residual with **any** ordinary explanation is not unexplained.
    """
    return [r for r in run_battery(signal, context) if r.explained]


# --- the firewall verdict -------------------------------------------------

@dataclass(frozen=True)
class ResidualClassification:
    """The firewall's verdict on a candidate residual.

    Carries the full attack battery (every attempt, firing or not), the
    subset that fired, the residual class, and a canonical record that
    conforms to ``residual_record.schema.json``.
    """

    residual_id: str
    observation_ids: tuple
    classification: ResidualClass
    battery: tuple
    combined_uncertainty: dict
    peak_amplitude: float
    reopening_test: str

    @property
    def explanations(self) -> list[AttackResult]:
        return [r for r in self.battery if r.explained]

    @property
    def claim_class(self) -> claims.ClaimClass:
        if self.classification is ResidualClass.UNEXPLAINED_INSTRUMENT_RESIDUAL:
            return RESIDUAL_CEILING
        if self.classification is ResidualClass.ORDINARY_EXPLANATION_FOUND:
            # the strongest-standing ordinary class among those that fired
            return self.explanations[0].claim_class
        return claims.ClaimClass.KNOWN_ORDINARY_EFFECT

    def as_record(self) -> dict:
        """A residual record conforming to residual_record.schema.json."""
        return {
            "residual_id": self.residual_id,
            "observation_ids": list(self.observation_ids),
            "ordinary_explanation_attacks": [r.as_dict() for r in self.battery],
            "combined_uncertainty": dict(self.combined_uncertainty),
            "classification": self.classification.value,
            "reopening_test": self.reopening_test,
            "claim_class": self.claim_class.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


def classify_residual(signal, context: AttackContext) -> ResidualClassification:
    """Run the firewall and classify a candidate residual.

    The verdict, in order:

    1. If the residual's peak amplitude is within the combined uncertainty
       coverage, it is ``NOISE_WITHIN_UNCERTAINTY`` -- not anomalous, and
       the attacks are still recorded.
    2. If **any** ordinary-explanation attack fires, it is
       ``ORDINARY_EXPLANATION_FOUND`` -- not unexplained.
    3. Only a residual above the budget that survives every attack reaches
       the ``UNEXPLAINED_INSTRUMENT_RESIDUAL`` ceiling. It is never new
       physics.
    """
    x = _as_signal(signal)
    battery = run_battery(x, context)
    fired = [r for r in battery if r.explained]
    peak = float(np.max(np.abs(_finite(x)))) if _finite(x).size else 0.0
    budget = {
        "combined_uncertainty": float(context.combined_uncertainty),
        "coverage_factor": float(context.coverage_factor),
        "coverage": float(context.coverage()),
        "residual_peak": peak,
    }
    within_budget = peak <= context.coverage()

    if within_budget:
        classification = ResidualClass.NOISE_WITHIN_UNCERTAINTY
        reopening = (
            "raise the residual above the combined-uncertainty coverage "
            "(k*u) with a real acquisition before treating it as anomalous")
    elif fired:
        classification = ResidualClass.ORDINARY_EXPLANATION_FOUND
        names = ", ".join(r.name.value for r in fired)
        reopening = (
            f"remove the ordinary cause(s) [{names}] and re-acquire; the "
            f"residual is explained until they are ruled out")
    else:
        classification = ResidualClass.UNEXPLAINED_INSTRUMENT_RESIDUAL
        reopening = (
            "independently replicate on a different apparatus and operator; "
            "an UNEXPLAINED_INSTRUMENT_RESIDUAL is the ceiling and is not "
            "new physics until replicated")

    return ResidualClassification(
        residual_id=context.residual_id,
        observation_ids=tuple(context.observation_ids),
        classification=classification,
        battery=tuple(battery),
        combined_uncertainty=budget,
        peak_amplitude=peak,
        reopening_test=reopening,
    )


# --- the load-bearing refusal --------------------------------------------

def refuse_residual_before_attacks(battery) -> None:
    """Refuse the UNEXPLAINED label before the attack battery has run.

    An ``UNEXPLAINED_INSTRUMENT_RESIDUAL`` is a residual that *survived*
    every ordinary-explanation attack. Applying the label without running
    them -- or with an empty battery -- inverts the firewall, so it is
    refused. Delegates to the governance core's residual refusal for the
    canonical text.
    """
    if battery is None or len(tuple(battery)) == 0:
        raise OrdinaryExplanationError(
            "refused: a residual cannot be called "
            "UNEXPLAINED_INSTRUMENT_RESIDUAL before the ordinary-explanation "
            "attack battery has run. The label is earned by surviving the "
            "attacks, not asserted ahead of them. "
            f"{PHYSICAL_VALIDATION}. {VERDICT}")


def refuse_residual_as_new_physics(*_a, **_k) -> None:
    """An unexplained instrument residual is never new physics."""
    claims.refuse_residual_as_new_physics()


# --- report ---------------------------------------------------------------

def ordinary_explanations_report() -> dict:
    """The standing statement of what the firewall is and is not."""
    return {
        "what_this_is": (
            "the R15 ordinary-explanation firewall as code: eleven attacks "
            "(raw-data defect, clock error, calibration drift, clipping, "
            "aliasing, spectral leakage, environmental coupling, fixture "
            "effect, cross-talk, specimen mismatch, model inadequacy), each "
            "a detector that must be survived before a residual may be "
            "called UNEXPLAINED_INSTRUMENT_RESIDUAL"),
        "attacks": [a.value for a in AttackName],
        "n_attacks": len(ATTACKS),
        "residual_classes": [c.value for c in ResidualClass],
        "residual_ceiling": RESIDUAL_CEILING.value,
        "no_exclusive_authority": (
            "the firewall verdict is a union over all attacks; no single "
            "attack can declare a residual unexplained"),
        "refusals": [
            "refuse_residual_before_attacks (no UNEXPLAINED label before the "
            "battery runs)",
            "refuse_residual_as_new_physics (the ceiling is never new "
            "physics)",
            "a residual below combined uncertainty is not anomalous",
        ],
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not measure anything and it does not detect new "
            "physics. Every fixture is a seeded synthetic waveform. The "
            "strongest label any residual reaches here is "
            "UNEXPLAINED_INSTRUMENT_RESIDUAL, which is the ceiling for an "
            "unreplicated residual that survived the ordinary-explanation "
            "attacks -- not a resonance, not a particle, not a new energy. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION",
    "SOFTWARE_CLAIM_CLASS", "RESIDUAL_CEILING",
    "OrdinaryExplanationError",
    "AttackName", "ResidualClass", "AttackContext", "AttackResult",
    "ATTACK_CLAIM_CLASS", "ATTACKS",
    "attack_raw_data_defect", "attack_clock_error",
    "attack_calibration_drift", "attack_clipping", "attack_aliasing",
    "attack_spectral_leakage", "attack_environmental_coupling",
    "attack_fixture_effect", "attack_cross_talk", "attack_specimen_mismatch",
    "attack_model_inadequacy",
    "run_battery", "run_all_attacks",
    "ResidualClassification", "classify_residual",
    "refuse_residual_before_attacks", "refuse_residual_as_new_physics",
    "ordinary_explanations_report",
]
