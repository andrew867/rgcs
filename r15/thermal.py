"""P16 — the thermal measurement lane: temperature in, drift explained.

Temperature is the quietest way an experiment lies to itself. A resonator's
frequency drifts a few parts per million per kelvin; a delay line's phase
walks as its path expands; a thermometer warms itself with its own bias
current and reads high. None of that is the specimen, and all of it looks
like a slow, clean signal. This lane reads temperature honestly and then
uses it to *explain away* the frequency and phase drift it causes -- the
opposite of discovering something.

**Five inputs, three transducer models.** A temperature comes from a
thermistor (a Beta/Steinhart resistance model), an RTD (a linear
Callendar resistance model), a thermocouple (a linear Seebeck voltage
model), an IR trace replayed from a recording, a manual note, or a
deterministic synthetic simulator. The three electrical transducers invert
a readout into kelvin; the conversion constants are CONVENTIONAL_LITERATURE
figures for a class of sensor, not a calibration of any device.

**Sensors are bound to a place and a lag.** A :class:`ThermalSensor`
carries a location and a first-order response time ``tau``; a sensor is not
a point probe of the specimen, it is a low-pass filter watching the ambient
from somewhere nearby. :func:`apply_sensor_response` models that lag and
:func:`estimate_sensor_lag_samples` recovers it by cross-correlation
(reusing :func:`r13.daq.cross_correlation_lag`).

**Two artifacts are corrected, not measured.** Self-heating (a sensor warms
itself, ``dT = R_theta * P``) and a slow ambient drift are both removed
explicitly. Self-heating is a property of the *sensor*, never the
specimen's output, and :func:`refuse_self_heating_as_specimen` refuses that
confusion.

**Thermal explanation for frequency and phase.** A mode's frequency drifts
with temperature through the thermal coefficient of frequency (TCf), and the
underlying mechanism -- the crystal expanding -- is read from
:mod:`r13.crystalframe`: the alpha-quartz lattice constants expand by their
literature coefficients, so a governing dimension grows and the frequency
falls. :func:`fit_thermal_coefficient` recovers a **planted** TCf from a
``(T, f)`` record, and :func:`thermal_phase_shift` turns a fractional
expansion into a phase walk. A temperature-induced shift is a
``KNOWN_ORDINARY_EFFECT``: :func:`refuse_thermal_drift_as_signal` refuses to
read it as a discovery, and (through :mod:`r11.detectors`) names it as the
thermal-expansion artifact a transducer used out of its domain produces.

**Four modes, kept distinct.** ``REAL_DEVICE`` is an interface only: no
thermometer exists here, so a real read acquires nothing -- it raises
:class:`NoThermalHardwareError` and its physical run is
``PREREGISTERED_NOT_RUN``. ``SYNTHETIC_DEVICE`` produces a deterministic
temperature time-series (and the co-drifting frequency) under a seed, with a
planted drift rate and TCf the fits recover. ``REPLAY_DEVICE`` replays a
recorded synthetic trace byte-for-byte. ``FAULT_INJECTION_DEVICE`` injects
clipping, drift, saturation, packet loss, missing samples and self-heating.

Nothing here is measured. Every synthetic reading is a
``SYNTHETIC_OBSERVATION`` from ``numpy.random.default_rng(seed)`` on a
supplied clock; a manual note is a ``SOURCE_CLAIM``; and a temperature-driven
frequency shift is a ``KNOWN_ORDINARY_EFFECT``. The strongest class this lane
reaches is a synthetic observation, and a synthetic observation is not a
``PHYSICAL_MEASUREMENT``. The verdict is
``R15_THERMAL_LANE_SYNTHETIC_NO_MEASUREMENT``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum

import numpy as np

from r11 import detectors as _detectors
from r13 import crystalframe as _crystalframe
from r13.daq import cross_correlation_lag
from r15 import claims

# --- verdict and standing claim vocabulary -------------------------------

#: The standing verdict for this module.
VERDICT = "R15_THERMAL_LANE_SYNTHETIC_NO_MEASUREMENT"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: A REAL thermal read cannot happen (no hardware) but the protocol is
#: fully specified: the physical run is preregistered, not run.
PREREGISTERED_NOT_RUN = "PREREGISTERED_NOT_RUN"
BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"

#: The class of the lane machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED
#: The ceiling any synthetic/replay reading may carry.
READING_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION
#: A hand-entered temperature is a source claim, not an observation.
MANUAL_CLAIM_CLASS = claims.ClaimClass.SOURCE_CLAIM
#: A temperature-induced frequency/phase shift is a known ordinary effect.
DRIFT_CLAIM_CLASS = claims.ClaimClass.KNOWN_ORDINARY_EFFECT
#: An error budget is a model prediction, not a measured coupling.
BUDGET_CLAIM_CLASS = claims.ClaimClass.MODEL_PREDICTION
#: Sensor conversion constants are cited literature figures.
CONVENTIONAL_LITERATURE = "CONVENTIONAL_LITERATURE"

#: The strongest evidence a deterministic synthetic thermal trace reaches.
MAX_THERMAL_EVIDENCE = claims.EvidenceLevel.E2
#: The quadrature combination label recorded in the error budget.
QUADRATURE = "quadrature_sum_rss"
#: Analysis version stamped on observation records.
ANALYSIS_VERSION = "r15.thermal/1.0.0"

#: CONVENTIONAL_LITERATURE linear thermal-expansion coefficients of
#: alpha-quartz, per kelvin: perpendicular to the c axis (the a axes) and
#: along c. Quoted from the crystallographic literature; NOT measured here.
QUARTZ_ALPHA_A_PER_K = 13.2e-6
QUARTZ_ALPHA_C_PER_K = 7.1e-6

#: Absolute zero, for Celsius<->Kelvin convenience only.
ZERO_CELSIUS_K = 273.15


class ThermalError(RuntimeError):
    """Raised on any thermal-lane refusal or ill-formed input.

    Covers the structural guards (a bad sensor record, a mismatched trace,
    a non-positive response time) and is the base of
    :class:`NoThermalHardwareError`.
    """


class NoThermalHardwareError(ThermalError):
    """Raised when a REAL_DEVICE thermal sensor is asked to acquire.

    No thermometer exists in this repository, so a real acquisition
    acquires nothing. The physical run is ``PREREGISTERED_NOT_RUN``, not
    faked with a synthetic value.
    """


# --- the vocabulary -------------------------------------------------------

class ThermalSensorKind(Enum):
    """A temperature input the lane can read from."""

    THERMISTOR = "thermistor"
    RTD = "rtd"
    THERMOCOUPLE = "thermocouple"
    IR = "ir"
    MANUAL = "manual"
    SYNTHETIC = "synthetic"


#: The claim class each input can honestly support here. No thermometer was
#: operated, so an electrical or IR trace is a synthetic observation and a
#: manual note is a declared source claim.
SENSOR_CLAIM_CLASS: dict[ThermalSensorKind, claims.ClaimClass] = {
    ThermalSensorKind.THERMISTOR: claims.ClaimClass.SYNTHETIC_OBSERVATION,
    ThermalSensorKind.RTD: claims.ClaimClass.SYNTHETIC_OBSERVATION,
    ThermalSensorKind.THERMOCOUPLE: claims.ClaimClass.SYNTHETIC_OBSERVATION,
    ThermalSensorKind.IR: claims.ClaimClass.SYNTHETIC_OBSERVATION,
    ThermalSensorKind.MANUAL: claims.ClaimClass.SOURCE_CLAIM,
    ThermalSensorKind.SYNTHETIC: claims.ClaimClass.SYNTHETIC_OBSERVATION,
}


class ThermalDeviceMode(Enum):
    """The four acquisition modes behind the one interface."""

    REAL_DEVICE = "REAL_DEVICE"
    SYNTHETIC_DEVICE = "SYNTHETIC_DEVICE"
    REPLAY_DEVICE = "REPLAY_DEVICE"
    FAULT_INJECTION_DEVICE = "FAULT_INJECTION_DEVICE"


class ThermalFaultMode(Enum):
    """The thermal-readout pathologies a fault-injection device can inject.

    The five generic instrument faults plus ``SELF_HEATING`` -- the sensor
    warming itself, which masquerades as a real ambient rise.
    """

    CLIPPING = "clipping"
    DRIFT = "drift"
    SATURATION = "saturation"
    PACKET_LOSS = "packet_loss"
    MISSING_SAMPLES = "missing_samples"
    SELF_HEATING = "self_heating"


# --- (1) transducer conversion models (readout -> kelvin) -----------------

def thermistor_temperature(resistance_ohm, *, r0_ohm: float = 10000.0,
                           t0_K: float = 298.15,
                           beta_K: float = 3950.0) -> np.ndarray:
    """Convert a thermistor resistance to temperature via the Beta model.

    ``1/T = 1/T0 + (1/B) ln(R/R0)``. ``r0_ohm`` is the nominal resistance at
    ``t0_K`` and ``beta_K`` is the material constant. The constants are
    CONVENTIONAL_LITERATURE figures for a class of NTC thermistor, not a
    calibration of any device.
    """
    r = np.asarray(resistance_ohm, dtype=float)
    if np.any(r <= 0.0):
        raise ThermalError("a thermistor resistance must be positive")
    if r0_ohm <= 0.0 or t0_K <= 0.0 or beta_K == 0.0:
        raise ThermalError("thermistor model constants must be positive")
    inv_t = 1.0 / float(t0_K) + np.log(r / float(r0_ohm)) / float(beta_K)
    return 1.0 / inv_t


def rtd_temperature(resistance_ohm, *, r0_ohm: float = 100.0,
                    t0_K: float = ZERO_CELSIUS_K,
                    alpha_per_K: float = 0.00385) -> np.ndarray:
    """Convert an RTD resistance to temperature via the linear Callendar model.

    ``R = R0 (1 + alpha (T - T0))`` inverted to
    ``T = T0 + (R/R0 - 1) / alpha``. Defaults are a Pt100
    (``R0 = 100 ohm`` at 0 C, ``alpha = 0.00385 /K``), a CONVENTIONAL_LITERATURE
    figure.
    """
    r = np.asarray(resistance_ohm, dtype=float)
    if r0_ohm <= 0.0 or alpha_per_K == 0.0:
        raise ThermalError("RTD model constants must be non-degenerate")
    return float(t0_K) + (r / float(r0_ohm) - 1.0) / float(alpha_per_K)


def thermocouple_temperature(voltage_V, *, seebeck_V_per_K: float = 4.1e-5,
                             t_ref_K: float = ZERO_CELSIUS_K) -> np.ndarray:
    """Convert a thermocouple EMF to temperature via a linear Seebeck model.

    ``V = S (T - T_ref)`` inverted to ``T = T_ref + V / S``. The
    reference-junction temperature ``t_ref_K`` must be supplied (cold-junction
    compensation); ``seebeck_V_per_K`` is a CONVENTIONAL_LITERATURE figure for
    a class of thermocouple. The linear model is a first-order approximation,
    not a polynomial calibration.
    """
    v = np.asarray(voltage_V, dtype=float)
    if seebeck_V_per_K == 0.0:
        raise ThermalError("the Seebeck coefficient must be non-zero")
    return float(t_ref_K) + v / float(seebeck_V_per_K)


# --- (2) a bound thermal sensor -------------------------------------------

@dataclass(frozen=True)
class ThermalSensor:
    """A temperature sensor bound to a location and a response time.

    ``response_time_s`` is the first-order thermal time constant ``tau`` --
    the sensor low-passes the ambient it watches. ``self_heating_K_per_W`` is
    the thermal resistance ``R_theta`` between the sensing element and its
    surroundings, and ``dissipated_power_W`` is the bias power the sensor
    dissipates; their product is the self-heating offset.
    """

    sensor_id: str
    kind: ThermalSensorKind
    location: str
    response_time_s: float
    units: str = "K"
    uncertainty_K: float = 0.0
    self_heating_K_per_W: float = 0.0
    dissipated_power_W: float = 0.0

    def __post_init__(self) -> None:
        if not str(self.sensor_id).strip():
            raise ThermalError("a thermal sensor needs an id")
        if not isinstance(self.kind, ThermalSensorKind):
            raise ThermalError(
                f"{self.sensor_id}: kind must be a ThermalSensorKind")
        if not str(self.location).strip():
            raise ThermalError(
                f"{self.sensor_id}: a sensor must be bound to a location; a "
                f"probe without a place measures an unnamed point")
        if float(self.response_time_s) < 0.0:
            raise ThermalError(
                f"{self.sensor_id}: response time (tau) cannot be negative")
        if float(self.uncertainty_K) < 0.0:
            raise ThermalError(
                f"{self.sensor_id}: uncertainty cannot be negative")
        if float(self.self_heating_K_per_W) < 0.0 or \
                float(self.dissipated_power_W) < 0.0:
            raise ThermalError(
                f"{self.sensor_id}: self-heating terms cannot be negative")
        if not self.units:
            raise ThermalError(f"{self.sensor_id}: a sensor needs units")

    @property
    def self_heating_offset_K(self) -> float:
        """The steady-state self-heating rise ``dT = R_theta * P`` (kelvin)."""
        return float(self.self_heating_K_per_W) * float(self.dissipated_power_W)

    @property
    def claim_class(self) -> claims.ClaimClass:
        return SENSOR_CLAIM_CLASS[self.kind]

    def as_dict(self) -> dict:
        return {
            "sensor_id": self.sensor_id,
            "kind": self.kind.value,
            "location": self.location,
            "response_time_s": float(self.response_time_s),
            "units": self.units,
            "uncertainty_K": float(self.uncertainty_K),
            "self_heating_K_per_W": float(self.self_heating_K_per_W),
            "dissipated_power_W": float(self.dissipated_power_W),
            "self_heating_offset_K": self.self_heating_offset_K,
            "claim_class": self.claim_class.value,
            "measured_here": MEASURED_HERE,
        }


def correct_self_heating(indicated_K, sensor: ThermalSensor) -> np.ndarray:
    """Subtract a sensor's self-heating offset from its indicated temperature.

    Self-heating raises what the sensor reads above the true ambient; removing
    it is a correction of a *sensor* artifact, never a change to the specimen.
    """
    return np.asarray(indicated_K, dtype=float) - sensor.self_heating_offset_K


# --- (3) sensor response, lag, and ambient-drift correction ---------------

def apply_sensor_response(ambient_K, dt_s: float, tau_s: float) -> np.ndarray:
    """Low-pass an ambient temperature trace by a first-order sensor lag.

    Models ``tau dT_sensor/dt = T_ambient - T_sensor`` as the discrete
    exponential smoother ``a = dt/(dt+tau)``. With ``tau = 0`` the sensor
    follows the ambient exactly; a larger ``tau`` produces a larger apparent
    lag, which :func:`estimate_sensor_lag_samples` recovers.
    """
    x = np.asarray(ambient_K, dtype=float)
    if x.ndim != 1 or x.size < 1:
        raise ThermalError("an ambient trace must be a 1-D array")
    if float(dt_s) <= 0.0:
        raise ThermalError("the sample interval must be positive")
    if float(tau_s) < 0.0:
        raise ThermalError("the time constant tau cannot be negative")
    a = float(dt_s) / (float(dt_s) + float(tau_s))
    out = np.empty_like(x)
    out[0] = x[0]
    for i in range(1, x.size):
        out[i] = out[i - 1] + a * (x[i] - out[i - 1])
    return out


def estimate_sensor_lag_samples(ambient_K, sensor_K) -> int:
    """Integer sample lag of a sensor trace behind the ambient it watches.

    Reuses :func:`r13.daq.cross_correlation_lag`. A positive lag means the
    sensor trace follows the ambient by that many samples -- the fingerprint
    of a finite response time. A sensor lag left uncorrected times a thermal
    correction to the wrong instant.
    """
    a = np.asarray(ambient_K, dtype=float)
    b = np.asarray(sensor_K, dtype=float)
    if a.shape != b.shape:
        raise ThermalError(
            "ambient and sensor traces must share a length to be correlated")
    return cross_correlation_lag(a, b)


def fit_ambient_drift(t_s, temperature_K) -> float:
    """Least-squares linear ambient drift, in kelvin per second.

    A slow ambient ramp is a nuisance, not a signal; recovering its rate is
    the first step to removing it.
    """
    t = np.asarray(t_s, dtype=float)
    T = np.asarray(temperature_K, dtype=float)
    if t.size < 2 or t.shape != T.shape:
        raise ThermalError("need matching t and T of length >= 2 to fit drift")
    slope, _intercept = np.polyfit(t - t[0], T, 1)
    return float(slope)


def correct_ambient_drift(t_s, temperature_K) -> np.ndarray:
    """Remove a fitted linear ambient drift, leaving the residual temperature."""
    t = np.asarray(t_s, dtype=float)
    T = np.asarray(temperature_K, dtype=float)
    if t.size < 2 or t.shape != T.shape:
        raise ThermalError("need matching t and T of length >= 2 to detrend")
    slope, intercept = np.polyfit(t - t[0], T, 1)
    return T - (slope * (t - t[0]) + intercept)


# --- (4) thermal explanation of frequency and phase -----------------------

def quartz_lattice_at_temperature(delta_T_K: float):
    """The alpha-quartz frame expanded to a temperature offset from reference.

    Applies the CONVENTIONAL_LITERATURE linear expansion coefficients to the
    :mod:`r13.crystalframe` literature lattice constants, returning a
    :class:`r13.crystalframe.LatticeFrame`. This is a geometry model of
    thermal expansion, not a diffraction measurement of any crystal.
    """
    dT = float(delta_T_K)
    a = _crystalframe.QUARTZ_A_ANGSTROM * (1.0 + QUARTZ_ALPHA_A_PER_K * dT)
    c = _crystalframe.QUARTZ_C_ANGSTROM * (1.0 + QUARTZ_ALPHA_C_PER_K * dT)
    return _crystalframe.LatticeFrame(a=a, c=c)


def expansion_frequency_coefficient(axis: str = "a") -> float:
    """The geometric thermal coefficient of frequency from lattice expansion.

    A thickness-governed mode has ``f ~ 1/L``; a dimension that expands by
    ``alpha`` per kelvin drops the frequency by ``-alpha`` per kelvin, so
    ``df/f = -alpha dT``. Returns ``-alpha`` for the chosen quartz axis. This
    is the pure geometric contribution; a real resonator's TCf also includes
    the temperature dependence of the elastic constants, which is why a
    device's TCf is planted and *fitted*, not asserted from geometry alone.
    """
    if axis == "a":
        return -QUARTZ_ALPHA_A_PER_K
    if axis == "c":
        return -QUARTZ_ALPHA_C_PER_K
    raise ThermalError("axis must be 'a' or 'c'")


def frequency_from_temperature(temperature_K, *, f0_hz: float, t_ref_K: float,
                               tcf_per_K: float,
                               tcf2_per_K2: float = 0.0) -> np.ndarray:
    """A resonator frequency as a function of temperature (the TCf model).

    ``f(T) = f0 (1 + a1 (T - Tref) + a2 (T - Tref)^2)`` where ``a1`` is the
    linear thermal coefficient of frequency (per kelvin) and ``a2`` an
    optional quadratic term. This is the forward model whose ``a1`` the fit
    recovers.
    """
    T = np.asarray(temperature_K, dtype=float)
    if float(f0_hz) <= 0.0:
        raise ThermalError("the reference frequency f0 must be positive")
    dT = T - float(t_ref_K)
    return float(f0_hz) * (1.0 + float(tcf_per_K) * dT
                           + float(tcf2_per_K2) * dT * dT)


@dataclass(frozen=True)
class ThermalCoefficientFit:
    """The recovered thermal coefficient of frequency and its quality."""

    tcf_per_K: float
    tcf2_per_K2: float
    f0_hz: float
    t_ref_K: float
    r_squared: float

    def as_dict(self) -> dict:
        return {
            "tcf_per_K": self.tcf_per_K,
            "tcf2_per_K2": self.tcf2_per_K2,
            "f0_hz": self.f0_hz,
            "t_ref_K": self.t_ref_K,
            "r_squared": self.r_squared,
            "claim_class": claims.ClaimClass.MODEL_PREDICTION.value,
            "measured_here": MEASURED_HERE,
        }


def fit_thermal_coefficient(temperature_K, frequency_hz, *, f0_hz: float,
                            t_ref_K: float,
                            quadratic: bool = True) -> ThermalCoefficientFit:
    """Recover the thermal coefficient of frequency from a ``(T, f)`` record.

    Solves ``f/f0 - 1 = a1 dT + a2 dT^2`` (dropping the quadratic column when
    ``quadratic`` is False) by least squares, with ``dT = T - Tref``. Given a
    trace generated by :func:`frequency_from_temperature` with a planted
    ``a1``, the fit returns that ``a1`` -- this is the lane's power check: a
    known thermal drift is reproduced and recovered.
    """
    T = np.asarray(temperature_K, dtype=float)
    f = np.asarray(frequency_hz, dtype=float)
    if T.shape != f.shape or T.size < 3:
        raise ThermalError(
            "need matching T and f of length >= 3 to fit a coefficient")
    if float(f0_hz) <= 0.0:
        raise ThermalError("the reference frequency f0 must be positive")
    dT = T - float(t_ref_K)
    y = f / float(f0_hz) - 1.0
    cols = [dT, dT * dT] if quadratic else [dT]
    design = np.vstack(cols).T
    coef, *_ = np.linalg.lstsq(design, y, rcond=None)
    pred = design @ coef
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    ss_res = float(np.sum((y - pred) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0.0 else 1.0
    a1 = float(coef[0])
    a2 = float(coef[1]) if quadratic else 0.0
    return ThermalCoefficientFit(tcf_per_K=a1, tcf2_per_K2=a2,
                                 f0_hz=float(f0_hz), t_ref_K=float(t_ref_K),
                                 r_squared=r2)


def thermal_frequency_shift(delta_T_K, *, f0_hz: float,
                            tcf_per_K: float) -> np.ndarray:
    """The frequency shift ``df = f0 a1 dT`` a temperature change explains."""
    dT = np.asarray(delta_T_K, dtype=float)
    return float(f0_hz) * float(tcf_per_K) * dT


def thermal_phase_shift(nominal_phase_rad, delta_T_K, *,
                        alpha_per_K: float = QUARTZ_ALPHA_A_PER_K) -> np.ndarray:
    """The phase walk a fractional thermal expansion explains.

    A delay-line phase ``phi = 2 pi f L / v`` walks as the path ``L`` expands:
    ``dphi = phi * alpha dT``. Reads the same expansion physics as the
    frequency model, from the phase side.
    """
    phi = np.asarray(nominal_phase_rad, dtype=float)
    dT = np.asarray(delta_T_K, dtype=float)
    return phi * float(alpha_per_K) * dT


def thermal_coupling_is_an_artifact() -> bool:
    """A thermometer does not couple to the specimen's mechanical mode.

    Consults :mod:`r11.detectors`: strain (a specimen's intrinsic mechanical
    observable) is transduced by a piezoelectric element, never by a
    thermometer. A frequency that tracks temperature is therefore the
    thermal-expansion artifact detectors names for a transducer used outside
    its domain -- not a measurement of the mode. Returns True.
    """
    strain_detectors = _detectors.select_detectors(_detectors.Observable.STRAIN)
    thermal_detectors = tuple(
        k for k in strain_detectors if "thermal" in k.value.lower())
    return len(strain_detectors) > 0 and len(thermal_detectors) == 0


# --- the acquisition result -----------------------------------------------

@dataclass(frozen=True)
class ThermalAcquisition:
    """One thermal reading behind the interface.

    Carries the timebase, the temperature series (kelvin), and -- when the
    device co-records a resonator under thermal drift -- the paired frequency
    series. ``claim_class`` is capped at ``SYNTHETIC_OBSERVATION`` and can
    never be a measurement class.
    """

    sensor_id: str
    mode: ThermalDeviceMode
    t: np.ndarray
    temperature_K: np.ndarray
    frequency_hz: np.ndarray | None
    seed: int
    claim_class: claims.ClaimClass = READING_CLAIM_CLASS
    faults: tuple = ()

    def __post_init__(self) -> None:
        if self.claim_class in claims.MEASUREMENT_CLASSES:
            # the load-bearing refusal, wired to the governance core
            claims.refuse_synthetic_as_physical()
        t = np.asarray(self.t, dtype=float)
        T = np.asarray(self.temperature_K, dtype=float)
        if t.shape != T.shape:
            raise ThermalError("t and temperature must have one sample each")

    @property
    def n(self) -> int:
        return int(np.asarray(self.temperature_K).size)

    def digest(self) -> str:
        """A deterministic hash of the temperature series."""
        arr = np.ascontiguousarray(self.temperature_K, dtype=float)
        return hashlib.sha256(arr.tobytes()).hexdigest()

    def as_dict(self) -> dict:
        return {
            "sensor_id": self.sensor_id,
            "mode": self.mode.value,
            "n_samples": self.n,
            "t0": float(np.asarray(self.t)[0]) if self.n else 0.0,
            "seed": int(self.seed),
            "faults": [f.value for f in self.faults],
            "has_frequency": self.frequency_hz is not None,
            "temperature_sha256": self.digest(),
            "claim_class": self.claim_class.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


# --- (5) the four modes ---------------------------------------------------

@dataclass(frozen=True)
class SyntheticThermalParams:
    """The deterministic drivers of a synthetic thermal record.

    Every value is a model figure. ``drift_rate_K_per_s`` and ``tcf_per_K``
    are the *planted* quantities the fits recover; ``self_heating_K`` is a
    constant offset applied to the indicated temperature.
    """

    t_mean_K: float = 300.0
    drift_rate_K_per_s: float = 0.0
    noise_K: float = 0.0
    self_heating_K: float = 0.0
    f0_hz: float = 1.0e7
    t_ref_K: float = 300.0
    tcf_per_K: float = -1.0e-5
    tcf2_per_K2: float = 0.0


class RealThermalDevice:
    """A real thermal sensor interface with no hardware behind it.

    Acquisition acquires nothing: it raises :class:`NoThermalHardwareError`.
    The physical run is fully specified but ``PREREGISTERED_NOT_RUN``.
    """

    mode = ThermalDeviceMode.REAL_DEVICE

    def __init__(self, sensor: ThermalSensor) -> None:
        self.sensor = sensor

    def acquire(self, *_a, **_k) -> ThermalAcquisition:
        raise NoThermalHardwareError(
            f"refused: {self.sensor.sensor_id} is a REAL_DEVICE and no "
            f"physical thermometer exists in this repository, so it acquires "
            f"NOTHING. The thermal protocol is fully specified but the "
            f"physical run is {PREREGISTERED_NOT_RUN}, not faked with a "
            f"synthetic temperature. {PHYSICAL_VALIDATION}. {VERDICT}")

    def preregistered_receipt(self) -> dict:
        """The honest status for a real read that cannot happen: preregistered."""
        return {
            "sensor_id": self.sensor.sensor_id,
            "mode": self.mode.value,
            "status": PREREGISTERED_NOT_RUN,
            "reason": ("no physical thermometer, oven or reference bath was "
                       "operated; nothing was acquired, the protocol is "
                       "preregistered"),
            "acquired": False,
            "n_samples": 0,
            "claim_class": PREREGISTERED_NOT_RUN,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


class SyntheticThermalDevice:
    """A deterministic synthetic thermal sensor.

    Same seed and clock => identical temperature (and frequency) series;
    different seed => different noise. The reading is a
    ``SYNTHETIC_OBSERVATION``.
    """

    mode = ThermalDeviceMode.SYNTHETIC_DEVICE

    def __init__(self, sensor: ThermalSensor,
                 params: SyntheticThermalParams) -> None:
        self.sensor = sensor
        self.params = params

    def acquire(self, t_s, *, seed: int,
                with_frequency: bool = True) -> ThermalAcquisition:
        t = np.asarray(t_s, dtype=float)
        if t.ndim != 1 or t.size < 1:
            raise ThermalError("a clock must be a 1-D array of timestamps")
        p = self.params
        rng = np.random.default_rng(int(seed))
        ramp = p.drift_rate_K_per_s * (t - t[0])
        fluct = p.noise_K * rng.standard_normal(t.size)
        temperature = p.t_mean_K + ramp + fluct + p.self_heating_K
        freq = None
        if with_frequency:
            freq = frequency_from_temperature(
                temperature, f0_hz=p.f0_hz, t_ref_K=p.t_ref_K,
                tcf_per_K=p.tcf_per_K, tcf2_per_K2=p.tcf2_per_K2)
        return ThermalAcquisition(
            sensor_id=self.sensor.sensor_id, mode=self.mode, t=t,
            temperature_K=temperature, frequency_hz=freq, seed=int(seed))


class ReplayThermalDevice:
    """Replays a previously recorded (synthetic) thermal trace byte-for-byte.

    It reads back what was stored and measures nothing new; the reading is a
    ``SYNTHETIC_OBSERVATION`` of a recorded trace.
    """

    mode = ThermalDeviceMode.REPLAY_DEVICE

    def __init__(self, sensor: ThermalSensor, recorded_t,
                 recorded_temperature_K, recorded_frequency_hz=None) -> None:
        self.sensor = sensor
        self._t = np.asarray(recorded_t, dtype=float)
        self._T = np.asarray(recorded_temperature_K, dtype=float)
        self._f = (None if recorded_frequency_hz is None
                   else np.asarray(recorded_frequency_hz, dtype=float))
        if self._t.shape != self._T.shape:
            raise ThermalError("recorded t and temperature must align")

    def acquire(self, *, n_samples: int | None = None,
                seed: int = 0) -> ThermalAcquisition:
        n = self._T.size if n_samples is None else int(n_samples)
        if n > self._T.size:
            raise ThermalError(
                f"the recorded trace has {self._T.size} samples; cannot "
                f"replay {n}")
        freq = None if self._f is None else self._f[:n].copy()
        return ThermalAcquisition(
            sensor_id=self.sensor.sensor_id, mode=self.mode,
            t=self._t[:n].copy(), temperature_K=self._T[:n].copy(),
            frequency_hz=freq, seed=int(seed))


class FaultInjectionThermalDevice:
    """Wraps a :class:`SyntheticThermalDevice` and injects readout faults.

    Deterministic under the acquisition seed. Every :class:`ThermalFaultMode`
    is injectable -- the five generic faults plus self-heating -- and the
    applied faults are carried on the :class:`ThermalAcquisition`.
    """

    mode = ThermalDeviceMode.FAULT_INJECTION_DEVICE

    def __init__(self, inner: SyntheticThermalDevice, faults: tuple,
                 config: dict | None = None) -> None:
        faults = tuple(faults)
        if not faults:
            raise ThermalError(
                "a fault-injection device with no faults injects nothing; "
                "supply at least one ThermalFaultMode")
        for f in faults:
            if not isinstance(f, ThermalFaultMode):
                raise ThermalError(f"{f!r} is not a ThermalFaultMode")
        self.inner = inner
        self.sensor = inner.sensor
        self.faults = faults
        self.config = dict(config or {})

    def acquire(self, t_s, *, seed: int,
                with_frequency: bool = True) -> ThermalAcquisition:
        clean = self.inner.acquire(t_s, seed=seed, with_frequency=with_frequency)
        temperature = np.asarray(clean.temperature_K, dtype=float).copy()
        for f in self.faults:
            rng = np.random.default_rng(
                np.random.SeedSequence([int(seed), _FAULT_TAG[f]]))
            temperature = _apply_thermal_fault(f, temperature, self.config, rng)
        return ThermalAcquisition(
            sensor_id=self.sensor.sensor_id, mode=self.mode,
            t=np.asarray(clean.t, dtype=float), temperature_K=temperature,
            frequency_hz=clean.frequency_hz, seed=int(seed),
            faults=self.faults)


# --- the fault injection kernels ------------------------------------------

#: A stable integer tag per fault so its rng stream is distinct yet
#: reproducible under the acquisition seed.
_FAULT_TAG: dict[ThermalFaultMode, int] = {
    ThermalFaultMode.CLIPPING: 0x0C,
    ThermalFaultMode.DRIFT: 0x0D,
    ThermalFaultMode.SATURATION: 0x05,
    ThermalFaultMode.PACKET_LOSS: 0x0B,
    ThermalFaultMode.MISSING_SAMPLES: 0x0A,
    ThermalFaultMode.SELF_HEATING: 0x51,
}


def _apply_thermal_fault(fault: ThermalFaultMode, samples: np.ndarray,
                         config: dict, rng: np.random.Generator) -> np.ndarray:
    """Apply one fault to a copy of a temperature trace, deterministically.

    Each fault demonstrably alters the trace relative to the clean synthetic
    reading, and each is a distinct, recognised thermal-readout pathology.
    """
    x = np.asarray(samples, dtype=float).copy()
    n = x.size
    if n == 0:
        return x
    span = float(np.ptp(x))
    scale = span if span > 0.0 else max(abs(float(np.mean(x))), 1.0)

    if fault is ThermalFaultMode.CLIPPING:
        # clip the trace at a fraction of its span about the mean
        mean = float(np.mean(x))
        level = float(config.get("clip_fraction", 0.4)) * scale
        return np.clip(x, mean - level, mean + level)

    if fault is ThermalFaultMode.DRIFT:
        # a slow linear readout drift added across the record
        slope = float(config.get("drift_fraction", 0.5)) * scale
        return x + np.linspace(0.0, slope, n)

    if fault is ThermalFaultMode.SATURATION:
        # a hard upper rail: the ADC / range saturates
        rail = float(np.min(x)) + float(config.get("saturation_fraction", 0.6)) \
            * scale
        return np.minimum(x, rail)

    if fault is ThermalFaultMode.PACKET_LOSS:
        # one contiguous "packet" is lost and held at the last good value
        frac = float(config.get("packet_fraction", 0.1))
        length = max(1, int(round(frac * n)))
        start = int(rng.integers(0, max(1, n - length + 1)))
        hold = x[start - 1] if start > 0 else x[start]
        x[start:start + length] = hold
        return x

    if fault is ThermalFaultMode.MISSING_SAMPLES:
        # scattered individual samples go missing (NaN)
        frac = float(config.get("missing_fraction", 0.05))
        k = max(1, int(round(frac * n)))
        idx = rng.choice(n, size=min(k, n), replace=False)
        x[idx] = np.nan
        return x

    if fault is ThermalFaultMode.SELF_HEATING:
        # a constant positive offset: the sensor warms itself. This is NOT a
        # rise in the ambient the specimen sees.
        offset = float(config.get("self_heating_K", 0.5))
        return x + offset

    raise ThermalError(f"unknown fault {fault!r}")  # pragma: no cover


# --- the thermal error budget ---------------------------------------------

class ThermalBudgetComponent(Enum):
    """The uncertainty contributions of a thermal result."""

    SENSOR_RESOLUTION = "sensor_resolution"
    CALIBRATION = "calibration"
    SELF_HEATING = "self_heating"
    AMBIENT_DRIFT = "ambient_drift"
    SENSOR_LAG = "sensor_lag"
    THERMAL_GRADIENT = "thermal_gradient"
    RADIATION = "radiation"
    LEAD_RESISTANCE = "lead_resistance"
    REFERENCE_JUNCTION = "reference_junction"
    NUMERICAL_METHOD = "numerical_method"
    MODEL_RESIDUAL = "model_residual"


@dataclass(frozen=True)
class ThermalErrorComponent:
    """One line of a thermal error budget: a labelled one-sigma contribution."""

    component: ThermalBudgetComponent
    sigma: float
    units: str
    note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.component, ThermalBudgetComponent):
            raise ThermalError("component must be a ThermalBudgetComponent")
        if float(self.sigma) < 0.0:
            raise ThermalError(
                f"{self.component.value}: a sigma cannot be negative")
        if not self.units:
            raise ThermalError(
                f"{self.component.value}: a sigma without units is not a "
                f"budget line")

    def as_dict(self) -> dict:
        return {
            "component": self.component.value,
            "sigma": float(self.sigma),
            "units": self.units,
            "note": self.note,
        }


def combine_quadrature(components) -> float:
    """Root-sum-square of the component sigmas -- the combined uncertainty."""
    comps = list(components)
    if not comps:
        raise ThermalError("an error budget needs at least one component")
    sigmas = np.asarray([float(c.sigma) for c in comps], dtype=float)
    return float(np.sqrt(np.sum(np.square(sigmas))))


def build_thermal_error_budget(budget_id: str, quantity: str, components, *,
                               coverage_factor: float = 2.0) -> dict:
    """Assemble a thermal error budget conforming to ``error_budget.schema.json``.

    The combined uncertainty is the quadrature sum of the component sigmas;
    the ``coverage_factor`` (``k``, default 2) expands it. The budget is a
    ``MODEL_PREDICTION``: no thermal coupling here was measured.
    """
    comps = list(components)
    if not budget_id:
        raise ThermalError("an error budget needs a budget_id")
    seen = [c.component for c in comps]
    if len(set(seen)) != len(seen):
        raise ThermalError("a budget must not list a component twice")
    combined = combine_quadrature(comps)
    return {
        "budget_id": str(budget_id),
        "quantity": str(quantity),
        "components": [c.as_dict() for c in comps],
        "combination_method": QUADRATURE,
        "combined_uncertainty": combined,
        "coverage_factor": float(coverage_factor),
        "expanded_uncertainty": float(coverage_factor) * combined,
        "claim_class": BUDGET_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


def default_thermal_budget(sensor: ThermalSensor, *,
                           budget_id: str = "thermal-budget",
                           quantity: str = "temperature") -> dict:
    """A representative thermal budget for a bound sensor, in kelvin.

    Every sigma is a model figure; the self-heating line is the sensor's own
    steady-state offset used as an uncertainty proxy when it is not corrected.
    """
    comps = [
        ThermalErrorComponent(
            ThermalBudgetComponent.SENSOR_RESOLUTION,
            max(float(sensor.uncertainty_K), 1e-3), "K",
            "quantisation and noise floor of the readout (model)"),
        ThermalErrorComponent(
            ThermalBudgetComponent.CALIBRATION, 0.05, "K",
            "conversion-constant tolerance (model)"),
        ThermalErrorComponent(
            ThermalBudgetComponent.SELF_HEATING,
            max(sensor.self_heating_offset_K, 1e-3), "K",
            "residual self-heating after correction (model)"),
        ThermalErrorComponent(
            ThermalBudgetComponent.AMBIENT_DRIFT, 0.02, "K",
            "uncorrected slow ambient drift (model)"),
        ThermalErrorComponent(
            ThermalBudgetComponent.SENSOR_LAG,
            max(float(sensor.response_time_s) * 0.01, 1e-3), "K",
            "temperature error from finite response time (model)"),
        ThermalErrorComponent(
            ThermalBudgetComponent.THERMAL_GRADIENT, 0.03, "K",
            "spatial gradient between sensor location and specimen (model)"),
        ThermalErrorComponent(
            ThermalBudgetComponent.NUMERICAL_METHOD, 1e-4, "K",
            "fit and arithmetic residual (model)"),
        ThermalErrorComponent(
            ThermalBudgetComponent.MODEL_RESIDUAL, 0.01, "K",
            "linear-model inadequacy (model)"),
    ]
    return build_thermal_error_budget(budget_id, quantity, comps)


def is_within_budget(residual: float, combined_sigma: float) -> bool:
    """Is a residual within the combined (quadrature) uncertainty?

    ``True`` means the residual is consistent with the known thermal error
    sources: it is not anomalous.
    """
    if float(combined_sigma) < 0.0:
        raise ThermalError("the combined sigma cannot be negative")
    return abs(float(residual)) <= float(combined_sigma)


# --- observation record ---------------------------------------------------

def thermal_observation_record(observation_id: str, run_id: str, *,
                               value: float, uncertainty_K: float,
                               source_artifacts, quantity: str = "temperature",
                               units: str = "K") -> dict:
    """A thermal observation conforming to ``observation_record.schema.json``.

    The claim class is capped at ``SYNTHETIC_OBSERVATION``: the value is a
    reduction of a seeded synthetic trace, never a physical measurement.
    """
    return {
        "observation_id": str(observation_id),
        "run_id": str(run_id),
        "source_artifacts": list(source_artifacts),
        "analysis_version": ANALYSIS_VERSION,
        "quantity": str(quantity),
        "value": float(value),
        "units": str(units),
        "uncertainty": {"one_sigma": float(uncertainty_K), "units": units},
        "claim_class": READING_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


# --- load-bearing refusals ------------------------------------------------

def refuse_thermal_drift_as_signal(
        delta_T_K: float = 1.0, df_hz: float = 0.0,
        claim: str = "a temperature-driven frequency shift is a signal") -> None:
    """A temperature-induced frequency/phase shift is not a signal. Always raises.

    A mode whose frequency (or phase) tracks temperature is exhibiting the
    thermal coefficient of frequency -- ordinary, expected, and quantified by
    the crystal's thermal expansion. It is a ``KNOWN_ORDINARY_EFFECT``, the
    same thermal-expansion artifact :mod:`r11.detectors` names when a
    transducer is read outside its domain, not a discovery of anything in the
    specimen.
    """
    artifact = thermal_coupling_is_an_artifact()
    raise ThermalError(
        f"refused: {claim!r}. A frequency shift of {float(df_hz):g} Hz over a "
        f"{float(delta_T_K):g} K change is the thermal coefficient of "
        f"frequency -- a {DRIFT_CLAIM_CLASS.value}, caused by the crystal "
        f"expanding (r13.crystalframe geometry) and its elastic constants "
        f"shifting with temperature. A thermometer does not couple to the "
        f"specimen's mechanical mode "
        f"(thermal_coupling_is_an_artifact={artifact}); a temperature-driven "
        f"shift is the thermal-expansion artifact, not a signal. Correct it "
        f"with the measured temperature; do not promote it. {VERDICT}.")


def refuse_self_heating_as_specimen(
        offset_K: float = 0.0,
        claim: str = "sensor self-heating is the specimen's output") -> None:
    """Self-heating is a sensor artifact, not specimen output. Always raises.

    A sensor dissipating its own bias power warms itself above the true
    ambient (``dT = R_theta * P``). That rise is a property of the sensor and
    its mounting, not of the specimen or the ambient the specimen sees.
    """
    raise ThermalError(
        f"refused: {claim!r}. A self-heating rise of {float(offset_K):g} K is "
        f"the sensor warming itself with its own bias power (dT = R_theta P); "
        f"it is an artifact of the sensor, not a temperature of the specimen "
        f"and not an output the specimen produced. Correct it "
        f"(correct_self_heating) or reduce the bias; do not read it as "
        f"specimen behaviour. {VERDICT}.")


def refuse_synthetic_thermal_as_measured(
        claim: str = "these temperatures are measured") -> None:
    """Synthetic thermal data is not a measurement. Always raises.

    Every temperature this lane produces is evaluated from a seeded generator
    on a supplied clock -- a ``SYNTHETIC_OBSERVATION``. No thermometer, oven or
    reference bath was operated; the REAL-mode read is ``PREREGISTERED_NOT_RUN``.
    """
    raise ThermalError(
        f"refused: {claim!r}. The temperatures here are deterministic "
        f"synthetic observations from a seeded generator on a supplied clock, "
        f"not instrument readings. No thermometer was operated; the REAL-mode "
        f"read is {PREREGISTERED_NOT_RUN}. A {READING_CLAIM_CLASS.value} is "
        f"not a PHYSICAL_MEASUREMENT. {VERDICT}.")


def refuse_manual_as_sensor(
        claim: str = "a manual temperature note is a sensor reading") -> None:
    """A hand-entered temperature is a source claim, not a sensor trace."""
    raise ThermalError(
        f"refused: {claim!r}. A manual note (\"the bath was about 25 C\") is a "
        f"{MANUAL_CLAIM_CLASS.value}, not a transduced reading; it cannot "
        f"stand in for a thermistor, RTD, thermocouple or IR trace. {VERDICT}.")


#: The forbidden promotions this lane guards, for the red team.
FORBIDDEN_PROMOTIONS = {
    "thermal_drift_to_signal": refuse_thermal_drift_as_signal,
    "self_heating_to_specimen": refuse_self_heating_as_specimen,
    "synthetic_thermal_to_measured": refuse_synthetic_thermal_as_measured,
    "manual_to_sensor": refuse_manual_as_sensor,
}


# --- real-mode status -----------------------------------------------------

def real_mode_status() -> dict:
    """The REAL-mode thermal read as it actually stands here: preregistered.

    No thermometer was operated in this repository, so a real temperature
    cannot be acquired. The protocol is specified but ``PREREGISTERED_NOT_RUN``.
    """
    return {
        "mode": ThermalDeviceMode.REAL_DEVICE.value,
        "status": PREREGISTERED_NOT_RUN,
        "reason": ("no thermistor, RTD, thermocouple, IR camera, oven or "
                   "reference bath was operated; nothing was acquired"),
        "claim_class": PREREGISTERED_NOT_RUN,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


# --- report ---------------------------------------------------------------

def thermal_report() -> dict:
    """The standing statement of what this lane is and is not."""
    return {
        "what_this_is": (
            "the R15 thermal measurement lane: thermistor / RTD / thermocouple "
            "/ IR / manual / synthetic inputs converted to temperature, bound "
            "to a location and a first-order response time, corrected for "
            "self-heating and ambient drift, and used to EXPLAIN the thermal "
            "coefficient of frequency and phase (via r13.crystalframe quartz "
            "expansion) -- with four distinct device modes and a quadrature "
            "thermal error budget"),
        "sensor_kinds": [k.value for k in ThermalSensorKind],
        "modes": [m.value for m in ThermalDeviceMode],
        "fault_modes": [f.value for f in ThermalFaultMode],
        "budget_components": [c.value for c in ThermalBudgetComponent],
        "combination_method": QUADRATURE,
        "quartz_expansion_per_K": {
            "alpha_a": QUARTZ_ALPHA_A_PER_K,
            "alpha_c": QUARTZ_ALPHA_C_PER_K,
            "class": CONVENTIONAL_LITERATURE,
        },
        "thermal_shift_is": DRIFT_CLAIM_CLASS.value,
        "thermal_coupling_is_an_artifact": thermal_coupling_is_an_artifact(),
        "real_mode_status": PREREGISTERED_NOT_RUN,
        "refusals": list(FORBIDDEN_PROMOTIONS),
        "reading_claim_class": READING_CLAIM_CLASS.value,
        "manual_claim_class": MANUAL_CLAIM_CLASS.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "max_evidence": MAX_THERMAL_EVIDENCE.name,
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not measure any temperature. Every reading is a "
            "deterministic synthetic observation from a seeded generator on a "
            "supplied clock; a manual note is a SOURCE_CLAIM; and the "
            "REAL-mode read is PREREGISTERED_NOT_RUN because no thermometer "
            "was operated. A temperature-induced frequency or phase shift is a "
            "KNOWN_ORDINARY_EFFECT (the thermal coefficient of frequency), not "
            "a signal, and sensor self-heating is a sensor artifact, never the "
            "specimen's output. A synthetic observation is never a "
            "PHYSICAL_MEASUREMENT. PHYSICAL_VALIDATION_NOT_CLAIMED."),
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION",
    "PREREGISTERED_NOT_RUN", "BLOCKED_MISSING_INPUT",
    "SOFTWARE_CLAIM_CLASS", "READING_CLAIM_CLASS", "MANUAL_CLAIM_CLASS",
    "DRIFT_CLAIM_CLASS", "BUDGET_CLAIM_CLASS", "CONVENTIONAL_LITERATURE",
    "MAX_THERMAL_EVIDENCE", "QUADRATURE", "ANALYSIS_VERSION",
    "QUARTZ_ALPHA_A_PER_K", "QUARTZ_ALPHA_C_PER_K", "ZERO_CELSIUS_K",
    "ThermalError", "NoThermalHardwareError",
    "ThermalSensorKind", "SENSOR_CLAIM_CLASS", "ThermalDeviceMode",
    "ThermalFaultMode",
    "thermistor_temperature", "rtd_temperature", "thermocouple_temperature",
    "ThermalSensor", "correct_self_heating",
    "apply_sensor_response", "estimate_sensor_lag_samples",
    "fit_ambient_drift", "correct_ambient_drift",
    "quartz_lattice_at_temperature", "expansion_frequency_coefficient",
    "frequency_from_temperature", "ThermalCoefficientFit",
    "fit_thermal_coefficient", "thermal_frequency_shift", "thermal_phase_shift",
    "thermal_coupling_is_an_artifact",
    "ThermalAcquisition", "SyntheticThermalParams",
    "RealThermalDevice", "SyntheticThermalDevice", "ReplayThermalDevice",
    "FaultInjectionThermalDevice",
    "ThermalBudgetComponent", "ThermalErrorComponent", "combine_quadrature",
    "build_thermal_error_budget", "default_thermal_budget", "is_within_budget",
    "thermal_observation_record",
    "refuse_thermal_drift_as_signal", "refuse_self_heating_as_specimen",
    "refuse_synthetic_thermal_as_measured", "refuse_manual_as_sensor",
    "FORBIDDEN_PROMOTIONS", "real_mode_status", "thermal_report",
]
