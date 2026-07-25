"""P01 — the instrument registry: one interface, four honest modes.

R15 needs an inventory of every instrument the platform could ever read
from, and it needs that inventory to be honest about which of those
instruments actually exist. This module is that inventory. It carries a
typed :class:`InstrumentRecord` for each instrument -- its id, type, mode,
firmware, clock source, capability set, uncertainty model, calibration
bindings and availability/quarantine status -- and it exposes exactly one
acquisition interface behind which sit four distinct modes.

**The four modes are not interchangeable, and the difference is the whole
point.**

* ``REAL_DEVICE`` is an interface only. There is no laboratory hardware in
  this repository, so a real acquisition acquires *nothing*: it raises a
  typed :class:`NoHardwareError` and returns a ``BLOCKED`` receipt rather
  than fabricating a reading. A blocked real read is the honest state, not
  a failure to paper over.
* ``SYNTHETIC_DEVICE`` produces a deterministic waveform from a driver
  under a numpy seed. Same seed, identical output; different seed,
  different output. It is a simulator, and its output is a
  ``SYNTHETIC_OBSERVATION`` -- never a physical measurement.
* ``REPLAY_DEVICE`` replays a previously recorded (synthetic) artifact
  byte-for-byte. It reads back what was stored; it measures nothing new.
* ``FAULT_INJECTION_DEVICE`` wraps a synthetic device and injects the
  ordinary instrument pathologies -- clipping, drift, saturation, packet
  loss and missing samples -- deterministically, so the downstream error
  budget can be exercised against known faults.

**The registry refuses before it acquires.** :class:`InstrumentRegistry`
checks the two things that invalidate a reading *before* any samples are
produced: an expired calibration (as of a supplied, explicit date -- never
the wall clock) and a capability the instrument does not have. A
quarantined instrument is refused outright. Only after those gates does the
registry delegate to the instrument's mode.

Nothing here is measured. Every synthetic reading is a
``SYNTHETIC_OBSERVATION`` produced by ``numpy.random.default_rng(seed)`` and
a deterministic signal model; the strongest class this module reaches is a
synthetic observation, and a synthetic observation is not a
``PHYSICAL_MEASUREMENT``.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Protocol, runtime_checkable

import numpy as np

from r15 import claims

# --- verdict and standing claim vocabulary -------------------------------

#: The standing verdict for this module.
VERDICT = "INSTRUMENT_REGISTRY_TYPED_NO_HARDWARE"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The ceiling any reading this module produces may carry. A synthetic or
#: replayed reading is a SYNTHETIC_OBSERVATION; it is never a measurement.
READING_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION
#: The class of the registry machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED


class InstrumentError(RuntimeError):
    """Raised on any registry or acquisition refusal.

    Covers the structural guards (an ill-formed record, an unknown
    instrument, a quarantined instrument, an unsupported capability, an
    expired or missing calibration) and is the base of
    :class:`NoHardwareError`.
    """


class NoHardwareError(InstrumentError):
    """Raised when a REAL_DEVICE is asked to acquire.

    There is no physical instrument in this repository, so a real
    acquisition acquires nothing. This is the hardware-access boundary: the
    read is BLOCKED, not faked.
    """


# --- the four modes, the status, and the capability vocabulary -----------

class InstrumentMode(Enum):
    """The four acquisition modes behind the one interface.

    Values match ``instrument_record.schema.json``.
    """

    REAL_DEVICE = "REAL_DEVICE"
    REPLAY_DEVICE = "REPLAY_DEVICE"
    SYNTHETIC_DEVICE = "SYNTHETIC_DEVICE"
    FAULT_INJECTION_DEVICE = "FAULT_INJECTION_DEVICE"


class InstrumentStatus(Enum):
    """Availability of an instrument in the registry."""

    AVAILABLE = "AVAILABLE"
    QUARANTINED = "QUARANTINED"
    #: A real instrument that cannot acquire because no hardware exists.
    BLOCKED_NO_HARDWARE = "BLOCKED_NO_HARDWARE"


class Capability(Enum):
    """A physical quantity an instrument is able to source or acquire.

    A capability is what the instrument *can* do; asking an instrument for
    a capability it does not carry is refused before acquisition.
    """

    SOURCE = "source"
    DIGITIZE = "digitize"
    IMPEDANCE = "impedance"
    ACOUSTIC = "acoustic"
    ACCELERATION = "acceleration"
    PHOTOCURRENT = "photocurrent"
    THERMAL = "thermal"
    MAGNETIC = "magnetic"
    TIMEBASE = "timebase"


class FaultMode(Enum):
    """The instrument pathologies a fault-injection device can inject."""

    CLIPPING = "clipping"
    DRIFT = "drift"
    SATURATION = "saturation"
    PACKET_LOSS = "packet_loss"
    MISSING_SAMPLES = "missing_samples"


# --- calibration bindings -------------------------------------------------

@dataclass(frozen=True)
class Calibration:
    """A calibration certificate with an explicit validity window.

    Validity is checked against a supplied ``as_of`` date, never the wall
    clock, so the refusal path is deterministic and testable.
    """

    calibration_id: str
    quantity: str
    valid_from: date
    valid_until: date

    def __post_init__(self) -> None:
        if not str(self.calibration_id).strip():
            raise InstrumentError("a calibration needs an id")
        if self.valid_until < self.valid_from:
            raise InstrumentError(
                f"{self.calibration_id}: valid_until precedes valid_from")

    def is_valid_at(self, as_of: date) -> bool:
        return self.valid_from <= as_of <= self.valid_until

    def as_dict(self) -> dict:
        return {
            "calibration_id": self.calibration_id,
            "quantity": self.quantity,
            "valid_from": self.valid_from.isoformat(),
            "valid_until": self.valid_until.isoformat(),
        }


# --- the typed instrument record -----------------------------------------

@dataclass(frozen=True)
class InstrumentRecord:
    """The authoritative record for one instrument.

    Matches ``instrument_record.schema.json``: ``instrument_id``,
    ``instrument_type``, ``mode``, ``firmware``, ``clock_source``,
    ``capabilities``, ``uncertainty_model``, ``calibration_ids`` and
    ``status``. ``capabilities`` is a frozenset of :class:`Capability`;
    ``uncertainty_model`` is a non-empty dict describing how the reading's
    uncertainty is modelled (units and a noise model), because a reading
    with no declared uncertainty cannot enter the evidence ladder.
    """

    instrument_id: str
    instrument_type: str
    mode: InstrumentMode
    firmware: str
    clock_source: str
    capabilities: frozenset
    uncertainty_model: dict
    calibration_ids: tuple = ()
    status: InstrumentStatus = InstrumentStatus.AVAILABLE

    def __post_init__(self) -> None:
        if not str(self.instrument_id).strip():
            raise InstrumentError("an instrument needs an id")
        if not str(self.instrument_type).strip():
            raise InstrumentError(
                f"{self.instrument_id}: an instrument needs a type")
        if not isinstance(self.mode, InstrumentMode):
            raise InstrumentError(
                f"{self.instrument_id}: mode must be an InstrumentMode")
        if not isinstance(self.status, InstrumentStatus):
            raise InstrumentError(
                f"{self.instrument_id}: status must be an InstrumentStatus")
        if not self.capabilities:
            raise InstrumentError(
                f"{self.instrument_id}: an instrument with no capability "
                f"transduces nothing and is not an instrument")
        for cap in self.capabilities:
            if not isinstance(cap, Capability):
                raise InstrumentError(
                    f"{self.instrument_id}: capability {cap!r} is not a "
                    f"Capability")
        if not isinstance(self.uncertainty_model, dict) or \
                not self.uncertainty_model:
            raise InstrumentError(
                f"{self.instrument_id}: uncertainty_model must be a "
                f"non-empty dict; a reading with no declared uncertainty "
                f"cannot enter the evidence ladder")
        object.__setattr__(self, "calibration_ids",
                           tuple(self.calibration_ids))

    def supports(self, capability: Capability) -> bool:
        return capability in self.capabilities

    def as_dict(self) -> dict:
        """Canonical, schema-shaped, deterministically ordered."""
        return {
            "instrument_id": self.instrument_id,
            "instrument_type": self.instrument_type,
            "mode": self.mode.value,
            "firmware": self.firmware,
            "clock_source": self.clock_source,
            "capabilities": sorted(c.value for c in self.capabilities),
            "uncertainty_model": dict(self.uncertainty_model),
            "calibration_ids": list(self.calibration_ids),
            "status": self.status.value,
            "measured_here": MEASURED_HERE,
        }


# --- the acquisition result ----------------------------------------------

@dataclass(frozen=True)
class Acquisition:
    """A single reading produced behind the interface.

    ``samples`` is a numpy array; ``claim_class`` is capped at
    ``SYNTHETIC_OBSERVATION`` and can never be a measurement class. A
    fault-injection reading carries the faults that were applied.
    """

    instrument_id: str
    mode: InstrumentMode
    capability: Capability
    samples: np.ndarray
    sample_rate_hz: float
    seed: int
    claim_class: claims.ClaimClass = READING_CLAIM_CLASS
    faults: tuple = ()

    def __post_init__(self) -> None:
        if self.claim_class in claims.MEASUREMENT_CLASSES:
            # the load-bearing refusal, wired to the governance core
            claims.refuse_synthetic_as_physical()

    def digest(self) -> str:
        """A deterministic hash of the samples for canonical comparison."""
        arr = np.ascontiguousarray(self.samples, dtype=float)
        return hashlib.sha256(arr.tobytes()).hexdigest()

    def as_dict(self) -> dict:
        arr = np.asarray(self.samples, dtype=float)
        return {
            "instrument_id": self.instrument_id,
            "mode": self.mode.value,
            "capability": self.capability.value,
            "n_samples": int(arr.size),
            "sample_rate_hz": float(self.sample_rate_hz),
            "seed": int(self.seed),
            "faults": [f.value for f in self.faults],
            "samples_sha256": self.digest(),
            "claim_class": self.claim_class.value,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


# --- the driver protocol (implemented in synthetic_instruments) ----------

@runtime_checkable
class SyntheticDriver(Protocol):
    """A deterministic signal source for a synthetic instrument.

    A driver turns ``(capability, n_samples, seed, sample_rate_hz)`` into a
    numpy array, deterministically under the seed. The concrete drivers
    live in :mod:`r15.synthetic_instruments`; this module only depends on
    the protocol so it carries no per-type signal knowledge.
    """

    instrument_type: str

    def default_sample_rate_hz(self, capability: Capability) -> float: ...

    def generate(self, capability: Capability, n_samples: int, seed: int,
                 sample_rate_hz: float) -> np.ndarray: ...


# --- the one interface, four modes ---------------------------------------

class Instrument:
    """Base of the one acquisition interface. Not used directly."""

    def __init__(self, record: InstrumentRecord) -> None:
        self.record = record

    @property
    def mode(self) -> InstrumentMode:
        return self.record.mode

    def acquire(self, capability: Capability, *, n_samples: int, seed: int,
                sample_rate_hz: float | None = None) -> Acquisition:
        raise NotImplementedError


class RealDevice(Instrument):
    """A real instrument interface with no hardware behind it.

    Acquisition acquires nothing: it raises :class:`NoHardwareError`. The
    device also offers :meth:`blocked_receipt` so callers can record the
    honest BLOCKED state instead of a fabricated reading.
    """

    def __init__(self, record: InstrumentRecord) -> None:
        if record.mode is not InstrumentMode.REAL_DEVICE:
            raise InstrumentError("RealDevice needs a REAL_DEVICE record")
        super().__init__(record)

    def acquire(self, capability: Capability, *, n_samples: int, seed: int,
                sample_rate_hz: float | None = None) -> Acquisition:
        raise NoHardwareError(
            f"refused: {self.record.instrument_id} is a REAL_DEVICE and no "
            f"physical hardware exists in this repository, so it acquires "
            f"NOTHING. The read is BLOCKED at the hardware-access boundary, "
            f"not faked with a synthetic value. A physical reading is "
            f"BLOCKED_MISSING_INPUT pending a built, calibrated instrument. "
            f"{PHYSICAL_VALIDATION}. {VERDICT}")

    def blocked_receipt(self, capability: Capability) -> dict:
        """The honest BLOCKED receipt for a real read that cannot happen."""
        return {
            "instrument_id": self.record.instrument_id,
            "mode": self.record.mode.value,
            "capability": capability.value,
            "status": "BLOCKED",
            "reason": "no physical hardware present; acquires nothing",
            "acquired": False,
            "n_samples": 0,
            "claim_class": "BLOCKED_MISSING_INPUT",
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


class SyntheticDevice(Instrument):
    """A deterministic synthetic instrument driven by a :class:`SyntheticDriver`.

    Same seed => identical samples; different seed => different samples.
    The reading is a ``SYNTHETIC_OBSERVATION``.
    """

    def __init__(self, record: InstrumentRecord,
                 driver: SyntheticDriver) -> None:
        if record.mode is not InstrumentMode.SYNTHETIC_DEVICE:
            raise InstrumentError(
                "SyntheticDevice needs a SYNTHETIC_DEVICE record")
        super().__init__(record)
        self.driver = driver

    def acquire(self, capability: Capability, *, n_samples: int, seed: int,
                sample_rate_hz: float | None = None) -> Acquisition:
        if not self.record.supports(capability):
            raise InstrumentError(
                f"{self.record.instrument_id} does not support "
                f"{capability.value}")
        rate = (self.driver.default_sample_rate_hz(capability)
                if sample_rate_hz is None else float(sample_rate_hz))
        samples = self.driver.generate(capability, int(n_samples), int(seed),
                                       rate)
        return Acquisition(
            instrument_id=self.record.instrument_id,
            mode=self.record.mode,
            capability=capability,
            samples=np.asarray(samples, dtype=float),
            sample_rate_hz=rate,
            seed=int(seed),
        )


class ReplayDevice(Instrument):
    """Replays a previously recorded (synthetic) artifact byte-for-byte.

    It reads back what was stored and measures nothing new; the reading is
    a ``SYNTHETIC_OBSERVATION`` of a recorded artifact.
    """

    def __init__(self, record: InstrumentRecord,
                 artifact: dict[Capability, np.ndarray],
                 sample_rate_hz: float) -> None:
        if record.mode is not InstrumentMode.REPLAY_DEVICE:
            raise InstrumentError("ReplayDevice needs a REPLAY_DEVICE record")
        super().__init__(record)
        self._artifact = {k: np.asarray(v, dtype=float)
                          for k, v in artifact.items()}
        self._rate = float(sample_rate_hz)

    def acquire(self, capability: Capability, *, n_samples: int, seed: int,
                sample_rate_hz: float | None = None) -> Acquisition:
        if capability not in self._artifact:
            raise InstrumentError(
                f"{self.record.instrument_id} has no recorded artifact for "
                f"{capability.value}")
        recorded = self._artifact[capability]
        n = int(n_samples)
        if n > recorded.size:
            raise InstrumentError(
                f"{self.record.instrument_id}: the recorded artifact for "
                f"{capability.value} has {recorded.size} samples; cannot "
                f"replay {n}")
        return Acquisition(
            instrument_id=self.record.instrument_id,
            mode=self.record.mode,
            capability=capability,
            samples=recorded[:n].copy(),
            sample_rate_hz=self._rate,
            seed=int(seed),
        )


class FaultInjectionDevice(Instrument):
    """Wraps a :class:`SyntheticDevice` and injects instrument faults.

    Deterministic under the acquisition seed: the fault selection stream is
    derived from the same seed, so the same seed reproduces the same faulty
    reading. Every :class:`FaultMode` is injectable, and the applied faults
    are carried on the :class:`Acquisition`.
    """

    def __init__(self, record: InstrumentRecord, inner: SyntheticDevice,
                 faults: tuple, config: dict | None = None) -> None:
        if record.mode is not InstrumentMode.FAULT_INJECTION_DEVICE:
            raise InstrumentError(
                "FaultInjectionDevice needs a FAULT_INJECTION_DEVICE record")
        super().__init__(record)
        faults = tuple(faults)
        if not faults:
            raise InstrumentError(
                "a fault-injection device with no faults injects nothing; "
                "supply at least one FaultMode")
        for f in faults:
            if not isinstance(f, FaultMode):
                raise InstrumentError(f"{f!r} is not a FaultMode")
        self.inner = inner
        self.faults = faults
        self.config = dict(config or {})

    def acquire(self, capability: Capability, *, n_samples: int, seed: int,
                sample_rate_hz: float | None = None) -> Acquisition:
        clean = self.inner.acquire(capability, n_samples=n_samples, seed=seed,
                                   sample_rate_hz=sample_rate_hz)
        samples = np.asarray(clean.samples, dtype=float).copy()
        for f in self.faults:
            # a per-fault deterministic stream derived from the seed
            rng = np.random.default_rng(
                np.random.SeedSequence([int(seed), _FAULT_TAG[f]]))
            samples = _apply_fault(f, samples, self.config, rng)
        return Acquisition(
            instrument_id=self.record.instrument_id,
            mode=self.record.mode,
            capability=capability,
            samples=samples,
            sample_rate_hz=clean.sample_rate_hz,
            seed=int(seed),
            faults=self.faults,
        )


# --- the fault injection kernels -----------------------------------------

#: A stable integer tag per fault so its rng stream is distinct yet
#: reproducible under the acquisition seed.
_FAULT_TAG: dict[FaultMode, int] = {
    FaultMode.CLIPPING: 0x0C,
    FaultMode.DRIFT: 0x0D,
    FaultMode.SATURATION: 0x05,
    FaultMode.PACKET_LOSS: 0x0B,
    FaultMode.MISSING_SAMPLES: 0x0A,
}


def _apply_fault(fault: FaultMode, samples: np.ndarray, config: dict,
                 rng: np.random.Generator) -> np.ndarray:
    """Apply one fault to a copy of ``samples``, deterministically.

    Each fault demonstrably alters the array relative to the clean
    synthetic reading, and each is a distinct, recognised instrument
    pathology.
    """
    x = np.asarray(samples, dtype=float).copy()
    n = x.size
    if n == 0:
        return x
    peak = float(np.max(np.abs(x)))
    scale = peak if peak > 0.0 else 1.0

    if fault is FaultMode.CLIPPING:
        # symmetric soft clip of the extremes at a fraction of the peak
        level = float(config.get("clip_fraction", 0.7)) * scale
        return np.clip(x, -level, level)

    if fault is FaultMode.DRIFT:
        # a slow linear baseline drift added across the record
        slope = float(config.get("drift_fraction", 0.5)) * scale
        return x + np.linspace(0.0, slope, n)

    if fault is FaultMode.SATURATION:
        # a hard rail: samples beyond the rail flatten onto it
        rail = float(config.get("saturation_fraction", 0.4)) * scale
        return np.clip(x, -rail, rail)

    if fault is FaultMode.PACKET_LOSS:
        # one contiguous "packet" is lost and zero-filled
        frac = float(config.get("packet_fraction", 0.1))
        length = max(1, int(round(frac * n)))
        start = int(rng.integers(0, max(1, n - length + 1)))
        x[start:start + length] = 0.0
        return x

    if fault is FaultMode.MISSING_SAMPLES:
        # scattered individual samples go missing (NaN)
        frac = float(config.get("missing_fraction", 0.05))
        k = max(1, int(round(frac * n)))
        idx = rng.choice(n, size=min(k, n), replace=False)
        x[idx] = np.nan
        return x

    raise InstrumentError(f"unknown fault {fault!r}")  # pragma: no cover


# --- the registry ---------------------------------------------------------

class InstrumentRegistry:
    """Register, look up, and quarantine instruments; refuse before acquiring.

    The registry is the single gate onto acquisition. It refuses a
    quarantined instrument, an unsupported capability, and an expired or
    missing calibration -- all *before* any samples are produced -- and
    only then delegates to the instrument's mode.
    """

    def __init__(self) -> None:
        self._instruments: dict[str, Instrument] = {}
        self._calibrations: dict[str, Calibration] = {}

    # -- calibration store --
    def register_calibration(self, cal: Calibration) -> None:
        if cal.calibration_id in self._calibrations:
            raise InstrumentError(
                f"calibration {cal.calibration_id} already registered")
        self._calibrations[cal.calibration_id] = cal

    def calibration(self, calibration_id: str) -> Calibration:
        try:
            return self._calibrations[calibration_id]
        except KeyError:
            raise InstrumentError(
                f"calibration {calibration_id!r} is not registered") from None

    # -- instrument store --
    def register(self, instrument: Instrument) -> None:
        rec = instrument.record
        if rec.instrument_id in self._instruments:
            raise InstrumentError(
                f"instrument {rec.instrument_id} already registered")
        for cid in rec.calibration_ids:
            if cid not in self._calibrations:
                raise InstrumentError(
                    f"{rec.instrument_id} references calibration {cid!r} "
                    f"which is not registered; register the calibration "
                    f"before the instrument")
        self._instruments[rec.instrument_id] = instrument

    def lookup(self, instrument_id: str) -> Instrument:
        try:
            return self._instruments[instrument_id]
        except KeyError:
            raise InstrumentError(
                f"instrument {instrument_id!r} is not registered; the "
                f"registry holds {sorted(self._instruments)}") from None

    def ids(self) -> tuple:
        return tuple(sorted(self._instruments))

    def quarantine(self, instrument_id: str, reason: str) -> None:
        """Move an instrument to QUARANTINED; it is refused acquisition."""
        inst = self.lookup(instrument_id)
        rec = inst.record
        inst.record = InstrumentRecord(
            instrument_id=rec.instrument_id,
            instrument_type=rec.instrument_type,
            mode=rec.mode,
            firmware=rec.firmware,
            clock_source=rec.clock_source,
            capabilities=rec.capabilities,
            uncertainty_model={**rec.uncertainty_model,
                               "quarantine_reason": reason},
            calibration_ids=rec.calibration_ids,
            status=InstrumentStatus.QUARANTINED,
        )

    def is_quarantined(self, instrument_id: str) -> bool:
        return self.lookup(instrument_id).record.status is \
            InstrumentStatus.QUARANTINED

    # -- the refusal gate --
    def _require_valid_calibration(self, rec: InstrumentRecord,
                                   as_of: date) -> None:
        if not rec.calibration_ids:
            raise InstrumentError(
                f"refused: {rec.instrument_id} has no calibration; an "
                f"uncalibrated instrument cannot acquire an evidence-grade "
                f"reading")
        for cid in rec.calibration_ids:
            cal = self.calibration(cid)
            if not cal.is_valid_at(as_of):
                raise InstrumentError(
                    f"refused: {rec.instrument_id} calibration {cid} is not "
                    f"valid as of {as_of.isoformat()} (valid "
                    f"{cal.valid_from.isoformat()}..{cal.valid_until.isoformat()}"
                    f"); acquisition is refused before any sample is taken")

    def acquire(self, instrument_id: str, capability: Capability, *,
                as_of: date, n_samples: int = 1024, seed: int = 0,
                sample_rate_hz: float | None = None) -> Acquisition:
        """Acquire through the registry gate, or refuse.

        Refuses -- before producing any sample -- a quarantined instrument,
        an unsupported capability, and an expired or missing calibration.
        A REAL_DEVICE that passes the gate still acquires nothing: it
        raises :class:`NoHardwareError`.
        """
        inst = self.lookup(instrument_id)
        rec = inst.record
        if rec.status is InstrumentStatus.QUARANTINED:
            raise InstrumentError(
                f"refused: {instrument_id} is QUARANTINED and cannot "
                f"acquire")
        if not rec.supports(capability):
            raise InstrumentError(
                f"refused: {instrument_id} does not have capability "
                f"{capability.value}; it carries "
                f"{sorted(c.value for c in rec.capabilities)}. An "
                f"instrument used outside its capability set returns an "
                f"artifact, not a measurement")
        self._require_valid_calibration(rec, as_of)
        return inst.acquire(capability, n_samples=n_samples, seed=seed,
                            sample_rate_hz=sample_rate_hz)

    def inventory(self) -> list:
        return [inst.record.as_dict()
                for _id, inst in sorted(self._instruments.items())]


# --- the load-bearing refusal --------------------------------------------

def refuse_reading_as_measurement(
        claim: str = "an instrument reading is a physical measurement"
) -> None:
    """Refuse any reading here read as a physical measurement. Always raises.

    Every reading this module produces is a ``SYNTHETIC_OBSERVATION`` from a
    seeded simulator or a recorded synthetic artifact, and a REAL_DEVICE
    acquires nothing. Delegates to the governance core so the refusal text
    is the canonical one.
    """
    raise InstrumentError(
        f"refused: {claim!r}. No instrument in this registry produced a "
        f"physical measurement: synthetic and replay readings are "
        f"SYNTHETIC_OBSERVATIONs and a REAL_DEVICE acquires nothing. "
        f"{PHYSICAL_VALIDATION}. {VERDICT} "
        f"[{claims.MAX_SOFTWARE_CLASS.value} is the software ceiling]")


# --- report ---------------------------------------------------------------

def instruments_report() -> dict:
    """The standing statement of what the registry is and is not."""
    return {
        "what_this_is": (
            "the R15 instrument registry: a typed InstrumentRecord per "
            "instrument and one acquisition interface behind four distinct "
            "modes -- REAL_DEVICE (interface only, acquires nothing), "
            "SYNTHETIC_DEVICE (deterministic under a seed), REPLAY_DEVICE "
            "(replays a recorded artifact), and FAULT_INJECTION_DEVICE "
            "(injects clipping, drift, saturation, packet loss and missing "
            "samples) -- with a registry that refuses a quarantined "
            "instrument, an unsupported capability, and an expired "
            "calibration before any sample is taken"),
        "modes": [m.value for m in InstrumentMode],
        "statuses": [s.value for s in InstrumentStatus],
        "capabilities": [c.value for c in Capability],
        "fault_modes": [f.value for f in FaultMode],
        "refusals": [
            "REAL_DEVICE.acquire raises NoHardwareError (acquires nothing)",
            "an unsupported capability is refused before acquisition",
            "an expired or missing calibration is refused before acquisition",
            "a quarantined instrument is refused acquisition",
            "refuse_reading_as_measurement (no reading is a measurement)",
        ],
        "reading_claim_class": READING_CLAIM_CLASS.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "hardware_status": (
            "no physical instrument exists here; a REAL_DEVICE read is "
            "BLOCKED and acquires nothing"),
        "what_would_change_this": (
            "a physical instrument on a calibrated bench, its raw artifact "
            "captured with an uncertainty budget, a clock binding and an "
            "environment log -- none of which exists in this repository"),
        "what_this_does_not_say": (
            "It does not say any instrument measured anything. Synthetic "
            "and replay readings are SYNTHETIC_OBSERVATIONs produced by a "
            "seeded simulator or a recorded synthetic artifact; a "
            "REAL_DEVICE acquires nothing and its read is BLOCKED. A "
            "synthetic observation is never a PHYSICAL_MEASUREMENT. "
            "PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION",
    "READING_CLAIM_CLASS", "SOFTWARE_CLAIM_CLASS",
    "InstrumentError", "NoHardwareError",
    "InstrumentMode", "InstrumentStatus", "Capability", "FaultMode",
    "Calibration", "InstrumentRecord", "Acquisition", "SyntheticDriver",
    "Instrument", "RealDevice", "SyntheticDevice", "ReplayDevice",
    "FaultInjectionDevice", "InstrumentRegistry",
    "refuse_reading_as_measurement", "instruments_report",
]
