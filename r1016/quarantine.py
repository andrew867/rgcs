"""R10.18C — quarantine ledger.

Values that may NEVER appear in a scoring table, a calibration set, a
rule-selection step, or a headline metric. They exist here only so the
exclusion is explicit and testable. If any of these reaches a scoring
path the run is INVALID by definition, not merely degraded.
"""

from __future__ import annotations

#: R10.44 OPERATOR LIFT (2026-07-29): the operator states the Montreal
#: issue is resolved and the quarantine is no longer required. Lifting is
#: the operator's call and is honoured here. The values move to
#: RELEASED_BY_OPERATOR and assert_clean() no longer refuses them.
#:
#: The TECHNICAL issue the quarantine was flagging does NOT disappear
#: with it, and is recorded in RELEASED_WITH_NOTE below: the direct wire
#: places Montreal in the Britain macroband (S8 hi5 = 15) when Montreal
#: is physically in North America. Only the canonical form (hi5 = 16)
#: places it correctly.
RELEASED_BY_OPERATOR = {
    "165879243": "direct wire; S8=120 -> hi5=15 = Britain band, but "
                 "Montreal is in North America. Use the canonical form "
                 "for any band-dependent scoring.",
    "168500683": "canonical; S8=130 -> hi5=16 = North America, correct. "
                 "NOTE it is the only recorded product of the superseded "
                 "R10.8 affine, so its band may be a consequence of that "
                 "fit rather than an independent test.",
    "168729543": "superseded transcription; S8=131, P12=2671 differs "
                 "from the other two (3191), so it is a different cell.",
}

_LEGACY_QUARANTINED = {
    "165879243": "Montreal raw/direct transport wire - not confirmed",
    "168500683": "Montreal canonical/bridge surface word - not confirmed",
    "168729543": "Montreal superseded transcription",
}

#: Emptied by the R10.44 operator lift. assert_clean() therefore passes
#: on the Montreal values; the technical note lives in
#: RELEASED_BY_OPERATOR and is not silently discarded.
QUARANTINED: dict = {}

QUARANTINED_FAMILIES = ()

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
