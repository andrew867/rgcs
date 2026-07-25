"""P22 — the circularity and leakage audit: refuse to call a circular
result confirmatory.

A number can look like a discovery and be nothing but the question asked
back to itself. This module is the audit that catches that: it examines an
analysis *pipeline* -- an ordered list of steps that split data, engineer
features, fit a model and score it -- and flags the steps whose result was
already contained in their own inputs. A pipeline that scores itself on
data it was tuned on has *measured nothing new*; the audit says so before
the score is ever offered as evidence.

Five kinds of circularity are each their own detector, and each returns
whether the pipeline is circular by that mechanism:

* **train/test leakage** -- a holdout id, or a feature derived from the
  labels, crosses into training. The holdout score is then a training
  score wearing the holdout's clothes. This detector reuses the R13
  decoder-holdout authority (:func:`r13.holdout.refuse_holdout_in_training`)
  rather than re-deriving the disjointness rule.
* **double-dipping** -- features, ROIs or thresholds are *selected* on the
  very same data later used to test them. The selection has already peeked
  at the answer, so the test is not independent of it.
* **target leakage** -- a predictor is a proxy for the label: a column that
  is a deterministic function of (or was computed from) the target. A model
  that reads the answer off an input is not predicting.
* **preprocessing-before-split** -- normalization, imputation, scaling or
  feature selection is *fit* on the full dataset before the train/test
  split, so the test fold's statistics have already informed the transform
  the model sees.
* **temporal leakage** -- a step uses information from the future to inform
  the past: a test timestamp precedes a train timestamp, or a
  forward-looking window feeds a backward prediction.

:func:`audit_pipeline` runs every detector over a list of
:class:`PipelineStep` records and returns a :class:`PipelineAudit` listing
the circular steps and the leak kinds found. **POWER:** a pipeline with a
planted leak of each kind is caught by that kind's detector; a clean
split-before-fit pipeline passes every detector. And
:func:`refuse_circular_result_as_confirmatory` raises whenever a circular
result is offered as confirmation of a hypothesis -- a result that contains
its own inputs confirms nothing.

Everything here is synthetic and abstract: ids are opaque strings, features
and labels are small integers, timestamps are integers. Nothing is
measured. ``measured_here`` is ``"nothing"`` and
``PHYSICAL_VALIDATION_NOT_CLAIMED``; the standing verdict is
``CIRCULARITY_AUDIT_NO_CIRCULAR_RESULT_IS_CONFIRMATORY``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13 import holdout as _holdout
from r13 import serialize as _serialize
from r15 import claims

# --- standing vocabulary -------------------------------------------------

#: The standing verdict for this module.
VERDICT = "CIRCULARITY_AUDIT_NO_CIRCULAR_RESULT_IS_CONFIRMATORY"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The class of the audit machinery itself. It types the pipeline it is
#: given; it operates no apparatus and measures nothing.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED

#: Bumped whenever the detection rules change; carried on every audit so a
#: rule change is versioned and auditable.
AUDIT_VERSION = "1.0.0"


class CircularityError(RuntimeError):
    """Raised on a malformed pipeline, an out-of-vocabulary step role, or a
    circular result offered as confirmatory."""


class LeakKind(Enum):
    """The five circularity/leakage mechanisms, each with its own detector."""

    TRAIN_TEST_LEAKAGE = "TRAIN_TEST_LEAKAGE"
    DOUBLE_DIPPING = "DOUBLE_DIPPING"
    TARGET_LEAKAGE = "TARGET_LEAKAGE"
    PREPROCESSING_BEFORE_SPLIT = "PREPROCESSING_BEFORE_SPLIT"
    TEMPORAL_LEAKAGE = "TEMPORAL_LEAKAGE"


class StepRole(Enum):
    """The role a pipeline step plays. The audit reasons about the ordering
    and the data-flow between roles, not about the numbers a step computes."""

    SPLIT = "SPLIT"                    # partition items into train / test
    PREPROCESS = "PREPROCESS"          # normalize / impute / scale
    SELECT_FEATURES = "SELECT_FEATURES"  # choose features / ROIs / thresholds
    FIT = "FIT"                        # fit / train the model
    PREDICT = "PREDICT"                # produce predictions
    SCORE = "SCORE"                    # score predictions against labels


#: The roles that constitute *fitting* on data -- a transform or model whose
#: parameters are estimated from whatever fold it is handed.
FITTING_ROLES: frozenset = frozenset({
    StepRole.PREPROCESS,
    StepRole.SELECT_FEATURES,
    StepRole.FIT,
})

#: The fold a step operates on. ``FULL`` means the step saw every item
#: before any split -- the anti-pattern for a fitting step.
class Fold(Enum):
    FULL = "FULL"        # the whole dataset, before any split
    TRAIN = "TRAIN"      # the training fold only
    TEST = "TEST"        # the held-out test fold only


# --- the pipeline step ---------------------------------------------------

@dataclass(frozen=True)
class PipelineStep:
    """One step in an analysis pipeline, as the audit sees it.

    A step has a ``role`` (:class:`StepRole`), the ``fold`` it operated on,
    the item ids it touched (``item_ids``), the feature names it read
    (``features``), and -- for a fitting or selecting step -- the ordinal
    ``position`` it holds in the pipeline. ``derived_from_labels`` marks a
    feature step whose feature was computed from the target; ``selected_on``
    marks which fold a selection peeked at; ``timestamps`` maps item ids to
    an integer time, so temporal ordering can be checked. None of these
    carry a physical quantity -- they are opaque bookkeeping."""

    name: str
    role: StepRole
    fold: Fold = Fold.TRAIN
    item_ids: tuple = ()
    features: tuple = ()
    derived_from_labels: tuple = ()
    selected_on: Fold | None = None
    timestamps: tuple = ()   # ((item_id, int_time), ...)

    def __post_init__(self) -> None:
        if not str(self.name).strip():
            raise CircularityError("a pipeline step needs a name")
        if not isinstance(self.role, StepRole):
            raise CircularityError(
                f"step {self.name!r}: role must be a StepRole, got "
                f"{self.role!r}")
        if not isinstance(self.fold, Fold):
            raise CircularityError(
                f"step {self.name!r}: fold must be a Fold, got {self.fold!r}")
        object.__setattr__(self, "item_ids", tuple(self.item_ids))
        object.__setattr__(self, "features", tuple(self.features))
        object.__setattr__(self, "derived_from_labels",
                           tuple(self.derived_from_labels))
        object.__setattr__(self, "timestamps", tuple(self.timestamps))

    def timestamp_map(self) -> dict:
        return {str(i): int(t) for i, t in self.timestamps}

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "role": self.role.value,
            "fold": self.fold.value,
            "item_ids": list(self.item_ids),
            "features": list(self.features),
            "derived_from_labels": list(self.derived_from_labels),
            "selected_on": None if self.selected_on is None
            else self.selected_on.value,
            "timestamps": [[str(i), int(t)] for i, t in self.timestamps],
        }


# --- one detector's finding ----------------------------------------------

@dataclass(frozen=True)
class LeakFinding:
    """One detector's verdict for a pipeline.

    ``circular`` is ``True`` when that detector found its leak kind;
    ``steps`` names the offending steps; ``detail`` explains why."""

    kind: LeakKind
    circular: bool
    steps: tuple
    detail: str

    def as_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "circular": bool(self.circular),
            "steps": list(self.steps),
            "detail": self.detail,
        }


# --- the five detectors --------------------------------------------------

def detect_train_test_leakage(steps) -> LeakFinding:
    """(1) A holdout id, or a label-derived feature, crossed into training.

    Two ways a test fold contaminates training: a TEST item id also appears
    among the TRAIN items (the same specimen graded and trained on), or a
    FIT/PREPROCESS step on the TRAIN fold reads a feature that was derived
    from the labels. The id-overlap check reuses the R13 holdout authority's
    disjointness rule so there is one truth system for "holdout leaked into
    training"."""
    steps = tuple(steps)
    train_ids: set = set()
    test_ids: set = set()
    for s in steps:
        if s.fold is Fold.TRAIN:
            train_ids |= set(s.item_ids)
        elif s.fold is Fold.TEST:
            test_ids |= set(s.item_ids)

    offenders: list = []
    detail_parts: list = []

    # id overlap, adjudicated by the R13 holdout authority
    leaked_ids = sorted(train_ids & test_ids)
    if leaked_ids:
        try:
            _holdout.refuse_holdout_in_training(
                sorted(train_ids), sorted(test_ids))
        except _holdout.HoldoutError as exc:
            detail_parts.append(str(exc))
        offenders.extend(s.name for s in steps
                         if s.fold is Fold.TRAIN
                         and set(s.item_ids) & test_ids)

    # a label-derived feature entering a training-side fitting step
    for s in steps:
        if s.role in FITTING_ROLES and s.fold is not Fold.TEST \
                and s.derived_from_labels:
            offenders.append(s.name)
            detail_parts.append(
                f"step {s.name!r} fits on features derived from the labels "
                f"{list(s.derived_from_labels)}: the target has leaked into "
                f"training")

    offenders = sorted(set(offenders))
    if offenders:
        return LeakFinding(
            LeakKind.TRAIN_TEST_LEAKAGE, True, tuple(offenders),
            "; ".join(detail_parts))
    return LeakFinding(
        LeakKind.TRAIN_TEST_LEAKAGE, False, (),
        "train and test folds are disjoint and no label-derived feature "
        "enters training")


