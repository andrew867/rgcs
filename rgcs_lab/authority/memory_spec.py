"""WS04 — provenance-memory benchmark: typed schema and design authority.

Claude owns the SPECIFICATION: the provenance graph types, authority
classes, the equal-budget benchmark design, and the mandatory
ablations. Codex owns the retrieval engines and benchmark runner; this
module is the contract those engines must satisfy, enforced by
construction and by ``tests/rgcs_lab/test_rlab_memory_spec.py``.

Standing non-claims (WS04 spec, verbatim discipline): symbolic
resonance is a RANKING METHOD, not consciousness; agent style
continuity is not self-awareness.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from rgcs_lab.common.status_schema import SchemaError


class MemoryAuthority(str, Enum):
    """Who may read a memory object. PRIVATE objects never enter public
    fixtures, receipts, or benchmark corpora."""

    PUBLIC = "PUBLIC"
    PRIVATE_OPERATOR = "PRIVATE_OPERATOR"


class NodeKind(str, Enum):
    RAW = "RAW"                    # verbatim source chunk
    SUMMARY = "SUMMARY"            # parent summary of children
    ROOT = "ROOT"                  # corpus root


@dataclass(frozen=True)
class MemoryNode:
    """One node of the multiresolution provenance graph.

    Every non-RAW node must name its children: a summary with no
    provenance is refused at construction — that is the entire point
    of a provenance memory.
    """

    node_id: str
    kind: NodeKind
    authority: MemoryAuthority
    text: str
    children: tuple[str, ...] = ()
    resolution_level: int = 0      # 0 = raw, increasing upward

    def __post_init__(self) -> None:
        if self.kind is not NodeKind.RAW and not self.children:
            raise SchemaError(
                f"{self.kind.value} node {self.node_id!r} has no "
                f"children: a summary without provenance is refused.")
        if self.kind is NodeKind.RAW and self.children:
            raise SchemaError("RAW nodes have no children")
        if self.resolution_level < 0:
            raise SchemaError("resolution_level must be >= 0")


#: The retrieval arms every benchmark run MUST include (equal budget).
BENCHMARK_ARMS = ("vector", "lexical", "graph", "hybrid",
                  "hybrid_plus_symbolic_reranker")

#: The mandatory ablations. A benchmark report missing any is invalid.
MANDATORY_ABLATIONS = (
    "no_symbolic_reranker",        # is the RHF-inspired reranker load-bearing?
    "no_graph_edges",              # does provenance structure matter?
    "shuffled_summaries",          # are summaries content or padding?
    "equal_budget_check",          # every arm same token/compute budget
)

#: Metrics every arm reports, with explicit units.
METRICS = (
    ("recall_at_10", "fraction"),
    ("mrr", "dimensionless"),
    ("provenance_depth_hit", "fraction of answers with full raw-chain"),
    ("latency_ms", "milliseconds"),
    ("budget_tokens", "tokens"),
)


def validate_benchmark_report(report: dict) -> dict:
    """A benchmark report is valid only if it covers every arm, every
    mandatory ablation, per-arm equal budgets, and only PUBLIC data."""
    missing_arms = [a for a in BENCHMARK_ARMS
                    if a not in report.get("arms", {})]
    if missing_arms:
        raise SchemaError(f"benchmark report missing arms: {missing_arms}")
    missing_abl = [a for a in MANDATORY_ABLATIONS
                   if a not in report.get("ablations", {})]
    if missing_abl:
        raise SchemaError(
            f"benchmark report missing mandatory ablations: {missing_abl}")
    budgets = {a: report["arms"][a].get("budget_tokens")
               for a in BENCHMARK_ARMS}
    if len(set(budgets.values())) != 1 or None in budgets.values():
        raise SchemaError(
            f"unequal or undeclared budgets across arms: {budgets} — "
            f"an arm that wins with a bigger budget has demonstrated "
            f"its budget, not its method.")
    if report.get("corpus_authority") != MemoryAuthority.PUBLIC.value:
        raise SchemaError(
            "benchmark corpora must be PUBLIC; private operator "
            "material never enters fixtures or receipts.")
    for arm, payload in report["arms"].items():
        for metric, _unit in METRICS:
            if metric not in payload:
                raise SchemaError(
                    f"arm {arm!r} missing metric {metric!r}")
    return {"valid": True, "arms": len(report["arms"]),
            "non_claim": "symbolic resonance is a ranking method, not "
                         "consciousness; style continuity is not "
                         "self-awareness"}
