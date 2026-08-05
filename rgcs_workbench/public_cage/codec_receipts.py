"""MOD-001 parse receipts over the rgcs_coordinate variable-length codec.

Wraps ``rgcs_coordinate.codecs.variable_length_36`` into the receipt
shape the spec pack requires: raw decimal, transport profile, binary
payload, octal stream, candidate field split with bit boundaries,
legal parse status, round-trip value, profile name, and a receipt
hash. A rejected parse gets a receipt too, with the exact reason --
rejection without a reason is the failure mode this module exists to
prevent.

The correction ledger is append-only. A corrected vector never
overwrites the raw vector; both stay, and the raw one is marked
superseded but remains readable.

This module does structural parse receipts. It does not claim a
physical or geographic endpoint for any vector. Endpoint
interpretation remains pending.
"""

from __future__ import annotations

import hashlib
import json

from rgcs_coordinate.codecs import variable_length_36 as VL

PROFILE_NAME = VL.CODEC_ID

FRAMING_INFERRED = "INFERRED_VARIABLE"
FRAMING_DIAGNOSTIC = "EXPLICIT_WIDTH_DIAGNOSTIC"

STATUS_LEGAL = "LEGAL_PARSE"
STATUS_REJECTED = "REJECTED"


def _receipt_hash(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _field_boundaries(word) -> dict:
    """Bit offsets from the most significant end, per receipt rules."""
    tail_bits = word.width_bits - VL.FIXED_BITS
    return {
        "root": [0, VL.ROOT_BITS],
        "surface": [VL.ROOT_BITS, VL.ROOT_BITS + VL.SURFACE_BITS],
        "path": [VL.ROOT_BITS + VL.SURFACE_BITS, VL.FIXED_BITS],
        "tail": [VL.FIXED_BITS, word.width_bits],
        "tail_bits": tail_bits,
        "tail_group_bits": VL.GROUP_BITS,
    }


def parse_receipt(value: int, *, width_bits: int | None = None) -> dict:
    """One receipt per vector, legal or rejected, always with a reason."""
    base = {
        "raw_decimal": value if isinstance(value, int) else str(value),
        "transport_profile": ("EXPLICIT_WIDTH" if width_bits is not None
                              else "MINIMAL_WIDTH"),
        "profile_name": PROFILE_NAME,
        "physical_projection_status": "NOT_PERFORMED",
    }
    try:
        word = VL.decode(value, width_bits=width_bits)
    except VL.VariableCodecError as err:
        base.update({
            "legal_parse_status": STATUS_REJECTED,
            "reject_reason": str(err),
        })
        base["receipt_hash"] = _receipt_hash(base)
        return base

    inferred = VL.infer_width(value)
    framing = (FRAMING_DIAGNOSTIC
               if width_bits is not None and width_bits != inferred
               else FRAMING_INFERRED)
    rebuilt = VL.encode(word.root, word.surface, word.path,
                        word.epoch_groups, word.check_group)
    base.update({
        "legal_parse_status": STATUS_LEGAL,
        "binary_payload": word.bits,
        "octal_stream": word.octal,
        "candidate_field_split": {
            "root": word.root,
            "surface": word.surface,
            "path": word.path,
            "epoch_groups": list(word.epoch_groups),
            "check_group": word.check_group,
        },
        "field_boundaries": _field_boundaries(word),
        "framing": framing,
        "round_trip_value": rebuilt.value,
        "round_trip_ok": (rebuilt.value == word.value
                          and rebuilt.width_bits == word.width_bits),
    })
    base["receipt_hash"] = _receipt_hash(base)
    return base


class CorrectionLedger:
    """Append-only raw/corrected vector ledger. Nothing is deleted."""

    def __init__(self) -> None:
        self._entries: list[dict] = []

    def record_raw(self, raw_value: int, note: str = "") -> dict:
        entry = {"kind": "RAW", "value": raw_value, "note": note,
                 "status": "ACTIVE",
                 "receipt": parse_receipt(raw_value)}
        self._entries.append(entry)
        return entry

    def record_correction(self, raw_value: int, corrected_value: int,
                          reason: str) -> dict:
        """The raw entry is marked superseded, never removed or edited
        in value; a correction without a reason is refused."""
        if not reason:
            raise ValueError("a correction requires an explicit reason")
        raw_entries = [e for e in self._entries
                       if e["kind"] == "RAW" and e["value"] == raw_value]
        if not raw_entries:
            raise ValueError("cannot correct a vector that was never "
                             "recorded raw")
        for entry in raw_entries:
            entry["status"] = "SUPERSEDED"
        corrected = {"kind": "CORRECTED", "value": corrected_value,
                     "supersedes": raw_value, "reason": reason,
                     "status": "ACTIVE",
                     "receipt": parse_receipt(corrected_value)}
        self._entries.append(corrected)
        return corrected

    def entries(self) -> list[dict]:
        return list(self._entries)

    def raw_values(self) -> list[int]:
        return [e["value"] for e in self._entries if e["kind"] == "RAW"]


__all__ = ["PROFILE_NAME", "FRAMING_INFERRED", "FRAMING_DIAGNOSTIC",
           "STATUS_LEGAL", "STATUS_REJECTED", "parse_receipt",
           "CorrectionLedger"]