def detect_double_dipping(steps) -> LeakFinding:
    """(2) Features/ROIs/thresholds selected on the same data used to test.

    A SELECT_FEATURES step whose ``selected_on`` fold is FULL or TEST has
    already peeked at the material it will later be graded on: the selection
    is not independent of the test. Selecting on TRAIN only is clean."""
    steps = tuple(steps)
    offenders: list = []
    for s in steps:
        if s.role is StepRole.SELECT_FEATURES and s.selected_on in (
                Fold.FULL, Fold.TEST):
            offenders.append(s.name)
    if offenders:
        return LeakFinding(
            LeakKind.DOUBLE_DIPPING, True, tuple(sorted(offenders)),
            "feature/ROI selection peeked at the test (or full) data it is "
            "later scored on; the selection is not independent of the test, "
            f"offending steps {sorted(offenders)}")
    return LeakFinding(
        LeakKind.DOUBLE_DIPPING, False, (),
        "feature/ROI selection is confined to the training fold")


def detect_target_leakage(steps, target_features=()) -> LeakFinding:
    """(3) A predictor is a proxy for the label.

    ``target_features`` names columns that are the target itself, or a
    deterministic function of it. A FIT or PREDICT step that reads any of
    them is reading the answer off its input, not predicting it. Also fires
    when a step's ``derived_from_labels`` names a feature it fits on."""
    steps = tuple(steps)
    target = set(str(f) for f in target_features)
    offenders: list = []
    detail_parts: list = []
    for s in steps:
        if s.role in (StepRole.FIT, StepRole.PREDICT):
            proxies = sorted(target & set(s.features))
            if proxies:
                offenders.append(s.name)
                detail_parts.append(
                    f"step {s.name!r} uses predictor(s) {proxies} that are a "
                    f"proxy for the label")
            if s.derived_from_labels:
                offenders.append(s.name)
                detail_parts.append(
                    f"step {s.name!r} uses feature(s) "
                    f"{list(s.derived_from_labels)} computed from the target")
    offenders = sorted(set(offenders))
    if offenders:
        return LeakFinding(
            LeakKind.TARGET_LEAKAGE, True, tuple(offenders),
            "; ".join(detail_parts))
    return LeakFinding(
        LeakKind.TARGET_LEAKAGE, False, (),
        "no predictor is a proxy for or derived from the label")


