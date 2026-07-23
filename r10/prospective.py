"""P18 — prospective evidence and paper-trading harness.

Everything else in this tranche is retrospective: it looks at a session
that already happened and asks whether its numbers, signals, and claims
survive a null. Retrospective analysis can only ever *fail* to find
something; it can never *confirm*, because the analyst already knows the
data. Confirmation requires a **prospective** prediction: frozen before
the outcome exists, scored against the outcome when it arrives, with the
failures kept.

This module is the registry for that. A prediction is registered with a
hash and a freeze time; its outcome can only be recorded *after* the
freeze; and a failed prediction can never be deleted -- deleting failures
is how a chance process is dressed up as a signal. It covers every kind
of holdout the pack asks for (signal, EMI, root, memory, sky, and
paper-market) through one typed mechanism.

**The financial firewall.** Investment-oriented source notes are private
hypotheses only. The single permitted validation is **blinded paper
trading**: ``paper_only`` is fixed True, real-money execution raises, and
the hypothesis must carry a frozen entry rule, exit rule, benchmark,
cost model, drawdown limit, horizon, and multiplicity correction before
any outcome is seen. No personalized advice, no trade is ever placed.

Nothing here is measured, and no outcome is available in this
environment: every registered holdout defaults to ``AWAITING_OUTCOME``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum


class ProspectiveError(RuntimeError):
    """Raised on a look-ahead, a deleted failure, or a real-money attempt."""


class Domain(Enum):
    SIGNAL = "signal"
    EMI = "emi"
    ROOT = "root"
    MEMORY = "memory"
    SKY = "sky"
    PAPER_MARKET = "paper_market"


class Outcome(Enum):
    AWAITING_OUTCOME = "AWAITING_OUTCOME"
    CONFIRMED = "CONFIRMED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class Prediction:
    """A prospective prediction, frozen before its outcome exists."""

    prediction_id: str
    domain: Domain
    statement: str                       # what will happen, specifically
    freeze_time: float                   # monotonic seconds; frozen at t0
    horizon_s: float                     # window in which it must resolve
    success_criterion: str               # how it will be scored
    multiplicity: int = 1                # how many predictions in the family

    def __post_init__(self) -> None:
        if self.horizon_s <= 0:
            raise ProspectiveError("horizon must be positive")
        if self.multiplicity < 1:
            raise ProspectiveError("multiplicity must be >= 1")

    @property
    def prereg_hash(self) -> str:
        parts = (self.prediction_id, self.domain.value, self.statement,
                 f"{self.freeze_time:.6f}", f"{self.horizon_s:.6f}",
                 self.success_criterion, str(self.multiplicity))
        return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()


@dataclass(frozen=True)
class PaperHypothesis:
    """A blinded paper-trading hypothesis. paper_only is fixed True."""

    hypothesis_id: str
    source_time: float
    asset_basket: tuple[str, ...]
    entry_rule: str
    exit_rule: str
    benchmark: str
    horizon_s: float
    cost_model: str
    drawdown_limit: float
    multiplicity: int = 1
    paper_only: bool = True

    def __post_init__(self) -> None:
        if not self.paper_only:
            raise ProspectiveError(
                "paper_only cannot be False; validation is blinded paper "
                "trading only, never real money")
        for name, val in (("entry_rule", self.entry_rule),
                          ("exit_rule", self.exit_rule),
                          ("benchmark", self.benchmark),
                          ("cost_model", self.cost_model)):
            if not val:
                raise ProspectiveError(
                    f"{name} must be frozen before any outcome is scored")
        if not self.asset_basket:
            raise ProspectiveError("asset_basket must be non-empty")


class HoldoutRegistry:
    """Append-only registry: outcomes only after freeze, failures kept."""

    def __init__(self) -> None:
        self._preds: dict[str, Prediction] = {}
        self._outcomes: dict[str, Outcome] = {}

    def register(self, pred: Prediction) -> str:
        if pred.prediction_id in self._preds:
            raise ProspectiveError("prediction_id already registered")
        self._preds[pred.prediction_id] = pred
        self._outcomes[pred.prediction_id] = Outcome.AWAITING_OUTCOME
        return pred.prereg_hash

    def record_outcome(self, prediction_id: str, outcome: Outcome,
                       observed_time: float) -> None:
        if prediction_id not in self._preds:
            raise ProspectiveError("unknown prediction")
        pred = self._preds[prediction_id]
        if observed_time < pred.freeze_time:
            raise ProspectiveError(
                "look-ahead: outcome time precedes the freeze time; an "
                "outcome may only be recorded after the prediction is "
                "frozen")
        self._outcomes[prediction_id] = outcome

    def refuse_delete_failure(self, prediction_id: str) -> None:
        raise ProspectiveError(
            "refused: a failed prediction is never deleted. Retaining "
            "failures is what keeps a prospective record honest; deleting "
            "them manufactures a signal from chance.")

    def outcome(self, prediction_id: str) -> Outcome:
        return self._outcomes[prediction_id]

    def scoreboard(self) -> dict:
        vals = list(self._outcomes.values())
        return {
            "total": len(vals),
            "awaiting": sum(v is Outcome.AWAITING_OUTCOME for v in vals),
            "confirmed": sum(v is Outcome.CONFIRMED for v in vals),
            "failed": sum(v is Outcome.FAILED for v in vals),
            "inconclusive": sum(v is Outcome.INCONCLUSIVE for v in vals),
            "note": ("failed predictions are retained and counted; a "
                     "confirmed count is meaningful only after multiplicity "
                     "correction across the whole family"),
        }


def multiplicity_adjusted_alpha(alpha: float, n: int) -> float:
    """Bonferroni-adjusted threshold for a family of n predictions."""
    if n < 1:
        raise ProspectiveError("n must be >= 1")
    return alpha / n


def refuse_real_money(*_args, **_kwargs) -> None:
    """Refuse any real-money execution or personalized trade instruction."""
    raise ProspectiveError(
        "refused: no real-money automation and no personalized trade "
        "instruction. Source investment notes are validated only by "
        "blinded paper trading with frozen rules and retained failures.")


def prospective_report() -> dict:
    return {
        "what_this_is": (
            "a preregistration registry for prospective predictions "
            "across signal, EMI, root, memory, sky, and paper-market "
            "holdouts, plus a paper-only financial harness"),
        "domains": [d.value for d in Domain],
        "rules": [
            "a prediction is frozen with a hash before its outcome exists",
            "an outcome may only be recorded after the freeze time",
            "failed predictions are retained, never deleted",
            "paper trading only: no real money, no personalized advice",
            "multiplicity is corrected across the prediction family",
        ],
        "evidence_class": "PROSPECTIVE_PREDICTION (none resolved here)",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "AWAITING_OUTCOME",
        "what_this_does_not_say": (
            "It does not report a confirmed prediction, does not place a "
            "trade, and does not give financial advice. Every holdout "
            "here is awaiting an outcome that this environment cannot "
            "produce, and a retrospective analysis is never promoted to a "
            "prospective confirmation."),
    }
