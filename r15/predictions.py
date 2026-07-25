"""P19 — the prospective prediction registry: seal the prediction before the run.

A confirmatory result means something only if the prediction it confirms was
fixed *before* the data existed. This module makes that order mechanical. A
prediction -- a hypothesis, a predicted signature broken out into named
quantities (with tolerances, modes, frequencies, directions, and the null
expectation for each), a null model, a decision rule, an analysis plan, and a
proven-power-on-planted-data promise -- is **sealed** at a passed-in epoch with
a SHA-256 commitment over the whole plan *and* over a fingerprint of the model,
code, data and parameters it was written against. Once sealed, the prediction
is a fixed object: any later edit changes the hash and is detectable, and a
result offered as confirmatory without a prior seal is, at most, exploratory.

**A sealed prediction is PROSPECTIVE, never a result.** Sealing commits what
the run *would* show if the hypothesis holds; it does not run anything.
:func:`refuse_prediction_as_result` refuses to read a sealed prediction as a
measured outcome, and every record carries claim class ``PROSPECTIVE_PREDICTION``
with an evidence level of E0 (a hypothesis on the ladder, nothing measured).

**Every prediction must be able to fail and to succeed.** This is the R10.6
band-clustering lesson made structural. :func:`refuse_prediction_without_null`
refuses a prediction with no null model -- a hypothesis with nothing to be
tested against confirms itself. :func:`refuse_prediction_without_power` refuses
one that never declares it can recover a planted effect of the predicted size --
a design that cannot detect its own hypothesis proves nothing when it fails and
little when it succeeds. :func:`power_on_planted_check` demonstrates the
discipline in miniature (reusing R13's): a detector must flag a planted effect
and stay silent on pure noise, or its null result is empty.

**The three forbidden retrofits.** :func:`refuse_edit_after_seal` catches
HARKing -- rewriting the hypothesis, the predicted quantities, or the analysis
plan after the seal and presenting it as the original.
:func:`refuse_result_without_prior_seal` refuses a confirmatory claim with no
sealed prediction: an analysis with no prior seal is EXPLORATORY, not
confirmatory. :func:`refuse_stale_prediction` invalidates a prediction whose
model/code/data/parameter fingerprint no longer matches the current one -- a
prediction sealed against a model that has since changed is stale, and running
it as though it still applied would confirm a prediction the current model
never made.

This module *extends* rather than duplicates: it reuses R13's preregistration
seal (:mod:`r13.preregister`), R13's power discipline
(:mod:`r13.experiments`), and R13's canonical serialization and hash chain
(:mod:`r13.serialize`), and it types every claim through :mod:`r15.claims`.

Nothing here is measured. Every prediction is a PROSPECTIVE_PREDICTION, the
strongest software class is ``MODEL_PREDICTION``, no apparatus is operated, and
the standing verdict is ``PROSPECTIVE_PREDICTION_REGISTRY_SEALED``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13 import experiments as _experiments
from r13 import preregister as _prereg
from r13 import serialize as _serialize
from r15 import claims as _claims

# =======================================================================
# Standing verdict, claim class, and the evidence level this touches
# =======================================================================

#: The standing verdict for a well-formed sealed prediction registry.
VERDICT = "PROSPECTIVE_PREDICTION_REGISTRY_SEALED"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The strongest class this module reaches from software alone. A sealed
#: prediction is a model prediction awaiting data, never a measurement.
CLAIM_CLASS = _claims.ClaimClass.MODEL_PREDICTION.value

#: The claim class every registered prediction carries: a prediction that
#: has been committed but not yet tested against data. Reused verbatim from
#: R13 so the whole platform names it identically.
PROSPECTIVE_PREDICTION = _prereg.PROSPECTIVE_PREDICTION

#: A sealed prediction sits at E0 on the R15 evidence ladder -- a hypothesis.
#: Sealing fixes it in advance; it does not move it up the ladder, because no
#: data have been acquired.
PREDICTION_EVIDENCE_LEVEL = _claims.EvidenceLevel.E0

#: Claim classes that assert a measurement happened. A prediction may never
#: carry one -- that would be the prediction claiming to be a result.
MEASUREMENT_CLAIM_CLASSES = _experiments.MEASUREMENT_CLAIM_CLASSES


class PredictionError(RuntimeError):
    """Raised on a malformed prediction, a prediction with no null model or
    no power promise, an edit after the seal (HARKing), a confirmatory claim
    with no prior seal, a stale prediction run against a changed model, or a
    sealed prediction read as a measured result."""


# =======================================================================
# Modes and directions
# =======================================================================

class PredictionMode(Enum):
    """Whether a prediction may confirm a hypothesis or only suggest one.

    An EXPLORATORY prediction generates hypotheses; a CONFIRMATORY one tests
    a hypothesis and analysis fixed in advance. The distinction is the whole
    point of a registry: a confirmatory result requires a prior seal, and an
    analysis with no seal is, at most, exploratory."""

    EXPLORATORY = "EXPLORATORY"
    CONFIRMATORY = "CONFIRMATORY"


class Direction(Enum):
    """The predicted direction of a quantity relative to its null.

    A prediction that only names a quantity is weak; a prediction that also
    fixes the direction of the effect (and, via the tolerance, its size) can
    be wrong in a way a directionless one cannot."""

    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    NONZERO = "NONZERO"
    UNCHANGED = "UNCHANGED"


# =======================================================================
# A predicted quantity: name, tolerance, mode, frequency, direction, null
# =======================================================================

@dataclass(frozen=True)
class PredictedQuantity:
    """One predicted quantity inside a predicted signature.

    Each quantity carries everything the pack asks a prediction to register:
    a ``name`` and ``unit``, a ``tolerance`` (the band within which the
    prediction counts as met), a ``mode`` label (the acquisition/analysis
    mode the quantity is read in), a ``frequency_hz`` (where in the spectrum
    it lives), a ``direction`` relative to the null, and the
    ``null_expectation`` -- what this quantity looks like if the hypothesis
    is false. A quantity with no null expectation is refused: without it, a
    negative result on this quantity would be uninterpretable."""

    name: str
    unit: str
    tolerance: float
    mode: str
    frequency_hz: float
    direction: Direction
    null_expectation: str

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise PredictionError("a predicted quantity needs a name")
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise PredictionError("a predicted quantity needs a unit")
        tol = float(self.tolerance)
        if not math.isfinite(tol) or tol < 0.0:
            raise PredictionError(
                "a predicted quantity's tolerance must be a finite, "
                "non-negative number (the band the prediction is met within)")
        if not math.isfinite(float(self.frequency_hz)):
            raise PredictionError("frequency_hz must be finite")
        if not isinstance(self.direction, Direction):
            raise PredictionError("direction must be a Direction")
        if not isinstance(self.mode, str) or not self.mode.strip():
            raise PredictionError("a predicted quantity needs a mode label")
        if not isinstance(self.null_expectation, str) or \
                not self.null_expectation.strip():
            raise PredictionError(
                "refused: a predicted quantity with no null expectation is "
                "not a prediction. State what this quantity looks like if "
                "the hypothesis is false, or a negative result cannot be "
                "read.")

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "unit": self.unit,
            "tolerance": float(self.tolerance),
            "mode": self.mode,
            "frequency_hz": float(self.frequency_hz),
            "direction": self.direction.value,
            "null_expectation": self.null_expectation,
        }


# =======================================================================
# The artifact fingerprint: hash of model, code, data, and parameters
# =======================================================================

@dataclass(frozen=True)
class ArtifactFingerprint:
    """A tamper-evident fingerprint of what a prediction was written against.

    ``model_hash``, ``code_hash``, ``data_hash`` and ``params_hash`` are the
    canonical content hashes (R13 serialize) of the model, the analysis code
    identifier, the (planted/holdout) data description, and the parameter
    set. Any change to any of them yields a different fingerprint, which is
    how a prediction is detected as stale after the model changes."""

    model_hash: str
    code_hash: str
    data_hash: str
    params_hash: str

    @classmethod
    def over(cls, model, code, data, params) -> "ArtifactFingerprint":
        """Build a fingerprint by canonically hashing each artifact."""
        return cls(
            model_hash=_serialize.content_hash(model),
            code_hash=_serialize.content_hash(code),
            data_hash=_serialize.content_hash(data),
            params_hash=_serialize.content_hash(params),
        )

    def combined(self) -> str:
        """A single hash over all four component hashes."""
        return _serialize.content_hash(self.as_dict())

    def as_dict(self) -> dict:
        return {
            "model_hash": self.model_hash,
            "code_hash": self.code_hash,
            "data_hash": self.data_hash,
            "params_hash": self.params_hash,
        }


# =======================================================================
# The registered prediction
# =======================================================================

#: The load-bearing fields whose change after sealing turns a prediction
#: into a different prediction wearing the old seal.
LOADBEARING_FIELDS = (
    "hypothesis",
    "predicted_signature",
    "analysis_plan",
    "decision_rule",
    "null_model",
    "quantities",
    "fingerprint",
)


@dataclass(frozen=True)
class RegisteredPrediction:
    """A prediction fixed before any run: hypothesis, predicted quantities,
    null model, decision rule, analysis plan, proven power, and a fingerprint
    of the model/code/data/parameters it was written against.

    ``epoch_committed`` is passed in by the caller and never read from the
    wall clock, so the seal is deterministic and reproducible.
    ``null_model`` and ``power_on_planted`` may not be empty: a prediction
    with no null cannot be wrong, and one with no proven power cannot mean
    anything when it fails. ``claim_class`` is pinned to
    ``PROSPECTIVE_PREDICTION``; a measurement class is refused at birth."""

    prediction_id: str
    hypothesis: str
    predicted_signature: str
    quantities: tuple
    null_model: str
    decision_rule: str
    analysis_plan: str
    power_on_planted: str
    fingerprint: ArtifactFingerprint
    stopping_rule: str = ""
    mode: PredictionMode = PredictionMode.CONFIRMATORY
    epoch_committed: int = 0
    claim_class: str = PROSPECTIVE_PREDICTION

    def __post_init__(self) -> None:
        if not isinstance(self.prediction_id, str) or \
                not self.prediction_id.strip():
            raise PredictionError("prediction_id must be a non-empty string")
        if not isinstance(self.hypothesis, str) or not self.hypothesis.strip():
            raise PredictionError("hypothesis must be a non-empty string")
        if not isinstance(self.predicted_signature, str) or \
                not self.predicted_signature.strip():
            raise PredictionError(
                "predicted_signature must be a non-empty string")
        if not isinstance(self.decision_rule, str) or \
                not self.decision_rule.strip():
            raise PredictionError("decision_rule must be a non-empty string")
        if not isinstance(self.analysis_plan, str) or \
                not self.analysis_plan.strip():
            raise PredictionError("analysis_plan must be a non-empty string")
        object.__setattr__(self, "quantities", tuple(self.quantities))
        if not self.quantities:
            raise PredictionError(
                "a prediction needs at least one predicted quantity")
        if not all(isinstance(q, PredictedQuantity) for q in self.quantities):
            raise PredictionError(
                "quantities must all be PredictedQuantity records")
        if not isinstance(self.fingerprint, ArtifactFingerprint):
            raise PredictionError("fingerprint must be an ArtifactFingerprint")
        if not isinstance(self.mode, PredictionMode):
            raise PredictionError("mode must be a PredictionMode")
        # The two structural refusals, at birth: a prediction with no null
        # model or no proven power is not a prediction.
        refuse_prediction_without_null(self)
        refuse_prediction_without_power(self)
        # A prediction may never carry a measurement claim class.
        if self.claim_class in MEASUREMENT_CLAIM_CLASSES:
            raise PredictionError(
                f"refused: prediction {self.prediction_id} declares claim "
                f"class {self.claim_class!r}, a measurement class. A sealed "
                f"prediction has measured nothing; it may only carry "
                f"{PROSPECTIVE_PREDICTION}.")
        if self.claim_class != PROSPECTIVE_PREDICTION:
            raise PredictionError(
                f"a registered prediction must carry claim class "
                f"{PROSPECTIVE_PREDICTION}, not {self.claim_class!r}")

    def base_preregistration(self) -> _prereg.Preregistration:
        """The R13 preregistration this prediction extends.

        The core plan -- hypothesis, predicted signature, null, decision
        rule, analysis plan, stopping rule, power -- maps onto an R13
        :class:`~r13.preregister.Preregistration`, so the R13 seal machinery
        is genuinely reused and its own null/decision refusals apply."""
        return _prereg.Preregistration(
            study_id=self.prediction_id,
            hypothesis=self.hypothesis,
            predicted_signature=self.predicted_signature,
            null_model=self.null_model,
            decision_rule=self.decision_rule,
            analysis_plan=self.analysis_plan,
            stopping_rule=self.stopping_rule,
            power_on_planted=self.power_on_planted,
            epoch_committed=self.epoch_committed,
            claim_class=self.claim_class,
        )

    def has_null_model(self) -> bool:
        return bool(self.null_model.strip())

    def declares_power(self) -> bool:
        return bool(self.power_on_planted.strip())

    def as_dict(self) -> dict:
        return {
            "prediction_id": self.prediction_id,
            "hypothesis": self.hypothesis,
            "predicted_signature": self.predicted_signature,
            "quantities": [q.as_dict() for q in self.quantities],
            "null_model": self.null_model,
            "decision_rule": self.decision_rule,
            "analysis_plan": self.analysis_plan,
            "power_on_planted": self.power_on_planted,
            "fingerprint": self.fingerprint.as_dict(),
            "stopping_rule": self.stopping_rule,
            "mode": self.mode.value,
            "epoch_committed": self.epoch_committed,
            "claim_class": self.claim_class,
        }


# =======================================================================
# Sealing: extend the R13 seal, bind the R15 fingerprint and quantities
# =======================================================================

#: commitment -> sealed body. The prediction seal ledger, append-only in
#: practice.
_LEDGER: dict = {}


def _sealed_body(prediction: RegisteredPrediction) -> dict:
    """The canonical content the commitment is taken over.

    Includes the R13 base seal (over the core plan) *and* the R15 additions
    -- the predicted quantities and the artifact fingerprint -- so the final
    commitment binds every input. Any change to any field alters this body
    and therefore the hash."""
    if not isinstance(prediction, RegisteredPrediction):
        raise PredictionError("expected a RegisteredPrediction")
    return {
        "base_seal": _prereg.seal(prediction.base_preregistration()),
        "prediction_id": prediction.prediction_id,
        "hypothesis": prediction.hypothesis,
        "predicted_signature": prediction.predicted_signature,
        "quantities": [q.as_dict() for q in prediction.quantities],
        "null_model": prediction.null_model,
        "decision_rule": prediction.decision_rule,
        "analysis_plan": prediction.analysis_plan,
        "power_on_planted": prediction.power_on_planted,
        "stopping_rule": prediction.stopping_rule,
        "mode": prediction.mode.value,
        "fingerprint": prediction.fingerprint.as_dict(),
        "epoch_committed": prediction.epoch_committed,
        "claim_class": prediction.claim_class,
    }


def seal(prediction: RegisteredPrediction) -> str:
    """Return the SHA-256 commitment over the whole prediction and record it.

    Deterministic -- the same prediction always yields the same hash -- and
    tamper-evident: any change to the hypothesis, a predicted quantity, the
    analysis plan, or the model/code/data/parameter fingerprint changes this
    hash, so a prediction quietly edited after the data arrived cannot
    masquerade as the sealed one."""
    body = _sealed_body(prediction)
    commitment = _serialize.content_hash(body)
    _LEDGER.setdefault(commitment, body)
    return commitment


def is_sealed(prediction_or_commitment) -> bool:
    """True iff this exact prediction (or this commitment) is in the ledger."""
    if isinstance(prediction_or_commitment, RegisteredPrediction):
        return seal(prediction_or_commitment) in _LEDGER
    if isinstance(prediction_or_commitment, str):
        return prediction_or_commitment in _LEDGER
    return False


def classify_analysis(commitment) -> str:
    """CONFIRMATORY iff a sealed prediction backs it; else EXPLORATORY.

    An analysis backed by a prior sealed commitment is confirmatory; one
    with no seal is exploratory whatever it looks like, because nothing
    distinguishes it from an analysis assembled once the answer was known."""
    if isinstance(commitment, str) and commitment in _LEDGER:
        return PredictionMode.CONFIRMATORY.value
    return PredictionMode.EXPLORATORY.value


# =======================================================================
# Staleness: a prediction sealed against a model that has since changed
# =======================================================================

def is_stale(prediction: RegisteredPrediction,
             current_fingerprint: ArtifactFingerprint) -> bool:
    """True iff the prediction's fingerprint no longer matches the current one.

    A prediction is sealed against a specific model, code, data description
    and parameter set. If any of those changes, the current fingerprint
    differs from the sealed one and the prediction is stale: it was written
    against a world that no longer exists."""
    if not isinstance(prediction, RegisteredPrediction):
        raise PredictionError("expected a RegisteredPrediction")
    if not isinstance(current_fingerprint, ArtifactFingerprint):
        raise PredictionError("current_fingerprint must be an ArtifactFingerprint")
    return prediction.fingerprint.combined() != current_fingerprint.combined()


def staleness_report(prediction: RegisteredPrediction,
                     current_fingerprint: ArtifactFingerprint) -> dict:
    """Which fingerprint components changed since the prediction was sealed."""
    sealed = prediction.fingerprint.as_dict()
    current = current_fingerprint.as_dict()
    changed = [k for k in sealed if sealed[k] != current[k]]
    return {
        "prediction_id": prediction.prediction_id,
        "stale": bool(changed),
        "changed_components": changed,
        "sealed_fingerprint": prediction.fingerprint.combined(),
        "current_fingerprint": current_fingerprint.combined(),
    }


# =======================================================================
# Power discipline: reuse the R13 planted-signal check
# =======================================================================

def power_on_planted_check(detect_func, planted_effect, *,
                           noise_seed: int = 20260724,
                           noise_scale: float = 1.0) -> dict:
    """Prove a detector has power on planted data (R13 discipline).

    Thin reuse of :func:`r13.experiments.planted_signal_power_check`: the
    detector must flag the planted effect (POWER) and stay silent on pure
    noise of the same shape (SPECIFICITY). A detector that fails either half
    has no power, and a null result from it would be empty."""
    return _experiments.planted_signal_power_check(
        detect_func, planted_effect, noise_seed=noise_seed,
        noise_scale=noise_scale)


# =======================================================================
# The registry
# =======================================================================

@dataclass
class PredictionRegistry:
    """A registry of sealed prospective predictions.

    :meth:`register` seals a prediction and stores its commitment;
    :meth:`validate` checks every registered prediction carries a null model
    and a proven-power promise (the R10.6 discipline at the registry level)
    and that none has drifted to a measurement class."""

    predictions: dict = field(default_factory=dict)
    commitments: dict = field(default_factory=dict)

    def register(self, prediction: RegisteredPrediction) -> str:
        """Seal a prediction and record it under its commitment."""
        if not isinstance(prediction, RegisteredPrediction):
            raise PredictionError("can only register a RegisteredPrediction")
        commitment = seal(prediction)
        self.predictions[prediction.prediction_id] = prediction
        self.commitments[prediction.prediction_id] = commitment
        return commitment

    def get(self, prediction_id: str) -> RegisteredPrediction:
        if prediction_id not in self.predictions:
            raise PredictionError(f"no registered prediction {prediction_id!r}")
        return self.predictions[prediction_id]

    def validate(self) -> dict:
        """Check every registered prediction carries a null and proven power.

        Construction already refuses a missing null or power, so a populated
        registry is valid by construction; this re-checks it explicitly and
        raises on any drift, matching the R13 registry discipline."""
        preds = tuple(self.predictions.values())
        missing_null = [p.prediction_id for p in preds if not p.has_null_model()]
        if missing_null:
            raise PredictionError(
                f"refused: {len(missing_null)} prediction(s) have no null "
                f"model ({', '.join(missing_null)}). A prediction with "
                f"nothing to be tested against confirms itself.")
        no_power = [p.prediction_id for p in preds if not p.declares_power()]
        if no_power:
            raise PredictionError(
                f"refused: {len(no_power)} prediction(s) do not prove power "
                f"on planted data ({', '.join(no_power)}). A null result "
                f"from a design that could never detect a real effect is "
                f"empty.")
        return {
            "prediction_count": len(preds),
            "all_have_null_model": True,
            "all_prove_power_on_planted_data": True,
            "all_prospective": all(
                p.claim_class == PROSPECTIVE_PREDICTION for p in preds),
            "ids": [p.prediction_id for p in preds],
        }


# =======================================================================
# Sealed bundles: a prediction committed onto an R13 hash chain
# =======================================================================

@dataclass(frozen=True)
class SealedBundle:
    """A sealed prediction committed onto an R13 tamper-evident hash chain.

    ``commitment`` is the prediction's seal; ``chain`` is the R13 serialize
    hash chain the commitment was appended to at ``epoch``. Editing any past
    record breaks :func:`verify_bundle`, so the order in which predictions
    were sealed is itself tamper-evident."""

    prediction_id: str
    commitment: str
    fingerprint_combined: str
    epoch: int
    chain: tuple


def seal_bundle(prediction: RegisteredPrediction, epoch: int,
                chain: tuple | None = None) -> SealedBundle:
    """Seal a prediction and append it to an R13 hash chain of commitments.

    ``epoch`` is passed in (never a clock read). If ``chain`` is None a new
    chain is started; otherwise the commitment is appended to the tip, so a
    sequence of sealed predictions forms a verifiable, ordered ledger."""
    commitment = seal(prediction)
    payload = {
        "prediction_id": prediction.prediction_id,
        "commitment": commitment,
        "fingerprint": prediction.fingerprint.as_dict(),
        "mode": prediction.mode.value,
        "claim_class": prediction.claim_class,
    }
    if chain is None:
        new_chain = _serialize.new_chain(
            payload, epoch, claim_class=PROSPECTIVE_PREDICTION)
    else:
        new_chain = _serialize.append_record(
            chain, payload, epoch, claim_class=PROSPECTIVE_PREDICTION)
    return SealedBundle(
        prediction_id=prediction.prediction_id,
        commitment=commitment,
        fingerprint_combined=prediction.fingerprint.combined(),
        epoch=int(epoch),
        chain=new_chain,
    )


def verify_bundle(bundle: SealedBundle) -> bool:
    """Verify the bundle's hash chain end to end (R13 serialize)."""
    if not isinstance(bundle, SealedBundle):
        raise PredictionError("expected a SealedBundle")
    return _serialize.verify_chain(bundle.chain)


