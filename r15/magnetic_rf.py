"""P17 — the magnetic and RF measurement lane.

This lane reads two coupled instruments and their one shared trap. A
**magnetometer** (a Hall plate or a fluxgate) reports a DC/AC magnetic flux
density; an **RF front end** (a spectrum analyser fed by a near-field probe
or a shielded loop antenna) reports power against frequency; and a
**magnetic-field-dependent frequency shift** binds them -- a spectral line
whose centre moves with the applied field. The lane recovers a planted line
and a planted field shift (that is POWER), and it refuses to call the
things that only *look* like signals a signal.

**Four device modes, kept distinct.**

* ``REAL_DEVICE`` is an interface only. No magnetometer, probe, antenna or
  analyser exists in this repository, so :class:`RealMagneticRFDevice`
  acquires nothing and raises; its physical run is ``PREREGISTERED_NOT_RUN``.
* ``SYNTHETIC_DEVICE`` builds a deterministic B-field trace and a
  deterministic RF spectrum from a closed-form model plus seeded noise under
  ``numpy.random.default_rng(seed)``. Its output is a
  ``SYNTHETIC_OBSERVATION`` -- generated here from a known model, never
  transduced from a specimen.
* ``REPLAY_DEVICE`` replays a previously recorded synthetic artifact
  byte-for-byte.
* ``FAULT_INJECTION_DEVICE`` wraps a synthetic trace and injects a named
  defect: clipping, drift, saturation, packet loss and missing samples in
  the time domain; EMI ingress, intermodulation products and spurs in the
  spectrum.

**The ordinary-explanation firewall for RF.** Ambient EMI and the RF
background are a ``KNOWN_ORDINARY_EFFECT``. A mains harmonic (60 Hz and its
multiples), a harmonic of a known drive, an intermodulation product of two
drives, or a spectrum-analyser spur is *not* a signal, and
:func:`refuse_emi_as_signal` raises rather than promote one. A line that
does not exceed the combined uncertainty budget is noise, not a resonance.

Nothing here is measured. Every trace is simulator output in model units
(tesla, dBm); the strongest class this lane reaches is
``SYNTHETIC_OBSERVATION``. ``PHYSICAL_VALIDATION_NOT_CLAIMED``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Mapping, Sequence

import numpy as np

from r15 import claims
from r11.detectors import DetectorKind, Observable, bandwidth_ok, capability
from r13.chiral import Helicity
from r13.magroot import (
    IGRF_ORIENTATION_REFERENCE_A,
    orientation_from_field,
    root_alias_set,
)

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
ANALYSIS_VERSION = "magnetic_rf-1.0"
VERDICT = "MAGNETIC_RF_LANE_FOUR_MODES_NO_PROMOTION"

#: The magnetometer this lane models is a Hall element; its capability and
#: bandwidth are the R11 authority's, reused rather than re-declared.
MAGNETOMETER_DETECTOR = DetectorKind.HALL


class MagneticRFError(RuntimeError):
    """Raised on a malformed input or a forbidden magnetic/RF promotion."""


class NoHardwareError(MagneticRFError):
    """Raised when a REAL_DEVICE is asked to acquire. There is none."""


# --- the four device modes -----------------------------------------------

class DeviceMode(Enum):
    """The four acquisition modes, kept distinct across the lane."""

    REAL_DEVICE = "REAL_DEVICE"
    SYNTHETIC_DEVICE = "SYNTHETIC_DEVICE"
    REPLAY_DEVICE = "REPLAY_DEVICE"
    FAULT_INJECTION_DEVICE = "FAULT_INJECTION_DEVICE"


class MagnetometerKind(Enum):
    """The two magnetometer front ends this lane models."""

    HALL = "hall"
    FLUXGATE = "fluxgate"


class FaultKind(Enum):
    """The defects the fault-injection device can plant.

    The first five corrupt the time-domain magnetometer trace; the last
    three corrupt the RF spectrum -- and each of the RF three is an ordinary
    RF pathology, not a signal.
    """

    CLIPPING = "clipping"
    DRIFT = "drift"
    SATURATION = "saturation"
    PACKET_LOSS = "packet_loss"
    MISSING_SAMPLES = "missing_samples"
    EMI_INGRESS = "emi_ingress"
    INTERMOD = "intermod"
    SPUR = "spur"


#: Faults that act on the time-domain magnetometer trace.
TIME_DOMAIN_FAULTS = frozenset({
    FaultKind.CLIPPING, FaultKind.DRIFT, FaultKind.SATURATION,
    FaultKind.PACKET_LOSS, FaultKind.MISSING_SAMPLES,
})
#: Faults that act on the RF spectrum, each an ordinary RF pathology.
SPECTRAL_FAULTS = frozenset({
    FaultKind.EMI_INGRESS, FaultKind.INTERMOD, FaultKind.SPUR,
})


class FeatureKind(Enum):
    """What a spectral line is, once the ordinary explanations are tried."""

    SIGNAL_CANDIDATE = "SIGNAL_CANDIDATE"
    MAINS_PICKUP = "MAINS_PICKUP"
    HARMONIC = "HARMONIC"
    INTERMOD = "INTERMOD"
    RF_SPUR = "RF_SPUR"


#: The feature kinds that are ordinary effects, never a signal.
ORDINARY_FEATURE_KINDS = frozenset({
    FeatureKind.MAINS_PICKUP, FeatureKind.HARMONIC,
    FeatureKind.INTERMOD, FeatureKind.RF_SPUR,
})

#: The error-budget components this lane names. ``rf_background`` is the
#: ambient EMI/RF term -- the KNOWN_ORDINARY_EFFECT floor a candidate must
#: clear before it is even a candidate.
CANONICAL_BUDGET_COMPONENTS = (
    "magnetometer_noise",
    "rf_background",
    "calibration",
    "clock",
    "quantization",
    "shielding_leakage",
)

#: The conventional mains fundamental (model units). Its integer multiples
#: are mains pickup, an ordinary effect.
MAINS_HZ = 60.0


# --- antenna geometry and shielding --------------------------------------

@dataclass(frozen=True)
class AntennaGeometry:
    """A near-field probe or loop antenna's geometry and shielding.

    Tracked so that an observation carries the aperture, orientation and
    shielding it was taken with. ``orientation`` is a 3-vector direction of
    the loop normal; ``shielding_db`` is the enclosure attenuation.
    """

    probe_type: str
    loop_area_m2: float
    turns: int
    orientation: tuple[float, float, float]
    shielding_db: float
    standoff_m: float

    def __post_init__(self) -> None:
        if self.loop_area_m2 <= 0.0:
            raise MagneticRFError("loop_area_m2 must be positive")
        if self.turns < 1:
            raise MagneticRFError("turns must be >= 1")
        if self.shielding_db < 0.0:
            raise MagneticRFError("shielding_db must be non-negative")
        if self.standoff_m < 0.0:
            raise MagneticRFError("standoff_m must be non-negative")
        v = np.asarray(self.orientation, dtype=float)
        if v.shape != (3,) or not np.all(np.isfinite(v)) or \
                float(np.linalg.norm(v)) <= 0.0:
            raise MagneticRFError(
                "orientation must be a finite non-zero 3-vector")

    def normal_unit(self) -> tuple[float, float, float]:
        v = np.asarray(self.orientation, dtype=float)
        u = v / float(np.linalg.norm(v))
        return (float(u[0]), float(u[1]), float(u[2]))

    def shielding_linear(self) -> float:
        """The shielding as a linear amplitude factor (<= 1)."""
        return float(10.0 ** (-self.shielding_db / 20.0))

    def orientation_reference(self, field_dir) -> dict:
        """Recover the probe attitude from the field, up to the axis turn.

        Reuses the R13 IGRF orientation reference: one field vector fixes
        two rotational degrees of freedom, never three. Ties the antenna
        geometry to a stated attitude with its ambiguity named.
        """
        return orientation_from_field(field_dir, self.normal_unit())


# --- RF band and clock binding -------------------------------------------

@dataclass(frozen=True)
class RFBand:
    """An RF measurement band, bound to a resolution bandwidth."""

    f_start_hz: float
    f_stop_hz: float
    rbw_hz: float

    def __post_init__(self) -> None:
        if self.f_start_hz < 0.0 or self.f_stop_hz <= self.f_start_hz:
            raise MagneticRFError(
                "RFBand needs 0 <= f_start < f_stop")
        if self.rbw_hz <= 0.0:
            raise MagneticRFError("rbw_hz must be positive")
        if self.rbw_hz > (self.f_stop_hz - self.f_start_hz):
            raise MagneticRFError(
                "rbw_hz cannot exceed the band span")

    @property
    def span_hz(self) -> float:
        return float(self.f_stop_hz - self.f_start_hz)

    @property
    def center_hz(self) -> float:
        return 0.5 * (self.f_start_hz + self.f_stop_hz)

    @property
    def n_bins(self) -> int:
        return int(round(self.span_hz / self.rbw_hz)) + 1

    def freqs(self) -> np.ndarray:
        return np.linspace(self.f_start_hz, self.f_stop_hz, self.n_bins)


@dataclass(frozen=True)
class ClockBinding:
    """The clock/timebase an RF or magnetometer trace is bound to."""

    sample_rate_hz: float
    clock_source: str
    epoch_s: float

    def __post_init__(self) -> None:
        if self.sample_rate_hz <= 0.0:
            raise MagneticRFError("sample_rate_hz must be positive")
        if not self.clock_source:
            raise MagneticRFError("a clock binding needs a named source")

    @property
    def nyquist_hz(self) -> float:
        return 0.5 * self.sample_rate_hz

    def covers(self, freq_hz: float) -> bool:
        """Is a frequency inside the Nyquist limit of this clock?"""
        return 0.0 <= float(freq_hz) <= self.nyquist_hz


# --- the error budget ----------------------------------------------------

@dataclass(frozen=True)
class MagneticRFBudget:
    """A magnetic/RF combined uncertainty, decomposed per R15 policy.

    ``components`` maps a subset of :data:`CANONICAL_BUDGET_COMPONENTS` to a
    non-negative standard uncertainty in ``units``; the combined uncertainty
    is their quadrature (root-sum-square) sum. ``rf_background`` -- the
    ambient EMI/RF floor -- is a required component: a lane that does not
    account for the background cannot judge whether a line is a signal.
    """

    quantity: str
    units: str
    components: Mapping[str, float]
    coverage_factor: float = 2.0

    def __post_init__(self) -> None:
        comps = dict(self.components)
        if not comps:
            raise MagneticRFError(
                "an error budget with no components declares no uncertainty")
        unknown = set(comps) - set(CANONICAL_BUDGET_COMPONENTS)
        if unknown:
            raise MagneticRFError(
                f"unknown budget component(s) {sorted(unknown)}; policy "
                f"names {list(CANONICAL_BUDGET_COMPONENTS)}")
        if "rf_background" not in comps:
            raise MagneticRFError(
                "the ambient rf_background component is required; it is the "
                "KNOWN_ORDINARY_EFFECT floor a candidate line must clear")
        clean: dict[str, float] = {}
        for name, value in comps.items():
            v = float(value)
            if not math.isfinite(v) or v < 0.0:
                raise MagneticRFError(
                    f"budget component {name!r} must be finite and "
                    f"non-negative, got {value!r}")
            clean[name] = v
        if self.coverage_factor <= 0.0:
            raise MagneticRFError("coverage_factor must be positive")
        object.__setattr__(self, "components", clean)

    def combined(self) -> float:
        return math.sqrt(sum(v * v for v in self.components.values()))

    def expanded(self) -> float:
        """The expanded uncertainty: combined * coverage_factor."""
        return self.combined() * float(self.coverage_factor)

    def to_record(self, budget_id: str) -> dict:
        """A dict conforming to ``error_budget.schema.json``."""
        return {
            "budget_id": budget_id,
            "quantity": self.quantity,
            "components": [
                {"name": name, "value": self.components[name],
                 "units": self.units}
                for name in CANONICAL_BUDGET_COMPONENTS
                if name in self.components
            ],
            "combination_method": "root_sum_square",
            "combined_uncertainty": self.combined(),
            "coverage_factor": float(self.coverage_factor),
        }


# --- the observation record ----------------------------------------------

@dataclass(frozen=True)
class MagneticRFObservation:
    """A typed magnetic/RF observation, schema-shaped and claim-capped."""

    observation_id: str
    run_id: str
    quantity: str
    value: object
    units: str
    uncertainty: Mapping[str, object]
    device_mode: DeviceMode
    source_artifacts: tuple = ()
    claim_class: claims.ClaimClass = claims.ClaimClass.SYNTHETIC_OBSERVATION
    analysis_version: str = ANALYSIS_VERSION

    def __post_init__(self) -> None:
        if self.claim_class in claims.MEASUREMENT_CLASSES:
            raise MagneticRFError(
                f"refused: {self.observation_id} claims "
                f"{self.claim_class.value}, a measurement class; this lane "
                f"acquires no physical data. {PHYSICAL_VALIDATION}")

    def to_record(self) -> dict:
        """A dict conforming to ``observation_record.schema.json``."""
        return {
            "observation_id": self.observation_id,
            "run_id": self.run_id,
            "source_artifacts": list(self.source_artifacts),
            "analysis_version": self.analysis_version,
            "quantity": self.quantity,
            "value": self.value,
            "units": self.units,
            "uncertainty": dict(self.uncertainty),
            "claim_class": self.claim_class.value,
            "device_mode": self.device_mode.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


# --- the deterministic synthetic models ----------------------------------

@dataclass(frozen=True)
class MagneticRFConfig:
    """The knobs of the deterministic synthetic magnetic/RF source."""

    magnetometer: MagnetometerKind = MagnetometerKind.HALL
    offset_t: float = 5.0e-5        # DC field offset (tesla)
    gyro_hz_per_t: float = 2.8e10   # line shift per tesla (model gyromag.)
    f0_hz: float = 1.0e6            # line centre at zero applied field
    ac_amp_t: float = 1.0e-7        # AC field amplitude
    ac_hz: float = 5.0e1            # AC field frequency
    b_noise_t: float = 1.0e-8       # magnetometer noise (tesla)
    line_amp: float = 1.0           # planted RF line amplitude (linear)
    background: float = 1.0e-3      # ambient RF background floor (linear)
    rf_noise: float = 1.0e-4        # RF noise sigma (linear)


def line_freq_from_field(config: MagneticRFConfig, applied_t: float) -> float:
    """The RF line centre for an applied field: ``f0 + gyro * B``.

    This is the magnetic-field-dependent frequency shift that binds the two
    instruments: the spectral line moves linearly with the applied field.
    """
    return float(config.f0_hz + config.gyro_hz_per_t * float(applied_t))


def field_from_line_freq(config: MagneticRFConfig, line_hz: float) -> float:
    """Invert :func:`line_freq_from_field` to recover the applied field."""
    if config.gyro_hz_per_t == 0.0:
        raise MagneticRFError("a zero gyromagnetic ratio cannot be inverted")
    return float((float(line_hz) - config.f0_hz) / config.gyro_hz_per_t)


def synth_bfield(config: MagneticRFConfig, *, n_samples: int, seed: int,
                 clock: ClockBinding, applied_t: float = 0.0) -> np.ndarray:
    """A deterministic magnetometer trace (tesla) under a numpy seed."""
    n = int(n_samples)
    if n < 1:
        raise MagneticRFError("n_samples must be positive")
    rng = np.random.default_rng(int(seed))
    t = np.arange(n, dtype=float) / clock.sample_rate_hz
    dc = config.offset_t + float(applied_t)
    ac = config.ac_amp_t * np.sin(2.0 * math.pi * config.ac_hz * t)
    noise = config.b_noise_t * rng.standard_normal(n)
    return dc + ac + noise


def synth_rf_spectrum(config: MagneticRFConfig, band: RFBand, *, seed: int,
                      applied_t: float = 0.0,
                      emi_lines: Sequence[float] = ()) -> tuple:
    """A deterministic RF power spectrum (freqs, power) under a seed.

    A flat background floor plus seeded noise, a planted narrow line at the
    field-shifted centre, and any ambient EMI lines requested. The planted
    line is what :func:`recover_rf_line` recovers -- that is POWER.
    """
    rng = np.random.default_rng(int(seed))
    freqs = band.freqs()
    power = config.background + config.rf_noise * np.abs(
        rng.standard_normal(freqs.size))
    line_hz = line_freq_from_field(config, applied_t)
    power = _add_line(freqs, power, line_hz, config.line_amp, band.rbw_hz)
    for emi_hz in emi_lines:
        power = _add_line(freqs, power, float(emi_hz),
                          0.5 * config.line_amp, band.rbw_hz)
    return freqs, power


def _add_line(freqs: np.ndarray, power: np.ndarray, center_hz: float,
              amp: float, rbw_hz: float) -> np.ndarray:
    """Add a narrow Gaussian line of width ~rbw at center_hz."""
    if center_hz < freqs[0] or center_hz > freqs[-1]:
        return power
    sigma = max(rbw_hz, 1e-30)
    line = amp * np.exp(-0.5 * ((freqs - center_hz) / sigma) ** 2)
    return power + line


# --- recovery: POWER on a planted line and a planted field shift ----------

def recover_rf_line(freqs: np.ndarray, power: np.ndarray,
                    budget: MagneticRFBudget) -> dict:
    """Recover the strongest spectral line and test it against the budget.

    Returns the peak frequency, its height above the background, and an
    ``above_budget`` flag. A line that does not exceed the expanded
    uncertainty is noise, not a resonance -- the caller must not promote it.
    """
    freqs = np.asarray(freqs, dtype=float)
    power = np.asarray(power, dtype=float)
    if freqs.shape != power.shape or freqs.size < 2:
        raise MagneticRFError("freqs and power must be equal-length arrays")
    baseline = float(np.median(power))
    idx = int(np.argmax(power))
    peak_freq = float(freqs[idx])
    height = float(power[idx] - baseline)
    threshold = budget.expanded()
    return {
        "peak_freq_hz": peak_freq,
        "peak_height": height,
        "baseline": baseline,
        "expanded_uncertainty": threshold,
        "above_budget": height > threshold,
        "claim_class": claims.ClaimClass.SYNTHETIC_OBSERVATION.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


def recover_field_shift(config: MagneticRFConfig, freqs: np.ndarray,
                        power: np.ndarray, budget: MagneticRFBudget) -> dict:
    """Recover the applied field from the RF line's shifted centre.

    Inverts the field-dependent frequency shift on the recovered line. POWER
    when the line clears the budget: the planted field is returned.
    """
    line = recover_rf_line(freqs, power, budget)
    if not line["above_budget"]:
        claims.refuse_noise_as_resonance()
    recovered_t = field_from_line_freq(config, line["peak_freq_hz"])
    return {
        "recovered_field_t": recovered_t,
        "line_freq_hz": line["peak_freq_hz"],
        "above_budget": line["above_budget"],
        "claim_class": claims.ClaimClass.SYNTHETIC_OBSERVATION.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


# --- the ordinary-explanation firewall for RF ----------------------------

def classify_feature(freq_hz: float, *, drive_fundamentals: Sequence[float] = (),
                     mains_hz: float = MAINS_HZ, tol_hz: float = 1.0,
                     max_order: int = 8) -> dict:
    """Type a spectral feature: mains, harmonic, intermod, spur, or candidate.

    Tries the ordinary explanations first, in a fixed precedence, so a line
    is only ever a ``SIGNAL_CANDIDATE`` once mains pickup, a drive harmonic
    and an intermodulation product have all been ruled out.
    """
    f = float(freq_hz)
    if f <= 0.0:
        raise MagneticRFError("a feature frequency must be positive")
    tol = float(tol_hz)

    # 1. mains harmonics
    if mains_hz > 0.0:
        k = round(f / mains_hz)
        if k >= 1 and abs(f - k * mains_hz) <= tol:
            return _feature(FeatureKind.MAINS_PICKUP, f,
                            f"{k}x mains ({mains_hz} Hz)")

    funds = [float(x) for x in drive_fundamentals if x > 0.0]
    # 2. harmonics of a single drive
    for f1 in funds:
        k = round(f / f1)
        if k >= 2 and abs(f - k * f1) <= tol:
            return _feature(FeatureKind.HARMONIC, f,
                            f"{k}x drive ({f1} Hz)")
    # 3. intermodulation products m*f1 +/- n*f2
    for i, f1 in enumerate(funds):
        for f2 in funds[i:]:
            for m in range(1, max_order + 1):
                for n in range(1, max_order + 1):
                    for sign in (1.0, -1.0):
                        prod = m * f1 + sign * n * f2
                        if prod > 0.0 and abs(f - prod) <= tol:
                            return _feature(
                                FeatureKind.INTERMOD, f,
                                f"{m}*{f1} {'+' if sign > 0 else '-'} "
                                f"{n}*{f2}")
    # 4. otherwise a candidate (subject to the budget test elsewhere)
    return _feature(FeatureKind.SIGNAL_CANDIDATE, f, "no ordinary match")


def _feature(kind: FeatureKind, freq_hz: float, detail: str) -> dict:
    return {
        "feature_kind": kind.value,
        "freq_hz": float(freq_hz),
        "is_ordinary": kind in ORDINARY_FEATURE_KINDS,
        "detail": detail,
    }


def localize_interference(freq_hz: float, known_sources: Mapping[str, float],
                          *, tol_hz: float = 1.0) -> dict:
    """Localize a feature to a named known interference source.

    ``known_sources`` maps a source name to its frequency. A match localizes
    the feature to exactly that source -- the interference is accounted for,
    not a mystery.
    """
    f = float(freq_hz)
    for name, src_hz in known_sources.items():
        if abs(f - float(src_hz)) <= float(tol_hz):
            return {
                "localized": True,
                "source": name,
                "source_hz": float(src_hz),
                "freq_hz": f,
                "feature_kind": FeatureKind.RF_SPUR.value
                if "spur" in name.lower() else FeatureKind.MAINS_PICKUP.value,
                "is_ordinary": True,
            }
    return {"localized": False, "source": None, "freq_hz": f,
            "is_ordinary": False}


# --- reversal and dummy-load controls ------------------------------------

def coil_reversal_demodulate(forward: np.ndarray, reverse: np.ndarray) -> dict:
    """Separate a field-linear response from pickup by coil reversal.

    A genuine field-linear magnetic response reverses sign when the drive
    coil current reverses; rectified pickup and EMI do not. The odd part
    ``(forward - reverse)/2`` isolates the field-linear signal; the even part
    ``(forward + reverse)/2`` is the pickup that survives reversal.

    Reversal signs propagate: the sign of the field-linear part follows the
    drive polarity, labelled with the R13 helicity sense.
    """
    fwd = np.asarray(forward, dtype=float)
    rev = np.asarray(reverse, dtype=float)
    if fwd.shape != rev.shape or fwd.size < 1:
        raise MagneticRFError(
            "forward and reverse traces must be equal-length arrays")
    field_linear = 0.5 * (fwd - rev)
    pickup = 0.5 * (fwd + rev)
    mean_signal = float(np.mean(field_linear))
    helicity = (Helicity.LEFT if mean_signal > 0.0
                else Helicity.RIGHT if mean_signal < 0.0 else Helicity.LINEAR)
    return {
        "field_linear": field_linear,
        "pickup": pickup,
        "field_linear_mean": mean_signal,
        "pickup_mean": float(np.mean(pickup)),
        "sign": int(np.sign(mean_signal)),
        "reversal_sense": helicity.value,
        "claim_class": claims.ClaimClass.SYNTHETIC_OBSERVATION.value,
    }


def dummy_load_control(specimen_power: np.ndarray, dummy_power: np.ndarray,
                       freqs: np.ndarray, *, tol: float | None = None) -> dict:
    """Expose pickup by comparing a specimen run to a dummy-load run.

    A dummy load presents the same electronics with no specimen. Any line
    that survives in the dummy spectrum is pickup, not specimen response; a
    line present only with the specimen is a candidate. Dummy loads expose
    pickup.
    """
    spec = np.asarray(specimen_power, dtype=float)
    dummy = np.asarray(dummy_power, dtype=float)
    freqs = np.asarray(freqs, dtype=float)
    if not (spec.shape == dummy.shape == freqs.shape) or spec.size < 2:
        raise MagneticRFError(
            "specimen, dummy and freqs must be equal-length arrays")
    thr = float(tol) if tol is not None else 3.0 * float(np.median(dummy))
    dummy_lines = freqs[dummy - np.median(dummy) > thr]
    spec_lines = freqs[spec - np.median(spec) > thr]
    pickup = sorted(float(f) for f in dummy_lines)
    dummy_set = set(np.round(dummy_lines, 6))
    candidates = sorted(
        float(f) for f in spec_lines
        if round(float(f), 6) not in dummy_set)
    return {
        "pickup_freqs": pickup,
        "candidate_freqs": candidates,
        "pickup_exposed": bool(pickup),
        "claim_class": claims.ClaimClass.SYNTHETIC_OBSERVATION.value,
    }


# --- the forbidden RF promotion ------------------------------------------

def refuse_emi_as_signal(freq_hz: float = MAINS_HZ,
                         kind: str = "mains_harmonic", **_k) -> None:
    """Ambient EMI / a spur / a mains harmonic is not a signal. Always raises.

    An RF spur, a mains harmonic, or the ambient RF background is a
    ``KNOWN_ORDINARY_EFFECT``. Calling one a signal promotes an ordinary
    effect past the firewall, which this refuses.
    """
    raise MagneticRFError(
        f"refused: a {kind} at {freq_hz} Hz is a KNOWN_ORDINARY_EFFECT "
        f"(ambient EMI / RF background / mains pickup / analyser spur), not "
        f"a signal. It must be localized to its source and subtracted, never "
        f"promoted to a SIGNAL_CANDIDATE. {PHYSICAL_VALIDATION}")


# --- the four devices ----------------------------------------------------

@dataclass(frozen=True)
class RealMagneticRFDevice:
    """A REAL_DEVICE interface. It acquires nothing: there is no hardware."""

    magnetometer: MagnetometerKind = MagnetometerKind.HALL
    device_mode: DeviceMode = DeviceMode.REAL_DEVICE

    def acquire(self, *_a, **_k):
        raise NoHardwareError(
            "refused: no magnetometer, near-field probe, antenna or spectrum "
            "analyser exists in this repository. A REAL_DEVICE acquisition "
            f"is PREREGISTERED_NOT_RUN. {PHYSICAL_VALIDATION}")

    def status(self) -> dict:
        return {
            "device_mode": self.device_mode.value,
            "physical_run": "PREREGISTERED_NOT_RUN",
            "acquires": "nothing",
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


@dataclass(frozen=True)
class SyntheticMagneticRFDevice:
    """A SYNTHETIC_DEVICE. Deterministic B-field and RF spectrum from a seed."""

    config: MagneticRFConfig = field(default_factory=MagneticRFConfig)
    device_mode: DeviceMode = DeviceMode.SYNTHETIC_DEVICE

    def acquire_bfield(self, *, n_samples: int, seed: int,
                       clock: ClockBinding, applied_t: float = 0.0
                       ) -> np.ndarray:
        return synth_bfield(self.config, n_samples=n_samples, seed=seed,
                            clock=clock, applied_t=applied_t)

    def acquire_spectrum(self, band: RFBand, *, seed: int,
                         applied_t: float = 0.0,
                         emi_lines: Sequence[float] = ()) -> tuple:
        return synth_rf_spectrum(self.config, band, seed=seed,
                                 applied_t=applied_t, emi_lines=emi_lines)

    def bandwidth_ok(self, freq_hz: float) -> bool:
        """Reuse the R11 Hall bandwidth to bind the magnetometer band."""
        return bandwidth_ok(MAGNETOMETER_DETECTOR, freq_hz)


@dataclass(frozen=True)
class ReplayMagneticRFDevice:
    """A REPLAY_DEVICE. Returns a recorded synthetic artifact unchanged."""

    recorded: np.ndarray
    device_mode: DeviceMode = DeviceMode.REPLAY_DEVICE

    def replay(self) -> np.ndarray:
        return np.array(self.recorded, dtype=float, copy=True)


@dataclass(frozen=True)
class FaultInjectionMagneticRFDevice:
    """A FAULT_INJECTION_DEVICE. Plants one named defect into synthetic data.

    Time-domain faults (clipping, drift, saturation, packet loss, missing
    samples) corrupt a magnetometer trace; spectral faults (EMI ingress,
    intermod, spur) add an ordinary RF pathology to a spectrum. Each is
    deterministic under a seed.
    """

    fault: FaultKind
    device_mode: DeviceMode = DeviceMode.FAULT_INJECTION_DEVICE
    rail: float = 4.0e-5
    drift_rate: float = 1.0e-6
    block: int = 8
    line_hz: float = 180.0
    line_amp: float = 0.5

    def inject_timeseries(self, trace: np.ndarray, *, seed: int = 0
                          ) -> np.ndarray:
        if self.fault not in TIME_DOMAIN_FAULTS:
            raise MagneticRFError(
                f"{self.fault.value} is a spectral fault; use "
                f"inject_spectrum")
        x = np.array(trace, dtype=float, copy=True)
        n = x.size
        rng = np.random.default_rng(int(seed))
        if self.fault is FaultKind.CLIPPING:
            return np.clip(x, -self.rail, self.rail)
        if self.fault is FaultKind.DRIFT:
            return x + self.drift_rate * np.arange(n, dtype=float)
        if self.fault is FaultKind.SATURATION:
            return self.rail * np.tanh(x / self.rail)
        if self.fault is FaultKind.PACKET_LOSS:
            start = int(rng.integers(0, max(1, n - self.block)))
            x[start:start + self.block] = 0.0
            return x
        if self.fault is FaultKind.MISSING_SAMPLES:
            k = min(self.block, n)
            idx = rng.choice(n, size=k, replace=False)
            x[idx] = np.nan
            return x
        raise MagneticRFError(f"unhandled time fault {self.fault}")

    def inject_spectrum(self, freqs: np.ndarray, power: np.ndarray, *,
                        drive_fundamentals: Sequence[float] = (),
                        rbw_hz: float = 1.0) -> tuple:
        if self.fault not in SPECTRAL_FAULTS:
            raise MagneticRFError(
                f"{self.fault.value} is a time-domain fault; use "
                f"inject_timeseries")
        freqs = np.asarray(freqs, dtype=float)
        power = np.array(power, dtype=float, copy=True)
        if self.fault is FaultKind.EMI_INGRESS:
            # a mains harmonic ingresses into the spectrum
            center = self.line_hz
        elif self.fault is FaultKind.SPUR:
            center = self.line_hz
        elif self.fault is FaultKind.INTERMOD:
            funds = [float(x) for x in drive_fundamentals if x > 0.0]
            if len(funds) < 2:
                raise MagneticRFError(
                    "an intermod fault needs two drive fundamentals")
            center = 2.0 * funds[0] - funds[1]
        else:  # pragma: no cover
            raise MagneticRFError(f"unhandled spectral fault {self.fault}")
        power = _add_line(freqs, power, center, self.line_amp, rbw_hz)
        return freqs, power, center


# --- the standing report -------------------------------------------------

def magnetic_rf_report() -> dict:
    """The standing statement of what this lane is and is not."""
    return {
        "what_this_is": (
            "the magnetic and RF measurement lane -- a magnetometer "
            "(Hall/fluxgate) trace, an RF near-field/spectrum readout, and a "
            "magnetic-field-dependent frequency shift binding them -- in four "
            "distinct device modes"),
        "device_modes": [m.value for m in DeviceMode],
        "real_device": "PREREGISTERED_NOT_RUN (no hardware; acquires nothing)",
        "magnetometer_kinds": [m.value for m in MagnetometerKind],
        "fault_kinds": [f.value for f in FaultKind],
        "budget_components": list(CANONICAL_BUDGET_COMPONENTS),
        "ambient_emi_is": claims.ClaimClass.KNOWN_ORDINARY_EFFECT.value,
        "feature_kinds": [k.value for k in FeatureKind],
        "ordinary_feature_kinds": [k.value for k in ORDINARY_FEATURE_KINDS],
        "forbidden_promotions": [
            "refuse_emi_as_signal (EMI/spur/mains harmonic is not a signal)",
            "refuse_noise_as_resonance (a line under budget is noise)",
            "refuse_synthetic_as_physical (a synthetic trace is not measured)",
        ],
        "reused_authorities": {
            "r11.detectors": "Hall magnetometer capability and bandwidth",
            "r13.magroot": "antenna orientation reference and alias limits",
            "r13.chiral": "reversal-sign (helicity) sense",
            "r15.claims": "claim taxonomy and forbidden promotions",
        },
        "reading_claim_class": claims.ClaimClass.SYNTHETIC_OBSERVATION.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say any B-field or RF spectrum was transduced from a "
            "specimen. Every trace is simulator output in model units; no "
            "magnetometer, probe, antenna or analyser exists here. A "
            "SYNTHETIC_OBSERVATION is not a PHYSICAL_MEASUREMENT, an RF spur "
            "or mains harmonic is a KNOWN_ORDINARY_EFFECT and not a signal, "
            "and a line below the combined uncertainty is noise, not a "
            f"resonance. {PHYSICAL_VALIDATION}."),
        "verdict": VERDICT,
    }


__all__ = [
    "MEASURED_HERE", "PHYSICAL_VALIDATION", "ANALYSIS_VERSION", "VERDICT",
    "MAGNETOMETER_DETECTOR", "MAINS_HZ", "CANONICAL_BUDGET_COMPONENTS",
    "TIME_DOMAIN_FAULTS", "SPECTRAL_FAULTS", "ORDINARY_FEATURE_KINDS",
    "MagneticRFError", "NoHardwareError",
    "DeviceMode", "MagnetometerKind", "FaultKind", "FeatureKind",
    "AntennaGeometry", "RFBand", "ClockBinding", "MagneticRFBudget",
    "MagneticRFObservation", "MagneticRFConfig",
    "line_freq_from_field", "field_from_line_freq",
    "synth_bfield", "synth_rf_spectrum",
    "recover_rf_line", "recover_field_shift",
    "classify_feature", "localize_interference",
    "coil_reversal_demodulate", "dummy_load_control",
    "refuse_emi_as_signal",
    "RealMagneticRFDevice", "SyntheticMagneticRFDevice",
    "ReplayMagneticRFDevice", "FaultInjectionMagneticRFDevice",
    "magnetic_rf_report",
]
