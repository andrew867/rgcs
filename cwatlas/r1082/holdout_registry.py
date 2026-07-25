"""P25 — Holdout vector registry and body-scope firewall.

Adversarial statistics start with an honest partition. This module builds a
**sealed** registry of source vectors split into *train*, *development*, and
*holdout* partitions, with two disciplines the rest of T07 depends on:

* **Train / holdout disjointness.** A vector may not appear in both the fitting
  set and the sealed holdout set (a holdout the fit has already seen is not a
  holdout). Registering the same opaque id into two partitions is refused, and
  the two sealed calibration anchors (the Wilkes fixed root and the
  ``165876523 = Stonehenge`` training anchor) may never be registered as
  holdouts — they were used in the T05 fit.

* **The body-scope firewall.** Only ``EARTH`` / ``TERRA`` vectors are in scope
  for the locked ``EARTH_ROOT_D_V1`` root. A vector reported for another planet
  or a star is **typed out of scope** and routed to the ``FOREIGN`` partition —
  it is *not* force-decoded onto Earth merely because it shares the ``01|65``
  prefix with Stonehenge. Declared body scope is required.

Every vector is referenced by an **opaque public id** only (for example
``HOLDOUT_SYN_0001``); no raw private vector or narrative is ever stored. The
holdout partition is sealed with a deterministic SHA-256 digest so a later
silent edit is detectable (the "no result shopping" discipline of T07).

A registered vector is at most a ``SOURCE`` claim; a holdout *prediction* made
later is a ``CALIBRATED_CANDIDATE`` at most — never a measured fact, never a
validated source origin. See :mod:`cwatlas.r1082.claims`.

    SOURCE_ORIGIN_NOT_VALIDATED
    PHYSICAL_VALIDATION_NOT_CLAIMED
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Optional, Tuple

from cwatlas.r1082 import claims, spatialization
from cwatlas.r1082.geocode_forward import BODY_IN_SCOPE
from cwatlas.r1082.source_import import STONEHENGE_FIXTURE_ID

REGISTRY_ID = "CW-R1082-HOLDOUT"
REGISTRY_VERSION = "1.0.0"

#: The opaque id of the Wilkes fixed-root training anchor (mirrors the id the
#: candidate ensemble renders training anchors under).
WILKES_ANCHOR_ID = "WILKES_FIXED_ROOT"

#: The two sealed anchors consumed by the T05 calibration fit. Neither may ever
#: be registered as a holdout (a fit anchor is not an unseen holdout).
FIT_USED_ANCHOR_IDS = frozenset({WILKES_ANCHOR_ID, STONEHENGE_FIXTURE_ID})

#: A fixed, conventional seal timestamp (ISO-8601). Passed in everywhere; this
#: constant is only a deterministic default, never a wall-clock read.
DEFAULT_SEALED_AT = "2026-07-25T00:00:00Z"


class HoldoutRegistryError(RuntimeError):
    """Raised on a partition conflict, a scope violation, or a sealed edit."""


class Partition(Enum):
    """A sealed data partition. ``FOREIGN`` is out of scope for the Earth root."""

    TRAIN = "train"
    DEV = "dev"
    HOLDOUT = "holdout"
    FOREIGN = "foreign_out_of_scope"


class BodyScope(Enum):
    """Whether a vector's declared body is described by the locked root."""

    IN_SCOPE = "IN_SCOPE"
    FOREIGN_OUT_OF_SCOPE = "FOREIGN_OUT_OF_SCOPE"


def classify_body(body: str) -> BodyScope:
    """Type a declared body as in-scope (Earth/Terra) or foreign (out of scope).

    The Earth root describes only :data:`BODY_IN_SCOPE`. Any other declared body
    (another planet, a star) is foreign and is not force-decoded onto Earth.
    """
    return (BodyScope.IN_SCOPE if str(body).upper() in BODY_IN_SCOPE
            else BodyScope.FOREIGN_OUT_OF_SCOPE)