# =======================================================================
# The refusals
# =======================================================================

def refuse_prediction_without_null(prediction: RegisteredPrediction) -> None:
    """Refuse a prediction that declares no null model.

    The R10.6 lesson: a hypothesis with nothing to be tested against
    confirms itself. Without a null model a prediction cannot say what the
    world looks like if it is false, so a negative result would be
    uninterpretable and a positive one unearned."""
    null_model = getattr(prediction, "null_model", "")
    if not isinstance(null_model, str) or not null_model.strip():
        raise PredictionError(
            "refused: a prediction with no null model is not a prediction. "
            "State the null the data could favour instead -- what this "
            "prediction looks like if the hypothesis is false -- or it "
            "confirms itself.")


def refuse_prediction_without_power(prediction: RegisteredPrediction) -> None:
    """Refuse a prediction that never proves power on planted data.

    A prediction has to be able to fail *and* to succeed for the right
    reason. If the design cannot recover an effect of the predicted size
    when one is planted, a null result proves nothing and a positive one is
    suspect. The declaration is a statement that, on data with a planted
    effect, the sealed analysis would detect it."""
    power = getattr(prediction, "power_on_planted", "")
    if not isinstance(power, str) or not power.strip():
        raise PredictionError(
            "refused: a prediction that does not prove power on planted "
            "data is empty. A design that cannot detect its own hypothesis "
            "proves nothing when it fails and little when it succeeds. "
            "Declare, and demonstrate, that the sealed analysis recovers a "
            "planted effect of the predicted size.")


