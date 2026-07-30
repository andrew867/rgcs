"""R10.9 private vector registry V2 (Phase 7).

Every known wire value with role, status, provenance, and firewalls:
superseded records preserved; corrupted session records excluded from
fitting; the frozen blind holdout locked against retuning. Labels on
records marked ``*_not_for_fit`` or holdouts never enter calibration.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

from r109.types import WireAddress


@dataclass(frozen=True)
class VectorRecord:
    raw: int
    role: str
    label: str | None
    status: str
    evidence_class: str
    fit_allowed: bool
    notes: str = ""

    def to_dict(self) -> dict:
        d = asdict(self)
        wire = WireAddress.from_raw(self.raw, provenance_id=f"r109:{self.raw}")
        d["octal"] = wire.octal
        d["octal_depth"] = wire.octal_depth
        d["decimal_terminal_digit"] = wire.decimal_terminal_marker.digit
        return d


REGISTRY_V2: tuple[VectorRecord, ...] = (
    VectorRecord(165876523, "compact_training_anchor", "Stonehenge",
                 "CURRENT", "SOURCE_REPORTED", True,
                 "fixed compact form; training equality; V2 calibration anchor"),
    VectorRecord(1643789253, "refined_training_anchor", "Stonehenge",
                 "CURRENT_T11_UNRESOLVED", "SOURCE_REPORTED", False,
                 "same physical address as 165876523 at higher precision; "
                 "T11 interleave unresolved — parent-child constraint only"),
    VectorRecord(167849523, "compact_training_anchor", "Erie",
                 "CURRENT", "SOURCE_REPORTED", True,
                 "V2 calibration anchor"),
    VectorRecord(165879243, "compact_training_anchor", "Montreal",
                 "CORRECTED_CURRENT_DIRECT", "SOURCE_REPORTED", True,
                 "DIRECT compact packet (R109-MTL-01); replaces the affine "
                 "bridge target 168500683 and the superseded transcription"),
    VectorRecord(168729543, "historical_record",
                 "Montreal superseded transcription",
                 "SUPERSEDED", "SUPERSEDED", False,
                 "preserved provenance; never a current anchor"),
    VectorRecord(168500683, "historical_record",
                 "Montreal affine-bridge target (stale)",
                 "SUPERSEDED", "SUPERSEDED", False,
                 "output of the superseded general affine bridge; retained "
                 "in the superseded-model ledger only"),
    VectorRecord(168930443, "compact_training_anchor", "Toronto",
                 "SOURCE_CONFIRMED", "SOURCE_REPORTED", True,
                 "V2 calibration anchor"),
    VectorRecord(1672875493, "refined_training_anchor", "Toronto",
                 "CURRENT_T11_UNRESOLVED", "SOURCE_REPORTED", False,
                 "same physical address as 168930443 at higher precision"),
    VectorRecord(1658274383, "labelled_record_not_for_fit", "CYYT St. John's",
                 "T11_UNRESOLVED", "SOURCE_REPORTED", False,
                 "Newfoundland record — excluded from warp fitting by "
                 "R109-HLD-01"),
    VectorRecord(1658792343, "corrupted_session_record",
                 "Gander/Argentia collision",
                 "DO_NOT_FIT_REACQUIRE", "UNRESOLVED", False,
                 "corrupted transcription session; reacquire from source; "
                 "never fitted"),
    VectorRecord(167854923, "frozen_blind_holdout", None,
                 "DO_NOT_RETUNE", "HOLDOUT_RESULT", False,
                 "frozen blind holdout with existing V1 blind receipt and "
                 "candidate Ohio output; V2 is never moved to change it"),
)

_BY_RAW = {r.raw: r for r in REGISTRY_V2}


class RegistryError(ValueError):
    pass


def record(raw: int) -> VectorRecord:
    try:
        return _BY_RAW[raw]
    except KeyError:
        raise RegistryError(f"vector {raw} is not in registry V2") from None


def fit_anchors() -> tuple[VectorRecord, ...]:
    """Exactly the records calibration may use."""
    return tuple(r for r in REGISTRY_V2 if r.fit_allowed)


def assert_fit_allowed(raw: int) -> VectorRecord:
    r = record(raw)
    if not r.fit_allowed:
        raise RegistryError(
            f"refused: {raw} ({r.label or r.role}, status {r.status}) is "
            f"not a permitted calibration input")
    return r


def registry_dict() -> dict:
    return {
        "schema": "rgcs.r109.vector-registry.v2",
        "records": [r.to_dict() for r in REGISTRY_V2],
        "fit_anchor_count": len(fit_anchors()),
    }
