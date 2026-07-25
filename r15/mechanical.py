"""P13 — the mechanical measurement lane: one interface, four honest modes.

R15 needs a mechanical observation lane that can *acquire* modal data --
an accelerometer record, a microphone (acoustic proxy) record, or a
ring-down decay -- and *fit* the modal frequencies, the quality factor
``Q``, and the damping ratio ``zeta = 1/(2Q)``. This module is that lane.
It reuses the R15 instrument machinery unchanged: the same four acquisition
modes sit behind one lane interface, and the same fault-injection kernels
exercise the error budget.

**The four modes are not interchangeable, and the difference is the whole
point.**

* ``REAL_DEVICE`` is an interface only. There is no accelerometer, shaker,
  laser vibrometer or microphone in this repository, so a real mechanical
  acquisition acquires *nothing*: it raises :class:`~r15.instruments.
  NoHardwareError` and the honest state is ``BLOCKED`` /
  ``PREREGISTERED_NOT_RUN``, never a fabricated modal record.
* ``SYNTHETIC_DEVICE`` produces a deterministic modal signal under a numpy
  seed -- a sum of decaying modes ``A exp(-t/tau) sin(2 pi f t + phi)`` with
  a **planted** mode the fit recovers. Same seed, identical samples;
  different seed, different samples. Its output is a
  ``SYNTHETIC_OBSERVATION``.
* ``REPLAY_DEVICE`` replays a previously recorded (synthetic) mechanical
  artifact byte-for-byte. It reads back what was stored; it measures nothing
  new.
* ``FAULT_INJECTION_DEVICE`` wraps a synthetic device and injects the
  ordinary instrument pathologies -- clipping, drift, saturation, packet
  loss and missing samples -- so the modal fit and its diagnostics can be
  exercised against known faults.

**The fit is not a measurement.** :func:`fit_ringdown` recovers the ``Q``,
``tau`` and frequency this module *planted* in a synthetic decay by reusing
the R13 ring-down authority :func:`r13.qcmstack.ringdown_Q`;
:func:`fit_modal_frequencies` finds the modal peaks this module planted in a
synthetic accelerometer record. Every recovered ``f``, ``Q`` and ``zeta`` is
a ``SYNTHETIC_OBSERVATION`` -- a number fitted to data this module
generated, not transduced from a specimen. A modal frequency *predicted*
from an elastic model (via :func:`r13.homogenize.sound_speed_from_chain`) is
a ``MODEL_PREDICTION``. A ``PHYSICAL_MEASUREMENT`` needs a specimen on a
calibrated fixture, and that is ``PREREGISTERED_NOT_RUN``.

The full error budget -- instrument resolution, calibration, clock,
environment, fixture repeatability, specimen geometry, DSP window/leakage,
numerical, and model residual -- is carried on every fit, because a fitted
value with no declared uncertainty cannot enter the evidence ladder, and a
residual below the combined uncertainty is not a mode.

Nothing here is measured. No accelerometer, microphone, shaker or
vibrometer exists in this repository; the strongest class this lane reaches
is a synthetic observation, and a synthetic observation is never a physical
measurement.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r15 import claims
from r15 import instruments as inst
from r15 import synthetic_instruments as si

from r13 import qcmstack
from r13 import homogenize
from r11 import detectors


# --- verdict and standing claim vocabulary -------------------------------

#: The standing verdict for this module.
VERDICT = "MECHANICAL_LANE_FOUR_MODES_FIT_IS_SYNTHETIC_NOT_MEASURED"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The version stamped onto every fit and observation record.
ANALYSIS_VERSION = "r15.mechanical/1.0"

#: A fit to synthetic mechanical data is a SYNTHETIC_OBSERVATION; it is
#: never a measurement class.
FIT_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION
#: A modal frequency predicted from an elastic model is a MODEL_PREDICTION.
PREDICTION_CLAIM_CLASS = claims.ClaimClass.MODEL_PREDICTION
#: The class of the lane machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED

#: The physical mechanical run is preregistered, not run: the software lane
#: is complete but no specimen has been mounted on a calibrated fixture.
PHYSICAL_ACQUISITION_STATUS = "PREREGISTERED_NOT_RUN"

#: A spectral peak whose prominence (peak magnitude over the spectral
#: median) does not exceed this is noise, not a mode.
MODE_PROMINENCE_MIN = 8.0


class MechanicalError(RuntimeError):
    """Raised on any mechanical-lane refusal or misuse.

    Covers the structural guards (a mode above Nyquist, a record too short
    to fit, a record carrying missing samples), and the load-bearing
    refusals (a fitted mode read as a physical measurement, a spectral
    feature within noise read as a mode, a model prediction read as a
    measurement).
    """


# --- the mechanical channels ---------------------------------------------

class MechanicalChannel(Enum):
    """A mechanical observation channel and the capability it acquires.

    ``ACCELEROMETER`` and ``MICROPHONE`` are contact and acoustic-proxy
    transducers; ``RINGDOWN`` is the free decay of a struck specimen after
    the drive is cut, acquired on the acceleration channel and analysed by
    its envelope.
    """

    ACCELEROMETER = "accelerometer"
    MICROPHONE = "microphone"
    RINGDOWN = "ringdown"

    @property
    def capability(self) -> inst.Capability:
        if self is MechanicalChannel.MICROPHONE:
            return inst.Capability.ACOUSTIC
        return inst.Capability.ACCELERATION

    @property
    def instrument_type(self) -> str:
        return f"mechanical_{self.value}"


# --- a planted modal mode ------------------------------------------------

@dataclass(frozen=True)
class ModalMode:
    """One planted mechanical mode: a frequency, a quality factor ``Q``, an
    amplitude and a phase.

    A synthetic mode, not a specimen resonance. The damping ratio
    ``zeta = 1/(2Q)`` and decay time ``tau = Q/(pi f)`` follow from ``Q``
    and ``f`` -- the same ``Q = w tau / 2`` written for ``tau``.
    """

    frequency_hz: float
    q: float
    amplitude: float = 1.0
    phase: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.frequency_hz) or self.frequency_hz <= 0.0:
            raise MechanicalError("a mode needs a positive, finite frequency")
        if not math.isfinite(self.q) or self.q <= 0.0:
            raise MechanicalError("a mode needs a positive, finite Q")

    @property
    def damping_ratio(self) -> float:
        """The viscous damping ratio ``zeta = 1/(2Q)``."""
        return 1.0 / (2.0 * self.q)

    @property
    def tau_s(self) -> float:
        """The ring-down decay time ``tau = Q/(pi f)``."""
        return self.q / (math.pi * self.frequency_hz)


#: A default single planted mode for the worked demonstration and the
#: default synthetic lane: 150 Hz, Q = 80.
DEFAULT_MODE = ModalMode(frequency_hz=150.0, q=80.0, amplitude=1.0)
DEFAULT_MODES: tuple = (DEFAULT_MODE,)


# --- deterministic synthetic modal signal --------------------------------

def synthesize_modal_record(modes, *, sample_rate_hz: float, n_samples: int,
                            seed: int = 0, noise: float = 5.0e-3
                            ) -> tuple[np.ndarray, np.ndarray]:
    """Build a deterministic mechanical record from planted ``modes``.

    The record is a sum of decaying modes plus seeded Gaussian noise,
    evaluated on a fixed time base. It is deterministic under ``seed``:
    same seed => identical arrays. A mode at or above the Nyquist frequency
    ``sample_rate_hz/2`` would alias and is refused before any sample is
    produced -- the honest response to an under-sampled mode is refusal,
    not a folded artifact.
    """
    fs = float(sample_rate_hz)
    n = int(n_samples)
    if fs <= 0.0:
        raise MechanicalError("the sample rate must be positive")
    if n < 16:
        raise MechanicalError("a modal record needs at least sixteen samples")
    modes = tuple(modes)
    if not modes:
        raise MechanicalError("a modal record needs at least one planted mode")
    nyquist = 0.5 * fs
    for m in modes:
        if m.frequency_hz >= nyquist:
            raise MechanicalError(
                f"refused: a planted mode at {m.frequency_hz:g} Hz is at or "
                f"above the Nyquist frequency {nyquist:g} Hz for a "
                f"{fs:g} Hz sample rate; it would ALIAS. Raise the sample "
                f"rate or lower the mode; a folded artifact is not a mode")
    t = np.arange(n, dtype=float) / fs
    signal = np.zeros(n, dtype=float)
    for m in modes:
        envelope = m.amplitude * np.exp(-t / m.tau_s)
        signal = signal + envelope * np.sin(
            2.0 * math.pi * m.frequency_hz * t + m.phase)
    if noise:
        rng = np.random.default_rng(int(seed))
        signal = signal + float(noise) * rng.standard_normal(n)
    return t, signal


@dataclass(frozen=True)
class ModalDriver(si.BaseSyntheticDriver):
    """A synthetic driver that plants modes for the mechanical lane.

    Implements the :class:`~r15.instruments.SyntheticDriver` protocol via
    :class:`~r15.synthetic_instruments.BaseSyntheticDriver`, so it drops
    straight into a :class:`~r15.instruments.SyntheticDevice`. Its
    ``_model`` is the summed decaying modes; the base class adds the seeded
    noise, so the same seed reproduces the same faulty-or-clean array.
    """

    instrument_type: str = "mechanical_accelerometer"
    capability: inst.Capability = inst.Capability.ACCELERATION
    sample_rate_hz: float = 1.0e4
    noise: float = 5.0e-3
    modes: tuple = DEFAULT_MODES

    def _model(self, t, rng):
        signal = np.zeros_like(t)
        for m in self.modes:
            envelope = m.amplitude * np.exp(-t / m.tau_s)
            signal = signal + envelope * np.sin(
                2.0 * math.pi * m.frequency_hz * t + m.phase)
        return signal

    def generate(self, capability, n_samples, seed, sample_rate_hz):
        nyquist = 0.5 * float(sample_rate_hz)
        for m in self.modes:
            if m.frequency_hz >= nyquist:
                raise MechanicalError(
                    f"refused: a planted mode at {m.frequency_hz:g} Hz would "
                    f"ALIAS at a {float(sample_rate_hz):g} Hz sample rate "
                    f"(Nyquist {nyquist:g} Hz)")
        return super().generate(capability, n_samples, seed, sample_rate_hz)


# --- the lane: one interface, four modes ---------------------------------

class MechanicalLane:
    """The mechanical observation lane: one interface over the four modes.

    Wraps any :class:`~r15.instruments.Instrument` (real, synthetic, replay
    or fault-injection) bound to one :class:`MechanicalChannel`. A
    ``REAL_DEVICE`` lane raises :class:`~r15.instruments.NoHardwareError`
    on acquire; every other mode returns an
    :class:`~r15.instruments.Acquisition` whose reading is a
    ``SYNTHETIC_OBSERVATION``.
    """

    def __init__(self, device: inst.Instrument,
                 channel: MechanicalChannel) -> None:
        if not isinstance(channel, MechanicalChannel):
            raise MechanicalError("channel must be a MechanicalChannel")
        self.device = device
        self.channel = channel

    @property
    def mode(self) -> inst.InstrumentMode:
        return self.device.mode

    def acquire(self, *, n_samples: int = 16384, seed: int = 0,
                sample_rate_hz: float | None = None) -> inst.Acquisition:
        """Acquire a mechanical record on this lane's channel.

        Delegates to the wrapped device. A ``REAL_DEVICE`` acquires nothing
        and raises :class:`~r15.instruments.NoHardwareError`.
        """
        return self.device.acquire(
            self.channel.capability, n_samples=int(n_samples), seed=int(seed),
            sample_rate_hz=sample_rate_hz)

    def blocked_receipt(self) -> dict:
        """The honest BLOCKED receipt for a real mechanical read.

        Only a ``REAL_DEVICE`` lane has one; it acquires nothing.
        """
        if not isinstance(self.device, inst.RealDevice):
            raise MechanicalError(
                "only a REAL_DEVICE lane produces a blocked receipt")
        receipt = self.device.blocked_receipt(self.channel.capability)
        receipt["channel"] = self.channel.value
        receipt["physical_acquisition_status"] = PHYSICAL_ACQUISITION_STATUS
        return receipt


def build_synthetic_lane(channel: MechanicalChannel = MechanicalChannel.ACCELEROMETER,
                         *, modes=DEFAULT_MODES, sample_rate_hz: float = 1.0e4,
                         noise: float = 5.0e-3, instrument_id: str | None = None
                         ) -> MechanicalLane:
    """A ``SYNTHETIC_DEVICE`` mechanical lane with planted ``modes``."""
    driver = ModalDriver(
        instrument_type=channel.instrument_type, capability=channel.capability,
        sample_rate_hz=float(sample_rate_hz), noise=float(noise),
        modes=tuple(modes))
    record = inst.InstrumentRecord(
        instrument_id=instrument_id or f"synthetic_{channel.instrument_type}",
        instrument_type=channel.instrument_type,
        mode=inst.InstrumentMode.SYNTHETIC_DEVICE, firmware="synthetic-1.0",
        clock_source="synthetic_seeded_rng",
        capabilities=frozenset({channel.capability}),
        uncertainty_model={"type": "additive_gaussian", "sigma": float(noise),
                           "note": "synthetic noise model; not a measured "
                                   "uncertainty budget"})
    return MechanicalLane(inst.SyntheticDevice(record, driver), channel)


def build_real_lane(channel: MechanicalChannel = MechanicalChannel.ACCELEROMETER,
                    *, instrument_id: str | None = None) -> MechanicalLane:
    """A ``REAL_DEVICE`` mechanical lane. It acquires nothing."""
    record = inst.InstrumentRecord(
        instrument_id=instrument_id or f"real_{channel.instrument_type}",
        instrument_type=channel.instrument_type,
        mode=inst.InstrumentMode.REAL_DEVICE, firmware="fw-0.0",
        clock_source="unbuilt_bench_clock",
        capabilities=frozenset({channel.capability}),
        uncertainty_model={"type": "datasheet",
                           "note": "no hardware exists; acquires nothing"})
    return MechanicalLane(inst.RealDevice(record), channel)


def build_replay_lane(recorded: inst.Acquisition,
                      channel: MechanicalChannel = MechanicalChannel.ACCELEROMETER,
                      *, instrument_id: str | None = None) -> MechanicalLane:
    """A ``REPLAY_DEVICE`` mechanical lane over a recorded artifact."""
    record = inst.InstrumentRecord(
        instrument_id=instrument_id or f"replay_{channel.instrument_type}",
        instrument_type=channel.instrument_type,
        mode=inst.InstrumentMode.REPLAY_DEVICE, firmware="replay-1.0",
        clock_source="recorded",
        capabilities=frozenset({channel.capability}),
        uncertainty_model={"type": "recorded",
                           "note": "replays stored bytes; measures nothing new"})
    device = inst.ReplayDevice(
        record, {channel.capability: np.asarray(recorded.samples, dtype=float)},
        sample_rate_hz=float(recorded.sample_rate_hz))
    return MechanicalLane(device, channel)


def build_fault_lane(channel: MechanicalChannel = MechanicalChannel.ACCELEROMETER,
                     *, faults, modes=DEFAULT_MODES, sample_rate_hz: float = 1.0e4,
                     noise: float = 5.0e-3, config: dict | None = None,
                     instrument_id: str | None = None) -> MechanicalLane:
    """A ``FAULT_INJECTION_DEVICE`` mechanical lane over a synthetic inner."""
    inner_id = (instrument_id or f"fault_{channel.instrument_type}") + "_inner"
    inner_driver = ModalDriver(
        instrument_type=channel.instrument_type, capability=channel.capability,
        sample_rate_hz=float(sample_rate_hz), noise=float(noise),
        modes=tuple(modes))
    inner_record = inst.InstrumentRecord(
        instrument_id=inner_id, instrument_type=channel.instrument_type,
        mode=inst.InstrumentMode.SYNTHETIC_DEVICE, firmware="synthetic-1.0",
        clock_source="synthetic_seeded_rng",
        capabilities=frozenset({channel.capability}),
        uncertainty_model={"type": "additive_gaussian", "sigma": float(noise)})
    inner = inst.SyntheticDevice(inner_record, inner_driver)
    fault_record = inst.InstrumentRecord(
        instrument_id=instrument_id or f"fault_{channel.instrument_type}",
        instrument_type=channel.instrument_type,
        mode=inst.InstrumentMode.FAULT_INJECTION_DEVICE, firmware="synthetic-1.0",
        clock_source="synthetic_seeded_rng",
        capabilities=frozenset({channel.capability}),
        uncertainty_model={"type": "additive_gaussian", "sigma": float(noise)})
    device = inst.FaultInjectionDevice(fault_record, inner, tuple(faults),
                                       config=config)
    return MechanicalLane(device, channel)


# --- the mechanical error budget -----------------------------------------

#: The nine relative uncertainty components of a mechanical modal fit, as
#: fractions. Every quantitative result decomposes into exactly these.
DEFAULT_BUDGET_COMPONENTS: dict[str, float] = {
    "instrument_resolution": 0.010,
    "calibration": 0.020,
    "clock": 0.005,
    "environment": 0.010,
    "fixture_repeatability": 0.020,
    "specimen_geometry": 0.015,
    "dsp_window_leakage": 0.020,
    "numerical": 0.005,
    "model_residual": 0.020,
}


@dataclass(frozen=True)
class MechanicalErrorBudget:
    """The full error budget for a mechanical modal fit.

    Combines the nine relative components in quadrature (root-sum-square),
    with a coverage factor for an expanded uncertainty. A residual below
    the expanded combined uncertainty is not a mode.
    """

    quantity: str = "modal_frequency"
    components: dict = field(default_factory=lambda: dict(DEFAULT_BUDGET_COMPONENTS))
    combination_method: str = "root_sum_square"
    coverage_factor: float = 2.0
    budget_id: str = "mechanical_modal_budget"

    def __post_init__(self) -> None:
        if not self.components:
            raise MechanicalError(
                "an empty error budget declares no uncertainty; a fit with "
                "no uncertainty cannot enter the evidence ladder")
        for name, value in self.components.items():
            if not math.isfinite(value) or value < 0.0:
                raise MechanicalError(
                    f"error-budget component {name!r} must be a non-negative "
                    f"finite fraction, got {value!r}")

    @property
    def combined_relative(self) -> float:
        """The combined (1-sigma) relative uncertainty, RSS of components."""
        return math.sqrt(sum(v * v for v in self.components.values()))

    @property
    def expanded_relative(self) -> float:
        """The expanded relative uncertainty ``k * u_c``."""
        return self.coverage_factor * self.combined_relative

    def within_budget(self, true_value: float, estimate: float) -> bool:
        """True iff ``estimate`` agrees with ``true_value`` inside the
        expanded relative uncertainty."""
        if true_value == 0.0:
            raise MechanicalError("cannot form a relative error about zero")
        rel = abs(estimate - true_value) / abs(true_value)
        return rel <= self.expanded_relative

    def to_error_budget_record(self) -> dict:
        """A record conforming to ``error_budget.schema.json``."""
        return {
            "budget_id": self.budget_id,
            "quantity": self.quantity,
            "components": [
                {"name": name, "relative": float(value), "type": "B"}
                for name, value in sorted(self.components.items())
            ],
            "combination_method": self.combination_method,
            "combined_uncertainty": float(self.combined_relative),
            "coverage_factor": float(self.coverage_factor),
        }


#: A default budget instance for the worked demonstration.
DEFAULT_BUDGET = MechanicalErrorBudget()


# --- a fitted mode -------------------------------------------------------

@dataclass(frozen=True)
class FittedMode:
    """A mode recovered from a synthetic mechanical record.

    Every field is fitted to data this module generated, so the whole thing
    is a ``SYNTHETIC_OBSERVATION`` -- never a measurement. ``prominence`` is
    the spectral peak's magnitude over the spectral median; a mode below
    :data:`MODE_PROMINENCE_MIN` is noise, not a mode.
    """

    frequency_hz: float
    q: float
    damping_ratio: float
    amplitude: float
    prominence: float
    method: str
    claim_class: claims.ClaimClass = FIT_CLAIM_CLASS

    def __post_init__(self) -> None:
        if self.claim_class in claims.MEASUREMENT_CLASSES:
            claims.refuse_synthetic_as_physical()

    def as_dict(self) -> dict:
        return {
            "frequency_hz": float(self.frequency_hz),
            "q": float(self.q),
            "damping_ratio": float(self.damping_ratio),
            "amplitude": float(self.amplitude),
            "prominence": float(self.prominence),
            "method": self.method,
            "claim_class": self.claim_class.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


# --- guards on the record ------------------------------------------------

def _clean_samples(samples) -> np.ndarray:
    x = np.asarray(samples, dtype=float)
    if x.ndim != 1 or x.size < 16:
        raise MechanicalError(
            "a mechanical record must be a 1-D array of at least sixteen "
            "samples")
    if np.any(np.isnan(x)):
        raise MechanicalError(
            "refused: the record carries missing samples (NaN); a modal fit "
            "over a gapped record would invent structure. Repair the "
            "acquisition (a FAULT_INJECTION missing-samples reading is a "
            "known fault, not a fittable record)")
    return x


# --- the ring-down fit (reuses the R13 authority) ------------------------

def fit_ringdown(samples, sample_rate_hz: float) -> FittedMode:
    """Recover ``f``, ``Q`` and ``zeta`` from a ring-down decay.

    Reuses :func:`r13.qcmstack.ringdown_Q` -- the R13 ring-down authority --
    which recovers ``tau`` from a log-linear envelope fit and ``w`` from the
    dominant spectral peak, so ``Q = w tau / 2`` is recovered from the data.
    The damping ratio is ``zeta = 1/(2Q)``. A fit to a SYNTHETIC decay, not
    a measurement of any resonator.
    """
    x = _clean_samples(samples)
    fs = float(sample_rate_hz)
    if fs <= 0.0:
        raise MechanicalError("the sample rate must be positive")
    t = np.arange(x.size, dtype=float) / fs
    rd = qcmstack.ringdown_Q(x, t)
    q = float(rd["Q"])
    prom = _peak_prominence(x)
    return FittedMode(
        frequency_hz=float(rd["f_hz"]), q=q, damping_ratio=1.0 / (2.0 * q),
        amplitude=float(np.nanmax(np.abs(x))), prominence=prom,
        method="ringdown_envelope+spectral_peak")


# --- the modal-frequency fit ---------------------------------------------

def _peak_prominence(samples) -> float:
    """The dominant spectral peak's magnitude over the spectral median."""
    x = np.asarray(samples, dtype=float)
    x = x - float(np.mean(x))
    window = np.hanning(x.size)
    mag = np.abs(np.fft.rfft(x * window))
    if mag.size < 3:
        return 0.0
    med = float(np.median(mag))
    if med <= 0.0:
        return float("inf") if float(np.max(mag)) > 0.0 else 0.0
    return float(np.max(mag)) / med


