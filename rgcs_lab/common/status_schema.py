"""Shared status and claim vocabulary — the 01_SHARED contract.

Every module in the program returns a :class:`ModuleStatus`; every UI
badge derives from it (never hand-written); every receipt validates
against ``receipt_schema.json``. Codex and Cursor import this module —
they do not redefine the vocabulary.

Pure stdlib. Deterministic. No network.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from importlib import resources

MODULES = ("coordinate", "golay", "frames", "memory", "dual_pole",
           "lattice", "metasurface", "prediction", "proofs")

STATUSES = ("GREEN", "YELLOW", "RED")


class ClaimClass(str, Enum):
    """The program-wide claim vocabulary (01_SHARED, verbatim)."""

    EXACT_ARITHMETIC = "EXACT_ARITHMETIC"
    IMPLEMENTED_SOFTWARE = "IMPLEMENTED_SOFTWARE"
    CONVENTIONAL_PHYSICS = "CONVENTIONAL_PHYSICS"
    TRAINING_EQUALITY = "TRAINING_EQUALITY"
    SOURCE_REPORTED = "SOURCE_REPORTED"
    EXPLORATORY_MODEL = "EXPLORATORY_MODEL"
    PROSPECTIVE_PREDICTION = "PROSPECTIVE_PREDICTION"
    MEASUREMENT = "MEASUREMENT"
    UNDERDETERMINED = "UNDERDETERMINED"
    FALSIFIED = "FALSIFIED"


#: Public wording allowed / banned (Project Authority Lock, verbatim).
ALLOWED_WORDING = ("candidate", "training equality", "source-reported",
                   "implemented", "reproduced", "conventional prior art",
                   "exploratory", "underdetermined", "falsified under test")
BANNED_WORDING = ("proven source technology", "confirmed anti-gravity",
                  "working spacetime drive",
                  "validated external transmission")


class SchemaError(ValueError):
    """A module status or receipt violates the shared contract."""


@dataclass(frozen=True)
class ModuleStatus:
    """The shared per-module status object (01_SHARED, verbatim keys)."""

    module: str
    status: str
    claim_class: tuple[str, ...]
    input: dict = field(default_factory=dict)
    models: tuple = ()
    result: dict = field(default_factory=dict)
    warnings: tuple[str, ...] = ()
    receipt: dict = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.module not in MODULES:
            raise SchemaError(
                f"unknown module {self.module!r}; the hub shows exactly "
                f"{MODULES}")
        if self.status not in STATUSES:
            raise SchemaError(f"status must be one of {STATUSES}")
        if not self.claim_class:
            raise SchemaError("at least one claim class is required")
        known = {c.value for c in ClaimClass}
        for c in self.claim_class:
            if c not in known:
                raise SchemaError(f"unknown claim class {c!r}")
        text = json.dumps(self.result).lower()
        for banned in BANNED_WORDING:
            if banned in text:
                raise SchemaError(
                    f"banned public wording {banned!r} in result payload "
                    f"(Project Authority Lock)")

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "status": self.status,
            "claim_class": list(self.claim_class),
            "input": dict(self.input),
            "models": list(self.models),
            "result": dict(self.result),
            "warnings": list(self.warnings),
            "receipt": dict(self.receipt),
        }

    def badge_text(self) -> str:
        """UI badge text derives from the schema — never hand-written."""
        return f"{self.module.upper()}: {self.status}"


def receipt_schema() -> dict:
    """The canonical receipt JSON schema (packaged copy of 01_SHARED)."""
    text = (resources.files("rgcs_lab.common")
            / "receipt_schema.json").read_text(encoding="utf-8")
    return json.loads(text)


REQUIRED_RECEIPT_KEYS = ("module", "version", "source_commit", "status",
                         "claim_class", "inputs", "models", "result",
                         "tests")


def validate_receipt(receipt: dict) -> dict:
    """Validate a receipt dict against the shared contract.

    Stdlib-only structural validation of the required keys and enums
    (the full JSON-Schema file ships alongside for external tooling).
    Returns a report; raises SchemaError on violation so a bad receipt
    can never be written silently.
    """
    for key in REQUIRED_RECEIPT_KEYS:
        if key not in receipt:
            raise SchemaError(f"receipt missing required key {key!r}")
    if receipt["status"] not in STATUSES:
        raise SchemaError(f"receipt status must be one of {STATUSES}")
    if not isinstance(receipt["claim_class"], list) or \
            not receipt["claim_class"]:
        raise SchemaError("receipt claim_class must be a non-empty list")
    known = {c.value for c in ClaimClass}
    for c in receipt["claim_class"]:
        if c not in known:
            raise SchemaError(f"unknown claim class {c!r} in receipt")
    if not isinstance(receipt["tests"], list):
        raise SchemaError("receipt tests must be a list")
    return {"valid": True, "module": receipt["module"],
            "status": receipt["status"]}
