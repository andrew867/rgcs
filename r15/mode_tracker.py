"""P29 — real-time mode tracker.

Follow a resonant mode's frequency as a control parameter (temperature,
drive, orientation) varies, keeping a peak/phase lock and — critically —
staying on the correct branch through an avoided crossing rather than
hopping to the neighbouring mode. The physics of the crossing is taken from
:mod:`r13.avoided` (minimum gap ``2|g|``): two coupled modes never touch
when ``g != 0``, so a tracker that jumps the gap has made a tracking error,
not found a new mode.

Nothing here is measured. The tracked trajectory is computed from a
synthetic sweep and is a ``SYNTHETIC_OBSERVATION``; a lock loss is an
instrument/tracking condition, never a signal, and a branch hop is never a
new mode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13 import avoided as AV
from r15 import claims as C


class ModeTrackerError(RuntimeError):
    """Raised on an illegal promotion of a tracking artifact."""


class TrackStatus(Enum):
    LOCKED = "LOCKED"
    SETTLING = "SETTLING"
    LOCK_LOST = "LOCK_LOST"


VERDICT = "REAL_TIME_MODE_TRACKER_SYNTHETIC_NO_HARDWARE"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"


@dataclass(frozen=True)
class TrackPoint:
    """One tracked step: control value, locked frequency, and lock quality."""

    control: float
    frequency: float
    quality: float
    status: TrackStatus


@dataclass
class ModeTracker:
    """A peak-tracking loop with a bounded search window.

    ``search_hz`` is how far the tracker will look for the peak around its
    predicted frequency; a peak beyond the window is a lock loss, not a jump
    to a far mode. ``quality_floor`` is the minimum normalized peak
    prominence to count as locked.
    """

    search_hz: float = 50.0
    quality_floor: float = 0.25
    track: list[TrackPoint] = field(default_factory=list)

    def _locate(self, freqs: np.ndarray, amp: np.ndarray,
                predicted: float) -> tuple[float, float]:
        """Return (peak frequency, quality) within the search window."""
        lo, hi = predicted - self.search_hz, predicted + self.search_hz
        win = (freqs >= lo) & (freqs <= hi)
        if not np.any(win):
            return predicted, 0.0
        fw, aw = freqs[win], amp[win]
        i = int(np.argmax(aw))
        peak = float(aw[i])
        # quality is the in-window peak relative to the global peak: a real
        # locked peak is ~1, a window holding only noise is ~0 (lock lost).
        global_peak = float(amp.max()) or 1.0
        quality = max(0.0, min(1.0, peak / global_peak))
        return float(fw[i]), float(quality)

    def step(self, control: float, freqs, amp, predicted: float) -> TrackPoint:
        """Track one acquisition; adiabatic — start the search at the last lock."""
        freqs = np.asarray(freqs, dtype=float)
        amp = np.asarray(amp, dtype=float)
        f, q = self._locate(freqs, amp, predicted)
        status = (TrackStatus.LOCKED if q >= self.quality_floor
                  else TrackStatus.LOCK_LOST)
        pt = TrackPoint(control=float(control), frequency=f, quality=q,
                        status=status)
        self.track.append(pt)
        return pt

    def trajectory(self) -> list[float]:
        return [p.frequency for p in self.track]

    def locked_fraction(self) -> float:
        if not self.track:
            return 0.0
        return sum(p.status is TrackStatus.LOCKED
                   for p in self.track) / len(self.track)


def avoided_crossing_branches(control, e1, e2, g):
    """The two adiabatic eigen-branches of a 2x2 avoided crossing.

    ``e1(x)``, ``e2(x)`` are the bare (diabatic) levels vs the control ``x``;
    ``g`` the coupling. Returns (lower, upper) branch arrays whose minimum
    separation is ``2|g|`` (reused from :mod:`r13.avoided`).
    """
    x = np.asarray(control, dtype=float)
    e1 = np.asarray([e1(v) for v in x], dtype=float)
    e2 = np.asarray([e2(v) for v in x], dtype=float)
    mean = 0.5 * (e1 + e2)
    half = 0.5 * (e1 - e2)
    split = np.sqrt(half ** 2 + abs(g) ** 2)
    return mean - split, mean + split


def synthetic_spectrum(center: float, *, fmin: float, fmax: float,
                       n: int = 2048, width: float = 5.0, seed: int = 0):
    """A deterministic Lorentzian peak at ``center`` on a noisy floor."""
    rng = np.random.default_rng(int(seed))
    freqs = np.linspace(fmin, fmax, int(n))
    amp = 1.0 / (1.0 + ((freqs - center) / width) ** 2)
    amp = amp + 0.01 * rng.standard_normal(freqs.size)
    return freqs, amp


def refuse_branch_hop_as_new_mode(*_a, **_k) -> None:
    """A tracker jumping branches at a crossing is an error, not a new mode."""
    raise ModeTrackerError(
        "refused: at an avoided crossing the modes repel by 2|g| and never "
        "touch; a track that hops to the neighbouring branch has made a "
        "tracking error, not discovered a new mode.")


def refuse_lock_loss_as_signal(*_a, **_k) -> None:
    """A lock loss is an instrument condition, not a signal."""
    raise ModeTrackerError(
        "refused: loss of lock (peak outside the search window, quality below "
        "floor) is a tracking/instrument condition, never a physical signal.")


def mode_tracker_report() -> dict:
    return {
        "what_this_is": "a real-time resonant-mode tracker with avoided-"
                        "crossing branch discipline",
        "claim_class": C.ClaimClass.SYNTHETIC_OBSERVATION.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It tracks a mode in a synthetic spectrum; it measures nothing. A "
            "branch hop is not a new mode and a lock loss is not a signal."),
    }
