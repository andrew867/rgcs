"""P02 — no-look-ahead and source independence, as a self-report only.

A prospective claim is only as clean as the boundary around what the
operator already knew. If a "prediction" can be contaminated by
information in hand before the session -- a clock already checked, a
search already run, a scene remembered from prior media -- then a later
"hit" proves nothing. This module models that prior-exposure boundary so
a prospective claim can be *guarded*, not decorated.

**"No look-ahead" is only ever a SELF-REPORT unless independently
captured.** It cannot be proven from inside. The operator saying "I did
not look anything up" is a claim by the same party who benefits from it,
and no amount of internal bookkeeping upgrades a self-report to evidence.
The only honest upgrade is external: an independent monitor, a sealed
log, a timestamp captured by someone other than the operator. Absent
that, the verdict is ``NO_LOOKAHEAD_SELF_REPORT`` and it stays there.

So this module refuses two temptations. It refuses to treat a
self-report as proof of no prior exposure
(:func:`refuse_prove_from_self_report`), and it refuses to count a cue
the operator could already have known as a clean prospective hit
(:func:`is_potentially_contaminated`). It also keeps the onset clock
honest: a clock first checked *after* the session began, or a minute
boundary that may already have rolled, widens the timestamp uncertainty
rather than pretending to a precision that was never observed.

Nothing here is measured and nothing physical is claimed. It is an
operator note about epistemic hygiene, recorded so a prospective claim
carries its own contamination caveats.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

#: The maximum extra uncertainty (seconds) a possible minute rollover
#: can add: if the displayed minute may already have ticked over, the
#: true onset could be anywhere in the preceding minute.
MINUTE_ROLLOVER_S = 60.0


class NoLookaheadError(RuntimeError):
    """Raised when a self-report is treated as proof of no prior exposure."""


class Independence(str, Enum):
    """How well the no-look-ahead boundary is actually attested."""

    #: An external monitor / sealed log captured it. The only evidenced case.
    INDEPENDENTLY_CAPTURED = "INDEPENDENTLY_CAPTURED"
    #: The operator's own word. The honest default; not evidence.
    NO_LOOKAHEAD_SELF_REPORT = "NO_LOOKAHEAD_SELF_REPORT"


@dataclass(frozen=True)
class ProvenanceWindow:
    """The prior-exposure boundary around one prospective session.

    Every timestamp is an operator-recorded string (ISO-8601 where
    known). ``independently_captured`` is the one field that, if True,
    means the boundary was attested by something other than the operator.
    """

    session_id: str
    session_onset_local: str
    session_onset_utc: str
    clock_first_checked_utc: str
    minute_rollover_ambiguity: bool = False
    search_start_utc: str = ""            # "" == no search reported
    prior_media_exposure: tuple[str, ...] = ()
    independently_captured: bool = False
    self_report_only: bool = True
    note: str = ""

    @property
    def digest(self) -> str:
        """A stable id for the window's declared contents."""
        payload = "|".join((
            self.session_id, self.session_onset_utc,
            self.clock_first_checked_utc, self.search_start_utc,
            str(self.minute_rollover_ambiguity),
            str(self.independently_captured),
            ";".join(self.prior_media_exposure),
        ))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _parse(ts: str) -> datetime | None:
    """Best-effort ISO-8601 parse; None if not a usable timestamp."""
    if not ts:
        return None
    try:
        dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def classify_independence(window: ProvenanceWindow) -> Independence:
    """External capture is the only thing that clears the self-report bar.

    Returns :attr:`Independence.INDEPENDENTLY_CAPTURED` only when the
    window was attested by something other than the operator; otherwise
    the honest downgrade, :attr:`Independence.NO_LOOKAHEAD_SELF_REPORT`.
    """
    if window.independently_captured:
        return Independence.INDEPENDENTLY_CAPTURED
    return Independence.NO_LOOKAHEAD_SELF_REPORT


def refuse_prove_from_self_report(window: ProvenanceWindow) -> None:
    """A self-report is a claim by the interested party, never a proof.

    Raised when code tries to treat an un-captured no-look-ahead as if it
    established that no prior exposure occurred.
    """
    if window.independently_captured:
        return
    raise NoLookaheadError(
        f"session {window.session_id!r}: no-look-ahead is a SELF-REPORT "
        f"and cannot prove absence of prior exposure. It was not "
        f"independently captured, so it stays a claim by the operator -- "
        f"the same party it favours. Proving no look-ahead needs external "
        f"evidence (an independent monitor, a sealed log, a third-party "
        f"timestamp) that internal bookkeeping cannot supply.")


def is_potentially_contaminated(
    cue_time_utc: str,
    search_start_utc: str,
    prior_media_exposure,
) -> tuple[bool, str]:
    """Could the operator have known this cue before it 'appeared'?

    A cue is potentially contaminated if it appeared *after* a search
    began (it could have been looked up) or if it matches remembered
    prior media (it could have been recalled). Either way it cannot count
    as a clean prospective hit. Returns ``(flag, reason)``.
    """
    media = tuple(prior_media_exposure or ())
    cue = _parse(cue_time_utc)
    search = _parse(search_start_utc)

    if cue is not None and search is not None and cue >= search:
        return (True, (
            f"cue at {cue_time_utc} is at or after search start "
            f"{search_start_utc}; it could have been looked up"))

    cue_norm = (cue_time_utc or "").strip().lower()
    for item in media:
        item_norm = item.strip().lower()
        if item_norm and (item_norm in cue_norm or cue_norm in item_norm):
            return (True, (
                f"cue matches remembered prior media {item!r}; it could "
                f"have been recalled rather than newly observed"))

    return (False, (
        "cue is not after any reported search and matches no remembered "
        "prior media; it is prospective on the evidence given (which does "
        "not itself prove independence)"))


def onset_uncertainty_s(window: ProvenanceWindow) -> float:
    """Seconds of uncertainty on the recorded session onset.

    A clock first checked *after* onset means the onset time was
    reconstructed, not observed: the gap between onset and first check is
    a lower bound on the uncertainty. A possible minute rollover adds up
    to 60 s on top, because the displayed minute may already have ticked.
    """
    seconds = 0.0
    onset = _parse(window.session_onset_utc)
    checked = _parse(window.clock_first_checked_utc)
    if onset is not None and checked is not None and checked > onset:
        seconds += (checked - onset).total_seconds()
    if window.minute_rollover_ambiguity:
        seconds += MINUTE_ROLLOVER_S
    return seconds


def nolookahead_report(window: ProvenanceWindow | None = None) -> dict:
    """Operator note. Measures nothing; claims no physical validation."""
    if window is None:
        window = ProvenanceWindow(
            session_id="SESSION_ALIAS",
            session_onset_local="T0_LOCAL",
            session_onset_utc="",
            clock_first_checked_utc="",
        )
    independence = classify_independence(window)
    return {
        "evidence_class": "OPERATOR_NOTE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "session_id": window.session_id,
        "window_digest": window.digest,
        "independence": independence.value,
        "independently_captured": window.independently_captured,
        "self_report_only": not window.independently_captured,
        "onset_uncertainty_s": onset_uncertainty_s(window),
        "minute_rollover_ambiguity": window.minute_rollover_ambiguity,
        "what_this_does_not_say": (
            "It does not say the operator had no prior exposure, that a "
            "prospective claim is clean, or that no cue was looked up or "
            "recalled. A self-report is a claim by the interested party; "
            "only independent capture is evidence, and none is asserted "
            "here. No timing, no cue, and no prediction is validated."),
        "verdict": independence.value,
    }
