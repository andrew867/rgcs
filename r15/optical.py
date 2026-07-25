"""P15 — the optical measurement lane: photodiode, interferometric,
speckle and photoelastic readout of surface displacement or wave
propagation, behind one interface with four honest device modes.

R15 needs an optical acquisition lane that is honest about what optics can
and cannot recover, and about the fact that no bench exists here. This
module is that lane. It carries a typed :class:`OpticalConfig` -- the
wavelength, bandwidth, power, polarization, geometry and thermal load every
optical result must be bound to -- and it exposes one acquisition interface
behind which sit four distinct device modes.

**The four modes are not interchangeable.**

* ``REAL_DEVICE`` is an interface only. No optical bench, laser, detector
  or specimen exists in this repository, so a real acquisition acquires
  *nothing*: it raises :class:`NoOpticalHardwareError` and returns a
  ``BLOCKED`` receipt. The physical run is ``PREREGISTERED_NOT_RUN``.
* ``SYNTHETIC_DEVICE`` produces a deterministic optical signal from a
  seeded generator with a *planted* displacement or fringe phase, and the
  pipeline recovers it. That recovery is the POWER control: a lane that
  could not recover a known planted displacement would be worthless. Its
  output is a ``SYNTHETIC_OBSERVATION`` -- never a physical measurement.
* ``REPLAY_DEVICE`` replays a previously recorded (synthetic) trace
  byte-for-byte; it measures nothing new.
* ``FAULT_INJECTION_DEVICE`` injects the ordinary instrument pathologies
  (clipping, drift, saturation, packet loss, missing samples) plus the two
  optical-specific ones -- interferometric fringe wash-out and speckle
  decorrelation -- so the error budget can be exercised against them.

**Intensity-only is separated from phase-sensitive.** A photodiode reads
optical power and is phase-blind: a pure displacement (a phase shift) does
not change the power it reads, so displacement cannot be recovered from it
(:func:`refuse_intensity_as_phase`). An interferometer scans a reference
phase and reads the fringe; the displacement lives in the fringe phase and
is recovered by projecting the carrier tone (reusing
:func:`r13.heterodyne.tone_amplitude`).

**Dark, flat, reference and drift corrections are traceable.** Each
correction returns both the corrected trace and a record of exactly what
was removed, so the correction chain is auditable end to end.

Nothing here is measured. Every trace is simulator output under
``numpy.random.default_rng(seed)``; a reconstruction of a synthetic fringe
or phantom is a ``SYNTHETIC_OBSERVATION``, never an image of a real source
(:func:`refuse_reconstruction_as_measured`, delegating to
:mod:`r13.imaging`). The strongest class this lane reaches is a synthetic
observation, and a synthetic observation is not a ``PHYSICAL_MEASUREMENT``.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, field
from datetime import date
from enum import Enum

import numpy as np

from r15 import claims
from r13 import heterodyne, imaging, sixangle

# --- verdict and standing claim vocabulary --------------------------------

#: The standing verdict for this module.
VERDICT = "OPTICAL_MEASUREMENT_LANE_SYNTHETIC_NO_HARDWARE"

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The analysis version stamped on every observation record.
ANALYSIS_VERSION = "r15.optical/1.0"

#: The ceiling any reading this lane produces may carry. A synthetic or
#: replayed reading is a SYNTHETIC_OBSERVATION; it is never a measurement.
READING_CLAIM_CLASS = claims.ClaimClass.SYNTHETIC_OBSERVATION
#: The class of the lane machinery itself.
SOFTWARE_CLAIM_CLASS = claims.ClaimClass.SOFTWARE_IMPLEMENTED


class OpticalError(RuntimeError):
    """Raised on any optical-lane refusal or malformed input.

    Covers the structural guards (a malformed config, an empty trace, a
    negative wavelength) and the load-bearing refusals. Base of
    :class:`NoOpticalHardwareError`.
    """


class NoOpticalHardwareError(OpticalError):
    """Raised when a REAL_DEVICE optical acquisition is attempted.

    No optical bench exists in this repository, so a real acquisition
    acquires nothing. This is the hardware-access boundary: the read is
    BLOCKED, not faked.
    """


# --- the four modes, the readout kinds, and the fault vocabulary ----------

class OpticalMode(Enum):
    """The four acquisition modes behind the one optical interface."""

    REAL_DEVICE = "REAL_DEVICE"
    REPLAY_DEVICE = "REPLAY_DEVICE"
    SYNTHETIC_DEVICE = "SYNTHETIC_DEVICE"
    FAULT_INJECTION_DEVICE = "FAULT_INJECTION_DEVICE"


class ReadoutKind(Enum):
    """How the optical lane transduces the field.

    ``PHOTODIODE`` reads optical power (intensity-only, phase-blind).
    ``INTERFEROMETRIC`` reads a fringe whose phase carries displacement
    (phase-sensitive). ``SPECKLE`` reads a speckle intensity field whose
    correlation decays with surface motion. ``PHOTOELASTIC`` reads the
    crossed-polarizer intensity of a stress-induced retardation
    (polarization, phase-sensitive).
    """

    PHOTODIODE = "photodiode"
    INTERFEROMETRIC = "interferometric"
    SPECKLE = "speckle"
    PHOTOELASTIC = "photoelastic"


#: The readout kinds that recover a phase (and hence a displacement or
#: retardation). A photodiode is intensity-only and is excluded.
PHASE_SENSITIVE_READOUTS = frozenset({
    ReadoutKind.INTERFEROMETRIC,
    ReadoutKind.PHOTOELASTIC,
})
#: The intensity-only readouts: power, no phase.
INTENSITY_ONLY_READOUTS = frozenset({ReadoutKind.PHOTODIODE})


class OpticalFault(Enum):
    """The pathologies an optical fault-injection device can inject.

    The first five are the generic instrument faults shared with every
    R15 lane; the last two are optical-specific: an interferometric fringe
    washing out (visibility collapsing to zero) and a speckle field
    decorrelating.
    """

    CLIPPING = "clipping"
    DRIFT = "drift"
    SATURATION = "saturation"
    PACKET_LOSS = "packet_loss"
    MISSING_SAMPLES = "missing_samples"
    FRINGE_WASHOUT = "fringe_washout"
    SPECKLE_DECORRELATION = "speckle_decorrelation"


#: The optical-specific fault modes, distinct from the generic ones.
OPTICAL_SPECIFIC_FAULTS = frozenset({
    OpticalFault.FRINGE_WASHOUT,
    OpticalFault.SPECKLE_DECORRELATION,
})


# --- the optical configuration every result is bound to -------------------

@dataclass(frozen=True)
class OpticalConfig:
    """Wavelength, bandwidth, power, polarization, geometry, thermal load.

    Every optical result is bound to one of these, plus a calibration id.
    ``geometry_passes`` is 2 for a retro-reflection double pass (so a
    surface displacement ``d`` produces an optical phase ``4*pi*d/lambda``)
    and 1 for a single pass. ``visibility`` is the interferometric fringe
    contrast in ``[0, 1]``.
    """

    wavelength_nm: float = 632.8
    bandwidth_nm: float = 0.01
    power_w: float = 1.0e-3
    polarization_deg: float = 0.0
    incidence_deg: float = 0.0
    standoff_m: float = 0.10
    geometry_passes: int = 2
    thermal_load_c: float = 25.0
    visibility: float = 0.9
    calibration_id: str = "opt_cal_synthetic"

    def __post_init__(self) -> None:
        if self.wavelength_nm <= 0.0:
            raise OpticalError("wavelength must be positive")
        if self.bandwidth_nm < 0.0:
            raise OpticalError("bandwidth cannot be negative")
        if self.power_w <= 0.0:
            raise OpticalError("optical power must be positive")
        if self.geometry_passes not in (1, 2):
            raise OpticalError("geometry_passes must be 1 (single) or 2 (double)")
        if not (0.0 <= self.visibility <= 1.0):
            raise OpticalError("visibility must lie in [0, 1]")

    @property
    def wavelength_m(self) -> float:
        return self.wavelength_nm * 1.0e-9

    @property
    def phase_per_metre(self) -> float:
        """Optical phase (rad) produced per metre of surface displacement.

        ``2*pi/lambda`` per pass; the double-pass geometry doubles it. This
        is the constant that converts a recovered fringe phase back into a
        displacement.
        """
        return self.geometry_passes * 2.0 * math.pi / self.wavelength_m

    def unambiguous_displacement_m(self) -> float:
        """Largest displacement whose phase stays within +/- pi (unwrapped)."""
        return math.pi / self.phase_per_metre

    def as_dict(self) -> dict:
        return {
            "wavelength_nm": self.wavelength_nm,
            "bandwidth_nm": self.bandwidth_nm,
            "power_w": self.power_w,
            "polarization_deg": self.polarization_deg,
            "incidence_deg": self.incidence_deg,
            "standoff_m": self.standoff_m,
            "geometry_passes": self.geometry_passes,
            "thermal_load_c": self.thermal_load_c,
            "visibility": self.visibility,
            "calibration_id": self.calibration_id,
        }


# --- traceable corrections: dark, flat, reference, drift ------------------

@dataclass(frozen=True)
class Correction:
    """A single applied correction and exactly what it removed.

    ``kind`` names the correction; ``removed`` is a scalar summary of what
    was taken out (a dark offset, a flat gain, a reference level, a drift
    slope). Keeping the removed quantity makes the correction chain
    auditable: a corrected trace can always be traced back to the raw one.
    """

    kind: str
    removed: float

    def as_dict(self) -> dict:
        return {"kind": self.kind, "removed": float(self.removed)}


def dark_correct(trace, dark_level: float) -> tuple[np.ndarray, Correction]:
    """Subtract a dark-frame offset; record the level removed."""
    x = np.asarray(trace, dtype=float)
    return x - float(dark_level), Correction("dark", float(dark_level))


def flat_correct(trace, flat_gain: float) -> tuple[np.ndarray, Correction]:
    """Divide out a flat-field gain; record the gain removed."""
    g = float(flat_gain)
    if g == 0.0:
        raise OpticalError("flat-field gain cannot be zero")
    x = np.asarray(trace, dtype=float)
    return x / g, Correction("flat", g)


def reference_correct(trace, reference) -> tuple[np.ndarray, Correction]:
    """Subtract a reference-arm baseline (scalar or trace); record its mean."""
    x = np.asarray(trace, dtype=float)
    ref = np.asarray(reference, dtype=float)
    if ref.ndim and ref.shape != x.shape:
        raise OpticalError("reference trace must match the signal shape")
    return x - ref, Correction("reference", float(np.mean(ref)))


def drift_correct(trace) -> tuple[np.ndarray, Correction]:
    """Remove a slow linear baseline drift; record the fitted slope.

    Fits a straight line across the record and subtracts it, so a
    fault-injected linear drift is removed and the recorded slope traces
    exactly how much was taken out.
    """
    x = np.asarray(trace, dtype=float)
    n = x.size
    if n < 2:
        return x.copy(), Correction("drift", 0.0)
    idx = np.arange(n, dtype=float)
    slope, intercept = np.polyfit(idx, x, 1)
    return x - (slope * idx + intercept), Correction("drift", float(slope))


# --- the synthetic optical signal generators -----------------------------

def _carrier(n: int, n_cycles: int) -> tuple[np.ndarray, np.ndarray, float]:
    """A reference-phase carrier with an integer number of cycles.

    Returns the sample-index time base ``t = 0..n-1``, the carrier phase
    ``psi = 2*pi*n_cycles*t/n`` and the carrier angular frequency ``w``.
    An integer cycle count makes the counter-rotating term of the tone
    projection vanish exactly, so the recovered phase is exact up to noise.
    """
    if n < 4:
        raise OpticalError("need at least 4 samples to carry a fringe")
    if n_cycles < 1 or n_cycles > n // 2:
        raise OpticalError("carrier cycles must lie in [1, n/2]")
    t = np.arange(n, dtype=float)
    w = 2.0 * math.pi * n_cycles / n
    return t, w * t, w


def synthetic_interferogram(config: OpticalConfig, displacement_m: float, *,
                            n: int = 4096, n_cycles: int = 37, seed: int = 0,
                            noise: float = 1.0e-3) -> np.ndarray:
    """A phase-sensitive interferometric fringe with a planted displacement.

    The detected intensity is ``I0*(1 + V*cos(psi + phi))`` where ``psi``
    is the scanned reference-phase carrier and ``phi =
    phase_per_metre * displacement`` is the planted fringe phase. The
    displacement is recovered by :func:`recover_displacement`. Deterministic
    under ``seed``.
    """
    _, psi, _ = _carrier(int(n), int(n_cycles))
    phi = config.phase_per_metre * float(displacement_m)
    i0 = config.power_w
    rng = np.random.default_rng(int(seed))
    fringe = i0 * (1.0 + config.visibility * np.cos(psi + phi))
    return fringe + float(noise) * i0 * rng.standard_normal(int(n))


def recover_displacement(trace, config: OpticalConfig, *,
                         n_cycles: int = 37) -> float:
    """Recover the planted displacement from an interferometric fringe.

    Removes the DC term and projects the carrier tone (reusing
    :func:`r13.heterodyne.tone_amplitude`); the tone phase is the fringe
    phase, which divides by ``phase_per_metre`` to give the displacement.
    This is the POWER control for the phase-sensitive readout.
    """
    x = np.asarray(trace, dtype=float)
    n = x.size
    t, _, w = _carrier(n, int(n_cycles))
    amp = heterodyne.tone_amplitude(x - x.mean(), t, w)
    phi = float(np.angle(amp))
    return phi / config.phase_per_metre


def synthetic_photodiode(config: OpticalConfig, *, displacement_m: float = 0.0,
                         n: int = 4096, seed: int = 0,
                         noise: float = 1.0e-3) -> np.ndarray:
    """An intensity-only photodiode trace: optical power, phase-blind.

    The trace is the incident optical power plus shot-like noise. The
    ``displacement_m`` argument is accepted but deliberately has NO effect:
    a photodiode reads power, and a pure displacement is a phase shift that
    leaves the power unchanged. That is the whole point of separating
    intensity-only from phase-sensitive readout.
    """
    rng = np.random.default_rng(int(seed))
    base = config.power_w * np.ones(int(n), dtype=float)
    return base + float(noise) * config.power_w * rng.standard_normal(int(n))


def recover_power_w(trace) -> float:
    """Recover the mean optical power from a photodiode trace."""
    return float(np.mean(np.asarray(trace, dtype=float)))


def synthetic_speckle_field(size: int = 64, *, seed: int = 0) -> np.ndarray:
    """A fully-developed synthetic speckle intensity field.

    A sum of random phasors gives a circular complex Gaussian field; its
    squared modulus is a speckle intensity with negative-exponential
    statistics. Deterministic under ``seed``.
    """
    if size < 4:
        raise OpticalError("speckle field must be at least 4x4")
    rng = np.random.default_rng(int(seed))
    real = rng.standard_normal((size, size))
    imag = rng.standard_normal((size, size))
    field_c = real + 1j * imag
    return np.abs(field_c) ** 2


def speckle_correlation(a, b) -> float:
    """Zero-lag normalised correlation of two speckle intensity fields.

    1.0 for identical fields, falling toward 0 as the fields decorrelate.
    This is how surface displacement is sensed by speckle: the field
    decorrelates as the surface moves, and the correlation drops.
    """
    x = np.asarray(a, dtype=float).ravel()
    y = np.asarray(b, dtype=float).ravel()
    if x.size != y.size:
        raise OpticalError("speckle fields must have the same size")
    x = x - x.mean()
    y = y - y.mean()
    denom = math.sqrt(float((x * x).sum()) * float((y * y).sum()))
    if denom == 0.0:
        raise OpticalError("degenerate speckle field; correlation undefined")
    return float((x * y).sum()) / denom


def decorrelate_speckle(field, frac: float, *, seed: int = 0) -> np.ndarray:
    """Partially decorrelate a speckle field by mixing in a fresh one.

    ``frac`` in ``[0, 1]`` is how much independent speckle is mixed in:
    0 returns the field unchanged, 1 returns a fully independent field. The
    correlation with the original falls monotonically as ``frac`` rises,
    modelling surface motion (and the SPECKLE_DECORRELATION fault).
    """
    f = np.asarray(field, dtype=float)
    frac = float(frac)
    if not (0.0 <= frac <= 1.0):
        raise OpticalError("decorrelation fraction must lie in [0, 1]")
    fresh = synthetic_speckle_field(f.shape[0], seed=seed)
    return math.sqrt(1.0 - frac) * f + math.sqrt(frac) * fresh


def synthetic_photoelastic(config: OpticalConfig, retardation_rad: float, *,
                           n: int = 2048, seed: int = 0,
                           noise: float = 1.0e-3) -> np.ndarray:
    """A crossed-polarizer photoelastic trace with a planted retardation.

    A stress-induced birefringence produces a retardation ``delta`` between
    the polarization components; between crossed polarizers the transmitted
    intensity is ``I0*sin^2(delta/2)``. The retardation is recovered by
    :func:`recover_retardation`. Deterministic under ``seed``.
    """
    delta = float(retardation_rad)
    if not (0.0 <= delta <= math.pi):
        raise OpticalError("retardation must lie in [0, pi] to be unambiguous")
    rng = np.random.default_rng(int(seed))
    i0 = config.power_w
    level = i0 * math.sin(delta / 2.0) ** 2
    return level * np.ones(int(n), dtype=float) \
        + float(noise) * i0 * rng.standard_normal(int(n))


def recover_retardation(trace, config: OpticalConfig) -> float:
    """Recover the planted retardation from a photoelastic trace.

    Inverts ``I = I0*sin^2(delta/2)`` on the mean intensity, giving
    ``delta = 2*arcsin(sqrt(I/I0))`` in ``[0, pi]``. POWER control for the
    polarization (photoelastic) readout.
    """
    mean = float(np.mean(np.asarray(trace, dtype=float)))
    ratio = min(1.0, max(0.0, mean / config.power_w))
    return 2.0 * math.asin(math.sqrt(ratio))


def polarization_rosette(config: OpticalConfig, retardation_rad: float, *,
                         n_analyzer: int = 6) -> np.ndarray:
    """Malus-law intensity at ``n_analyzer`` polarizer angles around a ring.

    Reuses :class:`r13.sixangle.AngleRing` to sample the analyzer sweep at
    equally spaced angles; the pattern is a synthetic angular rosette of the
    photoelastic response, never a measured polarimeter reading.
    """
    ring = sixangle.AngleRing(n=int(n_analyzer))
    i0 = config.power_w
    delta = float(retardation_rad)

    def pattern(theta: float) -> float:
        return i0 * (math.sin(theta) ** 2) * (math.sin(delta / 2.0) ** 2)

    return ring.sample_pattern(pattern)


# --- fringe / phantom reconstruction (a SYNTHETIC observation) -----------

def reconstruct_fringe_phantom(size: int = 48, *,
                               n_angles: int = 90) -> dict:
    """Reconstruct a synthetic optical phantom and score the round trip.

    Reuses :mod:`r13.imaging`: a synthetic phantom is forward-projected and
    reconstructed by filtered back-projection. The full-angle round trip
    recovers the phantom (low error) -- a correctness check on the transform
    pair, and a SYNTHETIC_OBSERVATION. It is NOT an image of any real
    source; :func:`refuse_reconstruction_as_measured` blocks that promotion.
    """
    phantom = imaging.two_disk_phantom(int(size))
    angles = np.linspace(0.0, 180.0, int(n_angles), endpoint=False)
    recon = imaging.reconstruct(imaging.forward_project(phantom, angles),
                                angles, image_size=int(size))
    return {
        "size": int(size),
        "n_angles": int(n_angles),
        "reconstruction_error": imaging.reconstruction_error(recon, phantom),
        "claim_class": READING_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "note": ("a filtered back-projection of a synthetic phantom; a "
                 "SYNTHETIC_OBSERVATION, not an image of a real source"),
    }


# --- the acquisition result ----------------------------------------------

@dataclass(frozen=True)
class OpticalObservation:
    """A single optical reading behind the interface.

    Bound to its :class:`OpticalConfig` (hence to geometry and calibration)
    and stamped with the recovered quantity, its value, units and an
    uncertainty object. ``claim_class`` is capped at
    ``SYNTHETIC_OBSERVATION`` and can never be a measurement class.
    """

    observation_id: str
    run_id: str
    mode: OpticalMode
    readout: ReadoutKind
    config: OpticalConfig
    quantity: str
    value: float
    units: str
    uncertainty: dict
    samples: np.ndarray
    seed: int
    faults: tuple = ()
    claim_class: claims.ClaimClass = READING_CLAIM_CLASS

    def __post_init__(self) -> None:
        if self.claim_class in claims.MEASUREMENT_CLASSES:
            # the load-bearing refusal, wired to the governance core
            claims.refuse_synthetic_as_physical()

    def digest(self) -> str:
        arr = np.ascontiguousarray(self.samples, dtype=float)
        return hashlib.sha256(arr.tobytes()).hexdigest()

    def bindings(self) -> claims.EvidenceBindings:
        """The evidence bindings this synthetic observation carries.

        A synthetic observation binds an instrument, protocol, clock,
        environment, uncertainty and a (synthetic) calibration, but there is
        no real specimen, fixture or raw physical artifact, so the evidence
        is capped below a physical measurement.
        """
        return claims.EvidenceBindings(
            instrument=True, calibration=True, specimen=False, fixture=False,
            protocol=True, clock=True, environment=True, raw_artifact=False,
            uncertainty=True)

    def evidence_level(self) -> claims.EvidenceLevel:
        return claims.evidence_cap(self.bindings(), claims.EvidenceLevel.E4)

    def as_observation_record(self) -> dict:
        """Canonical record conforming to observation_record.schema.json."""
        return {
            "observation_id": self.observation_id,
            "run_id": self.run_id,
            "source_artifacts": [f"synthetic:{self.digest()}"],
            "analysis_version": ANALYSIS_VERSION,
            "quantity": self.quantity,
            "value": float(self.value),
            "units": self.units,
            "uncertainty": dict(self.uncertainty),
            "claim_class": self.claim_class.value,
            "derivation_graph": [
                {"step": "synthetic_generation", "mode": self.mode.value},
                {"step": "readout", "kind": self.readout.value},
                {"step": "recovery", "quantity": self.quantity},
            ],
            "mode": self.mode.value,
            "readout": self.readout.value,
            "config": self.config.as_dict(),
            "faults": [f.value for f in self.faults],
            "evidence_level": self.evidence_level().name,
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


# --- the optical error budget --------------------------------------------

#: The uncertainty components an optical displacement budget decomposes
#: into, per the R15 error-budget policy plus the optical-specific terms
#: (wavelength, bandwidth, power, polarization). Values are relative
#: fractions of the measurand; thermal load is kept as its own component,
#: separate from the general environment term.
_DEFAULT_BUDGET_COMPONENTS: tuple[tuple[str, float], ...] = (
    ("instrument_resolution", 1.0e-3),
    ("calibration", 2.0e-3),
    ("wavelength", 5.0e-5),
    ("bandwidth", 3.0e-4),
    ("optical_power", 4.0e-4),
    ("polarization", 3.0e-4),
    ("clock", 1.0e-4),
    ("environment", 8.0e-4),
    ("thermal_load", 1.2e-3),
    ("fixture_repeatability", 9.0e-4),
    ("specimen_geometry", 7.0e-4),
    ("orientation", 6.0e-4),
    ("numerical_method", 2.0e-4),
    ("dsp", 3.0e-4),
    ("operator_action", 5.0e-4),
    ("model_residual", 4.0e-4),
)


def build_error_budget(config: OpticalConfig, *,
                       quantity: str = "surface_displacement",
                       coverage_factor: float = 2.0,
                       budget_id: str = "opt_budget",
                       components: tuple | None = None) -> dict:
    """Build a full optical error budget conforming to the schema.

    Components (relative) are combined in quadrature (root-sum-square); the
    combined uncertainty is scaled by the ``coverage_factor``. Thermal load
    is a distinct component from the general environment term, as the policy
    requires. Conforms to ``error_budget.schema.json``.
    """
    comps = tuple(components) if components is not None \
        else _DEFAULT_BUDGET_COMPONENTS
    if not comps:
        raise OpticalError("an error budget needs at least one component")
    rss = math.sqrt(sum(float(v) ** 2 for _n, v in comps))
    return {
        "budget_id": budget_id,
        "quantity": quantity,
        "components": [
            {"name": n, "relative_standard_uncertainty": float(v),
             "distribution": "normal"}
            for n, v in comps
        ],
        "combination_method": "root_sum_square",
        "combined_uncertainty": float(rss),
        "coverage_factor": float(coverage_factor),
        "expanded_uncertainty": float(rss * coverage_factor),
        "wavelength_nm": config.wavelength_nm,
        "thermal_load_c": config.thermal_load_c,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
    }


# --- the one interface, four modes ---------------------------------------

class OpticalDevice:
    """Base of the one optical acquisition interface. Not used directly."""

    def __init__(self, config: OpticalConfig, mode: OpticalMode) -> None:
        self.config = config
        self.mode = mode

    def acquire(self, readout: ReadoutKind, *, run_id: str, seed: int,
                displacement_m: float = 0.0,
                retardation_rad: float = 0.0) -> OpticalObservation:
        raise NotImplementedError


class OpticalRealDevice(OpticalDevice):
    """A real optical bench interface with no hardware behind it.

    Acquisition acquires nothing: it raises :class:`NoOpticalHardwareError`.
    :meth:`blocked_receipt` records the honest BLOCKED / preregistered state.
    """

    def __init__(self, config: OpticalConfig) -> None:
        super().__init__(config, OpticalMode.REAL_DEVICE)

    def acquire(self, readout: ReadoutKind, *, run_id: str, seed: int,
                displacement_m: float = 0.0,
                retardation_rad: float = 0.0) -> OpticalObservation:
        raise NoOpticalHardwareError(
            f"refused: a REAL_DEVICE optical acquisition ({readout.value}) "
            f"acquires NOTHING -- no laser, interferometer, photodetector, "
            f"polarizer or specimen exists in this repository. The read is "
            f"BLOCKED at the hardware-access boundary, not faked with a "
            f"synthetic value. The physical run is PREREGISTERED_NOT_RUN. "
            f"{PHYSICAL_VALIDATION}. {VERDICT}")

    def blocked_receipt(self, readout: ReadoutKind) -> dict:
        """The honest BLOCKED / preregistered receipt for a real read."""
        return {
            "mode": self.mode.value,
            "readout": readout.value,
            "status": "BLOCKED",
            "physical_run": "PREREGISTERED_NOT_RUN",
            "reason": "no optical hardware present; acquires nothing",
            "acquired": False,
            "n_samples": 0,
            "claim_class": "BLOCKED_MISSING_INPUT",
            "measured_here": MEASURED_HERE,
            "physical_validation": PHYSICAL_VALIDATION,
        }


class OpticalSyntheticDevice(OpticalDevice):
    """A deterministic synthetic optical device with a planted signal.

    Same seed => identical trace; different seed => different trace. The
    reading is a ``SYNTHETIC_OBSERVATION`` and the planted displacement /
    retardation is recovered by the pipeline (the POWER control).
    """

    def __init__(self, config: OpticalConfig, *, n: int = 4096,
                 n_cycles: int = 37, noise: float = 1.0e-3) -> None:
        super().__init__(config, OpticalMode.SYNTHETIC_DEVICE)
        self.n = int(n)
        self.n_cycles = int(n_cycles)
        self.noise = float(noise)

    def _trace(self, readout: ReadoutKind, *, seed: int,
               displacement_m: float, retardation_rad: float) -> np.ndarray:
        if readout is ReadoutKind.INTERFEROMETRIC:
            return synthetic_interferogram(
                self.config, displacement_m, n=self.n, n_cycles=self.n_cycles,
                seed=seed, noise=self.noise)
        if readout is ReadoutKind.PHOTODIODE:
            return synthetic_photodiode(
                self.config, displacement_m=displacement_m, n=self.n,
                seed=seed, noise=self.noise)
        if readout is ReadoutKind.PHOTOELASTIC:
            return synthetic_photoelastic(
                self.config, retardation_rad, n=self.n, seed=seed,
                noise=self.noise)
        if readout is ReadoutKind.SPECKLE:
            size = max(8, int(round(math.sqrt(self.n))))
            return synthetic_speckle_field(size, seed=seed)
        raise OpticalError(f"unknown readout {readout!r}")  # pragma: no cover

    def _recover(self, readout: ReadoutKind, trace: np.ndarray, *,
                 displacement_m: float, retardation_rad: float) -> tuple:
        if readout is ReadoutKind.INTERFEROMETRIC:
            d = recover_displacement(trace, self.config,
                                     n_cycles=self.n_cycles)
            return "surface_displacement", d, "m"
        if readout is ReadoutKind.PHOTODIODE:
            return "optical_power", recover_power_w(trace), "W"
        if readout is ReadoutKind.PHOTOELASTIC:
            return ("retardation",
                    recover_retardation(trace, self.config), "rad")
        if readout is ReadoutKind.SPECKLE:
            # correlation of the field with itself is 1.0 by construction;
            # the readout quantity is the field's mean intensity contrast
            arr = np.asarray(trace, dtype=float)
            contrast = float(arr.std() / (arr.mean() + 1e-300))
            return "speckle_contrast", contrast, "dimensionless"
        raise OpticalError(f"unknown readout {readout!r}")  # pragma: no cover

    def acquire(self, readout: ReadoutKind, *, run_id: str, seed: int,
                displacement_m: float = 0.0,
                retardation_rad: float = 0.0) -> OpticalObservation:
        trace = self._trace(readout, seed=seed, displacement_m=displacement_m,
                            retardation_rad=retardation_rad)
        quantity, value, units = self._recover(
            readout, trace, displacement_m=displacement_m,
            retardation_rad=retardation_rad)
        budget = build_error_budget(self.config, quantity=quantity)
        uncertainty = {
            "combined_relative": budget["combined_uncertainty"],
            "coverage_factor": budget["coverage_factor"],
            "type": "root_sum_square_budget",
        }
        return OpticalObservation(
            observation_id=f"{run_id}:{readout.value}:{seed}",
            run_id=run_id, mode=self.mode, readout=readout, config=self.config,
            quantity=quantity, value=value, units=units,
            uncertainty=uncertainty, samples=np.asarray(trace, dtype=float),
            seed=int(seed))


class OpticalReplayDevice(OpticalDevice):
    """Replays a previously recorded (synthetic) optical trace byte-for-byte.

    It reads back what was stored and measures nothing new; the reading is a
    ``SYNTHETIC_OBSERVATION`` of a recorded artifact.
    """

    def __init__(self, config: OpticalConfig,
                 artifact: dict[ReadoutKind, np.ndarray]) -> None:
        super().__init__(config, OpticalMode.REPLAY_DEVICE)
        self._artifact = {k: np.asarray(v, dtype=float)
                          for k, v in artifact.items()}

    def acquire(self, readout: ReadoutKind, *, run_id: str, seed: int,
                displacement_m: float = 0.0,
                retardation_rad: float = 0.0) -> OpticalObservation:
        if readout not in self._artifact:
            raise OpticalError(
                f"no recorded artifact for {readout.value}; the replay store "
                f"holds {sorted(k.value for k in self._artifact)}")
        trace = self._artifact[readout].copy()
        if readout is ReadoutKind.INTERFEROMETRIC:
            quantity, value, units = "surface_displacement", \
                recover_displacement(trace, self.config), "m"
        elif readout is ReadoutKind.PHOTOELASTIC:
            quantity, value, units = "retardation", \
                recover_retardation(trace, self.config), "rad"
        else:
            quantity, value, units = "optical_power", \
                recover_power_w(trace), "W"
        budget = build_error_budget(self.config, quantity=quantity)
        return OpticalObservation(
            observation_id=f"{run_id}:replay:{readout.value}",
            run_id=run_id, mode=self.mode, readout=readout, config=self.config,
            quantity=quantity, value=value, units=units,
            uncertainty={"combined_relative": budget["combined_uncertainty"],
                         "coverage_factor": budget["coverage_factor"],
                         "type": "root_sum_square_budget"},
            samples=trace, seed=int(seed))


class OpticalFaultInjectionDevice(OpticalDevice):
    """Wraps a synthetic optical device and injects optical faults.

    Deterministic under the acquisition seed. Every :class:`OpticalFault`
    is injectable -- the five generic instrument faults and the two
    optical-specific ones (fringe wash-out, speckle decorrelation) -- and
    the applied faults are carried on the :class:`OpticalObservation`.
    """

    def __init__(self, inner: OpticalSyntheticDevice, faults: tuple,
                 config_overrides: dict | None = None) -> None:
        super().__init__(inner.config, OpticalMode.FAULT_INJECTION_DEVICE)
        faults = tuple(faults)
        if not faults:
            raise OpticalError(
                "a fault-injection device with no faults injects nothing; "
                "supply at least one OpticalFault")
        for f in faults:
            if not isinstance(f, OpticalFault):
                raise OpticalError(f"{f!r} is not an OpticalFault")
        self.inner = inner
        self.faults = faults
        self.cfg = dict(config_overrides or {})

    def acquire(self, readout: ReadoutKind, *, run_id: str, seed: int,
                displacement_m: float = 0.0,
                retardation_rad: float = 0.0) -> OpticalObservation:
        clean = self.inner.acquire(
            readout, run_id=run_id, seed=seed, displacement_m=displacement_m,
            retardation_rad=retardation_rad)
        samples = np.asarray(clean.samples, dtype=float).copy()
        for f in self.faults:
            rng = np.random.default_rng(
                np.random.SeedSequence([int(seed), _FAULT_TAG[f]]))
            samples = _apply_optical_fault(f, samples, self.cfg, rng,
                                           self.config)
        # re-recover from the faulted trace so the value reflects the damage
        quantity = clean.quantity
        units = clean.units
        if readout is ReadoutKind.INTERFEROMETRIC:
            value = recover_displacement(np.nan_to_num(samples), self.config,
                                         n_cycles=self.inner.n_cycles)
        elif readout is ReadoutKind.PHOTOELASTIC:
            value = recover_retardation(np.nan_to_num(samples), self.config)
        elif readout is ReadoutKind.PHOTODIODE:
            value = recover_power_w(np.nan_to_num(samples))
        else:
            arr = np.nan_to_num(samples)
            value = float(arr.std() / (arr.mean() + 1e-300))
        return OpticalObservation(
            observation_id=f"{run_id}:fault:{readout.value}:{seed}",
            run_id=run_id, mode=self.mode, readout=readout, config=self.config,
            quantity=quantity, value=value, units=units,
            uncertainty=dict(clean.uncertainty), samples=samples,
            seed=int(seed), faults=self.faults)


# --- the fault injection kernels -----------------------------------------

#: A stable integer tag per fault so its rng stream is distinct yet
#: reproducible under the acquisition seed.
_FAULT_TAG: dict[OpticalFault, int] = {
    OpticalFault.CLIPPING: 0x0C,
    OpticalFault.DRIFT: 0x0D,
    OpticalFault.SATURATION: 0x05,
    OpticalFault.PACKET_LOSS: 0x0B,
    OpticalFault.MISSING_SAMPLES: 0x0A,
    OpticalFault.FRINGE_WASHOUT: 0xF0,
    OpticalFault.SPECKLE_DECORRELATION: 0x5D,
}


def _apply_optical_fault(fault: OpticalFault, samples: np.ndarray,
                         config: dict, rng: np.random.Generator,
                         optics: OpticalConfig) -> np.ndarray:
    """Apply one optical fault to a copy of ``samples``, deterministically.

    Each fault demonstrably alters the trace relative to the clean synthetic
    reading. The two optical-specific faults collapse fringe visibility
    (wash-out) and decorrelate a speckle field.
    """
    x = np.asarray(samples, dtype=float).copy()
    n = x.size
    if n == 0:
        return x
    peak = float(np.max(np.abs(x)))
    scale = peak if peak > 0.0 else 1.0

    if fault is OpticalFault.CLIPPING:
        level = float(config.get("clip_fraction", 0.7)) * scale
        return np.clip(x, -level, level)
    if fault is OpticalFault.DRIFT:
        slope = float(config.get("drift_fraction", 0.5)) * scale
        return x + np.linspace(0.0, slope, n)
    if fault is OpticalFault.SATURATION:
        rail = float(config.get("saturation_fraction", 0.4)) * scale
        return np.clip(x, -rail, rail)
    if fault is OpticalFault.PACKET_LOSS:
        frac = float(config.get("packet_fraction", 0.1))
        length = max(1, int(round(frac * n)))
        start = int(rng.integers(0, max(1, n - length + 1)))
        x[start:start + length] = 0.0
        return x
    if fault is OpticalFault.MISSING_SAMPLES:
        frac = float(config.get("missing_fraction", 0.05))
        k = max(1, int(round(frac * n)))
        idx = rng.choice(n, size=min(k, n), replace=False)
        x[idx] = np.nan
        return x
    if fault is OpticalFault.FRINGE_WASHOUT:
        # collapse the fringe modulation onto its DC level: the fringe
        # visibility washes out and the phase can no longer be recovered
        frac = float(config.get("washout_fraction", 0.98))
        dc = float(np.mean(x))
        return dc + (1.0 - frac) * (x - dc)
    if fault is OpticalFault.SPECKLE_DECORRELATION:
        # mix in an independent speckle realisation, dropping correlation
        frac = float(config.get("decorrelation_fraction", 0.8))
        fresh = rng.standard_normal(n) ** 2
        return math.sqrt(1.0 - frac) * x + math.sqrt(frac) * fresh * scale
    raise OpticalError(f"unknown optical fault {fault!r}")  # pragma: no cover


# --- the load-bearing refusals -------------------------------------------

def refuse_intensity_as_phase(
        claim: str = "a photodiode reading yields a displacement") -> None:
    """Refuse to read a displacement from an intensity-only readout.

    A photodiode reads optical power and is phase-blind. A surface
    displacement is a phase shift that leaves the power unchanged, so it is
    not recoverable from a photodiode trace; only a phase-sensitive
    (interferometric or photoelastic) readout can recover it. Always raises.
    """
    raise OpticalError(
        f"refused: {claim!r}. A photodiode is an INTENSITY-ONLY readout: it "
        f"reads optical power and carries no phase, and a displacement is a "
        f"phase shift that does not change the power. Displacement is "
        f"recoverable only from a phase-sensitive readout "
        f"({', '.join(r.value for r in sorted(PHASE_SENSITIVE_READOUTS, key=lambda r: r.value))}). "
        f"{VERDICT}")


def refuse_reconstruction_as_measured(
        claim: str = "a reconstructed fringe is an image of a real source"
) -> None:
    """Refuse to read a synthetic fringe reconstruction as a measurement.

    Delegates to :func:`r13.imaging.refuse_reconstruction_as_measured`: a
    filtered back-projection of a synthetic phantom or fringe is a
    reconstruction of generated numbers, not an image of any real emitter.
    Always raises.
    """
    try:
        imaging.refuse_reconstruction_as_measured()
    except imaging.ImagingError as exc:
        raise OpticalError(
            f"refused: {claim!r}. {exc} A reconstructed fringe here is a "
            f"SYNTHETIC_OBSERVATION, not a PHYSICAL_MEASUREMENT. {VERDICT}"
        ) from exc


def refuse_synthetic_as_physical(
        claim: str = "a synthetic optical trace is a physical measurement"
) -> None:
    """Refuse any optical reading read as a physical measurement.

    Every trace this lane produces is a ``SYNTHETIC_OBSERVATION`` from a
    seeded generator or a recorded synthetic artifact, and a REAL_DEVICE
    acquires nothing. Delegates to the governance core. Always raises.
    """
    try:
        claims.refuse_synthetic_as_physical()
    except claims.ClaimError as exc:
        raise OpticalError(
            f"refused: {claim!r}. {exc} {PHYSICAL_VALIDATION}. {VERDICT}"
        ) from exc


# --- report ---------------------------------------------------------------

def optical_report() -> dict:
    """The standing statement of what the optical lane is and is not."""
    config = OpticalConfig()
    planted = 0.5 * config.unambiguous_displacement_m()
    dev = OpticalSyntheticDevice(config)
    obs = dev.acquire(ReadoutKind.INTERFEROMETRIC, run_id="report", seed=0,
                      displacement_m=planted)
    recovered = obs.value
    rel_err = abs(recovered - planted) / abs(planted)
    return {
        "what_this_is": (
            "the R15 optical measurement lane: one acquisition interface "
            "behind four modes -- REAL_DEVICE (interface only, acquires "
            "nothing, physical run PREREGISTERED_NOT_RUN), SYNTHETIC_DEVICE "
            "(deterministic optical signal with a planted displacement or "
            "fringe the pipeline recovers), REPLAY_DEVICE (replays a "
            "recorded synthetic trace) and FAULT_INJECTION_DEVICE (injects "
            "clipping, drift, saturation, packet loss, missing samples, and "
            "the optical-specific fringe wash-out and speckle "
            "decorrelation) -- across photodiode, interferometric, speckle "
            "and photoelastic readouts, with a full optical error budget"),
        "modes": [m.value for m in OpticalMode],
        "readouts": [r.value for r in ReadoutKind],
        "phase_sensitive_readouts": sorted(r.value
                                           for r in PHASE_SENSITIVE_READOUTS),
        "intensity_only_readouts": sorted(r.value
                                          for r in INTENSITY_ONLY_READOUTS),
        "fault_modes": [f.value for f in OpticalFault],
        "optical_specific_faults": sorted(f.value
                                          for f in OPTICAL_SPECIFIC_FAULTS),
        "corrections": ["dark", "flat", "reference", "drift"],
        "tracked_quantities": ["wavelength", "bandwidth", "power",
                               "polarization", "geometry", "thermal_load"],
        "planted_displacement_m": planted,
        "recovered_displacement_m": recovered,
        "power_control_relative_error": rel_err,
        "power_control_recovers_planted": bool(rel_err < 1.0e-3),
        "error_budget": build_error_budget(config),
        "refusals": [
            "OpticalRealDevice.acquire raises NoOpticalHardwareError",
            "refuse_intensity_as_phase (a photodiode cannot yield "
            "displacement)",
            "refuse_reconstruction_as_measured (a synthetic fringe recon is "
            "not an image of a real source)",
            "refuse_synthetic_as_physical (no trace is a measurement)",
        ],
        "reading_claim_class": READING_CLAIM_CLASS.value,
        "software_ceiling": claims.MAX_SOFTWARE_CLASS.value,
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "hardware_status": (
            "no optical bench exists here; a REAL_DEVICE read is BLOCKED and "
            "acquires nothing, and the physical run is PREREGISTERED_NOT_RUN"),
        "what_would_change_this": (
            "a built optical bench -- a laser of known wavelength and "
            "bandwidth, an interferometer or polarimeter, a calibrated "
            "photodetector, a mounted specimen with a geometry binding, a "
            "clock and an environment log -- none of which exists here"),
        "what_this_does_not_say": (
            "It does not say any optical signal was transduced from a "
            "specimen. Every trace is simulator output under a seed; a "
            "photodiode is phase-blind and cannot yield displacement; a "
            "reconstructed fringe is a SYNTHETIC_OBSERVATION, not an image "
            "of a real source. A SYNTHETIC_OBSERVATION is never a "
            "PHYSICAL_MEASUREMENT. PHYSICAL_VALIDATION_NOT_CLAIMED."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "MEASURED_HERE", "PHYSICAL_VALIDATION", "ANALYSIS_VERSION",
    "READING_CLAIM_CLASS", "SOFTWARE_CLAIM_CLASS",
    "OpticalError", "NoOpticalHardwareError",
    "OpticalMode", "ReadoutKind", "OpticalFault",
    "PHASE_SENSITIVE_READOUTS", "INTENSITY_ONLY_READOUTS",
    "OPTICAL_SPECIFIC_FAULTS",
    "OpticalConfig", "Correction",
    "dark_correct", "flat_correct", "reference_correct", "drift_correct",
    "synthetic_interferogram", "recover_displacement",
    "synthetic_photodiode", "recover_power_w",
    "synthetic_speckle_field", "speckle_correlation", "decorrelate_speckle",
    "synthetic_photoelastic", "recover_retardation", "polarization_rosette",
    "reconstruct_fringe_phantom",
    "OpticalObservation", "build_error_budget",
    "OpticalDevice", "OpticalRealDevice", "OpticalSyntheticDevice",
    "OpticalReplayDevice", "OpticalFaultInjectionDevice",
    "refuse_intensity_as_phase", "refuse_reconstruction_as_measured",
    "refuse_synthetic_as_physical", "optical_report",
]
