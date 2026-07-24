"""P04 — typed state variables, units, and claim semantics.

This is the governance core R13 is built on: the rules that let a
certified cross-domain transfer happen *without* letting domains collapse
into one another. It does two jobs.

**It types every claim.** A result belongs to exactly one claim class,
and the classes form a strict ladder from arithmetic identity up to
independently replicated measurement. Nothing moves up the ladder by
assertion.

**It forbids the seven promotions.** The R13 pack names seven ways a
weak claim tries to become a strong one, and every one of them is a
refusal here:

* algebraic similarity -> physical equivalence
* a simulation -> a measurement
* a numeric match -> source authentication
* an unclosed energy ledger -> new energy
* angular uniformity in a plane -> 3-D isotropic emission
* a coordinate alias -> a decoded destination
* an exotic-particle paper -> evidence for an RGCS carrier

Each promotion is a named exception, so an attempt to make one is a typed
error rather than a quiet upgrade.

Nothing here is measured. The strongest class any R13 module reaches from
software alone is ``REPOSITORY_COMPUTATIONAL_RESULT``; the measurement
classes exist so the ladder is honest about what is still missing.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClaimError(RuntimeError):
    """Raised on an illegal promotion or an out-of-ladder claim."""


class ClaimClass(Enum):
    """The claim ladder. Order is meaning: higher is a stronger claim."""

    EXACT_IDENTITY = 0
    SOURCE_ESTABLISHED_PHYSICS = 1
    CONVENTIONAL_LITERATURE = 2
    DERIVED_ARITHMETIC = 3
    ANALYTIC_MODEL = 4
    NUMERICAL_SIMULATION = 5
    REPOSITORY_COMPUTATIONAL_RESULT = 6
    ENGINEERING_CANDIDATE = 7
    SOURCE_CLAIM = 8
    RETROSPECTIVE_NUMERIC_MATCH = 9
    PROSPECTIVE_PREDICTION = 10
    BENCH_MEASUREMENT = 11
    INDEPENDENTLY_REPLICATED = 12
    UNSUPPORTED = 90
    BLOCKED_MISSING_INPUT = 91


#: The classes that require real measured data. No R13 module reaches
#: these from software alone.
MEASUREMENT_CLASSES = frozenset({
    ClaimClass.BENCH_MEASUREMENT,
    ClaimClass.INDEPENDENTLY_REPLICATED,
})

#: The strongest class reachable from software/computation in this
#: environment.
MAX_SOFTWARE_CLASS = ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT


@dataclass(frozen=True)
class StateVariable:
    """A physical state variable with an explicit unit and domain.

    Two state variables from different domains may never be combined by
    number alone -- the unit and domain are what stop a hertz being
    compared with a microsecond, or a strain with a magnetic field.
    """

    name: str
    unit: str
    domain: str

    def __post_init__(self) -> None:
        if not self.name or not self.unit or not self.domain:
            raise ClaimError("a state variable needs a name, a unit, and a "
                             "domain; a bare number is not a state variable")


def refuse_unit_mismatch(a: StateVariable, b: StateVariable) -> None:
    """Refuse to combine two state variables of different unit or domain."""
    if a.unit != b.unit or a.domain != b.domain:
        raise ClaimError(
            f"refused: {a.name} [{a.unit}, {a.domain}] and "
            f"{b.name} [{b.unit}, {b.domain}] are different kinds of "
            f"quantity and may not be combined by number alone")


@dataclass(frozen=True)
class Claim:
    """A typed result: a value with a claim class and a justification."""

    statement: str
    claim_class: ClaimClass
    justification: str

    def __post_init__(self) -> None:
        if not self.justification:
            raise ClaimError("every claim must carry a justification")


def refuse_promotion(claim: Claim, target: ClaimClass) -> None:
    """Refuse to raise a claim's class without new evidence of that kind.

    Moving to a measurement class requires an actual measurement; this
    environment has none, so any such promotion is refused.
    """
    if target.value > claim.claim_class.value:
        if target in MEASUREMENT_CLASSES:
            raise ClaimError(
                f"refused: {claim.statement!r} is {claim.claim_class.name} "
                f"and cannot be promoted to {target.name} without a real "
                f"measurement, which does not exist here")
        raise ClaimError(
            f"refused: {claim.statement!r} may not be promoted from "
            f"{claim.claim_class.name} to {target.name} without new "
            f"evidence of that class")


# --- the seven forbidden promotions ------------------------------------

def refuse_similarity_as_equivalence(*_a, **_k) -> None:
    """Algebraic similarity is not physical equivalence."""
    raise ClaimError(
        "refused: two systems sharing an equation (a 2x2 coupling matrix, "
        "a Lorentzian, a symplectic map) are not therefore the same "
        "physics. Shared mathematics is not shared mechanism.")


def refuse_simulation_as_measurement(*_a, **_k) -> None:
    """A simulation is not a measurement."""
    raise ClaimError(
        "refused: a NUMERICAL_SIMULATION or a REPOSITORY_COMPUTATIONAL_"
        "RESULT is not a BENCH_MEASUREMENT. No apparatus was operated.")


def refuse_numeric_match_as_authentication(*_a, **_k) -> None:
    """A numeric match does not authenticate a source."""
    raise ClaimError(
        "refused: a close number is not a signature. A numeric match, "
        "however tight, does not authenticate a source or a transmitter.")


def refuse_unclosed_energy_as_new_energy(residual, interval) -> None:
    """An energy ledger that does not close is a calibration gap."""
    raise ClaimError(
        f"refused: an energy residual ({residual}) whose confidence "
        f"interval ({interval}) includes zero is an uncalibrated ledger, "
        f"not a new energy channel.")


def refuse_planar_uniformity_as_isotropy(*_a, **_k) -> None:
    """Angular uniformity in a plane is not 3-D isotropic emission."""
    raise ClaimError(
        "refused: uniform response around one circle of angles is planar "
        "uniformity, not unrestricted three-dimensional isotropic "
        "emission. The out-of-plane directions were not sampled.")


def refuse_alias_as_destination(*_a, **_k) -> None:
    """A coordinate alias is not a decoded destination."""
    raise ClaimError(
        "refused: a coordinate that is consistent with many frames, roots "
        "and projections is an alias set, not a decoded destination.")


def refuse_paper_as_carrier_evidence(*_a, **_k) -> None:
    """A theoretical exotic-particle paper is not evidence for a carrier."""
    raise ClaimError(
        "refused: a theoretical paper about an exotic state or particle is "
        "literature, not evidence that any such thing is a carrier in this "
        "project. Registering a paper is citation, not confirmation.")


#: The seven promotions, indexed by a short name for the red team.
FORBIDDEN_PROMOTIONS = {
    "similarity_to_equivalence": refuse_similarity_as_equivalence,
    "simulation_to_measurement": refuse_simulation_as_measurement,
    "match_to_authentication": refuse_numeric_match_as_authentication,
    "unclosed_to_new_energy":
        lambda: refuse_unclosed_energy_as_new_energy(0.0, (-1.0, 1.0)),
    "planar_to_isotropic": refuse_planar_uniformity_as_isotropy,
    "alias_to_destination": refuse_alias_as_destination,
    "paper_to_carrier": refuse_paper_as_carrier_evidence,
}


def claimtypes_report() -> dict:
    return {
        "what_this_is": (
            "the R13 claim ladder and the seven forbidden promotions"),
        "claim_classes": [c.name for c in ClaimClass],
        "measurement_classes": [c.name for c in MEASUREMENT_CLASSES],
        "max_software_class": MAX_SOFTWARE_CLASS.name,
        "forbidden_promotions": list(FORBIDDEN_PROMOTIONS),
        "claim_class": "EXACT_IDENTITY",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "CLAIM_SEMANTICS_TYPED_NO_PROMOTION",
        "what_this_does_not_say": (
            "It does not certify any result as measured. The strongest "
            "class any R13 module reaches from software is "
            "REPOSITORY_COMPUTATIONAL_RESULT; the measurement classes are "
            "defined so the ladder stays honest about what is missing."),
    }