def detect_preprocessing_before_split(steps) -> LeakFinding:
    """(4) Normalization/imputation fit on the full set before the split.

    A PREPROCESS (or SELECT_FEATURES) step that fits on the FULL fold, or
    that sits *before* the SPLIT step in the pipeline order, has let the test
    fold's statistics inform the transform the model later sees. A transform
    fit strictly after the split, on the train fold only, is clean."""
    steps = tuple(steps)
    split_positions = [i for i, s in enumerate(steps)
                       if s.role is StepRole.SPLIT]
    first_split = split_positions[0] if split_positions else None
    offenders: list = []
    detail_parts: list = []
    for i, s in enumerate(steps):
        if s.role not in (StepRole.PREPROCESS, StepRole.SELECT_FEATURES):
            continue
        if s.fold is Fold.FULL:
            offenders.append(s.name)
            detail_parts.append(
                f"step {s.name!r} is fit on the FULL dataset")
        elif first_split is not None and i < first_split:
            offenders.append(s.name)
            detail_parts.append(
                f"step {s.name!r} runs before the split at position "
                f"{first_split}")
        elif first_split is None:
            offenders.append(s.name)
            detail_parts.append(
                f"step {s.name!r} fits but the pipeline has no split step")
    offenders = sorted(set(offenders))
    if offenders:
        return LeakFinding(
            LeakKind.PREPROCESSING_BEFORE_SPLIT, True, tuple(offenders),
            "preprocessing/selection was fit on the full set or before the "
            "split, so test-fold statistics informed the transform; "
            + "; ".join(detail_parts))
    return LeakFinding(
        LeakKind.PREPROCESSING_BEFORE_SPLIT, False, (),
        "every preprocessing/selection step is fit after the split on the "
        "training fold only")


