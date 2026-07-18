"""P10 (A64-A70) — HAL memory-layer mapping onto tetrahedral
addresses.

HAL here is the repository's existing Hydrogenuine/HAL memory-bridge
concept (v3 Agent 04): a SYNTHETIC associative memory model, not a
brain interface. R3 maps its records onto the tetrahedral address
codec so recall studies can use the same addressing mathematics —
and puts an authority/privacy/consent gate in front of anything that
could ever hold a person's data.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import ClaimBoundaryError
from .address import decode, encode, parent


@dataclass(frozen=True)
class MemoryRecord:
    """One synthetic record at a tetrahedral address."""
    address_k: int
    depth: int
    payload_class: str            # "SYNTHETIC" only, in this release
    created_epoch_s: float
    consent_ref: str = ""

    def __post_init__(self):
        decode(self.address_k, self.depth)      # validates range
        if self.payload_class != "SYNTHETIC":
            raise ClaimBoundaryError(
                "only SYNTHETIC payloads exist in this release; a "
                "personal-data payload requires the consent gate and "
                "none is implemented")


def partition(records: list, level: int) -> dict:
    """A65: group records by their level-`level` ancestor — retrieval
    narrows by walking the hierarchy, never by scanning everything."""
    groups: dict = {}
    for r in records:
        groups.setdefault(parent(r.address_k, r.depth,
                                 r.depth - level), []).append(r)
    return {"level": level, "n_groups": len(groups),
            "groups": {k: len(v) for k, v in groups.items()}}


def activation(record: MemoryRecord, now_s: float,
               phase_match: float, recency_tau_s: float = 3600.0
               ) -> dict:
    """A66: activation = recency * phase-match, both in [0, 1]. A
    model of retrieval ordering in a synthetic store — not a claim
    about brains."""
    if not (0.0 <= phase_match <= 1.0):
        raise ClaimBoundaryError("phase_match must lie in [0, 1]")
    rec = math.exp(-(now_s - record.created_epoch_s) / recency_tau_s)
    return {"address_k": record.address_k,
            "recency": rec, "phase_match": phase_match,
            "activation": rec * phase_match,
            "claim": "retrieval ordering in a SYNTHETIC store",
            "evidence_class": "NUMERICAL_SIMULATION"}


def consent_audit(records: list) -> dict:
    """A69: the gate that keeps this lane honest. Every record must be
    SYNTHETIC; anything else is refused upstream, so the audit's job
    is to prove the invariant holds."""
    non_synthetic = [r.address_k for r in records
                     if r.payload_class != "SYNTHETIC"]
    return {"n_records": len(records),
            "all_synthetic": not non_synthetic,
            "violations": non_synthetic,
            "policy": "no personal, biometric, or user-derived data "
                      "may enter this store; a future consented lane "
                      "would need explicit consent records, revocation, "
                      "and an erasure path BEFORE any ingestion",
            "evidence_class": "ANALYTIC_MODEL"}