def _validate_route(tokens) -> Tuple[int, ...]:
    """Validate a five-token base-100 route shape (public, synthetic)."""
    seq = tuple(tokens)
    if len(seq) != spatialization.ROUTE_TOKENS:
        raise HoldoutRegistryError(
            f"route must have exactly {spatialization.ROUTE_TOKENS} tokens, got "
            f"{len(seq)}")
    out = []
    for i, t in enumerate(seq):
        if isinstance(t, bool) or not isinstance(t, int):
            raise HoldoutRegistryError(f"route token {i} must be an int, got {t!r}")
        if not spatialization.TOKEN_MIN <= t <= spatialization.TOKEN_MAX:
            raise HoldoutRegistryError(
                f"route token {i}={t} out of range "
                f"[{spatialization.TOKEN_MIN}, {spatialization.TOKEN_MAX}]")
        out.append(int(t))
    return tuple(out)


def _route_hash(tokens: Tuple[int, ...]) -> str:
    """An opaque content hash of a route shape (no raw private string)."""
    blob = json.dumps(list(tokens), separators=(",", ":"))
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class HoldoutVector:
    """A partitioned source vector, referenced by an opaque id only.

    Attributes
    ----------
    opaque_id:
        The public opaque id (never a private vector or narrative).
    tokens:
        The sanitised five-token base-100 route shape (public).
    route_hash:
        An opaque SHA-256 of the token shape.
    body:
        The declared body (normalised upper-case).
    body_scope:
        In-scope (Earth/Terra) or foreign-out-of-scope.
    partition:
        The sealed partition the vector belongs to.
    """

    opaque_id: str
    tokens: Tuple[int, ...]
    route_hash: str
    body: str
    body_scope: BodyScope
    partition: Partition

    @property
    def in_scope(self) -> bool:
        return self.body_scope is BodyScope.IN_SCOPE

    def public_projection(self) -> dict:
        """A narrative-free public projection (opaque id + route shape only)."""
        return {
            "opaque_id": self.opaque_id,
            "tokens": list(self.tokens),
            "route_hash": self.route_hash,
            "body": self.body,
            "body_scope": self.body_scope.value,
            "partition": self.partition.value,
            "in_scope": self.in_scope,
            "claim_class": claims.EvidenceClass.SOURCE.value,
        }

    def assert_not_measured(self) -> None:
        """A holdout prediction is a candidate, never a measured fact."""
        claims.refuse_candidate_as_measured()


@dataclass(frozen=True)
class HoldoutSeal:
    """A deterministic seal over the holdout partition (tamper-evident)."""

    registry_id: str
    registry_version: str
    sealed_at: str
    holdout_count: int
    holdout_digest: str

    def to_dict(self) -> dict:
        return {
            "registry_id": self.registry_id,
            "registry_version": self.registry_version,
            "sealed_at": self.sealed_at,
            "holdout_count": self.holdout_count,
            "holdout_digest": self.holdout_digest,
        }