def refuse_result_without_prior_seal(commitment=None, *,
                                     claim: str = "confirmatory") -> None:
    """Refuse a confirmatory claim with no prior sealed prediction.

    An analysis produced without a prior sealed prediction may be perfectly
    honest and is still, at most, EXPLORATORY: nothing distinguishes it from
    an analysis assembled once the answer was visible. It can suggest a
    hypothesis; it cannot confirm one. Seal a prediction first."""
    if not isinstance(commitment, str) or not commitment or \
            commitment not in _LEDGER:
        raise PredictionError(
            f"refused: a {claim} claim needs a sealed prediction, and none "
            f"was supplied (or the commitment is not in the ledger). An "
            f"analysis with no prior seal is at most EXPLORATORY -- it may "
            f"generate a hypothesis but cannot confirm one, because it "
            f"could have been chosen after the result was known. Seal a "
            f"prediction first, then this analysis can run as confirmatory.")


def _loadbearing_view(prediction: RegisteredPrediction) -> dict:
    """The load-bearing fields in a comparable, hashable form."""
    return {
        "hypothesis": prediction.hypothesis,
        "predicted_signature": prediction.predicted_signature,
        "analysis_plan": prediction.analysis_plan,
        "decision_rule": prediction.decision_rule,
        "null_model": prediction.null_model,
        "quantities": tuple(q.as_dict() for q in prediction.quantities),
        "fingerprint": prediction.fingerprint.as_dict(),
    }


