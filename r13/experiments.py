"""P25-P30 — the prospective experiment registry: six preregistered
protocols, none executed.

R13 assembles an apparatus stack, a detector chain, a transform library
and a feature disk, and the obvious question is what they would show if
run. This module answers that question honestly by *refusing to answer
it*. It registers the six experiments the pack calls out -- a baseline
modal survey, an avoided-crossing sweep, a rotation-versus-squeeze
discrimination, a polarization state discrimination, a cutoff-phase
timing measurement, and a cross-domain transfer benchmark -- as
**preregistered protocols**: a hypothesis, a predicted signature, a null
model, and a decision rule for each, and a status that stays
``PREREGISTERED_NOT_RUN`` because none of them can be performed in this
environment.

**A predicted signature is not a result.** The whole point of writing the
prediction down *before* any bench exists is that it cannot then be
quietly reread as an outcome. :class:`Experiment` refuses a ``RUN`` status
and refuses a measurement claim class at construction, so an experiment
cannot pretend to have executed;
:func:`refuse_prediction_as_result` and
:func:`refuse_preregistration_as_confirmation` refuse the two ways a
preregistration tries to launder itself into evidence.

**Every experiment must be able to fail, and must be able to succeed.**
This is the R10.6 band-clustering lesson made structural: a null result
means nothing unless the method could have detected a real effect. So
each protocol declares a **null model** (what the world looks like if the
hypothesis is false) *and* carries ``power_on_planted_data`` -- a promise
that the analysis provably flags a planted effect. :func:`validate_registry`
checks all six carry both, and an experiment missing its null model is
refused. :func:`planted_signal_power_check` demonstrates the discipline
in miniature: a detector must flag a planted effect and must return null
on pure noise, or it has no power and its null result is empty.

Nothing here is measured. The registry is a set of predictions and the
verdict is ``PROSPECTIVE_EXPERIMENT_REGISTRY_PREREGISTERED``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

import numpy as np

#: The standing verdict. Six predictions, none run.
DEFAULT_VERDICT = "PROSPECTIVE_EXPERIMENT_REGISTRY_PREREGISTERED"

#: The only claim class a prediction is allowed to carry.
PREDICTION_CLAIM_CLASS = "PROSPECTIVE_PREDICTION"

#: The only status a registered experiment is allowed to hold.
PREREGISTERED_STATUS = "PREREGISTERED_NOT_RUN"

#: Claim classes that assert a measurement happened. A prediction may
#: never carry one -- that would be the prediction claiming to be a result.
MEASUREMENT_CLAIM_CLASSES = frozenset({
    "BENCH_MEASUREMENT",
    "INDEPENDENTLY_REPLICATED",
})

CLAIM_CLASSES = (
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "PROSPECTIVE_PREDICTION",
    "BENCH_MEASUREMENT",
    "INDEPENDENTLY_REPLICATED",
    "BLOCKED_MISSING_INPUT",
)


class ExperimentsError(RuntimeError):
    """Raised on a malformed protocol, an experiment claiming to have run,
    a registry missing a null model, or a preregistration read as a
    confirmed result."""


class ExperimentId(Enum):
    """The six prospective experiments, keyed by their pack index."""

    P25_BASELINE_MODAL_SURVEY = "P25_BASELINE_MODAL_SURVEY"
    P26_AVOIDED_CROSSING_SWEEP = "P26_AVOIDED_CROSSING_SWEEP"
    P27_ROTATION_VS_SQUEEZE = "P27_ROTATION_VS_SQUEEZE"
    P28_POLARIZATION_STATE = "P28_POLARIZATION_STATE"
    P29_CUTOFF_PHASE_TIMING = "P29_CUTOFF_PHASE_TIMING"
    P30_CROSS_DOMAIN_TRANSFER = "P30_CROSS_DOMAIN_TRANSFER"


@dataclass(frozen=True)
class Experiment:
    """One preregistered protocol: hypothesis, predicted signature, null
    model, decision rule, and the two power promises.

    ``power_on_planted_data`` records that the analysis provably detects a
    planted effect -- without it, a null result is indistinguishable from
    a method that could never have seen anything. ``status`` is pinned to
    ``PREREGISTERED_NOT_RUN`` and ``claim_class`` to ``PROSPECTIVE_
    PREDICTION``; the ``__post_init__`` refuses any attempt to declare the
    experiment run or to give the prediction a measurement class."""

    id: ExperimentId
    title: str
    hypothesis: str
    predicted_signature: str
    null_model: str
    decision_rule: str
    power_on_planted_data: bool
    claim_class: str = PREDICTION_CLAIM_CLASS
    status: str = PREREGISTERED_STATUS

    def __post_init__(self) -> None:
        if not isinstance(self.id, ExperimentId):
            raise ExperimentsError("id must be an ExperimentId")
        for name in ("title", "hypothesis", "predicted_signature",
                     "decision_rule"):
            if not getattr(self, name):
                raise ExperimentsError(f"an experiment needs a {name}")
        if not isinstance(self.power_on_planted_data, bool):
            raise ExperimentsError("power_on_planted_data must be a bool")
        if self.claim_class in MEASUREMENT_CLAIM_CLASSES:
            raise ExperimentsError(
                f"refused: experiment {self.id.value} declares claim class "
                f"{self.claim_class!r}, a measurement class. A "
                f"preregistered prediction has measured nothing; it may "
                f"only carry {PREDICTION_CLAIM_CLASS}.")
        if self.claim_class != PREDICTION_CLAIM_CLASS:
            raise ExperimentsError(
                f"a registered experiment must carry claim class "
                f"{PREDICTION_CLAIM_CLASS}, not {self.claim_class!r}")
        if self.status == "RUN" or self.status in MEASUREMENT_CLAIM_CLASSES:
            raise ExperimentsError(
                f"refused: experiment {self.id.value} declares status "
                f"{self.status!r}. None of these experiments has been run "
                f"-- no bench exists in this environment -- so the only "
                f"legal status is {PREREGISTERED_STATUS}.")
        if self.status != PREREGISTERED_STATUS:
            raise ExperimentsError(
                f"status must be {PREREGISTERED_STATUS}, not "
                f"{self.status!r}")

    def has_null_model(self) -> bool:
        return bool(self.null_model)

    def as_dict(self) -> dict:
        return {
            "id": self.id.value,
            "title": self.title,
            "hypothesis": self.hypothesis,
            "predicted_signature": self.predicted_signature,
            "null_model": self.null_model,
            "decision_rule": self.decision_rule,
            "power_on_planted_data": self.power_on_planted_data,
            "claim_class": self.claim_class,
            "status": self.status,
        }


# =======================================================================
# The six preregistered experiments
# =======================================================================

def _build_registry() -> tuple[Experiment, ...]:
    """The six prospective experiments, P25 through P30."""
    return (
        Experiment(
            id=ExperimentId.P25_BASELINE_MODAL_SURVEY,
            title="Baseline modal survey",
            hypothesis=(
                "the resonator's low-order modes sit at the frequencies "
                "and Q-factors the analytic model predicts, within the "
                "declared tolerance"),
            predicted_signature=(
                "a comb of Lorentzian peaks at the predicted mode "
                "frequencies, each with a linewidth set by its predicted "
                "damping"),
            null_model=(
                "a smooth response with no peaks above the noise floor, or "
                "peaks whose positions are consistent with a uniform draw "
                "over the survey band (look-elsewhere corrected)"),
            decision_rule=(
                "CONFIRM if predicted peaks are resolved above the null "
                "band at the preregistered SNR; REFUTE if the observed "
                "peak positions are no better matched to the prediction "
                "than to random frequencies of the same count"),
            power_on_planted_data=True,
        ),
        Experiment(
            id=ExperimentId.P26_AVOIDED_CROSSING_SWEEP,
            title="Avoided-crossing sweep",
            hypothesis=(
                "as a tuning parameter is swept, two modes that would "
                "cross instead repel, with a minimum gap set by the "
                "predicted coupling"),
            predicted_signature=(
                "an anticrossing: the two eigenfrequency branches approach "
                "and separate with a nonzero minimum gap, and the "
                "eigenvectors hybridise at the closest approach"),
            null_model=(
                "two independent modes that cross freely (zero gap) as the "
                "parameter is swept, i.e. no coupling"),
            decision_rule=(
                "CONFIRM if the fitted minimum gap exceeds the linewidth "
                "and matches the predicted coupling; REFUTE if the "
                "branches cross within resolution (gap consistent with "
                "zero)"),
            power_on_planted_data=True,
        ),
        Experiment(
            id=ExperimentId.P27_ROTATION_VS_SQUEEZE,
            title="Rotation versus squeeze discrimination",
            hypothesis=(
                "the two-mode transformation under drive is a rotation "
                "(area-preserving, bounded) rather than a squeeze "
                "(area-preserving, unbounded along one quadrature)"),
            predicted_signature=(
                "quadrature variances that oscillate and stay bounded "
                "(rotation), as opposed to one quadrature growing "
                "exponentially while the conjugate one shrinks (squeeze)"),
            null_model=(
                "an isotropic classical drift with no coherent quadrature "
                "structure -- variances that neither rotate nor squeeze "
                "beyond the noise"),
            decision_rule=(
                "CONFIRM ROTATION if the covariance eigenvalues stay "
                "bounded and the principal axis precesses; CONFIRM SQUEEZE "
                "if one eigenvalue grows past the preregistered threshold; "
                "REFUTE both if neither exceeds the isotropic null"),
            power_on_planted_data=True,
        ),
        Experiment(
            id=ExperimentId.P28_POLARIZATION_STATE,
            title="Linear / elliptical / circular polarization discrimination",
            hypothesis=(
                "the emitted response carries a definite polarization "
                "state -- linear, elliptical, or circular -- predicted by "
                "the drive geometry"),
            predicted_signature=(
                "Stokes parameters that place the state at the predicted "
                "point on the Poincare sphere, with the predicted "
                "handedness for the circular case"),
            null_model=(
                "unpolarized response: Stokes parameters consistent with "
                "the origin of the Poincare sphere (degree of polarization "
                "consistent with zero)"),
            decision_rule=(
                "CONFIRM if the measured degree and ellipticity match the "
                "prediction above the unpolarized null; REFUTE if the "
                "degree of polarization is consistent with zero or the "
                "ellipticity contradicts the prediction"),
            power_on_planted_data=True,
        ),
        Experiment(
            id=ExperimentId.P29_CUTOFF_PHASE_TIMING,
            title="Cutoff-phase timing",
            hypothesis=(
                "the response phase advances through the predicted value "
                "at the predicted cutoff time, with the predicted slope"),
            predicted_signature=(
                "a phase-versus-time trace that reaches the predicted "
                "phase at the cutoff instant, distinguishable from a "
                "constant-rate advance"),
            null_model=(
                "a constant-rate (linear) phase advance with no feature at "
                "the predicted cutoff -- timing jitter drawn from the "
                "measured clock noise"),
            decision_rule=(
                "CONFIRM if the phase feature appears at the predicted "
                "time within the jitter budget; REFUTE if the trace is "
                "consistent with a featureless linear advance"),
            power_on_planted_data=True,
        ),
        Experiment(
            id=ExperimentId.P30_CROSS_DOMAIN_TRANSFER,
            title="Cross-domain transfer benchmark",
            hypothesis=(
                "a signature injected in one domain (mechanical) appears "
                "in another (electrical or optical) with the transfer "
                "efficiency the certificate predicts"),
            predicted_signature=(
                "a coherent response in the receiving domain at the "
                "injected frequency, with amplitude set by the predicted "
                "overlap and phase locked to the drive"),
            null_model=(
                "no coherent transfer: the receiving-domain response at "
                "the injected frequency is consistent with crosstalk and "
                "pickup measured with the coupling nominally switched off"),
            decision_rule=(
                "CONFIRM if the transferred amplitude exceeds the "
                "coupling-off null and matches the predicted overlap; "
                "REFUTE if it is consistent with the crosstalk null"),
            power_on_planted_data=True,
        ),
    )


#: The six preregistered experiments, in pack order.
REGISTRY: tuple[Experiment, ...] = _build_registry()

assert len(REGISTRY) == 6, "the registry holds exactly six experiments"


def get_experiment(exp_id: ExperimentId) -> Experiment:
    """The registered experiment with a given id."""
    if not isinstance(exp_id, ExperimentId):
        raise ExperimentsError("exp_id must be an ExperimentId")
    for e in REGISTRY:
        if e.id is exp_id:
            return e
    raise ExperimentsError(f"no registered experiment {exp_id!r}")


# =======================================================================
# Registry validation: null models and power everywhere
# =======================================================================

def validate_registry(registry: tuple[Experiment, ...] | None = None) -> dict:
    """Check every experiment declares a null model and a power promise.

    This enforces the R10.6 lesson at the registry level: an experiment
    with no null model cannot say what a negative result would look like,
    and one without a power promise cannot say a negative result means
    anything. Both are required of all six, and either missing is a
    refusal."""
    experiments = REGISTRY if registry is None else tuple(registry)
    if len(experiments) != 6:
        raise ExperimentsError(
            f"refused: the registry must hold exactly six experiments, "
            f"found {len(experiments)}")
    missing_null = [e.id.value for e in experiments if not e.has_null_model()]
    if missing_null:
        raise ExperimentsError(
            f"refused: {len(missing_null)} experiment(s) have no null "
            f"model ({', '.join(missing_null)}). Without a null model an "
            f"experiment cannot say what the world looks like if its "
            f"hypothesis is false, so a negative result would be "
            f"uninterpretable. Every protocol must declare one.")
    no_power = [e.id.value for e in experiments
                if not e.power_on_planted_data]
    if no_power:
        raise ExperimentsError(
            f"refused: {len(no_power)} experiment(s) do not promise power "
            f"on planted data ({', '.join(no_power)}). A null result from "
            f"a method that could never detect a real effect is empty. "
            f"Every protocol must prove it detects a planted effect.")
    return {
        "experiment_count": len(experiments),
        "all_have_null_model": True,
        "all_have_power_on_planted_data": True,
        "all_preregistered_not_run": all(
            e.status == PREREGISTERED_STATUS for e in experiments),
        "ids": [e.id.value for e in experiments],
    }


# =======================================================================
# The power discipline in miniature
# =======================================================================

def planted_signal_power_check(
        detect_func: Callable[[np.ndarray], bool],
        planted_effect: np.ndarray, *,
        noise_seed: int = 20260724,
        noise_scale: float = 1.0) -> dict:
    """Demonstrate the power discipline on one detector.

    A detector earns the right to report a null only if it would have
    flagged a real effect. So this runs ``detect_func`` twice: once on the
    ``planted_effect`` (it must flag it -- POWER) and once on pure noise of
    the same shape (it must not -- SPECIFICITY). A detector that fails
    either half has no power to report, and its null result would mean
    nothing.

    ``detect_func`` takes an array and returns True iff it flags an effect."""
    planted = np.asarray(planted_effect, dtype=float)
    if planted.size == 0:
        raise ExperimentsError("planted effect must be non-empty")
    rng = np.random.default_rng(noise_seed)
    noise = rng.normal(0.0, noise_scale, size=planted.shape)
    detects_planted = bool(detect_func(planted))
    detects_noise = bool(detect_func(noise))
    has_power = detects_planted and not detects_noise
    return {
        "detects_planted_effect": detects_planted,
        "detects_pure_noise": detects_noise,
        "has_power": has_power,
        "note": (
            "a detector has power only if it flags the planted effect and "
            "stays silent on pure noise; a null from a detector without "
            "power is empty" if has_power else
            "this detector failed the power discipline: it either missed "
            "the planted effect or fired on pure noise, so its null "
            "results carry no weight"),
    }


# =======================================================================
# The two refusals
# =======================================================================

def refuse_prediction_as_result(experiment: Experiment | ExperimentId | str,
                                *_args, **_kwargs) -> None:
    """Refuse to read a predicted signature as a measured outcome.

    The predicted signature was written down before any bench existed, so
    that it could not later be reread as evidence. A prediction that the
    modes sit at certain frequencies is not a measurement that they do.
    None of these experiments has been run, and the predicted signature
    is refused as a result whatever it says."""
    if isinstance(experiment, Experiment):
        label = experiment.id.value
    elif isinstance(experiment, ExperimentId):
        label = experiment.value
    else:
        label = str(experiment)
    raise ExperimentsError(
        f"refused: the predicted signature of {label} is a "
        f"{PREDICTION_CLAIM_CLASS}, not a measured result. It was "
        f"preregistered precisely so it could not be reread as evidence "
        f"once a bench exists. No apparatus was operated; the status is "
        f"{PREREGISTERED_STATUS}. A prediction is not an outcome.")


def refuse_preregistration_as_confirmation(*_args, **_kwargs) -> None:
    """Refuse to treat the act of preregistering as a confirmation.

    Registering a protocol -- writing the hypothesis, the signature, the
    null and the decision rule -- commits to what would count as evidence.
    It is not itself evidence. A registry full of well-specified
    predictions confirms nothing about the world; it only fixes the rules
    by which a future measurement could."""
    raise ExperimentsError(
        "refused: preregistering an experiment is a commitment to how it "
        "would be judged, not a confirmation of its hypothesis. The "
        "registry declares six predictions with null models and decision "
        "rules; none has been run, and writing a prediction down does not "
        "make it true. Confirmation would require a measurement that does "
        "not exist here.")


# =======================================================================
# The report
# =======================================================================

def _demo_power_check() -> dict:
    """A concrete power check: a threshold detector on a planted step."""
    planted = np.concatenate([np.zeros(64), 8.0 * np.ones(64)])

    def detect(x: np.ndarray) -> bool:
        # flags a coherent shift in the second half above the first
        half = x.size // 2
        return bool(abs(x[half:].mean() - x[:half].mean()) > 3.0)

    return planted_signal_power_check(detect, planted)


def experiments_report() -> dict:
    validation = validate_registry()
    return {
        "what_this_is": (
            "a registry of six prospective experiments (P25-P30) as "
            "preregistered protocols -- hypothesis, predicted signature, "
            "null model, decision rule -- none of which has been run"),
        "experiments": [e.as_dict() for e in REGISTRY],
        "experiment_ids": [e.id.value for e in REGISTRY],
        "registry_validation": validation,
        "all_preregistered_not_run": validation["all_preregistered_not_run"],
        "all_have_null_model": validation["all_have_null_model"],
        "all_have_power_on_planted_data":
            validation["all_have_power_on_planted_data"],
        "power_discipline_demo": _demo_power_check(),
        "refusals": [
            "refuse_prediction_as_result",
            "refuse_preregistration_as_confirmation",
        ],
        "claim_class": PREDICTION_CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say any of the six experiments was run, that any "
            "predicted signature was observed, or that any hypothesis is "
            "confirmed. Every entry is a PROSPECTIVE_PREDICTION with status "
            "PREREGISTERED_NOT_RUN: a hypothesis, a signature the world "
            "would show if the hypothesis holds, a null model for what it "
            "shows if the hypothesis fails, and a decision rule that fixes "
            "in advance what would confirm versus refute. Each protocol "
            "carries a null model and a power promise because the R10.6 "
            "band-clustering lesson is that a null result is meaningless "
            "unless the method could have detected a real effect. No "
            "apparatus exists in this environment, nothing was measured, "
            "and preregistering a prediction is not the same as "
            "confirming it. No physical validation is claimed."),
    }
