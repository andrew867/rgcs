"""P19 — the 192-feature disk: a frozen, versioned feature specification.

The coordinate/response codec upstream in R13 turns a linear-response
measurement into a fixed-width feature vector, and every downstream
holdout, benchmark and null model is scored against *that* vector. If the
feature set drifts -- a bin added here, a normalisation changed there --
then two runs are no longer comparable and every frozen-before-reveal
guarantee quietly evaporates, because the thing that was frozen is not
the thing being scored. So the feature set has to be pinned down once, in
full, and made tamper-evident.

That is all this module is: a **specification**, not a computation and
not a measurement. :class:`FeatureSpec` names one feature -- its index,
its group, its unit, and a short description of how it would be computed
-- and :data:`DISK` is the ordered list of exactly **192** of them,
partitioned into eight groups (spectral, modal, geometric, temporal,
angular, energy, phase, symmetry). The indices run 0..191, contiguous and
unique, and the groups partition the set with nothing left over and
nothing counted twice.

**Freeze by hash.** :func:`disk_hash` takes a sha256 over the ordered
specification, so the feature set is versioned and any edit -- a renamed
feature, a changed unit, a reordering -- changes the digest. Two runs
that agree on the digest agree on the feature set; two that disagree are
not comparable and the disagreement is visible rather than silent.

**A feature is an input, never an output.** The disk describes how a
signal is *represented*, not what a coordinate *decodes to*. A feature
vector is the codec's input side. Reading a decoded destination off a
feature -- "feature 137 is the latitude" -- is exactly the coordinate
alias-to-destination promotion R13 forbids, and
:func:`refuse_feature_as_decoded_output` raises on it unconditionally.
:func:`refuse_disk_as_measurement` raises likewise: a specification of
features is not a set of measured feature values.

Nothing here is measured. The disk is finalised as a specification and
nothing more; the verdict is ``FEATURE_DISK_FINALIZED_192_DIMENSIONS``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

#: The finalized dimensionality. The disk is exactly this wide, forever;
#: a different width is a different disk with a different hash.
DISK_DIMENSIONS = 192

#: The standing verdict. The disk is a frozen specification, nothing more.
DEFAULT_VERDICT = "FEATURE_DISK_FINALIZED_192_DIMENSIONS"

#: Every feature is a computed representation, not a measured value, so
#: each carries the same modelling claim class.
FEATURE_CLAIM_CLASS = "ANALYTIC_MODEL"

CLAIM_CLASSES = (
    "EXACT_IDENTITY",
    "DERIVED_ARITHMETIC",
    "ANALYTIC_MODEL",
    "NUMERICAL_SIMULATION",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "PROSPECTIVE_PREDICTION",
    "BLOCKED_MISSING_INPUT",
)


class DiskDriveError(RuntimeError):
    """Raised on a malformed feature, a broken partition, or any attempt
    to read a feature as a decoded destination or as a measurement."""


class FeatureGroup(Enum):
    """The eight groups the 192 features partition into. The order is part
    of the specification and fixes where each group sits on the disk."""

    SPECTRAL = "SPECTRAL"
    MODAL = "MODAL"
    GEOMETRIC = "GEOMETRIC"
    TEMPORAL = "TEMPORAL"
    ANGULAR = "ANGULAR"
    ENERGY = "ENERGY"
    PHASE = "PHASE"
    SYMMETRY = "SYMMETRY"


@dataclass(frozen=True)
class FeatureSpec:
    """One feature on the disk: its position, group, unit, and recipe.

    A specification, not a value. ``transform`` is a short description of
    how the feature would be computed from the windowed linear response;
    it names an input representation and never a decoded output. Two
    feature specs are equal iff every field agrees, which is what makes
    the disk hash tamper-evident."""

    index: int
    name: str
    group: FeatureGroup
    unit: str
    claim_class: str
    transform: str

    def __post_init__(self) -> None:
        if not isinstance(self.index, int) or isinstance(self.index, bool):
            raise DiskDriveError("feature index must be a plain int")
        if self.index < 0:
            raise DiskDriveError("feature index must be non-negative")
        if not self.name:
            raise DiskDriveError("a feature needs a non-empty name")
        if not isinstance(self.group, FeatureGroup):
            raise DiskDriveError("group must be a FeatureGroup")
        if not self.unit:
            raise DiskDriveError("a feature needs a unit")
        if self.claim_class not in CLAIM_CLASSES:
            raise DiskDriveError(
                f"unknown claim class {self.claim_class!r}")
        if not self.transform:
            raise DiskDriveError("a feature needs a transform description")

    def token(self) -> str:
        """The ordered token this feature contributes to the disk hash.

        Every field is included, so any edit -- a renamed feature, a
        changed unit, a reordered index -- moves the digest."""
        return "\x1f".join((
            str(self.index), self.name, self.group.value,
            self.unit, self.claim_class, self.transform))


# =======================================================================
# The group layout: how the 192 dimensions are apportioned
# =======================================================================

#: (group, count, unit, transform template). The counts sum to exactly
#: 192; the order is the order the features sit on the disk. Changing any
#: count, unit or template changes the disk and therefore the hash.
GROUP_LAYOUT: tuple[tuple[FeatureGroup, int, str, str], ...] = (
    (FeatureGroup.SPECTRAL, 32, "normalized_power",
     "normalized power in spectral bin {k} of the windowed response"),
    (FeatureGroup.MODAL, 24, "dimensionless",
     "projection of the response onto reference modal shape {k}"),
    (FeatureGroup.GEOMETRIC, 24, "dimensionless",
     "geometric moment {k} of the response support"),
    (FeatureGroup.TEMPORAL, 24, "seconds",
     "temporal decay statistic {k} of the impulse response"),
    (FeatureGroup.ANGULAR, 24, "radians",
     "in-plane angular harmonic {k} of the response pattern"),
    (FeatureGroup.ENERGY, 24, "joules_normalized",
     "normalized energy in ledger partition {k}"),
    (FeatureGroup.PHASE, 20, "radians",
     "relative phase in phase-alphabet slot {k}"),
    (FeatureGroup.SYMMETRY, 20, "dimensionless",
     "symmetry-class projection {k} of the response"),
)


def _build_disk() -> tuple[FeatureSpec, ...]:
    """Generate the ordered 192-feature disk from the group layout."""
    out: list[FeatureSpec] = []
    index = 0
    for group, count, unit, template in GROUP_LAYOUT:
        for k in range(count):
            out.append(FeatureSpec(
                index=index,
                name=f"{group.value}_{k:02d}",
                group=group,
                unit=unit,
                claim_class=FEATURE_CLAIM_CLASS,
                transform=template.format(k=k),
            ))
            index += 1
    return tuple(out)


#: The finalized, ordered feature disk. Exactly 192 features.
DISK: tuple[FeatureSpec, ...] = _build_disk()

assert len(DISK) == DISK_DIMENSIONS, (
    f"the disk must be exactly {DISK_DIMENSIONS} features wide, "
    f"built {len(DISK)}")
assert tuple(f.index for f in DISK) == tuple(range(DISK_DIMENSIONS)), (
    "disk indices must be 0..191, contiguous and in order")


# =======================================================================
# Lookups and partition bookkeeping
# =======================================================================

def feature_at(index: int) -> FeatureSpec:
    """The feature at a given disk index."""
    if not isinstance(index, int) or isinstance(index, bool):
        raise DiskDriveError("index must be a plain int")
    if not 0 <= index < DISK_DIMENSIONS:
        raise DiskDriveError(
            f"index {index} outside the disk range [0, {DISK_DIMENSIONS})")
    return DISK[index]


def features_in_group(group: FeatureGroup) -> tuple[FeatureSpec, ...]:
    """Every feature belonging to one group, in disk order."""
    if not isinstance(group, FeatureGroup):
        raise DiskDriveError("group must be a FeatureGroup")
    return tuple(f for f in DISK if f.group is group)


def group_sizes() -> dict[FeatureGroup, int]:
    """How many features each group contributes."""
    sizes: dict[FeatureGroup, int] = {g: 0 for g in FeatureGroup}
    for f in DISK:
        sizes[f.group] += 1
    return sizes


def groups_partition_the_disk() -> bool:
    """True iff the groups cover the disk exactly once, no gaps, no overlap.

    Every index in [0, 192) belongs to exactly one group and the group
    sizes sum to 192, so the eight groups are a genuine partition rather
    than an overlapping cover."""
    seen: set[int] = set()
    for group in FeatureGroup:
        for f in features_in_group(group):
            if f.index in seen:
                return False
            seen.add(f.index)
    return seen == set(range(DISK_DIMENSIONS))


# =======================================================================
# Freeze by hash
# =======================================================================

def disk_hash(disk: tuple[FeatureSpec, ...] | None = None) -> str:
    """The sha256 digest over the ordered feature specification.

    This is what versions the disk. Two runs that agree on this digest
    agree, feature for feature, on how a signal is represented; two that
    disagree are not comparable, and the disagreement is a changed hash
    rather than a silent drift. Any edit -- a renamed feature, a changed
    unit, a reordered index, a different transform -- moves the digest."""
    specs = DISK if disk is None else tuple(disk)
    body = "\x1e".join(f.token() for f in specs)
    return hashlib.sha256(body.encode()).hexdigest()


#: The frozen digest of the finalized disk, computed once at import.
DISK_HASH = disk_hash()


def verify_disk_hash(expected: str,
                     disk: tuple[FeatureSpec, ...] | None = None) -> bool:
    """True iff the disk still hashes to ``expected``."""
    if not isinstance(expected, str) or len(expected) != 64:
        raise DiskDriveError("expected a 64-character sha256 hex digest")
    return disk_hash(disk) == expected


# =======================================================================
# The two refusals
# =======================================================================

def refuse_feature_as_decoded_output(feature: FeatureSpec | int | str,
                                     *_args, **_kwargs) -> None:
    """Refuse to read any feature as a decoded destination.

    The disk describes the codec's *input* side: how a response is turned
    into a feature vector. A feature is a representation of a signal, not
    a coordinate the signal decodes to. Announcing that some feature *is*
    a latitude, a shell index, or a place is the alias-to-destination
    promotion R13 forbids -- a coordinate consistent with many frames is
    an alias set, never a decoded destination -- and it is refused here
    whatever the feature and whatever its value."""
    if isinstance(feature, FeatureSpec):
        label = f"feature {feature.index} ({feature.name})"
    else:
        label = f"feature {feature!r}"
    raise DiskDriveError(
        f"refused: {label} is an INPUT representation on the feature "
        f"disk, not a decoded destination. The disk specifies how a "
        f"response is turned into a fixed feature vector; it does not "
        f"contain, imply, or decode any coordinate, shell, place, or "
        f"target. Reading a feature as an output is the coordinate "
        f"alias-to-destination promotion R13 forbids.")


def refuse_disk_as_measurement(*_args, **_kwargs) -> None:
    """Refuse to treat the disk as a set of measured feature values.

    The disk is a *specification*: names, groups, units and recipes. It
    holds no numbers read off any apparatus. A specification of features
    is not a measurement of them, and no measurement is performed
    anywhere in this module."""
    raise DiskDriveError(
        "refused: the feature disk is a SPECIFICATION -- 192 named "
        "features with groups, units and transform descriptions -- not a "
        "set of measured feature values. No apparatus was operated and no "
        "feature was evaluated on real data. A specification is not a "
        "measurement.")


# =======================================================================
# The report
# =======================================================================

def diskdrive_report() -> dict:
    sizes = group_sizes()
    return {
        "what_this_is": (
            "the finalized 192-feature disk: a frozen, hash-versioned "
            "specification of the coordinate/response codec's feature "
            "vector, partitioned into eight groups"),
        "dimensions": DISK_DIMENSIONS,
        "feature_count": len(DISK),
        "groups": [g.value for g in FeatureGroup],
        "group_sizes": {g.value: n for g, n in sizes.items()},
        "groups_partition_the_disk": groups_partition_the_disk(),
        "indices_contiguous_and_unique": (
            tuple(f.index for f in DISK) == tuple(range(DISK_DIMENSIONS))),
        "disk_hash": DISK_HASH,
        "refusals": [
            "refuse_feature_as_decoded_output",
            "refuse_disk_as_measurement",
        ],
        "claim_class": FEATURE_CLAIM_CLASS,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say any feature was measured, evaluated, or read "
            "off an apparatus: the disk is a specification of how a "
            "response would be represented, not a set of values. It does "
            "not say any feature decodes to a coordinate, shell, or place "
            "-- a feature is the codec's input side, and reading one as a "
            "decoded destination is the alias-to-destination promotion "
            "R13 forbids. What the disk provides is a single frozen, "
            "tamper-evident feature set of exactly 192 dimensions, so "
            "that every downstream holdout and null model is scored "
            "against the same representation and any drift in that "
            "representation shows up as a changed hash. Nothing here is "
            "measured and no physical validation is claimed."),
    }