def refuse_edit_after_seal(sealed: RegisteredPrediction,
                           proposed: RegisteredPrediction, *,
                           already_sealed: bool = True) -> dict:
    """Refuse to relabel an edited prediction as the sealed one (HARKing).

    The prediction is sealed, the data come in, and someone rewrites the
    hypothesis (or a predicted quantity, or the analysis plan, or the model
    fingerprint) so the result becomes the thing that was 'predicted'. Each
    edit can look like a clarification; together they turn an exploratory
    finding into a counterfeit confirmation. The edit is legal before the
    seal and forbidden after."""
    if not isinstance(sealed, RegisteredPrediction) or \
            not isinstance(proposed, RegisteredPrediction):
        raise PredictionError("both arguments must be RegisteredPredictions")
    a = _loadbearing_view(sealed)
    b = _loadbearing_view(proposed)
    changed = [name for name in LOADBEARING_FIELDS if a[name] != b[name]]
    if changed and already_sealed:
        raise PredictionError(
            f"refused: {len(changed)} load-bearing field(s) changed after "
            f"the prediction was sealed ({', '.join(changed)}). A prediction "
            f"rewritten once the data are in view and then presented as "
            f"prospective is HARKing: it was fitted to the result it claims "
            f"to have predicted. The sealed commitment is {seal(sealed)}; "
            f"the proposed one is {seal(proposed)}. Seal the new prediction "
            f"as a fresh, exploratory plan and test it on data it has not "
            f"seen.")
    return {
        "changed_fields": list(changed),
        "already_sealed": bool(already_sealed),
        "sealed_commitment": seal(sealed),
        "proposed_commitment": seal(proposed),
        "allowed": True,
    }


