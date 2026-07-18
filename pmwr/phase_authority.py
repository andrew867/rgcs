"""A11/A16/A17/A24 — the phase authority, its synchronization state
machine, and the finite-Q phase-memory model.

A *phase authority* is the assembly that makes a phase claim
meaningful: oscillator + electronics + epoch + timescale +
synchronization method + cycle count + calibration + noise model.
Phase without an authority is a number without a reference.

The doctrine's central refusal: **a receiving crystal cannot be
assumed to share the phase of a transmitting crystal.** High Q extends
ringdown and selectivity; it does not preserve absolute phase forever,
and it never establishes a shared epoch by itself.

Finite-Q memory (A17): a ringdown decays as ``exp(-pi f t / Q)`` and
the usable phase memory is bounded by both amplitude decay and phase
diffusion. ``phase_memory_horizon`` reports when cycle count becomes
UNKNOWN; ``assert_not_perfect_memory`` is the refusal the adversarial
lane attacks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

from . import ClaimBoundaryError

#: Synchronization states (core/05). CYCLE_COUNT_UNKNOWN is a state,
#: not an error — losing count is normal physics.
SYNC_STATES = (
    "FREE_RINGDOWN", "FORCED_RESPONSE", "SELF_OSCILLATING",
    "FREQUENCY_LOCKED", "PHASE_LOCKED", "HOLDOVER", "REACQUIRED",
    "COHERENCE_LOST", "CYCLE_COUNT_UNKNOWN",
)

#: Legal transitions. There is no transition INTO PHASE_LOCKED except
#: through FREQUENCY_LOCKED, and no transition out of COHERENCE_LOST
#: except REACQUIRED — reacquisition never restores the old cycle
#: count. No force flag exists.
LEGAL_TRANSITIONS = {
    "FREE_RINGDOWN": ("FORCED_RESPONSE", "COHERENCE_LOST",
                      "CYCLE_COUNT_UNKNOWN"),
    "FORCED_RESPONSE": ("FREE_RINGDOWN", "SELF_OSCILLATING",
                        "FREQUENCY_LOCKED", "COHERENCE_LOST"),
    "SELF_OSCILLATING": ("FREQUENCY_LOCKED", "FREE_RINGDOWN",
                         "COHERENCE_LOST"),
    "FREQUENCY_LOCKED": ("PHASE_LOCKED", "HOLDOVER", "COHERENCE_LOST"),
    "PHASE_LOCKED": ("HOLDOVER", "FREQUENCY_LOCKED", "COHERENCE_LOST"),
    "HOLDOVER": ("REACQUIRED", "COHERENCE_LOST",
                 "CYCLE_COUNT_UNKNOWN"),
    "REACQUIRED": ("FREQUENCY_LOCKED",),
    "COHERENCE_LOST": ("REACQUIRED",),
    "CYCLE_COUNT_UNKNOWN": ("REACQUIRED", "COHERENCE_LOST"),
}

#: States in which an absolute cycle count may be asserted.
CYCLE_COUNT_VALID_STATES = ("PHASE_LOCKED",)


class SyncTransitionError(RuntimeError):
    pass


@dataclass(frozen=True)
class PhaseAuthority:
    """Everything a phase claim depends on. ``cycle_count=None`` means
    UNKNOWN, and unknown is the default — a count must be earned by a
    PHASE_LOCKED authority, never assumed."""
    id: str
    frequency_hz: float
    epoch_utc: str                      # ISO timestamp of phase zero
    timescale: str                      # "UTC" | "TAI" | "LOCAL_XO"
    sync_state: str = "FREE_RINGDOWN"
    cycle_count: int | None = None
    phase_rad_mod_2pi: float = 0.0
    coherence_time_s: float = 0.0
    calibration_ref: str = ""
    evidence_class: str = "ANALYTIC_MODEL"

    def __post_init__(self):
        if self.sync_state not in SYNC_STATES:
            raise SyncTransitionError(
                f"unknown sync state {self.sync_state!r}")
        if self.cycle_count is not None and \
                self.sync_state not in CYCLE_COUNT_VALID_STATES:
            raise ClaimBoundaryError(
                f"cycle_count asserted in state {self.sync_state}; an "
                "absolute count requires PHASE_LOCKED")

    def transition(self, new_state: str) -> "PhaseAuthority":
        if new_state not in LEGAL_TRANSITIONS.get(self.sync_state, ()):
            raise SyncTransitionError(
                f"{self.sync_state} -> {new_state} is not a legal "
                "transition (and there is no force flag)")
        # losing lock always surrenders the cycle count
        cc = self.cycle_count if new_state in CYCLE_COUNT_VALID_STATES \
            else None
        return replace(self, sync_state=new_state, cycle_count=cc)

    @property
    def shares_epoch_with(self):
        """Deliberately not implemented as an attribute of ONE
        authority: epoch sharing is a property of a PAIR plus a
        synchronization method. See ``epoch_comparison``."""
        raise ClaimBoundaryError(
            "epoch sharing is a pairwise property established by a "
            "synchronization method; one authority cannot declare it")


def epoch_comparison(a: PhaseAuthority, b: PhaseAuthority,
                     sync_method: str | None) -> dict:
    """Can phases from two authorities be compared at all?

    Without a synchronization method (common clock, transported
    reference, two-way link, or joint estimation) the answer is NO,
    whatever the two crystals' Q. This is the anti-'remote crystal
    shares my phase' gate.
    """
    if sync_method not in ("COMMON_CLOCK", "TRANSPORTED_REFERENCE",
                           "TWO_WAY_LINK", "JOINT_ESTIMATION"):
        return {"comparable": False,
                "reason": "no synchronization method: two authorities "
                          "with separate epochs have no defined phase "
                          "difference, regardless of Q",
                "evidence_class": "ANALYTIC_MODEL"}
    both_locked = (a.sync_state in ("PHASE_LOCKED", "FREQUENCY_LOCKED")
                   and b.sync_state in ("PHASE_LOCKED",
                                        "FREQUENCY_LOCKED"))
    return {"comparable": both_locked,
            "sync_method": sync_method,
            "reason": "" if both_locked else
            f"authorities in states {a.sync_state}/{b.sync_state} "
            "cannot support a phase comparison",
            "modulo": "2*pi unless both cycle counts are valid",
            "evidence_class": "ANALYTIC_MODEL"}


# --- finite-Q phase memory (A17) -----------------------------------------

@dataclass(frozen=True)
class RingdownModel:
    """Free decay of a resonator: a(t) = a0 exp(-pi f t / Q)."""
    frequency_hz: float
    q_factor: float
    amplitude_0: float = 1.0

    def __post_init__(self):
        if self.q_factor <= 0 or self.frequency_hz <= 0:
            raise ValueError("f and Q must be positive")
        if math.isinf(self.q_factor):
            raise ClaimBoundaryError(
                "infinite Q refused: a crystal is finite-coherence "
                "hardware, not an immortal phase oracle "
                "(firewall PERFECT_ABSOLUTE_PHASE)")

    @property
    def tau_s(self) -> float:
        """Amplitude 1/e time."""
        return self.q_factor / (math.pi * self.frequency_hz)

    def amplitude(self, t_s: float) -> float:
        return self.amplitude_0 * math.exp(-t_s / self.tau_s)

    def cycles_to_1e(self) -> float:
        """Cycles elapsed in one amplitude decay constant = Q/pi."""
        return self.q_factor / math.pi


def phase_memory_horizon(model: RingdownModel,
                         fractional_frequency_error: float,
                         detection_floor: float = 1e-3) -> dict:
    """When does the assembly stop knowing its cycle count?

    Two independent clocks run out:

    - amplitude: below ``detection_floor`` the signal is gone;
    - phase diffusion: a fractional frequency error y accumulates
      phase error 2*pi*f*y*t; when that reaches pi the cycle count is
      ambiguous (off-by-one is as likely as not).

    The horizon is the EARLIER of the two, and after it the honest
    state is CYCLE_COUNT_UNKNOWN.
    """
    if fractional_frequency_error <= 0:
        raise ClaimBoundaryError(
            "a zero frequency-error model is the perfect-memory claim "
            "in disguise; supply the oscillator's real stability")
    t_amp = -model.tau_s * math.log(detection_floor / model.amplitude_0)
    t_phase = 0.5 / (model.frequency_hz * fractional_frequency_error)
    horizon = min(t_amp, t_phase)
    return {
        "amplitude_horizon_s": t_amp,
        "phase_ambiguity_horizon_s": t_phase,
        "phase_memory_horizon_s": horizon,
        "limited_by": "amplitude" if t_amp < t_phase else
                      "phase_diffusion",
        "cycles_at_horizon": horizon * model.frequency_hz,
        "after_horizon_state": "CYCLE_COUNT_UNKNOWN",
        "evidence_class": "ANALYTIC_MODEL",
        "claim_boundary": "finite memory; absolute phase is not "
                          "preserved indefinitely",
    }


def assert_not_perfect_memory(claimed_horizon_s: float,
                              model: RingdownModel,
                              fractional_frequency_error: float) -> None:
    """Refuse any claim of phase memory beyond the physical horizon."""
    h = phase_memory_horizon(model, fractional_frequency_error)
    if claimed_horizon_s > h["phase_memory_horizon_s"]:
        raise ClaimBoundaryError(
            f"claimed phase memory {claimed_horizon_s} s exceeds the "
            f"assembly's horizon {h['phase_memory_horizon_s']:.3g} s "
            f"({h['limited_by']}); firewall PERFECT_ABSOLUTE_PHASE")


def holdover_drift(fractional_offset: float, drift_per_s: float,
                   duration_s: float, frequency_hz: float) -> dict:
    """Accumulated time and phase error in HOLDOVER."""
    time_err = fractional_offset * duration_s + \
        0.5 * drift_per_s * duration_s ** 2
    cycles_err = time_err * frequency_hz
    return {
        "duration_s": duration_s,
        "time_error_s": time_err,
        "cycle_error": cycles_err,
        "cycle_count_still_valid": abs(cycles_err) < 0.5,
        "evidence_class": "ANALYTIC_MODEL",
    }
