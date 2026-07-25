"""P01 — the deterministic synthetic drivers behind SYNTHETIC_DEVICE.

The registry in :mod:`r15.instruments` carries no per-type signal
knowledge; it drives a synthetic instrument through the
:class:`~r15.instruments.SyntheticDriver` protocol. This module supplies
the concrete drivers -- one per instrument type -- for a source, a
digitizer, an impedance analyzer, a microphone, an accelerometer, a
photodiode, a thermal sensor, a magnetometer and a clock.

**Every driver is deterministic under a numpy seed.** Each ``generate``
call builds its randomness from ``numpy.random.default_rng(seed)`` and adds
it to a fixed, closed-form signal model. There is no wall-clock time, no
unseeded ``numpy.random`` global, and no external entropy anywhere, so the
same seed always yields the same array and a different seed yields a
different one. That reproducibility is exactly what makes a synthetic
reading a ``SYNTHETIC_OBSERVATION`` and not a measurement: the numbers were
generated here from a known model, not transduced from a specimen.

Nothing here is measured. A source waveform, a digitized trace, an
impedance sweep, an acoustic record, an acceleration record, a photocurrent
trace, a temperature trace, a magnetic trace and a clock series are all
simulator output. No microphone, accelerometer, photodiode, thermometer,
magnetometer, digitizer or oscillator exists in this repository.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from r15 import claims
from r15.instruments import (
    Capability,
    InstrumentMode,
    InstrumentRecord,
    InstrumentStatus,
    SyntheticDevice,
    MEASURED_HERE,
    PHYSICAL_VALIDATION,
)

VERDICT = "SYNTHETIC_DRIVERS_DETERMINISTIC_NOT_MEASURED"


# --- the driver base ------------------------------------------------------

@dataclass(frozen=True)
class BaseSyntheticDriver:
    """A deterministic driver for one instrument type.

    Subclasses set ``instrument_type``, the ``capability`` they serve, a
    default sample rate, and implement :meth:`_model` -- the closed-form
    signal -- and :meth:`_noise_scale`. The public :meth:`generate` seeds a
    generator, evaluates the model on a fixed time base, and adds seeded
    noise, so identical seeds give identical arrays.
    """

    instrument_type: str = "synthetic"
    capability: Capability = Capability.SOURCE
    sample_rate_hz: float = 1.0e4
    noise: float = 1.0e-2

    def default_sample_rate_hz(self, capability: Capability) -> float:
        return float(self.sample_rate_hz)

    def _time_base(self, n: int, rate: float) -> np.ndarray:
        return np.arange(int(n), dtype=float) / float(rate)

    def _model(self, t: np.ndarray, rng: np.random.Generator) -> np.ndarray:
        raise NotImplementedError

    def generate(self, capability: Capability, n_samples: int, seed: int,
                 sample_rate_hz: float) -> np.ndarray:
        if capability is not self.capability:
            raise ValueError(
                f"{self.instrument_type} serves {self.capability.value}, "
                f"not {capability.value}")
        n = int(n_samples)
        if n < 1:
            raise ValueError("n_samples must be positive")
        rng = np.random.default_rng(int(seed))
        t = self._time_base(n, float(sample_rate_hz))
        signal = np.asarray(self._model(t, rng), dtype=float)
        if self.noise:
            signal = signal + float(self.noise) * rng.standard_normal(n)
        return signal


# --- the nine concrete drivers -------------------------------------------

@dataclass(frozen=True)
class SourceDriver(BaseSyntheticDriver):
    """A signal source: a clean stepped/swept sine reference tone."""

    instrument_type: str = "source"
    capability: Capability = Capability.SOURCE
    sample_rate_hz: float = 1.0e5
    noise: float = 5.0e-3
    tone_hz: float = 1.0e3
    amplitude: float = 1.0

    def _model(self, t, rng):
        return self.amplitude * np.sin(2.0 * math.pi * self.tone_hz * t)


@dataclass(frozen=True)
class DigitizerDriver(BaseSyntheticDriver):
    """A digitizer: a quantized noisy sine, as an ADC front end would give."""

    instrument_type: str = "digitizer"
    capability: Capability = Capability.DIGITIZE
    sample_rate_hz: float = 1.0e6
    noise: float = 2.0e-3
    tone_hz: float = 5.0e3
    lsb: float = 1.0 / 4096.0

    def _model(self, t, rng):
        wave = 0.8 * np.sin(2.0 * math.pi * self.tone_hz * t)
        # quantize to the LSB grid: a genuine digitizer artifact
        return np.round(wave / self.lsb) * self.lsb


@dataclass(frozen=True)
class ImpedanceDriver(BaseSyntheticDriver):
    """An impedance analyzer: a resonance magnitude sweep vs sample index."""

    instrument_type: str = "impedance"
    capability: Capability = Capability.IMPEDANCE
    sample_rate_hz: float = 1.0e3
    noise: float = 1.0e-3
    f0_hz: float = 1.0e6
    q: float = 1.0e3
    span_fraction: float = 0.1

    def _model(self, t, rng):
        n = t.size
        # a linear frequency sweep across the resonance, magnitude readout
        lo = self.f0_hz * (1.0 - self.span_fraction)
        hi = self.f0_hz * (1.0 + self.span_fraction)
        f = np.linspace(lo, hi, n)
        x = (f - self.f0_hz) / (self.f0_hz / (2.0 * self.q))
        return 1.0 / np.sqrt(1.0 + x * x)


@dataclass(frozen=True)
class MicrophoneDriver(BaseSyntheticDriver):
    """A microphone: a band-limited acoustic pressure record."""

    instrument_type: str = "microphone"
    capability: Capability = Capability.ACOUSTIC
    sample_rate_hz: float = 4.8e4
    noise: float = 1.0e-2
    tone_hz: float = 4.4e2

    def _model(self, t, rng):
        # a tone plus a second harmonic, as room acoustics would carry
        return (0.6 * np.sin(2.0 * math.pi * self.tone_hz * t)
                + 0.2 * np.sin(2.0 * math.pi * 2.0 * self.tone_hz * t))


@dataclass(frozen=True)
class AccelerometerDriver(BaseSyntheticDriver):
    """An accelerometer: a decaying mechanical vibration record."""

    instrument_type: str = "accelerometer"
    capability: Capability = Capability.ACCELERATION
    sample_rate_hz: float = 1.0e4
    noise: float = 5.0e-3
    tone_hz: float = 1.2e2
    tau_s: float = 0.2

    def _model(self, t, rng):
        return np.exp(-t / self.tau_s) * np.sin(
            2.0 * math.pi * self.tone_hz * t)


@dataclass(frozen=True)
class PhotodiodeDriver(BaseSyntheticDriver):
    """A photodiode: a DC-biased photocurrent with shot-like fluctuations."""

    instrument_type: str = "photodiode"
    capability: Capability = Capability.PHOTOCURRENT
    sample_rate_hz: float = 1.0e6
    noise: float = 0.0  # shot noise is modelled explicitly below
    bias: float = 1.0
    shot: float = 0.02

    def _model(self, t, rng):
        # a steady photocurrent with Poisson-like (shot) fluctuation
        base = self.bias * np.ones_like(t)
        return base + self.shot * rng.standard_normal(t.size)


@dataclass(frozen=True)
class ThermalDriver(BaseSyntheticDriver):
    """A thermal sensor: a slow temperature drift about a setpoint."""

    instrument_type: str = "thermal"
    capability: Capability = Capability.THERMAL
    sample_rate_hz: float = 1.0e1
    noise: float = 2.0e-3
    setpoint_c: float = 25.0
    drift_c: float = 0.05

    def _model(self, t, rng):
        span = t[-1] if t.size > 1 and t[-1] > 0 else 1.0
        return self.setpoint_c + self.drift_c * (t / span)


@dataclass(frozen=True)
class MagneticDriver(BaseSyntheticDriver):
    """A magnetometer: a DC field offset with low-frequency fluctuation."""

    instrument_type: str = "magnetic"
    capability: Capability = Capability.MAGNETIC
    sample_rate_hz: float = 1.0e3
    noise: float = 1.0e-3
    offset_t: float = 5.0e-5
    ripple_hz: float = 5.0e1
    ripple_t: float = 1.0e-6

    def _model(self, t, rng):
        return self.offset_t + self.ripple_t * np.sin(
            2.0 * math.pi * self.ripple_hz * t)


@dataclass(frozen=True)
class ClockDriver(BaseSyntheticDriver):
    """A clock: successive timestamps about a nominal period, with jitter."""

    instrument_type: str = "clock"
    capability: Capability = Capability.TIMEBASE
    sample_rate_hz: float = 1.0e7
    noise: float = 0.0  # jitter is modelled explicitly below
    jitter_s: float = 1.0e-9

    def _model(self, t, rng):
        period = 1.0 / self.sample_rate_hz
        jitter = self.jitter_s * rng.standard_normal(t.size)
        return t + jitter * period / max(period, 1e-30)


#: The nine synthetic drivers, keyed by instrument type.
SYNTHETIC_DRIVERS: dict[str, BaseSyntheticDriver] = {
    "source": SourceDriver(),
    "digitizer": DigitizerDriver(),
    "impedance": ImpedanceDriver(),
    "microphone": MicrophoneDriver(),
    "accelerometer": AccelerometerDriver(),
    "photodiode": PhotodiodeDriver(),
    "thermal": ThermalDriver(),
    "magnetic": MagneticDriver(),
    "clock": ClockDriver(),
}


def driver(instrument_type: str) -> BaseSyntheticDriver:
    """The synthetic driver for one instrument type."""
    try:
        return SYNTHETIC_DRIVERS[instrument_type]
    except KeyError:
        raise KeyError(
            f"{instrument_type!r} has no synthetic driver; available: "
            f"{sorted(SYNTHETIC_DRIVERS)}") from None


def _uncertainty_model(drv: BaseSyntheticDriver) -> dict:
    return {
        "type": "additive_gaussian",
        "sigma": float(drv.noise),
        "sample_rate_hz": float(drv.sample_rate_hz),
        "note": "synthetic noise model; not a measured uncertainty budget",
    }


def synthetic_record(instrument_type: str, *, instrument_id: str | None = None,
                     calibration_ids: tuple = (),
                     firmware: str = "synthetic-1.0",
                     clock_source: str = "synthetic_seeded_rng"
                     ) -> InstrumentRecord:
    """Build a SYNTHETIC_DEVICE :class:`InstrumentRecord` for a driver."""
    drv = driver(instrument_type)
    iid = instrument_id or f"synthetic_{instrument_type}"
    return InstrumentRecord(
        instrument_id=iid,
        instrument_type=instrument_type,
        mode=InstrumentMode.SYNTHETIC_DEVICE,
        firmware=firmware,
        clock_source=clock_source,
        capabilities=frozenset({drv.capability}),
        uncertainty_model=_uncertainty_model(drv),
        calibration_ids=tuple(calibration_ids),
        status=InstrumentStatus.AVAILABLE,
    )


def build_synthetic_device(instrument_type: str, *,
                           instrument_id: str | None = None,
                           calibration_ids: tuple = ()) -> SyntheticDevice:
    """A ready-to-register :class:`SyntheticDevice` for an instrument type."""
    rec = synthetic_record(instrument_type, instrument_id=instrument_id,
                           calibration_ids=calibration_ids)
    return SyntheticDevice(rec, driver(instrument_type))


def synthetic_instruments_report() -> dict:
    """The standing statement of what the drivers are and are not."""
    return {
        "what_this_is": (
            "nine deterministic synthetic drivers -- source, digitizer, "
            "impedance, microphone, accelerometer, photodiode, thermal, "
            "magnetic and clock -- each producing a closed-form signal plus "
            "seeded noise under numpy.random.default_rng(seed)"),
        "drivers": {
            name: {
                "instrument_type": drv.instrument_type,
                "capability": drv.capability.value,
                "default_sample_rate_hz": float(drv.sample_rate_hz),
                "uncertainty_model": _uncertainty_model(drv),
            }
            for name, drv in sorted(SYNTHETIC_DRIVERS.items())
        },
        "determinism": (
            "every driver seeds numpy.random.default_rng(seed); no "
            "wall-clock time, no unseeded global RNG, no external entropy. "
            "Same seed => identical array; different seed => different array"),
        "reading_claim_class": claims.ClaimClass.SYNTHETIC_OBSERVATION.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any of these signals was transduced from a "
            "specimen. Each is simulator output generated here from a known "
            "model under a seed; no microphone, accelerometer, photodiode, "
            "thermometer, magnetometer, digitizer or oscillator exists in "
            "this repository. A SYNTHETIC_OBSERVATION is not a "
            "PHYSICAL_MEASUREMENT. PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT",
    "BaseSyntheticDriver",
    "SourceDriver", "DigitizerDriver", "ImpedanceDriver",
    "MicrophoneDriver", "AccelerometerDriver", "PhotodiodeDriver",
    "ThermalDriver", "MagneticDriver", "ClockDriver",
    "SYNTHETIC_DRIVERS", "driver", "synthetic_record",
    "build_synthetic_device", "synthetic_instruments_report",
]