def refuse_stale_prediction(prediction: RegisteredPrediction,
                            current_fingerprint: ArtifactFingerprint) -> None:
    """Refuse to run a prediction whose model/code/data has since changed.

    A prediction sealed against a model that has since changed is stale.
    Running it as though it still applied would confirm a prediction the
    current model never made -- the fingerprint bound to the seal no longer
    matches the world the analysis runs in. Re-seal against the current
    model as a fresh prediction instead."""
    if is_stale(prediction, current_fingerprint):
        report = staleness_report(prediction, current_fingerprint)
        raise PredictionError(
            f"refused: prediction {prediction.prediction_id} is stale. Its "
            f"fingerprint components {report['changed_components']} changed "
            f"since it was sealed, so it was written against a model, code, "
            f"data, or parameter set that no longer exists. Running it now "
            f"would confirm a prediction the current model never made. "
            f"Re-seal against the current fingerprint as a new prediction.")


def refuse_prediction_as_result(prediction=None, *_args, **_kwargs) -> None:
    """Refuse to read a sealed prediction as a measured outcome.

    A sealed prediction is a statement about what *would* be observed if the
    hypothesis holds. Sealing commits it; it does not run anything. The
    strongest thing a seal establishes is PROSPECTIVE_PREDICTION -- never a
    measurement, never a confirmed result."""
    label = (prediction.prediction_id
             if isinstance(prediction, RegisteredPrediction)
             else str(prediction) if prediction is not None else "<prediction>")
    raise PredictionError(
        f"refused: the sealed prediction {label} is a "
        f"{PROSPECTIVE_PREDICTION}, not a measured outcome. Sealing commits "
        f"what the run predicts; it does not perform the run. No apparatus "
        f"was operated; a prediction cannot be reported as a measurement or "
        f"a confirmed result until data exist and the sealed analysis has "
        f"been run against them.")


