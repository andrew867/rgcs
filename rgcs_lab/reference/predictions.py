"""Prospective prediction freeze / verify registry."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any


def _canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True)


def _base_body(prediction: dict[str, Any]) -> dict[str, Any]:
    """Strip freeze metadata before hashing."""
    doc = deepcopy(prediction)
    for key in ("freeze_hash", "frozen", "status"):
        doc.pop(key, None)
    return doc


def freeze_prediction(prediction: dict[str, Any]) -> dict[str, Any]:
    """Freeze a prediction document; reject if already measured."""
    if prediction.get("measurement_started") or prediction.get("measured"):
        raise ValueError(
            "refused: a prediction is not editable after measurement begins"
        )
    body = _base_body(prediction)
    classes = list(body.get("claim_class") or [])
    for item in ("PROSPECTIVE_PREDICTION", "UNDERDETERMINED"):
        if item not in classes:
            classes.append(item)
    body["claim_class"] = classes
    digest = hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()
    out = deepcopy(body)
    out["freeze_hash"] = digest
    out["status"] = "YELLOW"
    out["frozen"] = True
    return out


def verify_prediction(prediction: dict[str, Any]) -> dict[str, Any]:
    """Recompute freeze hash and report match without promoting claims."""
    supplied = prediction.get("freeze_hash")
    again = freeze_prediction(prediction)
    match = supplied == again["freeze_hash"]
    return {
        "match": match,
        "supplied_hash": supplied,
        "recomputed_hash": again["freeze_hash"],
        "status": "YELLOW",
        "claim_class": again["claim_class"],
        "note": (
            "A matching hash freezes the protocol; it does not validate a mechanism."
        ),
        "editable_after_measurement": False,
    }
