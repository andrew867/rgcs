"""A17 — RF/FPGA architecture and the safety gate.

The programme's arithmetic involves 2.45 GHz. Its hardware must not.
This module makes that structural: a plan that would radiate at
2.45 GHz cannot be approved by any code path here, whatever the
requester's intent.

Binding hardware rules (core/04):

- No open 2.45 GHz radiator. RF work, if any, uses legal modules in a
  shielded enclosure with attenuators, dummy loads, and measured
  leakage.
- Gen-0/Gen-1 electronics are low-voltage, current-limited, isolated.
- No human, animal, food, or biological exposure lane exists.
- Optical work is enclosed; no exposed beam at eye height.
- Stop on unexpected heating, arcing, fracture, smoke, eye hazard, or
  uncontrolled radiation.

The refusals are the feature. ``approve()`` returns a REFUSED verdict
with the rule cited, and there is deliberately no override flag —
following the v4.3 lifecycle precedent of a state machine with no force
flag.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction

from .units import exact

#: Frequencies above this need shielding review regardless of power.
RF_REVIEW_THRESHOLD_HZ = Fraction(1_000_000)     # 1 MHz

#: The band the programme will not radiate into.
ISM_2G4_LOW = Fraction(2_400_000_000)
ISM_2G4_HIGH = Fraction(2_500_000_000)


class SafetyRefusal(RuntimeError):
    """Raised when a plan violates a binding hardware rule."""


@dataclass(frozen=True)
class RFPlan:
    """A proposed electrical/RF configuration."""
    id: str
    frequency_hz: Fraction
    enclosure: str            # "OPEN" | "SHIELDED" | "DUMMY_LOAD"
    output: str               # "ANTENNA" | "COAX_DUMMY_LOAD" | "PIEZO" | "NONE"
    max_power_w: Fraction
    isolated_supply: bool
    mains_constructed: bool = False
    biological_target: bool = False
    leakage_measured: bool = False
    notes: str = ""


@dataclass(frozen=True)
class Verdict:
    plan_id: str
    approved: bool
    refusals: tuple = field(default=())
    conditions: tuple = field(default=())
    evidence_class: str = "ANALYTIC_MODEL"

    def to_dict(self) -> dict:
        return {"plan_id": self.plan_id, "approved": self.approved,
                "refusals": list(self.refusals),
                "conditions": list(self.conditions),
                "evidence_class": self.evidence_class,
                "note": "a software approval is a paperwork gate, not "
                        "a safety inspection; a qualified person still "
                        "signs off physical work"}


def in_2g4_band(f) -> bool:
    return ISM_2G4_LOW <= exact(f) <= ISM_2G4_HIGH


def approve(plan: RFPlan) -> Verdict:
    """Evaluate a plan against the binding rules. No override exists."""
    refusals, conditions = [], []
    f = exact(plan.frequency_hz)

    if in_2g4_band(f) and plan.output == "ANTENNA":
        refusals.append(
            "REFUSED: open 2.45 GHz radiation. The programme's "
            "2.45 GHz content is arithmetic only; no open radiator is "
            "authorized (core/04 hardware safety).")
    if in_2g4_band(f) and plan.enclosure == "OPEN":
        refusals.append(
            "REFUSED: 2.4-2.5 GHz work outside a shielded enclosure.")
    if in_2g4_band(f) and not plan.leakage_measured:
        refusals.append(
            "REFUSED: 2.4-2.5 GHz work without measured leakage.")
    if plan.biological_target:
        refusals.append(
            "REFUSED: no human, animal, food, or biological exposure "
            "lane exists in this programme.")
    if plan.mains_constructed:
        refusals.append(
            "REFUSED: improvised mains-powered apparatus. Mains work "
            "requires a qualified person and certified equipment.")
    if not plan.isolated_supply:
        refusals.append(
            "REFUSED: supply must be isolated and current-limited "
            "(Gen-0/Gen-1 rule).")
    if f >= RF_REVIEW_THRESHOLD_HZ and plan.enclosure == "OPEN":
        refusals.append(
            f"REFUSED: {f} Hz radiated from an open fixture requires "
            "shielding review.")
    if plan.max_power_w > Fraction(1):
        conditions.append(
            "power above 1 W: thermal monitoring and a documented stop "
            "condition are required")
    if plan.output == "PIEZO":
        conditions.append(
            "mechanical drive: keep electrical, mechanical, optical and "
            "thermal channels separately instrumented so a thermal "
            "artifact cannot be read as a resonance")
    conditions.append(
        "stop immediately on unexpected heating, arcing, fracture, "
        "smoke, eye hazard, or uncontrolled radiation")

    return Verdict(plan.id, not refusals, tuple(refusals),
                   tuple(conditions))


def require_approved(plan: RFPlan) -> Verdict:
    """Approve or raise. Use at any boundary that would otherwise
    proceed to a physical action."""
    v = approve(plan)
    if not v.approved:
        raise SafetyRefusal("; ".join(v.refusals))
    return v


#: The architecture the programme actually endorses for its low
#: frequency work: everything below 1 MHz, into a piezo or dummy load,
#: from an isolated low-voltage supply. No RF radiator anywhere.
ENDORSED_ARCHITECTURE = {
    "signal_source": "FPGA or MCU NCO with a binary reference clock "
                     "(exact tuning words for the binary target "
                     "family)",
    "output_stage": "current-limited driver into a piezo transducer or "
                    "a 50 ohm dummy load",
    "frequency_range_hz": "0.03 to 1e6",
    "rf_radiator": "NONE — the 2.45 GHz content of this programme is "
                   "arithmetic and stays arithmetic",
    "isolation": "isolated supply, opto-isolated control, no mains "
                 "construction",
    "instrumentation": "separate electrical, mechanical, optical and "
                       "thermal channels; a thermal artifact must not "
                       "be readable as a resonance",
    "evidence_class": "ANALYTIC_MODEL",
    "physical_status": "UNTESTED — no apparatus has been built or "
                       "operated",
}
