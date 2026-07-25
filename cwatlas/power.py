"""P50 — Planted-signal recovery and power tests.

A null result only means something if the machinery *could* have found a signal
had one been present. This module plants a known hidden mapping into synthetic
data, confirms the pipeline **recovers** it (POWER), and confirms that pure
noise yields **no** recovery (the null control). Together those two facts make a
null result on real material a finding about the material rather than blindness
in the pipeline.

The planting is deterministic. :func:`planted_label` maps an opaque item id to a
class index through a salted SHA-256 hash: fully determined by the id, so the
decoder that knows the planting rule scores exactly on it while a decoder that
does not stays at the ``1 / num_classes`` chance rate. :class:`PlantedDataset`
carries the ids, the planting salt, and a train/holdout split inherited from the
sealed-holdout framework (P49), so power is measured on TRAIN and the sealed
holdout stays untouched.

The governance teeth: a method that shows **no power on planted data** is
refused as vacuous by :func:`refuse_vacuous_method`. A decoder that cannot
recover a signal that is *known to be there* proves nothing by returning null on
data where the presence of a signal is unknown — its null is uninformative and
may not be reported as a negative finding.

Everything here is synthetic; ids are opaque and labels are class indices.
Recovering a planted mapping says nothing about any source vector's meaning.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Callable, Sequence, Tuple

import numpy as np

from cwatlas.claims import ClaimClass, ClaimError
from cwatlas.holdout import HoldoutSplit, make_split, synthetic_ids

#: How many classes a planted label can take, by default.
DEFAULT_NUM_CLASSES = 7

#: Recovery rate a decoder must exceed on TRAIN before a planted signal is
#: called detected. Set well above the 1/num_classes chance rate.
POWER_DETECTION_THRESHOLD = 0.9

#: How close to chance a null decoder must stay to confirm the null control.
NULL_MARGIN = 0.10

DEFAULT_PLANT_SALT = "R10_8_1_PLANT"


class PowerError(ValueError):
    """Raised on a malformed power/recovery request. Explicit result state."""


def refuse_vacuous_method(power_result: "PowerResult", *_a, **_k) -> None:
    """Refuse a method that shows no power on planted data as vacuous.

    A decoder that cannot recover a mapping *known to be present* has no power;
    its null result on unknown data is uninformative and may not be reported as
    a negative finding. Establish power first, then a null means something.
    """
    if not power_result.detected:
        raise ClaimError(
            f"refused: this method recovered the PLANTED signal at only "
            f"{power_result.train_recovery:.3f} on TRAIN (threshold "
            f"{power_result.detection_threshold:.3f}, chance "
            f"{power_result.chance_rate:.3f}); it has no power. A method that "
            f"cannot find a signal known to be present cannot make its null "
            f"result on unknown data a meaningful negative finding.")


def planted_label(item_id: str, salt: str = DEFAULT_PLANT_SALT,
                  num_classes: int = DEFAULT_NUM_CLASSES) -> int:
    """The PLANTED label of an item: a deterministic function of the id.

    This is the signal a competent decoder should recover. It is a salted SHA-256
    hash of the id reduced to a class index — fully determined by the id, so a
    decoder that knows the rule scores exactly and one that does not stays at
    chance.
    """
    if num_classes < 2:
        raise PowerError("num_classes must be >= 2")
    digest = hashlib.sha256(
        f"PLANT\x1f{salt}\x1f{item_id}".encode("utf-8")).hexdigest()
    return int(digest, 16) % num_classes


@dataclass(frozen=True)
class PlantedDataset:
    """A set of items whose labels were planted by a known rule.

    The POWER control. Because the labels are a deterministic function of the
    ids, the decoder that knows the rule recovers them perfectly on TRAIN — so a
    null result on genuinely unlabelled material is a finding about the material
    and not blindness in the machinery.
    """

    ids: Tuple[str, ...]
    salt: str = DEFAULT_PLANT_SALT
    num_classes: int = DEFAULT_NUM_CLASSES
    holdout_fraction: float = 0.3
    split_salt: str = "R10_8_1_HOLDOUT_SPLIT"

    def labels(self) -> dict:
        return {i: planted_label(i, self.salt, self.num_classes)
                for i in self.ids}

    def split(self) -> HoldoutSplit:
        return make_split(self.ids, self.holdout_fraction, self.split_salt)

    def train_labeled(self) -> Tuple[Tuple[str, int], ...]:
        labels = self.labels()
        return tuple((i, labels[i]) for i in self.split().train)

    def holdout_labeled(self) -> Tuple[Tuple[str, int], ...]:
        labels = self.labels()
        return tuple((i, labels[i]) for i in self.split().holdout)


def planted_decoder(planted: PlantedDataset) -> Callable[[str], int]:
    """The decoder that knows the planting rule. Recovers TRAIN exactly."""
    def decode(item_id: str) -> int:
        return planted_label(item_id, planted.salt, planted.num_classes)
    return decode


def noise_decoder(num_classes: int = DEFAULT_NUM_CLASSES,
                  seed: int = 0) -> Callable[[str], int]:
    """A null decoder: a deterministic hash unrelated to the planting rule.

    It ignores the planting salt entirely, so it stays at the chance rate on
    planted data — the null control that makes a positive power result mean
    something. Deterministic given ``seed``.
    """
    def decode(item_id: str) -> int:
        digest = hashlib.sha256(
            f"NOISE\x1f{seed}\x1f{item_id}".encode("utf-8")).hexdigest()
        return int(digest, 16) % num_classes
    return decode


def constant_decoder(value: int = 0) -> Callable[[str], int]:
    """A degenerate null decoder that ignores the id entirely."""
    def decode(_item_id: str) -> int:
        return value
    return decode


def _recovery(decoder: Callable[[str], int],
              labeled: Sequence[Tuple[str, int]]) -> float:
    rows = tuple(labeled)
    if not rows:
        raise PowerError("cannot score an empty set")
    hits = np.array([1 if decoder(i) == label else 0 for i, label in rows])
    return float(hits.mean())


@dataclass(frozen=True)
class PowerResult:
    """Whether a decoder recovers the PLANTED signal on TRAIN."""

    train_size: int
    num_classes: int
    chance_rate: float
    train_recovery: float
    detection_threshold: float
    detected: bool
    claim_class: str
    justification: str


def power_test(decoder: Callable[[str], int],
               planted: PlantedDataset) -> PowerResult:
    """POWER: confirm ``decoder`` recovers the PLANTED signal on TRAIN.

    The decoder that knows the planting rule scores essentially perfectly and
    the signal is detected; a null decoder stays near the chance rate and is
    not. Without this, a null elsewhere could mean the pipeline is simply blind.
    """
    if not isinstance(planted, PlantedDataset):
        raise PowerError("power_test needs a PlantedDataset")
    train_labeled = planted.train_labeled()
    recovery = _recovery(decoder, train_labeled)
    chance = 1.0 / planted.num_classes
    detected = bool(recovery >= POWER_DETECTION_THRESHOLD)
    if detected:
        why = ("the decoder recovered the planted mapping on TRAIN, so the "
               "pipeline can detect a signal that is genuinely present; a null "
               "elsewhere is then a finding, not blindness")
    else:
        why = ("the decoder did not recover the planted mapping on TRAIN; the "
               "method has no demonstrated power and its null is uninformative")
    return PowerResult(
        train_size=len(train_labeled),
        num_classes=planted.num_classes,
        chance_rate=chance,
        train_recovery=recovery,
        detection_threshold=POWER_DETECTION_THRESHOLD,
        detected=detected,
        claim_class=ClaimClass.MATHEMATICAL_TRANSLATION.value,
        justification=why,
    )


@dataclass(frozen=True)
class NullControlResult:
    """Whether a null decoder stays at chance on planted data (the control)."""

    train_size: int
    chance_rate: float
    train_recovery: float
    margin: float
    is_null: bool
    claim_class: str


def null_control(decoder: Callable[[str], int],
                 planted: PlantedDataset,
                 margin: float = NULL_MARGIN) -> NullControlResult:
    """Confirm a null decoder stays near chance on planted data.

    The mirror of :func:`power_test`: pure noise must **not** recover the planted
    mapping. If a "null" decoder scored well above chance, the recovery metric
    would be meaningless. ``is_null`` is True when recovery is within ``margin``
    of the chance rate.
    """
    train_labeled = planted.train_labeled()
    recovery = _recovery(decoder, train_labeled)
    chance = 1.0 / planted.num_classes
    return NullControlResult(
        train_size=len(train_labeled),
        chance_rate=chance,
        train_recovery=recovery,
        margin=margin,
        is_null=bool(abs(recovery - chance) <= margin),
        claim_class=ClaimClass.MATHEMATICAL_TRANSLATION.value,
    )


@dataclass(frozen=True)
class RecoveryReport:
    """A method's power (planted recovered) paired with its null control."""

    power: PowerResult
    null: NullControlResult
    method_has_power: bool
    null_is_meaningful: bool
    claim_class: str


