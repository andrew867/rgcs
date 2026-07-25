"""P20 — the holdout dataset authority: sealed partitions, one-shot scoring,
and an access log that makes a holdout null result mean something.

A holdout is only a holdout for as long as it stays unseen. This module
turns that discipline into machinery: it partitions data into named
partitions, seals the HOLDOUT before any modeling, freezes the model
before the holdout is scored, and then lets the holdout be scored ONCE
(or a fixed number of times against a spent error budget) and never
against anything but the sealed labels.

**Named partitions, assigned deterministically.**
:func:`partition_dataset` splits a set of opaque item ids into five
partitions -- DEVELOPMENT, CALIBRATION, CONTROL, HOLDOUT, and
FUTURE_MEASUREMENT -- by a hash of the id and a salt. The assignment is a
function of the ids and salt alone, so it is reproducible, the partitions
are disjoint and cover every item, and no one chose after the fact which
items would be held out. Development data cannot later be *relabelled*
holdout: :func:`refuse_relabel_partition_as_holdout` refuses it, because
an item already used for development has been seen and is no longer blind.

**The holdout is sealed before any modeling.** :func:`seal_holdout`
returns a :class:`HoldoutManifest` carrying a SHA-256 commitment over the
holdout ids and their labels (reusing :func:`r13.holdout.commit_holdout`).
The seal is tamper-evident: a substituted holdout, or the same holdout
with one label altered, fails to match while the true holdout matches.
Both synthetic planted holdouts and externally supplied physical holdout
labels are supported (:class:`HoldoutSource`); this module measures
nothing either way.

**No peeking: freeze the model, then score once.** The legitimate order
is partition, seal the holdout, freeze the model, then score.
:func:`r13.holdout.refuse_decode_before_commit` refuses a score before the
holdout is sealed; :func:`refuse_score_before_model_frozen` refuses a
score before the model is frozen (a model still free to change can be
tuned until the holdout flatters it); and under the ONE_SHOT policy
:func:`refuse_multiple_holdout_scoring` refuses a second look, because a
re-used holdout is no longer a holdout. A SEQUENTIAL policy permits more
than one look but spends an :class:`AlphaBudget`; when the budget is
exhausted, further looks are refused.

**Every access is logged, and unauthorized access is refused.** The
authority records every access to the holdout. Reading the sealed labels
for TRAINING or MODEL_SELECTION is not an authorized purpose --
:func:`refuse_unauthorized_access` refuses it -- so the holdout cannot be
used to pick a model against its own labels. And a training score is never
generalization: :func:`r13.holdout.refuse_overfit_as_generalization`
refuses reading TRAIN performance as a holdout result.

**Power on planted data.** :func:`development_power_check` shows a
rule-aware model recovering a PLANTED signal on the DEVELOPMENT partition,
so a null on the sealed holdout is a finding about the data rather than
blindness in the machinery.

Everything here is synthetic and abstract -- ids are opaque strings and
labels are small class indices -- so nothing names or implies any real
quantity, and no physical measurement is performed. The strongest class
this module reaches is ``SOFTWARE_IMPLEMENTED``. The standing verdict is
``HOLDOUT_DATASET_AUTHORITY_SEALED``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13 import holdout as _holdout
from r13 import serialize as _serialize
from r15 import claims as _claims

# =======================================================================
# Standing verdict, claim class, and the evidence level this touches
# =======================================================================

#: The standing verdict for a well-formed sealed holdout authority.
VERDICT = "HOLDOUT_DATASET_AUTHORITY_SEALED"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The class this module produces from software alone: an implementation,
#: never a measurement.
CLAIM_CLASS = _claims.ClaimClass.SOFTWARE_IMPLEMENTED.value

#: The evidence a result on a sealed, blinded holdout can support. E6 in
#: the R15 ladder is "blinded holdout support" -- the protocol ceiling,
#: not a measurement claim.
HOLDOUT_EVIDENCE_LEVEL = _claims.EvidenceLevel.E6

#: Salts, declared not assumed. Reused across seal/verify so a manifest is
#: reproducible.
DEFAULT_PARTITION_SALT = "R15_P20_PARTITION_SALT"
DEFAULT_COMMIT_SALT = "R15_P20_HOLDOUT_COMMIT_SALT"
DEFAULT_PLANTING_SALT = "R15_P20_POWER_PLANT"

#: Reused directly from the R13 authority.
DEFAULT_NUM_CLASSES = _holdout.DEFAULT_NUM_CLASSES
POWER_DETECTION_THRESHOLD = _holdout.POWER_DETECTION_THRESHOLD

#: Resolution of the hashed partition assignment.
_PARTITION_RESOLUTION = 1 << 32


class HoldoutAuthorityError(RuntimeError):
    """Raised on a development item relabelled holdout, a score before the
    model is frozen, a second score of a one-shot holdout, an exhausted
    sequential budget, or an unauthorized access to the sealed holdout."""


# =======================================================================
# The named partitions
# =======================================================================

class Partition(Enum):
    """The named partitions of an experimental dataset.

    DEVELOPMENT is where models are built and tuned; CALIBRATION fixes
    nuisance parameters; CONTROL is a negative reference; HOLDOUT is the
    sealed set scored once at the end; FUTURE_MEASUREMENT is reserved for
    data not yet acquired. HOLDOUT is the only partition sealed by a
    commitment."""

    DEVELOPMENT = "DEVELOPMENT"
    CALIBRATION = "CALIBRATION"
    CONTROL = "CONTROL"
    HOLDOUT = "HOLDOUT"
    FUTURE_MEASUREMENT = "FUTURE_MEASUREMENT"


#: The fixed order the partition bands are laid out in. Deterministic so
#: the assignment is reproducible.
_PARTITION_ORDER = (
    Partition.DEVELOPMENT,
    Partition.CALIBRATION,
    Partition.CONTROL,
    Partition.HOLDOUT,
    Partition.FUTURE_MEASUREMENT,
)

#: Default fractions; must sum to 1.0.
DEFAULT_FRACTIONS = {
    Partition.DEVELOPMENT: 0.50,
    Partition.CALIBRATION: 0.15,
    Partition.CONTROL: 0.10,
    Partition.HOLDOUT: 0.20,
    Partition.FUTURE_MEASUREMENT: 0.05,
}


def _partition_score(item_id: str, salt: str) -> int:
    """A deterministic value in ``[0, _PARTITION_RESOLUTION)`` for an id."""
    digest = hashlib.sha256(f"{salt}\x1f{item_id}".encode()).hexdigest()
    return int(digest, 16) % _PARTITION_RESOLUTION


@dataclass(frozen=True)
class DatasetPartition:
    """A reproducible assignment of item ids to the named partitions.

    ``members`` is a sorted tuple of ``(partition_value, ids)`` pairs. The
    assignment is a function of the ids, the salt, and the fractions
    alone, so it is deterministic and cannot be cherry-picked after a
    model has been tried. The partitions are disjoint and their union is
    the full set of (deduplicated) ids."""

    members: tuple
    salt: str

    def _map(self) -> dict:
        return {name: ids for name, ids in self.members}

    def ids(self, partition: Partition) -> tuple:
        return self._map().get(partition.value, ())

    def holdout_ids(self) -> tuple:
        return self.ids(Partition.HOLDOUT)

    def development_ids(self) -> tuple:
        return self.ids(Partition.DEVELOPMENT)

    def all_ids(self) -> tuple:
        out: list = []
        for _, ids in self.members:
            out.extend(ids)
        return tuple(sorted(out))

    def is_disjoint(self) -> bool:
        seen: set = set()
        for _, ids in self.members:
            s = set(ids)
            if s & seen:
                return False
            seen |= s
        return True

    def covers(self, item_ids) -> bool:
        return set(self.all_ids()) == set(str(i) for i in item_ids)

    def actual_fraction(self, partition: Partition) -> float:
        n = len(self.all_ids())
        return len(self.ids(partition)) / n if n else 0.0


def partition_dataset(item_ids, fractions: dict | None = None,
                      salt: str = DEFAULT_PARTITION_SALT) -> DatasetPartition:
    """Partition ``item_ids`` into the five named partitions by a hash.

    An id lands in a partition iff its hashed score falls in that
    partition's cumulative band. Deterministic: the same ids, salt, and
    fractions give the same partition every time, so the holdout is fixed
    before any modeling and no partition can be selected to suit a result.
    """
    fractions = dict(fractions) if fractions is not None else dict(DEFAULT_FRACTIONS)
    if set(fractions) != set(Partition):
        raise HoldoutAuthorityError(
            "fractions must specify exactly the five named partitions")
    total = sum(fractions.values())
    if not abs(total - 1.0) < 1e-9:
        raise HoldoutAuthorityError(
            f"partition fractions must sum to 1.0 (got {total})")
    if any(f < 0 for f in fractions.values()):
        raise HoldoutAuthorityError("partition fractions must be non-negative")

    ids = sorted(set(str(i) for i in item_ids))
    if len(ids) < len(_PARTITION_ORDER):
        raise HoldoutAuthorityError(
            "a five-way partition needs at least five distinct items")

    # Cumulative thresholds over the resolution, in the fixed order.
    thresholds: list = []
    cum = 0.0
    for part in _PARTITION_ORDER:
        cum += fractions[part]
        thresholds.append((part, cum * _PARTITION_RESOLUTION))

    buckets: dict = {part.value: [] for part in _PARTITION_ORDER}
    for item_id in ids:
        score = _partition_score(item_id, salt)
        for part, thresh in thresholds:
            if score < thresh:
                buckets[part.value].append(item_id)
                break
        else:  # pragma: no cover - score < resolution always assigns
            buckets[_PARTITION_ORDER[-1].value].append(item_id)

    members = tuple((part.value, tuple(buckets[part.value]))
                    for part in _PARTITION_ORDER)
    return DatasetPartition(members=members, salt=salt)


# =======================================================================
# Labels and the sealed holdout manifest
# =======================================================================

class HoldoutSource(Enum):
    """Where a holdout's labels come from.

    SYNTHETIC_PLANTED labels are a deterministic function of the ids (the
    power control); EXTERNAL_PHYSICAL labels are supplied from outside this
    module. Neither is a physical measurement performed here -- an external
    label is opaque data to this authority."""

    SYNTHETIC_PLANTED = "SYNTHETIC_PLANTED"
    EXTERNAL_PHYSICAL = "EXTERNAL_PHYSICAL"


def planted_labels(ids, salt: str = DEFAULT_PLANTING_SALT,
                   num_classes: int = DEFAULT_NUM_CLASSES) -> tuple:
    """Labelled rows ``((id, planted_label), ...)`` for a set of ids.

    Reuses :func:`r13.holdout.planted_label`: each label is a hash of the
    id under a planting salt, so a rule-aware decoder recovers it exactly
    and a null decoder stays at chance."""
    return tuple((str(i), _holdout.planted_label(str(i), salt, num_classes))
                 for i in ids)


@dataclass(frozen=True)
class HoldoutManifest:
    """A sealed holdout: the labelled holdout, its commitment, and provenance.

    ``commitment`` is a SHA-256 over the holdout ids and labels
    (:func:`r13.holdout.commit_holdout`), taken BEFORE any modeling.
    ``epoch`` is passed in, never read from a clock, so the manifest is
    reproducible. Carrying the ``commitment`` attribute lets
    :func:`r13.holdout.refuse_decode_before_commit` treat a manifest as a
    committed protocol."""

    holdout_labeled: tuple
    commitment: str
    epoch: int
    commit_salt: str
    source: str

    @property
    def committed(self) -> bool:
        return bool(self.commitment)

    def size(self) -> int:
        return len(self.holdout_labeled)

    def verify(self, holdout_labeled) -> bool:
        """True iff ``holdout_labeled`` reproduces the sealed commitment."""
        return _holdout.verify_commitment(
            holdout_labeled, self.commitment, self.commit_salt)


def seal_holdout(holdout_labeled, epoch: int,
                 source: HoldoutSource = HoldoutSource.SYNTHETIC_PLANTED,
                 salt: str = DEFAULT_COMMIT_SALT) -> HoldoutManifest:
    """Seal a labelled holdout under a SHA-256 commitment at an epoch.

    Call this BEFORE any modeling. The commitment binds every holdout id
    to its label, so a later reveal of a different holdout -- or the same
    holdout with a changed label -- will not match, while the true holdout
    will. Reuses :func:`r13.holdout.commit_holdout` directly."""
    rows = tuple(holdout_labeled)
    commitment = _holdout.commit_holdout(rows, salt)
    return HoldoutManifest(holdout_labeled=rows, commitment=commitment,
                           epoch=int(epoch), commit_salt=salt,
                           source=source.value)


# =======================================================================
# Freezing the model before the holdout is scored
# =======================================================================

@dataclass(frozen=True)
class ModelFreeze:
    """A seal over a model description, taken at a passed-in epoch.

    ``model_hash`` is the canonical content hash of the model descriptor
    (:func:`r13.serialize.content_hash`); ``epoch`` is supplied by the
    caller. A frozen model is a fixed object a later holdout score cannot
    have steered."""

    model_hash: str
    epoch: int

    def matches(self, model) -> bool:
        return self.model_hash == _serialize.content_hash(model)


def freeze_model(model_descriptor, epoch: int) -> ModelFreeze:
    """Freeze a model descriptor under a content hash at an explicit epoch."""
    return ModelFreeze(model_hash=_serialize.content_hash(model_descriptor),
                       epoch=int(epoch))


# =======================================================================
# Access purposes, records, and the sequential error budget
# =======================================================================

class ScoringPolicy(Enum):
    """How many times the sealed holdout may be scored.

    ONE_SHOT permits exactly one score -- the strictest and the default;
    a re-used holdout is no longer a holdout. SEQUENTIAL permits more than
    one look but each spends an :class:`AlphaBudget`, and looks are refused
    once the budget is exhausted."""

    ONE_SHOT = "ONE_SHOT"
    SEQUENTIAL = "SEQUENTIAL"


class AccessPurpose(Enum):
    """Why the holdout is being accessed.

    SCORE (score the frozen model once/against budget) and AUDIT (verify
    the machinery, never tune against labels) are authorized. TRAINING and
    MODEL_SELECTION are NOT: reading the sealed labels to build or pick a
    model turns the holdout into training data."""

    SCORE = "SCORE"
    AUDIT = "AUDIT"
    TRAINING = "TRAINING"
    MODEL_SELECTION = "MODEL_SELECTION"


#: The only purposes for which the sealed holdout may be accessed.
AUTHORIZED_PURPOSES = frozenset({AccessPurpose.SCORE, AccessPurpose.AUDIT})


@dataclass(frozen=True)
class AccessRecord:
    """One logged access to the sealed holdout.

    Every access -- granted or refused -- is recorded: its purpose, the
    requester, a passed-in epoch, whether it was granted, and a note. The
    log is what makes "the holdout was scored once" checkable rather than
    asserted."""

    purpose: str
    requester: str
    epoch: int
    granted: bool
    note: str = ""


@dataclass(frozen=True)
class AlphaSpend:
    """One spend against a sequential error budget."""

    amount: float
    epoch: int
    label: str


@dataclass
class AlphaBudget:
    """A sequential error budget spent across holdout looks.

    A sequential analysis that looks at the holdout more than once inflates
    its false-positive rate unless each look spends part of a fixed error
    budget. ``total`` is the budget; :meth:`spend` reduces the remaining
    and refuses a spend that exceeds it. When the budget is exhausted,
    further looks are refused."""

    total: float
    spends: tuple = ()

    def __post_init__(self) -> None:
        if not 0.0 < self.total <= 1.0:
            raise HoldoutAuthorityError(
                "an error budget must lie in (0, 1]")

    @property
    def spent(self) -> float:
        return float(sum(s.amount for s in self.spends))

    @property
    def remaining(self) -> float:
        return self.total - self.spent

    def spend(self, amount: float, epoch: int, label: str) -> AlphaSpend:
        if amount <= 0:
            raise HoldoutAuthorityError("a spend must be positive")
        if amount > self.remaining + 1e-12:
            raise HoldoutAuthorityError(
                f"refused: a sequential look wants to spend {amount} of a "
                f"remaining error budget of {self.remaining}. The budget is "
                f"exhausted; a further look at the holdout would spend error "
                f"the analysis has not reserved, inflating the "
                f"false-positive rate. No budget, no look.")
        s = AlphaSpend(amount=float(amount), epoch=int(epoch), label=label)
        self.spends = self.spends + (s,)
        return s


# =======================================================================
# The authority: seal, freeze, score once, log every access
# =======================================================================

@dataclass
class HoldoutAuthority:
    """The state a sealed-holdout run passes through: seal, freeze, score.

    Holds the sealed :class:`HoldoutManifest`, the scoring policy, the
    model freeze, an access log, and (for SEQUENTIAL) an error budget. A
    score requires the holdout committed, the model frozen, the presented
    labels matching the seal, and the policy satisfied; every access is
    recorded."""

    manifest: HoldoutManifest
    policy: ScoringPolicy = ScoringPolicy.ONE_SHOT
    model_freeze: ModelFreeze | None = None
    budget: AlphaBudget | None = None
    accesses: tuple = ()
    scored_count: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.manifest, HoldoutManifest):
            raise HoldoutAuthorityError("authority needs a HoldoutManifest")
        if self.policy is ScoringPolicy.SEQUENTIAL and self.budget is None:
            raise HoldoutAuthorityError(
                "a SEQUENTIAL policy needs an AlphaBudget to spend")

    # -- freezing the model ----------------------------------------------

    def freeze(self, model_descriptor, epoch: int) -> ModelFreeze:
        """Freeze the model; scoring becomes possible only after this."""
        self.model_freeze = freeze_model(model_descriptor, epoch)
        return self.model_freeze

    @property
    def model_is_frozen(self) -> bool:
        return self.model_freeze is not None

    # -- the access log --------------------------------------------------

    def _log(self, purpose: AccessPurpose, requester: str, epoch: int,
             granted: bool, note: str) -> AccessRecord:
        rec = AccessRecord(purpose=purpose.value, requester=requester,
                           epoch=int(epoch), granted=granted, note=note)
        self.accesses = self.accesses + (rec,)
        return rec

    def request_access(self, purpose: AccessPurpose, requester: str,
                       epoch: int) -> AccessRecord:
        """Request access to the sealed holdout for a stated purpose.

        Every request is logged. An unauthorized purpose (TRAINING or
        MODEL_SELECTION) is recorded as refused and then raised -- the
        holdout cannot be read to build or pick a model against its own
        labels."""
        authorized = purpose in AUTHORIZED_PURPOSES
        self._log(purpose, requester, epoch, granted=authorized,
                  note="access request")
        if not authorized:
            refuse_unauthorized_access(purpose)
        return self.accesses[-1]

    # -- scoring the holdout ---------------------------------------------

    def score(self, decoder, holdout_labeled, requester: str, epoch: int,
              alpha_spend: float | None = None) -> dict:
        """Score a frozen model on the sealed holdout, using only the
        committed labels.

        Gates, in order: the holdout must be committed
        (:func:`r13.holdout.refuse_decode_before_commit`); the model must
        be frozen (:func:`refuse_score_before_model_frozen`); the presented
        labels must match the seal (enforced by
        :func:`r13.holdout.score_holdout`); and the policy must permit the
        look -- ONE_SHOT refuses a second score
        (:func:`refuse_multiple_holdout_scoring`), SEQUENTIAL spends the
        error budget. Every score attempt is logged."""
        self._log(AccessPurpose.SCORE, requester, epoch, granted=True,
                  note=f"score attempt #{self.scored_count + 1}")

        _holdout.refuse_decode_before_commit(self.manifest)
        refuse_score_before_model_frozen(self)

        if self.policy is ScoringPolicy.ONE_SHOT and self.scored_count >= 1:
            refuse_multiple_holdout_scoring(self.scored_count)

        spend = None
        if self.policy is ScoringPolicy.SEQUENTIAL:
            if alpha_spend is None:
                raise HoldoutAuthorityError(
                    "a SEQUENTIAL score must declare an alpha_spend against "
                    "the error budget")
            spend = self.budget.spend(alpha_spend, epoch,
                                      f"look-{self.scored_count + 1}")

        result = _holdout.score_holdout(
            decoder, holdout_labeled, self.manifest.commitment,
            self.manifest.commit_salt)
        self.scored_count += 1

        return {
            **result,
            "policy": self.policy.value,
            "score_index": self.scored_count,
            "evidence_level": HOLDOUT_EVIDENCE_LEVEL.name,
            "alpha_spent": None if spend is None else spend.amount,
            "budget_remaining": (None if self.budget is None
                                 else self.budget.remaining),
            "claim_class": CLAIM_CLASS,
        }


# =======================================================================
# Power: a rule-aware model recovers a planted signal on DEVELOPMENT
# =======================================================================

def _accuracy(decoder, labeled) -> float:
    rows = tuple(labeled)
    if not rows:
        raise HoldoutAuthorityError("cannot score an empty set")
    hits = np.array([1 if decoder(i) == label else 0 for i, label in rows])
    return float(hits.mean())


def development_power_check(partition: DatasetPartition, decoder,
                           planting_salt: str = DEFAULT_PLANTING_SALT,
                           num_classes: int = DEFAULT_NUM_CLASSES,
                           threshold: float = POWER_DETECTION_THRESHOLD
                           ) -> dict:
    """POWER: confirm the decoder recovers a PLANTED signal on DEVELOPMENT.

    Plants a deterministic label on every development item and scores the
    decoder there. A rule-aware decoder recovers them and the signal is
    detected; a null decoder stays near the 1/num_classes chance rate.
    Without this, a null on the sealed holdout could mean the machinery is
    blind rather than that the holdout carries no signal."""
    dev_ids = partition.development_ids()
    labeled = tuple((i, _holdout.planted_label(i, planting_salt, num_classes))
                    for i in dev_ids)
    accuracy = _accuracy(decoder, labeled)
    return {
        "planting_salt": planting_salt,
        "development_size": len(labeled),
        "num_classes": num_classes,
        "chance_rate": 1.0 / num_classes,
        "development_accuracy": accuracy,
        "detection_threshold": threshold,
        "detected": bool(accuracy >= threshold),
        "claim_class": CLAIM_CLASS,
        "note": ("a rule-aware model recovers the planted DEVELOPMENT "
                 "labels, so the machinery can detect a signal that is "
                 "really present; a null on the sealed holdout is then a "
                 "finding, not blindness"),
    }


#: Reused directly: the rule-aware and null decoders over planted labels.
planted_decoder = _holdout.planted_decoder
constant_decoder = _holdout.constant_decoder


# =======================================================================
# The refusals (new here + reused from r13.holdout)
# =======================================================================

def refuse_relabel_partition_as_holdout(current: Partition,
                                        proposed: Partition) -> None:
    """Refuse relabelling a non-holdout partition as HOLDOUT.

    A HOLDOUT is defined by never having been seen. An item assigned to
    DEVELOPMENT (or CALIBRATION, or CONTROL) has already been used to build,
    tune, or reference a model; calling it holdout after the fact
    manufactures a holdout out of data the model has effectively seen. The
    partition is fixed by the deterministic split before any modeling and
    cannot be renamed to suit a result."""
    if current is not Partition.HOLDOUT and proposed is Partition.HOLDOUT:
        raise HoldoutAuthorityError(
            f"refused: {current.value} data cannot be relabelled HOLDOUT. A "
            f"holdout is data the model has never seen; an item already "
            f"assigned to {current.value} has been used in development or "
            f"calibration and is no longer blind. Relabelling it holdout "
            f"turns training data into a counterfeit holdout. The partition "
            f"is fixed by the deterministic split before modeling.")


def refuse_score_before_model_frozen(authority: HoldoutAuthority) -> None:
    """Refuse a holdout score before the model is frozen.

    A model still free to change -- a threshold nudged, a feature swapped,
    a hyperparameter re-tuned -- can be adjusted until the holdout score
    looks good, and then presented as though the model had predated the
    score. Freezing the model with a content hash before the holdout is
    touched is what makes the holdout score a test rather than a fit."""
    frozen = getattr(authority, "model_is_frozen", None)
    if frozen is None:
        frozen = getattr(authority, "model_freeze", None) is not None
    if not frozen:
        raise HoldoutAuthorityError(
            "refused: the holdout was scored before the model was frozen. A "
            "model still free to change can be tuned until the holdout "
            "flatters it and then presented as if it predated the score. "
            "Freeze the model (authority.freeze(...)) first, then score.")


def refuse_multiple_holdout_scoring(scored_count: int) -> None:
    """Refuse a second score of a one-shot holdout.

    The first score reveals the holdout: any subsequent model choice, even
    an honest one, is now informed by how the holdout responded, so a
    second score is a training score wearing the holdout's clothes. Under a
    ONE_SHOT policy the holdout is spent after one look. To look more than
    once, declare a SEQUENTIAL policy and spend an error budget."""
    raise HoldoutAuthorityError(
        f"refused: the holdout has already been scored {scored_count} "
        f"time(s) under a ONE_SHOT policy. A re-used holdout is no longer a "
        f"holdout: once its response is known, any further model choice is "
        f"informed by it, and a second score is a training score in "
        f"disguise. Seal a fresh holdout, or use a SEQUENTIAL policy that "
        f"spends an error budget for each look.")


def refuse_unauthorized_access(purpose: AccessPurpose) -> None:
    """Refuse access to the sealed holdout for an unauthorized purpose.

    SCORE and AUDIT are the only authorized purposes. Reading the sealed
    labels for TRAINING or MODEL_SELECTION is exactly the leak the holdout
    exists to prevent: a model built or chosen against the holdout labels
    has been fitted to them, and its holdout score means nothing."""
    raise HoldoutAuthorityError(
        f"refused: access to the sealed holdout for purpose "
        f"{purpose.value} is not authorized. Only "
        f"{', '.join(sorted(p.value for p in AUTHORIZED_PURPOSES))} may "
        f"touch the holdout; reading its labels for TRAINING or "
        f"MODEL_SELECTION fits a model to the very data it will be graded "
        f"on, and the holdout score would then certify nothing.")


#: Reused directly from the R13 holdout authority.
refuse_holdout_in_training = _holdout.refuse_holdout_in_training
refuse_decode_before_commit = _holdout.refuse_decode_before_commit
refuse_overfit_as_generalization = _holdout.refuse_overfit_as_generalization


# =======================================================================
# A worked, fully specified example and the report
# =======================================================================

def build_synthetic_authority(
        count: int = 300,
        policy: ScoringPolicy = ScoringPolicy.ONE_SHOT,
        epoch: int = 20260724) -> tuple:
    """A synthetic partitioned dataset with a sealed holdout authority.

    Returns ``(partition, authority)``. Every id and label is synthetic;
    nothing here names or implies any real quantity."""
    ids = _holdout.synthetic_ids(count)
    partition = partition_dataset(ids)
    holdout_labeled = planted_labels(partition.holdout_ids())
    manifest = seal_holdout(holdout_labeled, epoch=epoch,
                            source=HoldoutSource.SYNTHETIC_PLANTED)
    budget = (AlphaBudget(total=0.05)
              if policy is ScoringPolicy.SEQUENTIAL else None)
    authority = HoldoutAuthority(manifest=manifest, policy=policy,
                                 budget=budget)
    return partition, authority


def holdouts_report() -> dict:
    """The standing result: sealed partitions, one-shot scoring, access log."""
    epoch = 20260724
    partition, authority = build_synthetic_authority(epoch=epoch)
    ids = partition.all_ids()
    holdout_labeled = authority.manifest.holdout_labeled

    # The seal is tamper-evident.
    tampered = ((holdout_labeled[0][0],
                 (holdout_labeled[0][1] + 1) % DEFAULT_NUM_CLASSES),
                ) + tuple(holdout_labeled[1:])

    # Development data cannot be relabelled holdout.
    relabel_refused = False
    try:
        refuse_relabel_partition_as_holdout(Partition.DEVELOPMENT,
                                            Partition.HOLDOUT)
    except HoldoutAuthorityError:
        relabel_refused = True

    # A score before the model is frozen is refused.
    score_before_freeze_refused = False
    try:
        authority.score(planted_decoder(
            _holdout.PlantedDataset(ids=partition.holdout_ids(),
                                    salt=DEFAULT_PLANTING_SALT)),
            holdout_labeled, requester="analyst", epoch=epoch)
    except HoldoutAuthorityError:
        score_before_freeze_refused = True

    # Freeze the model, then score once.
    authority.freeze({"model": "rule_aware", "version": 1}, epoch=epoch)

    def _decode(item_id):
        return _holdout.planted_label(item_id, DEFAULT_PLANTING_SALT,
                                      DEFAULT_NUM_CLASSES)

    first = authority.score(_decode, holdout_labeled,
                            requester="analyst", epoch=epoch)

    # A second score of a one-shot holdout is refused.
    second_score_refused = False
    try:
        authority.score(_decode, holdout_labeled, requester="analyst",
                        epoch=epoch + 1)
    except HoldoutAuthorityError:
        second_score_refused = True

    # Unauthorized access (model selection against labels) is refused.
    unauthorized_refused = False
    try:
        authority.request_access(AccessPurpose.MODEL_SELECTION,
                                 requester="analyst", epoch=epoch)
    except HoldoutAuthorityError:
        unauthorized_refused = True

    # Power on the DEVELOPMENT partition.
    good_power = development_power_check(partition, _decode)
    null_power = development_power_check(partition, constant_decoder(0))

    # Sequential policy spends an error budget.
    _, seq_authority = build_synthetic_authority(
        policy=ScoringPolicy.SEQUENTIAL, epoch=epoch)
    seq_authority.freeze({"model": "rule_aware", "version": 1}, epoch=epoch)
    seq_first = seq_authority.score(_decode, seq_authority.manifest.holdout_labeled,
                                    requester="analyst", epoch=epoch,
                                    alpha_spend=0.03)
    budget_exhausted_refused = False
    try:
        seq_authority.score(_decode, seq_authority.manifest.holdout_labeled,
                            requester="analyst", epoch=epoch + 1,
                            alpha_spend=0.03)
    except HoldoutAuthorityError:
        budget_exhausted_refused = True

    return {
        "what_this_is": (
            "a holdout dataset authority: data is partitioned into named "
            "partitions by a deterministic hash, the HOLDOUT is sealed by a "
            "SHA-256 commitment before any modeling, the model is frozen "
            "before the holdout is scored, and the holdout is scored once "
            "(or against a spent error budget) with every access logged"),
        "partitions": [p.value for p in Partition],
        "item_count": len(ids),
        "partition_is_disjoint": partition.is_disjoint(),
        "partition_covers_all_items": partition.covers(ids),
        "holdout_fraction_actual": partition.actual_fraction(Partition.HOLDOUT),
        "holdout_size": authority.manifest.size(),
        "commitment": authority.manifest.commitment,
        "true_holdout_matches_commitment":
            authority.manifest.verify(holdout_labeled),
        "tampered_holdout_matches_commitment":
            authority.manifest.verify(tampered),
        "development_cannot_be_relabelled_holdout": relabel_refused,
        "score_before_model_frozen_refused": score_before_freeze_refused,
        "first_holdout_score_accuracy": first["accuracy"],
        "second_one_shot_score_refused": second_score_refused,
        "unauthorized_access_refused": unauthorized_refused,
        "access_log_length": len(authority.accesses),
        "power_rule_aware_detected": good_power["detected"],
        "power_null_detected": null_power["detected"],
        "sequential_first_look_alpha_spent": seq_first["alpha_spent"],
        "sequential_budget_remaining_after_first": seq_first["budget_remaining"],
        "sequential_budget_exhausted_refused": budget_exhausted_refused,
        "refusals": [
            "refuse_relabel_partition_as_holdout",
            "refuse_score_before_model_frozen",
            "refuse_multiple_holdout_scoring",
            "refuse_unauthorized_access",
            "refuse_holdout_in_training (reused)",
            "refuse_decode_before_commit (reused)",
            "refuse_overfit_as_generalization (reused)",
        ],
        "claim_class": CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any model generalized. It provides the sealed "
            "holdout discipline under which such a claim could be tested. "
            "The partition is a deterministic hash of the item ids, so the "
            "holdout is fixed before any modeling and cannot be "
            "cherry-picked; development data cannot be relabelled holdout; "
            "the holdout is sealed by a SHA-256 commitment over its ids and "
            "labels, so a relabelled or substituted holdout fails to match "
            "while the true one matches; the model must be frozen before "
            "the holdout is scored; the holdout is scored once under "
            "ONE_SHOT (a re-used holdout is no longer a holdout) or against "
            "a spent error budget under SEQUENTIAL; reading the holdout for "
            "training or model selection is refused; every access is "
            "logged; and the power check shows a rule-aware model recovers "
            "a PLANTED signal on DEVELOPMENT, so a null on the holdout is a "
            "finding rather than blindness. Every id and label here is "
            "synthetic; nothing is measured and no physical validation is "
            "claimed. The strongest class here is SOFTWARE_IMPLEMENTED."),
    }


__all__ = [
    "VERDICT", "PHYSICAL_VALIDATION", "CLAIM_CLASS", "HOLDOUT_EVIDENCE_LEVEL",
    "DEFAULT_PARTITION_SALT", "DEFAULT_COMMIT_SALT", "DEFAULT_PLANTING_SALT",
    "DEFAULT_NUM_CLASSES", "POWER_DETECTION_THRESHOLD",
    "HoldoutAuthorityError",
    "Partition", "DEFAULT_FRACTIONS", "DatasetPartition", "partition_dataset",
    "HoldoutSource", "planted_labels", "HoldoutManifest", "seal_holdout",
    "ModelFreeze", "freeze_model",
    "ScoringPolicy", "AccessPurpose", "AUTHORIZED_PURPOSES", "AccessRecord",
    "AlphaSpend", "AlphaBudget", "HoldoutAuthority",
    "development_power_check", "planted_decoder", "constant_decoder",
    "refuse_relabel_partition_as_holdout", "refuse_score_before_model_frozen",
    "refuse_multiple_holdout_scoring", "refuse_unauthorized_access",
    "refuse_holdout_in_training", "refuse_decode_before_commit",
    "refuse_overfit_as_generalization",
    "build_synthetic_authority", "holdouts_report",
]
