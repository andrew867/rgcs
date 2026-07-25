"""P04 -- the result-class state machine and the evidence firewall.

R10.8.1 stopped a source-vector map at a single bare refusal,
``NO_UNIQUE_GEOGRAPHIC_DECODE``. R10.8.2 keeps the same discipline but produces
a **richer** outcome: a bounded pin, cell, region, or alias set with declared
uncertainty -- never invented precision, never a bare refusal.

This module is the state machine over the seven non-negotiable result classes
(:class:`cwatlas.r1082.claims.ResultClass`):

* ``CANONICAL_EXACT_POINT`` -- a reversible codec round-trip of a *declared*
  canonical address. A ``DERIVED_MATHEMATICS`` fact about the codec.
* ``CANDIDATE_CALIBRATED_POINT`` -- one candidate under a declared calibration.
* ``CANDIDATE_REGION`` -- one candidate but no calibration: a point would
  invent precision, so a bounded region is returned.
* ``CANDIDATE_ALIAS_SET`` -- a small set of admissible candidates.
* ``CALIBRATION_REQUIRED`` -- a decode is reachable but a CRS/epoch/calibration
  is missing.
* ``UNDERDETERMINED`` -- no admissible candidate, or a set too diffuse to bound.
* ``INVALID`` -- malformed input.

**The evidence firewall.** Every candidate class carries at most
``CALIBRATED_CANDIDATE`` evidence -- it is a ``SOFTWARE_RESULT`` under a
declared calibration, **never** ``MEASURED`` or ``REPLICATED``.
:func:`evidence_for` never returns a measurement class for a candidate, and
:meth:`MapResult.assert_not_measured` / :meth:`MapResult.to_serializable`
route any attempt to serialize a candidate as a measured coordinate through
:func:`cwatlas.r1082.claims.refuse_candidate_as_measured`.

Deterministic; epochs are passed in, never read from a clock.

    SOURCE_ORIGIN_NOT_VALIDATED
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from cwatlas.r1082 import claims
from cwatlas.r1082.claims import EvidenceClass, ResultClass

#: A candidate set at or above this size is too diffuse to bound as an alias
#: set and is reported as UNDERDETERMINED (a region / heatmap, not a pin set).
DEFAULT_ALIAS_MAX = 6

#: The candidate result classes -- each is CALIBRATED_CANDIDATE evidence.
CANDIDATE_RESULT_CLASSES = frozenset({
    ResultClass.CANDIDATE_CALIBRATED_POINT,
    ResultClass.CANDIDATE_REGION,
    ResultClass.CANDIDATE_ALIAS_SET,
})

#: The evidence class each result class carries. No candidate ever reaches a
#: measurement class -- this table is the firewall in data form.
_EVIDENCE_BY_RESULT = {
    ResultClass.CANONICAL_EXACT_POINT: EvidenceClass.DERIVED_MATHEMATICS,
    ResultClass.CANDIDATE_CALIBRATED_POINT: EvidenceClass.CALIBRATED_CANDIDATE,
    ResultClass.CANDIDATE_REGION: EvidenceClass.CALIBRATED_CANDIDATE,
    ResultClass.CANDIDATE_ALIAS_SET: EvidenceClass.CALIBRATED_CANDIDATE,
    ResultClass.CALIBRATION_REQUIRED: EvidenceClass.SOFTWARE_RESULT,
    ResultClass.UNDERDETERMINED: EvidenceClass.SOFTWARE_RESULT,
    ResultClass.INVALID: EvidenceClass.SOFTWARE_RESULT,
}

#: Stable API error / status codes for each result class (user + API surface).
_API_CODE = {
    ResultClass.CANONICAL_EXACT_POINT: "OK_CANONICAL_EXACT_POINT",
    ResultClass.CANDIDATE_CALIBRATED_POINT: "OK_CANDIDATE_CALIBRATED_POINT",
    ResultClass.CANDIDATE_REGION: "OK_CANDIDATE_REGION",
    ResultClass.CANDIDATE_ALIAS_SET: "OK_CANDIDATE_ALIAS_SET",
    ResultClass.CALIBRATION_REQUIRED: "E_CALIBRATION_REQUIRED",
    ResultClass.UNDERDETERMINED: "E_UNDERDETERMINED",
    ResultClass.INVALID: "E_INVALID",
}

#: Plain-language explanations shown to a user for each result class.
_EXPLANATION = {
    ResultClass.CANONICAL_EXACT_POINT: (
        "A declared canonical address round-trips exactly through the codec. "
        "This is a mathematical property of the codec, not a measured fact."),
    ResultClass.CANDIDATE_CALIBRATED_POINT: (
        "One candidate location under a declared calibration. It is a software "
        "result, not a measured or replicated coordinate."),
    ResultClass.CANDIDATE_REGION: (
        "One arithmetic candidate, but no prospective calibration is available. "
        "A single pin would invent precision, so a bounded region is shown."),
    ResultClass.CANDIDATE_ALIAS_SET: (
        "Several admissible candidates. The complete bounded alias set is "
        "shown rather than forcing one pin."),
    ResultClass.CALIBRATION_REQUIRED: (
        "A decode is reachable, but a coordinate-reference-system, epoch, or "
        "calibration is missing. Provide it to place a candidate."),
    ResultClass.UNDERDETERMINED: (
        "No admissible candidate was produced, or the set is too diffuse to "
        "bound. This is a normal, successful result, not a failure."),
    ResultClass.INVALID: (
        "The input is malformed and cannot be decoded."),
}

#: The legacy R10.8.1 refusal code this state machine migrates away from.
LEGACY_NO_UNIQUE_DECODE = "NO_UNIQUE_GEOGRAPHIC_DECODE"


def evidence_for(result_class: ResultClass) -> EvidenceClass:
    """The evidence class a result class carries.

    Never a measurement class for a candidate: a candidate is at most
    ``CALIBRATED_CANDIDATE``. This is the firewall as a pure function.
    """
    ev = _EVIDENCE_BY_RESULT[result_class]
    if result_class in CANDIDATE_RESULT_CLASSES and ev in claims.MEASUREMENT_EVIDENCE:
        # Unreachable by construction; guard against a future table edit.
        claims.refuse_candidate_as_measured(result_class)
    return ev


def is_candidate(result_class: ResultClass) -> bool:
    """True iff the result class is a candidate (CALIBRATED_CANDIDATE evidence)."""
    return result_class in CANDIDATE_RESULT_CLASSES


@dataclass(frozen=True)
class MapResult:
    """A typed result-class outcome, with its firewalled evidence class.

    ``result_class`` is one of the seven classes; ``evidence_class`` is derived
    from it and is never a measurement class for a candidate; ``candidate_count``
    is how many admissible candidates were found; ``api_code`` and
    ``explanation`` are the API and user surfaces.
    """

    result_class: ResultClass
    evidence_class: EvidenceClass
    candidate_count: int
    api_code: str
    explanation: str
    calibration_available: bool
    crs: Optional[str] = None
    epoch: Optional[float] = None

    def is_candidate(self) -> bool:
        return is_candidate(self.result_class)

    def assert_not_measured(self) -> None:
        """Refuse to treat a candidate result as a measured coordinate.

        Wired to :func:`cwatlas.r1082.claims.refuse_candidate_as_measured`.
        A candidate is a software result under a declared calibration; it may
        not be promoted to a measured or replicated fact.
        """
        if self.is_candidate():
            claims.refuse_candidate_as_measured(self.result_class)

    def to_serializable(self, *, as_measured: bool = False) -> dict:
        """Serialize the result, refusing to emit a candidate as measured.

        ``as_measured=True`` on a candidate is refused: candidate outputs are
        never serialized as measured coordinates (phase requirement 3).
        """
        if as_measured:
            self.assert_not_measured()
        return {
            "result_class": self.result_class.value,
            "evidence_class": self.evidence_class.value,
            "candidate_count": self.candidate_count,
            "api_code": self.api_code,
            "explanation": self.explanation,
            "calibration_available": self.calibration_available,
            "crs": self.crs,
            "epoch": self.epoch,
            "measured_here": "nothing",
            "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        }


def _build(result_class: ResultClass, candidate_count: int,
           calibration_available: bool, crs, epoch) -> MapResult:
    return MapResult(
        result_class=result_class,
        evidence_class=evidence_for(result_class),
        candidate_count=candidate_count,
        api_code=_API_CODE[result_class],
        explanation=_EXPLANATION[result_class],
        calibration_available=calibration_available,
        crs=crs,
        epoch=epoch,
    )


def classify(
    *,
    valid: bool,
    candidate_count: int,
    calibration_available: bool,
    canonical_exact: bool = False,
    crs: Optional[str] = None,
    epoch: Optional[float] = None,
    alias_max: int = DEFAULT_ALIAS_MAX,
) -> MapResult:
    """Select the result class for a decode outcome.

    The state machine never forces a pin: a lone candidate without calibration
    falls to ``CANDIDATE_REGION``, and a missing CRS/epoch falls to
    ``CALIBRATION_REQUIRED`` rather than an invented point.
    """
    if not valid:
        return _build(ResultClass.INVALID, candidate_count,
                      calibration_available, crs, epoch)
    if canonical_exact:
        # A declared canonical round-trip is exact and needs no calibration.
        return _build(ResultClass.CANONICAL_EXACT_POINT, candidate_count,
                      calibration_available, crs, epoch)
    if candidate_count <= 0:
        return _build(ResultClass.UNDERDETERMINED, 0,
                      calibration_available, crs, epoch)
    # A geographic pin needs a declared CRS and epoch (System Contract inv. 9).
    if not crs or epoch is None:
        return _build(ResultClass.CALIBRATION_REQUIRED, candidate_count,
                      calibration_available, crs, epoch)
    if candidate_count == 1:
        cls = (ResultClass.CANDIDATE_CALIBRATED_POINT if calibration_available
               else ResultClass.CANDIDATE_REGION)
        return _build(cls, 1, calibration_available, crs, epoch)
    if candidate_count < alias_max:
        return _build(ResultClass.CANDIDATE_ALIAS_SET, candidate_count,
                      calibration_available, crs, epoch)
    # Too diffuse to bound as an alias set: a region / heatmap, not a pin set.
    return _build(ResultClass.UNDERDETERMINED, candidate_count,
                  calibration_available, crs, epoch)


def migrate_no_unique_decode(
    *,
    candidate_count: int,
    calibration_available: bool,
    crs: Optional[str] = None,
    epoch: Optional[float] = None,
    alias_max: int = DEFAULT_ALIAS_MAX,
) -> MapResult:
    """Migrate a legacy ``NO_UNIQUE_GEOGRAPHIC_DECODE`` into a richer class.

    The old behavior returned a single bare refusal. This maps the same
    situation to a bounded pin, region, or alias set (or ``UNDERDETERMINED``
    when nothing is admissible), always preserving the evidence firewall -- the
    migrated result is never stronger than ``CALIBRATED_CANDIDATE``.
    """
    result = classify(
        valid=True,
        candidate_count=candidate_count,
        calibration_available=calibration_available,
        crs=crs,
        epoch=epoch,
        alias_max=alias_max,
    )
    # Firewall invariant: the migration can never mint a measurement class.
    assert result.evidence_class not in claims.MEASUREMENT_EVIDENCE
    return result


def result_states_report() -> dict:
    """What this module claims -- and, deliberately, what it does not."""
    return {
        "module": "cwatlas.r1082.result_states",
        "phase_id": "P04",
        "result_classes": [r.value for r in ResultClass],
        "candidate_result_classes": sorted(
            r.value for r in CANDIDATE_RESULT_CLASSES),
        "evidence_by_result": {
            r.value: evidence_for(r).value for r in ResultClass},
        "api_codes": {r.value: _API_CODE[r] for r in ResultClass},
        "legacy_migrated_from": LEGACY_NO_UNIQUE_DECODE,
        "firewall": "a candidate is CALIBRATED_CANDIDATE evidence, never "
                    "MEASURED or REPLICATED",
        "claim": "the result-class state machine that turns a legacy bare "
                 "refusal into bounded candidate states without breaking the "
                 "evidence firewall",
        "claim_class": EvidenceClass.SOFTWARE_RESULT.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "CANDIDATE_RESULT_STATES_WITH_EVIDENCE_FIREWALL",
        "what_this_does_not_say": (
            "A candidate pin, region, or alias set is a software result under a "
            "declared calibration. It is not a measured or replicated fact, and "
            "it validates neither the source's origin nor any physical effect."),
    }
