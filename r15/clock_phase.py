"""P18 — the clock and phase measurement lane.

A cross-domain experiment is only as honest as the timebase it is measured
against. This module is that timebase lane: it characterises a reference
clock (jitter, drift, an Allan-deviation-style stability), it measures a
tone's phase and frequency, and it synchronises several channels and reports
their skew -- all in software, from a deterministic synthetic clock. No
oscillator, counter, GPSDO or phase comparator is operated, and nothing is
acquired.

**One interface, four honest modes.** Behind :class:`ClockLane` sit the four
R15 device modes, and the difference between them is the point.

* ``REAL_DEVICE`` is an interface only. There is no timebase hardware here,
  so a real acquisition acquires *nothing*: it raises
  :class:`NoClockHardwareError` and its receipt is ``PREREGISTERED_NOT_RUN``.
* ``SYNTHETIC_DEVICE`` produces a deterministic synthetic clock -- a tone on
  a jittered, drifting timebase and the matching time-error series -- under
  a numpy seed. Same seed, identical output. Its output is a
  ``SYNTHETIC_OBSERVATION``, never a physical measurement. This is the mode
  with power: planted jitter, skew and phase are recovered from it.
* ``REPLAY_DEVICE`` replays a previously recorded synthetic acquisition
  byte-for-byte; it measures nothing new.
* ``FAULT_INJECTION_DEVICE`` injects the ordinary instrument pathologies
  (clipping, drift, saturation, packet loss, missing samples) *and* the
  clock-specific ones (cycle slip, glitch, holdover), deterministically, so
  the timing error budget can be exercised against known faults.

**The measurements.** :func:`recover_phase` reads a tone's phase back with
the R13 I/Q demodulator; :func:`recover_skews` recovers per-channel skew with
the R13 cross-correlation; :func:`estimate_drift` recovers a planted
frequency drift; :func:`estimate_jitter` recovers a planted timebase jitter;
:func:`allan_deviation` reports an overlapping Allan deviation from the
time-error series. :func:`closure_residual` distinguishes a *common clock*
(channels sharing one reference close to numerical zero) from *independent
oscillators* (distinct fractional frequencies do not close).

**Clock jitter is not a signal.** Timebase jitter scatters a tone's energy
out of its bin and *raises the noise floor* -- a ``KNOWN_ORDINARY_EFFECT``,
computed here by the R13 ``jitter_snr`` model. Reading that raised floor as a
tone is the promotion :func:`refuse_jitter_as_signal` blocks. And an
unknown transport latency stays *uncertain*: without a reference delay the
absolute latency carries a cycle ambiguity, so :func:`transport_latency`
returns an interval, not a point.

**No promotion, no relativity.** A synthetic clock is not a measured one
(:func:`refuse_synthetic_clock_as_measured`), and a synthetic fractional
frequency offset is never read as gravitational or relativistic time dilation
when the sensitivity to do so does not exist here
(:func:`refuse_relativistic_interpretation`). The strongest class this module
reaches is a ``SYNTHETIC_OBSERVATION``; nothing is measured.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r13 import daq
from r13 import quadfield
from r15 import claims

# --- verdict and standing claim vocabulary -------------------------------

#: The standing verdict for this module.
VERDICT = "CLOCK_PHASE_LANE_SYNTHETIC_NO_TIMEBASE_HARDWARE"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: A physical clock/phase run is preregistered, not run: no timebase
#: hardware exists in this repository.
PHYSICAL_RUN_STATUS = "PREREGISTERED_NOT_RUN"

#: The analysis version stamped on every observation and budget produced
#: here, so a result is reproducible and a change is visible.
ANALYSIS_VERSION = "clock_phase-1"

#: The ceiling any reading this module produces may carry. A synthetic or
#: replayed reading is a SYNTHETIC_OBSERVATION; it is never a measurement.
READING_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION
#: The class of the lane machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED

#: Coverage factor for the expanded timing uncertainty (k = 2).
DEFAULT_COVERAGE_FACTOR = 2.0


class ClockPhaseError(RuntimeError):
    """Raised on any clock/phase refusal or structural guard.

    Covers the structural guards (a non-positive rate or frequency, a
    mismatched channel set, an unknown fault) and the load-bearing
    refusals :func:`refuse_jitter_as_signal`,
    :func:`refuse_synthetic_clock_as_measured` and
    :func:`refuse_relativistic_interpretation`. Base of
    :class:`NoClockHardwareError`.
    """


class NoClockHardwareError(ClockPhaseError):
    """Raised when a REAL_DEVICE clock is asked to acquire.

    There is no timebase hardware in this repository, so a real clock
    acquisition acquires nothing. The read is BLOCKED at the
    hardware-access boundary and the physical run is PREREGISTERED_NOT_RUN.
    """


# --- the four modes and the fault vocabulary -----------------------------

class ClockMode(Enum):
    """The four acquisition modes behind the one clock interface."""

    REAL_DEVICE = "REAL_DEVICE"
    REPLAY_DEVICE = "REPLAY_DEVICE"
    SYNTHETIC_DEVICE = "SYNTHETIC_DEVICE"
    FAULT_INJECTION_DEVICE = "FAULT_INJECTION_DEVICE"


class ClockFaultMode(Enum):
    """The pathologies a fault-injection clock can inject.

    The first five are the ordinary DAQ instrument faults (shared with the
    R15 instrument registry); the last three are clock-specific -- a cycle
    slip (a phase/time discontinuity), a glitch (a single large spike), and
    holdover (an undisciplined free-run after a breakpoint).
    """

    CLIPPING = "clipping"
    DRIFT = "drift"
    SATURATION = "saturation"
    PACKET_LOSS = "packet_loss"
    MISSING_SAMPLES = "missing_samples"
    CYCLE_SLIP = "cycle_slip"
    GLITCH = "glitch"
    HOLDOVER = "holdover"


# --- the synthetic clock specification -----------------------------------

@dataclass(frozen=True)
class SyntheticClockSpec:
    """The declared parameters of a synthetic clock and its tone.

    Every field is a model number, not a measured one. ``tone_freq`` is the
    tone carried on the timebase; ``fs`` and ``duration`` set the record;
    ``jitter_std`` is the timebase edge jitter (seconds, white phase noise);
    ``freq_offset`` and ``drift_rate`` are the fractional frequency offset
    (dimensionless) and its linear drift (per second); ``planted_phase`` is
    the tone phase to be recovered; ``skew_samples`` is a fixed integer
    channel delay in samples.
    """

    tone_freq: float = 100.0
    fs: float = 8000.0
    duration: float = 0.5
    jitter_std: float = 0.0
    freq_offset: float = 0.0
    drift_rate: float = 0.0
    planted_phase: float = 0.0
    skew_samples: int = 0

    def __post_init__(self) -> None:
        if float(self.tone_freq) <= 0.0:
            raise ClockPhaseError("the tone frequency must be positive")
        if float(self.fs) <= 0.0:
            raise ClockPhaseError("the sample rate must be positive")
        if float(self.duration) <= 0.0:
            raise ClockPhaseError("the duration must be positive")
        if float(self.jitter_std) < 0.0:
            raise ClockPhaseError("the jitter std cannot be negative")
        if float(self.tone_freq) >= 0.5 * float(self.fs):
            raise ClockPhaseError(
                "the tone must sit below Nyquist (fs/2) to be recovered")

    @property
    def w_ref(self) -> float:
        """The tone's reference angular frequency, ``2*pi*tone_freq``."""
        return 2.0 * np.pi * float(self.tone_freq)

    @property
    def n_samples(self) -> int:
        return int(round(float(self.fs) * float(self.duration)))