# =======================================================================
# A worked, fully specified example
# =======================================================================

#: The model, code, data description and parameters the example prediction is
#: sealed against. Neutral synthetic tokens -- nothing here names or implies
#: any real quantity, specimen, apparatus, or measurement.
EXAMPLE_MODEL = {"model_id": "SYNTHETIC_MODEL_V1", "order": 4}
EXAMPLE_CODE = {"analysis_id": "SYNTHETIC_ANALYSIS_V1"}
EXAMPLE_DATA = {"dataset_id": "PLANTED_HOLDOUT_V1", "n": 160}
EXAMPLE_PARAMS = {"margin": 0.15, "seed": 20260724}

#: The fingerprint the example prediction is sealed against.
EXAMPLE_FINGERPRINT = ArtifactFingerprint.over(
    EXAMPLE_MODEL, EXAMPLE_CODE, EXAMPLE_DATA, EXAMPLE_PARAMS)


def example_quantities() -> tuple:
    """A synthetic predicted signature broken into two named quantities."""
    return (
        PredictedQuantity(
            name="planted_hit_rate_excess",
            unit="fraction",
            tolerance=0.15,
            mode="HELD_OUT_HIT_RATE",
            frequency_hz=0.0,
            direction=Direction.INCREASE,
            null_expectation=(
                "hit rate no better than the best of four matched "
                "shuffled-label nulls (excess consistent with zero)"),
        ),
        PredictedQuantity(
            name="synthetic_tone_amplitude",
            unit="arb",
            tolerance=0.05,
            mode="AMPLITUDE_SPECTRUM",
            frequency_hz=1000.0,
            direction=Direction.NONZERO,
            null_expectation=(
                "a smooth spectrum with no tone above the synthetic noise "
                "floor at the predicted frequency"),
        ),
    )


