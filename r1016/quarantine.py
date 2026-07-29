"""R10.18C — quarantine ledger.

Values that may NEVER appear in a scoring table, a calibration set, a
rule-selection step, or a headline metric. They exist here only so the
exclusion is explicit and testable. If any of these reaches a scoring
path the run is INVALID by definition, not merely degraded.
"""

from __future__ import annotations

QUARANTINED = {
    "165879243": "Montreal raw/direct transport wire - not confirmed",
    "168500683": "Montreal canonical/bridge surface word - not confirmed",
    "168729543": "Montreal superseded transcription",
}

QUARANTINED_FAMILIES = ("MONTREAL_RIGAUD_CONFLICT_FAMILY",)

REASON = ("operator instruction R10.18C: Montreal is not confirmed and "
          "is removed from calibration, scoring, rule selection and "
          "headline metrics")


class QuarantineError(ValueError):
    pass


def assert_clean(values, where: str = "scoring table") -> None:
    """Refuse any collection that contains a quarantined value."""
    hits = [str(v) for v in values if str(v) in QUARANTINED]
    if hits:
        raise QuarantineError(
            f"INVALID RUN: quarantined value(s) {hits} reached the "
            f"{where}. {REASON}")


def is_quarantined(value) -> bool:
    return str(value) in QUARANTINED
