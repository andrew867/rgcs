"""R11 P14 — a two-channel rotating field, interrupted. Preregistered, not run.

The proposal is simple to state and easy to over-read: drive a resonator
with two orthogonal coil channels in quadrature so the applied field
*rotates*, then cut the drive at a chosen point of the rotation and watch
what rings down. If the cutoff phase matters, the story goes, something
about the rotation is being stored.

This module builds that experiment in full and **does not run it**. There
is no bench in this repository: no coils, no electrodes, no resonator, no
counter, no thermometer. Every observable the experiment would need is
enumerated and carries status ``BLOCKED_MISSING_DATA``, and
:func:`refuse_bench_claim` raises rather than let a modelled waveform be
quoted as a measurement.

**The drive, written once.**

    Bx(t) = B0 * ax * cos(2*pi*f_drive*t + phi0)
    By(t) = B0 * ay * sin(2*pi*f_drive*t + phi0)

is the balanced quadrature special case of the general two-channel drive
carried here, in which the second channel lags the first by an arbitrary
*rational* phase ``p`` measured in turns:

    Bx(t) = B0 * ax * cos(2*pi*(f*t + phi0))
    By(t) = B0 * ay * cos(2*pi*(f*t + phi0 - p))

``p = 1/4`` recovers ``cos -> sin`` exactly, and the rational phases are
kept as ``Fraction`` for the same reason :mod:`r11.phasealpha` keeps its
alphabet exact: the sense of rotation is decided by the sign of
``sin(2*pi*p)``, and a sign decided on the last bit of a mantissa is not
a decided sign. :func:`rotation_sense` therefore reads the sense off the
rational directly, and the three outcomes are genuinely different
physics:

* ``ax == ay`` with ``p = 1/4`` — a **circular** rotating field;
* ``ax != ay`` — an **elliptical** one, still rotating;
* ``p = 0`` or ``p = 1/2`` — a **linear** field. The two channels are in
  (or in anti-) phase, the tip of the vector runs back and forth along a
  line, and there is no rotation at all. That is ``DEGENERATE``, and it
  is the single most important control the experiment has, because it
  reproduces the envelope, the timing and the total power of the rotating
  case while removing the only thing under test.

**One exact preregistered prediction is encoded.** For the registered
N=7 scalar geometry — sound speed ``v = 6310 m/s``, drive ``f = 4096 Hz``,
``N = 7`` segments — the segment length is ``L = v/(2*N*f)``, so the
round-trip acoustic time is ``2L/v = 1/(N*f)`` and the round-trip phase
at the drive frequency is

    f * 2L/v = 1/N  turns  =  360/7 degrees  =  51.428571... degrees

**exactly**, with ``v`` cancelling identically. :func:`roundtrip_phase_turns`
computes that chain in ``Fraction`` arithmetic and returns
``Fraction(1, N)`` as an exact rational, not a float that rounds to one.
It is an ``EXACT_IDENTITY`` about the geometry as defined, and it is
*not* a measurement: it says what the geometry would predict, which is
precisely what makes it worth freezing before any bench exists.

**Eight controls, declared, and none of them optional.** A cutoff-phase
dependence is exactly the shape an artifact of the switch itself takes,
so :class:`Control` names all eight nulls the experiment must run, and
:func:`refuse_result_without_controls` refuses a result while any one is
undeclared. **The preregistration is hashed before any comparison**, and
:func:`refuse_unfrozen_scoring` refuses scoring against a prediction set
that was not frozen first.

Nothing here is measured, driven, switched, or observed.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

import numpy as np

from r11.phasealpha import (
    DEGREES_PER_TURN,
    Quantity,
    Unit,
    angular_frequency,
    degrees_of,
    phase_mod_turn,
    refuse_unit_confusion,
)

# --- verdict, claim vocabulary, statuses ---------------------------------

#: The standing verdict for this module.
VERDICT = "ROTATING_FIELD_EXPERIMENT_PREREGISTERED_NOT_RUN"

#: The typed claim vocabulary, exact strings, shared across R11.
CLAIM_CLASSES: tuple[str, ...] = (
    "EXACT_IDENTITY",
    "SOURCE_ESTABLISHED_PHYSICS",
    "REPOSITORY_COMPUTATIONAL_RESULT",
    "ENGINEERING_CANDIDATE",
    "RETROSPECTIVE_NUMERIC_MATCH",
    "PROSPECTIVE_PREDICTION",
    "BENCH_MEASUREMENT",
    "UNSUPPORTED",
    "BLOCKED_MISSING_DATA",
)

EXACT_IDENTITY = "EXACT_IDENTITY"
PROSPECTIVE_PREDICTION = "PROSPECTIVE_PREDICTION"
BENCH_MEASUREMENT = "BENCH_MEASUREMENT"
BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"

#: The claim class of this module as a whole.
CLAIM_CLASS = PROSPECTIVE_PREDICTION

MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Relative tolerance used when a *numerically sampled* trajectory is
#: cross-checked against the exact rational rotation sense.
NUMERIC_SENSE_TOL = 1e-9


class RotFieldError(RuntimeError):
    """Raised when the rotating-field experiment is asked for more than it has.

    Covers the exactness guards (a float where a rational phase belongs),
    the unit guards (a drive frequency that is not in cycles per second),
    the control refusal (:func:`refuse_result_without_controls`), the
    bench refusal (:func:`refuse_bench_claim`) and the preregistration
    refusal (:func:`refuse_unfrozen_scoring`).
    """


# --- exactness guard -----------------------------------------------------

def _exact(value: object, what: str) -> Fraction:
    """Return ``value`` as an exact ``Fraction``, or refuse it.

    Channel amplitudes and channel phases decide a *sign*, and a sign is
    not a quantity that may be approximated. Ints, ``Fraction`` and exact
    decimal strings pass; bools, floats and complex numbers raise.
    """
    if isinstance(value, bool):
        raise RotFieldError(
            f"refusing a boolean as {what}: {value!r} is not a quantity")
    if isinstance(value, float):
        raise RotFieldError(
            f"refusing the float {value!r} as {what}. The rotation sense "
            f"is the sign of sin(2*pi*p), and a sign decided on the last "
            f"bit of a mantissa is not a decided sign. Pass an int, a "
            f"Fraction (e.g. Fraction"
            f"({Fraction(value).limit_denominator(10 ** 9)})), or an "
            f"exact decimal string.")
    if isinstance(value, complex):
        raise RotFieldError(f"refusing the complex value {value!r} as {what}")
    if isinstance(value, (int, Fraction)):
        return Fraction(value)
    try:
        return Fraction(value)
    except (TypeError, ValueError):
        raise RotFieldError(
            f"cannot read {value!r} as an exact {what}; give an int, a "
            f"Fraction, or an exact decimal string.") from None


def _amplitude(value: object, what: str) -> Fraction:
    """An exact, non-negative channel amplitude."""
    a = _exact(value, what)
    if a < 0:
        raise RotFieldError(
            f"{what} must be non-negative; a negative channel amplitude is "
            f"a half-turn of channel phase wearing a minus sign, and "
            f"mixing the two hides the phase from rotation_sense. Use the "
            f"phase argument.")
    return a


# --- (1) rotation sense, exactly -----------------------------------------

class RotationSense(Enum):
    """Which way the field vector turns, if it turns at all.

    ``DEGENERATE`` is not "unknown": it is the positive statement that the
    trajectory encloses no area, which happens when either channel is
    dead or when the two channels are in phase or in anti-phase. A
    degenerate drive is a *linear* field, and it is the control the whole
    experiment leans on.
    """

    COUNTERCLOCKWISE = "COUNTERCLOCKWISE"
    CLOCKWISE = "CLOCKWISE"
    DEGENERATE = "DEGENERATE"

    @property
    def sign(self) -> int:
        """+1 counterclockwise, -1 clockwise, 0 degenerate."""
        return {"COUNTERCLOCKWISE": 1, "CLOCKWISE": -1,
                "DEGENERATE": 0}[self.value]

    @property
    def rotates(self) -> bool:
        return self is not RotationSense.DEGENERATE


class Polarization(Enum):
    """The shape the field-vector tip traces out over one drive period."""

    CIRCULAR = "CIRCULAR"
    ELLIPTICAL = "ELLIPTICAL"
    LINEAR = "LINEAR"


def sense_sign(ax: object, ay: object, phase: object) -> int:
    """Sign of ``ax*ay*sin(2*pi*p)``, computed exactly from the rational.

    ``sin(2*pi*p)`` is positive for ``0 < p < 1/2``, negative for
    ``1/2 < p < 1``, and zero at ``p = 0`` and ``p = 1/2`` -- all decided
    by comparing rationals, with no trigonometry and therefore no
    rounding.
    """
    a = _amplitude(ax, "ax")
    b = _amplitude(ay, "ay")
    if a == 0 or b == 0:
        return 0
    p = phase_mod_turn(_exact(phase, "channel phase in turns"))
    if p == 0 or p == Fraction(1, 2):
        return 0
    return 1 if p < Fraction(1, 2) else -1


def rotation_sense(ax: object, ay: object,
                   phase: object = Fraction(1, 4)) -> RotationSense:
    """The sense of rotation of a two-channel drive.

    ``ax`` and ``ay`` are the (exact, non-negative) channel amplitudes and
    ``phase`` is the lag of channel y behind channel x in **turns**. With
    ``ax == ay`` and ``phase == 1/4`` this is the balanced circular drive
    ``(cos, sin)``, which advances counterclockwise. ``phase == 3/4``
    reverses it. ``phase == 0`` or ``1/2`` makes the two channels
    proportional, the trajectory a line, and the sense ``DEGENERATE``; so
    does killing either channel, which is the ONE_CHANNEL_ONLY control.

    Amplitude imbalance changes the *shape* (see :func:`polarization`) and
    never the *sense*: an ellipse still goes round.
    """
    s = sense_sign(ax, ay, phase)
    if s > 0:
        return RotationSense.COUNTERCLOCKWISE
    if s < 0:
        return RotationSense.CLOCKWISE
    return RotationSense.DEGENERATE


def polarization(ax: object, ay: object,
                 phase: object = Fraction(1, 4)) -> Polarization:
    """CIRCULAR, ELLIPTICAL or LINEAR, decided on exact rationals.

    CIRCULAR requires *both* balanced channels (``ax == ay``) and exact
    quadrature (``p = 1/4`` or ``3/4``). Anything else that still rotates
    is ELLIPTICAL, and anything that does not rotate is LINEAR.
    """
    a = _amplitude(ax, "ax")
    b = _amplitude(ay, "ay")
    if sense_sign(a, b, phase) == 0:
        return Polarization.LINEAR
    p = phase_mod_turn(_exact(phase, "channel phase in turns"))
    quadrature = p in (Fraction(1, 4), Fraction(3, 4))
    if a == b and quadrature:
        return Polarization.CIRCULAR
    return Polarization.ELLIPTICAL


def reversed_phase(phase: object) -> Fraction:
    """The channel phase that reverses the sense: ``-p`` mod one turn.

    This is the REVERSED_ROTATION control, as arithmetic. Applying it
    twice returns the original phase, and applying it to a degenerate
    phase leaves it degenerate -- a linear drive has no sense to reverse.
    """
    return phase_mod_turn(-_exact(phase, "channel phase in turns"))


def enclosed_area(ax: object, ay: object,
                  phase: object = Fraction(1, 4),
                  b0: float = 1.0) -> float:
    """Signed area swept per drive period: ``pi * B0^2 * ax*ay*sin(2*pi*p)``.

    Float, because ``sin`` is. Its *sign* is not taken from here -- that
    comes from :func:`sense_sign`, exactly -- and the two are required to
    agree by :func:`sense_consistency`.
    """
    a = float(_amplitude(ax, "ax"))
    b = float(_amplitude(ay, "ay"))
    p = phase_mod_turn(_exact(phase, "channel phase in turns"))
    return float(math.pi * float(b0) ** 2 * a * b
                 * math.sin(2.0 * math.pi * float(p)))


# --- (2) the drive itself -------------------------------------------------

#: The registered drive frequency, as a united quantity.
DRIVE_FREQUENCY = Quantity(4096.0, Unit.CYCLES_PER_SECOND)


@dataclass(frozen=True)
class RotatingDrive:
    """A two-channel drive with exact amplitudes and an exact channel phase.

    ``f_drive`` is a :class:`r11.phasealpha.Quantity` and must be in
    cycles per second; the module never multiplies a frequency by a time
    without knowing which of ``f`` and ``omega`` it is holding, because
    the two differ by ``2*pi`` and that factor is not a rounding detail.
    """

    b0: float = 1.0
    ax: Fraction = Fraction(1)
    ay: Fraction = Fraction(1)
    f_drive: Quantity = DRIVE_FREQUENCY
    phi0: Fraction = Fraction(0)            # common start phase, turns
    phase: Fraction = Fraction(1, 4)        # y lags x by this, turns

    def __post_init__(self) -> None:
        object.__setattr__(self, "ax", _amplitude(self.ax, "ax"))
        object.__setattr__(self, "ay", _amplitude(self.ay, "ay"))
        object.__setattr__(self, "phi0",
                           _exact(self.phi0, "start phase in turns"))
        object.__setattr__(self, "phase",
                           _exact(self.phase, "channel phase in turns"))
        if not isinstance(self.f_drive, Quantity):
            raise RotFieldError(
                "f_drive must be a Quantity; an unlabelled number is not a "
                "frequency")
        if self.f_drive.unit is not Unit.CYCLES_PER_SECOND:
            raise RotFieldError(
                f"f_drive must be in {Unit.CYCLES_PER_SECOND.value}, got "
                f"{self.f_drive.unit.value}. Frequency and angular "
                f"frequency differ by 2*pi; convert with "
                f"r11.phasealpha.ordinary_frequency rather than reusing "
                f"the number.")
        if not math.isfinite(self.f_drive.value) or self.f_drive.value <= 0.0:
            raise RotFieldError("drive frequency must be finite and positive")
        if not math.isfinite(float(self.b0)) or float(self.b0) <= 0.0:
            raise RotFieldError("B0 must be finite and positive")
        if self.ax == 0 and self.ay == 0:
            raise RotFieldError("a drive with both channels dead is no drive")

    # -- units ------------------------------------------------------------

    def omega(self) -> Quantity:
        """``omega = 2*pi*f``, as a united quantity."""
        return angular_frequency(self.f_drive)

    def period_s(self) -> float:
        return 1.0 / float(self.f_drive.value)

    def same_frequency_as(self, other: "RotatingDrive") -> Unit:
        """Guard: two drives may only be compared in the same unit kind."""
        return refuse_unit_confusion(self.f_drive, other.f_drive)

    # -- the field --------------------------------------------------------

    def field(self, t: float) -> tuple[float, float]:
        """``(Bx, By)`` at time ``t`` seconds.

        ``Bx = B0*ax*cos(2*pi*(f*t + phi0))`` and
        ``By = B0*ay*cos(2*pi*(f*t + phi0 - p))``. At ``p = 1/4`` the
        second is ``B0*ay*sin(2*pi*(f*t + phi0))`` identically, which is
        the drive as originally written.
        """
        turns = float(self.f_drive.value) * float(t) + float(self.phi0)
        bx = float(self.b0) * float(self.ax) * math.cos(2.0 * math.pi * turns)
        by = float(self.b0) * float(self.ay) * math.cos(
            2.0 * math.pi * (turns - float(self.phase)))
        return (bx, by)

    def waveform(self, n_samples: int = 256,
                 periods: float = 1.0) -> dict:
        """Sample the trajectory over ``periods`` drive periods."""
        n = int(n_samples)
        if n < 3:
            raise RotFieldError("a trajectory needs at least three samples")
        if float(periods) <= 0.0:
            raise RotFieldError("periods must be positive")
        t = np.linspace(0.0, float(periods) * self.period_s(), n,
                        endpoint=False)
        pairs = np.array([self.field(float(x)) for x in t])
        return {"t_s": t, "bx": pairs[:, 0], "by": pairs[:, 1]}

    # -- what it is -------------------------------------------------------

    @property
    def sense(self) -> RotationSense:
        return rotation_sense(self.ax, self.ay, self.phase)

    @property
    def polarization(self) -> Polarization:
        return polarization(self.ax, self.ay, self.phase)

    def reversed(self) -> "RotatingDrive":
        """The same drive with the rotation sense reversed."""
        return RotatingDrive(self.b0, self.ax, self.ay, self.f_drive,
                             self.phi0, reversed_phase(self.phase))

    def as_dict(self) -> dict:
        return {
            "b0": float(self.b0),
            "ax": str(self.ax),
            "ay": str(self.ay),
            "balanced_channels": self.ax == self.ay,
            "f_drive_hz": float(self.f_drive.value),
            "f_drive_unit": self.f_drive.unit.value,
            "omega_rad_per_s": float(self.omega().value),
            "omega_unit": self.omega().unit.value,
            "phi0_turns": str(self.phi0),
            "channel_phase_turns": str(self.phase),
            "channel_phase_degrees": float(degrees_of(
                phase_mod_turn(self.phase))),
            "rotation_sense": self.sense.value,
            "rotation_sense_sign": self.sense.sign,
            "polarization": self.polarization.value,
            "enclosed_area_per_period": enclosed_area(
                self.ax, self.ay, self.phase, self.b0),
            "measured_here": MEASURED_HERE,
        }


#: The balanced circular drive of the proposal: ax == ay, p = 1/4.
CIRCULAR_DRIVE = RotatingDrive()

#: The linear (degenerate) control: same envelope, same power, no rotation.
LINEAR_CONTROL_DRIVE = RotatingDrive(phase=Fraction(0))


def numeric_sense(drive: RotatingDrive, n_samples: int = 512
                  ) -> RotationSense:
    """The rotation sense read off a *sampled* trajectory, independently.

    Uses the signed-area rule ``sum(bx[i]*by[i+1] - bx[i+1]*by[i])``, the
    same quadrature test :mod:`r11.rotor` applies to two pickup channels.
    This is a numerical route to the same answer :func:`rotation_sense`
    reaches by exact rational comparison, and
    :func:`sense_consistency` requires the two to agree. If a sign
    convention were wrong in one of them, they would disagree.
    """
    w = drive.waveform(n_samples)
    bx, by = w["bx"], w["by"]
    cross = float(np.sum(bx[:-1] * by[1:] - bx[1:] * by[:-1]))
    scale = (len(bx) * float(drive.b0) ** 2
             * max(float(drive.ax), 1e-30) * max(float(drive.ay), 1e-30))
    normalised = cross / scale
    if normalised > NUMERIC_SENSE_TOL:
        return RotationSense.COUNTERCLOCKWISE
    if normalised < -NUMERIC_SENSE_TOL:
        return RotationSense.CLOCKWISE
    return RotationSense.DEGENERATE


def sense_consistency(drive: RotatingDrive, n_samples: int = 512) -> dict:
    """Exact rational sense against numerically sampled sense."""
    exact = drive.sense
    numeric = numeric_sense(drive, n_samples)
    return {
        "channel_phase_turns": str(drive.phase),
        "exact_sense": exact.value,
        "numeric_sense": numeric.value,
        "agree": exact is numeric,
        "measured_here": MEASURED_HERE,
    }


# --- (3) the exact preregistered round-trip phase -------------------------

#: The registered N=7 scalar geometry. Model parameters, not measurements.
N7_SOUND_SPEED_M_PER_S = Fraction(6310)
N7_DRIVE_HZ = Fraction(4096)
N7_SEGMENTS = 7


def segment_length_m(v: object = N7_SOUND_SPEED_M_PER_S,
                     f: object = N7_DRIVE_HZ,
                     n_segments: int = N7_SEGMENTS) -> Fraction:
    """``L = v / (2*N*f)``, exactly."""
    speed = _exact(v, "sound speed in m/s")
    freq = _exact(f, "frequency in hertz")
    n = int(n_segments)
    if speed <= 0:
        raise RotFieldError("sound speed must be positive")
    if freq <= 0:
        raise RotFieldError("frequency must be positive")
    if n < 1:
        raise RotFieldError("the segment count N must be a positive integer")
    return speed / (2 * n * freq)


def roundtrip_time_s(v: object = N7_SOUND_SPEED_M_PER_S,
                     f: object = N7_DRIVE_HZ,
                     n_segments: int = N7_SEGMENTS) -> Fraction:
    """``t = 2L/v = 1/(N*f)``, exactly. The sound speed cancels."""
    speed = _exact(v, "sound speed in m/s")
    return 2 * segment_length_m(v, f, n_segments) / speed


def roundtrip_phase_turns(v: object = N7_SOUND_SPEED_M_PER_S,
                          f: object = N7_DRIVE_HZ,
                          n_segments: int = N7_SEGMENTS) -> Fraction:
    """The round-trip acoustic phase at the drive frequency, in turns.

    Derived, not asserted::

        L    = v / (2*N*f)
        t    = 2L/v = 1/(N*f)
        turns = f * t = 1/N

    Every step is ``Fraction`` arithmetic, so the return value is the
    exact rational ``1/N`` and compares equal to ``Fraction(1, N)`` under
    ``==``, not under ``pytest.approx``. For the registered geometry
    (``v = 6310 m/s``, ``f = 4096 Hz``, ``N = 7``) that is ``1/7`` turn,
    ``360/7 = 51.428571...`` degrees.

    The sound speed cancels identically, which is the content of the
    identity: the phase is fixed by the *choice* ``L = v/(2*N*f)``, so it
    is exact for any ``v`` at all, and is therefore a statement about the
    geometry as defined rather than about any material.
    """
    freq = _exact(f, "frequency in hertz")
    return freq * roundtrip_time_s(v, f, n_segments)


def roundtrip_phase_degrees(v: object = N7_SOUND_SPEED_M_PER_S,
                            f: object = N7_DRIVE_HZ,
                            n_segments: int = N7_SEGMENTS) -> Fraction:
    """The same phase in degrees, exactly: ``360/N``."""
    return degrees_of(roundtrip_phase_turns(v, f, n_segments))


#: The registered values, computed once by the functions above.
N7_ROUNDTRIP_TURNS = roundtrip_phase_turns()
N7_ROUNDTRIP_DEGREES = roundtrip_phase_degrees()
N7_SEGMENT_LENGTH_M = segment_length_m()


def roundtrip_phase_prediction() -> dict:
    """The one exact prediction this module freezes."""
    return {
        "geometry": "N7_SCALAR_GEOMETRY",
        "sound_speed_m_per_s": str(N7_SOUND_SPEED_M_PER_S),
        "drive_hz": str(N7_DRIVE_HZ),
        "n_segments": N7_SEGMENTS,
        "segment_length_m_exact": str(N7_SEGMENT_LENGTH_M),
        "segment_length_m_float": float(N7_SEGMENT_LENGTH_M),
        "roundtrip_time_s_exact": str(roundtrip_time_s()),
        "roundtrip_phase_turns_exact": str(N7_ROUNDTRIP_TURNS),
        "roundtrip_phase_turns_is_one_over_n":
            N7_ROUNDTRIP_TURNS == Fraction(1, N7_SEGMENTS),
        "roundtrip_phase_degrees_exact": str(N7_ROUNDTRIP_DEGREES),
        "roundtrip_phase_degrees_float": float(N7_ROUNDTRIP_DEGREES),
        "degrees_per_turn": DEGREES_PER_TURN,
        "sound_speed_cancels": True,
        "derivation": ("L = v/(2*N*f);  t = 2L/v = 1/(N*f);  "
                       "phase = f*t = 1/N turns"),
        "claim_class": EXACT_IDENTITY,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "note": ("an exact identity about the geometry as defined. It is "
                 "not a measurement of a crystal, a resonator, or a "
                 "sound speed, and 6310 m/s is a model parameter that "
                 "cancels out of the result"),
    }


# --- (4) the observables the bench would need, all blocked ----------------

class Observable(Enum):
    """Every channel the interruption experiment would have to record."""

    COIL_CURRENT = "COIL_CURRENT"
    COIL_VOLTAGE = "COIL_VOLTAGE"
    ELECTRODE_VOLTAGE = "ELECTRODE_VOLTAGE"
    ELECTRODE_CURRENT = "ELECTRODE_CURRENT"
    BVD_PARAMETERS_BEFORE = "BVD_PARAMETERS_BEFORE"
    BVD_PARAMETERS_AFTER = "BVD_PARAMETERS_AFTER"
    RINGDOWN_AMPLITUDE = "RINGDOWN_AMPLITUDE"
    RINGDOWN_PHASE = "RINGDOWN_PHASE"
    MODAL_ENERGY_FRACTIONS = "MODAL_ENERGY_FRACTIONS"
    SIDEBAND_SPECTRUM = "SIDEBAND_SPECTRUM"
    QUALITY_FACTOR = "QUALITY_FACTOR"
    TEMPERATURE = "TEMPERATURE"
    ACCELEROMETER = "ACCELEROMETER"
    EXTERNAL_QTF = "EXTERNAL_QTF"


OBSERVABLE_UNITS: dict[Observable, str] = {
    Observable.COIL_CURRENT: "A",
    Observable.COIL_VOLTAGE: "V",
    Observable.ELECTRODE_VOLTAGE: "V",
    Observable.ELECTRODE_CURRENT: "A",
    Observable.BVD_PARAMETERS_BEFORE: "(R_ohm, L_H, C_F, C0_F)",
    Observable.BVD_PARAMETERS_AFTER: "(R_ohm, L_H, C_F, C0_F)",
    Observable.RINGDOWN_AMPLITUDE: "V",
    Observable.RINGDOWN_PHASE: "turns",
    Observable.MODAL_ENERGY_FRACTIONS: "dimensionless",
    Observable.SIDEBAND_SPECTRUM: "V/sqrt(Hz)",
    Observable.QUALITY_FACTOR: "dimensionless",
    Observable.TEMPERATURE: "K",
    Observable.ACCELEROMETER: "m/s^2",
    Observable.EXTERNAL_QTF: "V",
}

OBSERVABLE_REASONS: dict[Observable, str] = {
    Observable.COIL_CURRENT:
        "the field actually applied, as opposed to the field commanded; "
        "coil inductance means the current lags the drive and the cutoff "
        "phase of the FIELD is not the cutoff phase of the WAVEFORM",
    Observable.COIL_VOLTAGE:
        "with the current, it gives the electrical power delivered and "
        "the switching transient at cutoff",
    Observable.ELECTRODE_VOLTAGE:
        "the drive seen by the resonator electrodes, which is what the "
        "energy ledger charges against",
    Observable.ELECTRODE_CURRENT:
        "motional plus static-capacitance current; separating the two is "
        "what makes the mechanical response distinguishable from the "
        "electrical one",
    Observable.BVD_PARAMETERS_BEFORE:
        "the Butterworth-Van Dyke equivalent circuit fitted before the "
        "interruption, so that any change afterwards has a baseline",
    Observable.BVD_PARAMETERS_AFTER:
        "the same fit afterwards; a claimed effect that does not move any "
        "BVD parameter has not changed the resonator",
    Observable.RINGDOWN_AMPLITUDE:
        "the primary observable: how much energy is still ringing after "
        "the drive is cut at a given phase",
    Observable.RINGDOWN_PHASE:
        "the secondary observable: whether the ringdown remembers the "
        "phase at which the drive stopped",
    Observable.MODAL_ENERGY_FRACTIONS:
        "where the stored energy sits across modes after the cut; a "
        "cutoff-phase dependence that only moves energy between modes is "
        "redistribution, not a new channel",
    Observable.SIDEBAND_SPECTRUM:
        "an abrupt cut is a broadband event; the sidebands it produces "
        "are ordinary Fourier bookkeeping and must be accounted before "
        "anything is called anomalous",
    Observable.QUALITY_FACTOR:
        "Q sets the ringdown time constant, so a Q drift across the "
        "sweep mimics a cutoff-phase dependence exactly",
    Observable.TEMPERATURE:
        "quartz frequency and Q are temperature dependent; an unlogged "
        "thermal drift is the most common false positive available",
    Observable.ACCELEROMETER:
        "mechanical shock from the switch, the disk, or the room, which "
        "couples to the resonator without any field being involved",
    Observable.EXTERNAL_QTF:
        "an independent tuning fork outside the drive, as a "
        "common-mode witness: anything it also sees is environmental",
}


@dataclass(frozen=True)
class ObservableRecord:
    """One observable at one sweep point. There is no bench, so no value."""

    observable: Observable
    unit: str
    why_it_matters: str
    value: object | None = None
    status: str = BLOCKED_MISSING_DATA

    def __post_init__(self) -> None:
        if self.status == BLOCKED_MISSING_DATA and self.value is not None:
            raise RotFieldError(
                f"{self.observable.value} is {BLOCKED_MISSING_DATA} and "
                f"carries a value; a blocked observable has no reading")
        if self.status != BLOCKED_MISSING_DATA:
            raise RotFieldError(
                f"{self.observable.value} may only be carried with status "
                f"{BLOCKED_MISSING_DATA}: no bench exists in this "
                f"repository, so no observable here has been recorded")

    def as_dict(self) -> dict:
        return {
            "observable": self.observable.value,
            "unit": self.unit,
            "why_it_matters": self.why_it_matters,
            "value": self.value,
            "status": self.status,
        }


def observable_set() -> tuple[ObservableRecord, ...]:
    """Every required observable, in declaration order, all blocked."""
    return tuple(
        ObservableRecord(o, OBSERVABLE_UNITS[o], OBSERVABLE_REASONS[o])
        for o in Observable)


REQUIRED_OBSERVABLES: tuple[ObservableRecord, ...] = observable_set()


# --- (5) the cutoff sweep --------------------------------------------------

DEFAULT_SWEEP_POINTS = 12


def cutoff_sweep(n_points: int = DEFAULT_SWEEP_POINTS,
                 drive: RotatingDrive = CIRCULAR_DRIVE) -> dict:
    """Sweep the cutoff phase through one full turn. Nothing is recorded.

    The cutoff phase is the point of the rotation at which the drive is
    interrupted, and the sweep visits ``n_points`` equally spaced phases
    ``i/n_points`` turns for ``i`` in ``0 .. n_points-1``. The phases are
    exact rationals and the last one plus one step is exactly one turn,
    so the sweep genuinely closes rather than nearly closing.

    Every point carries the full observable list, and every observable
    carries status ``BLOCKED_MISSING_DATA`` because there is no coil, no
    electrode, no counter and no thermometer in this repository. The
    sweep is a *specification of an experiment*, and
    :func:`refuse_bench_claim` refuses to let it be read as a run.
    """
    n = int(n_points)
    if n < 2:
        raise RotFieldError("a cutoff sweep needs at least two points")
    step = Fraction(1, n)
    phases = [Fraction(i, n) for i in range(n)]
    records = [r.as_dict() for r in REQUIRED_OBSERVABLES]
    points = [
        {
            "index": i,
            "cutoff_phase_turns_exact": str(p),
            "cutoff_phase_degrees_exact": str(degrees_of(p)),
            "cutoff_phase_degrees": float(degrees_of(p)),
            "field_at_cutoff": drive.field(
                float(p) * drive.period_s()),
            "observables": records,
            "status": BLOCKED_MISSING_DATA,
        }
        for i, p in enumerate(phases)
    ]
    return {
        "n_points": n,
        "step_turns_exact": str(step),
        "points": points,
        "covers_full_turn": phases[-1] + step == 1,
        "phases_are_exact_rationals": all(
            isinstance(p, Fraction) for p in phases),
        "drive": drive.as_dict(),
        "observables_per_point": len(REQUIRED_OBSERVABLES),
        "all_observables_blocked": all(
            o["status"] == BLOCKED_MISSING_DATA
            for pt in points for o in pt["observables"]),
        "any_observable_recorded": any(
            o["value"] is not None
            for pt in points for o in pt["observables"]),
        "status": BLOCKED_MISSING_DATA,
        "claim_class": BLOCKED_MISSING_DATA,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "verdict": VERDICT,
    }


# --- (6) the eight declared controls --------------------------------------

class Control(Enum):
    """The eight nulls this experiment cannot report a result without.

    Each removes one thing the claim depends on while leaving everything
    else -- envelope, timing, power, thermal load -- as close to identical
    as the apparatus allows. A cutoff-phase dependence that survives all
    eight is interesting; one that does not survive any single one of
    them has been explained.
    """

    STATIC_NONROTATING = "STATIC_NONROTATING"
    ONE_CHANNEL_ONLY = "ONE_CHANNEL_ONLY"
    REVERSED_ROTATION = "REVERSED_ROTATION"
    CONTINUOUS_DRIVE = "CONTINUOUS_DRIVE"
    PHASE_RANDOMIZED_CUTOFF = "PHASE_RANDOMIZED_CUTOFF"
    SAME_ENVELOPE_DDS = "SAME_ENVELOPE_DDS"
    SAME_TIMING_MECHANICAL_DISK = "SAME_TIMING_MECHANICAL_DISK"
    DUMMY_QUARTZ_OR_GLASS = "DUMMY_QUARTZ_OR_GLASS"


#: All eight, in declaration order. None is optional.
REQUIRED_CONTROLS: tuple[Control, ...] = tuple(Control)

CONTROL_REASONS: dict[Control, str] = {
    Control.STATIC_NONROTATING:
        "a DC or single-frequency non-rotating field of the same "
        "magnitude: removes rotation while keeping the field",
    Control.ONE_CHANNEL_ONLY:
        "drive one coil, ground the other: the field is linear, so any "
        "surviving cutoff-phase dependence is not about rotation",
    Control.REVERSED_ROTATION:
        "swap the channel phase to its reverse; a genuine rotation "
        "effect must change sign, and an artifact of the switch will not",
    Control.CONTINUOUS_DRIVE:
        "never cut the drive at all: separates the interruption from the "
        "rotation, since anything seen here needs neither",
    Control.PHASE_RANDOMIZED_CUTOFF:
        "cut at uniformly random phases: destroys any phase-locked "
        "structure while keeping the same number of interruptions and the "
        "same thermal load",
    Control.SAME_ENVELOPE_DDS:
        "synthesise the identical amplitude envelope from a direct "
        "digital synthesiser with no rotating field: isolates the "
        "envelope and the switching transient from the rotation",
    Control.SAME_TIMING_MECHANICAL_DISK:
        "reproduce the interruption timing with a mechanical chopper "
        "disk: a mechanical route to the same schedule, with different "
        "electromagnetic side effects",
    Control.DUMMY_QUARTZ_OR_GLASS:
        "replace the resonator with an inert glass or dummy blank: any "
        "signal that survives is instrumentation, not the specimen",
}


def _as_controls(ran: object) -> tuple[Control, ...]:
    """Coerce a declaration of controls to :class:`Control` members."""
    if ran is None:
        return ()
    if isinstance(ran, (Control, str)):
        ran = (ran,)
    try:
        items = list(ran)                                # type: ignore[arg-type]
    except TypeError:
        raise RotFieldError(
            f"cannot read {ran!r} as a collection of declared controls"
        ) from None
    out: list[Control] = []
    for item in items:
        if isinstance(item, Control):
            out.append(item)
            continue
        try:
            out.append(Control(str(item)))
        except ValueError:
            raise RotFieldError(
                f"{item!r} is not a declared control; the eight are "
                f"{', '.join(c.value for c in Control)}") from None
    return tuple(out)


def missing_controls(ran: object) -> tuple[Control, ...]:
    """Which of the eight are not in the declaration, in fixed order."""
    declared = set(_as_controls(ran))
    return tuple(c for c in REQUIRED_CONTROLS if c not in declared)


def refuse_result_without_controls(ran: object = ()) -> tuple[Control, ...]:
    """Refuse a result while any of the eight controls is undeclared.

    Returns the eight controls when all eight are declared -- and that is
    all it returns. Declaring the controls is a *precondition* for a
    result, not a result: no control has been run either, and
    :func:`refuse_bench_claim` still refuses every number.
    """
    missing = missing_controls(ran)
    if missing:
        why = "; ".join(f"{c.value}: {CONTROL_REASONS[c]}" for c in missing)
        raise RotFieldError(
            f"refused: {len(missing)} of {len(REQUIRED_CONTROLS)} declared "
            f"controls are missing ({', '.join(c.value for c in missing)}). "
            f"{why}. A cutoff-phase dependence is exactly the shape an "
            f"artifact of the switch, the envelope, the timing or the "
            f"thermal load takes, so a result without all eight nulls is "
            f"not a result about rotation. {VERDICT}")
    return REQUIRED_CONTROLS


def refuse_bench_claim(claim: str = "a cutoff-phase dependence was observed",
                       observable: Observable | str | None = None) -> None:
    """Refuse any measured reading from this experiment. Always raises.

    Nothing in this module has been driven, switched, cut or recorded.
    Every observable is ``BLOCKED_MISSING_DATA``, and a modelled waveform
    is a modelled waveform however faithfully it is plotted.
    """
    named = ""
    if observable is not None:
        name = getattr(observable, "value", observable)
        named = f" for {name}"
    raise RotFieldError(
        f"refused: {claim!r}{named} is a {BENCH_MEASUREMENT} claim and no "
        f"bench exists here. There is no coil, no electrode, no resonator, "
        f"no counter, no thermometer and no accelerometer in this "
        f"repository; all {len(REQUIRED_OBSERVABLES)} required observables "
        f"carry status {BLOCKED_MISSING_DATA}. What this module contains "
        f"is a drive model, an exact geometric identity, a cutoff sweep "
        f"specification and eight declared controls. {VERDICT}")


# --- (7) preregistration: frozen before any comparison --------------------

@dataclass(frozen=True)
class Prediction:
    """One preregistered statement, with the rule that will score it."""

    prediction_id: str
    statement: str
    success_criterion: str
    claim_class: str = PROSPECTIVE_PREDICTION

    def __post_init__(self) -> None:
        if self.claim_class not in CLAIM_CLASSES:
            raise RotFieldError(
                f"{self.claim_class!r} is not a declared claim class")
        for name in ("prediction_id", "statement", "success_criterion"):
            if not str(getattr(self, name)).strip():
                raise RotFieldError(
                    f"a prediction needs a non-empty {name}; a vague "
                    f"prediction cannot be scored and is therefore not one")

    def canonical(self) -> str:
        return "\x1f".join((self.prediction_id, self.claim_class,
                            self.statement, self.success_criterion))


@dataclass(frozen=True)
class PredictionSet:
    """A set of predictions frozen together, identified by its hash.

    The hash is over the canonical text of every prediction in order. It
    exists so that a later claim of "we predicted that" can be checked
    against the bytes rather than against a memory: change a criterion,
    add a prediction, or reorder the set, and the hash changes.
    """

    set_id: str
    predictions: tuple[Prediction, ...]

    def __post_init__(self) -> None:
        if not self.predictions:
            raise RotFieldError("an empty prediction set freezes nothing")
        ids = [p.prediction_id for p in self.predictions]
        if len(set(ids)) != len(ids):
            raise RotFieldError("prediction ids must be unique within a set")

    @property
    def prereg_hash(self) -> str:
        payload = "\x1e".join([self.set_id]
                              + [p.canonical() for p in self.predictions])
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def as_dict(self) -> dict:
        return {
            "set_id": self.set_id,
            "n_predictions": len(self.predictions),
            "prereg_hash": self.prereg_hash,
            "predictions": [
                {"prediction_id": p.prediction_id,
                 "statement": p.statement,
                 "success_criterion": p.success_criterion,
                 "claim_class": p.claim_class}
                for p in self.predictions],
            "outcome": "AWAITING_OUTCOME",
            "measured_here": MEASURED_HERE,
        }


FROZEN_PREDICTIONS = PredictionSet(
    "ROTATING_FIELD_INTERRUPTION_PREREG_A",
    (
        Prediction(
            "P_ROUNDTRIP_PHASE",
            "for the N=7 scalar geometry with L = v/(2*N*f), the "
            "round-trip acoustic phase at the 4096 Hz drive is exactly "
            "1/7 turn (360/7 = 51.428571... degrees), independently of "
            "the sound speed",
            "exact rational equality of roundtrip_phase_turns(v, f, 7) "
            "with Fraction(1, 7); no tolerance is permitted",
            EXACT_IDENTITY),
        Prediction(
            "P_SENSE_REVERSAL",
            "reversing the channel phase from p to -p reverses the "
            "rotation sense, so any cutoff-phase asymmetry attributable "
            "to rotation must change sign under the REVERSED_ROTATION "
            "control",
            "the sign of the ringdown asymmetry inverts within its own "
            "uncertainty; an asymmetry that does not invert is not about "
            "rotation"),
        Prediction(
            "P_LINEAR_NULL",
            "a linear (degenerate) drive with the same envelope, the "
            "same timing and the same delivered power produces no "
            "cutoff-phase dependence beyond the switching transient",
            "the linear-control sweep is flat within its uncertainty "
            "while the rotating sweep is not"),
        Prediction(
            "P_PERIODICITY",
            "any genuine cutoff-phase dependence is periodic in the "
            "cutoff phase with period exactly one turn",
            "the fitted fundamental period is one turn to within the "
            "sweep resolution, with no half-turn or third-turn component "
            "above the noise floor"),
        Prediction(
            "P_LEDGER_CLOSES",
            "the electromagnetic energy ledger closes at every cutoff "
            "phase once switching work is included, with no residual "
            "channel required",
            "E_unclosed is consistent with zero at every sweep point "
            "within the propagated interval; see r11.energyledger"),
    ),
)

#: The hash of the frozen set, computed before any comparison exists.
PREREGISTRATION_HASH = FROZEN_PREDICTIONS.prereg_hash


def preregistration() -> dict:
    """The frozen prediction set and its hash."""
    d = FROZEN_PREDICTIONS.as_dict()
    d["frozen_before_any_comparison"] = True
    d["outcomes_available_here"] = False
    d["claim_class"] = PROSPECTIVE_PREDICTION
    d["verdict"] = VERDICT
    return d


def refuse_unfrozen_scoring(prediction_set: object = None,
                            observed: object = None,
                            declared_hash: str | None = None) -> None:
    """Refuse to score anything against an unfrozen prediction set.

    Always raises, for two reasons and not one. First, there is nothing
    to score: no observable in this module has a value. Second, and more
    durably, a prediction set may only be scored against data that did
    not exist when the set was hashed -- so the scoring call must carry
    the hash that was recorded *beforehand*, and a set assembled or
    amended at scoring time is a description of the data wearing the
    grammar of a prediction.
    """
    given = getattr(prediction_set, "prereg_hash", declared_hash)
    seen = f" against {observed!r}" if observed is not None else ""
    raise RotFieldError(
        f"refused: scoring{seen} requires a prediction set frozen and "
        f"hashed before the data existed. The frozen set here is "
        f"{FROZEN_PREDICTIONS.set_id} with hash {PREREGISTRATION_HASH}, "
        f"and the hash offered was {given!r}. Even with a matching hash "
        f"there is nothing to score: every observable in this module is "
        f"{BLOCKED_MISSING_DATA}, no sweep has been run, and a prediction "
        f"set amended at scoring time describes the data rather than "
        f"predicting it. {VERDICT}")


# --- (8) report ------------------------------------------------------------

def rotfield_report() -> dict:
    """The standing statement of what this module is and is not."""
    sweep = cutoff_sweep()
    return {
        "what_this_is": (
            "a two-channel rotating-field interruption experiment, "
            "modelled and preregistered: a general drive with exact "
            "rational channel amplitudes and an exact rational channel "
            "phase, an exact round-trip phase identity for the N=7 "
            "scalar geometry, a cutoff-phase sweep over a full turn, "
            "eight declared controls, and a hashed prediction set"),
        "drive": {
            "balanced_quadrature":
                "Bx = B0*ax*cos(2*pi*f*t + phi0), "
                "By = B0*ay*sin(2*pi*f*t + phi0)",
            "general_form":
                "By = B0*ay*cos(2*pi*(f*t + phi0 - p)) for a rational "
                "channel phase p in turns; p = 1/4 recovers the sine",
            "circular": CIRCULAR_DRIVE.as_dict(),
            "linear_control": LINEAR_CONTROL_DRIVE.as_dict(),
            "senses": [s.value for s in RotationSense],
            "polarizations": [p.value for p in Polarization],
        },
        "exact_prediction": roundtrip_phase_prediction(),
        "cutoff_sweep": {
            "n_points": sweep["n_points"],
            "covers_full_turn": sweep["covers_full_turn"],
            "observables_per_point": sweep["observables_per_point"],
            "all_observables_blocked": sweep["all_observables_blocked"],
            "any_observable_recorded": sweep["any_observable_recorded"],
            "status": sweep["status"],
        },
        "required_observables": [r.as_dict() for r in REQUIRED_OBSERVABLES],
        "controls": {c.value: CONTROL_REASONS[c] for c in REQUIRED_CONTROLS},
        "n_controls_required": len(REQUIRED_CONTROLS),
        "controls_run": 0,
        "preregistration": preregistration(),
        "refusals": [
            "refuse_result_without_controls",
            "refuse_bench_claim",
            "refuse_unfrozen_scoring",
        ],
        "firewalls": [
            "a rotation sense is the sign of an exact rational, never a "
            "float comparison",
            "an equal-phase two-channel drive is LINEAR and has no "
            "rotation to test",
            "a modelled waveform is not a measurement",
            "a result requires all eight controls to be declared, and "
            "none has been run",
            "a prediction set is hashed before any comparison exists",
        ],
        "hardware_status": (
            "BLOCKED_MISSING_DATA - no coil, electrode, resonator, "
            "counter, thermometer or accelerometer exists here"),
        "claim_class": CLAIM_CLASS,
        "claim_classes": list(CLAIM_CLASSES),
        "evidence_class": "ANALYTIC_MODEL",
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "what_would_change_this": (
            "a built two-channel drive with logged coil current, an "
            "instrumented resonator with BVD fits before and after, the "
            "full cutoff sweep run against all eight declared controls, "
            "and scoring against this exact preregistration hash rather "
            "than against a prediction set written afterwards"),
        "what_this_does_not_say": (
            "It does not say any field was applied, that any drive was "
            "cut, that any ringdown was recorded, or that the cutoff "
            "phase matters -- no bench exists in this repository and "
            "every one of the required observables carries status "
            "BLOCKED_MISSING_DATA. It does not say the rotating case "
            "differs from the linear control, because neither has been "
            "run. The one exact statement here is geometric: with "
            "L = v/(2*N*f) the round-trip phase at the drive frequency "
            "is exactly 1/N turn, the sound speed cancelling identically, "
            "so 51.428571... degrees is a property of the definition and "
            "not a measurement of quartz, of a crystal, or of anything "
            "physical. It does not say the eight controls were run: they "
            "are declared, and declaring a control is not running it."),
        "verdict": VERDICT,
    }


__all__ = [
    "VERDICT", "CLAIM_CLASS", "CLAIM_CLASSES", "EXACT_IDENTITY",
    "PROSPECTIVE_PREDICTION", "BENCH_MEASUREMENT", "BLOCKED_MISSING_DATA",
    "MEASURED_HERE", "PHYSICAL_VALIDATION", "NUMERIC_SENSE_TOL",
    "RotFieldError",
    "RotationSense", "Polarization", "sense_sign", "rotation_sense",
    "polarization", "reversed_phase", "enclosed_area",
    "DRIVE_FREQUENCY", "RotatingDrive", "CIRCULAR_DRIVE",
    "LINEAR_CONTROL_DRIVE", "numeric_sense", "sense_consistency",
    "N7_SOUND_SPEED_M_PER_S", "N7_DRIVE_HZ", "N7_SEGMENTS",
    "N7_ROUNDTRIP_TURNS", "N7_ROUNDTRIP_DEGREES", "N7_SEGMENT_LENGTH_M",
    "segment_length_m", "roundtrip_time_s", "roundtrip_phase_turns",
    "roundtrip_phase_degrees", "roundtrip_phase_prediction",
    "Observable", "OBSERVABLE_UNITS", "OBSERVABLE_REASONS",
    "ObservableRecord", "observable_set", "REQUIRED_OBSERVABLES",
    "DEFAULT_SWEEP_POINTS", "cutoff_sweep",
    "Control", "REQUIRED_CONTROLS", "CONTROL_REASONS", "missing_controls",
    "refuse_result_without_controls", "refuse_bench_claim",
    "Prediction", "PredictionSet", "FROZEN_PREDICTIONS",
    "PREREGISTRATION_HASH", "preregistration", "refuse_unfrozen_scoring",
    "rotfield_report",
]