def detect_temporal_leakage(steps) -> LeakFinding:
    """(5) Future information informs the past.

    Using the timestamps carried on the TRAIN and TEST folds, the audit
    checks that training does not include items that occur at or after the
    earliest test item: if any training timestamp is >= the earliest test
    timestamp, the model was fit on data from the test period's future
    relative to a forward-prediction task."""
    steps = tuple(steps)
    train_times: list = []
    test_times: list = []
    for s in steps:
        tmap = s.timestamp_map()
        if not tmap:
            continue
        if s.fold is Fold.TRAIN:
            train_times.extend(tmap.values())
        elif s.fold is Fold.TEST:
            test_times.extend(tmap.values())
    if not train_times or not test_times:
        return LeakFinding(
            LeakKind.TEMPORAL_LEAKAGE, False, (),
            "no train/test timestamps to compare; temporal ordering not "
            "asserted")
    earliest_test = min(test_times)
    latest_train = max(train_times)
    if latest_train >= earliest_test:
        offenders = sorted(s.name for s in steps
                          if s.fold is Fold.TRAIN and any(
                              t >= earliest_test
                              for t in s.timestamp_map().values()))
        return LeakFinding(
            LeakKind.TEMPORAL_LEAKAGE, True, tuple(offenders),
            f"a training item at time {latest_train} is at or after the "
            f"earliest test item at time {earliest_test}: the past was "
            f"informed by the future")
    return LeakFinding(
        LeakKind.TEMPORAL_LEAKAGE, False, (),
        f"every training item (latest {latest_train}) precedes the earliest "
        f"test item ({earliest_test}); time order is respected")


#: The five detectors, indexed by their leak kind, for the red team.
DETECTORS = {
    LeakKind.TRAIN_TEST_LEAKAGE: detect_train_test_leakage,
    LeakKind.DOUBLE_DIPPING: detect_double_dipping,
    LeakKind.TARGET_LEAKAGE: detect_target_leakage,
    LeakKind.PREPROCESSING_BEFORE_SPLIT: detect_preprocessing_before_split,
    LeakKind.TEMPORAL_LEAKAGE: detect_temporal_leakage,
}


# --- the pipeline audit --------------------------------------------------

