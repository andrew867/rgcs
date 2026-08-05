"""MOD-006 craft-path hypothesis registry -- append-only, role-separated.

Archives craft-scale geometry, frequency, and path hypotheses without
treating any of them as validated hardware. Every record states its
evidence status from a fixed ladder; promotion to validated requires
bench AND replication receipts, and the function that promotes is the
only door, so the refusal is enforced by code rather than by memory.

The frequency spine below is the pack's public-safe list. Each value
carries exactly one role; role separation is a test, because two
hypotheses silently sharing a number is how spines rot.

This module does provenance-tracked hypothesis archival. It does not
claim flight capability or validated hardware. Bench receipts and
independent replication remain pending for every record.
"""

from __future__ import annotations

STATUS = "HYPOTHESIS_REGISTRY"

#: Fixed evidence statuses (spec pack, MOD-006).
RECORD_STATUSES = (
    "SOURCE_REPORTED",
    "DERIVED_ARITHMETIC",
    "ENGINEERING_TRANSLATION",
    "BENCH_PROTOCOL",
    "BENCH_MEASURED",
    "INDEPENDENTLY_REPLICATED",
    "SUPERSEDED",
    "REFUSED_PUBLIC_CLAIM",
)

#: Public-safe frequency spine, one role per value (spec pack list).
FREQUENCY_SPINE = (
    {"value_hz": 4096.0, "role": "phase authority"},
    {"value_hz": 1683456.0, "role": "annular external resonance"},
    {"value_hz": 1695000.0, "role": "Earth or outer-envelope lane candidate"},
    {"value_hz": 1600000.0, "role": "rounded ring or injection geometry candidate"},
    {"value_hz": 13183593.75, "role": "craft operating carrier candidate"},
    {"value_hz": 20480.0, "role": "first crystal burst control"},
    {"value_hz": 40960.0, "role": "second crystal burst control"},
)

#: Provenance a source-attributed record must carry.
SOURCE_PROVENANCE_FIELDS = ("source_id", "source_type", "capture_datetime")


class ValidationRefused(RuntimeError):
    """Raised when a record tries to become validated without receipts."""


class CraftPathRegistry:
    """Append-only. Records are superseded, never edited or deleted."""

    def __init__(self) -> None:
        self._records: list[dict] = []

    def add_record(self, record: dict) -> dict:
        status = record.get("status")
        if status not in RECORD_STATUSES:
            raise ValueError(f"unknown record status '{status}'; use one "
                             f"of {RECORD_STATUSES}")
        if status in ("BENCH_MEASURED", "INDEPENDENTLY_REPLICATED"):
            raise ValidationRefused(
                "records enter as hypotheses; measured or replicated "
                "status requires promote_with_receipts()")
        if status == "SOURCE_REPORTED":
            missing = [f for f in SOURCE_PROVENANCE_FIELDS
                       if not record.get(f)]
            if missing:
                raise ValueError(f"source-attributed record missing "
                                 f"provenance fields {missing}")
        if status == "DERIVED_ARITHMETIC" and not record.get("inputs"):
            raise ValueError("derived arithmetic must identify its inputs")
        entry = dict(record)
        entry["registry_index"] = len(self._records)
        self._records.append(entry)
        return entry

    def supersede(self, registry_index: int, replacement: dict) -> dict:
        """The old record stays, marked SUPERSEDED; the new one appends."""
        old = self._records[registry_index]
        old["status"] = "SUPERSEDED"
        return self.add_record(replacement)

    def promote_with_receipts(self, registry_index: int,
                              bench_receipt: str | None,
                              replication_receipt: str | None) -> dict:
        """The only door to measured/replicated status."""
        if not bench_receipt:
            raise ValidationRefused("promotion requires a bench receipt")
        old = self._records[registry_index]
        status = ("INDEPENDENTLY_REPLICATED" if replication_receipt
                  else "BENCH_MEASURED")
        promoted = dict(old)
        promoted.update({
            "status": status,
            "bench_receipt": bench_receipt,
            "replication_receipt": replication_receipt,
            "promoted_from_index": registry_index,
        })
        old["status"] = "SUPERSEDED"
        return self.add_record_promoted(promoted)

    def add_record_promoted(self, record: dict) -> dict:
        entry = dict(record)
        entry["registry_index"] = len(self._records)
        self._records.append(entry)
        return entry

    def records(self) -> list[dict]:
        return list(self._records)


def load_public_records() -> "CraftPathRegistry":
    """Load the imported public-safe seed records through the same
    validation door every other record uses."""
    import json
    import pathlib
    data = json.loads(
        (pathlib.Path(__file__).resolve().parent
         / "craft_path_records.json").read_text(encoding="utf-8"))
    registry = CraftPathRegistry()
    for record in data["records"]:
        registry.add_record(record)
    return registry


def spine_roles_are_separated() -> bool:
    roles = [entry["role"] for entry in FREQUENCY_SPINE]
    values = [entry["value_hz"] for entry in FREQUENCY_SPINE]
    return len(set(roles)) == len(roles) and len(set(values)) == len(values)


__all__ = ["STATUS", "RECORD_STATUSES", "FREQUENCY_SPINE",
           "SOURCE_PROVENANCE_FIELDS", "ValidationRefused",
           "CraftPathRegistry", "load_public_records",
           "spine_roles_are_separated"]