#: A complete, well-formed prediction. Every field is populated and the epoch
#: is passed in explicitly, so its seal is deterministic and reproducible.
EXAMPLE_PREDICTION = RegisteredPrediction(
    prediction_id="R15_P19_PREDICTION_EXAMPLE",
    hypothesis=(
        "the frozen synthetic codec assigns held-out tokens to their sealed "
        "alias sets at a rate above the shuffled-label null, and a planted "
        "tone appears at the predicted frequency"),
    predicted_signature=(
        "a held-out hit-rate excess over the best matched null exceeding the "
        "preregistered margin, and a resolved tone at the predicted "
        "frequency above the synthetic noise floor"),
    quantities=example_quantities(),
    null_model=(
        "shuffled labels and a tone-free smooth spectrum: same inputs, "
        "wrongly paired labels preserving both marginals, and no coherent "
        "tone above the noise floor"),
    decision_rule=(
        "declare CONFIRM only if the held-out excess exceeds 0.15 over the "
        "best null AND the tone is resolved above the floor; REFUTE if "
        "either is consistent with its null"),
    analysis_plan=(
        "freeze the codec and the spectrum estimator, reveal held-out "
        "labels once, compute the excess against the planted control and all "
        "four nulls and the tone amplitude, with no re-freezing"),
    power_on_planted=(
        "on data planted by the codec's own canonical reading, and with a "
        "tone injected at the predicted amplitude, the sealed analysis "
        "recovers both effects and returns null on shuffled, tone-free "
        "data, so the design has power"),
    fingerprint=EXAMPLE_FINGERPRINT,
    stopping_rule=(
        "fixed sample of 160 held-out trials, decided in advance; no interim "
        "looks"),
    mode=PredictionMode.CONFIRMATORY,
    epoch_committed=20260724,
)


def example_seal() -> str:
    """Seal the worked example and return its commitment."""
    return seal(EXAMPLE_PREDICTION)


def _demo_power_check() -> dict:
    """A concrete power check: a threshold detector on a planted step."""
    planted = np.concatenate([np.zeros(64), 8.0 * np.ones(64)])

    def detect(x: np.ndarray) -> bool:
        half = x.size // 2
        return bool(abs(x[half:].mean() - x[:half].mean()) > 3.0)

    return power_on_planted_check(detect, planted)


# =======================================================================
# The report
# =======================================================================