def _parabolic(freqs: np.ndarray, mag: np.ndarray, i: int) -> float:
    """Sub-bin peak frequency near index ``i`` via a 3-point parabola."""
    if 0 < i < mag.size - 1:
        y0, y1, y2 = float(mag[i - 1]), float(mag[i]), float(mag[i + 1])
        denom = y0 - 2.0 * y1 + y2
        if denom != 0.0:
            delta = 0.5 * (y0 - y2) / denom
            df = float(freqs[1] - freqs[0])
            return float(freqs[i]) + delta * df
    return float(freqs[i])


def _half_power_q(freqs: np.ndarray, mag: np.ndarray, i: int,
                  f_peak: float) -> float:
    """Q from the half-power (-3 dB) bandwidth about a peak, or NaN."""
    half = float(mag[i]) / math.sqrt(2.0)
    lo = None
    j = i
    while j > 0:
        if mag[j] <= half:
            lo = float(freqs[j])
            break
        j -= 1
    hi = None
    j = i
    while j < mag.size - 1:
        if mag[j] <= half:
            hi = float(freqs[j])
            break
        j += 1
    if lo is None or hi is None or hi <= lo:
        return float("nan")
    return f_peak / (hi - lo)


def fit_modal_frequencies(samples, sample_rate_hz: float, *, n_modes: int = 1,
                          prominence_min: float = MODE_PROMINENCE_MIN,
                          min_separation_hz: float | None = None
                          ) -> list[FittedMode]:
    """Identify up to ``n_modes`` modal peaks in a mechanical record.

    Windows the record, takes the magnitude spectrum, and returns the
    strongest local maxima whose prominence exceeds ``prominence_min``. Each
    peak's frequency is refined by a 3-point parabola and its ``Q`` by the
    half-power bandwidth. Candidates within ``min_separation_hz`` of an
    already-accepted peak are merged, so a single mode's window side-lobes
    are not counted as extra modes. A peak within noise is not returned --
    it is not a mode. A fit to a SYNTHETIC record, not a measurement.
    """
    x = _clean_samples(samples)
    fs = float(sample_rate_hz)
    if fs <= 0.0:
        raise MechanicalError("the sample rate must be positive")
    xc = x - float(np.mean(x))
    window = np.hanning(xc.size)
    mag = np.abs(np.fft.rfft(xc * window))
    freqs = np.fft.rfftfreq(xc.size, 1.0 / fs)
    med = float(np.median(mag)) or 1.0
    df = float(freqs[1] - freqs[0]) if freqs.size > 1 else fs
    min_sep = 4.0 * df if min_separation_hz is None else float(min_separation_hz)

    # local maxima, strongest first
    candidates: list[int] = []
    for i in range(1, mag.size - 1):
        if mag[i] > mag[i - 1] and mag[i] >= mag[i + 1]:
            candidates.append(i)
    candidates.sort(key=lambda k: mag[k], reverse=True)

    out: list[FittedMode] = []
    for i in candidates:
        prom = float(mag[i]) / med
        if prom < prominence_min:
            break
        f_peak = _parabolic(freqs, mag, i)
        if any(abs(f_peak - m.frequency_hz) < min_sep for m in out):
            continue  # a side-lobe of an already-accepted mode
        q = _half_power_q(freqs, mag, i, f_peak)
        if not math.isfinite(q) or q <= 0.0:
            q = float("nan")
        zeta = 1.0 / (2.0 * q) if math.isfinite(q) and q > 0.0 else float("nan")
        out.append(FittedMode(
            frequency_hz=f_peak, q=q, damping_ratio=zeta,
            amplitude=float(mag[i]), prominence=prom,
            method="windowed_spectral_peak+half_power"))
        if len(out) >= int(n_modes):
            break
    return out