# --- the clock acquisition -----------------------------------------------

@dataclass(frozen=True)
class ClockAcquisition:
    """One synthetic clock reading: a tone waveform and a time-error series.

    ``samples`` is the tone sampled on the (jittered) timebase, used for
    phase, skew and SNR; ``time_error`` is the clock's time-error series
    ``x(t)`` in seconds (offset + drift + jitter), used for drift, Allan
    deviation and jitter estimation; ``edges`` are the nominal tick times.
    ``claim_class`` is capped at ``SYNTHETIC_OBSERVATION`` and can never be
    a measurement class.
    """

    mode: ClockMode
    samples: np.ndarray
    time_error: np.ndarray
    edges: np.ndarray
    fs: float
    tone_freq: float
    seed: int
    tau0: float
    claim_class: claims.ClaimClass = READING_CLAIM_CLASS
    faults: tuple = ()

    def __post_init__(self) -> None:
        if self.claim_class in claims.MEASUREMENT_CLASSES:
            claims.refuse_synthetic_as_physical()

    def digest(self) -> str:
        """A deterministic hash over the tone and time-error arrays."""
        a = np.ascontiguousarray(self.samples, dtype=float).tobytes()
        b = np.ascontiguousarray(self.time_error, dtype=float).tobytes()
        return hashlib.sha256(a + b).hexdigest()

    def as_dict(self) -> dict:
        return {
            "mode": self.mode.value,
            "n_samples": int(np.asarray(self.samples).size),
            "fs": float(self.fs),
            "tone_freq": float(self.tone_freq),
            "seed": int(self.seed),
            "tau0": float(self.tau0),
            "faults": [f.value for f in self.faults],
            "digest": self.digest(),
            "claim_class": self.claim_class.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


# --- the synthetic clock model -------------------------------------------

#: Distinct seed tags so the tone jitter and the time-error jitter draw
#: independent-but-reproducible streams from the acquisition seed.
_TONE_TAG = 0x54
_TERR_TAG = 0x45


def _tone_func(spec: SyntheticClockSpec, phase: float):
    """The synthetic tone ``cos(w t + phi)`` as a callable of ``t``."""
    w = spec.w_ref
    return lambda t: np.cos(w * np.asarray(t, dtype=float) + float(phase))


def synthetic_time_error(spec: SyntheticClockSpec, seed: int) -> np.ndarray:
    """The clock's time-error series ``x(t)`` in seconds.

    ``x(t) = freq_offset*t + 0.5*drift_rate*t^2 + jitter``: a constant
    fractional frequency offset integrates to a linear phase, its drift to
    a quadratic phase, and the timebase jitter adds a white term. This is
    the series the drift, Allan-deviation and jitter estimators read.
    """
    n = spec.n_samples
    t = np.arange(n, dtype=float) / float(spec.fs)
    x = float(spec.freq_offset) * t + 0.5 * float(spec.drift_rate) * t * t
    if float(spec.jitter_std) > 0.0:
        rng = np.random.default_rng(
            np.random.SeedSequence([int(seed), _TERR_TAG]))
        x = x + rng.normal(0.0, float(spec.jitter_std), size=n)
    return x


def synthesize(spec: SyntheticClockSpec, seed: int = 0) -> ClockAcquisition:
    """Produce a deterministic synthetic clock acquisition.

    The tone is sampled on a jittered timebase with the R13 ``daq``
    sampler, then rolled by the integer channel skew; the time-error series
    is built by :func:`synthetic_time_error`. Same seed, identical output.
    """
    phase = float(spec.planted_phase)
    if float(spec.jitter_std) > 0.0:
        sig = daq.sample_with_jitter(
            _tone_func(spec, phase), spec.fs, spec.duration,
            float(spec.jitter_std),
            seed=int(np.random.SeedSequence([int(seed), _TONE_TAG]).generate_state(1)[0]))
        samples = sig.values
        edges = sig.t
    else:
        sig = daq.sample(_tone_func(spec, phase), spec.fs, spec.duration)
        samples = sig.values
        edges = sig.t
    if int(spec.skew_samples):
        samples = np.roll(samples, int(spec.skew_samples))
    return ClockAcquisition(
        mode=ClockMode.SYNTHETIC_DEVICE,
        samples=np.asarray(samples, dtype=float),
        time_error=synthetic_time_error(spec, int(seed)),
        edges=np.asarray(edges, dtype=float),
        fs=float(spec.fs),
        tone_freq=float(spec.tone_freq),
        seed=int(seed),
        tau0=1.0 / float(spec.fs),
    )


# --- the four device modes -----------------------------------------------

class ClockDevice:
    """Base of the one clock interface. Not used directly."""

    mode: ClockMode

    def acquire(self, seed: int = 0) -> ClockAcquisition:
        raise NotImplementedError


class RealClockDevice(ClockDevice):
    """A real timebase interface with no hardware behind it.

    Acquisition acquires nothing: it raises :class:`NoClockHardwareError`.
    :meth:`blocked_receipt` records the honest PREREGISTERED_NOT_RUN state.
    """

    mode = ClockMode.REAL_DEVICE

    def __init__(self, instrument_id: str = "real_clock") -> None:
        self.instrument_id = str(instrument_id)

    def acquire(self, seed: int = 0) -> ClockAcquisition:
        raise NoClockHardwareError(
            f"refused: {self.instrument_id} is a REAL_DEVICE clock and no "
            f"timebase hardware (oscillator, counter, GPSDO, phase "
            f"comparator) exists in this repository, so it acquires "
            f"NOTHING. The read is BLOCKED at the hardware-access boundary. "
            f"A physical clock run is {PHYSICAL_RUN_STATUS}. "
            f"{PHYSICAL_VALIDATION}. {VERDICT}")

    def blocked_receipt(self) -> dict:
        """The honest blocked receipt for a real clock read that cannot run."""
        return {
            "instrument_id": self.instrument_id,
            "mode": self.mode.value,
            "status": "BLOCKED",
            "physical_run": PHYSICAL_RUN_STATUS,
            "reason": ("no timebase hardware present; acquires nothing. The "
                       "clock/phase physical protocol is preregistered but "
                       "not run"),
            "acquired": False,
            "n_samples": 0,
            "claim_class": "BLOCKED_MISSING_INPUT",
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


class SyntheticClockDevice(ClockDevice):
    """A deterministic synthetic clock driven by a :class:`SyntheticClockSpec`.

    Same seed => identical acquisition; different seed => different jitter
    realisation. The reading is a ``SYNTHETIC_OBSERVATION``.
    """

    mode = ClockMode.SYNTHETIC_DEVICE

    def __init__(self, spec: SyntheticClockSpec) -> None:
        self.spec = spec

    def acquire(self, seed: int = 0) -> ClockAcquisition:
        return synthesize(self.spec, int(seed))


class ReplayClockDevice(ClockDevice):
    """Replays a previously recorded synthetic acquisition byte-for-byte.

    It reads back what was stored and measures nothing new; the reading is
    a ``SYNTHETIC_OBSERVATION`` of a recorded artifact.
    """

    mode = ClockMode.REPLAY_DEVICE

    def __init__(self, recorded: ClockAcquisition) -> None:
        if not isinstance(recorded, ClockAcquisition):
            raise ClockPhaseError("a replay clock needs a recorded acquisition")
        self._recorded = recorded

    def acquire(self, seed: int = 0) -> ClockAcquisition:
        r = self._recorded
        return ClockAcquisition(
            mode=ClockMode.REPLAY_DEVICE,
            samples=np.asarray(r.samples, dtype=float).copy(),
            time_error=np.asarray(r.time_error, dtype=float).copy(),
            edges=np.asarray(r.edges, dtype=float).copy(),
            fs=r.fs, tone_freq=r.tone_freq, seed=r.seed, tau0=r.tau0,
            faults=r.faults)


class FaultInjectionClockDevice(ClockDevice):
    """Wraps a :class:`SyntheticClockDevice` and injects clock faults.

    Deterministic under the acquisition seed: each fault draws a distinct,
    reproducible stream. Every :class:`ClockFaultMode` is injectable -- the
    five ordinary DAQ faults and the three clock-specific ones -- and the
    applied faults are carried on the acquisition.
    """

    mode = ClockMode.FAULT_INJECTION_DEVICE

    def __init__(self, inner: SyntheticClockDevice, faults, config=None) -> None:
        faults = tuple(faults)
        if not faults:
            raise ClockPhaseError(
                "a fault-injection clock with no faults injects nothing; "
                "supply at least one ClockFaultMode")
        for f in faults:
            if not isinstance(f, ClockFaultMode):
                raise ClockPhaseError(f"{f!r} is not a ClockFaultMode")
        self.inner = inner
        self.faults = faults
        self.config = dict(config or {})

    def acquire(self, seed: int = 0) -> ClockAcquisition:
        clean = self.inner.acquire(int(seed))
        samples = np.asarray(clean.samples, dtype=float).copy()
        time_error = np.asarray(clean.time_error, dtype=float).copy()
        for f in self.faults:
            rng = np.random.default_rng(
                np.random.SeedSequence([int(seed), _FAULT_TAG[f]]))
            samples, time_error = _apply_clock_fault(
                f, samples, time_error, self.inner.spec, self.config, rng)
        return ClockAcquisition(
            mode=ClockMode.FAULT_INJECTION_DEVICE,
            samples=samples, time_error=time_error,
            edges=np.asarray(clean.edges, dtype=float).copy(),
            fs=clean.fs, tone_freq=clean.tone_freq, seed=int(seed),
            tau0=clean.tau0, faults=self.faults)


# --- the fault kernels ----------------------------------------------------

_FAULT_TAG: dict[ClockFaultMode, int] = {
    ClockFaultMode.CLIPPING: 0x0C,
    ClockFaultMode.DRIFT: 0x0D,
    ClockFaultMode.SATURATION: 0x05,
    ClockFaultMode.PACKET_LOSS: 0x0B,
    ClockFaultMode.MISSING_SAMPLES: 0x0A,
    ClockFaultMode.CYCLE_SLIP: 0x51,
    ClockFaultMode.GLITCH: 0x61,
    ClockFaultMode.HOLDOVER: 0x40,
}


def _apply_clock_fault(fault, samples, time_error, spec, config, rng):
    """Apply one fault to copies of the tone and time-error series.

    Each fault demonstrably alters the reading relative to the clean
    synthetic one. The ordinary faults act on the tone waveform; the
    clock-specific faults also disturb the time-error series.
    """
    x = np.asarray(samples, dtype=float).copy()
    te = np.asarray(time_error, dtype=float).copy()
    n = x.size
    if n == 0:
        return x, te
    peak = float(np.max(np.abs(x)))
    scale = peak if peak > 0.0 else 1.0

    if fault is ClockFaultMode.CLIPPING:
        level = float(config.get("clip_fraction", 0.7)) * scale
        return np.clip(x, -level, level), te

    if fault is ClockFaultMode.DRIFT:
        slope = float(config.get("drift_fraction", 0.5)) * scale
        return x + np.linspace(0.0, slope, n), te

    if fault is ClockFaultMode.SATURATION:
        rail = float(config.get("saturation_fraction", 0.4)) * scale
        return np.clip(x, -rail, rail), te

    if fault is ClockFaultMode.PACKET_LOSS:
        frac = float(config.get("packet_fraction", 0.1))
        length = max(1, int(round(frac * n)))
        start = int(rng.integers(0, max(1, n - length + 1)))
        x[start:start + length] = 0.0
        return x, te

    if fault is ClockFaultMode.MISSING_SAMPLES:
        frac = float(config.get("missing_fraction", 0.05))
        k = max(1, int(round(frac * n)))
        idx = rng.choice(n, size=min(k, n), replace=False)
        x[idx] = np.nan
        return x, te

    if fault is ClockFaultMode.CYCLE_SLIP:
        # a phase/time discontinuity: the tail slips by a fraction of a
        # tone period, and the time-error series steps by one cycle.
        bp = n // 2
        period_samples = max(
            1, int(round(spec.fs / spec.tone_freq)))
        slip = max(1, int(round(0.5 * period_samples)))
        x[bp:] = np.roll(x[bp:], slip)
        te[bp:] = te[bp:] + 1.0 / float(spec.tone_freq)
        return x, te

    if fault is ClockFaultMode.GLITCH:
        # a single large spike on one sample.
        idx = int(rng.integers(0, n))
        x[idx] = x[idx] + float(config.get("glitch_gain", 5.0)) * scale
        te[idx] = te[idx] + float(config.get("glitch_gain", 5.0)) * \
            (1.0 / float(spec.tone_freq))
        return x, te

    if fault is ClockFaultMode.HOLDOVER:
        # an undisciplined free-run after a breakpoint: an accumulating
        # ramp is added to the tail of the time-error series and a slow
        # baseline shift to the tone.
        bp = n // 2
        tail = n - bp
        slope = float(config.get("holdover_fraction", 0.6))
        te[bp:] = te[bp:] + np.linspace(0.0, slope * float(spec.jitter_std
                                        if spec.jitter_std > 0 else 1e-6), tail)
        x[bp:] = x[bp:] + np.linspace(0.0, slope * scale, tail)
        return x, te

    raise ClockPhaseError(f"unknown fault {fault!r}")  # pragma: no cover


# --- phase and frequency measurement -------------------------------------

def recover_phase(acq: ClockAcquisition, w_ref: float | None = None) -> float:
    """Recover a tone's phase with the R13 I/Q demodulator.

    Reads the phase ``phi`` back from ``a = I + iQ`` of the acquisition's
    tone. For a clean synthetic tone this recovers the planted phase.
    """
    samples = np.asarray(acq.samples, dtype=float)
    if not np.all(np.isfinite(samples)):
        raise ClockPhaseError(
            "cannot demodulate a record with non-finite samples; a "
            "fault-injected record must be repaired first")
    t = np.arange(samples.size, dtype=float) / float(acq.fs)
    w = 2.0 * np.pi * float(acq.tone_freq) if w_ref is None else float(w_ref)
    return quadfield.iq_demodulate(samples, t, w).phase


def recover_skews(channels, reference_index: int = 0) -> tuple[int, ...]:
    """Recover per-channel integer skews with the R13 cross-correlation.

    A thin wrapper over :func:`r13.daq.estimate_skews`: an integer channel
    skew is recovered exactly from the cross-correlation peak.
    """
    return daq.estimate_skews(channels, reference_index=reference_index)


def estimate_drift(time_error: np.ndarray, tau0: float) -> float:
    """Recover the fractional frequency drift rate from a time-error series.

    ``x(t) = f0*t + 0.5*D*t^2 + noise`` fits a quadratic in ``t``; the
    ``t^2`` coefficient is ``0.5*D``, so ``D = 2*c2``. Recovers a planted
    drift ``drift_rate`` up to the fit noise.
    """
    x = np.asarray(time_error, dtype=float)
    if x.size < 3:
        raise ClockPhaseError("need at least three points to fit a drift")
    if float(tau0) <= 0.0:
        raise ClockPhaseError("the sample interval tau0 must be positive")
    t = np.arange(x.size, dtype=float) * float(tau0)
    c2, _c1, _c0 = np.polyfit(t, x, 2)
    return float(2.0 * c2)


def estimate_frequency_offset(time_error: np.ndarray, tau0: float) -> float:
    """Recover the mean fractional frequency offset from a time-error series.

    The slope of ``x(t)`` after removing curvature is the fractional
    frequency offset ``f0``.
    """
    x = np.asarray(time_error, dtype=float)
    if x.size < 3:
        raise ClockPhaseError("need at least three points to fit an offset")
    t = np.arange(x.size, dtype=float) * float(tau0)
    _c2, c1, _c0 = np.polyfit(t, x, 2)
    return float(c1)


def estimate_jitter(time_error: np.ndarray, tau0: float,
                    trend_deg: int = 2) -> float:
    """Recover the timebase jitter as the detrended residual std.

    Removing the offset/drift polynomial from ``x(t)`` leaves the white
    phase noise; its standard deviation is the planted ``jitter_std`` up to
    the estimator's own scatter.
    """
    x = np.asarray(time_error, dtype=float)
    n = x.size
    if n < int(trend_deg) + 2:
        raise ClockPhaseError("not enough points to detrend for jitter")
    t = np.arange(n, dtype=float) * float(tau0)
    coeffs = np.polyfit(t, x, int(trend_deg))
    residual = x - np.polyval(coeffs, t)
    return float(np.std(residual, ddof=1))


def allan_deviation(time_error: np.ndarray, tau0: float,
                    m_list=None) -> dict:
    """Overlapping Allan deviation from a time-error (phase) series.

    ``sigma_y(tau)`` at ``tau = m*tau0`` from the second difference of the
    time-error samples:

        sigma_y^2 = 1/(2 tau^2 (N-2m)) * sum (x[i+2m] - 2 x[i+m] + x[i])^2.

    A stability characterisation of the clock, not a measurement. Returns a
    mapping ``tau -> ADEV``.
    """
    x = np.asarray(time_error, dtype=float)
    n = x.size
    if float(tau0) <= 0.0:
        raise ClockPhaseError("the sample interval tau0 must be positive")
    if n < 3:
        raise ClockPhaseError("need at least three points for Allan deviation")
    if m_list is None:
        m_max = max(1, (n - 1) // 2)
        m_list = [m for m in (1, 2, 4, 8, 16, 32, 64) if m <= m_max]
        if not m_list:
            m_list = [1]
    out: dict[float, float] = {}
    for m in m_list:
        m = int(m)
        if m < 1 or (n - 2 * m) < 1:
            continue
        tau = m * float(tau0)
        d = x[2 * m:] - 2.0 * x[m:n - m] + x[:n - 2 * m]
        avar = float(np.sum(d * d)) / (2.0 * tau * tau * (n - 2 * m))
        out[tau] = float(np.sqrt(avar))
    if not out:
        raise ClockPhaseError("no valid averaging time for Allan deviation")
    return out


# --- multi-channel closure: common clock vs independent oscillators ------

def per_channel_frequency(channels_time_error, tau0: float) -> tuple[float, ...]:
    """The fractional frequency offset of each channel's time-error series."""
    return tuple(estimate_frequency_offset(np.asarray(c, dtype=float), tau0)
                 for c in channels_time_error)


def closure_residual(channels_time_error, tau0: float) -> dict:
    """Closure residual across channels: does one common clock explain them?

    Under the common-clock hypothesis every channel shares one reference,
    so their fractional frequency offsets are identical and the loop
    closes: the residual (the spread of per-channel offsets) is at the
    numerical-noise level. Independent oscillators carry distinct offsets,
    so the residual is nonzero -- and that is the whole difference between a
    shared timebase and independent ones.
    """
    freqs = np.asarray(per_channel_frequency(channels_time_error, tau0),
                       dtype=float)
    if freqs.size < 2:
        raise ClockPhaseError("closure needs at least two channels")
    residual = float(np.std(freqs, ddof=1))
    spread = float(np.max(freqs) - np.min(freqs))
    return {
        "per_channel_frequency": [float(f) for f in freqs],
        "closure_residual": residual,
        "frequency_spread": spread,
        "n_channels": int(freqs.size),
        "claim_class": READING_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
    }


def common_clock_closure(spec: SyntheticClockSpec, n_channels: int = 3,
                         seed: int = 0) -> dict:
    """Closure for ``n_channels`` sharing ONE synthetic clock.

    Every channel is disciplined by the same reference -- the same
    fractional frequency offset and drift -- and differs only by its own
    independent readout jitter. Their per-channel frequencies therefore
    coincide up to the jitter, so the closure residual is at the
    jitter-noise level: the loop closes.
    """
    channels = [synthetic_time_error(spec, int(seed) + k)
                for k in range(int(n_channels))]
    out = closure_residual(channels, 1.0 / float(spec.fs))
    out["hypothesis"] = "common_clock"
    return out


def independent_oscillator_closure(spec: SyntheticClockSpec, n_channels: int = 3,
                                   offsets=None, seed: int = 0) -> dict:
    """Closure for ``n_channels`` on INDEPENDENT oscillators.

    Each channel gets its own distinct fractional frequency offset (and its
    own jitter realisation), so the per-channel frequencies differ by far
    more than the jitter and the closure residual is nonzero: the loop does
    not close to a single common timebase.
    """
    if offsets is None:
        offsets = tuple(1e-3 * (k + 1) for k in range(int(n_channels)))
    channels = []
    for k, off in enumerate(offsets):
        s = SyntheticClockSpec(
            tone_freq=spec.tone_freq, fs=spec.fs, duration=spec.duration,
            jitter_std=spec.jitter_std, freq_offset=float(off),
            drift_rate=spec.drift_rate)
        channels.append(synthetic_time_error(s, int(seed) + k))
    out = closure_residual(channels, 1.0 / float(spec.fs))
    out["hypothesis"] = "independent_oscillators"
    return out


# --- jitter raises the noise floor (a KNOWN_ORDINARY_EFFECT) -------------

def jitter_noise_floor(spec: SyntheticClockSpec, jitter_std: float,
                       n_realizations: int = 16, seed: int = 0) -> dict:
    """The tone SNR and noise floor at a jitter level, via the R13 model.

    Uses :func:`r13.daq.jitter_snr`: timebase jitter scatters the tone's
    energy out of its bin, so more jitter means a lower SNR and a higher
    noise floor. The raised floor is a ``KNOWN_ORDINARY_EFFECT`` of the
    clock -- it is not a signal, and reading it as one is refused by
    :func:`refuse_jitter_as_signal`.
    """
    snr = daq.jitter_snr(spec.tone_freq, spec.fs, spec.duration,
                         float(jitter_std), n_realizations=int(n_realizations),
                         seed=int(seed))
    floor = 1.0 / snr if snr > 0.0 else float("inf")
    return {
        "jitter_std": float(jitter_std),
        "tone_snr": float(snr),
        "noise_floor": float(floor),
        "effect": "jitter raises the noise floor",
        "claim_class": claims.ClaimClass.KNOWN_ORDINARY_EFFECT.value,
        "is_signal": False,
        "measured_here": MEASURED_HERE,
    }


# --- transport latency stays uncertain -----------------------------------

def transport_latency(measured_lag_samples: int, fs: float,
                      reference_delay_s: float | None = None) -> dict:
    """Estimate a transport latency, honestly bounded by the cycle ambiguity.

    A cross-correlation gives a lag modulo the record, but without a known
    reference (cable/propagation) delay the *absolute* transport latency
    carries an integer-cycle ambiguity: the value is uncertain, and this
    returns an interval with ``resolved=False``. Supplying a
    ``reference_delay_s`` calibrates the offset and the latency resolves to
    a point.
    """
    rate = float(fs)
    if rate <= 0.0:
        raise ClockPhaseError("the sample rate must be positive")
    lag_time = float(measured_lag_samples) / rate
    if reference_delay_s is None:
        # one sample-period ambiguity on each side, plus the unknown
        # absolute reference: the latency is an interval, not a point.
        half = 1.0 / rate
        return {
            "quantity": "transport_latency",
            "value": lag_time,
            "units": "s",
            "uncertainty": {"type": "interval",
                            "low": lag_time - half,
                            "high": lag_time + half,
                            "half_width": half},
            "resolved": False,
            "reason": ("no reference delay supplied; the absolute latency "
                       "carries a cycle ambiguity and stays uncertain"),
            "claim_class": READING_CLAIM_CLASS.value,
            "measured_here": MEASURED_HERE,
        }
    resolved = lag_time - float(reference_delay_s)
    return {
        "quantity": "transport_latency",
        "value": float(resolved),
        "units": "s",
        "uncertainty": {"type": "point", "half_width": 0.0},
        "resolved": True,
        "reason": "reference delay supplied; latency resolved",
        "claim_class": READING_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
    }


# --- the timing error budget ---------------------------------------------

#: The timing error budget components, in reporting order, each tagged with
#: an error-budget category from the R15 error budget policy.
_BUDGET_CATEGORIES: dict[str, str] = {
    "synthesis_error": "clock",
    "clock_jitter": "clock",
    "reference_instability": "clock",
    "frequency_drift": "clock",
    "quantization": "instrument_resolution",
    "sync_skew": "clock",
    "transport_delay": "environment",
    "latency": "environment",
    "demod_residual": "dsp",
    "residual_phase": "model_residual",
}


def timing_error_budget(components: dict,
                        coverage_factor: float = DEFAULT_COVERAGE_FACTOR,
                        budget_id: str = "timing_error_budget-1") -> dict:
    """A full timing error budget, RSS-combined, schema-shaped.

    ``components`` maps a known component name (a key of
    ``_BUDGET_CATEGORIES``) to a 1-sigma magnitude in seconds. The
    components are combined in quadrature (RSS); the combined uncertainty is
    the 1-sigma total and the coverage factor expands it. Synthesis error,
    transport delay, latency and residual phase are separate named
    components, as the phase prompt requires.

    Conforms to ``error_budget.schema.json``.
    """
    if not components:
        raise ClockPhaseError("a timing error budget needs at least one term")
    rows = []
    ssq = 0.0
    for name in _BUDGET_CATEGORIES:
        if name not in components:
            continue
        value = float(components[name])
        if value < 0.0:
            raise ClockPhaseError(f"budget component {name!r} cannot be "
                                  f"negative")
        ssq += value * value
        rows.append({"name": name,
                     "category": _BUDGET_CATEGORIES[name],
                     "value": value,
                     "units": "s"})
    unknown = set(components) - set(_BUDGET_CATEGORIES)
    if unknown:
        raise ClockPhaseError(
            f"unknown timing budget component(s) {sorted(unknown)}; known "
            f"components are {sorted(_BUDGET_CATEGORIES)}")
    combined = float(np.sqrt(ssq))
    return {
        "budget_id": budget_id,
        "quantity": "timing_error",
        "components": rows,
        "combination_method": "RSS",
        "combined_uncertainty": combined,
        "coverage_factor": float(coverage_factor),
        "expanded_uncertainty": combined * float(coverage_factor),
        "separated": {
            "synthesis_error": float(components.get("synthesis_error", 0.0)),
            "transport_delay": float(components.get("transport_delay", 0.0)),
            "latency": float(components.get("latency", 0.0)),
            "residual_phase": float(components.get("residual_phase", 0.0)),
        },
        "analysis_version": ANALYSIS_VERSION,
        "claim_class": READING_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


# --- a schema-shaped observation record ----------------------------------

def phase_observation(recovered_phase: float, uncertainty: float,
                      run_id: str, observation_id: str = "obs_phase-1",
                      source_artifacts=None) -> dict:
    """A phase measurement as an ``observation_record.schema.json`` record.

    The value is a recovered phase in radians, capped at
    ``SYNTHETIC_OBSERVATION``: it is a synthetic clock's phase, not a
    measured one.
    """
    return {
        "observation_id": observation_id,
        "run_id": run_id,
        "source_artifacts": list(source_artifacts or ["synthetic_clock"]),
        "analysis_version": ANALYSIS_VERSION,
        "quantity": "phase",
        "value": float(recovered_phase),
        "units": "rad",
        "uncertainty": {"type": "standard", "sigma": float(uncertainty),
                        "k": 1.0},
        "claim_class": READING_CLAIM_CLASS.value,
        "derivation_graph": ["synthesize", "iq_demodulate", "recover_phase"],
    }


# --- the load-bearing refusals -------------------------------------------

def refuse_jitter_as_signal(
        claim: str = "the jitter-raised noise floor is a tone") -> None:
    """Refuse reading a jitter-raised noise floor as a signal. Always raises.

    Timebase jitter scatters a tone's energy out of its bin and raises the
    surrounding noise floor. That raised floor is a ``KNOWN_ORDINARY_EFFECT``
    of the clock -- it is broadband and it has no phase to recover -- and it
    is emphatically not a new tone, line or resonance. Delegates to the
    governance core's noise-to-resonance refusal for the canonical text.
    """
    try:
        claims.refuse_noise_as_resonance()
    except claims.ClaimError as exc:
        raise ClockPhaseError(
            f"refused: {claim!r}. Clock jitter raises the noise floor as a "
            f"KNOWN_ORDINARY_EFFECT; a raised broadband floor is not a "
            f"signal, a tone or a resonance. {exc} {VERDICT}") from exc


def refuse_synthetic_clock_as_measured(
        claim: str = "this synthetic clock is a measured timebase") -> None:
    """Refuse promoting a synthetic clock to a measured one. Always raises."""
    raise ClockPhaseError(
        f"refused: {claim!r}. Every edge, tone and time-error value here is "
        f"produced by evaluating a declared clock model under a seed -- a "
        f"SYNTHETIC_OBSERVATION, not a reading of any oscillator, counter or "
        f"phase comparator. No timebase hardware was operated; a physical "
        f"clock run is {PHYSICAL_RUN_STATUS}. {PHYSICAL_VALIDATION}. {VERDICT}")


def refuse_relativistic_interpretation(
        fractional_offset: float = 0.0,
        claim: str = "a fractional frequency offset is relativistic time "
                     "dilation") -> None:
    """Refuse relativistic language for a clock offset here. Always raises.

    Reading a fractional frequency offset as gravitational or special-
    relativistic time dilation demands a calibrated, differentially
    characterised pair of real clocks with a sensitivity budget that
    resolves the effect. None of that exists here: the offset is a declared
    parameter of a synthetic model, the sensitivity to a relativistic shift
    is not established, and the interpretation is refused.
    """
    raise ClockPhaseError(
        f"refused: {claim!r} (offset={float(fractional_offset):g}). A "
        f"relativistic interpretation of a clock offset requires two real, "
        f"calibrated clocks and a demonstrated sensitivity to the shift; "
        f"here the offset is a declared parameter of a synthetic clock and "
        f"no such sensitivity exists. Relativistic language is refused when "
        f"the sensitivity is insufficient. {PHYSICAL_VALIDATION}. {VERDICT}")


# --- report ---------------------------------------------------------------

def clock_phase_report() -> dict:
    """The standing statement of what this lane is and is not."""
    spec = SyntheticClockSpec(jitter_std=1e-6, drift_rate=2e-3,
                              planted_phase=0.7, skew_samples=5)
    acq = synthesize(spec, seed=0)
    common = common_clock_closure(spec)
    indep = independent_oscillator_closure(spec)
    return {
        "what_this_is": (
            "the R15 clock and phase measurement lane: a deterministic "
            "synthetic reference clock characterised for jitter, drift and "
            "Allan-deviation stability; I/Q phase and frequency measurement; "
            "multi-channel synchronization and skew recovery; and a full "
            "timing error budget -- behind one interface with four modes "
            "(REAL_DEVICE acquires nothing, SYNTHETIC_DEVICE is deterministic "
            "under a seed, REPLAY_DEVICE replays a recorded artifact, "
            "FAULT_INJECTION_DEVICE injects clipping, drift, saturation, "
            "packet loss, missing samples, cycle slip, glitch and holdover)"),
        "modes": [m.value for m in ClockMode],
        "fault_modes": [f.value for f in ClockFaultMode],
        "reuses": ["r13.daq (sampling, jitter->SNR, cross-correlation skew)",
                   "r13.quadfield (I/Q phase demodulation)",
                   "r15.claims (taxonomy and refusals)"],
        "recovered_phase": recover_phase(acq),
        "recovered_drift": estimate_drift(acq.time_error, acq.tau0),
        "recovered_jitter": estimate_jitter(acq.time_error, acq.tau0),
        "common_clock_closure": common["closure_residual"],
        "independent_oscillator_closure": indep["closure_residual"],
        "closure_differs": (indep["closure_residual"] >
                            common["closure_residual"]),
        "refusals": [
            "refuse_jitter_as_signal (a jitter-raised floor is not a tone)",
            "refuse_synthetic_clock_as_measured (synthetic is not measured)",
            "refuse_relativistic_interpretation (no sensitivity for it)",
            "REAL_DEVICE.acquire raises NoClockHardwareError (acquires "
            "nothing)",
        ],
        "reading_claim_class": READING_CLAIM_CLASS.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "physical_run": PHYSICAL_RUN_STATUS,
        "hardware_status": (
            "no timebase hardware exists here; a REAL_DEVICE clock read is "
            "BLOCKED and the physical clock run is PREREGISTERED_NOT_RUN"),
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any clock was measured. The tone, timebase, "
            "jitter, drift and skew are all produced by evaluating a declared "
            "clock model under a seed; every reading is a "
            "SYNTHETIC_OBSERVATION and a REAL_DEVICE acquires nothing. A "
            "jitter-raised noise floor is a KNOWN_ORDINARY_EFFECT, not a "
            "signal; an unknown transport latency stays uncertain; and a "
            "synthetic frequency offset is never read as relativistic time "
            "dilation. PHYSICAL_VALIDATION_NOT_CLAIMED."),
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION", "PHYSICAL_RUN_STATUS",
    "ANALYSIS_VERSION", "READING_CLAIM_CLASS", "SOFTWARE_CLAIM_CLASS",
    "DEFAULT_COVERAGE_FACTOR",
    "ClockPhaseError", "NoClockHardwareError",
    "ClockMode", "ClockFaultMode",
    "SyntheticClockSpec", "ClockAcquisition",
    "synthetic_time_error", "synthesize",
    "ClockDevice", "RealClockDevice", "SyntheticClockDevice",
    "ReplayClockDevice", "FaultInjectionClockDevice",
    "recover_phase", "recover_skews", "estimate_drift",
    "estimate_frequency_offset", "estimate_jitter", "allan_deviation",
    "per_channel_frequency", "closure_residual", "common_clock_closure",
    "independent_oscillator_closure",
    "jitter_noise_floor", "transport_latency", "timing_error_budget",
    "phase_observation",
    "refuse_jitter_as_signal", "refuse_synthetic_clock_as_measured",
    "refuse_relativistic_interpretation", "clock_phase_report",
]
