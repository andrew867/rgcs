"""P14 — the electrical measurement lane: impedance/admittance + BVD, four modes.

This is the electrical and impedance lane of the R15 platform. It measures
nothing. What it *does* is stand up, in software, the full apparatus an
electrical resonator measurement would need -- the constitutive electrical
relations, an impedance/admittance frequency sweep, a Butterworth-Van Dyke
(BVD) fit that recovers ``f_s``, ``f_p``, ``Q`` and the motional ``R, L, C``
with the static ``C0``, a fixture model with cable capacitance and lead
resistance, an open-short-load (OSL) de-embedding calibration, an electrical
error budget, and the ordinary electrical pathologies (ground loops,
saturation, clipping, drift, packet loss, missing samples) -- and it keeps
strict track of what could be measured versus what actually was, which is
nothing.

**One lane interface, four honest modes.** Every acquisition goes through
one :class:`ElectricalLane` interface behind which sit four distinct modes:

* ``REAL_DEVICE`` is an interface only. There is no impedance analyzer,
  LCR bridge, or crystal in this repository, so a real sweep acquires
  *nothing*: it raises :class:`NoElectricalHardwareError` and offers a
  ``blocked_receipt`` whose physical run is ``PREREGISTERED_NOT_RUN``.
* ``SYNTHETIC_DEVICE`` synthesises a deterministic complex impedance sweep
  from a planted :class:`~r13.qcmstack.BVDResonator` (optionally behind a
  cable/lead fixture) under a numpy seed. The BVD fit recovers the planted
  ``R, L, C, C0, f_s, f_p, Q``. That recovery is the power result -- and it
  is a ``SYNTHETIC_OBSERVATION``, never a measured crystal.
* ``REPLAY_DEVICE`` replays a previously recorded (synthetic) sweep
  point-for-point; it reads back what was stored and measures nothing new.
* ``FAULT_INJECTION_DEVICE`` wraps a synthetic device and injects the five
  ordinary instrument pathologies -- clipping, drift, saturation, packet
  loss and missing samples -- deterministically, so the error budget and
  the downstream fit can be exercised against known faults.

**The load-bearing line.** A BVD fit here recovers the parameters this
module *planted* in a synthetic sweep. No crystal was cut, electroded,
mounted or swept and no analyzer read anything, so the fit is a
``SYNTHETIC_OBSERVATION`` and a measured device's parameters are
``PREREGISTERED_NOT_RUN`` / ``BLOCKED_MISSING_INPUT``.
:func:`refuse_synthetic_fit_as_measured_device` and
:func:`refuse_sweep_as_measurement` draw that line, and the REAL device
acquires nothing.

This module extends the R13 measurement stack -- it reuses
:func:`r13.qcmstack.synthetic_bvd_sweep` and :func:`r13.qcmstack.fit_bvd`
for the impedance sweep and the BVD fit, :class:`r13.piezobridge.BVDCircuit`
for the equivalent circuit, and :mod:`r13.response` for the transfer
function -- and it is typed against the R15 claim taxonomy in
:mod:`r15.claims`. It hard-imports no sibling R15 phase module.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r15 import claims
from r13.qcmstack import BVDResonator, synthetic_bvd_sweep, fit_bvd
from r13.piezobridge import BVDCircuit
from r13 import response as _resp

# --- verdict and standing claim vocabulary -------------------------------

#: The standing verdict for this module.
VERDICT = "ELECTRICAL_LANE_TYPED_NO_DEVICE_SYNTHETIC_BVD_RECOVERED"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"
#: A real electrical sweep has been designed but not run.
PHYSICAL_RUN = "PREREGISTERED_NOT_RUN"

#: The ceiling for a synthetic sweep or a fit to one: a synthetic
#: observation, never a measurement.
SWEEP_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION
FIT_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION
#: An OSL de-embedding is a calibration self-test result.
CALIBRATION_CLAIM_CLASS = claims.ClaimClass.CALIBRATION_RESULT
#: The class of the lane machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED

#: Boltzmann constant, J/K -- for the Johnson-Nyquist thermal noise model.
BOLTZMANN_J_PER_K = 1.380649e-23
#: A conventional laboratory reference temperature, kelvin.
ROOM_TEMPERATURE_K = 290.0


class ElectricalError(RuntimeError):
    """Raised on any electrical-lane refusal or structural guard.

    Covers the guards (a non-finite value, a degenerate sweep, a mismatched
    array) and is the base of :class:`NoElectricalHardwareError` and
    :class:`CalibrationLimitError` and the load-bearing refusals.
    """


class NoElectricalHardwareError(ElectricalError):
    """Raised when a REAL_DEVICE is asked to sweep.

    There is no impedance analyzer, LCR bridge or crystal here, so a real
    sweep acquires nothing. The read is BLOCKED at the hardware-access
    boundary and the physical run is PREREGISTERED_NOT_RUN.
    """


class CalibrationLimitError(ElectricalError):
    """Raised when an OSL calibration is applied outside its valid grid.

    A calibration corrects only the frequencies it was measured on. Asking
    it to correct a sweep on a different or out-of-range grid is refused
    rather than silently extrapolated.
    """


def _finite(value: object, what: str) -> float:
    try:
        x = float(value)                              # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ElectricalError(f"cannot read {value!r} as {what}") from None
    if not math.isfinite(x):
        raise ElectricalError(f"{what} must be finite, got {value!r}")
    return x


def _positive(value: object, what: str) -> float:
    x = _finite(value, what)
    if x <= 0.0:
        raise ElectricalError(f"{what} must be positive, got {x!r}")
    return x


# --- (1) the constitutive electrical relations ---------------------------

def impedance_from_vi(voltage, current) -> np.ndarray:
    """Complex impedance ``Z = V / I`` from complex voltage and current.

    The defining electrical relation. ``voltage`` and ``current`` are
    complex phasors (scalars or matching arrays); a zero current has no
    defined impedance and is refused.
    """
    v = np.asarray(voltage, dtype=complex)
    i = np.asarray(current, dtype=complex)
    if v.shape != i.shape:
        raise ElectricalError("voltage and current must have the same shape")
    if np.any(i == 0):
        raise ElectricalError(
            "a zero current has no defined impedance V/I; refused")
    return v / i


def admittance(impedance) -> np.ndarray:
    """Complex admittance ``Y = 1 / Z``, the reciprocal of impedance."""
    z = np.asarray(impedance, dtype=complex)
    if np.any(z == 0):
        raise ElectricalError(
            "a zero impedance has no defined admittance 1/Z; refused")
    return 1.0 / z


def phase_deg(impedance) -> np.ndarray:
    """The phase angle of a complex impedance, in degrees."""
    z = np.asarray(impedance, dtype=complex)
    return np.degrees(np.angle(z))


def charge_from_current(current, t) -> np.ndarray:
    """Accumulated charge ``q(t) = integral i dt`` by the trapezoid rule.

    Charge is the time integral of current. Returns a running total the
    same length as ``current``, starting at zero, on the supplied time base
    ``t`` (which must be strictly increasing).
    """
    i = np.asarray(current, dtype=float)
    tt = np.asarray(t, dtype=float)
    if i.shape != tt.shape or i.ndim != 1 or i.size < 2:
        raise ElectricalError(
            "current and t must be matching 1-D arrays of at least 2 points")
    dt = np.diff(tt)
    if np.any(dt <= 0.0):
        raise ElectricalError("the time base t must be strictly increasing")
    steps = 0.5 * (i[1:] + i[:-1]) * dt
    return np.concatenate(([0.0], np.cumsum(steps)))


def johnson_noise_voltage(resistance: float, bandwidth_hz: float,
                          temperature_k: float = ROOM_TEMPERATURE_K) -> float:
    """RMS Johnson-Nyquist thermal noise voltage ``sqrt(4 kB T R B)``.

    The unavoidable thermal noise across a resistor ``R`` in a bandwidth
    ``B`` at temperature ``T``. A model of the electrical noise floor; not
    a measured noise reading.
    """
    r = _positive(resistance, "the resistance")
    b = _positive(bandwidth_hz, "the bandwidth")
    temp = _positive(temperature_k, "the temperature")
    return math.sqrt(4.0 * BOLTZMANN_J_PER_K * temp * r * b)


# --- (2) source / load impedance and the transfer function ---------------

@dataclass(frozen=True)
class SourceLoad:
    """The source (output) and load (meter input) impedances of a setup.

    A real sweep is never taken through ideal wires: the driver has an
    output impedance and the meter a finite input impedance, and both load
    the device under test. Tracking them is required so the raw reading can
    be corrected back to the DUT.
    """

    source_ohm: float = 50.0
    load_ohm: float = 1.0e6

    def __post_init__(self) -> None:
        _positive(self.source_ohm, "the source impedance")
        _positive(self.load_ohm, "the load impedance")

    def divider_transfer(self, z_dut) -> np.ndarray:
        """The transfer function ``H = Z_meas / (Z_source + Z_meas)``.

        ``Z_meas`` is the DUT in parallel with the meter's input impedance;
        ``H`` is the fraction of the source voltage that appears at the
        meter. A model of how source and load impedance shape the reading.
        """
        z = np.asarray(z_dut, dtype=complex)
        z_meas = z * self.load_ohm / (z + self.load_ohm)
        return z_meas / (self.source_ohm + z_meas)

    def as_dict(self) -> dict:
        return {"source_ohm": self.source_ohm, "load_ohm": self.load_ohm}


def single_pole_transfer(pole_rate: float, s: complex) -> complex:
    """A single-real-pole transfer function ``H(s) = 1/(s + a)``.

    Reuses the R13 linear-response state-space core
    (:func:`r13.response.statespace_transfer`) so the lane's transfer-
    function machinery is the same one used across the release. For a BVD
    motional branch the terminal admittance answers through exactly this
    kind of pole; here it is a model evaluation, not a measurement.
    """
    a = _positive(pole_rate, "the pole rate a")
    return _resp.statespace_transfer([[-a]], [[1.0]], [[1.0]], [[0.0]], s)


# --- (3) the fixture: cable capacitance and lead resistance --------------

class ConnectionTopology(Enum):
    """How the DUT is wired to the analyzer.

    Two-wire carries the lead impedance in series with the DUT; four-wire
    (Kelvin) senses across the DUT so the lead impedance drops out; a bridge
    is a null-balance topology, modelled here like a four-wire connection
    with the shunt fixture capacitance still present.
    """

    TWO_WIRE = "two_wire"
    FOUR_WIRE = "four_wire"
    BRIDGE = "bridge"


@dataclass(frozen=True)
class FixtureModel:
    """The parasitics of the test fixture: a shunt cable capacitance and a
    series lead impedance.

    The cable capacitance ``C_cable`` sits in parallel with the DUT at the
    node; the lead resistance and inductance sit in series between the
    analyzer and that node. A four-wire or bridge connection removes the
    series lead term; the shunt cable capacitance is present in all
    topologies. These are the fixture effects an OSL calibration removes.
    """

    cable_capacitance_f: float = 0.0
    lead_resistance_ohm: float = 0.0
    lead_inductance_h: float = 0.0
    topology: ConnectionTopology = ConnectionTopology.TWO_WIRE

    def __post_init__(self) -> None:
        _finite(self.cable_capacitance_f, "the cable capacitance")
        _finite(self.lead_resistance_ohm, "the lead resistance")
        _finite(self.lead_inductance_h, "the lead inductance")
        if self.cable_capacitance_f < 0.0 or self.lead_resistance_ohm < 0.0 \
                or self.lead_inductance_h < 0.0:
            raise ElectricalError("fixture parasitics must be non-negative")
        if not isinstance(self.topology, ConnectionTopology):
            raise ElectricalError("topology must be a ConnectionTopology")

    def shunt_admittance(self, freqs: np.ndarray) -> np.ndarray:
        """The shunt cable admittance ``Y_shunt = j w C_cable``."""
        w = 2.0 * math.pi * np.asarray(freqs, dtype=float)
        return 1j * w * self.cable_capacitance_f

    def series_impedance(self, freqs: np.ndarray) -> np.ndarray:
        """The series lead impedance ``R_lead + j w L_lead``.

        Zero for a four-wire or bridge connection, which senses across the
        DUT and so does not carry the lead impedance.
        """
        w = 2.0 * math.pi * np.asarray(freqs, dtype=float)
        if self.topology in (ConnectionTopology.FOUR_WIRE,
                             ConnectionTopology.BRIDGE):
            return np.zeros_like(w, dtype=complex)
        return self.lead_resistance_ohm + 1j * w * self.lead_inductance_h

    def embed(self, freqs: np.ndarray, z_dut: np.ndarray) -> np.ndarray:
        """Embed a bare DUT impedance behind this fixture.

        The node sees the DUT in parallel with the cable capacitance; the
        analyzer sees that node through the series lead impedance:
        ``Z = Z_series + 1/(1/Z_dut + Y_shunt)``.
        """
        z = np.asarray(z_dut, dtype=complex)
        y_node = 1.0 / z + self.shunt_admittance(freqs)
        return self.series_impedance(freqs) + 1.0 / y_node


#: The default synthetic resonator: f_s = 1 MHz, Q = 1000 (from R13).
DEFAULT_RESONATOR = BVDResonator(R=10.0, L=1.5915e-3, C=1.5915e-11,
                                 C0=1.0e-10)


def bvd_circuit(resonator: BVDResonator = DEFAULT_RESONATOR) -> BVDCircuit:
    """The R13 :class:`~r13.piezobridge.BVDCircuit` for a resonator.

    Re-expresses the planted motional ``R, L, C`` and static ``C0`` as the
    equivalent-circuit object from the piezo bridge, so the lane and the
    bridge share one BVD representation.
    """
    return BVDCircuit(R=resonator.R, L=resonator.L, C=resonator.C,
                      C0=resonator.C0)


# --- (4) the synthetic impedance sweep -----------------------------------

def synthetic_electrical_sweep(resonator: BVDResonator = DEFAULT_RESONATOR,
                               *, fixture: FixtureModel | None = None,
                               n: int = 16001, seed: int = 0,
                               noise: float = 0.0) -> dict:
    """Synthesize a complex impedance sweep of a BVD resonator behind a fixture.

    Starts from :func:`r13.qcmstack.synthetic_bvd_sweep` (the bare BVD
    impedance), embeds it behind the fixture parasitics if any, and adds
    seeded complex noise. Deterministic under ``seed``: same seed, identical
    sweep. Every number is generated here; nothing is measured.
    """
    if not isinstance(resonator, BVDResonator):
        raise ElectricalError("synthetic_electrical_sweep needs a BVDResonator")
    fix = fixture if fixture is not None else FixtureModel()
    base = synthetic_bvd_sweep(resonator, n=int(n))
    freqs = base["freqs_hz"]
    z = fix.embed(freqs, base["Z"])
    if noise:
        rng = np.random.default_rng(int(seed))
        scale = float(noise) * float(np.median(np.abs(z)))
        z = z + scale * (rng.standard_normal(z.size)
                         + 1j * rng.standard_normal(z.size))
    return {
        "freqs_hz": freqs,
        "Z": z,
        "Y": 1.0 / z,
        "true_R": resonator.R,
        "true_L": resonator.L,
        "true_C": resonator.C,
        "true_C0": resonator.C0,
        "true_f_s": base["true_f_s"],
        "true_f_p": base["true_f_p"],
        "true_Q": base["true_Q"],
        "fixture": {
            "cable_capacitance_f": fix.cable_capacitance_f,
            "lead_resistance_ohm": fix.lead_resistance_ohm,
            "topology": fix.topology.value,
        },
        "seed": int(seed),
        "measured_here": MEASURED_HERE,
    }


# --- (5) the four device modes behind one lane interface -----------------

class ElectricalDeviceMode(Enum):
    """The four acquisition modes behind the one electrical lane interface."""

    REAL_DEVICE = "REAL_DEVICE"
    SYNTHETIC_DEVICE = "SYNTHETIC_DEVICE"
    REPLAY_DEVICE = "REPLAY_DEVICE"
    FAULT_INJECTION_DEVICE = "FAULT_INJECTION_DEVICE"


class FaultMode(Enum):
    """The five ordinary instrument pathologies the lane can inject."""

    CLIPPING = "clipping"
    DRIFT = "drift"
    SATURATION = "saturation"
    PACKET_LOSS = "packet_loss"
    MISSING_SAMPLES = "missing_samples"


@dataclass(frozen=True)
class ElectricalSweep:
    """A single impedance sweep produced behind the lane interface.

    ``freqs_hz`` and ``Z`` are matching arrays; ``claim_class`` is capped at
    ``SYNTHETIC_OBSERVATION`` and can never be a measurement class. A
    fault-injection sweep carries the faults that were applied.
    """

    instrument_id: str
    mode: ElectricalDeviceMode
    topology: ConnectionTopology
    freqs_hz: np.ndarray
    Z: np.ndarray
    seed: int
    claim_class: claims.ClaimClass = SWEEP_CLAIM_CLASS
    faults: tuple = ()
    source_load: SourceLoad | None = None

    def __post_init__(self) -> None:
        if self.claim_class in claims.MEASUREMENT_CLASSES:
            claims.refuse_synthetic_as_physical()
        f = np.asarray(self.freqs_hz, dtype=float)
        z = np.asarray(self.Z, dtype=complex)
        if f.shape != z.shape or f.ndim != 1:
            raise ElectricalError("freqs and Z must be matching 1-D arrays")

    @property
    def admittance(self) -> np.ndarray:
        return 1.0 / np.asarray(self.Z, dtype=complex)

    def digest(self) -> str:
        """A deterministic hash of the complex sweep for canonical compare."""
        z = np.ascontiguousarray(self.Z, dtype=complex)
        return hashlib.sha256(z.tobytes()).hexdigest()

    def as_dict(self) -> dict:
        z = np.asarray(self.Z, dtype=complex)
        return {
            "instrument_id": self.instrument_id,
            "mode": self.mode.value,
            "topology": self.topology.value,
            "n_points": int(z.size),
            "seed": int(self.seed),
            "faults": [f.value for f in self.faults],
            "z_sha256": self.digest(),
            "claim_class": self.claim_class.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


class ElectricalLane:
    """Base of the one impedance-sweep interface. Not used directly."""

    def __init__(self, instrument_id: str,
                 mode: ElectricalDeviceMode) -> None:
        self.instrument_id = str(instrument_id)
        self.mode = mode

    def acquire_sweep(self, *, seed: int = 0) -> ElectricalSweep:
        raise NotImplementedError


class RealElectricalDevice(ElectricalLane):
    """A real electrical lane with no analyzer behind it.

    A sweep acquires nothing: it raises :class:`NoElectricalHardwareError`.
    The device offers :meth:`blocked_receipt` so callers record the honest
    PREREGISTERED_NOT_RUN state instead of a fabricated sweep.
    """

    def __init__(self, instrument_id: str = "real_impedance_analyzer",
                 topology: ConnectionTopology = ConnectionTopology.FOUR_WIRE
                 ) -> None:
        super().__init__(instrument_id, ElectricalDeviceMode.REAL_DEVICE)
        self.topology = topology

    def acquire_sweep(self, *, seed: int = 0) -> ElectricalSweep:
        raise NoElectricalHardwareError(
            f"refused: {self.instrument_id} is a REAL_DEVICE and no impedance "
            f"analyzer, LCR bridge or crystal exists in this repository, so "
            f"it acquires NOTHING. The sweep is BLOCKED at the "
            f"hardware-access boundary, not faked. A physical sweep is "
            f"{PHYSICAL_RUN}; the measured BVD parameters are "
            f"BLOCKED_MISSING_INPUT pending a built, calibrated instrument. "
            f"{PHYSICAL_VALIDATION}. {VERDICT}")

    def blocked_receipt(self) -> dict:
        """The honest BLOCKED / PREREGISTERED_NOT_RUN receipt for a real sweep."""
        return {
            "instrument_id": self.instrument_id,
            "mode": self.mode.value,
            "topology": self.topology.value,
            "status": "BLOCKED",
            "reason": ("no impedance analyzer, LCR bridge or crystal present; "
                       "acquires nothing"),
            "acquired": False,
            "n_points": 0,
            "claim_class": "BLOCKED_MISSING_INPUT",
            "physical_run": PHYSICAL_RUN,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


class SyntheticElectricalDevice(ElectricalLane):
    """A deterministic synthetic impedance-sweep source.

    Holds a planted :class:`~r13.qcmstack.BVDResonator` behind a
    :class:`FixtureModel`. Same seed => identical sweep. The sweep is a
    ``SYNTHETIC_OBSERVATION``.
    """

    def __init__(self, resonator: BVDResonator = DEFAULT_RESONATOR, *,
                 instrument_id: str = "synthetic_impedance_analyzer",
                 fixture: FixtureModel | None = None, n: int = 16001,
                 noise: float = 0.0,
                 source_load: SourceLoad | None = None) -> None:
        super().__init__(instrument_id, ElectricalDeviceMode.SYNTHETIC_DEVICE)
        if not isinstance(resonator, BVDResonator):
            raise ElectricalError("SyntheticElectricalDevice needs a BVDResonator")
        self.resonator = resonator
        self.fixture = fixture if fixture is not None else FixtureModel()
        self.n = int(n)
        self.noise = float(noise)
        self.source_load = source_load

    def acquire_sweep(self, *, seed: int = 0) -> ElectricalSweep:
        data = synthetic_electrical_sweep(self.resonator, fixture=self.fixture,
                                          n=self.n, seed=int(seed),
                                          noise=self.noise)
        return ElectricalSweep(
            instrument_id=self.instrument_id,
            mode=self.mode,
            topology=self.fixture.topology,
            freqs_hz=data["freqs_hz"],
            Z=data["Z"],
            seed=int(seed),
            source_load=self.source_load,
        )


class ReplayElectricalDevice(ElectricalLane):
    """Replays a previously recorded (synthetic) sweep point-for-point.

    It reads back what was stored and measures nothing new; the sweep is a
    ``SYNTHETIC_OBSERVATION`` of a recorded artifact.
    """

    def __init__(self, recorded: ElectricalSweep, *,
                 instrument_id: str = "replay_impedance_analyzer") -> None:
        super().__init__(instrument_id, ElectricalDeviceMode.REPLAY_DEVICE)
        if not isinstance(recorded, ElectricalSweep):
            raise ElectricalError("ReplayElectricalDevice needs an ElectricalSweep")
        self._freqs = np.asarray(recorded.freqs_hz, dtype=float).copy()
        self._z = np.asarray(recorded.Z, dtype=complex).copy()
        self._topology = recorded.topology

    def acquire_sweep(self, *, seed: int = 0) -> ElectricalSweep:
        return ElectricalSweep(
            instrument_id=self.instrument_id,
            mode=self.mode,
            topology=self._topology,
            freqs_hz=self._freqs.copy(),
            Z=self._z.copy(),
            seed=int(seed),
        )


#: A stable integer tag per fault so its rng stream is distinct yet
#: reproducible under the acquisition seed.
_FAULT_TAG: dict[FaultMode, int] = {
    FaultMode.CLIPPING: 0x0C,
    FaultMode.DRIFT: 0x0D,
    FaultMode.SATURATION: 0x05,
    FaultMode.PACKET_LOSS: 0x0B,
    FaultMode.MISSING_SAMPLES: 0x0A,
}


def _apply_electrical_fault(fault: FaultMode, z: np.ndarray, config: dict,
                            rng: np.random.Generator) -> np.ndarray:
    """Apply one fault to a copy of a complex sweep ``z``, deterministically.

    Each fault demonstrably alters the sweep relative to the clean synthetic
    one, and each is a distinct, recognised instrument pathology.
    """
    out = np.asarray(z, dtype=complex).copy()
    n = out.size
    if n == 0:
        return out
    mag = np.abs(out)
    peak = float(np.max(mag))
    scale = peak if peak > 0.0 else 1.0

    if fault is FaultMode.CLIPPING:
        # soft-clip the magnitude at a fraction of the peak, keep phase
        level = float(config.get("clip_fraction", 0.7)) * scale
        clipped = np.minimum(mag, level)
        phase = np.exp(1j * np.angle(out))
        return clipped * phase

    if fault is FaultMode.DRIFT:
        # a slow linear baseline drift added to the real part
        slope = float(config.get("drift_fraction", 0.5)) * scale
        return out + np.linspace(0.0, slope, n)

    if fault is FaultMode.SATURATION:
        # a hard magnitude rail: points beyond the rail flatten onto it
        rail = float(config.get("saturation_fraction", 0.4)) * scale
        mag2 = np.abs(out)
        railed = np.where(mag2 > rail, rail, mag2)
        phase = np.exp(1j * np.angle(out))
        return railed * phase

    if fault is FaultMode.PACKET_LOSS:
        # one contiguous block of frequency points is lost and zero-filled
        frac = float(config.get("packet_fraction", 0.1))
        length = max(1, int(round(frac * n)))
        start = int(rng.integers(0, max(1, n - length + 1)))
        out[start:start + length] = 0.0
        return out

    if fault is FaultMode.MISSING_SAMPLES:
        # scattered individual points go missing (NaN)
        frac = float(config.get("missing_fraction", 0.05))
        k = max(1, int(round(frac * n)))
        idx = rng.choice(n, size=min(k, n), replace=False)
        out[idx] = np.nan
        return out

    raise ElectricalError(f"unknown fault {fault!r}")  # pragma: no cover


class FaultInjectionElectricalDevice(ElectricalLane):
    """Wraps a :class:`SyntheticElectricalDevice` and injects sweep faults.

    Deterministic under the acquisition seed: each fault's stream is derived
    from the same seed, so the same seed reproduces the same faulty sweep.
    Every :class:`FaultMode` is injectable, and the applied faults are
    carried on the :class:`ElectricalSweep`.
    """

    def __init__(self, inner: SyntheticElectricalDevice, faults: tuple, *,
                 instrument_id: str = "fault_impedance_analyzer",
                 config: dict | None = None) -> None:
        super().__init__(instrument_id,
                         ElectricalDeviceMode.FAULT_INJECTION_DEVICE)
        if not isinstance(inner, SyntheticElectricalDevice):
            raise ElectricalError(
                "FaultInjectionElectricalDevice wraps a SyntheticElectricalDevice")
        faults = tuple(faults)
        if not faults:
            raise ElectricalError(
                "a fault-injection device with no faults injects nothing; "
                "supply at least one FaultMode")
        for f in faults:
            if not isinstance(f, FaultMode):
                raise ElectricalError(f"{f!r} is not a FaultMode")
        self.inner = inner
        self.faults = faults
        self.config = dict(config or {})

    def acquire_sweep(self, *, seed: int = 0) -> ElectricalSweep:
        clean = self.inner.acquire_sweep(seed=seed)
        z = np.asarray(clean.Z, dtype=complex).copy()
        for f in self.faults:
            rng = np.random.default_rng(
                np.random.SeedSequence([int(seed), _FAULT_TAG[f]]))
            z = _apply_electrical_fault(f, z, self.config, rng)
        return ElectricalSweep(
            instrument_id=self.instrument_id,
            mode=self.mode,
            topology=clean.topology,
            freqs_hz=clean.freqs_hz,
            Z=z,
            seed=int(seed),
            faults=self.faults,
        )


# --- (6) the BVD fit -----------------------------------------------------

def fit_synthetic_bvd(sweep: ElectricalSweep) -> dict:
    """Recover ``f_s, f_p, Q, R, L, C, C0`` from a synthetic sweep.

    Delegates the fit to :func:`r13.qcmstack.fit_bvd` and re-types the
    result to the R15 taxonomy: it is a ``SYNTHETIC_OBSERVATION``, never a
    measured device. A REAL or fault-injection sweep must not be fit as a
    clean recovery -- a real sweep does not exist, and a fault sweep carries
    injected pathology -- so both are refused.
    """
    if not isinstance(sweep, ElectricalSweep):
        raise ElectricalError("fit_synthetic_bvd needs an ElectricalSweep")
    if sweep.mode is ElectricalDeviceMode.REAL_DEVICE:
        raise NoElectricalHardwareError(
            "refused: a REAL_DEVICE sweep does not exist; there is nothing to "
            f"fit. {PHYSICAL_RUN}. {PHYSICAL_VALIDATION}.")
    if sweep.faults:
        raise ElectricalError(
            "refused: this sweep carries injected faults "
            f"{[f.value for f in sweep.faults]}; a fault-injection sweep is "
            "for exercising the error budget, not for a clean BVD recovery")
    fit = fit_bvd(sweep.freqs_hz, sweep.Z)
    return {
        "f_s_hz": fit["f_s_hz"],
        "f_p_hz": fit["f_p_hz"],
        "Q": fit["Q"],
        "fwhm_hz": fit["fwhm_hz"],
        "R": fit["R"],
        "L": fit["L"],
        "C": fit["C"],
        "C0": fit["C0"],
        "claim_class": FIT_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "note": ("a fit to a SYNTHETIC impedance sweep planted in this "
                 "module; not a measurement of any crystal"),
    }


# --- (7) the open-short-load de-embedding calibration --------------------

@dataclass(frozen=True)
class OSLCalibration:
    """A one-port open-short-load de-embedding calibration.

    Built from three standards measured on a fixed frequency grid: an
    *open* (DUT removed, revealing the shunt cable admittance), a *short*
    (revealing the series lead impedance), and a *load* (a known resistance,
    for a tracking check). :meth:`correct` removes the series and shunt
    fixture terms from a raw sweep so the recovered impedance is the bare
    DUT. It corrects only the grid it was measured on -- an out-of-range
    request raises :class:`CalibrationLimitError`.
    """

    freqs_hz: np.ndarray
    z_short: np.ndarray          # series lead impedance
    z_open: np.ndarray           # series + 1/shunt admittance
    load_ohm: float

    def __post_init__(self) -> None:
        f = np.asarray(self.freqs_hz, dtype=float)
        object.__setattr__(self, "freqs_hz", f)
        object.__setattr__(self, "z_short",
                           np.asarray(self.z_short, dtype=complex))
        object.__setattr__(self, "z_open",
                           np.asarray(self.z_open, dtype=complex))
        if not (f.shape == self.z_short.shape == self.z_open.shape):
            raise ElectricalError("OSL standards must share the grid shape")
        if f.ndim != 1 or f.size < 8:
            raise ElectricalError("an OSL calibration needs >= 8 grid points")
        _positive(self.load_ohm, "the OSL load resistance")

    @property
    def shunt_admittance(self) -> np.ndarray:
        """The recovered shunt admittance ``Y_shunt = 1/(Z_open - Z_short)``."""
        delta = self.z_open - self.z_short
        if np.any(delta == 0):
            raise ElectricalError(
                "the open and short standards coincide; no shunt term to "
                "recover")
        return 1.0 / delta

    def recovered_cable_capacitance_f(self) -> float:
        """The cable capacitance implied by the shunt admittance.

        ``Im(Y_shunt) = w C_cable``, so ``C_cable = median(Im(Y_shunt)/w)``.
        This is how the fixture's cable capacitance appears in the
        calibration.
        """
        w = 2.0 * math.pi * self.freqs_hz
        return float(np.median(np.imag(self.shunt_admittance) / w))

    def correct(self, freqs_hz, z_meas) -> np.ndarray:
        """De-embed a raw sweep back to the bare DUT impedance.

        ``Z_dut = 1 / (1/(Z_meas - Z_short) - Y_shunt)``. Refuses any grid
        that does not match the calibration grid: a calibration corrects
        only the frequencies it was measured on.
        """
        f = np.asarray(freqs_hz, dtype=float)
        z = np.asarray(z_meas, dtype=complex)
        if f.shape != self.freqs_hz.shape:
            raise CalibrationLimitError(
                f"refused: this OSL calibration covers {self.freqs_hz.size} "
                f"grid points; a sweep of {f.size} points is outside it")
        if not np.allclose(f, self.freqs_hz, rtol=1e-9, atol=0.0):
            raise CalibrationLimitError(
                "refused: the sweep grid does not match the OSL calibration "
                "grid; a calibration corrects only the frequencies it was "
                "measured on, it is not extrapolated")
        node = z - self.z_short
        if np.any(node == 0):
            raise ElectricalError("a corrected node impedance is zero; the "
                                  "sweep coincides with the short standard")
        y_dut = 1.0 / node - self.shunt_admittance
        if np.any(y_dut == 0):
            raise ElectricalError("a corrected DUT admittance is zero")
        return 1.0 / y_dut

    def as_dict(self) -> dict:
        return {
            "n_points": int(self.freqs_hz.size),
            "f_lo_hz": float(self.freqs_hz[0]),
            "f_hi_hz": float(self.freqs_hz[-1]),
            "load_ohm": float(self.load_ohm),
            "recovered_cable_capacitance_f":
                self.recovered_cable_capacitance_f(),
            "claim_class": CALIBRATION_CLAIM_CLASS.value,
            "measured_here": MEASURED_HERE,
        }


def build_osl_calibration(freqs_hz, fixture: FixtureModel, *,
                          load_ohm: float = 50.0) -> OSLCalibration:
    """Synthesize the three OSL standards for a fixture.

    Uses the same embedding network as :func:`synthetic_electrical_sweep`:
    the open standard is the fixture with the DUT removed
    (``Z_open = Z_series + 1/Y_shunt``), the short standard is the fixture
    with the DUT shorted (``Z_short = Z_series``), and the load standard is
    a known resistance behind the fixture (kept for a tracking check). A
    calibration self-test, not a measured calibration.
    """
    if not isinstance(fixture, FixtureModel):
        raise ElectricalError("build_osl_calibration needs a FixtureModel")
    f = np.asarray(freqs_hz, dtype=float)
    z_series = fixture.series_impedance(f)
    y_shunt = fixture.shunt_admittance(f)
    if np.any(y_shunt == 0):
        raise ElectricalError(
            "this fixture has no cable capacitance, so the open standard is "
            "an open circuit; an OSL de-embedding needs a finite shunt term")
    z_open = z_series + 1.0 / y_shunt
    z_short = z_series.astype(complex)
    return OSLCalibration(freqs_hz=f, z_short=z_short, z_open=z_open,
                          load_ohm=float(load_ohm))


# --- (8) ordinary electrical pathology detectors -------------------------

def detect_saturation(samples, rail: float | None = None,
                      fraction_threshold: float = 0.02) -> dict:
    """Detect saturation (railing) in a real record.

    Flags saturation when more than ``fraction_threshold`` of the samples
    sit at or beyond a hard rail. Without an explicit ``rail`` the rail is
    taken as the record's own maximum magnitude, which detects a flat-topped
    (clipped) record.
    """
    x = np.abs(np.asarray(samples, dtype=float))
    if x.size == 0:
        raise ElectricalError("an empty record has no saturation to detect")
    lim = float(np.max(x)) if rail is None else _positive(rail, "the rail")
    at_rail = int(np.count_nonzero(x >= lim * (1.0 - 1e-9)))
    frac = at_rail / x.size
    return {
        "saturated": bool(frac > fraction_threshold),
        "fraction_at_rail": frac,
        "rail": lim,
    }


def detect_ground_loop(samples, sample_rate_hz: float,
                       mains_hz: tuple = (50.0, 60.0),
                       ratio_threshold: float = 8.0) -> dict:
    """Detect a mains-frequency ground-loop pickup in a real record.

    A ground loop injects power at the mains line frequency (50 or 60 Hz).
    Compares the spectral power in a narrow band around each mains frequency
    to the median spectral power; a ratio above ``ratio_threshold`` flags a
    ground loop.
    """
    x = np.asarray(samples, dtype=float)
    if x.ndim != 1 or x.size < 16:
        raise ElectricalError("a ground-loop check needs a 1-D record of >= 16 "
                              "samples")
    rate = _positive(sample_rate_hz, "the sample rate")
    x = x - float(np.mean(x))
    mag = np.abs(np.fft.rfft(x * np.hanning(x.size)))
    freqs = np.fft.rfftfreq(x.size, 1.0 / rate)
    power = mag ** 2
    median = float(np.median(power[1:])) if power.size > 1 else 0.0
    best_ratio = 0.0
    best_f = None
    for mf in mains_hz:
        if mf >= rate / 2.0:
            continue
        band = np.abs(freqs - mf) <= max(2.0, rate / x.size)
        if not np.any(band):
            continue
        peak = float(np.max(power[band]))
        ratio = peak / median if median > 0.0 else 0.0
        if ratio > best_ratio:
            best_ratio, best_f = ratio, mf
    return {
        "ground_loop": bool(best_ratio > ratio_threshold),
        "mains_hz": best_f,
        "power_ratio": best_ratio,
    }


# --- (9) the electrical error budget and observation record --------------

#: The one-sigma electrical uncertainty components, dimensionless relative
#: contributions to the impedance magnitude. Placeholders, not measured.
_ELECTRICAL_COMPONENT_SIGMAS = {
    "instrument_resolution": 0.010,
    "calibration": 0.008,
    "clock": 0.002,
    "environment": 0.004,
    "fixture_repeatability": 0.006,
    "cable_capacitance": 0.005,
    "lead_resistance": 0.004,
    "dsp_windowing": 0.003,
    "model_residual": 0.005,
}

#: Coverage factor for the expanded uncertainty (k=2, ~95%).
COVERAGE_FACTOR = 2.0


def electrical_error_budget(budget_id: str = "P14_electrical_impedance"
                            ) -> dict:
    """The electrical error budget, conforming to ``error_budget.schema``.

    The relative-uncertainty components combine in quadrature
    (root-sum-of-squares of independent contributions); the expanded
    uncertainty is ``k`` times the combined standard uncertainty. A modelled
    budget over synthetic components, not a measured uncertainty.
    """
    components = [
        {"name": name, "type": "B", "distribution": "normal",
         "relative_standard_uncertainty": sigma}
        for name, sigma in _ELECTRICAL_COMPONENT_SIGMAS.items()
    ]
    combined = math.sqrt(sum(s * s
                             for s in _ELECTRICAL_COMPONENT_SIGMAS.values()))
    return {
        "budget_id": budget_id,
        "quantity": "impedance_magnitude_relative",
        "components": components,
        "combination_method": "root_sum_of_squares",
        "combined_uncertainty": combined,
        "coverage_factor": COVERAGE_FACTOR,
    }


def expanded_uncertainty(budget: dict | None = None) -> float:
    """The expanded (k-times) relative uncertainty of the budget."""
    b = budget if budget is not None else electrical_error_budget()
    return float(b["combined_uncertainty"]) * float(b["coverage_factor"])


def observation_record(fit: dict, *, observation_id: str = "P14_obs_f_s",
                       run_id: str = "P14_synthetic_run") -> dict:
    """A schema-shaped observation record for the fitted series resonance.

    Conforms to ``observation_record.schema``. The ``claim_class`` is
    ``SYNTHETIC_OBSERVATION``: the value is recovered from a synthetic
    sweep, not measured on a crystal.
    """
    budget = electrical_error_budget()
    return {
        "observation_id": observation_id,
        "run_id": run_id,
        "source_artifacts": ["synthetic_electrical_sweep(seed)"],
        "analysis_version": "r15.electrical.fit_synthetic_bvd/1",
        "quantity": "series_resonance_frequency",
        "value": float(fit["f_s_hz"]),
        "units": "Hz",
        "uncertainty": {
            "relative_standard_uncertainty": budget["combined_uncertainty"],
            "coverage_factor": budget["coverage_factor"],
            "note": "modelled electrical budget; not a measured uncertainty",
        },
        "claim_class": SWEEP_CLAIM_CLASS.value,
        "derivation_graph": [
            "BVDResonator (planted) -> synthetic_electrical_sweep -> "
            "fit_synthetic_bvd -> f_s",
        ],
    }


# --- (10) the load-bearing refusals --------------------------------------

def refuse_synthetic_fit_as_measured_device(
        quantity: str = "a fitted BVD parameter") -> None:
    """Refuse a synthetic BVD fit read as a measured device. Always raises.

    :func:`fit_synthetic_bvd` recovers the parameters this module *planted*
    in a synthetic sweep. There is no crystal, impedance analyzer or LCR
    bridge here, so the recovered ``R, L, C, C0, f_s, f_p, Q`` describe a
    model, not a device. A measured device's parameters are
    PREREGISTERED_NOT_RUN / BLOCKED_MISSING_INPUT.
    """
    raise ElectricalError(
        f"refused: {quantity!r} is recovered from a SYNTHETIC impedance "
        f"sweep planted in this module, not measured on a device. No "
        f"crystal was cut, electroded, mounted or swept and no analyzer "
        f"read anything, so the fit is a "
        f"{SWEEP_CLAIM_CLASS.value}. A measured device's R, L, C, C0, f_s, "
        f"f_p or Q is {PHYSICAL_RUN} / BLOCKED_MISSING_INPUT. "
        f"{PHYSICAL_VALIDATION}. {VERDICT}")


def refuse_sweep_as_measurement(
        claim: str = "an impedance sweep is a physical measurement") -> None:
    """Refuse any sweep here read as a physical measurement. Always raises.

    Delegates to the governance core so the refusal is the canonical one:
    every sweep this lane produces is a ``SYNTHETIC_OBSERVATION`` from a
    seeded simulator or a recorded synthetic artifact, and a REAL_DEVICE
    acquires nothing.
    """
    try:
        claims.refuse_synthetic_as_physical()
    except claims.ClaimError as exc:
        raise ElectricalError(
            f"refused: {claim!r}. {exc} {PHYSICAL_VALIDATION}. {VERDICT} "
            f"[{claims.MAX_SOFTWARE_CLASS.value} is the software ceiling]"
        ) from exc


# --- (11) the report -----------------------------------------------------

def electrical_report() -> dict:
    """The standing statement of what the electrical lane is and is not."""
    budget = electrical_error_budget()
    return {
        "what_this_is": (
            "the R15 electrical measurement lane: the constitutive "
            "electrical relations (voltage, current, impedance, admittance, "
            "phase, charge, thermal noise, transfer function), a complex "
            "impedance/admittance sweep and a Butterworth-Van Dyke fit that "
            "recovers f_s, f_p, Q and the motional R, L, C with the static "
            "C0, a cable/lead fixture model, an open-short-load de-embedding "
            "calibration, an electrical error budget, and detectors for "
            "ground loops, saturation and cable capacitance -- behind one "
            "lane interface with four distinct modes"),
        "modes": [m.value for m in ElectricalDeviceMode],
        "topologies": [t.value for t in ConnectionTopology],
        "fault_modes": [f.value for f in FaultMode],
        "reuses": [
            "r13.qcmstack.synthetic_bvd_sweep / fit_bvd (impedance sweep + "
            "BVD fit)",
            "r13.piezobridge.BVDCircuit (equivalent circuit)",
            "r13.response.statespace_transfer (transfer function)",
            "r15.claims (claim taxonomy and forbidden promotions)",
        ],
        "refusals": [
            "REAL_DEVICE.acquire_sweep raises NoElectricalHardwareError "
            "(acquires nothing; PREREGISTERED_NOT_RUN)",
            "fit_synthetic_bvd refuses a REAL or fault-injection sweep",
            "OSLCalibration.correct refuses an out-of-grid sweep "
            "(CalibrationLimitError)",
            "refuse_synthetic_fit_as_measured_device",
            "refuse_sweep_as_measurement",
        ],
        "sweep_claim_class": SWEEP_CLAIM_CLASS.value,
        "fit_claim_class": FIT_CLAIM_CLASS.value,
        "calibration_claim_class": CALIBRATION_CLAIM_CLASS.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "error_budget": budget,
        "expanded_relative_uncertainty": expanded_uncertainty(budget),
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "physical_run": PHYSICAL_RUN,
        "hardware_status": (
            "no impedance analyzer, LCR bridge or crystal exists here; a "
            "REAL_DEVICE sweep is BLOCKED and acquires nothing"),
        "what_would_change_this": (
            "a physical crystal on a calibrated impedance analyzer, its raw "
            "complex sweep captured with an OSL calibration, a clock binding "
            "and an environment log, each with its uncertainty and its null "
            "-- none of which exists in this repository"),
        "what_this_does_not_say": (
            "It does not say any crystal or circuit was measured. A "
            "synthetic sweep is simulator output and a BVD fit recovers "
            "parameters this module PLANTED; there is no impedance analyzer, "
            "LCR bridge or crystal here, a REAL_DEVICE acquires nothing, and "
            "a SYNTHETIC_OBSERVATION is never a PHYSICAL_MEASUREMENT. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION", "PHYSICAL_RUN",
    "SWEEP_CLAIM_CLASS", "FIT_CLAIM_CLASS", "CALIBRATION_CLAIM_CLASS",
    "SOFTWARE_CLAIM_CLASS", "BOLTZMANN_J_PER_K", "ROOM_TEMPERATURE_K",
    "COVERAGE_FACTOR",
    "ElectricalError", "NoElectricalHardwareError", "CalibrationLimitError",
    "impedance_from_vi", "admittance", "phase_deg", "charge_from_current",
    "johnson_noise_voltage", "SourceLoad", "single_pole_transfer",
    "ConnectionTopology", "FixtureModel", "DEFAULT_RESONATOR", "bvd_circuit",
    "synthetic_electrical_sweep",
    "ElectricalDeviceMode", "FaultMode", "ElectricalSweep", "ElectricalLane",
    "RealElectricalDevice", "SyntheticElectricalDevice",
    "ReplayElectricalDevice", "FaultInjectionElectricalDevice",
    "fit_synthetic_bvd",
    "OSLCalibration", "build_osl_calibration",
    "detect_saturation", "detect_ground_loop",
    "electrical_error_budget", "expanded_uncertainty", "observation_record",
    "refuse_synthetic_fit_as_measured_device", "refuse_sweep_as_measurement",
    "electrical_report",
]
