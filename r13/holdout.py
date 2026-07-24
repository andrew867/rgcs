"""P37b — the decoder holdout / blinding protocol: a train/holdout split
that stops a decoder from being tuned on the answer.

A decoder search is only worth anything if the decoder is written down
*before* it sees the labels it will be scored on. This module supplies
the machinery that makes that discipline checkable rather than promised.

**The split is deterministic, not cherry-picked.** :class:`HoldoutSplit`
partitions a set of item ids into TRAIN and HOLDOUT by a hash of the id
and a salt. The same items and salt always produce the same split, the
two parts are disjoint and together cover every item, and the holdout
fraction comes out approximately as requested -- so no one chose which
items would be held out after seeing which split flattered the decoder.

**The holdout is sealed before any decoding.** :func:`commit_holdout`
returns a SHA-256 commitment over the holdout ids and their labels. The
commitment is tamper-evident: revealing a different holdout, or the same
holdout with one label altered, fails to match, while the true holdout
matches. Committing before decoding is what makes a later holdout score
evidence rather than a story.

**No peeking, no decoding before the commit.**
:func:`refuse_holdout_in_training` raises if any holdout item has leaked
into the training set -- a leak turns a holdout score into a training
score wearing its clothes. :func:`refuse_decode_before_commit` raises if
a decode is attempted before the holdout has been committed, because a
decoder that runs before the seal can be adjusted until the seal would
have fit.

**Power on planted data, and only the committed labels count.**
:func:`power_check` shows a decoder recovering a PLANTED answer on TRAIN:
if the machinery could not detect a decoder that is genuinely present, a
null result on the holdout would mean nothing. And
:func:`score_holdout` scores only against the committed labels -- it
verifies the labels it is handed against the commitment first and refuses
any set that does not match, so the holdout cannot be quietly relabelled
after the fact.

**Train is not holdout.** :func:`refuse_overfit_as_generalization` raises
whenever perfect (or any) training performance is offered as
generalization. Fitting the training data is what a free decoder does
effortlessly; only the sealed holdout speaks to generalization.

Everything here is synthetic and abstract -- ids are opaque strings and
labels are small class indices -- so nothing in this module names or
implies any real quantity. The standing verdict is
**DECODER_HOLDOUT_PROTOCOL_BLINDED**.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

import numpy as np

# =======================================================================
# Claim classes and the standing verdict
# =======================================================================

CLAIM_EXACT_IDENTITY = "EXACT_IDENTITY"
CLAIM_ANALYTIC_MODEL = "ANALYTIC_MODEL"
CLAIM_REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
CLAIM_NUMERICAL_SIMULATION = "NUMERICAL_SIMULATION"
CLAIM_UNSUPPORTED = "UNSUPPORTED"
CLAIM_BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"

VERDICT = "DECODER_HOLDOUT_PROTOCOL_BLINDED"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Resolution of the hashed split. The fraction of a full-width hash below
#: ``fraction * _SPLIT_RESOLUTION`` is assigned to the holdout.
_SPLIT_RESOLUTION = 1 << 32

#: How many classes a planted label can take.
DEFAULT_NUM_CLASSES = 7

#: Hit rate a decoder must exceed on TRAIN before power_check calls the
#: planted signal detected. Set well above the 1/NUM_CLASSES chance rate.
POWER_DETECTION_THRESHOLD = 0.9


class HoldoutError(RuntimeError):
    """Raised on a holdout item that leaked into training, a decode
    attempted before the holdout was committed, a set of labels that does
    not match the sealed commitment, or an attempt to read training
    performance as generalization."""


# =======================================================================
# The deterministic split
# =======================================================================

def _split_score(item_id: str, salt: str) -> int:
    """A deterministic value in ``[0, _SPLIT_RESOLUTION)`` for an id."""
    digest = hashlib.sha256(f"{salt}\x1f{item_id}".encode()).hexdigest()
    return int(digest, 16) % _SPLIT_RESOLUTION


@dataclass(frozen=True)
class HoldoutSplit:
    """A reproducible TRAIN / HOLDOUT partition of a set of item ids.

    The split is a function of the ids and the salt alone, so it is
    deterministic and cannot be cherry-picked after a decoder has been
    tried. The two parts are disjoint and their union is the full set of
    (deduplicated) ids."""

    train: tuple
    holdout: tuple
    salt: str
    holdout_fraction: float

    def all_ids(self) -> tuple:
        return tuple(sorted(set(self.train) | set(self.holdout)))

    def is_disjoint(self) -> bool:
        return not (set(self.train) & set(self.holdout))

    def covers(self, item_ids) -> bool:
        return set(self.all_ids()) == set(item_ids)

    def actual_holdout_fraction(self) -> float:
        n = len(self.train) + len(self.holdout)
        return len(self.holdout) / n if n else 0.0


def make_split(item_ids, holdout_fraction: float = 0.3,
               salt: str = "R13_HOLDOUT_SALT") -> HoldoutSplit:
    """Partition ``item_ids`` into TRAIN and HOLDOUT by a hash of the id.

    An id joins the holdout iff its hashed score falls in the low
    ``holdout_fraction`` band of the resolution. Deterministic: same ids
    and salt give the same split every time, so the holdout is fixed
    before any decoder is run and no split can be selected to suit a
    result."""
    if not 0.0 < holdout_fraction < 1.0:
        raise HoldoutError("holdout_fraction must lie in (0, 1)")
    ids = sorted(set(str(i) for i in item_ids))
    if len(ids) < 2:
        raise HoldoutError("a split needs at least two distinct items")
    threshold = holdout_fraction * _SPLIT_RESOLUTION
    train, holdout = [], []
    for item_id in ids:
        if _split_score(item_id, salt) < threshold:
            holdout.append(item_id)
        else:
            train.append(item_id)
    return HoldoutSplit(tuple(train), tuple(holdout), salt, holdout_fraction)


def refuse_holdout_in_training(train, holdout, *_args, **_kwargs) -> None:
    """Refuse a training set that contains any holdout item.

    A single leaked item turns the holdout score into a training score in
    disguise: the decoder has already seen the answer it is about to be
    graded on. The leak is often innocent -- an id that appears in both
    lists, a merge that lost the partition -- and it is fatal to the
    evidence regardless of intent."""
    leaked = sorted(set(train) & set(holdout))
    if leaked:
        raise HoldoutError(
            f"refused: {len(leaked)} holdout item(s) are present in the "
            f"training set ({', '.join(leaked[:8])}"
            f"{' ...' if len(leaked) > 8 else ''}). A holdout item seen "
            f"during training makes its holdout score a training score in "
            f"disguise -- the decoder was graded on data it had already "
            f"been shown. The holdout must be strictly disjoint from "
            f"training for its score to mean anything.")


# =======================================================================
# Planted data and toy decoders
# =======================================================================

def synthetic_ids(count: int, prefix: str = "ITEM") -> tuple:
    """A deterministic set of opaque item ids. Not derived from anything."""
    if count < 2:
        raise HoldoutError("need at least two items")
    width = max(4, len(str(count - 1)))
    return tuple(f"{prefix}_{i:0{width}d}" for i in range(count))


def planted_label(item_id: str, salt: str,
                  num_classes: int = DEFAULT_NUM_CLASSES) -> int:
    """The PLANTED label of an item: a deterministic function of the id.

    This is the signal a competent decoder should recover. It is a hash
    of the id under a planting salt, reduced to a class index -- fully
    determined by the id, so a decoder that knows the rule scores exactly
    on it and a decoder that does not stays at chance."""
    digest = hashlib.sha256(f"PLANT\x1f{salt}\x1f{item_id}".encode()).hexdigest()
    return int(digest, 16) % num_classes


@dataclass(frozen=True)
class PlantedDataset:
    """A set of items whose labels were planted by a known rule.

    The POWER control. Because the labels are a deterministic function of
    the ids, the decoder that knows the rule recovers them perfectly on
    TRAIN -- so a null result on genuinely unlabelled material is a
    finding about the material and not blindness in the machinery."""

    ids: tuple
    salt: str
    holdout_fraction: float = 0.3
    num_classes: int = DEFAULT_NUM_CLASSES
    split_salt: str = "R13_HOLDOUT_SALT"

    def labels(self) -> dict:
        return {i: planted_label(i, self.salt, self.num_classes)
                for i in self.ids}

    def split(self) -> HoldoutSplit:
        return make_split(self.ids, self.holdout_fraction, self.split_salt)

    def holdout_labeled(self) -> tuple:
        labels = self.labels()
        return tuple((i, labels[i]) for i in self.split().holdout)

    def train_labeled(self) -> tuple:
        labels = self.labels()
        return tuple((i, labels[i]) for i in self.split().train)


def planted_decoder(planted: PlantedDataset):
    """The decoder that knows the planting rule. Recovers TRAIN exactly."""
    def decode(item_id: str) -> int:
        return planted_label(item_id, planted.salt, planted.num_classes)
    return decode


def constant_decoder(value: int = 0):
    """A null decoder that ignores the id. Stays at chance on planted data."""
    def decode(_item_id: str) -> int:
        return value
    return decode


def _accuracy(decoder, labeled) -> float:
    rows = tuple(labeled)
    if not rows:
        raise HoldoutError("cannot score an empty set")
    hits = np.array([1 if decoder(i) == label else 0 for i, label in rows])
    return float(hits.mean())


# =======================================================================
# Blinding: commit the holdout before any decoding
# =======================================================================

def _canonical_holdout(holdout_labeled) -> str:
    """The canonical string a holdout commitment is taken over.

    Sorted by id so the commitment is independent of ordering, and it
    binds each id to its label, so relabelling any item breaks the seal."""
    rows = sorted((str(i), int(label)) for i, label in holdout_labeled)
    return ";".join(f"{i}={label}" for i, label in rows)


def commit_holdout(holdout_labeled, salt: str = "R13_COMMIT_SALT") -> str:
    """Seal a labelled holdout under a SHA-256 commitment.

    Call this BEFORE any decoding. The commitment binds every holdout id
    to its label, so a later reveal of a different holdout -- or the same
    holdout with one label changed -- will not match it, while the true
    holdout will."""
    rows = tuple(holdout_labeled)
    if not rows:
        raise HoldoutError("cannot commit an empty holdout")
    payload = f"{salt}\x1f{_canonical_holdout(rows)}"
    return hashlib.sha256(payload.encode()).hexdigest()


def verify_commitment(holdout_labeled, commitment: str,
                      salt: str = "R13_COMMIT_SALT") -> bool:
    """True iff ``holdout_labeled`` reproduces ``commitment`` under ``salt``."""
    return commit_holdout(holdout_labeled, salt) == commitment


@dataclass
class HoldoutProtocol:
    """The state a blinded run passes through: split, then seal, then decode.

    A protocol starts uncommitted. :meth:`commit` seals the labelled
    holdout and records the commitment; only after that may a decode be
    scored against it. The ordering is the discipline, and
    :func:`refuse_decode_before_commit` enforces it."""

    holdout_labeled: tuple
    salt: str = "R13_COMMIT_SALT"
    commitment: str | None = None

    @property
    def committed(self) -> bool:
        return self.commitment is not None

    def commit(self) -> str:
        self.commitment = commit_holdout(self.holdout_labeled, self.salt)
        return self.commitment


def refuse_decode_before_commit(protocol, *_args, **_kwargs) -> None:
    """Refuse a decode attempted before the holdout was committed.

    Accepts a :class:`HoldoutProtocol` (or anything with a ``committed``
    flag / a ``commitment``). A decoder run before the seal can be nudged
    -- a field flipped, a tolerance widened -- until the answer fits, and
    then the commitment taken afterwards records a decoder that was
    already tuned. The seal has to come first."""
    committed = getattr(protocol, "committed", None)
    if committed is None:
        committed = bool(getattr(protocol, "commitment", None))
    if not committed:
        raise HoldoutError(
            "refused: a decode was attempted before the holdout was "
            "committed. The labelled holdout must be sealed with "
            "commit_holdout() BEFORE any decoder is run on it; a decoder "
            "run first can be adjusted until it fits and then sealed as "
            "though it had predated the answer. Commit the holdout, then "
            "decode.")


# =======================================================================
# Scoring: only the committed labels count
# =======================================================================

def score_holdout(decoder, holdout_labeled, commitment: str,
                  salt: str = "R13_COMMIT_SALT") -> dict:
    """Score a decoder on the holdout, using ONLY the committed labels.

    The labels handed in are verified against the commitment first; a set
    that does not match is refused, so the holdout cannot be quietly
    relabelled to a decoder's advantage after the seal. Only once the
    labels are shown to be the sealed ones is the decoder scored."""
    if not verify_commitment(holdout_labeled, commitment, salt):
        raise HoldoutError(
            "refused: the holdout labels handed to the scorer do not "
            "match the sealed commitment. Scoring uses only the committed "
            "labels; a label set that fails the commitment has been "
            "altered since the seal and cannot be used to grade a "
            "decoder.")
    accuracy = _accuracy(decoder, holdout_labeled)
    return {
        "holdout_size": len(tuple(holdout_labeled)),
        "accuracy": accuracy,
        "commitment": commitment,
        "labels_match_commitment": True,
        "claim_class": CLAIM_REPOSITORY_COMPUTATIONAL_RESULT,
    }


# =======================================================================
# Power: the decoder recovers a planted answer on TRAIN
# =======================================================================

def power_check(decoder, planted: PlantedDataset) -> dict:
    """POWER: confirm the decoder recovers the PLANTED answer on TRAIN.

    Scores the decoder on the TRAIN portion of a planted dataset. The
    decoder that knows the planting rule scores essentially perfectly and
    the signal is detected; a null decoder stays near the 1/num_classes
    chance rate and is not. Without this, a null on the holdout could
    mean the machinery is simply blind rather than that the material
    carries no decoder."""
    if not isinstance(planted, PlantedDataset):
        raise HoldoutError("power_check needs a PlantedDataset")
    train_labeled = planted.train_labeled()
    accuracy = _accuracy(decoder, train_labeled)
    chance = 1.0 / planted.num_classes
    return {
        "planting_salt": planted.salt,
        "train_size": len(train_labeled),
        "num_classes": planted.num_classes,
        "chance_rate": chance,
        "train_accuracy": accuracy,
        "detection_threshold": POWER_DETECTION_THRESHOLD,
        "detected": bool(accuracy >= POWER_DETECTION_THRESHOLD),
        "claim_class": CLAIM_REPOSITORY_COMPUTATIONAL_RESULT,
        "note": (
            "the decoder that knows the planting rule recovers the TRAIN "
            "labels, so the protocol can detect a decoder that is really "
            "present; a null elsewhere is then a finding, not blindness"),
    }


def refuse_overfit_as_generalization(train_score, holdout_score=None,
                                     *_args, **_kwargs) -> None:
    """Refuse to read training performance as generalization.

    A decoder with enough free choices fits its training data effortlessly
    -- perfect train accuracy is the expected behaviour of an
    unconstrained decoder, not evidence that it has learned anything that
    transfers. Only a score on the sealed, disjoint holdout speaks to
    generalization, and it must be earned there separately."""
    raise HoldoutError(
        f"refused: a training score ({train_score!r}) is not a "
        f"generalization result. A decoder free to choose its own fields "
        f"can match the training labels perfectly whether or not it has "
        f"captured any real structure, so training accuracy -- even 1.0 "
        f"-- certifies nothing about held-out items. Generalization is "
        f"measured ONLY on the sealed, disjoint holdout "
        f"(holdout score supplied: {holdout_score!r}); it cannot be "
        f"inferred from training performance.")


# =======================================================================
# The report
# =======================================================================

def holdout_report() -> dict:
    ids = synthetic_ids(240)
    planted = PlantedDataset(ids=ids, salt="R13_POWER_DEMO")
    split = planted.split()
    good = power_check(planted_decoder(planted), planted)
    null = power_check(constant_decoder(0), planted)
    holdout_labeled = planted.holdout_labeled()
    commitment = commit_holdout(holdout_labeled)
    tampered = ((holdout_labeled[0][0],
                 (holdout_labeled[0][1] + 1) % planted.num_classes),
                ) + tuple(holdout_labeled[1:])
    return {
        "what_this_is": (
            "a deterministic train/holdout split with a sealed holdout "
            "commitment, no-peeking enforcement, and a planted-data power "
            "check that makes a holdout null meaningful"),
        "item_count": len(ids),
        "holdout_fraction_requested": planted.holdout_fraction,
        "holdout_fraction_actual": split.actual_holdout_fraction(),
        "split_is_disjoint": split.is_disjoint(),
        "split_covers_all_items": split.covers(ids),
        "commitment": commitment,
        "true_holdout_matches_commitment":
            verify_commitment(holdout_labeled, commitment),
        "tampered_holdout_matches_commitment":
            verify_commitment(tampered, commitment),
        "power_planted_decoder_detected": good["detected"],
        "power_null_decoder_detected": null["detected"],
        "power_check": good,
        "refusals": [
            "refuse_holdout_in_training",
            "refuse_decode_before_commit",
            "refuse_overfit_as_generalization",
        ],
        "claim_class": CLAIM_REPOSITORY_COMPUTATIONAL_RESULT,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any decoder generalized. It provides the "
            "blinding discipline under which such a claim could be tested "
            "and never lets training stand in for it. The split is a "
            "deterministic hash of the item ids, so the holdout is fixed "
            "before any decoder runs and cannot be cherry-picked; the "
            "holdout is sealed by a SHA-256 commitment over its ids and "
            "labels, so a relabelled or substituted holdout fails to "
            "match while the true one matches; a holdout item that leaks "
            "into training, or a decode attempted before the seal, is "
            "refused; scoring uses only the committed labels; and the "
            "power check shows the machinery recovers a PLANTED answer on "
            "TRAIN, so a null elsewhere is a finding rather than "
            "blindness. Perfect training performance is never "
            "generalization (refuse_overfit_as_generalization). Every id "
            "and label here is synthetic; nothing is measured and no "
            "physical validation is claimed."),
    }


__all__ = [
    "HoldoutError", "VERDICT", "PHYSICAL_VALIDATION",
    "HoldoutSplit", "make_split", "refuse_holdout_in_training",
    "synthetic_ids", "planted_label", "PlantedDataset",
    "planted_decoder", "constant_decoder",
    "commit_holdout", "verify_commitment",
    "HoldoutProtocol", "refuse_decode_before_commit",
    "score_holdout", "power_check", "refuse_overfit_as_generalization",
    "holdout_report", "POWER_DETECTION_THRESHOLD", "DEFAULT_NUM_CLASSES",
    "CLAIM_EXACT_IDENTITY", "CLAIM_ANALYTIC_MODEL",
    "CLAIM_REPOSITORY_COMPUTATIONAL_RESULT", "CLAIM_NUMERICAL_SIMULATION",
    "CLAIM_UNSUPPORTED", "CLAIM_BLOCKED_MISSING_INPUT",
]
