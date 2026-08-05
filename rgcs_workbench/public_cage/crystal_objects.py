"""MOD-003 crystal measurement objects -- schema and gating only.

Validators for the public crystal lane: a specimen needs a UUID and a
full measurement context, a transfer measurement needs raw and
processed hashes, computed values carry a computational marker, and a
bench claim without a bench receipt raises. The physics models stay
in the research packages (rgcs_core, rscs2_core); this module holds
the public boundary.

This module does measurement-record validation. It does not claim
healing, consciousness, propulsion, or energy generation effects.
Bench receipts remain pending for every physical hypothesis.

Validation returns problem LISTS, never bare booleans, so every
failure states its reason.
"""

from __future__ import annotations

import uuid

STATUS = "MEASUREMENT_HYPOTHESIS_NOT_VALIDATED"

#: Context every specimen record must carry.
SPECIMEN_REQUIRED_FIELDS = (
    "specimen_id", "material", "mass", "dimensions", "cut_geometry",
    "orientation_estimate", "fixture_description",
)

#: Context every transfer measurement must carry (spec pack list).
MEASUREMENT_REQUIRED_FIELDS = (
    "specimen_id", "drive_frequency", "drive_amplitude", "sensor_type",
    "temperature", "humidity", "clock_source",
    "raw_file_hash", "processed_receipt_hash",
)

COMPUTATIONAL_MARK = "COMPUTATIONAL_MODEL"


class BenchReceiptRequired(RuntimeError):
    """Raised when a bench claim arrives without a bench receipt."""


def _is_uuid(value) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError, TypeError):
        return False


def validate_specimen(record: dict) -> list[str]:
    problems = [f"specimen missing required field '{field}'"
                for field in SPECIMEN_REQUIRED_FIELDS
                if not record.get(field)]
    if record.get("specimen_id") and not _is_uuid(record["specimen_id"]):
        problems.append("specimen_id must be a UUID")
    return problems


def validate_transfer_measurement(record: dict) -> list[str]:
    problems = [f"measurement missing required field '{field}'"
                for field in MEASUREMENT_REQUIRED_FIELDS
                if not record.get(field)]
    if record.get("specimen_id") and not _is_uuid(record["specimen_id"]):
        problems.append("specimen_id must be a UUID")
    for hash_field in ("raw_file_hash", "processed_receipt_hash"):
        value = str(record.get(hash_field, ""))
        if value and len(value) < 32:
            problems.append(f"{hash_field} is too short to be a real "
                            f"content hash")
    return problems


def computed_value(name: str, value, inputs: dict) -> dict:
    """Wrap any computed optical or phase value with its marker and
    its inputs; a computed number with no inputs is refused."""
    if not inputs:
        raise ValueError(f"computed value '{name}' must identify its "
                         f"inputs")
    return {"name": name, "value": value, "inputs": dict(inputs),
            "evidence_class": COMPUTATIONAL_MARK,
            "bench_measured": False}


def bench_claim(statement: str, bench_receipts: list | None) -> dict:
    """A bench claim exists only with at least one bench receipt."""
    if not bench_receipts:
        raise BenchReceiptRequired(
            f"refusing bench claim '{statement}': no bench receipt; "
            f"source language alone cannot promote a physical effect")
    return {"statement": statement,
            "bench_receipts": list(bench_receipts),
            "status": "BENCH_CLAIM_RECORDED",
            "independently_replicated": False}


__all__ = ["STATUS", "SPECIMEN_REQUIRED_FIELDS",
           "MEASUREMENT_REQUIRED_FIELDS", "COMPUTATIONAL_MARK",
           "BenchReceiptRequired", "validate_specimen",
           "validate_transfer_measurement", "computed_value",
           "bench_claim"]
