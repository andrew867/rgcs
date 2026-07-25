"""P51 — Search-space accounting.

A "match" between a candidate decode and a target means nothing until you know
how large a space you searched to find it. Enumerate enough codecs, frames,
depths, catalogue entries, transforms, orientations, shells, epochs, anchors,
and destinations and a nearby hit is *expected by chance* — the look-everywhere
effect. This module counts the total number of hypotheses considered and reports
it **with every candidate**, so a hit in a huge space is read against the size
of the space, not celebrated in isolation.

The account is a product over named dimensions:

    total = codecs x frames x depths x catalogue x transforms x ...

Each dimension is a positive integer count of the distinct options that arm of
the search ranged over. :class:`SearchSpace` holds the named counts and computes
the product; :func:`interpret_match` charges a raw per-comparison probability
against the whole space via the Šidák family-wise value ``1 - (1 - p)^N`` and
the expected number of chance hits ``N * p`` — the same look-everywhere
arithmetic the catalogue firewall (P47) uses, generalized to the full pipeline.

The governance rule: :func:`refuse_match_without_search_space` refuses any
candidate or match reported without an attached search-space count. A match
without its denominator is not interpretable and may not be presented as one.

Everything here is arithmetic over counts; nothing is measured.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Tuple

from cwatlas.claims import ClaimClass, ClaimError

#: Default family-wise significance threshold, matching the catalogue firewall.
DEFAULT_ALPHA = 0.05

#: The canonical search dimensions of the CW Atlas pipeline, in report order.
CANONICAL_DIMENSIONS = (
    "codecs", "frames", "depths", "catalogue", "transforms",
    "orientations", "shells", "epochs", "anchors", "destinations",
)


class SearchSpaceError(ValueError):
    """Raised on an invalid search-space account. Explicit result state."""


def refuse_match_without_search_space(candidate, *_a, **_k) -> None:
    """Refuse a candidate/match reported without an attached search-space count.

    A match is only interpretable against the size of the space searched to find
    it: a hit among ten hypotheses and a hit among ten million are different
    facts. A candidate presented without its search-space denominator invites
    exactly the look-everywhere error this phase exists to prevent.
    """
    has_space = False
    if isinstance(candidate, Mapping):
        n = candidate.get("search_space_total", candidate.get("search_space"))
        has_space = isinstance(n, int) and n > 0
    else:
        n = getattr(candidate, "search_space_total", None)
        has_space = isinstance(n, int) and n > 0
    if not has_space:
        raise ClaimError(
            "refused: a match/candidate was reported without a positive "
            "search_space_total. A match is meaningless without the size of the "
            "space searched to find it; attach the search-space count "
            "(SearchSpace.total()) to every candidate before interpreting it.")


@dataclass(frozen=True)
class SearchSpace:
    """A count of the total hypotheses considered, as named dimensions.

    Each entry in ``dimensions`` is a positive integer count of the distinct
    options one arm of the search ranged over. :meth:`total` is their product —
    the number of (codec, frame, depth, ...) combinations examined.
    """

    dimensions: Mapping[str, int]

    def __post_init__(self) -> None:
        dims = dict(self.dimensions)
        if not dims:
            raise SearchSpaceError("a search space needs at least one dimension")
        for name, count in dims.items():
            if not isinstance(count, int) or count < 1:
                raise SearchSpaceError(
                    f"dimension {name!r} must be a positive integer, got "
                    f"{count!r}")
        object.__setattr__(self, "dimensions", dims)

    def total(self) -> int:
        """The product of all dimension counts (an exact Python int)."""
        total = 1
        for count in self.dimensions.values():
            total *= count
        return total

    def to_dict(self) -> dict:
        return {
            "dimensions": dict(self.dimensions),
            "search_space_total": self.total(),
        }


def count_search_space(**dimensions: int) -> SearchSpace:
    """Build a :class:`SearchSpace` from keyword dimension counts.

    Example::

        count_search_space(codecs=4, frames=3, depths=8, catalogue=5,
                           transforms=6)
    """
    return SearchSpace(dimensions=dict(dimensions))


@dataclass(frozen=True)
class MatchInterpretation:
    """A raw match read against the size of the space searched.

    ``adjusted_p`` is the Šidák family-wise probability of at least one chance
    hit across the whole space; ``expected_chance_hits`` is ``total * p``. A
    match is ``surprising`` only if the family-wise value clears ``alpha``.
    """

    search_space_total: int
    per_comparison_p: float
    adjusted_p: float
    expected_chance_hits: float
    alpha: float
    surprising_after_accounting: bool
    claim_class: str
    justification: str


def interpret_match(space: SearchSpace,
                    per_comparison_p: float,
                    alpha: float = DEFAULT_ALPHA) -> MatchInterpretation:
    """Interpret a raw per-comparison probability against ``space``.

    ``per_comparison_p`` is the chance that a single random comparison would
    match (e.g. a spherical-cap fraction). The family-wise adjusted probability
    of at least one chance hit across the whole search space is
    ``1 - (1 - p)^N``; the expected number of chance hits is ``N * p``. A raw
    hit that looks impressive shrinks toward certainty once ``N`` is large.
    """
    if not isinstance(space, SearchSpace):
        raise SearchSpaceError("interpret_match needs a SearchSpace")
    if not (0.0 <= per_comparison_p <= 1.0):
        raise SearchSpaceError("per_comparison_p must be in [0, 1]")
    if not (0.0 < alpha < 1.0):
        raise SearchSpaceError("alpha must be in (0, 1)")
    n = space.total()
    adjusted_p = 1.0 - (1.0 - per_comparison_p) ** n
    expected_hits = n * per_comparison_p
    surprising = adjusted_p < alpha
    if surprising:
        why = (f"even across {n} hypotheses the family-wise chance of a hit is "
               f"{adjusted_p:.4g} < alpha={alpha}; the match is surprising")
    else:
        why = (f"a hit is expected by chance across {n} hypotheses "
               f"(family-wise p={adjusted_p:.4g}, expected hits "
               f"{expected_hits:.3g}); the match is not surprising")
    return MatchInterpretation(
        search_space_total=n,
        per_comparison_p=float(per_comparison_p),
        adjusted_p=adjusted_p,
        expected_chance_hits=expected_hits,
        alpha=alpha,
        surprising_after_accounting=surprising,
        claim_class=ClaimClass.MATHEMATICAL_TRANSLATION.value,
        justification=why,
    )


def attach_search_space(candidate: dict, space: SearchSpace) -> dict:
    """Return a copy of ``candidate`` with the search-space count attached.

    The helper that keeps every candidate accountable: after this, the candidate
    passes :func:`refuse_match_without_search_space`.
    """
    out = dict(candidate)
    out["search_space_total"] = space.total()
    out["search_space"] = space.to_dict()
    return out


def search_space_report() -> dict:
    """P51 declaration receipt. Every match is read against the space searched."""
    space = count_search_space(
        codecs=4, frames=3, depths=8, catalogue=5, transforms=6,
        orientations=2, shells=9, epochs=3, anchors=12, destinations=20)
    # A tight 5 km cap on Earth: per-comparison probability of a chance hit.
    per_comparison_p = 3.1e-7
    interp = interpret_match(space, per_comparison_p)
    return {
        "phase_id": "P51",
        "tranche": "T07",
        "what_this_is": (
            "search-space accounting: the total number of hypotheses considered "
            "is the product over codecs, frames, depths, catalogue entries, "
            "transforms, orientations, shells, epochs, anchors, and "
            "destinations, and it is reported with every candidate so a match is "
            "read against the size of the space searched, not in isolation."),
        "dimensions": dict(space.dimensions),
        "search_space_total": space.total(),
        "example_per_comparison_p": per_comparison_p,
        "example_adjusted_p": interp.adjusted_p,
        "example_expected_chance_hits": interp.expected_chance_hits,
        "example_surprising_after_accounting": interp.surprising_after_accounting,
        "refusals": ["refuse_match_without_search_space"],
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "GREEN_R10_8_1_P51_SEARCH_SPACE_ACCOUNTING",
        "what_this_does_not_say": (
            "It does not say any match is a decode. It states the denominator: "
            "how many hypotheses were examined, so a hit in a large space is "
            "recognized as expected by chance. A candidate reported without its "
            "search-space count is refused. All counts are illustrative; "
            "nothing is measured and no physical validation is claimed."),
    }


__all__ = [
    "SearchSpaceError", "DEFAULT_ALPHA", "CANONICAL_DIMENSIONS",
    "refuse_match_without_search_space", "SearchSpace", "count_search_space",
    "MatchInterpretation", "interpret_match", "attach_search_space",
    "search_space_report",
]
