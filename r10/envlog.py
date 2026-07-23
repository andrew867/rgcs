"""P12 — an environmental signal logger that refuses unsynchronized joins.

The source material wants several environmental channels -- radio-
frequency, mains, magnetic, temperature, acoustic, optical, the
device's own state, and an operator's written annotations -- read
together so that an event in one can be lined up against an event in
another. That is an ordinary data-engineering job: put every stream on
one timebase and interpolate. This module does exactly that and no more.

**The real operation.** Each :class:`Stream` carries its own sample
times (monotonic seconds) and, separately, a ``clock_offset_s`` that
says how far its clock runs ahead of or behind the common reference.
:func:`align` corrects each stream's timestamps by its offset and
resamples every stream onto one regular grid by linear interpolation.
Only the region every stream actually covers is used; the grid is the
*intersection* of the corrected spans.

**The firewall, and it is the point.** You cannot correlate what you
have not time-aligned, and you cannot time-align a stream whose clock
offset is unknown. A stream with ``clock_offset_s is None`` has an
undetermined position on the shared axis, so admitting it into an
alignment would be inventing a synchronization that was never measured.
:func:`refuse_correlation_without_sync` refuses it, and :func:`align`
refuses to extrapolate past the overlapping span -- no value is ever
manufactured outside the interval where a stream was actually sampled.

**The power control.** A refusal is only honest if the machinery could
have succeeded. :func:`cross_correlation` and :func:`lag_of_peak`,
applied to two aligned streams built with a *known* injected lag,
recover that lag to within one grid step. The aligner and correlator
have power; the refusals are choices, not incapacity.

Nothing here is measured. No apparatus exists, no environmental channel
was recorded, and no timebase was established on a bench. The streams
in the tests are synthetic and seeded.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np


class EnvLogError(RuntimeError):
    """Raised when streams are joined without an established common sync."""


class StreamKind(Enum):
    RF = "rf"
    MAINS = "mains"
    MAGNETIC = "magnetic"
    TEMPERATURE = "temperature"
    ACOUSTIC = "acoustic"
    OPTICAL = "optical"
    DEVICE = "device_state"
    OPERATOR = "operator_annotation"


@dataclass
class Stream:
    """One environmental channel as a time series on its own clock.

    ``timestamps`` are monotonic seconds on the stream's *own* clock;
    ``clock_offset_s`` is how far that clock leads the common reference,
    so the corrected time of sample ``i`` is
    ``timestamps[i] - clock_offset_s``. An offset of ``None`` means the
    stream has never been synchronized and cannot enter an alignment.
    """

    name: str
    kind: StreamKind
    timestamps: np.ndarray
    values: np.ndarray
    clock_offset_s: float | None
    unit: str = "arbitrary"

    def __post_init__(self) -> None:
        self.timestamps = np.asarray(self.timestamps, dtype=float)
        self.values = np.asarray(self.values, dtype=float)
        if self.timestamps.shape != self.values.shape:
            raise EnvLogError(
                f"stream {self.name!r}: timestamps and values differ in "
                f"length ({self.timestamps.size} vs {self.values.size})")
        if self.timestamps.size < 2:
            raise EnvLogError(
                f"stream {self.name!r}: need at least two samples to "
                f"interpolate")
        if np.any(np.diff(self.timestamps) <= 0):
            raise EnvLogError(
                f"stream {self.name!r}: timestamps must be strictly "
                f"increasing (monotonic seconds)")

    @property
    def is_synchronized(self) -> bool:
        return self.clock_offset_s is not None

    def corrected_timestamps(self) -> np.ndarray:
        """Timestamps on the common reference clock, offset removed."""
        if self.clock_offset_s is None:
            raise EnvLogError(
                f"stream {self.name!r} has an unknown clock offset; its "
                f"position on the common timebase is undetermined")
        return self.timestamps - float(self.clock_offset_s)


# --- the refusals -------------------------------------------------------

def refuse_correlation_without_sync(streams: list[Stream]) -> None:
    """Refuse to correlate streams whose clock offsets are unknown.

    Correlation is a statement about relative timing, and relative
    timing is meaningless until every stream sits on one axis. A stream
    with ``clock_offset_s is None`` has no established position on that
    axis, so admitting it would be asserting a synchronization that was
    never measured.
    """
    unsynced = [s.name for s in streams if not s.is_synchronized]
    if unsynced:
        raise EnvLogError(
            f"cannot correlate: stream(s) {unsynced!r} have unknown clock "
            f"offsets and have not been time-aligned. You cannot correlate "
            f"what you have not synchronized; an unknown offset is a "
            f"missing measurement, not a zero. Establish each offset first.")


# --- alignment ----------------------------------------------------------

@dataclass(frozen=True)
class Alignment:
    """The result of :func:`align`: a common grid and resampled streams."""

    grid: np.ndarray
    grid_hz: float
    names: tuple[str, ...]
    aligned: dict[str, np.ndarray]
    overlap_start_s: float
    overlap_end_s: float


def align(streams: list[Stream], grid_hz: float) -> Alignment:
    """Resample every stream onto one regular grid by linear interpolation.

    Each stream's timestamps are first corrected by its clock offset.
    The grid spans only the *intersection* of the corrected spans, so no
    value is ever extrapolated beyond where a stream was sampled.
    """
    if not streams:
        raise EnvLogError("no streams to align")
    if grid_hz <= 0:
        raise EnvLogError("grid_hz must be positive")

    refuse_correlation_without_sync(streams)

    spans = [s.corrected_timestamps() for s in streams]
    start = max(float(t[0]) for t in spans)
    end = min(float(t[-1]) for t in spans)
    if not (end > start):
        raise EnvLogError(
            f"streams do not overlap on the common timebase: latest start "
            f"{start:g}s is not before earliest end {end:g}s. There is no "
            f"interval every stream covers, so no honest grid exists.")

    step = 1.0 / float(grid_hz)
    n = int(np.floor((end - start) / step)) + 1
    grid = start + step * np.arange(n)
    # guard against a floating-point straddle of the right edge
    grid = grid[grid <= end + 1e-12]

    aligned: dict[str, np.ndarray] = {}
    for s, t in zip(streams, spans):
        # explicit no-extrapolation guard: the grid is inside every span
        if grid[0] < t[0] - 1e-9 or grid[-1] > t[-1] + 1e-9:
            raise EnvLogError(
                f"stream {s.name!r}: alignment grid would require "
                f"extrapolation beyond the sampled span "
                f"[{t[0]:g}, {t[-1]:g}]s; no value is manufactured "
                f"outside the overlap")
        aligned[s.name] = np.interp(grid, t, s.values)

    return Alignment(
        grid=grid,
        grid_hz=float(grid_hz),
        names=tuple(s.name for s in streams),
        aligned=aligned,
        overlap_start_s=start,
        overlap_end_s=end,
    )


# --- correlation on ALIGNED series --------------------------------------

def cross_correlation(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Full cross-correlation of two ALIGNED, equal-length series.

    Both inputs must already live on the same grid (see :func:`align`).
    Each is mean-removed first so a constant offset does not dominate.
    The returned array has length ``2*N - 1`` and its centre index
    ``N - 1`` is zero lag; see :func:`lag_of_peak`.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    if a.shape != b.shape:
        raise EnvLogError(
            "cross_correlation needs equal-length aligned series; align "
            "the streams onto a common grid first")
    if a.size < 2:
        raise EnvLogError("need at least two aligned samples")
    a = a - a.mean()
    b = b - b.mean()
    return np.correlate(a, b, mode="full")


def lag_of_peak(xcorr: np.ndarray, grid_hz: float) -> tuple[int, float]:
    """Return (lag_in_samples, lag_in_seconds) of the correlation peak.

    A positive lag means the *second* argument of
    :func:`cross_correlation` is delayed relative to the first by that
    many samples: if ``b(t) == a(t - lag)``, the recovered lag is
    positive and equal to that delay.
    """
    xcorr = np.asarray(xcorr)
    n = (xcorr.size + 1) // 2
    lag_samples = (n - 1) - int(np.argmax(xcorr))
    return lag_samples, lag_samples / float(grid_hz)


# --- the power control, as a runnable demonstration ---------------------

def _sync_demo(*, grid_hz: float = 100.0, injected_lag_s: float = 0.37,
               duration_s: float = 4.0, seed: int = 20260723) -> dict:
    """Two synthetic streams with a KNOWN injected lag; recover it.

    Stream B is stream A delayed by ``injected_lag_s``. After align and
    cross-correlation the recovered lag matches the injection to within
    one grid step -- the machinery has power.
    """
    # a linear chirp: broadband, non-periodic, sharply autocorrelated, so
    # the cross-correlation peak sits unambiguously at the true lag. (A
    # random walk would be trend-dominated and peak at zero regardless.)
    fs = grid_hz * 3.0
    t = np.arange(0.0, duration_s, 1.0 / fs)
    f0, f1 = 2.0, grid_hz / 4.0
    k = (f1 - f0) / duration_s
    base = np.sin(2.0 * np.pi * (f0 * t + 0.5 * k * t * t))

    a = Stream("A", StreamKind.RF, t, base, clock_offset_s=0.0, unit="a.u.")
    # B samples the same waveform but its timeline is shifted by the lag
    b = Stream("B", StreamKind.MAGNETIC, t + injected_lag_s, base,
               clock_offset_s=0.0, unit="a.u.")

    al = align([a, b], grid_hz)
    xc = cross_correlation(al.aligned["A"], al.aligned["B"])
    lag_samples, lag_s = lag_of_peak(xc, grid_hz)
    return {
        "injected_lag_s": injected_lag_s,
        "recovered_lag_s": lag_s,
        "recovered_lag_samples": lag_samples,
        "grid_step_s": 1.0 / grid_hz,
        "within_one_step": abs(lag_s - injected_lag_s) <= 1.0 / grid_hz,
    }


# --- report -------------------------------------------------------------

def envlog_report() -> dict:
    return {
        "what_this_is": (
            "an environmental signal logger: it puts several channels "
            "(RF, mains, magnetic, temperature, acoustic, optical, "
            "device-state, operator-annotation) onto one timebase by "
            "clock-offset correction and linear resampling"),
        "the_real_operation": (
            "align() corrects each stream by its clock offset and "
            "interpolates onto the intersection of the corrected spans; "
            "cross_correlation()/lag_of_peak() then measure relative "
            "timing on the aligned series"),
        "the_firewalls": [
            "a stream with an unknown clock offset cannot enter an "
            "alignment: an unknown offset is a missing measurement, not "
            "a zero, and correlating unsynchronized streams is refused",
            "the grid is the overlap only; no value is extrapolated "
            "beyond where a stream was actually sampled",
        ],
        "the_power_control": (
            "two synthetic streams with a known injected lag: after align "
            "and cross-correlation the lag is recovered to within one "
            "grid step, so the refusals are choices, not incapacity"),
        "stream_kinds": [k.name for k in StreamKind],
        "evidence_class": "DERIVED_MATHEMATICS",
        "hardware_status": "DEFERRED — no apparatus has been built",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "SYNCHRONIZATION_REQUIRED_BEFORE_CORRELATION",
        "what_this_does_not_say": (
            "It does not say any environmental channel was recorded, that "
            "any two channels were found correlated, or that any physical "
            "coupling exists between them. It establishes only that "
            "unsynchronized streams may not be correlated and that "
            "aligned ones may be, demonstrated on seeded synthetic data. "
            "No timebase was established on a bench."),
    }
