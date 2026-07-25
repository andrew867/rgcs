"""P24 — independent-replication receipts: the only path off the ceiling.

A single laboratory's unexplained residual is capped at
``UNEXPLAINED_INSTRUMENT_RESIDUAL`` (P12): it survived the
ordinary-explanation firewall and exceeded its own error budget, but one
apparatus in one room run by one operator cannot promote it further. The
*only* way up the ladder -- to ``REPLICATED_ANOMALY`` (E7) -- is independent
replication, and this module types exactly what that requires.

**A replication receipt records one independent attempt.** It names the
originating laboratory and the replicating one (each a distinct operator,
apparatus, and site, optionally a distinct specimen), the frozen protocol
hash the replica followed, its own residual and combined uncertainty, whether
it actually ran the ordinary-explanation firewall and whether the residual
survived it, and its outcome: ``CONFIRMS``, ``FAILS_TO_CONFIRM``, or
``CONTRADICTS``. Rerun, independent implementation, independent operator, and
independent laboratory are represented as **distinct** independence levels --
a re-run of the same code on the same data is a ``RERUN``, not a replication.

**Promotion is deliberately hard.** A residual reaches ``REPLICATED_ANOMALY``
only when at least :data:`MIN_INDEPENDENT_REPLICATIONS` genuinely independent
replications (different apparatus **and** site **and** operator, mutually
distinct as well as distinct from the origin) each *confirm* it: each
followed the frozen protocol, produced a residual exceeding its own budget,
and survived the full firewall. Everything short of that stays at the
ceiling. Failed and contradicting attempts are never discarded -- the bundle
is a hash-chained ledger (:mod:`r13.serialize`) that preserves every receipt,
so a promotion can always be re-derived and a retraction always drops it.

Nothing here is measured. Every receipt in this repository is a synthetic
fixture; the module types passed-in receipts and operates no apparatus.
``measured_here`` is ``"nothing"`` and ``PHYSICAL_VALIDATION_NOT_CLAIMED``.
Even a ``REPLICATED_ANOMALY`` is only a replicated *unexplained* effect
warranting further study -- it is never new physics and there is no
``PHRYLL_DETECTED`` state (:func:`refuse_phryll_detected`, reused from the
governance core).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from r13 import serialize
from r15 import claims

# --- standing vocabulary -------------------------------------------------

#: The standing verdict for this module.
VERDICT = "REPLICATION_RECEIPTS_TYPED_CEILING_AT_UNEXPLAINED_RESIDUAL"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The class of the receipting machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED

#: The strongest label a single lab's unreplicated residual can carry.
RESIDUAL_CEILING = claims.ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL

#: The class an independently replicated residual can reach -- still not new
#: physics, only a replicated unexplained effect.
REPLICATED_CLASS = claims.ClaimClass.REPLICATED_ANOMALY

#: Genuine independent replication requires at least this many mutually
#: independent confirming replications. Two, not one: a single lab -- however
#: many times it re-runs -- can never satisfy this.
MIN_INDEPENDENT_REPLICATIONS = 2

#: Bumped whenever the promotion rules change; carried on every verdict so a
#: promotion decision is versioned and auditable.
REPLICATION_VERSION = "1.0.0"


class ReplicationError(RuntimeError):
    """Raised on a malformed receipt or a forbidden promotion."""


# --- modes: REAL / REPLAY / SYNTHETIC / FAULT_INJECTION kept distinct ----

class ReplicationMode(Enum):
    """How a replication attempt's data was produced. Only ``REAL`` is a
    physical acquisition; the others are software constructs."""

    REAL = "REAL"
    REPLAY = "REPLAY"
    SYNTHETIC = "SYNTHETIC"
    FAULT_INJECTION = "FAULT_INJECTION"

    @property
    def is_physical(self) -> bool:
        """Only a REAL acquisition of a specimen is physical."""
        return self is ReplicationMode.REAL


# --- the independence ladder ---------------------------------------------

class IndependenceLevel(Enum):
    """The distinct levels of independence, weakest to strongest.

    * ``RERUN`` -- the same apparatus, operator, and site: a re-run (or a
      reanalysis of the same data). Not a replication.
    * ``INDEPENDENT_IMPLEMENTATION`` -- a distinct apparatus/implementation,
      but the same operator or site.
    * ``INDEPENDENT_OPERATOR`` -- a distinct apparatus and operator, same site.
    * ``INDEPENDENT_LABORATORY`` -- distinct apparatus **and** operator **and**
      site: the only level that counts as genuine independence.
    """

    RERUN = 0
    INDEPENDENT_IMPLEMENTATION = 1
    INDEPENDENT_OPERATOR = 2
    INDEPENDENT_LABORATORY = 3


class ReplicationOutcome(Enum):
    """A replication attempt's verdict on the originating residual."""

    CONFIRMS = "CONFIRMS"
    FAILS_TO_CONFIRM = "FAILS_TO_CONFIRM"
    CONTRADICTS = "CONTRADICTS"


