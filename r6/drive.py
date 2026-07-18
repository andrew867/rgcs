"""P02 — drive programme compiler for the dual-helical coil.

Compiles a requested slot programme into a *realized* waveform under
declared amplifier limits, and builds the energy-matched control that
any claim about "alternating structure" has to beat.

    NO COIL HAS BEEN WOUND and no current has ever been passed through
    one. Every waveform here is produced by a declared model of a
    declared amplifier. Nothing in this module is bench data; every
    returned object carries ``evidence_class = "SYNTHETIC_MODEL"``.

Why REQUESTED and REALIZED are separate
---------------------------------------

The source specifies an idealised square alternation (copper
``1-0-1-0-1-0``, silver ``0-1-0-1-0-1``, "both pulses equal in
intensity"). No amplifier delivers that. A real driver has a finite
slew rate and a finite compliance, so into an inductive load the
current edges are ramps, not steps, and the peak may clip. If the
programme only ever recorded what it asked for, a later analysis would
attribute an effect to a waveform that was never applied.

:func:`compile_program` therefore returns both, plus the worst-case
deviation, and refuses to let the two be confused: they are different
fields with different names on the same object.

Why the energy-matched control is mandatory
-------------------------------------------

Claim R6-C-002 is a claim about *structure* ("if you alternate the
structure of the two pulses it will empower the torsion field"). A
comparison against no drive, or against a weaker drive, tests total
energy and not structure. :func:`matched_energy_control` returns a
non-alternating programme delivering the same total joules into the
same load, so that structure is the only thing that varies. Without
it, any positive result is uninterpretable — this is the v4.6 lesson
about granularity-matched nulls applied to waveforms.

R6 has no instrument for "torsion field". This module compiles drive
programmes; it does not measure whatever the source believes they
empower.

Units: SI throughout. Currents ampere, times second, energies joule,
resistance ohm, slew rate ampere per second.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, asdict
from typing import Literal

#: Nothing in this module is measurement.
EVIDENCE_CLASS = "SYNTHETIC_MODEL"

DriveMode = Literal[
    "SINGLE",                    # one winding driven, the other open
    "PARALLEL",                  # both windings driven in phase
    "SERIES",                    # one current through both in series
    "ALTERNATING_DIFFERENTIAL",  # the source's interleaved programme
]

#: All four connection configurations. The source presents three and
#: selects the separated/alternating one; the fourth (SINGLE) is kept
#: because it is the natural control for "does the second winding do
#: anything at all".
DRIVE_MODES: tuple[str, ...] = (
    "SINGLE",
    "PARALLEL",
    "SERIES",
    "ALTERNATING_DIFFERENTIAL",
)

MODE_DESCRIPTIONS = {
    "SINGLE": ("one winding energised, the other left open; control for "
               "whether the second winding contributes at all"),
    "PARALLEL": ("both windings energised in phase from one source; "
                 "pure common mode, no differential component"),
    "SERIES": ("a single current path through both windings; currents "
               "are identical by construction and cannot be alternated"),
    "ALTERNATING_DIFFERENTIAL": (
        "separated windings on independent drivers, interleaved "
        "1-0-1-0 / 0-1-0-1; the configuration the source selects "
        "(claim R6-C-002)"),
}


class DriveError(ValueError):
    """Raised when a drive programme is not realizable as declared."""


# --------------------------------------------------------------------
# Amplifier limits
# --------------------------------------------------------------------

@dataclass(frozen=True)
class DriveLimits:
    """Declared driver limits.

    Units
    -----
    max_amplitude_a : A, hard clip on the magnitude of either channel
    slew_rate_a_per_s : A/s, maximum |di/dt| the driver can produce
    sample_rate_hz : Hz, the rate at which the realized waveform is
        evaluated. This is a model resolution, not hardware.
    load_resistance_ohm : ohm, series resistance used for energy
        accounting. Purely resistive: the reactive energy stored in the
        winding inductance is returned to the source over a cycle and
        so does not enter the dissipated total.
    """

    max_amplitude_a: float = 5.0
    slew_rate_a_per_s: float = 1.0e4
    sample_rate_hz: float = 1.0e5
    load_resistance_ohm: float = 1.0

    def __post_init__(self) -> None:
        for name in ("max_amplitude_a", "slew_rate_a_per_s",
                     "sample_rate_hz", "load_resistance_ohm"):
            v = getattr(self, name)
            if not math.isfinite(v) or v <= 0.0:
                raise DriveError(
                    f"{name} must be finite and positive, got {v!r}")

    def as_record(self) -> dict:
        d = asdict(self)
        d["units"] = {"max_amplitude_a": "A",
                      "slew_rate_a_per_s": "A/s",
                      "sample_rate_hz": "Hz",
                      "load_resistance_ohm": "ohm"}
        d["evidence_class"] = EVIDENCE_CLASS
        return d


#: Deliberately tight defaults: with 5 A slots and a 1 ms slot, a
#: 1e4 A/s driver needs 0.5 ms to reach amplitude, so REALIZED differs
#: from REQUESTED by construction and cannot be forgotten.
DEFAULT_LIMITS = DriveLimits()


# --------------------------------------------------------------------
# Programme
# --------------------------------------------------------------------

@dataclass(frozen=True)
class DriveProgram:
    """A requested slot programme for the two windings.

    Units
    -----
    slots : tuple of (i1, i2) in amperes, one pair per slot
    slot_duration_s : s, duration of every slot
    repetition : dimensionless count of times the slot sequence repeats
    """

    mode: str
    slots: tuple[tuple[float, float], ...]
    slot_duration_s: float
    repetition: int = 1
    label: str = ""

    def __post_init__(self) -> None:
        if self.mode not in DRIVE_MODES:
            raise DriveError(
                f"unknown drive mode {self.mode!r}; expected one of "
                f"{DRIVE_MODES}")
        if not self.slots:
            raise DriveError("a drive programme needs at least one slot")
        for k, s in enumerate(self.slots):
            if len(s) != 2:
                raise DriveError(
                    f"slot {k} must be a (i1, i2) pair in amperes")
            for v in s:
                if not math.isfinite(float(v)):
                    raise DriveError(
                        f"slot {k} current {v!r} is not a finite ampere "
                        "value")
        if not math.isfinite(self.slot_duration_s) or \
                self.slot_duration_s <= 0.0:
            raise DriveError(
                f"slot_duration_s must be finite and positive, got "
                f"{self.slot_duration_s!r}")
        if not isinstance(self.repetition, int) or self.repetition < 1:
            raise DriveError(
                f"repetition must be an integer >= 1, got "
                f"{self.repetition!r}")
        if self.mode == "SERIES":
            for k, (i1, i2) in enumerate(self.slots):
                if i1 != i2:
                    raise DriveError(
                        f"SERIES mode carries one current through both "
                        f"windings, but slot {k} requests {i1} A and "
                        f"{i2} A. Unequal currents require the separated "
                        "configuration.")
        if self.mode == "SINGLE":
            for k, (i1, i2) in enumerate(self.slots):
                if i2 != 0.0:
                    raise DriveError(
                        f"SINGLE mode leaves the second winding open, "
                        f"but slot {k} requests {i2} A in it")

    # -- derived -----------------------------------------------------

    @property
    def n_slots(self) -> int:
        """Slots in one repetition (dimensionless)."""
        return len(self.slots)

    @property
    def total_slots(self) -> int:
        return len(self.slots) * self.repetition

    @property
    def total_duration_s(self) -> float:
        return self.slot_duration_s * self.total_slots

    def expanded_slots(self) -> tuple[tuple[float, float], ...]:
        """The full slot sequence including repetitions."""
        return tuple(self.slots) * self.repetition

    def as_record(self) -> dict:
        return {
            "mode": self.mode,
            "mode_description": MODE_DESCRIPTIONS[self.mode],
            "slots_a": [list(s) for s in self.slots],
            "slot_duration_s": self.slot_duration_s,
            "repetition": self.repetition,
            "label": self.label,
            "n_slots": self.n_slots,
            "total_slots": self.total_slots,
            "total_duration_s": self.total_duration_s,
            "stage": "REQUESTED",
            "units": {"slots_a": "A", "slot_duration_s": "s",
                      "repetition": "1", "total_duration_s": "s"},
            "evidence_class": EVIDENCE_CLASS,
            "note": "requested programme only; no coil has been wound",
        }


# --------------------------------------------------------------------
# Source programme
# --------------------------------------------------------------------

def alternating_program(n_slots: int = 6, amplitude_a: float = 5.0,
                        slot_duration_s: float = 1.0e-3,
                        repetition: int = 1) -> DriveProgram:
    """The source's programme: copper 1-0-1-0..., silver 0-1-0-1...

    Winding 1 is energised on even slots, winding 2 on odd slots, both
    at ``amplitude_a`` — "both pulses should be equal in intensity".

    Units: amplitude A, slot duration s, counts dimensionless.
    """
    if not isinstance(n_slots, int) or n_slots < 1:
        raise DriveError(f"n_slots must be an integer >= 1, got {n_slots!r}")
    if not math.isfinite(amplitude_a) or amplitude_a <= 0.0:
        raise DriveError(
            f"amplitude_a must be finite and positive, got {amplitude_a!r}")
    slots = tuple((amplitude_a, 0.0) if k % 2 == 0 else (0.0, amplitude_a)
                  for k in range(n_slots))
    return DriveProgram(
        mode="ALTERNATING_DIFFERENTIAL",
        slots=slots,
        slot_duration_s=slot_duration_s,
        repetition=repetition,
        label="source alternating programme (claim R6-C-002)",
    )


# --------------------------------------------------------------------
# Energy and duty
# --------------------------------------------------------------------

def energy_per_slot(program: DriveProgram,
                    limits: DriveLimits = DEFAULT_LIMITS) -> dict:
    """Resistively dissipated energy per slot, in joules.

    ``E_k = (i1_k^2 + i2_k^2) * R * T`` for the separated
    configurations. In SERIES the same current traverses both windings,
    so the resistance seen is ``2R`` and the same expression applies
    with ``i1 == i2``.

    The winding inductance stores and returns energy rather than
    dissipating it, so it does not appear. This makes the figure a
    *dissipated* energy, which is the right invariant to hold fixed
    across a structural comparison; it is not the instantaneous stored
    energy and must not be quoted as such.

    Units: joule per slot; total in joule.
    """
    r = limits.load_resistance_ohm
    t = program.slot_duration_s
    per_slot = [(float(i1) ** 2 + float(i2) ** 2) * r * t
                for i1, i2 in program.slots]
    total = sum(per_slot) * program.repetition
    return {
        "per_slot_j": per_slot,
        "per_repetition_j": sum(per_slot),
        "total_energy_j": total,
        "mean_power_w": (total / program.total_duration_s
                         if program.total_duration_s > 0 else 0.0),
        "load_resistance_ohm": r,
        "slot_duration_s": t,
        "mode": program.mode,
        "stage": "REQUESTED",
        "model": "resistive dissipation only; inductive storage excluded",
        "units": {"per_slot_j": "J", "per_repetition_j": "J",
                  "total_energy_j": "J", "mean_power_w": "W",
                  "load_resistance_ohm": "ohm", "slot_duration_s": "s"},
        "evidence_class": EVIDENCE_CLASS,
    }


def duty_cycle(program: DriveProgram, threshold_a: float = 0.0) -> dict:
    """Fraction of slots in which each winding carries current.

    ``threshold_a`` (A) is the magnitude above which a slot counts as
    active; the default 0 A counts any non-zero request.

    Units: all fractions dimensionless.
    """
    if not math.isfinite(threshold_a) or threshold_a < 0.0:
        raise DriveError("threshold_a must be a finite non-negative current")
    n = program.n_slots
    a1 = sum(1 for i1, _ in program.slots if abs(i1) > threshold_a)
    a2 = sum(1 for _, i2 in program.slots if abs(i2) > threshold_a)
    both = sum(1 for i1, i2 in program.slots
               if abs(i1) > threshold_a and abs(i2) > threshold_a)
    either = sum(1 for i1, i2 in program.slots
                 if abs(i1) > threshold_a or abs(i2) > threshold_a)
    return {
        "winding_1_duty": a1 / n,
        "winding_2_duty": a2 / n,
        "simultaneous_duty": both / n,
        "any_winding_duty": either / n,
        "n_slots": n,
        "threshold_a": threshold_a,
        "mode": program.mode,
        "stage": "REQUESTED",
        "units": {"winding_1_duty": "1", "winding_2_duty": "1",
                  "simultaneous_duty": "1", "any_winding_duty": "1",
                  "threshold_a": "A"},
        "evidence_class": EVIDENCE_CLASS,
    }


# --------------------------------------------------------------------
# Compilation: REQUESTED -> REALIZED
# --------------------------------------------------------------------

@dataclass(frozen=True)
class CompiledProgram:
    """A compiled waveform holding REQUESTED and REALIZED side by side.

    Units
    -----
    times_s               : s, sample instants from 0
    requested_a           : list of (i1, i2) in A, the ideal square slots
    realized_a            : list of (i1, i2) in A, after slew and clip
    max_deviation_a       : A, worst |realized - requested| over all
                            samples and both channels
    requested_energy_j /
    realized_energy_j     : J, resistively dissipated
    """

    program: DriveProgram
    limits: DriveLimits
    times_s: tuple[float, ...]
    requested_a: tuple[tuple[float, float], ...]
    realized_a: tuple[tuple[float, float], ...]
    max_deviation_a: float
    deviation_channel: int
    clipped: bool
    slew_limited: bool
    requested_energy_j: float
    realized_energy_j: float

    @property
    def energy_shortfall_fraction(self) -> float:
        """(requested - realized) / requested, dimensionless."""
        if self.requested_energy_j == 0.0:
            return 0.0
        return ((self.requested_energy_j - self.realized_energy_j)
                / self.requested_energy_j)

    def as_record(self) -> dict:
        return {
            "drive_mode": self.program.mode,
            "mode_description": MODE_DESCRIPTIONS[self.program.mode],
            "label": self.program.label,
            "n_samples": len(self.times_s),
            "sample_period_s": 1.0 / self.limits.sample_rate_hz,
            "requested": {
                "stage": "REQUESTED",
                "slots_a": [list(s) for s in self.program.slots],
                "energy_j": self.requested_energy_j,
                "peak_a": max((max(abs(a), abs(b))
                               for a, b in self.requested_a), default=0.0),
            },
            "realized": {
                "stage": "REALIZED",
                "energy_j": self.realized_energy_j,
                "peak_a": max((max(abs(a), abs(b))
                               for a, b in self.realized_a), default=0.0),
                "clipped": self.clipped,
                "slew_limited": self.slew_limited,
            },
            "max_deviation_a": self.max_deviation_a,
            "deviation_channel": self.deviation_channel,
            "energy_shortfall_fraction": self.energy_shortfall_fraction,
            "limits": self.limits.as_record(),
            "units": {"times_s": "s", "requested_a": "A",
                      "realized_a": "A", "max_deviation_a": "A",
                      "energy_j": "J",
                      "energy_shortfall_fraction": "1"},
            "evidence_class": EVIDENCE_CLASS,
            "note": ("REQUESTED is what was asked for; REALIZED is what "
                     "the declared amplifier model can produce. Neither "
                     "is a measurement: no coil has been wound."),
        }


def compile_program(spec: DriveProgram,
                    limits: DriveLimits = DEFAULT_LIMITS
                    ) -> CompiledProgram:
    """Realize a requested programme under slew-rate and clip limits.

    The realized channel current tracks the requested square slot value
    but may change by at most ``slew_rate_a_per_s / sample_rate_hz``
    amperes per sample, and is clipped to +/- ``max_amplitude_a``.

    Consequence, and the reason this function exists: for any finite
    slew rate the realized waveform differs from the requested one at
    every edge, so ``max_deviation_a > 0`` whenever the programme
    contains a transition. A programme that reported only its request
    would be reporting a waveform that was never applied.

    Deterministic: no randomness, no jitter model. A real driver has
    both; this model does not, and the absence is a limitation, not a
    claim of precision.

    Units: as documented on :class:`CompiledProgram`.
    """
    if not isinstance(spec, DriveProgram):
        raise DriveError("spec must be a DriveProgram")
    dt = 1.0 / limits.sample_rate_hz
    max_step = limits.slew_rate_a_per_s * dt
    slots = spec.expanded_slots()
    n_per_slot = int(round(spec.slot_duration_s * limits.sample_rate_hz))
    if n_per_slot < 1:
        raise DriveError(
            f"sample_rate_hz {limits.sample_rate_hz} Hz gives fewer than "
            f"one sample per {spec.slot_duration_s} s slot; the realized "
            "waveform would be meaningless")

    times: list[float] = []
    requested: list[tuple[float, float]] = []
    realized: list[tuple[float, float]] = []
    cur = [0.0, 0.0]
    max_dev = 0.0
    dev_ch = 0
    clipped = False
    slew_limited = False

    idx = 0
    for i1, i2 in slots:
        target = (float(i1), float(i2))
        for _ in range(n_per_slot):
            out = []
            for ch in (0, 1):
                want = target[ch]
                delta = want - cur[ch]
                if abs(delta) > max_step:
                    slew_limited = True
                    delta = max_step if delta > 0.0 else -max_step
                v = cur[ch] + delta
                if abs(v) > limits.max_amplitude_a:
                    clipped = True
                    v = math.copysign(limits.max_amplitude_a, v)
                cur[ch] = v
                out.append(v)
            for ch in (0, 1):
                d = abs(out[ch] - target[ch])
                if d > max_dev:
                    max_dev = d
                    dev_ch = ch + 1
            times.append(idx * dt)
            requested.append(target)
            realized.append((out[0], out[1]))
            idx += 1

    r = limits.load_resistance_ohm
    req_e = sum((a * a + b * b) for a, b in requested) * r * dt
    real_e = sum((a * a + b * b) for a, b in realized) * r * dt

    return CompiledProgram(
        program=spec,
        limits=limits,
        times_s=tuple(times),
        requested_a=tuple(requested),
        realized_a=tuple(realized),
        max_deviation_a=max_dev,
        deviation_channel=dev_ch,
        clipped=clipped,
        slew_limited=slew_limited,
        requested_energy_j=req_e,
        realized_energy_j=real_e,
    )


# --------------------------------------------------------------------
# The energy-matched null
# --------------------------------------------------------------------

def matched_energy_control(program: DriveProgram,
                           limits: DriveLimits = DEFAULT_LIMITS,
                           mode: str = "PARALLEL") -> dict:
    """A non-alternating programme delivering the SAME total energy.

    Claim R6-C-002 is about *structure*, not amplitude. The control
    therefore holds the resistively dissipated energy, the slot count,
    the slot duration and the load fixed, and changes only the
    structure: instead of alternating, both windings are driven in
    every slot at a constant amplitude

        i_control = sqrt(E_total / (2 * n_slots * R * T))

    For the source's programme (one winding at A per slot) this gives
    exactly ``A / sqrt(2)`` in both windings — the same joules, no
    alternation, zero differential component.

    Under ``mode="SINGLE"`` the control instead drives one winding
    continuously at ``sqrt(E_total / (n_slots * R * T))``, putting the
    same joules through a single channel. For the source's programme
    that is exactly ``A``: same energy, same peak, no alternation.
    SERIES is refused as a control because its currents
    are equal by construction, which makes it a re-parameterisation of
    PARALLEL rather than an independent structure.

    Returns a dict containing the control ``DriveProgram`` under
    ``"program"`` plus the energy check.

    Units: currents A, energies J, times s.
    """
    if mode not in DRIVE_MODES:
        raise DriveError(f"unknown control mode {mode!r}")
    if mode == "SERIES":
        raise DriveError(
            "SERIES is not an independent control structure: its two "
            "currents are equal by construction, so it duplicates "
            "PARALLEL. Use PARALLEL or SINGLE.")
    if mode == "ALTERNATING_DIFFERENTIAL":
        raise DriveError(
            "the control must not itself be the alternating structure "
            "under test")

    e = energy_per_slot(program, limits)
    total = e["total_energy_j"]
    n = program.n_slots
    r = limits.load_resistance_ohm
    t = program.slot_duration_s
    reps = program.repetition

    channels = 2 if mode == "PARALLEL" else 1
    denom = channels * n * reps * r * t
    if denom <= 0.0:
        raise DriveError("degenerate control: zero denominator")
    amp = math.sqrt(total / denom) if total > 0.0 else 0.0

    slots = tuple((amp, amp) if channels == 2 else (amp, 0.0)
                  for _ in range(n))
    control = DriveProgram(
        mode=mode,
        slots=slots,
        slot_duration_s=t,
        repetition=reps,
        label=f"energy-matched control for {program.label or program.mode}",
    )
    ce = energy_per_slot(control, limits)
    ctrl_total = ce["total_energy_j"]
    mismatch = (abs(ctrl_total - total) / total) if total > 0.0 else 0.0

    return {
        "program": control,
        "control_record": control.as_record(),
        "drive_mode": mode,
        "control_amplitude_a": amp,
        "matched_quantity": "resistively dissipated energy",
        "source_total_energy_j": total,
        "control_total_energy_j": ctrl_total,
        "energy_mismatch_fraction": mismatch,
        "energy_matched": mismatch < 1.0e-12,
        "held_fixed": ("total dissipated energy, slot count, slot "
                       "duration, repetition, load resistance"),
        "varied": "temporal structure (alternating vs simultaneous)",
        "stage": "REQUESTED",
        "why_required": (
            "claim R6-C-002 asserts an effect of alternating structure; "
            "a comparison against a weaker or absent drive would test "
            "amplitude instead. Energy is held constant so that "
            "structure is the only free variable."),
        "limitation": (
            "energy matching is on the REQUESTED programme. Slew and "
            "clip limits act differently on the two structures, so "
            "compile both and compare realized energies before running "
            "anything."),
        "units": {"control_amplitude_a": "A",
                  "source_total_energy_j": "J",
                  "control_total_energy_j": "J",
                  "energy_mismatch_fraction": "1"},
        "evidence_class": EVIDENCE_CLASS,
        "note": "no coil has been wound; this control has not been run",
    }


__all__ = [
    "EVIDENCE_CLASS",
    "DriveMode",
    "DRIVE_MODES",
    "MODE_DESCRIPTIONS",
    "DriveError",
    "DriveLimits",
    "DEFAULT_LIMITS",
    "DriveProgram",
    "CompiledProgram",
    "alternating_program",
    "compile_program",
    "energy_per_slot",
    "duty_cycle",
    "matched_energy_control",
]
