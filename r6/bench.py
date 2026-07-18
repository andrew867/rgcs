"""P09 — bench readiness, and where the programme stops.

R6 is a software programme. This module states precisely what would
have to exist before any R6 model could be compared against a
measurement, and refuses to pretend that any of it does.

The distinction that matters: a design can be *bench ready* (fully
specified, costed, safety-reviewed) while the programme remains
*physically untested*. Bench readiness is a statement about the
documentation, never about the world.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict, field

#: Gates that must ALL be open before a physical run is justified.
READINESS_GATES = (
    "APPARATUS_SPECIFIED",
    "INSTRUMENT_MATRIX_COMPLETE",
    "CALIBRATION_PLAN",
    "CONTROL_DESIGN",
    "BLINDING_PROTOCOL",
    "PREREGISTERED_ANALYSIS",
    "SAFETY_REVIEW",
    "OPERATOR_COMPETENCE",
    "DATA_MANAGEMENT_PLAN",
    "STOPPING_RULE",
)

#: Hazards the apparatus family actually presents. Each carries the
#: control that makes it acceptable, or a refusal if it does not.
HAZARDS = {
    "HIGH_VOLTAGE_PULSE": {
        "description": "pulsed drive into an inductive load produces "
                       "large back-EMF at switch-off",
        "control": "enclosed drive, interlocked cover, snubber and "
                   "clamp, discharge path, isolated probe only",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "MAINS_CONSTRUCTION": {
        "description": "any mains-connected build",
        "control": "must be performed by a qualified person to the "
                   "local electrical code",
        "status": "REFUSED_UNLESS_QUALIFIED",
    },
    "RF_EMISSION": {
        "description": "drive harmonics and switching transients "
                       "radiate",
        "control": "screened enclosure, no open 2.45 GHz radiator, "
                   "emission survey before extended running",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "OPTICAL": {
        "description": "readout laser or probe beam",
        "control": "fully enclosed beam path, no exposed beam at eye "
                   "height, interlocks, appropriate eyewear class",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "ULTRASOUND": {
        "description": "acoustic drive above audibility",
        "control": "enclosure, exposure limits, no direct contact "
                   "with the specimen mount during drive",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "MECHANICAL_FRACTURE": {
        "description": "a driven crystal can fracture; the source "
                       "itself warns the sound could 'breach' it",
        "control": "containment shield, drive amplitude ramp, modal "
                   "Q limit, eye protection",
        "status": "CONTROLLED_BY_DESIGN",
    },
    "BIOLOGICAL_EXPOSURE": {
        "description": "any human or animal exposure",
        "control": "none offered",
        "status": "REFUSED_ENTIRELY",
    },
}


@dataclass
class ReadinessAssessment:
    gates_open: tuple[str, ...] = ()
    evidence: dict = field(default_factory=dict)

    def missing(self) -> tuple[str, ...]:
        return tuple(g for g in READINESS_GATES
                     if g not in self.gates_open)

    def as_record(self) -> dict:
        d = asdict(self)
        d["gates_open"] = list(self.gates_open)
        d["missing"] = list(self.missing())
        d["ready"] = not self.missing()
        return d


def current_assessment() -> ReadinessAssessment:
    """What R6 has actually produced, gate by gate.

    Honest state at the end of the software programme: the modelling
    gates are open because the models exist and are tested; the gates
    that require physical objects, people and institutions are shut,
    because none of those exist.
    """
    return ReadinessAssessment(
        gates_open=(
            "APPARATUS_SPECIFIED",
            "INSTRUMENT_MATRIX_COMPLETE",
            "CONTROL_DESIGN",
            "BLINDING_PROTOCOL",
            "STOPPING_RULE",
        ),
        evidence={
            "APPARATUS_SPECIFIED":
                "r6.helix / r6.drive parameterized twins, solver "
                "validated against the solenoid analytic limit",
            "INSTRUMENT_MATRIX_COMPLETE":
                "r6.instrument covers all eighteen ordinary channels",
            "CONTROL_DESIGN":
                "r6.controls material, orientation and environmental "
                "controls including the empty-mount control",
            "BLINDING_PROTOCOL":
                "r6.controls.blinding_protocol",
            "STOPPING_RULE":
                "this module: the programme stops at the last real "
                "capability and does not fabricate bench data",
            "CALIBRATION_PLAN":
                "ABSENT: no owned instrument, so no calibration "
                "certificate, no traceability chain",
            "PREREGISTERED_ANALYSIS":
                "ABSENT: no registration with any third party",
            "SAFETY_REVIEW":
                "ABSENT: no reviewer, no institution",
            "OPERATOR_COMPETENCE":
                "ABSENT: not assessed; mains work requires a "
                "qualified person",
            "DATA_MANAGEMENT_PLAN":
                "ABSENT: no data exists to manage",
        })


def bench_readiness() -> dict:
    """The P09 certificate."""
    a = current_assessment()
    return {
        "programme": "RGCS-V4.9-R6",
        "gates_total": len(READINESS_GATES),
        "gates_open": len(a.gates_open),
        "gates_missing": list(a.missing()),
        "ready_for_bench": False,
        "status": "SOFTWARE_COMPLETE_PHYSICALLY_UNTESTED",
        "hazards": HAZARDS,
        "hazards_refused": [k for k, v in HAZARDS.items()
                            if v["status"].startswith("REFUSED")],
        "evidence": a.evidence,
        "statement": (
            "R6 produced models, controls and refusals. It produced "
            "no measurement. No coil has been wound, no crystal "
            "driven, no clock compared, no spin written or read, and "
            "no geophysical dataset loaded. Bench readiness here "
            "describes documentation completeness and nothing about "
            "the physical world."
        ),
        "next_real_step": (
            "The cheapest genuinely informative experiment is not the "
            "full apparatus. It is a two-oscillator comparison with a "
            "declared transfer link, because it tests the witness "
            "channel -- the one component whose claim ceiling is "
            "actually reachable -- without needing the coil, the "
            "crystal, or any of the contested geometry."
        ),
    }


def refuse_synthetic_as_measurement(*args, **kwargs):
    """Refuses to relabel a model output as a measurement."""
    raise RuntimeError(
        "a synthetic model output may not be recorded as a bench "
        "measurement. R6 owns no instrument, holds no calibration "
        "certificate, and has taken no reading. The evidence classes "
        "BENCH_MEASUREMENT and INDEPENDENT_REPLICATION are closed to "
        "this programme.")