# --- who/what/where: a laboratory identity -------------------------------

@dataclass(frozen=True)
class LabIdentity:
    """The independence-bearing identity of a laboratory attempt.

    ``operator_id``, ``apparatus_id``, and ``site_id`` are the three axes of
    independence; ``specimen_id`` is carried so a distinct specimen can be
    recorded where claimed.
    """

    operator_id: str
    apparatus_id: str
    site_id: str
    specimen_id: str = ""

    def __post_init__(self) -> None:
        for name in ("operator_id", "apparatus_id", "site_id"):
            if not str(getattr(self, name)).strip():
                raise ReplicationError(
                    f"a lab identity needs a non-empty {name}")

    def as_dict(self) -> dict:
        return {
            "operator_id": self.operator_id,
            "apparatus_id": self.apparatus_id,
            "site_id": self.site_id,
            "specimen_id": self.specimen_id,
        }


def independence_level(origin: LabIdentity,
                       replica: LabIdentity) -> IndependenceLevel:
    """The independence level of ``replica`` relative to ``origin``.

    Genuine independence -- ``INDEPENDENT_LABORATORY`` -- requires all three
    of apparatus, operator, and site to differ. Anything less is a weaker
    (or no) form of independence.
    """
    distinct_apparatus = replica.apparatus_id != origin.apparatus_id
    distinct_operator = replica.operator_id != origin.operator_id
    distinct_site = replica.site_id != origin.site_id
    if distinct_apparatus and distinct_operator and distinct_site:
        return IndependenceLevel.INDEPENDENT_LABORATORY
    if distinct_apparatus and distinct_operator:
        return IndependenceLevel.INDEPENDENT_OPERATOR
    if distinct_apparatus:
        return IndependenceLevel.INDEPENDENT_IMPLEMENTATION
    return IndependenceLevel.RERUN


# --- a replication receipt -----------------------------------------------