def predictions_report() -> dict:
    """The standing result: a sealed prospective prediction registry."""
    prediction = EXAMPLE_PREDICTION
    commitment = seal(prediction)

    # Register into a fresh registry and validate it.
    registry = PredictionRegistry()
    registry.register(prediction)
    registry_validation = registry.validate()

    # An analysis with no prior seal is exploratory, not confirmatory.
    exploratory_refused = False
    try:
        refuse_result_without_prior_seal("not-a-sealed-commitment")
    except PredictionError:
        exploratory_refused = True
    unsealed_is_exploratory = (
        classify_analysis("not-a-sealed-commitment")
        == PredictionMode.EXPLORATORY.value)
    sealed_is_confirmatory = (
        classify_analysis(commitment) == PredictionMode.CONFIRMATORY.value)

    # An edit to a load-bearing field after the seal is detected (HARKing).
    edited = RegisteredPrediction(
        prediction_id=prediction.prediction_id,
        hypothesis=prediction.hypothesis + " (rewritten after the data)",
        predicted_signature=prediction.predicted_signature,
        quantities=prediction.quantities,
        null_model=prediction.null_model,
        decision_rule=prediction.decision_rule,
        analysis_plan=prediction.analysis_plan,
        power_on_planted=prediction.power_on_planted,
        fingerprint=prediction.fingerprint,
        stopping_rule=prediction.stopping_rule,
        mode=prediction.mode,
        epoch_committed=prediction.epoch_committed,
    )
    edit_refused = False
    try:
        refuse_edit_after_seal(prediction, edited)
    except PredictionError:
        edit_refused = True

    # A changed model fingerprint makes the prediction stale.
    changed_model = dict(EXAMPLE_MODEL)
    changed_model["order"] = 5
    current_fp = ArtifactFingerprint.over(
        changed_model, EXAMPLE_CODE, EXAMPLE_DATA, EXAMPLE_PARAMS)
    stale = is_stale(prediction, current_fp)
    stale_refused = False
    try:
        refuse_stale_prediction(prediction, current_fp)
    except PredictionError:
        stale_refused = True

    # A sealed prediction is never a result.
    prediction_as_result_refused = False
    try:
        refuse_prediction_as_result(prediction)
    except PredictionError:
        prediction_as_result_refused = True

    # A prediction with no null / no power is refused at birth.
    null_refused = False
    try:
        RegisteredPrediction(
            prediction_id="NO_NULL", hypothesis="h",
            predicted_signature="s", quantities=example_quantities(),
            null_model="   ", decision_rule="d", analysis_plan="a",
            power_on_planted="p", fingerprint=EXAMPLE_FINGERPRINT)
    except PredictionError:
        null_refused = True
    power_refused = False
    try:
        RegisteredPrediction(
            prediction_id="NO_POWER", hypothesis="h",
            predicted_signature="s", quantities=example_quantities(),
            null_model="n", decision_rule="d", analysis_plan="a",
            power_on_planted="", fingerprint=EXAMPLE_FINGERPRINT)
    except PredictionError:
        power_refused = True

    # A sealed bundle on an R13 hash chain verifies.
    bundle = seal_bundle(prediction, epoch=20260724)
    bundle_verifies = verify_bundle(bundle)

    return {
        "what_this_is": (
            "a prospective prediction registry: a prediction (hypothesis, "
            "predicted quantities with tolerances, modes, frequencies, "
            "directions and null expectations, a null model, a decision "
            "rule, an analysis plan and proven power on planted data) is "
            "sealed with a timestamp and a SHA-256 commitment over the plan "
            "and a fingerprint of the model, code, data and parameters, "
            "before any run, so results cannot be retrofitted"),
        "example_prediction": prediction.as_dict(),
        "example_commitment": commitment,
        "seal_is_deterministic": commitment == seal(prediction),
        "registry_validation": registry_validation,
        "power_discipline_demo": _demo_power_check(),
        "unsealed_analysis_is_exploratory": unsealed_is_exploratory,
        "sealed_analysis_is_confirmatory": sealed_is_confirmatory,
        "result_without_prior_seal_refused": exploratory_refused,
        "edit_after_seal_refused": edit_refused,
        "prediction_is_stale_after_model_change": stale,
        "stale_prediction_refused": stale_refused,
        "prediction_as_result_refused": prediction_as_result_refused,
        "prediction_without_null_refused": null_refused,
        "prediction_without_power_refused": power_refused,
        "sealed_bundle_verifies": bundle_verifies,
        "refusals": [
            "refuse_prediction_without_null",
            "refuse_prediction_without_power",
            "refuse_result_without_prior_seal",
            "refuse_edit_after_seal",
            "refuse_stale_prediction",
            "refuse_prediction_as_result",
        ],
        "prediction_claim_class": PROSPECTIVE_PREDICTION,
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say the sealed prediction is true, and it does not "
            "say any run was performed. Sealing a prediction and fingerprint "
            "is a statement about the ORDER in which the plan and the data "
            "were fixed -- the plan first, hashed and committed against a "
            "known model; the data, if they ever exist, second. A seal "
            "establishes PROSPECTIVE_PREDICTION and nothing stronger: no "
            "measurement is performed here, no data are analysed, and no "
            "outcome is confirmed. Every prediction carries a null model and "
            "proven power because a null result is meaningless unless the "
            "design could have detected a real effect. The value of the seal "
            "is entirely negative -- it makes a retrofitted analysis "
            "detectable, an unsealed result exploratory, and a stale "
            "prediction refusable -- and that is all it claims. The "
            "strongest class here is MODEL_PREDICTION."),
    }


__all__ = [
    "VERDICT", "PHYSICAL_VALIDATION", "CLAIM_CLASS", "PROSPECTIVE_PREDICTION",
    "PREDICTION_EVIDENCE_LEVEL", "MEASUREMENT_CLAIM_CLASSES",
    "PredictionError",
    "PredictionMode", "Direction",
    "PredictedQuantity", "ArtifactFingerprint", "RegisteredPrediction",
    "LOADBEARING_FIELDS",
    "seal", "is_sealed", "classify_analysis",
    "is_stale", "staleness_report",
    "power_on_planted_check",
    "PredictionRegistry",
    "SealedBundle", "seal_bundle", "verify_bundle",
    "refuse_prediction_without_null", "refuse_prediction_without_power",
    "refuse_result_without_prior_seal", "refuse_edit_after_seal",
    "refuse_stale_prediction", "refuse_prediction_as_result",
    "EXAMPLE_MODEL", "EXAMPLE_CODE", "EXAMPLE_DATA", "EXAMPLE_PARAMS",
    "EXAMPLE_FINGERPRINT", "example_quantities", "EXAMPLE_PREDICTION",
    "example_seal", "predictions_report",
]
