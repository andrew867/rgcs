"""P43 -- legacy candidate codec search (vector -> alias set, 0..N).

The legacy arm of the inverse decoder. Architecture spec, Decode behavior:

    legacy vector -> zero or more candidates with score and uncertainty

Where canonical decode (P42) resolves a self-describing CW-GEO-1 vector to
exactly one point, legacy decode faces an ambiguous *found* string. This module
runs **every registered legacy codec** (via
:func:`cwatlas.codec_registry.build_default_registry`) over one raw source
vector and gathers **all admissible candidates** into an
:class:`~cwatlas.codec_registry.AliasSet` -- zero, one, or many, each carrying
its ``codec_id``, ``score``, ``uncertainty``, and ``search_space_count``.

It **never forces one pin** (System Contract invariant 4) and it **never
returns a location**: a source vector yields candidates or a refusal, never a
decoded destination. Asking this module to treat the source as geographic, or
to collapse a multi-candidate set to a single pin, is a typed refusal routed
through :mod:`cwatlas.claims`.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Deterministic: candidate order follows the registry's sorted codec ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

from cwatlas import claims
from cwatlas.codec_registry import (
    AliasCandidate,
    AliasSet,
    CodecRegistry,
    build_default_registry,
)
from cwatlas.ingest import IngestedVector


class LegacySearchError(ValueError):
    """Raised on a malformed legacy-search request."""


class SearchStatus(Enum):
    """The explicit outcomes of a legacy candidate search."""

    OK_ALIAS_SET = "OK_ALIAS_SET"  # one or more admissible candidates
    REFUSAL = "REFUSAL"  # no legacy codec admitted the vector


@dataclass(frozen=True)
class LegacySearchResult:
    """The result of running the legacy codecs over one raw source vector.

    ``alias_set`` holds 0..N :class:`AliasCandidate` decodes.
    ``search_space_total`` sums the candidates' declared search-space counts
    (skipping any that report ``-1``, i.e. unknown). The result is candidates
    or a refusal; it is never a location.
    """

    raw: str
    status: SearchStatus
    alias_set: AliasSet
    search_space_total: int
    reason: str
    claim_class: str

    def candidate_count(self) -> int:
        return len(self.alias_set)

    def is_empty(self) -> bool:
        return self.alias_set.is_empty()

    def require_unique_pin(self) -> AliasCandidate:
        """Return the sole candidate, or refuse (invariant 4).

        A genuinely unique decode (exactly one candidate) is returned. Zero or
        many candidates is refused -- forcing one pin invents precision.
        """
        return self.alias_set.require_unique_pin()

    def refuse_as_location(self, *_a, **_k) -> None:
        """A legacy source vector does not identify a real place -- refuse."""
        claims.refuse_source_as_geographic()

    def to_dict(self) -> dict:
        return {
            "raw": self.raw,
            "status": self.status.value,
            "count": self.candidate_count(),
            "search_space_total": self.search_space_total,
            "alias_set": self.alias_set.to_dict(),
            "reason": self.reason,
            "claim_class": self.claim_class,
        }


def _sum_search_space(alias_set: AliasSet) -> int:
    """Sum declared search-space counts, skipping unknown (``-1``) reports."""
    total = 0
    for candidate in alias_set.candidates:
        n = candidate.search_space_count
        if n > 0:
            total += n
    return total


def search_legacy(
    raw: str,
    *,
    registry: Optional[CodecRegistry] = None,
) -> LegacySearchResult:
    """Run all registered legacy codecs over ``raw`` and gather an alias set.

    Returns a :class:`LegacySearchResult` whose status is
    :attr:`SearchStatus.OK_ALIAS_SET` when one or more codecs admitted the
    vector, else :attr:`SearchStatus.REFUSAL`. Never forces a pin; never
    returns a location.
    """
    if not isinstance(raw, str):
        raise LegacySearchError(f"raw must be a str, got {type(raw).__name__}")
    reg = registry or build_default_registry()
    alias_set = reg.decode_all(raw)
    total = _sum_search_space(alias_set)
    if alias_set.is_empty():
        return LegacySearchResult(
            raw=raw,
            status=SearchStatus.REFUSAL,
            alias_set=alias_set,
            search_space_total=0,
            reason=(
                "no registered legacy codec admitted this vector; a refusal, "
                "not an invented decode"),
            claim_class=claims.ClaimClass.REFUSAL.value,
        )
    return LegacySearchResult(
        raw=raw,
        status=SearchStatus.OK_ALIAS_SET,
        alias_set=alias_set,
        search_space_total=total,
        reason=(
            f"{len(alias_set)} admissible legacy candidate(s); no pin forced "
            f"(invariant 4)"),
        claim_class=claims.ClaimClass.LEGACY_ALIAS_CANDIDATE.value,
    )


def search_legacy_ingested(
    ingested: IngestedVector,
    *,
    use_digits: bool = True,
    registry: Optional[CodecRegistry] = None,
) -> LegacySearchResult:
    """Search legacy codecs over an :class:`IngestedVector`.

    ``use_digits`` (default) feeds the digit-only view -- the right input for a
    numeric vector that arrived grouped or dashed -- otherwise the normalized
    (whitespace-free) view. The original bytes are never mutated; only a derived
    view is searched.
    """
    if not isinstance(ingested, IngestedVector):
        raise LegacySearchError("expected an IngestedVector")
    search_string = ingested.digits_only() if use_digits else ingested.normalized
    return search_legacy(search_string, registry=registry)


def refuse_source_as_location(*_a, **_k) -> None:
    """Module-level guard: a source vector is never a decoded location."""
    claims.refuse_source_as_geographic()


def decode_legacy_report() -> dict:
    """P43 declaration receipt. Candidates or refusal; never a pin, never a place."""
    reg = build_default_registry()
    return {
        "module": "cwatlas.decode_legacy",
        "phase_id": "P43",
        "tranche": "T06",
        "search_statuses": [s.value for s in SearchStatus],
        "legacy_codec_ids": sorted(
            getattr(c, "codec_id") for c in reg.legacy_codecs()),
        "decode_behavior": (
            "legacy vector -> zero or more LEGACY_ALIAS_CANDIDATE decodes, each "
            "with score, uncertainty, and search-space count; never one forced "
            "pin (invariant 4), never a location"),
        "claim_class": claims.ClaimClass.LEGACY_ALIAS_CANDIDATE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "LEGACY_CANDIDATE_SEARCH_ALIAS_SET_NO_FORCED_PIN",
        "what_this_does_not_say": (
            "That a legacy codec can arithmetically re-express a source string "
            "is not evidence the source intended that encoding, nor that the "
            "string identifies a place. The search returns an alias set or a "
            "refusal; source geographic semantics remain NOT_CLAIMED."),
    }