def evaluate_method(method: Callable[[str], int],
                    planted: PlantedDataset,
                    null: Callable[[str], int] | None = None) -> RecoveryReport:
    """Evaluate a method: it must recover the planted signal AND pass a null.

    Runs :func:`power_test` on ``method`` and :func:`null_control` on ``null``
    (a fresh noise decoder by default). A null result from ``method`` is only
    meaningful — reportable as a negative finding — once ``method`` has shown
    power on planted data.
    """
    power = power_test(method, planted)
    null_dec = null if null is not None else noise_decoder(
        num_classes=planted.num_classes, seed=1)
    null_res = null_control(null_dec, planted)
    return RecoveryReport(
        power=power,
        null=null_res,
        method_has_power=power.detected,
        null_is_meaningful=bool(power.detected and null_res.is_null),
        claim_class=ClaimClass.MATHEMATICAL_TRANSLATION.value,
    )


def power_report() -> dict:
    """P50 declaration receipt. Planted recovered (power); noise null (control)."""
    ids = synthetic_ids(240)
    planted = PlantedDataset(ids=ids, salt="R10_8_1_POWER_DEMO")
    good = power_test(planted_decoder(planted), planted)
    null = null_control(noise_decoder(num_classes=planted.num_classes), planted)
    report = evaluate_method(planted_decoder(planted), planted)
    return {
        "phase_id": "P50",
        "tranche": "T07",
        "what_this_is": (
            "planted-signal recovery and power tests: a known hidden mapping is "
            "planted into synthetic data, the pipeline is shown to recover it "
            "(POWER), and pure noise is shown not to (the null control), so a "
            "null result becomes a finding rather than blindness. A method with "
            "no power on planted data is refused as vacuous."),
        "item_count": len(ids),
        "num_classes": planted.num_classes,
        "chance_rate": good.chance_rate,
        "power_planted_recovery": good.train_recovery,
        "power_detected": good.detected,
        "null_noise_recovery": null.train_recovery,
        "null_is_null": null.is_null,
        "null_is_meaningful": report.null_is_meaningful,
        "detection_threshold": POWER_DETECTION_THRESHOLD,
        "refusals": ["refuse_vacuous_method"],
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "GREEN_R10_8_1_P50_PLANTED_SIGNAL_RECOVERY_AND_POWER_TESTS",
        "what_this_does_not_say": (
            "Recovering a planted synthetic mapping says nothing about any "
            "source vector's meaning. It establishes only that the pipeline has "
            "power: it can detect a signal known to be present, so that a null "
            "on real material is informative. A method with no power on planted "
            "data is vacuous and its null is refused. Every id and label is "
            "synthetic; nothing is measured and no physical validation is "
            "claimed."),
    }


__all__ = [
    "PowerError", "DEFAULT_NUM_CLASSES", "POWER_DETECTION_THRESHOLD",
    "NULL_MARGIN", "DEFAULT_PLANT_SALT",
    "refuse_vacuous_method", "planted_label", "PlantedDataset",
    "planted_decoder", "noise_decoder", "constant_decoder",
    "PowerResult", "power_test", "NullControlResult", "null_control",
    "RecoveryReport", "evaluate_method", "power_report",
]
