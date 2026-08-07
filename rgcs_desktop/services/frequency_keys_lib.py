"""Frequency Key Library: keys load from the packaged data file and are
exposed as selectable, sourced, testable records.

Statuses are conservative: *source-language* keys are preserved, not
endorsed; *candidates* are never promoted by numerical coincidence
alone; the single *hardware base* (4096 Hz) carries its published null
result in its own record.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parents[1] / "data" / "frequency_keys.json"

#: match tolerance when looking a key up by value (Hz)
_TOL_HZ = 1e-6


@lru_cache(maxsize=1)
def _load() -> dict:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))


def load_keys() -> list[dict]:
    """All registered keys, ascending by frequency."""
    return sorted(_load()["keys"], key=lambda k: float(k["key_hz"]))


def library_claim_boundary() -> str:
    return str(_load()["claim_boundary"])


def known_key_hz(key_hz: float) -> dict | None:
    """The registered record for a frequency, or None if unregistered."""
    for rec in _load()["keys"]:
        if abs(float(rec["key_hz"]) - float(key_hz)) <= _TOL_HZ:
            return rec
    return None


def custom_key_record(key_hz: float) -> dict:
    """A record for a user-entered key outside the registry. Always
    labelled custom — never silently merged into the registry."""
    return {
        "key_hz": float(key_hz),
        "label": f"custom {key_hz:g} Hz",
        "family": "custom",
        "source_status": "custom",
        "source_ids": [],
        "math_relations": "",
        "audio_role": "user-entered",
        "modulation_role": "user-entered",
        "hardware_role": "",
        "tests": "",
        "null_criteria": "custom key; recorded verbatim with no status",
    }