# --- mode identification: separating drive, fixture and specimen ---------

def is_genuine_mode(prominence: float,
                    prominence_min: float = MODE_PROMINENCE_MIN) -> bool:
    """True iff a spectral peak's prominence marks a mode, not noise."""
    return float(prominence) >= float(prominence_min)


def assert_mode_above_noise(prominence: float,
                            prominence_min: float = MODE_PROMINENCE_MIN) -> None:
    """Refuse to call a within-noise spectral feature a mode. Raises if the
    prominence does not clear the noise floor."""
    if not is_genuine_mode(prominence, prominence_min):
        claims.refuse_noise_as_resonance()


def separate_fixture_specimen(modes, fixture_band: tuple[float, float]) -> dict:
    """Split identified modes into specimen and fixture motion.

    A mode whose frequency falls in the known fixture resonance band is
    attributed to the fixture, not the specimen -- fixture motion is never
    assigned to the specimen. Everything else is candidate specimen motion.
    """
    lo, hi = float(fixture_band[0]), float(fixture_band[1])
    if hi <= lo:
        raise MechanicalError("the fixture band must be an increasing (lo, hi)")
    specimen: list[FittedMode] = []
    fixture: list[FittedMode] = []
    for m in modes:
        (fixture if lo <= m.frequency_hz <= hi else specimen).append(m)
    return {
        "specimen_modes": specimen,
        "fixture_modes": fixture,
        "fixture_band_hz": (lo, hi),
        "note": ("fixture-band modes are attributed to the fixture, not the "
                 "specimen; drive/fixture/specimen motion are kept distinct"),
    }


