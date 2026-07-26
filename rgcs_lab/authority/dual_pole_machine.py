"""WS05 — dual-pole research loop: state machine and evidence contract.

The enforceable core of the proposer/critic/reviser/receipt loop:
a typed state machine in which the CRITIC CAN BLOCK promotion, and a
claim ledger in which no claim reaches ``APPROVED`` without evidence
bindings that satisfy its claim class. LLM prompting sits on top of
this machine (Codex/Cursor lanes); the machine itself is
deterministic, so its guarantees are testable without any model.

Authority points (locked here, tested in
``tests/rgcs_lab/test_rlab_dual_pole.py``):

* agreement between agents is NOT independent evidence — a critic
  APPROVE without at least one evidence binding is refused;
* a MEASUREMENT claim requires a receipt-backed binding;
* a blocked claim can only move through REVISION, never straight back
  to APPROVED;
* every transition writes a ledger entry; the ledger is append-only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from rgcs_lab.common.status_schema import ClaimClass, SchemaError


class ClaimState(str, Enum):
    PROPOSED = "PROPOSED"
    UNDER_ATTACK = "UNDER_ATTACK"
    BLOCKED = "BLOCKED"
    IN_REVISION = "IN_REVISION"
    APPROVED = "APPROVED"
    WITHDRAWN = "WITHDRAWN"


#: Legal transitions: (from, actor) -> allowed targets. The critic owns
#: BLOCK/APPROVE; the proposer owns PROPOSE/REVISE/WITHDRAW. There is
#: deliberately NO (BLOCKED -> APPROVED) edge.
TRANSITIONS: dict[tuple[ClaimState, str], tuple[ClaimState, ...]] = {
    (ClaimState.PROPOSED, "critic"): (ClaimState.UNDER_ATTACK,),
    (ClaimState.UNDER_ATTACK, "critic"): (ClaimState.BLOCKED,
                                          ClaimState.APPROVED),
    (ClaimState.BLOCKED, "proposer"): (ClaimState.IN_REVISION,
                                       ClaimState.WITHDRAWN),
    (ClaimState.IN_REVISION, "proposer"): (ClaimState.UNDER_ATTACK,),
    (ClaimState.PROPOSED, "proposer"): (ClaimState.WITHDRAWN,),
}


@dataclass(frozen=True)
class EvidenceBinding:
    """One piece of evidence bound to a claim."""

    kind: str          # RECEIPT | TEST | CITATION | DATASET | DERIVATION
    reference: str     # path, DOI, test id — resolvable, not vibes
    note: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ("RECEIPT", "TEST", "CITATION", "DATASET",
                             "DERIVATION"):
            raise SchemaError(f"unknown evidence kind {self.kind!r}")
        if not self.reference:
            raise SchemaError("evidence binding needs a resolvable "
                              "reference")


@dataclass
class Claim:
    claim_id: str
    text: str
    claim_class: str
    state: ClaimState = ClaimState.PROPOSED
    evidence: list[EvidenceBinding] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.claim_class not in {c.value for c in ClaimClass}:
            raise SchemaError(f"unknown claim class {self.claim_class!r}")


@dataclass(frozen=True)
class LedgerEntry:
    claim_id: str
    actor: str
    from_state: str
    to_state: str
    reason: str


class DualPoleMachine:
    """The enforced loop. One proposer, one critic, append-only ledger."""

    def __init__(self) -> None:
        self._claims: dict[str, Claim] = {}
        self._ledger: list[LedgerEntry] = []

    # -- ledger is append-only; expose copies ---------------------------
    @property
    def ledger(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._ledger)

    def claim(self, claim_id: str) -> Claim:
        try:
            return self._claims[claim_id]
        except KeyError:
            raise SchemaError(f"unknown claim {claim_id!r}") from None

    def propose(self, claim_id: str, text: str, claim_class: str,
                evidence: list[EvidenceBinding] | None = None) -> Claim:
        if claim_id in self._claims:
            raise SchemaError(f"claim {claim_id!r} already exists; "
                              f"revise it, do not re-propose over it")
        c = Claim(claim_id, text, claim_class,
                  evidence=list(evidence or []))
        self._claims[claim_id] = c
        self._ledger.append(LedgerEntry(claim_id, "proposer", "-",
                                        c.state.value, "proposed"))
        return c

    def bind_evidence(self, claim_id: str,
                      binding: EvidenceBinding) -> None:
        self.claim(claim_id).evidence.append(binding)

    def _move(self, claim_id: str, actor: str, target: ClaimState,
              reason: str) -> Claim:
        c = self.claim(claim_id)
        allowed = TRANSITIONS.get((c.state, actor), ())
        if target not in allowed:
            raise SchemaError(
                f"refused: {actor} may not move claim {claim_id!r} "
                f"{c.state.value} -> {target.value}. Legal targets for "
                f"({c.state.value}, {actor}): "
                f"{[t.value for t in allowed] or 'none'}. There is no "
                f"path from BLOCKED to APPROVED except through "
                f"revision and re-attack.")
        if not reason:
            raise SchemaError("every transition requires a reason")
        entry = LedgerEntry(claim_id, actor, c.state.value,
                            target.value, reason)
        c.state = target
        self._ledger.append(entry)
        return c

    # -- the critic's powers --------------------------------------------
    def attack(self, claim_id: str, reason: str) -> Claim:
        return self._move(claim_id, "critic", ClaimState.UNDER_ATTACK,
                          reason)

    def block(self, claim_id: str, reason: str) -> Claim:
        return self._move(claim_id, "critic", ClaimState.BLOCKED, reason)

    def approve(self, claim_id: str, reason: str) -> Claim:
        c = self.claim(claim_id)
        if not c.evidence:
            raise SchemaError(
                f"refused: claim {claim_id!r} has no evidence bindings. "
                f"Critic agreement is not independent evidence; an "
                f"unsupported claim cannot be approved, only blocked.")
        if c.claim_class == ClaimClass.MEASUREMENT.value and \
                not any(b.kind == "RECEIPT" for b in c.evidence):
            raise SchemaError(
                f"refused: MEASUREMENT claim {claim_id!r} requires a "
                f"RECEIPT evidence binding (frozen apparatus/analysis "
                f"receipt), not citations alone.")
        return self._move(claim_id, "critic", ClaimState.APPROVED, reason)

    # -- the proposer's powers ------------------------------------------
    def revise(self, claim_id: str, new_text: str, reason: str) -> Claim:
        c = self._move(claim_id, "proposer", ClaimState.IN_REVISION,
                       reason)
        c.text = new_text
        return c

    def resubmit(self, claim_id: str, reason: str) -> Claim:
        return self._move(claim_id, "proposer", ClaimState.UNDER_ATTACK,
                          reason)

    def withdraw(self, claim_id: str, reason: str) -> Claim:
        return self._move(claim_id, "proposer", ClaimState.WITHDRAWN,
                          reason)

    def receipt(self) -> dict:
        """Machine-readable loop receipt (approvals, blocks, ledger)."""
        states = {c.claim_id: c.state.value
                  for c in self._claims.values()}
        return {
            "claims": states,
            "approved": [k for k, v in states.items()
                         if v == "APPROVED"],
            "blocked": [k for k, v in states.items() if v == "BLOCKED"],
            "ledger": [e.__dict__ for e in self._ledger],
            "authority": "critic approval requires evidence bindings; "
                         "agreement alone is never evidence",
        }