class HoldoutRegistry:
    """A registry enforcing train/holdout disjointness and the body firewall.

    Public construction only: every vector is a synthetic, opaque-id record. The
    holdout partition can be sealed once; after that no holdout may be added or
    moved (no result shopping).
    """

    def __init__(self) -> None:
        self._vectors: Dict[str, HoldoutVector] = {}
        self._seal: Optional[HoldoutSeal] = None

    def __len__(self) -> int:
        return len(self._vectors)

    @property
    def is_sealed(self) -> bool:
        return self._seal is not None

    @property
    def vectors(self) -> Tuple[HoldoutVector, ...]:
        return tuple(self._vectors[k] for k in self._vectors)

    def register(self, opaque_id: str, tokens, *, partition: Partition,
                 body: str = "EARTH") -> HoldoutVector:
        """Register one source vector into a partition, behind the firewall.

        A foreign body is **typed out of scope** and forced into the ``FOREIGN``
        partition (not force-decoded). An Earth/Terra vector may not be marked
        ``FOREIGN``. Registering an already-known id into a *different* partition
        is refused (train/holdout disjointness), and a sealed anchor may never be
        a holdout.
        """
        if not opaque_id:
            raise HoldoutRegistryError("opaque_id must be a non-empty public id")
        if not isinstance(partition, Partition):
            raise HoldoutRegistryError("partition must be a Partition enum")
        route = _validate_route(tokens)
        body_norm = str(body).upper()
        scope = classify_body(body_norm)

        # The body-scope firewall: a foreign body is typed out of scope; an
        # in-scope body may not be filed as FOREIGN.
        if scope is BodyScope.FOREIGN_OUT_OF_SCOPE:
            effective = Partition.FOREIGN
        else:
            if partition is Partition.FOREIGN:
                raise HoldoutRegistryError(
                    f"body {body_norm!r} is in scope for the Earth root; it may "
                    f"not be filed as FOREIGN")
            effective = partition

        # A sealed calibration anchor is never an unseen holdout.
        if effective is Partition.HOLDOUT and opaque_id in FIT_USED_ANCHOR_IDS:
            raise HoldoutRegistryError(
                f"refused: {opaque_id!r} was used in the T05 fit (a sealed "
                f"training anchor); it may not be registered as a holdout")

        # Train/holdout disjointness: a vector cannot be in two partitions.
        existing = self._vectors.get(opaque_id)
        if existing is not None:
            if existing.partition is not effective:
                raise HoldoutRegistryError(
                    f"refused: {opaque_id!r} is already in partition "
                    f"{existing.partition.value!r} and cannot also be "
                    f"{effective.value!r} (train/holdout disjointness)")
            raise HoldoutRegistryError(
                f"duplicate registration of {opaque_id!r}")

        # No holdout may be added once the holdout partition is sealed.
        if self._seal is not None and effective is Partition.HOLDOUT:
            raise HoldoutRegistryError(
                "refused: the holdout partition is sealed; no holdout may be "
                "added after the seal (no result shopping)")

        rec = HoldoutVector(
            opaque_id=opaque_id, tokens=route, route_hash=_route_hash(route),
            body=body_norm, body_scope=scope, partition=effective)
        self._vectors[opaque_id] = rec
        return rec

    def _ids_in(self, partition: Partition) -> Tuple[str, ...]:
        return tuple(sorted(k for k, v in self._vectors.items()
                            if v.partition is partition))

    @property
    def train_ids(self) -> Tuple[str, ...]:
        return self._ids_in(Partition.TRAIN)

    @property
    def dev_ids(self) -> Tuple[str, ...]:
        return self._ids_in(Partition.DEV)

    @property
    def holdout_ids(self) -> Tuple[str, ...]:
        return self._ids_in(Partition.HOLDOUT)

    @property
    def foreign_ids(self) -> Tuple[str, ...]:
        return self._ids_in(Partition.FOREIGN)

    def in_scope_vectors(self) -> Tuple[HoldoutVector, ...]:
        return tuple(v for v in self.vectors if v.in_scope)

    def foreign_vectors(self) -> Tuple[HoldoutVector, ...]:
        return tuple(v for v in self.vectors if not v.in_scope)

    def assert_disjoint(self) -> None:
        """Confirm the train and holdout id sets do not intersect (invariant)."""
        overlap = set(self.train_ids) & set(self.holdout_ids)
        if overlap:
            raise HoldoutRegistryError(
                f"train/holdout partitions overlap: {sorted(overlap)}")

    def holdout_digest(self) -> str:
        """A deterministic content digest over the sealed holdout partition."""
        payload = [self._vectors[i].public_projection()
                   for i in self.holdout_ids]
        blob = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def seal(self, *, sealed_at: str = DEFAULT_SEALED_AT) -> HoldoutSeal:
        """Seal the holdout partition (idempotent) after checking disjointness."""
        self.assert_disjoint()
        if self._seal is None:
            self._seal = HoldoutSeal(
                registry_id=REGISTRY_ID, registry_version=REGISTRY_VERSION,
                sealed_at=sealed_at, holdout_count=len(self.holdout_ids),
                holdout_digest=self.holdout_digest())
        return self._seal

    def export_public(self) -> dict:
        """A narrative-free public projection of the whole registry."""
        return {
            "registry_id": REGISTRY_ID,
            "registry_version": REGISTRY_VERSION,
            "counts": {
                "train": len(self.train_ids),
                "dev": len(self.dev_ids),
                "holdout": len(self.holdout_ids),
                "foreign_out_of_scope": len(self.foreign_ids),
            },
            "vectors": [v.public_projection() for v in self.vectors],
            "sealed": self.is_sealed,
            "holdout_digest": self.holdout_digest(),
        }