# --- fault diagnostics: aliasing and clipping ----------------------------

def aliasing_risk(frequency_hz: float, sample_rate_hz: float) -> bool:
    """True iff a mode at ``frequency_hz`` aliases at ``sample_rate_hz``."""
    return float(frequency_hz) >= 0.5 * float(sample_rate_hz)


def clipping_fraction(samples, *, rail_tol: float = 1.0e-6) -> float:
    """The fraction of finite samples pinned within ``rail_tol`` of the rail.

    A clean decaying record touches its peak only briefly, so the fraction
    is tiny; a clipped or saturated record pins many samples on the rail.
    Missing samples (NaN) are ignored so a gap does not masquerade as a rail.
    """
    x = np.asarray(samples, dtype=float)
    finite = x[np.isfinite(x)]
    if finite.size == 0:
        return 0.0
    peak = float(np.max(np.abs(finite)))
    if peak <= 0.0:
        return 0.0
    at_rail = np.abs(np.abs(finite) - peak) <= rail_tol * peak
    return float(np.count_nonzero(at_rail)) / float(finite.size)


def is_clipped(samples, *, threshold: float = 5.0e-3,
               rail_tol: float = 1.0e-6) -> bool:
    """True iff a suspicious fraction of samples sit on the rail (clipping/
    saturation)."""
    return clipping_fraction(samples, rail_tol=rail_tol) > float(threshold)