@dataclass(frozen=True)
class PipelineAudit:
    """The verdict for a whole pipeline: which steps are circular, and how.

    ``circular`` is ``True`` if any detector fired. ``findings`` is the full
    per-kind breakdown; ``circular_steps`` is the union of offending step
    names; ``leak_kinds`` names the kinds found. ``content_hash`` is a
    deterministic fingerprint of the audit (via the R13 serialize
    authority), so the same pipeline always audits to the same digest."""

    circular: bool
    findings: tuple
    circular_steps: tuple
    leak_kinds: tuple
    reopening_test: str
    content_hash: str
    audit_version: str = AUDIT_VERSION

    def as_dict(self) -> dict:
        return {
            "circular": bool(self.circular),
            "findings": [f.as_dict() for f in self.findings],
            "circular_steps": list(self.circular_steps),
            "leak_kinds": list(self.leak_kinds),
            "reopening_test": self.reopening_test,
            "content_hash": self.content_hash,
            "audit_version": self.audit_version,
            "evidence_if_circular": (
                "a circular result is NOT confirmatory; the analysis "
                "measured nothing new"),
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
            "verdict": VERDICT,
        }


_REOPENING_TEST = (
    "Reopen the audit if any pipeline step changes fold, selection fold, "
    "label-derivation, or timestamp ordering: re-run every detector. A "
    "pipeline flagged circular is reopened to CLEAN only when the offending "
    "step is re-run on a strictly disjoint, split-before-fit, "
    "label-blind, time-ordered fold, and no result from a circular pipeline "
    "may be offered as confirmatory until then.")


def audit_pipeline(steps, target_features=()) -> PipelineAudit:
    """Run every detector over a pipeline and return the combined audit.

    Deterministic and pure: the same steps always yield the same audit
    (byte-identical content hash). A pipeline flagged circular has, in at
    least one detector, produced a result already contained in its inputs;
    a clean split-before-fit pipeline passes every detector."""
    steps = tuple(steps)
    if not steps:
        raise CircularityError("cannot audit an empty pipeline")
    for s in steps:
        if not isinstance(s, PipelineStep):
            raise CircularityError(f"{s!r} is not a PipelineStep")

    findings = (
        detect_train_test_leakage(steps),
        detect_double_dipping(steps),
        detect_target_leakage(steps, target_features),
        detect_preprocessing_before_split(steps),
        detect_temporal_leakage(steps),
    )
    circular_steps = sorted({name for f in findings if f.circular
                            for name in f.steps})
    leak_kinds = [f.kind.value for f in findings if f.circular]
    circular = bool(leak_kinds)
    body = {
        "steps": [s.as_dict() for s in steps],
        "target_features": sorted(str(f) for f in target_features),
        "findings": [f.as_dict() for f in findings],
        "audit_version": AUDIT_VERSION,
    }
    return PipelineAudit(
        circular=circular,
        findings=findings,
        circular_steps=tuple(circular_steps),
        leak_kinds=tuple(leak_kinds),
        reopening_test=_REOPENING_TEST,
        content_hash=_serialize.content_hash(body),
    )


# --- synthetic pipelines: the POWER controls -----------------------------

def clean_pipeline() -> tuple:
    """A clean split-before-fit pipeline: passes every detector.

    Train and test folds are disjoint; the split precedes every fitting
    step; preprocessing and selection are fit on the train fold only; no
    predictor is a label proxy; and every training item precedes every test
    item in time. This is the negative control the detectors must pass."""
    train_ids = tuple(f"ITEM_{i:04d}" for i in range(0, 60))
    test_ids = tuple(f"ITEM_{i:04d}" for i in range(60, 80))
    train_ts = tuple((i, t) for t, i in enumerate(train_ids))
    test_ts = tuple((i, 100 + t) for t, i in enumerate(test_ids))
    return (
        PipelineStep("split", StepRole.SPLIT, Fold.FULL,
                     item_ids=train_ids + test_ids),
        PipelineStep("normalize", StepRole.PREPROCESS, Fold.TRAIN,
                     item_ids=train_ids, features=("x0", "x1")),
        PipelineStep("select", StepRole.SELECT_FEATURES, Fold.TRAIN,
                     item_ids=train_ids, features=("x0", "x1"),
                     selected_on=Fold.TRAIN),
        PipelineStep("fit", StepRole.FIT, Fold.TRAIN,
                     item_ids=train_ids, features=("x0", "x1"),
                     timestamps=train_ts),
        PipelineStep("predict", StepRole.PREDICT, Fold.TEST,
                     item_ids=test_ids, features=("x0", "x1"),
                     timestamps=test_ts),
        PipelineStep("score", StepRole.SCORE, Fold.TEST, item_ids=test_ids),
    )


