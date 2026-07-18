"""A49-A54 — bench architecture, safety plan, characterization and
benchmark protocols, and the honest stop.

Everything here is a PLAN. The stop matrix (core/13) decides what may
proceed: the programme may continue in simulation with any physical
gate blocked, but may never synthesize a physical verdict, and A54
requires an explicit blocker where one exists.

The staged architecture deliberately puts the cheapest disqualifying
test first: a classical four-domain cell proves the CODEC end-to-end
without any spin claim, so a codec failure is caught before anyone
buys cryogenics.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from . import PHYSICAL_GATES, PhysicalGateBlocked
from .platforms import REGISTRY, stop_matrix_report
from cspc.experiments import Preregistration


@dataclass(frozen=True)
class BenchStage:
    id: str
    goal: str
    platform: str
    hardware: tuple
    disqualifies_if: str
    safety_gates: tuple
    status: str = "NOT BUILT"


STAGES = (
    BenchStage(
        "S0-CODEC-ON-CLASSICAL",
        "prove the codec end-to-end on a four-state CLASSICAL cell "
        "with no spin claim whatsoever",
        "CLASSICAL_FOUR_DOMAIN",
        ("4-level resistive/magnetic cell array", "microcontroller",
         "isolated low-voltage supply"),
        "if the codec cannot survive a real 4-symbol channel here, no "
        "spin platform will rescue it",
        ("isolated supply", "no mains construction",
         "current limiting")),
    BenchStage(
        "S1-MATERIAL-CHARACTERIZATION",
        "identify and characterize a candidate spin-active defect "
        "before any memory claim",
        "SIC_V_SI_SPIN_3_2",
        ("EPR/ODMR bench", "optical excitation", "static field coil",
         "photodetector"),
        "no identified defect with a reproducible resonance means the "
        "platform is not qualified — stop",
        ("enclosed optical path", "no eye-height beam",
         "wavelength-appropriate eyewear", "RF field limits",
         "cryogen handling if used")),
    BenchStage(
        "S2-FOUR-STATE-WRITE-READ",
        "demonstrate intentional preparation and discrimination of "
        "four levels, with sign resolution",
        "SIC_V_SI_SPIN_3_2",
        ("pulse generator", "microwave source", "lock-in/photon "
         "counter", "shielded enclosure"),
        "pair-degenerate readout without sign resolution means the "
        "four-state manifold is unproven — stop",
        ("RF exposure limits", "shielded enclosure",
         "interlocked optics")),
    BenchStage(
        "S3-RETENTION-ENDURANCE",
        "measure T1, retention, crosstalk and endurance",
        "SIC_V_SI_SPIN_3_2",
        ("temperature control", "long-run automation"),
        "unmeasured retention blocks any memory claim",
        ("thermal monitoring", "unattended-run limits")),
    BenchStage(
        "S4-COMPRESSION-ON-HARDWARE",
        "run the codec over the physical channel end to end",
        "SIC_V_SI_SPIN_3_2",
        ("full S1-S3 stack",),
        "compression-on-hardware requires standalone memory success "
        "first (R48); without S2 and S3 it may not run",
        ("all prior gates",)),
)


def bench_readiness() -> dict:
    """A54: the honest stop. Which stages could start today?"""
    rows = []
    for s in STAGES:
        gates = stop_matrix_report(s.platform)["open_gates"]
        blocked_by_hardware = True          # no apparatus exists
        rows.append({
            "stage": s.id, "platform": s.platform,
            "open_platform_gates": gates,
            "hardware_present": not blocked_by_hardware,
            "status": "BLOCKED_NO_APPARATUS",
            "disqualifies_if": s.disqualifies_if,
        })
    return {
        "stages": rows,
        "any_stage_runnable_now": False,
        "blocker": "HARDWARE_SAFETY_BLOCKED / no apparatus exists: "
                   "every stage requires instruments this programme "
                   "does not have. Simulation may continue; a physical "
                   "verdict may not be emitted.",
        "s4_precondition":
            "compression-on-hardware (S4) is gated on standalone "
            "memory success in S2 and S3 (R48)",
        "physical_status": "UNTESTED",
        "evidence_class": "ANALYTIC_MODEL",
    }


def four_state_write_read_protocol() -> Preregistration:
    """A52: the preregistered four-state trial (reusing the v4.6
    preregistration type)."""
    return Preregistration(
        id="R4-BENCH-4STATE",
        question="Can four spin levels be intentionally prepared and "
                 "discriminated on held-out trials above the "
                 "pair-degenerate chance rate?",
        target_hz=(35_000_000,),
        control_hz=(30_000_000, 40_000_000),
        n_per_condition=200,
        randomisation="target level order randomised per block from a "
                      "seeded permutation fixed before the first run",
        blinding="analyst blind to the prepared level; mapping sealed "
                 "until the analysis is locked",
        stopping_rule="fixed N of 200 per level; no interim peeking, "
                      "no extension on a promising trend",
        primary_outcome="4x4 confusion matrix on HELD-OUT trials; "
                        "mean diagonal fidelity with CI",
        analysis="preregistered: fidelity vs the 25% chance rate AND "
                 "vs the 50% pair-degenerate rate, since resolving "
                 "|m_s| alone is not four-state discrimination",
        correction="Holm-Bonferroni across levels",
        safety=("enclosed optics, no eye-height beam",
                "RF exposure limits with shielded enclosure",
                "isolated low-voltage drive",
                "stop on unexpected heating or arcing"),
    )


def material_characterization_protocol() -> Preregistration:
    """A51: identify the defect before claiming anything about it."""
    return Preregistration(
        id="R4-BENCH-MATERIAL",
        question="Does the specimen contain a spin-active defect with "
                 "a reproducible, assignable resonance?",
        target_hz=(35_000_000,),
        control_hz=(0,),
        n_per_condition=20,
        randomisation="field sweep direction alternated, seeded",
        blinding="analysis on coded spectra",
        stopping_rule="fixed N",
        primary_outcome="resonance position, linewidth, and "
                        "assignment against published defect catalogues",
        analysis="an unassigned line is UNIDENTIFIED, not a discovery",
        correction="none needed (identification, not comparison)",
        safety=("RF limits", "no sample heating", "enclosed optics"),
    )


def protocols() -> dict:
    plans = {p.id: p.to_dict() for p in
             (material_characterization_protocol(),
              four_state_write_read_protocol())}
    return {"protocols": plans, "n": len(plans),
            "apparatus_status": "NOT BUILT",
            "data_status": "NO DATA COLLECTED",
            "physical_status": "UNTESTED",
            "claim_boundary":
                "preregistered plans only; quartz remains BLOCKED and "
                "no spin has been written, read, or reset"}
