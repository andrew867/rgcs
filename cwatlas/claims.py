"""CW Atlas claim taxonomy and the forbidden promotions.

This is the governance core the atlas rests on. It separates what the
reversible synthetic codec can assert (an exact, verified round-trip) from
what an operator-reported source vector may claim (nothing geographic,
without prospective evidence), and it makes every over-claim a typed refusal.

The taxonomy (System Contract invariant 10 + the claim/privacy boundary):

* ``CANONICAL_ROUND_TRIP`` — a reversible codec mapped a *declared* canonical
  coordinate to a vector and back, exactly. A math fact about the codec, not
  a claim about any real-world reported vector.
* ``MATHEMATICAL_TRANSLATION`` — a legacy string was re-expressed by an
  arithmetic codec. No meaning is asserted.
* ``LEGACY_ALIAS_CANDIDATE`` — one admissible decode among a set, with a
  score and an uncertainty.
* ``SOURCE_CLAIM`` — a value or interpretation reported by a source.
* ``OPERATOR_HYPOTHESIS`` — a hypothesis proposed by the operator.
* ``CALIBRATED_MAPPING`` — a source semantics that has survived a prospective
  known-destination challenge. Not reachable without that evidence.
* ``REFUSAL`` — a decode declined for missing calibration / CRS / epoch.

Nothing here promotes a source vector into a geographic fact, an alias set
into a unique pin, or a close arithmetic match into intended encoding.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ClaimError(RuntimeError):
    """Raised on an illegal promotion or an out-of-taxonomy claim."""


class ClaimClass(Enum):
    """The CW Atlas claim taxonomy."""

    CANONICAL_ROUND_TRIP = "CANONICAL_ROUND_TRIP"
    MATHEMATICAL_TRANSLATION = "MATHEMATICAL_TRANSLATION"
    LEGACY_ALIAS_CANDIDATE = "LEGACY_ALIAS_CANDIDATE"
    SOURCE_CLAIM = "SOURCE_CLAIM"
    OPERATOR_HYPOTHESIS = "OPERATOR_HYPOTHESIS"
    CALIBRATED_MAPPING = "CALIBRATED_MAPPING"
    REFUSAL = "REFUSAL"


#: Classes that require prospective calibration evidence to reach. No atlas
#: operation reaches these from arithmetic alone.
EVIDENCE_GATED_CLASSES = frozenset({ClaimClass.CALIBRATED_MAPPING})

#: The strongest class reachable for a *source-reported* vector without
#: prospective evidence: it is, at most, an arithmetic re-expression.
MAX_SOURCE_CLASS = ClaimClass.MATHEMATICAL_TRANSLATION


@dataclass(frozen=True)
class Claim:
    """A typed atlas result: statement, claim class, justification."""

    statement: str
    claim_class: ClaimClass
    justification: str

    def __post_init__(self) -> None:
        if not self.justification:
            raise ClaimError("every claim must carry a justification")


def refuse_source_as_geographic(*_a, **_k) -> None:
    """A source vector does not identify a real location."""
    raise ClaimError(
        "refused: a source or legacy vector does not identify a real "
        "geographic (or extraterrestrial) location. It yields an alias set "
        "or a refusal, never a decoded destination, until a prospective "
        "known-destination challenge calibrates its semantics.")


def refuse_alias_as_unique(candidates=None, *_a, **_k) -> None:
    """A legacy candidate set may not be forced to one pin."""
    n = len(candidates) if candidates is not None else "many"
    raise ClaimError(
        f"refused: a legacy decode produced {n} admissible candidates; "
        f"forcing one pin would invent precision the data do not support. "
        f"Return the alias set, a region, or a refusal.")


def refuse_close_match_as_intent(*_a, **_k) -> None:
    """A close arithmetic match does not establish intended encoding."""
    raise ClaimError(
        "refused: a close arithmetic match between a source string and a "
        "coordinate does not establish that the source intended that "
        "encoding. Coincidence is not authorship.")


def refuse_synthetic_codec_as_source_meaning(*_a, **_k) -> None:
    """A reversible synthetic codec does not prove a source vector's meaning."""
    raise ClaimError(
        "refused: that CW-GEO-1 (or any reversible codec) round-trips a "
        "declared coordinate says nothing about what an operator-reported "
        "source vector meant. The two systems are separate.")


def refuse_pin_without_crs_epoch(crs=None, epoch=None, *_a, **_k) -> None:
    """A map pin needs a CRS and an epoch receipt (invariant 9)."""
    if not crs or epoch is None:
        raise ClaimError(
            "refused: a map pin may not be produced without a declared "
            "coordinate-reference-system and an epoch receipt "
            f"(crs={crs!r}, epoch={epoch!r}).")


def refuse_control_claim(*_a, **_k) -> None:
    """The coordinate system controls nothing physical."""
    raise ClaimError(
        "refused: the coordinate system does not control gravity, portals, "
        "craft, or consciousness. No such claim is supported.")


def refuse_patent_as_craft_validation(*_a, **_k) -> None:
    """A public patent does not validate a secret craft programme."""
    raise ClaimError(
        "refused: a public patent is a document, not evidence that a secret "
        "craft programme exists or that a source vector is real.")


def refuse_site_decoded(site: str = "a site", *_a, **_k) -> None:
    """No named site has been decoded from the vector family."""
    raise ClaimError(
        f"refused: {site} has not been decoded from the vector family; an "
        f"arithmetic proximity is not a decode.")


#: The forbidden promotions, indexed by a short name for the red team.
FORBIDDEN_PROMOTIONS = {
    "source_as_geographic": refuse_source_as_geographic,
    "alias_as_unique": lambda: refuse_alias_as_unique([1, 2, 3]),
    "close_match_as_intent": refuse_close_match_as_intent,
    "synthetic_codec_as_source_meaning": refuse_synthetic_codec_as_source_meaning,
    "pin_without_crs_epoch": refuse_pin_without_crs_epoch,
    "control_claim": refuse_control_claim,
    "patent_as_craft_validation": refuse_patent_as_craft_validation,
    "site_decoded": refuse_site_decoded,
}


def claims_report() -> dict:
    return {
        "what_this_is": "the CW Atlas claim taxonomy and forbidden promotions",
        "claim_classes": [c.value for c in ClaimClass],
        "evidence_gated_classes": [c.value for c in EVIDENCE_GATED_CLASSES],
        "max_source_class": MAX_SOURCE_CLASS.value,
        "forbidden_promotions": list(FORBIDDEN_PROMOTIONS),
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_CLAIM_TAXONOMY_TYPED_NO_PROMOTION",
        "what_this_does_not_say": (
            "A reversible canonical round-trip is a verified property of the "
            "codec, not evidence that any operator-reported source vector "
            "identifies a real location. Source-vector geographic semantics "
            "remain NOT_CLAIMED without a prospective known-destination "
            "challenge."),
    }
