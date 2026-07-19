"""P09 — open-legacy and IP decision gate.

R7 does not automatically make anything public. Before any public
disclosure the operator must choose exactly one path and sign the
decision:

- ``FILE_THEN_PUBLISH`` — preserve patent options, file first;
- ``DEFENSIVE_PUBLICATION`` — make it permanent public prior art;
- ``PRIVATE_RC`` — finish privately, decide later.

Only ``PRIVATE_RC`` is reversible. Publication cannot be withdrawn:
once an enabling disclosure is public it is public, and in
strict-novelty jurisdictions it destroys the novelty of the disclosed
subject matter immediately. Filing first forecloses nothing, so the
ordering of these options is not arbitrary.

This module is a gate, not advice. It enforces that a decision exists
and is signed before :func:`authorize_publication` will return true.
It cannot tell anyone whether to patent, and it says so.

**A git commit is evidence of a date. It is not a patent filing, not a
defensive publication, and not legal advice.** That distinction is the
one most likely to be got wrong by a technically-minded person who
reasons that a public timestamped repository "counts", so it is
enforced in code rather than mentioned in a footnote.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, asdict, field

from . import PUBLICATION_PATHS

#: Requirements each path must satisfy before it can be acted on.
PATH_REQUIREMENTS: dict[str, tuple[str, ...]] = {
    "FILE_THEN_PUBLISH": (
        "registered_patent_agent_consulted",
        "invention_inventory",
        "inventor_list",
        "prior_disclosure_history",
        "prior_art_search",
        "enabling_specification",
        "jurisdiction_strategy",
        "filing_receipt",
        "publication_after_filing",
        "open_source_patent_policy",
    ),
    "DEFENSIVE_PUBLICATION": (
        "complete_enabling_disclosure",
        "architecture_methods_equations_code_vectors_drawings",
        "limitations_documented",
        "immutable_timestamp_and_hash",
        "archival_copies",
        "explicit_open_licence",
        "patent_non_assertion_reviewed_by_counsel",
        "attribution_and_correction_mechanism",
    ),
    "PRIVATE_RC": (
        "artifacts_preserved",
        "nothing_new_published",
    ),
}

#: Paths that cannot be undone once executed.
IRREVERSIBLE_PATHS = ("FILE_THEN_PUBLISH", "DEFENSIVE_PUBLICATION")


class PublicationRefused(RuntimeError):
    """Raised when publication is attempted without a signed decision."""


@dataclass(frozen=True)
class DecisionRecord:
    """A signed choice of publication path.

    ``signed_by`` is required and ``rationale`` must be substantive:
    an unsigned or unexplained record is treated as no decision at
    all, because the whole point of the gate is that a human made a
    deliberate choice.
    """

    path: str
    signed_by: str
    signed_at: str
    rationale: str
    evidence: dict = field(default_factory=dict)
    legal_advice_obtained: bool = False

    def __post_init__(self) -> None:
        if self.path not in PUBLICATION_PATHS:
            raise ValueError(f"unknown publication path {self.path!r}")
        if not self.signed_by.strip():
            raise ValueError(
                "a decision record must name who signed it")
        if len(self.rationale.strip()) < 20:
            raise ValueError(
                "a decision record must carry a substantive rationale")
        if self.path == "FILE_THEN_PUBLISH" and \
                not self.legal_advice_obtained:
            raise ValueError(
                "FILE_THEN_PUBLISH requires a registered patent agent; "
                "this module cannot substitute for one")

    def digest(self) -> str:
        blob = json.dumps(
            {"path": self.path, "signed_by": self.signed_by,
             "signed_at": self.signed_at,
             "rationale": self.rationale,
             "evidence": self.evidence},
            sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()

    def missing_requirements(self) -> tuple[str, ...]:
        return tuple(r for r in PATH_REQUIREMENTS[self.path]
                     if not self.evidence.get(r))

    def is_complete(self) -> bool:
        return not self.missing_requirements()

    def as_record(self) -> dict:
        d = asdict(self)
        d["digest"] = self.digest()
        d["missing_requirements"] = list(self.missing_requirements())
        d["complete"] = self.is_complete()
        d["reversible"] = self.path not in IRREVERSIBLE_PATHS
        return d


def authorize_publication(decision: DecisionRecord | None) -> dict:
    """The gate. Returns whether public disclosure may proceed."""
    if decision is None:
        raise PublicationRefused(
            "no signed decision record exists. R7 does not "
            "automatically make the repository public; the operator "
            "must choose exactly one path and sign it (core/09).")
    if decision.path == "PRIVATE_RC":
        return {
            "authorized": False,
            "path": decision.path,
            "digest": decision.digest(),
            "status": "PRIVATE_RC_NOTHING_PUBLISHED",
            "note": ("PRIVATE_RC is a decision to publish nothing new. "
                     "It is the only reversible option: FILE_THEN_"
                     "PUBLISH and DEFENSIVE_PUBLICATION can both be "
                     "chosen later, and neither can be undone once "
                     "chosen."),
        }
    if not decision.is_complete():
        raise PublicationRefused(
            f"{decision.path} is missing required evidence: "
            f"{', '.join(decision.missing_requirements())}")
    return {
        "authorized": True,
        "path": decision.path,
        "digest": decision.digest(),
        "status": "PUBLICATION_AUTHORIZED",
        "note": "all declared requirements for this path are recorded",
    }


def commit_is_not_a_filing() -> dict:
    """The distinction most likely to be got wrong, stated plainly."""
    return {
        "git_commit_provides": [
            "evidence of a date, if the repository history is "
            "preserved and trusted",
            "a content hash that shows the text has not changed since",
        ],
        "git_commit_does_not_provide": [
            "a patent filing or any priority date",
            "a defensive publication in the legal sense",
            "publication at all, while the repository is private",
            "an enabling disclosure organized for a searcher to find",
            "legal advice of any kind",
        ],
        "why_it_matters": (
            "A private repository discloses nothing, so it neither "
            "establishes prior art nor endangers novelty. Making it "
            "public is the act that does both at once -- it creates "
            "prior art against others and destroys novelty for the "
            "author. Those happen in the same instant and cannot be "
            "separated after the fact."),
        "status": "NOT_LEGAL_ADVICE",
    }


def path_comparison() -> dict:
    """What each path costs and forecloses."""
    return {
        "FILE_THEN_PUBLISH": {
            "preserves_patent_rights": True,
            "creates_public_prior_art": "after filing",
            "reversible": False,
            "requires_professional": True,
            "cost": "patent agent fees plus filing fees, per "
                    "jurisdiction",
            "forecloses": "nothing, if filing precedes any disclosure",
        },
        "DEFENSIVE_PUBLICATION": {
            "preserves_patent_rights": False,
            "creates_public_prior_art": "immediately",
            "reversible": False,
            "requires_professional": "counsel review of the "
                                     "non-assertion policy",
            "cost": "archival and preparation effort",
            "forecloses": "the author's own ability to patent the "
                          "disclosed subject matter in most "
                          "jurisdictions",
        },
        "PRIVATE_RC": {
            "preserves_patent_rights": True,
            "creates_public_prior_art": False,
            "reversible": True,
            "requires_professional": False,
            "cost": "none",
            "forecloses": "nothing",
        },
        "ordering_note": (
            "The options are not symmetric. PRIVATE_RC preserves both "
            "other paths. FILE_THEN_PUBLISH preserves the ability to "
            "publish. DEFENSIVE_PUBLICATION preserves neither. Choose "
            "the reversible option when the decision is unresolved."),
        "disclaimer": (
            "This comparison is a summary of the pack's own guidance "
            "and is not legal advice. Grace periods, jurisdictional "
            "rules and what counts as an enabling disclosure are "
            "questions for a registered patent agent."),
    }


def private_rc_decision(signed_by: str, signed_at: str,
                        rationale: str) -> DecisionRecord:
    """Construct the PRIVATE_RC record, the reversible default."""
    return DecisionRecord(
        path="PRIVATE_RC", signed_by=signed_by, signed_at=signed_at,
        rationale=rationale,
        evidence={"artifacts_preserved": True,
                  "nothing_new_published": True})


def refuse_publication_without_decision(*args, **kwargs):
    """Always refuses. Kept so the refusal is callable and testable."""
    raise PublicationRefused(
        "public publication requires a signed decision record naming "
        "one of FILE_THEN_PUBLISH, DEFENSIVE_PUBLICATION or "
        "PRIVATE_RC. A commit date is not a substitute "
        "(r7 FORBIDDEN_COLLAPSES: COMMIT_DATE_IS_LEGAL_PRIORITY).")
