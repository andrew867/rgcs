"""A12/A13/A15 — separated signal stages and the path/worldline schema.

The chain the whole programme hangs on:

    ideal -> commanded -> realized -> propagated -> observed
          -> reconstructed

Each stage is a distinct type. There is no implicit conversion:
moving down the chain requires the operation that physically happens
there (quantization, channel, measurement), and moving UP the chain is
estimation, which returns a ``Reconstructed`` carrying uncertainty and
alternatives — never a bare number.

Phase is stored wrapped (mod 2π) with an explicit cycle-count field
that may be UNKNOWN. An unwrapped phase is a derived claim requiring a
valid cycle count.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from . import ClaimBoundaryError

TWO_PI = 2.0 * math.pi

STAGES = ("IDEAL", "COMMANDED", "REALIZED", "PROPAGATED", "OBSERVED",
          "RECONSTRUCTED")

DOMAINS = ("ELECTRICAL", "MAGNETIC", "MECHANICAL", "ACOUSTIC",
           "OPTICAL", "THERMAL")


@dataclass(frozen=True)
class WrappedPhase:
    """Phase modulo 2π with explicit cycle knowledge."""
    phase_rad: float                    # in [0, 2π)
    cycle_count: int | None = None      # None = UNKNOWN

    def __post_init__(self):
        if not (0.0 <= self.phase_rad < TWO_PI):
            raise ValueError("wrapped phase must lie in [0, 2*pi)")

    @property
    def cycle_known(self) -> bool:
        return self.cycle_count is not None

    def unwrapped(self) -> float:
        if self.cycle_count is None:
            raise ClaimBoundaryError(
                "cannot unwrap: cycle count UNKNOWN. Absolute phase "
                "is modulo 2*pi without a counted history.")
        return self.cycle_count * TWO_PI + self.phase_rad


def wrap(phase_rad: float, cycles_known: bool = False) -> WrappedPhase:
    n = math.floor(phase_rad / TWO_PI)
    return WrappedPhase(phase_rad - n * TWO_PI,
                        n if cycles_known else None)


@dataclass(frozen=True)
class SignalState:
    """One tone in one domain at one stage."""
    stage: str
    domain: str
    frequency_hz: float
    amplitude: float
    phase: WrappedPhase
    polarization: str = ""
    uncertainty: dict = field(default_factory=dict)
    provenance: str = ""

    def __post_init__(self):
        if self.stage not in STAGES:
            raise ClaimBoundaryError(f"unknown stage {self.stage!r}")
        if self.domain not in DOMAINS:
            raise ClaimBoundaryError(f"unknown domain {self.domain!r}")


def command(ideal: SignalState, resolution_hz: float) -> SignalState:
    """IDEAL -> COMMANDED: quantize to what the synthesizer can ask
    for."""
    _expect(ideal, "IDEAL")
    f = round(ideal.frequency_hz / resolution_hz) * resolution_hz
    return SignalState("COMMANDED", ideal.domain, f, ideal.amplitude,
                       ideal.phase, ideal.polarization,
                       {"quantization_hz": abs(f - ideal.frequency_hz)},
                       ideal.provenance + " |> command")


def realize(commanded: SignalState, actual_scale: float,
            phase_error_rad: float = 0.0) -> SignalState:
    """COMMANDED -> REALIZED: hardware imperfection applied."""
    _expect(commanded, "COMMANDED")
    return SignalState(
        "REALIZED", commanded.domain,
        commanded.frequency_hz * actual_scale, commanded.amplitude,
        wrap(commanded.phase.phase_rad + phase_error_rad),
        commanded.polarization,
        {**commanded.uncertainty, "scale": actual_scale},
        commanded.provenance + " |> realize")


def propagate(realized: SignalState, delay_s: float,
              gain: float, doppler_scale: float = 1.0) -> SignalState:
    """REALIZED -> PROPAGATED through one path. The propagation phase
    2π·f·τ is huge, so the cycle count is LOST here unless the delay is
    known to a fraction of a cycle — which is the whole inverse
    problem. The propagated cycle count is therefore always UNKNOWN."""
    _expect(realized, "REALIZED")
    f = realized.frequency_hz * doppler_scale
    phi = realized.phase.phase_rad + TWO_PI * f * delay_s
    return SignalState(
        "PROPAGATED", realized.domain, f, realized.amplitude * gain,
        wrap(phi, cycles_known=False), realized.polarization,
        {**realized.uncertainty, "delay_s": delay_s},
        realized.provenance + " |> propagate")


def observe(propagated: SignalState, noise_amp: float,
            phase_noise_rad: float) -> SignalState:
    """PROPAGATED -> OBSERVED: the receiver's measurement, with noise
    entered into the uncertainty budget."""
    _expect(propagated, "PROPAGATED")
    return SignalState(
        "OBSERVED", propagated.domain, propagated.frequency_hz,
        propagated.amplitude, propagated.phase,
        propagated.polarization,
        {**propagated.uncertainty, "noise_amp": noise_amp,
         "phase_noise_rad": phase_noise_rad},
        propagated.provenance + " |> observe")


def _expect(s: SignalState, stage: str) -> None:
    if s.stage != stage:
        raise ClaimBoundaryError(
            f"stage violation: expected {stage}, got {s.stage}. "
            "Stages do not convert implicitly.")


@dataclass(frozen=True)
class Reconstructed:
    """The ONLY way estimates re-enter the chain: with uncertainty,
    alternatives, and an explicit identifiability verdict."""
    estimate: dict
    posterior_width: dict
    alternatives: tuple
    identifiable: bool
    refusal_reason: str = ""
    evidence_class: str = "NUMERICAL_SIMULATION"

    def __post_init__(self):
        if not self.identifiable and not self.refusal_reason:
            raise ClaimBoundaryError(
                "a non-identifiable reconstruction must carry its "
                "refusal reason")
