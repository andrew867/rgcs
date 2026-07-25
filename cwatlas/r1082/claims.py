"""R10.8.2 evidence classes, result classes, and the locked-root refusals.

The System Contract keeps seven evidence classes separate and defines seven
result classes. This module types them and makes every over-claim a refusal:
a candidate pin is a software result under a declared calibration, never a
measured fact; the source origin is never validated; and after the profile is
frozen there is no result shopping.
"""

from __future__ import annotations

from enum import Enum

from cwatlas import claims as _cw


class R1082ClaimError(RuntimeError):
    """Raised on an illegal promotion or a post-freeze retune."""


class EvidenceClass(Enum):
    """Kept separate (System Contract)."""

    SOURCE = "SOURCE"
    OPERATOR_SELECTION = "OPERATOR_SELECTION"
    DERIVED_MATHEMATICS = "DERIVED_MATHEMATICS"
    SOFTWARE_RESULT = "SOFTWARE_RESULT"
    CALIBRATED_CANDIDATE = "CALIBRATED_CANDIDATE"
    MEASURED = "MEASURED"
    REPLICATED = "REPLICATED"


class ResultClass(Enum):
    """The seven non-negotiable result classes (Locked Decisions)."""

    CANONICAL_EXACT_POINT = "CANONICAL_EXACT_POINT"
    CANDIDATE_CALIBRATED_POINT = "CANDIDATE_CALIBRATED_POINT"
    CANDIDATE_REGION = "CANDIDATE_REGION"
    CANDIDATE_ALIAS_SET = "CANDIDATE_ALIAS_SET"
    CALIBRATION_REQUIRED = "CALIBRATION_REQUIRED"
    UNDERDETERMINED = "UNDERDETERMINED"
    INVALID = "INVALID"


#: Evidence classes that require real measurement — unreachable from a
#: calibrated software candidate.
MEASUREMENT_EVIDENCE = frozenset({EvidenceClass.MEASURED,
                                  EvidenceClass.REPLICATED})

#: The strongest evidence a candidate pin can carry.
MAX_CANDIDATE_EVIDENCE = EvidenceClass.CALIBRATED_CANDIDATE

#: The frozen-profile parameters that must never change after a freeze
#: (changing any one mints a NEW profile id and invalidates holdouts).
FROZEN_PARAMETERS = (
    "grid_rotation", "handedness", "root_feature", "topology",
    "tokenization", "destination_label_split", "epoch_choice",
)


def refuse_candidate_as_measured(result_class=None, *_a, **_k) -> None:
    """A calibrated candidate pin is not a measured fact."""
    raise R1082ClaimError(
        "refused: a CANDIDATE_CALIBRATED_POINT (or region / alias set) is a "
        "SOFTWARE_RESULT under a declared calibration, not a MEASURED or "
        "REPLICATED fact. It may not be promoted without real measurement.")


def refuse_source_origin_validated(*_a, **_k) -> None:
    """The source origin is user-reported and unverified."""
    raise R1082ClaimError(
        "refused: the source attribution is user-reported and unverified. A "
        "calibrated candidate map does not validate the source's origin.")


def refuse_nonhuman_origin(*_a, **_k) -> None:
    """No nonhuman / extraterrestrial origin is claimed."""
    raise R1082ClaimError(
        "refused: no nonhuman or extraterrestrial origin of the source code "
        "is claimed or established. SOURCE_ORIGIN_NOT_VALIDATED.")


def refuse_physical_effect(*_a, **_k) -> None:
    """The coordinate system claims no physical effect."""
    raise R1082ClaimError(
        "refused: no physical effect is claimed. The atlas maps and "
        "calibrates coordinates; it does not act on the world. "
        "PHYSICAL_EFFECTS_NOT_CLAIMED.")


def refuse_post_output_retuning(parameter: str = "", *, frozen: bool = True,
                                **_k) -> None:
    """After a freeze, changing a frozen parameter is result shopping."""
    if frozen:
        raise R1082ClaimError(
            f"refused: {parameter or 'a frozen parameter'} may not be changed "
            f"after EARTH_ROOT_D_V1 is frozen. Any such change mints a NEW "
            f"profile id and invalidates comparison with prior holdouts "
            f"(no result shopping).")


def refuse_altitude_missing_when_shell_present(shell_state=None, *_a,
                                               **_k) -> None:
    """The shell supplies the radius; do not report altitude as missing."""
    if shell_state is not None:
        raise R1082ClaimError(
            "refused: the shell profile supplies the body-relative radius used "
            "by the dynamic magnetic layer; altitude is present via the shell "
            "and must not be reported as missing.")


#: The forbidden promotions, indexed for the red team.
FORBIDDEN_PROMOTIONS = {
    "candidate_as_measured": refuse_candidate_as_measured,
    "source_origin_validated": refuse_source_origin_validated,
    "nonhuman_origin": refuse_nonhuman_origin,
    "physical_effect": refuse_physical_effect,
    "post_output_retuning": lambda: refuse_post_output_retuning(
        "grid_rotation", frozen=True),
    "altitude_missing_when_shell_present": lambda:
        refuse_altitude_missing_when_shell_present(shell_state=3),
    # the inherited CW Atlas rule: a source vector is not a decoded location
    "source_as_geographic": _cw.refuse_source_as_geographic,
}


def claims_report() -> dict:
    return {
        "what_this_is": "the R10.8.2 evidence/result taxonomy and locked-root "
                        "refusals",
        "evidence_classes": [e.value for e in EvidenceClass],
        "result_classes": [r.value for r in ResultClass],
        "measurement_evidence": [e.value for e in MEASUREMENT_EVIDENCE],
        "max_candidate_evidence": MAX_CANDIDATE_EVIDENCE.value,
        "frozen_parameters": list(FROZEN_PARAMETERS),
        "forbidden_promotions": list(FORBIDDEN_PROMOTIONS),
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "R1082_CLAIM_TAXONOMY_TYPED_NO_PROMOTION",
        "what_this_does_not_say": (
            "A candidate calibrated pin is a software result under a declared, "
            "frozen calibration. It does not validate the source origin, "
            "assert a physical effect, or become a measured fact."),
    }