def planted_leak_pipeline(kind: LeakKind) -> tuple:
    """A clean pipeline with exactly ONE planted leak of ``kind``.

    Each planted leak is the minimal edit to :func:`clean_pipeline` that
    trips exactly the named detector: an overlapping id (train/test
    leakage), a selection on the full set (double-dipping), a label-proxy
    predictor (target leakage), a full-set normalizer (preprocessing before
    split), or a training item timestamped into the test period (temporal
    leakage). The POWER control: each planted leak must be caught by its
    detector."""
    if not isinstance(kind, LeakKind):
        raise CircularityError(f"{kind!r} is not a LeakKind")
    steps = list(clean_pipeline())

    if kind is LeakKind.TRAIN_TEST_LEAKAGE:
        # a test id leaks into the training fold
        leaked = steps[3]  # the fit step, on TRAIN
        steps[3] = PipelineStep(
            leaked.name, leaked.role, leaked.fold,
            item_ids=leaked.item_ids + ("ITEM_0065",),
            features=leaked.features, timestamps=leaked.timestamps)
        return tuple(steps)

    if kind is LeakKind.DOUBLE_DIPPING:
        sel = steps[2]
        steps[2] = PipelineStep(
            sel.name, sel.role, sel.fold, item_ids=sel.item_ids,
            features=sel.features, selected_on=Fold.FULL)
        return tuple(steps)

    if kind is LeakKind.TARGET_LEAKAGE:
        fit = steps[3]
        steps[3] = PipelineStep(
            fit.name, fit.role, fit.fold, item_ids=fit.item_ids,
            features=fit.features + ("label_proxy",),
            timestamps=fit.timestamps)
        # the leaking column is declared a target feature at audit time
        return tuple(steps)

    if kind is LeakKind.PREPROCESSING_BEFORE_SPLIT:
        norm = steps[1]
        steps[1] = PipelineStep(
            norm.name, norm.role, Fold.FULL, item_ids=norm.item_ids,
            features=norm.features)
        return tuple(steps)

    if kind is LeakKind.TEMPORAL_LEAKAGE:
        fit = steps[3]
        # retag one training item with a timestamp inside the test period
        bad_ts = fit.timestamps[:-1] + ((fit.timestamps[-1][0], 150),)
        steps[3] = PipelineStep(
            fit.name, fit.role, fit.fold, item_ids=fit.item_ids,
            features=fit.features, timestamps=bad_ts)
        return tuple(steps)

    raise CircularityError(f"no planted leak for {kind!r}")  # pragma: no cover


#: The target-feature list that makes the TARGET_LEAKAGE plant fire.
PLANTED_TARGET_FEATURES = ("label_proxy",)


# --- the load-bearing refusal --------------------------------------------

def refuse_circular_result_as_confirmatory(audit,
                                           hypothesis: str = "") -> None:
    """Refuse to offer a circular result as confirmation of a hypothesis.

    A result produced by a circular pipeline already contained its own
    inputs: the holdout was trained on, the features were selected on the
    test data, a predictor was the label in disguise, the transform saw the
    test fold, or the past was told the future. Such a result confirms
    nothing -- it is the question asked back to itself. If ``audit`` is
    circular this always raises; a clean audit passes silently."""
    circular = getattr(audit, "circular", None)
    kinds = getattr(audit, "leak_kinds", ())
    steps = getattr(audit, "circular_steps", ())
    if circular is None:
        circular = bool(kinds)
    if circular:
        raise CircularityError(
            f"refused: a circular result cannot confirm"
            + (f" the hypothesis {hypothesis!r}" if hypothesis else "")
            + f". The pipeline is circular by {list(kinds)} at step(s) "
            f"{list(steps)}: the result already contained its own inputs "
            f"(trained on the holdout, selected on the test fold, read a "
            f"label proxy, preprocessed before the split, or let the future "
            f"inform the past). A result that contains the answer it claims "
            f"to find measures nothing new and is not confirmatory. "
            + VERDICT + ".")


