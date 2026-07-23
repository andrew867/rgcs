"""P03 — the harm, medical, human-classification, and financial firewall.

This is a *content-claim* firewall, and it is a different thing from the
publication firewall in :mod:`r10.firewall`. That one keeps private
*material* out of the public tree. This one keeps unsupported and
dangerous *claims* from being promoted into findings, verdicts, or
actions -- while still preserving them faithfully as source records.

The private source session contains claims that are, in order of
seriousness, dangerous if acted on: that a virus affects hidden human
groups differently, that some people are a hidden hybrid or genetically
modified species, medical predictions, and investment tips. The honest
handling is the same for all of them:

**Preserve the claim as a source record. Refuse to act on it.**

A Tier-A source record is faithful attribution -- who said what, when,
in what words, with what uncertainty. It is *never* empirical evidence,
and this module makes the promotion from ``SOURCE_CLAIM`` to anything
stronger impossible for the quarantined categories without prospective,
discriminating evidence that does not exist here.

What this module refuses, always:

* classifying any real person as nonhuman, hybrid, genetically altered,
  or a member of a hidden species;
* inferring biology, health, or susceptibility from race, ethnicity,
  nationality, geography, appearance, or social group;
* producing pathogen-engineering, genetic-targeting, or group-targeted
  medical analysis;
* giving medical advice derived from a source message;
* making a public accusation about a named person or group;
* issuing a personalized financial action or executing a trade.

What it allows: provenance, pointers to primary peer-reviewed
literature, harm analysis, privacy-safe nulls, and an explicit
``UNSUPPORTED`` verdict. Nothing here is measured or validated.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class ClaimFirewallError(RuntimeError):
    """Raised when a quarantined claim is pushed past the firewall."""


class Quarantine(Enum):
    """The categories that may never be acted on from a source message."""

    HARM_BIOLOGICAL = "harm_biological"          # engineered/differential pathogens
    MEDICAL = "medical"                          # diagnosis, treatment, health prediction
    HUMAN_CLASSIFICATION = "human_classification"  # hidden species / hybrid / genetic
    DISCRIMINATION = "discrimination"            # group-targeted inference
    FINANCIAL = "financial"                      # investment tips / trade signals


#: The only evidence statuses a quarantined claim may hold. Note what is
#: absent: nothing that asserts the claim is true. A quarantined claim is
#: a record of something said, never a finding.
ALLOWED_STATUSES = (
    "SOURCE_CLAIM",          # faithfully recorded, not endorsed
    "QUARANTINED",           # flagged, held, not acted on
    "UNSUPPORTED",           # no evidence supports it
    "CONTRADICTED",          # evidence contradicts it
    "UNRESOLVED",            # open, no claim either way
)

#: Statuses a quarantined claim may NEVER be promoted to.
FORBIDDEN_PROMOTIONS = (
    "MEASURED", "REPLICATED", "SOFTWARE_VERIFIED", "PHYSICAL_HYPOTHESIS",
    "PROSPECTIVE_PREDICTION", "CONFIRMED", "IDENTIFIED",
)


@dataclass(frozen=True)
class QuarantinedClaim:
    """A source claim held behind the firewall.

    The claim text is preserved verbatim as a source record; the point of
    the record is faithful provenance, not endorsement. ``source_id`` is
    a private Tier-A id (e.g. an alias); no real name is required or
    stored here.
    """

    claim_id: str
    category: Quarantine
    source_id: str                       # e.g. "OMEGA_REGION_SOURCE"
    recorded_verbatim: str               # the claim, as said (a record)
    evidence_status: str = "QUARANTINED"
    publication_class: str = "PRIVATE_ONLY"
    rationale: str = ""

    def __post_init__(self) -> None:
        if self.evidence_status not in ALLOWED_STATUSES:
            raise ClaimFirewallError(
                f"evidence_status {self.evidence_status!r} is not allowed "
                f"for a quarantined claim; allowed: {ALLOWED_STATUSES}")
        if not self.claim_id or not self.recorded_verbatim:
            raise ClaimFirewallError("claim_id and recorded_verbatim "
                                     "are required")

    def public_record(self) -> dict:
        """A privacy-safe record. It states that a claim exists and is
        quarantined; it does NOT reproduce the claim text (which is
        PRIVATE_ONLY) and asserts nothing about its truth."""
        return {
            "claim_id": self.claim_id,
            "category": self.category.value,
            "evidence_status": self.evidence_status,
            "publication_class": self.publication_class,
            "endorsed": False,
            "verdict": "UNSUPPORTED",
            "note": ("a source claim in this category is recorded for "
                     "provenance and is not acted on, promoted, or "
                     "reproduced publicly"),
        }


def quarantine(claim_id: str, category: Quarantine, source_id: str,
               recorded_verbatim: str, rationale: str = "") -> QuarantinedClaim:
    """Record a claim as quarantined. This is the only intake path."""
    return QuarantinedClaim(claim_id, category, source_id,
                            recorded_verbatim, "QUARANTINED",
                            "PRIVATE_ONLY", rationale)


def refuse_promotion(claim: QuarantinedClaim, target_status: str) -> None:
    """Refuse to promote a quarantined claim to an evidentiary status.

    A quarantined claim can only ever be recorded, marked unsupported,
    contradicted, or left unresolved. Promotion to any status that
    asserts truth requires prospective, discriminating evidence that this
    project does not have.
    """
    if target_status in FORBIDDEN_PROMOTIONS or target_status not in ALLOWED_STATUSES:
        raise ClaimFirewallError(
            f"cannot promote a {claim.category.value!r} claim to "
            f"{target_status!r}. A source claim in this category is not "
            f"evidence; promotion requires prospective discriminating "
            f"evidence that does not exist here. It stays UNSUPPORTED.")


def refuse_person_classification(*_args, **_kwargs) -> None:
    """Never classify a real person as nonhuman/hybrid/genetic/hidden."""
    raise ClaimFirewallError(
        "refused: this project does not classify any real person as "
        "nonhuman, hybrid, genetically altered, or a member of a hidden "
        "species. There is no such capability and no such claim is "
        "supported.")


def refuse_biological_inference_from_group(*_args, **_kwargs) -> None:
    """Never infer biology/health from race/geography/appearance/group."""
    raise ClaimFirewallError(
        "refused: biology, health, and susceptibility are never inferred "
        "from race, ethnicity, nationality, geography, appearance, or "
        "social group. That is discrimination, not science.")


def refuse_pathogen_or_genetic_targeting(*_args, **_kwargs) -> None:
    """Never produce pathogen engineering or genetic-targeting analysis."""
    raise ClaimFirewallError(
        "refused: no pathogen-engineering, differential-susceptibility, "
        "or genetic-targeting analysis is produced. The source claim is "
        "quarantined as UNSUPPORTED.")


def refuse_medical_advice(*_args, **_kwargs) -> None:
    """Never give medical advice derived from a source message."""
    raise ClaimFirewallError(
        "refused: no medical advice, diagnosis, or health prediction is "
        "derived from a source message. Consult a licensed professional; "
        "the source claim carries no medical authority.")


def refuse_public_accusation(*_args, **_kwargs) -> None:
    """Never make a public accusation about a named person or group."""
    raise ClaimFirewallError(
        "refused: no public accusation is made about any named person or "
        "group on the basis of a source claim.")


def refuse_financial_action(*_args, **_kwargs) -> None:
    """Never issue a personalized financial action or execute a trade.

    Investment-oriented source notes are private hypotheses only; the
    single permitted validation path is blinded paper trading with frozen
    rules and retained failures (see :mod:`r10.papertrade`).
    """
    raise ClaimFirewallError(
        "refused: no personalized investment advice and no trade "
        "execution from a source message. Investment notes are private "
        "hypotheses; validation is blinded paper trading only.")


#: The outputs the firewall DOES permit for a quarantined category.
ALLOWED_OUTPUTS = (
    "provenance record",
    "pointer to primary peer-reviewed literature",
    "harm analysis",
    "privacy-safe null result",
    "explicit UNSUPPORTED verdict",
)


def claimfirewall_report() -> dict:
    return {
        "what_this_is": (
            "a content-claim firewall that preserves dangerous or "
            "unsupported source claims as records while refusing to act "
            "on, promote, or publicly reproduce them"),
        "distinct_from": (
            "r10.firewall, which keeps private material out of the public "
            "tree; this keeps unsupported claims out of findings"),
        "quarantine_categories": [q.value for q in Quarantine],
        "allowed_statuses": list(ALLOWED_STATUSES),
        "forbidden_promotions": list(FORBIDDEN_PROMOTIONS),
        "allowed_outputs": list(ALLOWED_OUTPUTS),
        "evidence_class": "SOURCE_CLAIM",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": "UNSUPPORTED",
        "what_this_does_not_say": (
            "It does not say any biological, medical, human-"
            "classification, or financial claim is true, and it does not "
            "identify, accuse, diagnose, or advise. It records that a "
            "claim was made and refuses to do anything more with it than "
            "hold it and mark it unsupported."),
    }
