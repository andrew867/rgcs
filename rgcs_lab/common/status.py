"""UI envelope over the canonical status contract.

The vocabulary (modules, statuses, claim classes, banned public
wording) is defined ONCE in :mod:`rgcs_lab.common.status_schema`
(Claude authority). This module derives from it and adds the
presentation envelope (``ModuleResult``) plus the hub catalog. A
``ModuleResult`` that violates the canonical contract cannot be
constructed: ``__post_init__`` round-trips through ``ModuleStatus``.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from rgcs_lab.common.status_schema import (
    MODULES,
    STATUSES,
    ClaimClass,
    ModuleStatus,
)


class Status(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


assert tuple(s.value for s in Status) == STATUSES, (
    "Status enum must mirror the canonical STATUSES vocabulary")

#: Derived from the canonical ClaimClass enum — never restated by hand.
CLAIM_CLASSES = tuple(c.value for c in ClaimClass)


@dataclass
class ModuleResult:
    """Canonical envelope returned by adapters and the API.

    Construction validates through the shared ``ModuleStatus``
    contract: unknown modules, unknown claim classes, and banned
    public wording in the result payload all raise ``SchemaError``.
    """

    module: str
    status: Status
    claim_class: list[str]
    input: dict[str, Any] = field(default_factory=dict)
    models: list[Any] = field(default_factory=list)
    result: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    receipt: dict[str, Any] = field(default_factory=dict)
    does: str = ""
    does_not: str = ""
    tests: list[str] = field(default_factory=list)
    source: str = ""

    def __post_init__(self) -> None:
        ModuleStatus(
            module=self.module,
            status=Status(self.status).value,
            claim_class=tuple(self.claim_class),
            input=dict(self.input),
            models=tuple(self.models),
            result=dict(self.result),
            warnings=tuple(self.warnings),
            receipt=dict(self.receipt),
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["status"] = self.status.value
        return d


def module_catalog() -> list[dict[str, Any]]:
    """Nine-module hub catalog with standing status badges."""
    catalog = [
        {
            "id": "coordinate",
            "title": "Coordinate",
            "status": Status.GREEN.value,
            "physical_status": Status.YELLOW.value,
            "purpose": "Exact Federation/Terra 30-bit F5|Q22|S3 structural codec.",
            "does_not": "Does not yet establish a unique physical source map.",
            "claim_class": ["EXACT_ARITHMETIC", "TRAINING_EQUALITY", "UNDERDETERMINED"],
        },
        {
            "id": "golay",
            "title": "Golay",
            "status": Status.GREEN.value,
            "physical_status": Status.YELLOW.value,
            "purpose": "Extended binary Golay G24 transport wrapper for a 36-bit address.",
            "does_not": "Does not show that an external civilization uses Golay coding.",
            "claim_class": ["EXACT_ARITHMETIC", "IMPLEMENTED_SOFTWARE"],
        },
        {
            "id": "frames",
            "title": "Frames",
            "status": Status.GREEN.value,
            "physical_status": Status.YELLOW.value,
            "purpose": "Ordered quaternion frame compositions with round-trip checks.",
            "does_not": "Does not demonstrate a physical field effect.",
            "claim_class": ["EXACT_ARITHMETIC", "IMPLEMENTED_SOFTWARE"],
        },
        {
            "id": "memory",
            "title": "Memory",
            "status": Status.GREEN.value,
            "physical_status": Status.YELLOW.value,
            "purpose": "Reproducible provenance-memory retrieval benchmark harness.",
            "does_not": "Does not demonstrate consciousness.",
            "claim_class": ["IMPLEMENTED_SOFTWARE", "EXPLORATORY_MODEL"],
        },
        {
            "id": "dual_pole",
            "title": "Dual-Pole",
            "status": Status.GREEN.value,
            "physical_status": Status.YELLOW.value,
            "purpose": "Proposer/critic research loop with typed attack families.",
            "does_not": "Does not make two models independent witnesses.",
            "claim_class": ["IMPLEMENTED_SOFTWARE", "EXPLORATORY_MODEL"],
        },
        {
            "id": "lattice",
            "title": "Lattice",
            "status": Status.GREEN.value,
            "physical_status": Status.YELLOW.value,
            "purpose": "64-state synthetic resonant lattice with an energy ledger.",
            "does_not": "Does not transport matter.",
            "claim_class": ["IMPLEMENTED_SOFTWARE", "CONVENTIONAL_PHYSICS", "EXPLORATORY_MODEL"],
        },
        {
            "id": "metasurface",
            "title": "Metasurface",
            "status": Status.YELLOW.value,
            "physical_status": Status.YELLOW.value,
            "purpose": "Passive reduced-order spoof-SPP cell with energy accounting.",
            "does_not": "Does not modify gravity.",
            "claim_class": ["IMPLEMENTED_SOFTWARE", "CONVENTIONAL_PHYSICS", "UNDERDETERMINED"],
        },
        {
            "id": "predictions",
            "title": "Predictions",
            "status": Status.YELLOW.value,
            "physical_status": Status.YELLOW.value,
            "purpose": "Freeze prospective predictions and null controls before measurement.",
            "does_not": "Does not validate a mechanism merely because one outcome matches.",
            "claim_class": ["PROSPECTIVE_PREDICTION", "UNDERDETERMINED"],
        },
        {
            "id": "proofs",
            "title": "Proofs",
            "status": Status.GREEN.value,
            "physical_status": Status.YELLOW.value,
            "purpose": "Aggregate receipts, hashes, and claim-boundary audit surface.",
            "does_not": "Does not convert a green UI into a physical proof.",
            "claim_class": ["IMPLEMENTED_SOFTWARE"],
        },
    ]
    assert tuple(c["id"] for c in catalog) == MODULES
    return catalog
