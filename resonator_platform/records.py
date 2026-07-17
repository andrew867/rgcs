"""Platform records: stable identifiers, the event-sourced ledger, and
the predicted/measured/fitted/accepted separation (R002, R004, R005).

The ledger is append-only in code: `ResonatorLedger.append` is the only
write path, records are deep-frozen on entry, and any attempt to modify
or delete an entry raises. History is the evidence; a platform that can
edit its own past cannot certify anything.
"""

from __future__ import annotations

import copy
import hashlib
import json
import time


class LedgerError(RuntimeError):
    pass


# --- stable identifiers (R002) ------------------------------------------------

ID_KINDS = ("design", "specimen", "fixture", "sweep", "mode",
            "trim_op", "certificate", "session")


def make_id(kind: str, *parts) -> str:
    """Deterministic, content-derived identifier: KIND-<12 hex>.
    Content-derived so re-running the same campaign yields the same
    ids (reproducibility) while distinct content cannot collide in
    any realistic campaign size."""
    if kind not in ID_KINDS:
        raise LedgerError(f"unknown id kind {kind!r}")
    h = hashlib.sha256("|".join(str(p) for p in parts)
                       .encode()).hexdigest()[:12]
    return f"{kind.upper()}-{h}"


# --- frequency-role separation (R005) ------------------------------------------

FREQUENCY_ROLES = ("predicted_hz", "measured_peak_hz", "fitted_hz",
                   "accepted_hz")


def frequency_record(predicted_hz: float | None = None,
                     measured_peak_hz: float | None = None,
                     fitted_hz: float | None = None,
                     accepted_hz: float | None = None,
                     fitted_uncertainty_hz: float | None = None
                     ) -> dict:
    """The four roles are distinct fields, never one number:

    - predicted:  from the model, before any measurement
    - measured:   the raw sweep peak (grid-quantized)
    - fitted:     the line-shape fit with uncertainty
    - accepted:   set ONLY by an acceptance decision against the
                  preregistered band; requires a fitted value

    A caller cannot 'accept' a prediction: accepted without fitted
    raises."""
    if accepted_hz is not None and fitted_hz is None:
        raise LedgerError("accepted_hz requires a fitted_hz — a "
                          "prediction cannot be accepted")
    if fitted_hz is not None and fitted_uncertainty_hz is None:
        raise LedgerError("fitted_hz requires "
                          "fitted_uncertainty_hz")
    return {"predicted_hz": predicted_hz,
            "measured_peak_hz": measured_peak_hz,
            "fitted_hz": fitted_hz,
            "fitted_uncertainty_hz": fitted_uncertainty_hz,
            "accepted_hz": accepted_hz,
            "roles_are_distinct": True}


# --- event-sourced ledger (R004) -----------------------------------------------

class ResonatorLedger:
    """Append-only event ledger with hash chaining.

    Every event carries: sequence, monotonic logical time, event type,
    payload, synthetic flag, and the hash of the previous event —
    so any later edit breaks the chain and is detected by verify()."""

    def __init__(self, synthetic: bool = True):
        self._events: list[dict] = []
        self._seq = 0
        # the platform has never touched hardware; synthetic is the
        # only legal value today and the flag is per-ledger AND
        # per-event so it survives export
        self.synthetic = bool(synthetic)

    def append(self, event_type: str, payload: dict) -> dict:
        prev = self._events[-1]["event_hash"] if self._events else "0"
        event = {
            "seq": self._seq,
            "logical_time": time.monotonic_ns(),
            "event_type": event_type,
            "payload": copy.deepcopy(payload),
            "synthetic": self.synthetic,
            "prev_hash": prev,
        }
        event["event_hash"] = hashlib.sha256(
            json.dumps({k: v for k, v in event.items()
                        if k != "event_hash"},
                       sort_keys=True, default=str).encode()
        ).hexdigest()
        self._events.append(event)
        self._seq += 1
        return copy.deepcopy(event)

    def __len__(self):
        return len(self._events)

    def events(self, event_type: str | None = None) -> list:
        """Read-only deep copies; the internal list is never handed
        out."""
        evs = [e for e in self._events
               if event_type is None or e["event_type"] == event_type]
        return copy.deepcopy(evs)

    def verify(self) -> dict:
        """Recompute the hash chain; any tamper breaks it."""
        prev = "0"
        for e in self._events:
            if e["prev_hash"] != prev:
                return {"intact": False, "broken_at": e["seq"],
                        "reason": "prev_hash mismatch"}
            recomputed = hashlib.sha256(
                json.dumps({k: v for k, v in e.items()
                            if k != "event_hash"},
                           sort_keys=True, default=str).encode()
            ).hexdigest()
            if recomputed != e["event_hash"]:
                return {"intact": False, "broken_at": e["seq"],
                        "reason": "event content altered"}
            prev = e["event_hash"]
        return {"intact": True, "n_events": len(self._events)}

    # deletion and mutation are not part of the API, and the obvious
    # attempts fail loudly rather than silently no-op
    def __delitem__(self, *_):
        raise LedgerError("ledger events cannot be deleted")

    def __setitem__(self, *_):
        raise LedgerError("ledger events cannot be modified")

    def export(self) -> str:
        return json.dumps({"synthetic": self.synthetic,
                           "events": self._events}, indent=2,
                          default=str)


# --- lifecycle state machine (R001) ---------------------------------------------

class Lifecycle:
    """State machine over LIFECYCLE_STATES with the ledger recording
    every transition. Illegal transitions raise; there is no force
    flag."""

    def __init__(self, ledger: ResonatorLedger, specimen_id: str):
        from . import LIFECYCLE_STATES, LIFECYCLE_TRANSITIONS
        self._states = LIFECYCLE_STATES
        self._trans = LIFECYCLE_TRANSITIONS
        self.ledger = ledger
        self.specimen_id = specimen_id
        self.state = "DESIGNED"
        ledger.append("lifecycle", {"specimen_id": specimen_id,
                                    "state": self.state,
                                    "from": None})

    def to(self, new_state: str, **context) -> str:
        if new_state not in self._states:
            raise LedgerError(f"unknown state {new_state}")
        if new_state not in self._trans[self.state]:
            raise LedgerError(
                f"illegal transition {self.state} -> {new_state}; "
                f"legal: {sorted(self._trans[self.state])}")
        self.ledger.append("lifecycle", {
            "specimen_id": self.specimen_id, "from": self.state,
            "state": new_state, **context})
        self.state = new_state
        return new_state