@dataclass(frozen=True)
class ReplicationReceipt:
    """One independent replication attempt for an originating residual.

    Records the originating and replicating labs, the frozen protocol hash the
    replica followed, its own residual and combined uncertainty, whether it
    actually ran the ordinary-explanation firewall and whether the residual
    survived it, and the outcome. ``has_raw_artifact`` is required (with a
    ``REAL`` mode) before an attempt could ever be a *physical* replication;
    no such artifact exists in this repository.
    """

    receipt_id: str
    origin: LabIdentity
    replica: LabIdentity
    protocol_hash: str
    mode: ReplicationMode
    residual_magnitude: float
    combined_uncertainty: float
    ran_ordinary_explanation_firewall: bool
    survived_ordinary_explanations: bool
    outcome: ReplicationOutcome
    blinded: bool = False
    independent_calibration: bool = False
    independent_analysis: bool = False
    has_raw_artifact: bool = False
    notes: str = ""

    def __post_init__(self) -> None:
        if not str(self.receipt_id).strip():
            raise ReplicationError("a receipt needs an id")
        if not isinstance(self.origin, LabIdentity) or \
                not isinstance(self.replica, LabIdentity):
            raise ReplicationError(
                f"{self.receipt_id}: origin and replica must be LabIdentity")
        if not str(self.protocol_hash).strip():
            raise ReplicationError(
                f"{self.receipt_id}: a receipt must record the frozen "
                f"protocol hash it followed")
        if not isinstance(self.mode, ReplicationMode):
            raise ReplicationError(
                f"{self.receipt_id}: mode must be a ReplicationMode")
        if not isinstance(self.outcome, ReplicationOutcome):
            raise ReplicationError(
                f"{self.receipt_id}: outcome must be a ReplicationOutcome")
        for name in ("residual_magnitude", "combined_uncertainty"):
            v = float(getattr(self, name))
            if not np.isfinite(v) or v < 0.0:
                raise ReplicationError(
                    f"{self.receipt_id}: {name} must be a finite, "
                    f"non-negative value, got {getattr(self, name)!r}")

    # -- independence --
    def independence_level(self) -> IndependenceLevel:
        return independence_level(self.origin, self.replica)

    def is_independent_of_origin(self) -> bool:
        """True only at ``INDEPENDENT_LABORATORY``: distinct apparatus AND
        site AND operator from the originating lab."""
        return (self.independence_level()
                is IndependenceLevel.INDEPENDENT_LABORATORY)

    # -- the ordinary-explanation firewall --
    def exceeds_uncertainty(self) -> bool:
        """The replica's residual exceeds its own combined uncertainty."""
        return self.residual_magnitude > self.combined_uncertainty

    def passed_firewall(self) -> bool:
        """The replica actually ran the ordinary-explanation attacks AND the
        residual survived them. Skipping the attacks never counts."""
        return bool(self.ran_ordinary_explanation_firewall
                    and self.survived_ordinary_explanations)

    # -- confirmation --
    def is_valid_confirmation(self) -> bool:
        """A confirmation counts only if the outcome is ``CONFIRMS``, the
        residual exceeds the replica's own budget, and it survived the full
        ordinary-explanation firewall it actually ran."""
        return (self.outcome is ReplicationOutcome.CONFIRMS
                and self.exceeds_uncertainty()
                and self.passed_firewall())

    def is_physical_replication(self) -> bool:
        """A physical replication needs a REAL acquisition with a raw
        artifact. No such artifact exists here, so this is always False for
        the synthetic fixtures in this repository."""
        return self.mode.is_physical and self.has_raw_artifact

    def receipt_claim_class(self) -> claims.ClaimClass:
        """The honest class of the receipt itself: a synthetic attempt is a
        ``SYNTHETIC_OBSERVATION``; nothing here is a physical measurement."""
        if self.is_physical_replication():
            return claims.ClaimClass.INDEPENDENT_REPLICATION
        return claims.ClaimClass.SYNTHETIC_OBSERVATION

    def as_dict(self) -> dict:
        return {
            "receipt_id": self.receipt_id,
            "origin": self.origin.as_dict(),
            "replica": self.replica.as_dict(),
            "protocol_hash": self.protocol_hash,
            "mode": self.mode.value,
            "residual_magnitude": float(self.residual_magnitude),
            "combined_uncertainty": float(self.combined_uncertainty),
            "exceeds_uncertainty": self.exceeds_uncertainty(),
            "ran_ordinary_explanation_firewall":
                bool(self.ran_ordinary_explanation_firewall),
            "survived_ordinary_explanations":
                bool(self.survived_ordinary_explanations),
            "passed_firewall": self.passed_firewall(),
            "outcome": self.outcome.value,
            "blinded": bool(self.blinded),
            "independent_calibration": bool(self.independent_calibration),
            "independent_analysis": bool(self.independent_analysis),
            "has_raw_artifact": bool(self.has_raw_artifact),
            "independence_level": self.independence_level().name,
            "is_independent_of_origin": self.is_independent_of_origin(),
            "is_valid_confirmation": self.is_valid_confirmation(),
            "is_physical_replication": self.is_physical_replication(),
            "receipt_claim_class": self.receipt_claim_class().value,
            "notes": self.notes,
        }


# --- the promotion verdict -----------------------------------------------

@dataclass(frozen=True)
class ReplicationVerdict:
    """The claim class an originating residual is entitled to given its
    bundle of replication receipts, and why."""

    claim_class: claims.ClaimClass
    promoted: bool
    independent_confirmations: int
    confirming_receipt_ids: tuple
    total_receipts: int
    failed_receipts: int
    contradicting_receipts: int
    reason: str
    reopening_test: str
    replication_version: str = REPLICATION_VERSION

    def as_dict(self) -> dict:
        return {
            "claim_class": self.claim_class.value,
            "promoted": bool(self.promoted),
            "independent_confirmations": self.independent_confirmations,
            "confirming_receipt_ids": list(self.confirming_receipt_ids),
            "total_receipts": self.total_receipts,
            "failed_receipts": self.failed_receipts,
            "contradicting_receipts": self.contradicting_receipts,
            "min_independent_replications": MIN_INDEPENDENT_REPLICATIONS,
            "reason": self.reason,
            "reopening_test": self.reopening_test,
            "replication_version": self.replication_version,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
            "verdict": VERDICT,
        }


