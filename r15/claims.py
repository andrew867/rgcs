"""R15 claim taxonomy, evidence ladder, and the forbidden promotions.

This is the governance core the whole R15 platform rests on. It does three
jobs.

**It types every claim.** A result belongs to exactly one claim class, and
the classes separate what software can produce (a source claim, an
implementation, a synthetic fixture or observation, a calibration self-test
result, a model prediction) from what only real acquisition can produce (a
physical measurement, a repeated measurement, an independent replication)
and from the *explanations* an observation must survive (a known ordinary
effect, a model/calibration/fixture error) before it may be called an
``UNEXPLAINED_INSTRUMENT_RESIDUAL`` -- the ceiling for anything unreplicated.

**It caps evidence by what is bound.** The evidence ladder runs from a bare
hypothesis (E0) to independent replication (E7). Missing calibration, a raw
artifact, a fixture binding, or a clock binding caps the evidence below a
physical measurement, no matter how clean the number looks.

**It forbids the promotions.** Synthetic to physical, source to
measurement, model to measurement, noise to resonance, and unexplained
residual to new physics are each a named refusal. There is no
``PHRYLL_DETECTED`` state and asking for one raises.

Nothing here is measured. The strongest class any R15 module reaches from
software alone is ``MODEL_PREDICTION`` (or a synthetic observation / a
calibration self-test); the physical classes exist so the ladder stays
honest about what is still missing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ClaimError(RuntimeError):
    """Raised on an illegal promotion or an out-of-taxonomy claim."""


class ClaimClass(Enum):
    """The R15 claim taxonomy. Membership, not a single linear order:
    software classes, physical classes, ordinary-explanation classes, and
    the residual/anomaly ceiling are distinct families."""

    # what software alone can produce
    SOURCE_CLAIM = "SOURCE_CLAIM"
    SOFTWARE_IMPLEMENTED = "SOFTWARE_IMPLEMENTED"
    SYNTHETIC_FIXTURE = "SYNTHETIC_FIXTURE"
    SYNTHETIC_OBSERVATION = "SYNTHETIC_OBSERVATION"
    CALIBRATION_RESULT = "CALIBRATION_RESULT"
    MODEL_PREDICTION = "MODEL_PREDICTION"
    # what only real physical acquisition can produce
    PHYSICAL_MEASUREMENT = "PHYSICAL_MEASUREMENT"
    REPEATED_PHYSICAL_MEASUREMENT = "REPEATED_PHYSICAL_MEASUREMENT"
    INDEPENDENT_REPLICATION = "INDEPENDENT_REPLICATION"
    # ordinary explanations a residual must survive
    KNOWN_ORDINARY_EFFECT = "KNOWN_ORDINARY_EFFECT"
    MODEL_ERROR = "MODEL_ERROR"
    CALIBRATION_ERROR = "CALIBRATION_ERROR"
    FIXTURE_EFFECT = "FIXTURE_EFFECT"
    # the ceilings
    UNEXPLAINED_INSTRUMENT_RESIDUAL = "UNEXPLAINED_INSTRUMENT_RESIDUAL"
    REPLICATED_ANOMALY = "REPLICATED_ANOMALY"


#: Classes that require real measured data. No R15 module reaches these
#: from software alone.
MEASUREMENT_CLASSES = frozenset({
    ClaimClass.PHYSICAL_MEASUREMENT,
    ClaimClass.REPEATED_PHYSICAL_MEASUREMENT,
    ClaimClass.INDEPENDENT_REPLICATION,
    ClaimClass.REPLICATED_ANOMALY,
})

#: The strongest class reachable from software/simulation in this
#: environment.
MAX_SOFTWARE_CLASS = ClaimClass.MODEL_PREDICTION

#: Software may emit exactly these; anything else needs artifacts.
SOFTWARE_CLASSES = frozenset({
    ClaimClass.SOURCE_CLAIM,
    ClaimClass.SOFTWARE_IMPLEMENTED,
    ClaimClass.SYNTHETIC_FIXTURE,
    ClaimClass.SYNTHETIC_OBSERVATION,
    ClaimClass.CALIBRATION_RESULT,
    ClaimClass.MODEL_PREDICTION,
})


class EvidenceLevel(Enum):
    """The evidence ladder. Higher is stronger; missing bindings cap it."""

    E0 = 0   # source or hypothesis
    E1 = 1   # software derivation
    E2 = 2   # deterministic synthetic observation
    E3 = 3   # calibrated instrument self-test
    E4 = 4   # single physical observation
    E5 = 5   # repeated observation with remounting / randomization
    E6 = 6   # blinded holdout support
    E7 = 7   # independent replication


#: Above this level, real physical acquisition is required.
MAX_SOFTWARE_EVIDENCE = EvidenceLevel.E3


@dataclass(frozen=True)
class EvidenceBindings:
    """The bindings an observation must carry to count as physical.

    Any missing binding caps the evidence below a physical measurement
    (E4), regardless of how clean the value is.
    """

    instrument: bool = False
    calibration: bool = False
    specimen: bool = False
    fixture: bool = False
    protocol: bool = False
    clock: bool = False
    environment: bool = False
    raw_artifact: bool = False
    uncertainty: bool = False

    def complete_for_physical(self) -> bool:
        return all((self.instrument, self.calibration, self.specimen,
                    self.fixture, self.protocol, self.clock,
                    self.environment, self.raw_artifact, self.uncertainty))

    def missing(self) -> list[str]:
        return [n for n, v in self.__dict__.items() if not v]


def evidence_cap(bindings: EvidenceBindings,
                 requested: EvidenceLevel) -> EvidenceLevel:
    """Cap a requested evidence level by the available bindings.

    Without every physical binding, evidence cannot reach E4; software and
    synthetic work top out at E3 (a calibrated self-test).
    """
    if requested.value >= EvidenceLevel.E4.value and \
            not bindings.complete_for_physical():
        return MAX_SOFTWARE_EVIDENCE
    return requested


@dataclass(frozen=True)
class Claim:
    """A typed R15 result: a statement, a claim class, a justification, and
    the evidence level actually supported."""

    statement: str
    claim_class: ClaimClass
    justification: str
    evidence: EvidenceLevel = EvidenceLevel.E1

    def __post_init__(self) -> None:
        if not self.justification:
            raise ClaimError("every claim must carry a justification")


def refuse_promotion_to_measurement(claim: Claim) -> None:
    """Refuse to relabel a software/synthetic claim as a measurement."""
    if claim.claim_class in MEASUREMENT_CLASSES:
        raise ClaimError(
            f"refused: {claim.statement!r} is claimed as "
            f"{claim.claim_class.value}, a measurement class, but no "
            f"physical acquisition with artifacts exists here")


def cap_claim_to_software(requested: ClaimClass) -> ClaimClass:
    """A requested measurement class collapses to the software ceiling when
    no physical artifacts exist."""
    if requested in MEASUREMENT_CLASSES:
        return MAX_SOFTWARE_CLASS
    return requested


# --- the forbidden promotions ------------------------------------------

def refuse_synthetic_as_physical(*_a, **_k) -> None:
    """A synthetic observation is not a physical measurement."""
    raise ClaimError(
        "refused: a SYNTHETIC_OBSERVATION is not a PHYSICAL_MEASUREMENT. A "
        "deterministic simulator output was produced, not an instrument "
        "reading of a specimen.")


def refuse_source_as_measurement(*_a, **_k) -> None:
    """A source claim is not a measurement."""
    raise ClaimError(
        "refused: a SOURCE_CLAIM (a cited value or hypothesis) is not a "
        "measurement made on this apparatus.")


def refuse_model_as_measurement(*_a, **_k) -> None:
    """A model prediction is not a measurement."""
    raise ClaimError(
        "refused: a MODEL_PREDICTION is not a PHYSICAL_MEASUREMENT. A model "
        "was evaluated; no apparatus was operated.")


def refuse_noise_as_resonance(*_a, **_k) -> None:
    """A feature within noise/uncertainty is not a resonance."""
    raise ClaimError(
        "refused: a spectral feature not exceeding the combined "
        "uncertainty budget is noise, not a resonance. A residual below "
        "combined uncertainty is not anomalous.")


def refuse_residual_as_new_physics(*_a, **_k) -> None:
    """An unexplained instrument residual is not new physics."""
    raise ClaimError(
        "refused: an UNEXPLAINED_INSTRUMENT_RESIDUAL is the ceiling for an "
        "unreplicated residual that survived the ordinary-explanation "
        "attacks. It is not evidence of new physics, a new particle, or a "
        "new energy, and it is not a REPLICATED_ANOMALY until independently "
        "replicated.")


def refuse_phryll_detected(*_a, **_k) -> None:
    """There is no PHRYLL_DETECTED state in R15."""
    raise ClaimError(
        "refused: R15 has no PHRYLL_DETECTED state. The strongest label "
        "available for an unreplicated residual is "
        "UNEXPLAINED_INSTRUMENT_RESIDUAL.")


#: The forbidden promotions, indexed by a short name for the red team.
FORBIDDEN_PROMOTIONS = {
    "synthetic_to_physical": refuse_synthetic_as_physical,
    "source_to_measurement": refuse_source_as_measurement,
    "model_to_measurement": refuse_model_as_measurement,
    "noise_to_resonance": refuse_noise_as_resonance,
    "residual_to_new_physics": refuse_residual_as_new_physics,
    "phryll_detected": refuse_phryll_detected,
}


def claims_report() -> dict:
    return {
        "what_this_is": (
            "the R15 claim taxonomy, evidence ladder, and forbidden "
            "promotions"),
        "claim_classes": [c.value for c in ClaimClass],
        "measurement_classes": [c.value for c in MEASUREMENT_CLASSES],
        "max_software_class": MAX_SOFTWARE_CLASS.value,
        "evidence_levels": [e.name for e in EvidenceLevel],
        "max_software_evidence": MAX_SOFTWARE_EVIDENCE.name,
        "forbidden_promotions": list(FORBIDDEN_PROMOTIONS),
        "has_phryll_detected_state": False,
        "residual_ceiling": ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL.value,
        "claim_class": "SOFTWARE_IMPLEMENTED",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "R15_CLAIM_TAXONOMY_TYPED_NO_PROMOTION",
        "what_this_does_not_say": (
            "It certifies no result as physically measured. The strongest "
            "class reachable from software is MODEL_PREDICTION; the "
            "measurement classes exist so the ladder stays honest about "
            "what is missing, and UNEXPLAINED_INSTRUMENT_RESIDUAL is never "
            "new physics."),
    }
