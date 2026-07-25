"""P49 — No-look-ahead and sealed-holdout framework.

A retrospective decoder search is worthless unless the answer it will be scored
on is *frozen before the decoder is chosen*. This module supplies the machinery
that makes that discipline checkable rather than promised, in the CW Atlas
idiom, and it is the T07 statistics-and-evidence spine that P50–P52 build on.

The protocol has one direction of time:

1. **Split deterministically.** :func:`make_split` partitions opaque item ids
   into TRAIN and HOLDOUT by a salted SHA-256 hash of the id. The same ids and
   salt always produce the same split, the two parts are disjoint and cover
   every id, and the holdout fraction comes out approximately as requested — so
   nobody chose *which* items would be held out after seeing which split
   flattered a transform.

2. **Seal the holdout before any transform selection.** :func:`seal_holdout`
   returns a SHA-256 commitment over the holdout ids **and** their geographic
   labels. Sealing binds each id to its label, so revealing a different holdout,
   or the same holdout with one label altered, fails to match while the true
   holdout matches. Sealing *before* transform selection is System Contract
   **invariant 5** made mechanical: geographic labels and known destinations
   remain sealed while the transform is chosen.

3. **Score once, against the committed labels only.**
   :meth:`SealedHoldout.score_once` verifies the labels handed to it against
   the seal, refuses any set that does not match, scores the decoder, and then
   *locks* — a second scoring attempt is refused so the holdout cannot be
   re-graded until a happier number appears.

The three no-look-ahead guards:

* :func:`refuse_decode_before_seal` — a decode/score attempted before the seal
  is refused, because a decoder run first can be nudged until it fits and then
  sealed as though it predated the answer;
* :func:`refuse_holdout_in_training` — a holdout item leaked into training is
  refused, because a holdout score computed on data the transform already saw
  is a training score wearing the holdout's clothes;
* :func:`refuse_multiple_scoring` — scoring the sealed holdout more than once is
  refused, because "best of many looks" is not a single held-out result.

Everything here is synthetic and abstract: ids are opaque strings and labels
are small class indices, so nothing names or implies any real quantity. A
retrospective fit never becomes a decoded destination.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Callable, Iterable, Sequence, Tuple

import numpy as np

from cwatlas.claims import ClaimClass, ClaimError

#: Resolution of the hashed split. The band of the hash below
#: ``fraction * _SPLIT_RESOLUTION`` is assigned to the holdout.
_SPLIT_RESOLUTION = 1 << 32

#: Default salts. Passed in for anything that must vary; never wall-clock.
DEFAULT_SPLIT_SALT = "R10_8_1_HOLDOUT_SPLIT"
DEFAULT_SEAL_SALT = "R10_8_1_HOLDOUT_SEAL"


class HoldoutError(ValueError):
    """Raised on a malformed split, a leaked holdout item, a label set that
    does not match the seal, a decode before the seal, or a second scoring.

    An explicit result state, never a silent guess.
    """


class SealError(ClaimError):
    """Raised when the no-look-ahead ordering is violated (invariant 5).

    Extends :class:`~cwatlas.claims.ClaimError`: sealing the holdout before
    transform selection is a governance rule, not just an input check.
    """


# --------------------------------------------------------------------------- #
# The deterministic split
# --------------------------------------------------------------------------- #

def _split_score(item_id: str, salt: str) -> int:
    """A deterministic value in ``[0, _SPLIT_RESOLUTION)`` for an id + salt."""
    digest = hashlib.sha256(f"{salt}\x1f{item_id}".encode("utf-8")).hexdigest()
    return int(digest, 16) % _SPLIT_RESOLUTION


@dataclass(frozen=True)
class HoldoutSplit:
    """A reproducible TRAIN / HOLDOUT partition of a set of item ids.

    The split is a function of the ids and the salt alone, so it is
    deterministic and cannot be cherry-picked after a transform has been
    tried. The two parts are disjoint and their union is the full set of
    (deduplicated) ids.
    """

    train: Tuple[str, ...]
    holdout: Tuple[str, ...]
    salt: str
    holdout_fraction: float

    def all_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(set(self.train) | set(self.holdout)))

    def is_disjoint(self) -> bool:
        return not (set(self.train) & set(self.holdout))

    def covers(self, item_ids: Iterable[str]) -> bool:
        return set(self.all_ids()) == set(str(i) for i in item_ids)

    def actual_holdout_fraction(self) -> float:
        n = len(self.train) + len(self.holdout)
        return len(self.holdout) / n if n else 0.0


def make_split(item_ids: Iterable[str],
               holdout_fraction: float = 0.3,
               salt: str = DEFAULT_SPLIT_SALT) -> HoldoutSplit:
    """Partition ``item_ids`` into TRAIN and HOLDOUT by a salted hash.

    An id joins the holdout iff its hashed score falls in the low
    ``holdout_fraction`` band of the resolution. Deterministic: the same ids
    and salt give the same split every time, so the holdout is fixed before any
    transform is chosen and no split can be selected to suit a result.
    """
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
    if not holdout or not train:
        raise HoldoutError(
            "degenerate split: one side is empty at this fraction/salt; "
            "choose a different fraction or provide more items")
    return HoldoutSplit(tuple(train), tuple(holdout), salt, holdout_fraction)


def refuse_holdout_in_training(train: Iterable[str],
                               holdout: Iterable[str],
                               *_a, **_k) -> None:
    """Refuse a training set that contains any holdout item.

    A single leaked item turns the holdout score into a training score in
    disguise: the transform has already seen the answer it is about to be graded
    on. The leak is often innocent — an id in both lists, a merge that lost the
    partition — and it is fatal to the evidence regardless of intent.
    """
    leaked = sorted(set(str(i) for i in train) & set(str(i) for i in holdout))
    if leaked:
        raise HoldoutError(
            f"refused: {len(leaked)} holdout item(s) are present in the "
            f"training set ({', '.join(leaked[:8])}"
            f"{' ...' if len(leaked) > 8 else ''}). A holdout item seen during "
            f"training makes its holdout score a training score in disguise; "
            f"the holdout must be strictly disjoint from training for its score "
            f"to mean anything.")


# --------------------------------------------------------------------------- #
# Sealing: commit ids + geographic labels before transform selection
# --------------------------------------------------------------------------- #

def _canonical_holdout(holdout_labeled: Iterable[Tuple[str, int]]) -> str:
    """The canonical string a holdout seal is taken over.

    Sorted by id so the seal is independent of ordering, and it binds each id to
    its label, so relabelling any item breaks the seal.
    """
    rows = sorted((str(i), int(label)) for i, label in holdout_labeled)
    if not rows:
        raise HoldoutError("cannot seal an empty holdout")
    return ";".join(f"{i}={label}" for i, label in rows)


def seal_holdout(holdout_labeled: Iterable[Tuple[str, int]],
                 salt: str = DEFAULT_SEAL_SALT) -> str:
    """Seal a labelled holdout under a SHA-256 commitment (invariant 5).

    Call this BEFORE any transform is selected. The seal binds every holdout id
    to its geographic label, so a later reveal of a different holdout — or the
    same holdout with one label changed — will not match it, while the true
    holdout will.
    """
    payload = f"{salt}\x1f{_canonical_holdout(holdout_labeled)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def verify_seal(holdout_labeled: Iterable[Tuple[str, int]],
                seal: str,
                salt: str = DEFAULT_SEAL_SALT) -> bool:
    """True iff ``holdout_labeled`` reproduces ``seal`` under ``salt``."""
    return seal_holdout(holdout_labeled, salt) == seal


def refuse_decode_before_seal(holdout: "SealedHoldout", *_a, **_k) -> None:
    """Refuse a decode/score attempted before the holdout was sealed.

    A decoder run before the seal can be nudged — a field flipped, a tolerance
    widened — until the answer fits, and the seal taken afterwards then records a
    transform that was already tuned. The seal has to come first.
    """
    if not getattr(holdout, "sealed", False):
        raise SealError(
            "refused: a decode/score was attempted before the holdout was "
            "sealed. The labelled holdout must be sealed with seal_holdout() "
            "BEFORE any transform is selected or scored (invariant 5); a "
            "transform chosen first can be adjusted until it fits and then "
            "sealed as though it had predated the answer.")


def refuse_multiple_scoring(holdout: "SealedHoldout", *_a, **_k) -> None:
    """Refuse a second scoring of the same sealed holdout.

    A holdout scored once is a held-out result; a holdout scored repeatedly
    until one look is favourable is a training result again. Score once.
    """
    if getattr(holdout, "scored", False):
        raise HoldoutError(
            "refused: this sealed holdout has already been scored once. "
            "Scoring it again — trying transform after transform until one "
            "clears the bar — turns the held-out score back into a training "
            "score chosen for its result. The holdout is scored exactly once.")


@dataclass
class ScoreResult:
    """The single, sealed holdout score. Not a generalization guarantee."""

    holdout_size: int
    accuracy: float
    seal: str
    labels_match_seal: bool
    claim_class: str = ClaimClass.MATHEMATICAL_TRANSLATION.value


@dataclass
class SealedHoldout:
    """The no-look-ahead protocol state: split, then seal, then score once.

    Starts unsealed and unscored. :meth:`seal` fixes the commitment over the
    labelled holdout; only after that may a transform be scored, via
    :meth:`score_once`, which locks the holdout so it cannot be re-graded.
    """

    holdout_labeled: Tuple[Tuple[str, int], ...]
    salt: str = DEFAULT_SEAL_SALT
    seal: str | None = None
    scored: bool = False
    _score: ScoreResult | None = field(default=None, repr=False)

    @property
    def sealed(self) -> bool:
        return self.seal is not None

    def do_seal(self) -> str:
        """Seal the labelled holdout and record the commitment."""
        self.seal = seal_holdout(self.holdout_labeled, self.salt)
        return self.seal

    def score_once(self, decoder: Callable[[str], int]) -> ScoreResult:
        """Score ``decoder`` on the sealed holdout, using ONLY sealed labels.

        Refuses a decode before the seal, refuses a second scoring, and refuses
        labels that do not match the seal — so the holdout cannot be quietly
        relabelled, previewed, or re-graded.
        """
        refuse_decode_before_seal(self)
        refuse_multiple_scoring(self)
        assert self.seal is not None  # guaranteed by refuse_decode_before_seal
        if not verify_seal(self.holdout_labeled, self.seal, self.salt):
            raise HoldoutError(
                "refused: the holdout labels do not match the seal. Scoring "
                "uses only the sealed labels; a set that fails the seal has "
                "been altered since it was committed and cannot grade a "
                "transform.")
        rows = tuple(self.holdout_labeled)
        hits = np.array([1 if decoder(i) == label else 0 for i, label in rows])
        result = ScoreResult(
            holdout_size=len(rows),
            accuracy=float(hits.mean()) if len(rows) else 0.0,
            seal=self.seal,
            labels_match_seal=True,
        )
        self.scored = True
        self._score = result
        return result


def synthetic_ids(count: int, prefix: str = "ITEM") -> Tuple[str, ...]:
    """A deterministic set of opaque item ids. Not derived from anything real."""
    if count < 2:
        raise HoldoutError("need at least two items")
    width = max(4, len(str(count - 1)))
    return tuple(f"{prefix}_{i:0{width}d}" for i in range(count))


def holdout_report() -> dict:
    """P49 declaration receipt. Split, seal, score-once — no look-ahead."""
    ids = synthetic_ids(200)
    split = make_split(ids, holdout_fraction=0.3)
    # A synthetic labelling: label = deterministic hash class, sealed here.
    labels = {
        i: int(hashlib.sha256(f"LBL\x1f{i}".encode()).hexdigest(), 16) % 7
        for i in ids
    }
    holdout_labeled = tuple((i, labels[i]) for i in split.holdout)
    protocol = SealedHoldout(holdout_labeled)
    protocol.do_seal()
    tampered = ((holdout_labeled[0][0], (holdout_labeled[0][1] + 1) % 7),) \
        + tuple(holdout_labeled[1:])
    return {
        "phase_id": "P49",
        "tranche": "T07",
        "what_this_is": (
            "a no-look-ahead sealed-holdout framework: a deterministic salted-"
            "hash train/holdout split, a SHA-256 seal over holdout ids and "
            "geographic labels taken before transform selection (invariant 5), "
            "and a score-once discipline that grades against the sealed labels "
            "exactly once."),
        "item_count": len(ids),
        "holdout_fraction_requested": split.holdout_fraction,
        "holdout_fraction_actual": split.actual_holdout_fraction(),
        "split_is_disjoint": split.is_disjoint(),
        "split_covers_all_items": split.covers(ids),
        "seal": protocol.seal,
        "true_holdout_matches_seal": verify_seal(holdout_labeled, protocol.seal),
        "tampered_holdout_matches_seal": verify_seal(tampered, protocol.seal),
        "refusals": [
            "refuse_decode_before_seal",
            "refuse_holdout_in_training",
            "refuse_multiple_scoring",
        ],
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "GREEN_R10_8_1_P49_NO_LOOK_AHEAD_AND_SEALED_HOLDOUT_FRAMEWORK",
        "what_this_does_not_say": (
            "It does not say any transform generalized. It provides the "
            "blinding discipline under which such a claim could be tested: the "
            "split is a deterministic hash of the item ids, so the holdout is "
            "fixed before any transform runs; the holdout is sealed by a SHA-256 "
            "commitment over its ids and geographic labels, so a relabelled or "
            "substituted holdout fails to match while the true one matches; a "
            "holdout item leaked into training, a decode before the seal, or a "
            "second scoring is refused. Every id and label is synthetic; "
            "nothing is measured and no physical validation is claimed."),
    }


__all__ = [
    "HoldoutError", "SealError",
    "HoldoutSplit", "make_split", "refuse_holdout_in_training",
    "seal_holdout", "verify_seal", "refuse_decode_before_seal",
    "refuse_multiple_scoring", "ScoreResult", "SealedHoldout",
    "synthetic_ids", "holdout_report",
    "DEFAULT_SPLIT_SALT", "DEFAULT_SEAL_SALT",
]