#: Reused from the governance core: there is no PHRYLL_DETECTED state, and a
#: model result is never a physical measurement.
refuse_phryll_detected = claims.refuse_phryll_detected
refuse_model_as_measurement = claims.refuse_model_as_measurement


#: The refusals this module enforces, indexed for the red team.
CIRCULARITY_REFUSALS = {
    "circular_result_as_confirmatory": refuse_circular_result_as_confirmatory,
    "model_as_measurement": refuse_model_as_measurement,
    "phryll_detected": refuse_phryll_detected,
}


# --- report --------------------------------------------------------------

def circularity_report() -> dict:
    """The standing statement of what the audit is and is not."""
    clean = audit_pipeline(clean_pipeline())
    planted = {
        kind.value: audit_pipeline(
            planted_leak_pipeline(kind),
            target_features=PLANTED_TARGET_FEATURES).circular
        for kind in LeakKind
    }
    return {
        "what_this_is": (
            "the R15 circularity and leakage audit: five detectors -- "
            "train/test leakage, double-dipping, target leakage, "
            "preprocessing-before-split, and temporal leakage -- each "
            "flagging whether an analysis pipeline is circular by that "
            "mechanism, plus audit_pipeline() which runs them all and "
            "refuse_circular_result_as_confirmatory() which refuses to offer "
            "a circular result as confirmation"),
        "leak_kinds": [k.value for k in LeakKind],
        "detectors": [k.value for k in DETECTORS],
        "clean_pipeline_is_circular": clean.circular,
        "planted_leak_caught_by_kind": planted,
        "all_planted_leaks_caught": all(planted.values()),
        "audit_version": AUDIT_VERSION,
        "refusals": list(CIRCULARITY_REFUSALS),
        "reuses": [
            "r13.holdout.refuse_holdout_in_training (disjointness authority)",
            "r13.serialize.content_hash (deterministic audit fingerprint)",
            "r15.claims (claim taxonomy and forbidden promotions)",
        ],
        "has_phryll_detected_state": False,
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "rules": [
            "a holdout id or a label-derived feature crossing into training "
            "is train/test leakage",
            "selecting features/ROIs on the same data used to test is "
            "double-dipping",
            "a predictor that is a proxy for the label is target leakage",
            "fitting normalization/imputation before the split is "
            "preprocessing-before-split leakage",
            "using future information to inform the past is temporal leakage",
            "a circular result is never confirmatory and measures nothing new",
        ],
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any pipeline's non-circular result is true, "
            "replicated, or physically measured -- only that the result was "
            "not already contained in its own inputs. The audit operates no "
            "apparatus and measures nothing; it types the pipeline it is "
            "given. A clean audit is a necessary, not sufficient, condition "
            "for a result to count as evidence, and a circular result is "
            "refused as confirmatory outright. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION",
    "SOFTWARE_CLAIM_CLASS", "AUDIT_VERSION",
    "CircularityError", "LeakKind", "StepRole", "Fold", "FITTING_ROLES",
    "PipelineStep", "LeakFinding",
    "detect_train_test_leakage", "detect_double_dipping",
    "detect_target_leakage", "detect_preprocessing_before_split",
    "detect_temporal_leakage", "DETECTORS",
    "PipelineAudit", "audit_pipeline",
    "clean_pipeline", "planted_leak_pipeline", "PLANTED_TARGET_FEATURES",
    "refuse_circular_result_as_confirmatory", "refuse_model_as_measurement",
    "refuse_phryll_detected", "CIRCULARITY_REFUSALS", "circularity_report",
]