# --- the blinded replication bundle: a hash-chained ledger ---------------

class ReplicationBundle:
    """An append-only, hash-chained bundle of replication receipts for one
    originating residual under one frozen protocol.

    The genesis record is the single-lab residual (the ceiling,
    ``UNEXPLAINED_INSTRUMENT_RESIDUAL``); every appended receipt -- confirming,
    failed, or contradicting -- is chained on top via :mod:`r13.serialize`, so
    no attempt is ever discarded and any tamper breaks
    :meth:`verify` downstream. Epochs are passed in; the bundle never reads a
    clock. Promotion to ``REPLICATED_ANOMALY`` is re-derived from the chained
    receipts by :meth:`verdict`.
    """

    def __init__(self, *, residual_id: str, protocol_hash: str,
                 origin: LabIdentity, epoch,
                 origin_residual_magnitude: float = 0.0,
                 origin_combined_uncertainty: float = 0.0) -> None:
        if not str(residual_id).strip():
            raise ReplicationError("a bundle needs a residual_id")
        if not str(protocol_hash).strip():
            raise ReplicationError(
                "a bundle needs the frozen protocol hash being replicated")
        if not isinstance(origin, LabIdentity):
            raise ReplicationError("origin must be a LabIdentity")
        if epoch is None:
            raise ReplicationError(
                "an epoch must be passed in; the bundle never reads a clock")
        self._residual_id = residual_id
        self._protocol_hash = protocol_hash
        self._origin = origin
        self._receipts: tuple[ReplicationReceipt, ...] = ()
        genesis = {
            "kind": "origin_residual",
            "residual_id": residual_id,
            "protocol_hash": protocol_hash,
            "origin": origin.as_dict(),
            "residual_magnitude": float(origin_residual_magnitude),
            "combined_uncertainty": float(origin_combined_uncertainty),
            "claim_class": RESIDUAL_CEILING.value,
        }
        self._records = serialize.new_chain(
            genesis, epoch, claims.ClaimClass.SOFTWARE_IMPLEMENTED.value)

    # -- identity / chain --
    @property
    def residual_id(self) -> str:
        return self._residual_id

    @property
    def protocol_hash(self) -> str:
        return self._protocol_hash

    @property
    def origin(self) -> LabIdentity:
        return self._origin

    @property
    def receipts(self) -> tuple[ReplicationReceipt, ...]:
        return self._receipts

    @property
    def records(self) -> tuple:
        return self._records

    def __len__(self) -> int:
        return len(self._receipts)

    def tip_hash(self) -> str:
        return self._records[-1].record_hash

    def add_receipt(self, receipt: ReplicationReceipt, epoch) -> None:
        """Append a receipt to the bundle, chaining it on the tip.

        Every attempt is preserved -- failed and contradicting replications
        are recorded, not dropped. A receipt that followed a *different*
        protocol hash, or that names an origin different from the bundle's, is
        still chained (for the record) but can never count toward promotion.
        """
        if not isinstance(receipt, ReplicationReceipt):
            raise ReplicationError("can only add a ReplicationReceipt")
        if epoch is None:
            raise ReplicationError(
                "an epoch must be passed in; the bundle never reads a clock")
        self._records = serialize.append_record(
            self._records, receipt.as_dict(), epoch,
            receipt.receipt_claim_class().value)
        self._receipts = self._receipts + (receipt,)

    def verify(self) -> bool:
        """Recompute every hash and back-link; False if any record tampered."""
        return serialize.verify_chain(self._records)

    def verify_report(self) -> dict:
        return serialize.verify_chain_report(self._records)

    # -- promotion --
    def _counts_toward_promotion(self, receipt: ReplicationReceipt) -> bool:
        """A receipt counts only if it followed this bundle's frozen protocol,
        is independent of the origin, and is a valid firewall-surviving
        confirmation."""
        return (receipt.protocol_hash == self._protocol_hash
                and receipt.origin == self._origin
                and receipt.is_independent_of_origin()
                and receipt.is_valid_confirmation())

    def _mutually_independent_confirmations(
            self) -> tuple[ReplicationReceipt, ...]:
        """A deterministic, mutually independent set of counting receipts.

        Two confirmations that share an operator, apparatus, or site are not
        independent of each other -- a same-lab re-run is a ``RERUN``, not a
        second replication -- so only one of them counts. Selection is greedy
        over ``receipt_id`` order, so the count is reproducible.
        """
        used_operators: set = set()
        used_apparatus: set = set()
        used_sites: set = set()
        selected: list = []
        for r in sorted((r for r in self._receipts
                         if self._counts_toward_promotion(r)),
                        key=lambda r: r.receipt_id):
            rep = r.replica
            if (rep.operator_id in used_operators
                    or rep.apparatus_id in used_apparatus
                    or rep.site_id in used_sites):
                continue
            used_operators.add(rep.operator_id)
            used_apparatus.add(rep.apparatus_id)
            used_sites.add(rep.site_id)
            selected.append(r)
        return tuple(selected)

    def independent_confirmations(self) -> int:
        return len(self._mutually_independent_confirmations())

    def verdict(self) -> ReplicationVerdict:
        """Type the originating residual given its bundle of receipts.

        ``REPLICATED_ANOMALY`` requires at least
        :data:`MIN_INDEPENDENT_REPLICATIONS` mutually independent confirming
        replications, each following the frozen protocol and surviving the
        firewall. Anything short of that stays at the
        ``UNEXPLAINED_INSTRUMENT_RESIDUAL`` ceiling.
        """
        confirming = self._mutually_independent_confirmations()
        n = len(confirming)
        failed = sum(1 for r in self._receipts
                     if r.outcome is ReplicationOutcome.FAILS_TO_CONFIRM)
        contradicting = sum(1 for r in self._receipts
                            if r.outcome is ReplicationOutcome.CONTRADICTS)
        ids = tuple(r.receipt_id for r in confirming)

        if n >= MIN_INDEPENDENT_REPLICATIONS:
            return ReplicationVerdict(
                claim_class=REPLICATED_CLASS,
                promoted=True,
                independent_confirmations=n,
                confirming_receipt_ids=ids,
                total_receipts=len(self._receipts),
                failed_receipts=failed,
                contradicting_receipts=contradicting,
                reason=(
                    f"{n} mutually independent replications (distinct "
                    f"operator, apparatus, and site) each followed the frozen "
                    f"protocol {self._protocol_hash[:12]}..., produced a "
                    f"residual exceeding their own budget, and survived the "
                    f"full ordinary-explanation firewall: {list(ids)}. The "
                    f"residual is a REPLICATED_ANOMALY -- a replicated "
                    f"unexplained effect, not new physics."),
                reopening_test=_reopening_test(REPLICATED_CLASS),
            )
        return ReplicationVerdict(
            claim_class=RESIDUAL_CEILING,
            promoted=False,
            independent_confirmations=n,
            confirming_receipt_ids=ids,
            total_receipts=len(self._receipts),
            failed_receipts=failed,
            contradicting_receipts=contradicting,
            reason=(
                f"only {n} genuinely independent confirming replication(s); "
                f"{MIN_INDEPENDENT_REPLICATIONS} are required. A single "
                f"laboratory's residual -- however many times it re-runs -- "
                f"stays at the UNEXPLAINED_INSTRUMENT_RESIDUAL ceiling and is "
                f"never new physics."),
            reopening_test=_reopening_test(RESIDUAL_CEILING),
        )

    def as_dict(self) -> dict:
        return {
            "residual_id": self._residual_id,
            "protocol_hash": self._protocol_hash,
            "origin": self._origin.as_dict(),
            "receipts": [r.as_dict() for r in self._receipts],
            "chain_length": len(self._records),
            "chain_verifies": self.verify(),
            "verdict": self.verdict().as_dict(),
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


# --- reopening tests ------------------------------------------------------

def _reopening_test(claim_class: claims.ClaimClass) -> str:
    if claim_class is REPLICATED_CLASS:
        return ("Reopen if any contributing replication is retracted, found "
                "non-independent (a shared operator, apparatus, or site), or "
                "found to have skipped the ordinary-explanation firewall, "
                f"dropping the mutually independent confirming count below "
                f"{MIN_INDEPENDENT_REPLICATIONS}.")
    return ("Reopen ONLY via at least "
            f"{MIN_INDEPENDENT_REPLICATIONS} mutually independent "
            "replications -- distinct operator AND apparatus AND site, "
            "distinct from the origin and from each other -- each following "
            "the frozen protocol hash, producing a residual that exceeds its "
            "own error budget, and surviving the full ordinary-explanation "
            "firewall. A same-lab re-run or a reanalysis of the same data "
            "cannot reopen this, and it is never new physics.")


# --- the load-bearing refusals -------------------------------------------

def refuse_same_lab_as_independent(origin: LabIdentity | None = None,
                                   replica: LabIdentity | None = None) -> None:
    """Refuse to treat a same-lab re-run as an independent replication.

    Independence requires a distinct operator AND apparatus AND site. A re-run
    on the same setup -- or a reanalysis of the same data -- is a ``RERUN``,
    not a replication, and cannot count toward promotion. Always raises.
    """
    level = (independence_level(origin, replica)
             if origin is not None and replica is not None else None)
    raise ReplicationError(
        "refused: a re-run on the same operator/apparatus/site is not an "
        "independent replication; genuine independence requires a distinct "
        "operator AND apparatus AND site (INDEPENDENT_LABORATORY)"
        + (f" (this pair is {level.name})" if level is not None else "")
        + ". A same-setup re-run is a RERUN and cannot promote a residual.")


def refuse_promotion_without_replication(
        independent_confirmations: int = 0) -> None:
    """Refuse to promote a single-lab residual to a replicated anomaly.

    An ``UNEXPLAINED_INSTRUMENT_RESIDUAL`` becomes a ``REPLICATED_ANOMALY``
    only with at least :data:`MIN_INDEPENDENT_REPLICATIONS` mutually
    independent confirming replications. One lab, or one run, cannot do it.
    Always raises.
    """
    raise ReplicationError(
        f"refused: a single laboratory's residual cannot be promoted to "
        f"REPLICATED_ANOMALY; {MIN_INDEPENDENT_REPLICATIONS} mutually "
        f"independent confirming replications are required and "
        f"{independent_confirmations} is present. Without them the residual "
        f"stays at the UNEXPLAINED_INSTRUMENT_RESIDUAL ceiling.")


def refuse_confirmation_bias(receipt: ReplicationReceipt | None = None) -> None:
    """Refuse to count a replication that skipped the firewall.

    A replication that did not actually run the ordinary-explanation attacks
    (or whose residual did not survive them, or did not exceed its own budget)
    is not a confirmation, no matter what outcome it declares. Counting it
    would be confirmation bias. Always raises.
    """
    detail = ""
    if receipt is not None:
        detail = (f" (receipt {receipt.receipt_id!r}: "
                  f"ran_firewall={receipt.ran_ordinary_explanation_firewall}, "
                  f"survived={receipt.survived_ordinary_explanations}, "
                  f"exceeds_uncertainty={receipt.exceeds_uncertainty()})")
    raise ReplicationError(
        "refused: a replication that skipped the ordinary-explanation "
        "firewall -- or whose residual did not survive it or did not exceed "
        "its own error budget -- is not a confirmation and does not count"
        + detail + ". Accepting it would be confirmation bias.")


def refuse_reanalysis_as_replication() -> None:
    """Refuse to treat a reanalysis of the same data as a replication.

    Re-running the same code on the same recorded data is a ``RERUN`` -- it
    reproduces the analysis, not the phenomenon. Replication requires a new,
    independent acquisition on a distinct apparatus, operator, and site.
    Always raises.
    """
    raise ReplicationError(
        "refused: reanalysis is not replication. Re-running the same code on "
        "the same data reproduces an analysis, not the phenomenon; it is a "
        "RERUN. Replication requires an independent acquisition on a distinct "
        "operator, apparatus, and site.")


def refuse_residual_as_new_physics(*_a, **_k) -> None:
    """A replicated anomaly is still not new physics. Always raises.

    Delegates to the governance core so the text stays single-sourced, but
    raises a :class:`ReplicationError` for this lane.
    """
    try:
        claims.refuse_residual_as_new_physics()
    except claims.ClaimError as exc:
        raise ReplicationError(str(exc)) from exc


#: Reused from the governance core: there is no PHRYLL_DETECTED state, even
#: for a replicated anomaly.
refuse_phryll_detected = claims.refuse_phryll_detected


#: The refusals this module enforces, indexed for the red team.
REPLICATION_REFUSALS = {
    "same_lab_as_independent": refuse_same_lab_as_independent,
    "promotion_without_replication": refuse_promotion_without_replication,
    "confirmation_bias": refuse_confirmation_bias,
    "reanalysis_as_replication": refuse_reanalysis_as_replication,
    "residual_to_new_physics": refuse_residual_as_new_physics,
    "phryll_detected": refuse_phryll_detected,
}


# --- report ---------------------------------------------------------------

def replication_report() -> dict:
    """The standing statement of what the receipting layer is and is not."""
    return {
        "what_this_is": (
            "the R15 independent-replication receipting layer: it types "
            "replication receipts (originating and replicating lab, the frozen "
            "protocol hash followed, the replica's own residual and error "
            "budget, its ordinary-explanation firewall pass, and its outcome) "
            "and, from a hash-chained bundle of them, decides whether a "
            "single-lab UNEXPLAINED_INSTRUMENT_RESIDUAL may be promoted to a "
            "REPLICATED_ANOMALY. It is the only path off the single-lab "
            "ceiling"),
        "independence_levels": [lvl.name for lvl in IndependenceLevel],
        "modes": [m.value for m in ReplicationMode],
        "outcomes": [o.value for o in ReplicationOutcome],
        "residual_ceiling": RESIDUAL_CEILING.value,
        "replicated_class": REPLICATED_CLASS.value,
        "min_independent_replications": MIN_INDEPENDENT_REPLICATIONS,
        "replication_version": REPLICATION_VERSION,
        "refusals": list(REPLICATION_REFUSALS),
        "has_phryll_detected_state": False,
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "rules": [
            "rerun, independent implementation, independent operator, and "
            "independent laboratory are distinct levels; only "
            "INDEPENDENT_LABORATORY (distinct operator AND apparatus AND site) "
            "is genuine independence",
            "reanalysis of the same data is a RERUN, not a replication",
            "a confirmation counts only if it followed the frozen protocol, "
            "exceeded its own error budget, and survived the "
            "ordinary-explanation firewall it actually ran",
            "two confirmations sharing an operator, apparatus, or site are not "
            "mutually independent; only one counts",
            "REPLICATED_ANOMALY requires at least "
            f"{MIN_INDEPENDENT_REPLICATIONS} mutually independent confirming "
            "replications; a single lab cannot reach it",
            "failed and contradicting replications are preserved in the "
            "hash-chained bundle, never discarded",
            "a REPLICATED_ANOMALY is still not new physics and there is no "
            "PHRYLL_DETECTED state",
        ],
        "what_would_change_this": (
            "at least "
            f"{MIN_INDEPENDENT_REPLICATIONS} genuine physical replications on "
            "distinct apparatus, sites, and operators, each with a raw "
            "artifact and a surviving firewall pass -- none of which exists in "
            "this repository, where every receipt is a synthetic fixture"),
        "what_this_does_not_say": (
            "It does not say any residual was physically replicated. Every "
            "receipt here is synthetic; the module types passed-in receipts "
            "and operates no apparatus. Even a REPLICATED_ANOMALY is only a "
            "replicated unexplained effect warranting further study, never a "
            "detection, a resonance, a new particle, a new energy, or new "
            "physics. PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION", "SOFTWARE_CLAIM_CLASS",
    "RESIDUAL_CEILING", "REPLICATED_CLASS", "MIN_INDEPENDENT_REPLICATIONS",
    "REPLICATION_VERSION", "ReplicationError", "ReplicationMode",
    "IndependenceLevel", "ReplicationOutcome", "LabIdentity",
    "independence_level", "ReplicationReceipt", "ReplicationVerdict",
    "ReplicationBundle", "refuse_same_lab_as_independent",
    "refuse_promotion_without_replication", "refuse_confirmation_bias",
    "refuse_reanalysis_as_replication", "refuse_residual_as_new_physics",
    "refuse_phryll_detected", "REPLICATION_REFUSALS", "replication_report",
]