#: A small deterministic set of synthetic, public holdout/train/foreign vectors.
#: Opaque ids only; no private vector or narrative. The foreign entries carry a
#: non-Earth declared body to exercise the firewall.
SYNTHETIC_FIXTURES: Tuple[dict, ...] = (
    {"opaque_id": "TRAIN_SYN_0001", "tokens": (0, 0, 0, 0, 0),
     "partition": Partition.TRAIN, "body": "EARTH"},
    {"opaque_id": "TRAIN_SYN_0002", "tokens": (12, 34, 56, 78, 90),
     "partition": Partition.TRAIN, "body": "TERRA"},
    {"opaque_id": "DEV_SYN_0001", "tokens": (7, 7, 7, 7, 7),
     "partition": Partition.DEV, "body": "EARTH"},
    {"opaque_id": "HOLDOUT_SYN_0001", "tokens": (50, 0, 50, 0, 50),
     "partition": Partition.HOLDOUT, "body": "EARTH"},
    {"opaque_id": "HOLDOUT_SYN_0002", "tokens": (99, 99, 99, 99, 99),
     "partition": Partition.HOLDOUT, "body": "EARTH"},
    # Foreign bodies: shares the 01|65 prefix but is NOT forced onto Earth.
    {"opaque_id": "FOREIGN_SYN_0001", "tokens": (1, 65, 3, 4, 5),
     "partition": Partition.FOREIGN, "body": "MARS"},
    {"opaque_id": "FOREIGN_SYN_0002", "tokens": (1, 65, 87, 65, 23),
     "partition": Partition.FOREIGN, "body": "PROXIMA_CENTAURI_B"},
)


def build_default_registry() -> HoldoutRegistry:
    """Build the deterministic synthetic registry (public fixtures only)."""
    reg = HoldoutRegistry()
    for fx in SYNTHETIC_FIXTURES:
        reg.register(fx["opaque_id"], fx["tokens"],
                     partition=fx["partition"], body=fx["body"])
    return reg


def holdout_registry_report() -> dict:
    """P25 declaration receipt. Disjoint partitions; foreign bodies out of scope."""
    reg = build_default_registry()
    seal = reg.seal()
    return {
        "phase_id": "P25",
        "tranche": "T07",
        "what_this_is": (
            "the holdout vector registry and body-scope firewall: source "
            "vectors are split into sealed train/dev/holdout partitions with "
            "train/holdout disjointness enforced, foreign-body vectors typed out "
            "of scope (routed to FOREIGN, never force-decoded onto Earth), and "
            "every vector referenced by an opaque public id only; the holdout "
            "partition is sealed with a deterministic SHA-256 digest."),
        "registry_id": REGISTRY_ID,
        "registry_version": REGISTRY_VERSION,
        "bodies_in_scope": sorted(BODY_IN_SCOPE),
        "fit_used_anchor_ids": sorted(FIT_USED_ANCHOR_IDS),
        "counts": {
            "train": len(reg.train_ids),
            "dev": len(reg.dev_ids),
            "holdout": len(reg.holdout_ids),
            "foreign_out_of_scope": len(reg.foreign_ids),
        },
        "train_holdout_disjoint": True,
        "foreign_bodies_force_decoded": False,
        "holdouts_used_in_fit": False,
        "opaque_ids_only": True,
        "holdout_sealed": reg.is_sealed,
        "holdout_digest": seal.holdout_digest,
        "claim_class": claims.EvidenceClass.SOURCE.value,
        "max_evidence": claims.MAX_CANDIDATE_EVIDENCE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_HOLDOUT_REGISTRY_DISJOINT_SEALED_BODY_SCOPE_FIREWALL",
        "what_this_does_not_say": (
            "A registered vector is a reported SOURCE claim referenced by an "
            "opaque id. Partitioning and sealing it validates neither its origin "
            "nor any geographic meaning; a foreign-body vector is typed out of "
            "scope, not decoded; and a holdout prediction, when later made, is a "
            "CALIBRATED_CANDIDATE at most, never a measured fact."),
    }