# --- FRF, coherence, and integration placeholders ------------------------

def _segments(x: np.ndarray, nseg: int) -> np.ndarray:
    """Split ``x`` into ``nseg`` equal Hann-windowed segments (rows)."""
    n = x.size // nseg
    if n < 4:
        raise MechanicalError("too few samples per segment for an FRF")
    w = np.hanning(n)
    return np.stack([x[k * n:(k + 1) * n] * w for k in range(nseg)])


def frf(drive, response, sample_rate_hz: float, *, nseg: int = 8) -> dict:
    """A single-input frequency response function ``H`` (H1 estimator).

    ``H = S_xy / S_xx`` with segment-averaged auto/cross spectra, reported
    with its magnitude and phase. A model relation over synthetic signals,
    not a measured transfer function.
    """
    x = _clean_samples(drive)
    y = _clean_samples(response)
    if x.size != y.size:
        raise MechanicalError("drive and response must be the same length")
    fs = float(sample_rate_hz)
    xs, ys = _segments(x, nseg), _segments(y, nseg)
    X, Y = np.fft.rfft(xs, axis=1), np.fft.rfft(ys, axis=1)
    sxx = np.mean(np.conj(X) * X, axis=0)
    sxy = np.mean(np.conj(X) * Y, axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        H = np.where(np.abs(sxx) > 0, sxy / sxx, 0.0)
    freqs = np.fft.rfftfreq(x.size // nseg, 1.0 / fs)
    return {"freqs_hz": freqs, "H": H, "magnitude": np.abs(H),
            "phase_rad": np.angle(H),
            "claim_class": PREDICTION_CLAIM_CLASS.value,
            "measured_here": MEASURED_HERE}


def coherence(drive, response, sample_rate_hz: float, *, nseg: int = 8) -> dict:
    """The ordinary coherence ``gamma^2 = |S_xy|^2 / (S_xx S_yy)``.

    Bounded in [0, 1]. Two linearly related signals cohere at 1; unrelated
    signals do not. A diagnostic over synthetic signals, not a measurement.
    """
    x = _clean_samples(drive)
    y = _clean_samples(response)
    if x.size != y.size:
        raise MechanicalError("drive and response must be the same length")
    fs = float(sample_rate_hz)
    xs, ys = _segments(x, nseg), _segments(y, nseg)
    X, Y = np.fft.rfft(xs, axis=1), np.fft.rfft(ys, axis=1)
    sxx = np.mean(np.conj(X) * X, axis=0).real
    syy = np.mean(np.conj(Y) * Y, axis=0).real
    sxy = np.mean(np.conj(X) * Y, axis=0)
    denom = sxx * syy
    with np.errstate(divide="ignore", invalid="ignore"):
        gamma2 = np.where(denom > 0, np.abs(sxy) ** 2 / denom, 0.0)
    gamma2 = np.clip(gamma2, 0.0, 1.0)
    freqs = np.fft.rfftfreq(x.size // nseg, 1.0 / fs)
    return {"freqs_hz": freqs, "coherence": gamma2,
            "claim_class": PREDICTION_CLAIM_CLASS.value,
            "measured_here": MEASURED_HERE}


def integrate_spectral(accel, sample_rate_hz: float, order: int, *,
                       highpass_hz: float = 5.0) -> np.ndarray:
    """Integrate an acceleration record ``order`` times in the frequency
    domain: divide by ``(i w)`` per integration.

    A placeholder relation -- ``order=1`` gives velocity, ``order=2`` gives
    displacement -- over a synthetic record; nothing is measured. Bins below
    ``highpass_hz`` are zeroed, the standard high-pass that suppresses the
    integration drift ``1/w^order`` amplifies at near-DC frequencies.
    """
    x = _clean_samples(accel)
    fs = float(sample_rate_hz)
    n = x.size
    freqs = np.fft.rfftfreq(n, 1.0 / fs)
    spectrum = np.fft.rfft(x - float(np.mean(x)))
    w = 2.0 * math.pi * freqs
    factor = np.zeros_like(spectrum)
    keep = w > 0.0
    factor[keep] = 1.0 / ((1j * w[keep]) ** int(order))
    factor[freqs < float(highpass_hz)] = 0.0
    return np.fft.irfft(spectrum * factor, n=n)


def to_velocity(accel, sample_rate_hz: float) -> np.ndarray:
    """Velocity placeholder: one spectral integration of acceleration."""
    return integrate_spectral(accel, sample_rate_hz, 1)


def to_displacement(accel, sample_rate_hz: float) -> np.ndarray:
    """Displacement placeholder: two spectral integrations of acceleration."""
    return integrate_spectral(accel, sample_rate_hz, 2)


@dataclass(frozen=True)
class ModeShapeField:
    """A placeholder modal field: a mode shape sampled at sensor positions.

    A ``MODEL_PREDICTION`` -- a shape function evaluated at positions, not a
    measured field. No optical or scanning field is acquired here.
    """

    positions: tuple
    amplitudes: tuple
    claim_class: claims.ClaimClass = PREDICTION_CLAIM_CLASS

    def as_dict(self) -> dict:
        return {"positions": list(self.positions),
                "amplitudes": list(self.amplitudes),
                "claim_class": self.claim_class.value,
                "measured_here": MEASURED_HERE,
                "note": "placeholder mode-shape field; predicted, not measured"}


def mode_shape_placeholder(n_points: int = 9, harmonic: int = 1) -> ModeShapeField:
    """A free-free bar mode shape ``sin(n pi x/L)`` at ``n_points``, as a
    placeholder modal field (a prediction, not a measurement)."""
    n = max(2, int(n_points))
    xs = np.linspace(0.0, 1.0, n)
    amps = np.sin(int(harmonic) * math.pi * xs)
    return ModeShapeField(tuple(float(x) for x in xs),
                          tuple(float(a) for a in amps))


# --- modal-frequency prediction (reuses the R13 elastic authority) -------

def predicted_rod_mode_hz(harmonic: int, length_m: float, K: float, m: float,
                          a: float) -> dict:
    """Predict a longitudinal rod mode ``f_n = n c / (2 L)`` from elasticity.

    Reuses :func:`r13.homogenize.sound_speed_from_chain` -- the R13 elastic /
    sound-speed authority -- to get the continuum sound speed ``c`` of a 1-D
    chain, then applies the free-free rod relation. This is a
    ``MODEL_PREDICTION``: a modal frequency computed from an elastic model,
    never a measured resonance.
    """
    n = int(harmonic)
    if n < 1:
        raise MechanicalError("the harmonic number must be a positive integer")
    if length_m <= 0.0:
        raise MechanicalError("the rod length must be positive")
    c = homogenize.sound_speed_from_chain(K, m, a)
    f = n * c / (2.0 * float(length_m))
    return {"frequency_hz": float(f), "harmonic": n, "sound_speed_m_s": float(c),
            "length_m": float(length_m),
            "claim_class": PREDICTION_CLAIM_CLASS.value,
            "measured_here": MEASURED_HERE,
            "note": ("a modal frequency PREDICTED from an elastic model via "
                     "r13.homogenize; not a measured resonance")}


def channel_band_ok(channel: MechanicalChannel, frequency_hz: float) -> bool:
    """Whether a piezoelectric mechanical channel reaches ``frequency_hz``.

    Consults the R11 detector authority (:mod:`r11.detectors`) for the
    piezoelectric transducer's band; a model-only domain check, not a
    measurement.
    """
    return detectors.bandwidth_ok(detectors.DetectorKind.PIEZOELECTRIC,
                                  float(frequency_hz))


# --- observation records --------------------------------------------------

def modal_observation_record(observation_id: str, run_id: str,
                             source_artifacts, quantity: str, value,
                             units: str, uncertainty: dict) -> dict:
    """A modal observation conforming to ``observation_record.schema.json``.

    Its ``claim_class`` is ``SYNTHETIC_OBSERVATION`` -- a fit to synthetic
    data. It is not a physical measurement.
    """
    return {
        "observation_id": observation_id,
        "run_id": run_id,
        "source_artifacts": list(source_artifacts),
        "analysis_version": ANALYSIS_VERSION,
        "quantity": quantity,
        "value": value,
        "units": units,
        "uncertainty": dict(uncertainty),
        "claim_class": FIT_CLAIM_CLASS.value,
        "derivation_graph": [
            {"step": "acquire", "produces": "raw_mechanical_record",
             "mode": "SYNTHETIC_DEVICE"},
            {"step": "fit", "software": ANALYSIS_VERSION,
             "produces": quantity},
        ],
    }


# --- the load-bearing refusals -------------------------------------------

def refuse_fit_as_measurement(
        claim: str = "the modal fit measured a specimen",
        quantity: str | None = None) -> None:
    """Refuse a synthetic modal fit read as a physical measurement. Raises.

    :func:`fit_ringdown` and :func:`fit_modal_frequencies` recover the modes
    this module PLANTED in a synthetic record. There is no accelerometer,
    microphone, shaker or vibrometer here, so nothing was measured. A
    measured specimen's ``f``, ``Q`` or ``zeta`` is ``PREREGISTERED_NOT_RUN``
    pending a specimen on a calibrated fixture.
    """
    named = f" of {quantity}" if quantity else ""
    raise MechanicalError(
        f"refused: {claim!r}{named}. The modal fit recovers modes PLANTED "
        f"by this module in a SYNTHETIC mechanical record; no accelerometer, "
        f"microphone, shaker or vibrometer exists here, so nothing was "
        f"measured. A synthetic observation is not a PHYSICAL_MEASUREMENT; a "
        f"measured modal f, Q or zeta is {PHYSICAL_ACQUISITION_STATUS}. "
        f"{PHYSICAL_VALIDATION}. {VERDICT}")


def refuse_synthetic_Q_as_device_Q(q_value: float | None = None) -> None:
    """Refuse a synthetic modal ``Q`` read as a device ``Q``. Raises.

    Delegates to the R13 ring-down authority
    :func:`r13.qcmstack.refuse_model_Q_as_device_Q`, because the ``Q`` the
    lane recovers is a model/synthetic ``Q``, not the ``Q`` of any physical
    resonator (whose value is set by mounting, gas-damping and anchor
    losses this lane does not contain).
    """
    qcmstack.refuse_model_Q_as_device_Q(
        claim="the fitted modal Q is the specimen Q", q_value=q_value)


def refuse_prediction_as_measurement(*_a, **_k) -> None:
    """Refuse a predicted modal frequency read as a measurement. Raises.

    Delegates to the governance core: a ``MODEL_PREDICTION`` (a modal
    frequency computed from an elastic model) is not a
    ``PHYSICAL_MEASUREMENT``.
    """
    claims.refuse_model_as_measurement()


# --- report ---------------------------------------------------------------

def mechanical_report() -> dict:
    """The standing statement of what the lane is and is not.

    Runs a worked, deterministic demonstration: a single planted mode is
    synthesized, recovered by the ring-down fit within the error budget, a
    fault-injected reading is flagged clipped, and a fixture-band mode is
    kept off the specimen. Nothing here is measured.
    """
    fs = 1.0e4
    # a planted mode recovered within budget
    t, sig = synthesize_modal_record((DEFAULT_MODE,), sample_rate_hz=fs,
                                     n_samples=16384, seed=0)
    fit = fit_ringdown(sig, fs)
    budget = DEFAULT_BUDGET
    q_ok = budget.within_budget(DEFAULT_MODE.q, fit.q)
    f_ok = budget.within_budget(DEFAULT_MODE.frequency_hz, fit.frequency_hz)

    # a fault-injected reading is flagged clipped
    fault = build_fault_lane(faults=(inst.FaultMode.CLIPPING,))
    clipped = fault.acquire(n_samples=4096, seed=3)
    clipped_flagged = is_clipped(clipped.samples)

    # a two-mode record: fixture motion is kept off the specimen
    two = (ModalMode(300.0, 120.0, 1.0), ModalMode(820.0, 120.0, 1.0))
    _, two_sig = synthesize_modal_record(two, sample_rate_hz=fs,
                                        n_samples=16384, seed=1)
    ids = fit_modal_frequencies(two_sig, fs, n_modes=2)
    split = separate_fixture_specimen(ids, fixture_band=(780.0, 860.0))
    specimen_free_of_fixture = all(
        not (750.0 <= m.frequency_hz <= 850.0)
        for m in split["specimen_modes"])

    return {
        "what_this_is": (
            "the R15 mechanical measurement lane: one interface over four "
            "modes -- REAL_DEVICE (acquires nothing), SYNTHETIC_DEVICE "
            "(deterministic planted modal signal under a seed), "
            "REPLAY_DEVICE (replays a recorded artifact), and "
            "FAULT_INJECTION_DEVICE (clipping, drift, saturation, packet "
            "loss, missing samples) -- with a ring-down Q fit, a "
            "modal-frequency fit, fixture/specimen separation, FRF and "
            "coherence, and a full error budget"),
        "channels": [c.value for c in MechanicalChannel],
        "modes": [m.value for m in inst.InstrumentMode],
        "fault_modes": [f.value for f in inst.FaultMode],
        "error_budget_components": sorted(DEFAULT_BUDGET_COMPONENTS),
        "error_budget_combined_relative": budget.combined_relative,
        "error_budget_expanded_relative": budget.expanded_relative,
        "planted_mode": {"frequency_hz": DEFAULT_MODE.frequency_hz,
                         "q": DEFAULT_MODE.q,
                         "damping_ratio": DEFAULT_MODE.damping_ratio},
        "recovered_mode": fit.as_dict(),
        "recovered_frequency_within_budget": f_ok,
        "recovered_q_within_budget": q_ok,
        "fault_reading_flagged_clipped": clipped_flagged,
        "identified_mode_count": len(ids),
        "specimen_free_of_fixture_mode": specimen_free_of_fixture,
        "refusals": [
            "REAL_DEVICE mechanical read raises NoHardwareError (acquires "
            "nothing)",
            "a mode at/above Nyquist is refused (aliasing) before any sample",
            "a record with missing samples (NaN) is refused for fitting",
            "a spectral feature within noise is not a mode "
            "(refuse_noise_as_resonance)",
            "refuse_fit_as_measurement (a synthetic fit is not a measurement)",
            "refuse_synthetic_Q_as_device_Q (a synthetic Q is not a device Q)",
            "refuse_prediction_as_measurement (a MODEL_PREDICTION is not a "
            "measurement)",
        ],
        "fit_claim_class": FIT_CLAIM_CLASS.value,
        "prediction_claim_class": PREDICTION_CLAIM_CLASS.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "physical_acquisition_status": PHYSICAL_ACQUISITION_STATUS,
        "hardware_status": (
            "no accelerometer, microphone, shaker or vibrometer exists here; "
            "a REAL_DEVICE mechanical read is BLOCKED and the physical run is "
            "PREREGISTERED_NOT_RUN"),
        "what_would_change_this": (
            "a specimen mounted on a calibrated fixture, driven by a shaker "
            "or impact hammer, its acceleration/acoustic/ring-down response "
            "captured on a calibrated transducer with a clock binding, an "
            "environment log, an immutable raw artifact and an uncertainty "
            "budget -- none of which exists in this repository"),
        "what_this_does_not_say": (
            "It does not say any specimen was measured. fit_ringdown and "
            "fit_modal_frequencies recover modes PLANTED in a SYNTHETIC "
            "record; there is no accelerometer, microphone, shaker or "
            "vibrometer in this repository. A fitted f, Q or zeta is a "
            "SYNTHETIC_OBSERVATION, and a predicted modal frequency is a "
            "MODEL_PREDICTION; neither is a PHYSICAL_MEASUREMENT. The "
            "physical acquisition is PREREGISTERED_NOT_RUN. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION", "ANALYSIS_VERSION",
    "FIT_CLAIM_CLASS", "PREDICTION_CLAIM_CLASS", "SOFTWARE_CLAIM_CLASS",
    "PHYSICAL_ACQUISITION_STATUS", "MODE_PROMINENCE_MIN",
    "MechanicalError", "MechanicalChannel", "ModalMode",
    "DEFAULT_MODE", "DEFAULT_MODES", "synthesize_modal_record", "ModalDriver",
    "MechanicalLane", "build_synthetic_lane", "build_real_lane",
    "build_replay_lane", "build_fault_lane",
    "DEFAULT_BUDGET_COMPONENTS", "MechanicalErrorBudget", "DEFAULT_BUDGET",
    "FittedMode", "fit_ringdown", "fit_modal_frequencies",
    "is_genuine_mode", "assert_mode_above_noise", "separate_fixture_specimen",
    "aliasing_risk", "clipping_fraction", "is_clipped",
    "frf", "coherence", "integrate_spectral", "to_velocity", "to_displacement",
    "ModeShapeField", "mode_shape_placeholder", "predicted_rod_mode_hz",
    "channel_band_ok", "modal_observation_record",
    "refuse_fit_as_measurement", "refuse_synthetic_Q_as_device_Q",
    "refuse_prediction_as_measurement", "mechanical_report",
]
