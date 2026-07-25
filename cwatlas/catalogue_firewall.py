"""P47 — Geographic catalogue and selection-bias firewall.

When a candidate decode is scored against a catalogue of notable places, a
match to a famous site is **expected by chance** once you account for the
look-everywhere effect: many candidate decodes times many catalogue entries is
a large search space, and a nearby "hit" is cheap. This module corrects for
that inflation and refuses a catalogue match as evidence without a prospective
test.

The correction:

* the **search-space size** is ``n_candidates * len(catalogue)`` comparisons;
* the **per-comparison probability** that a random point lands within the match
  radius of a given catalogue entry is the spherical cap fraction
  ``(1 - cos(radius)) / 2``;
* the **look-everywhere-adjusted** probability of at least one chance hit
  across the whole search space is the Šidák family-wise value
  ``1 - (1 - p)^N``. A single raw hit that looks impressive shrinks to
  near-certainty once ``N`` is large.

A catalogue match is only *evidence* if it survives a **prospective** test
(frozen transform, unseen target). Without it,
:func:`refuse_catalogue_match_as_evidence` raises. Catalogue entries are
synthetic.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence, Tuple

from cwatlas.calibration import great_circle_m
from cwatlas.claims import ClaimClass, ClaimError

#: Mean Earth radius (metres), matching :mod:`cwatlas.calibration`.
_EARTH_RADIUS_M = 6_371_000.0
#: Default family-wise significance threshold.
DEFAULT_ALPHA = 0.05


class FirewallError(ValueError):
    """Raised on an invalid firewall input. An explicit result state."""


def refuse_catalogue_match_as_evidence(*_a, **_k) -> None:
    """A catalogue match is not evidence without a prospective test."""
    raise ClaimError(
        "refused: a match between a candidate decode and a famous catalogue "
        "site is expected by chance across a large search space (the look-"
        "everywhere effect). It is not evidence of intended encoding without a "
        "prospective test: freeze the transform, then decode an unseen target.")


@dataclass(frozen=True)
class CatalogueEntry:
    """A notable place in the catalogue. Synthetic coordinates only."""

    name: str
    point: Tuple[float, float]  # (lat, lon)
    synthetic: bool = True

    def __post_init__(self) -> None:
        lat, lon = float(self.point[0]), float(self.point[1])
        if not (-90.0 <= lat <= 90.0):
            raise FirewallError(f"latitude must be in [-90, 90], got {lat}.")
        object.__setattr__(self, "point", (lat, lon))


@dataclass(frozen=True)
class CatalogueMatch:
    """One catalogue entry within the match radius of a candidate."""

    entry_name: str
    distance_m: float
    within_radius: bool


@dataclass(frozen=True)
class FirewallResult:
    """A selection-bias-corrected scoring of a candidate against a catalogue."""

    matches: Tuple[CatalogueMatch, ...]
    hit_count: int
    search_space_size: int
    per_comparison_p: float
    adjusted_p: float          # look-everywhere family-wise probability
    expected_chance_hits: float
    alpha: float
    significant_after_correction: bool
    prospective_test_passed: bool
    is_evidence: bool
    claim_class: str
    justification: str


def build_synthetic_catalogue() -> Tuple[CatalogueEntry, ...]:
    """A small synthetic catalogue of notable-place stand-ins.

    Names are generic; coordinates are invented, not real site coordinates.
    """
    return (
        CatalogueEntry("Synthetic Monument A", (10.0, 20.0)),
        CatalogueEntry("Synthetic Monument B", (-15.0, 55.0)),
        CatalogueEntry("Synthetic Landmark C", (40.0, -30.0)),
        CatalogueEntry("Synthetic Landmark D", (-45.0, 120.0)),
        CatalogueEntry("Synthetic Site E", (5.0, -75.0)),
    )


def _cap_fraction(radius_m: float) -> float:
    """Spherical-cap area fraction for an angular radius of ``radius_m``."""
    angular = radius_m / _EARTH_RADIUS_M
    if angular >= math.pi:
        return 1.0
    return (1.0 - math.cos(angular)) / 2.0


def score_candidate(candidate_point: Tuple[float, float],
                    catalogue: Sequence[CatalogueEntry],
                    match_radius_m: float,
                    n_candidates: int = 1,
                    alpha: float = DEFAULT_ALPHA,
                    prospective_test_passed: bool = False) -> FirewallResult:
    """Score a candidate against a catalogue with a look-everywhere correction.

    ``n_candidates`` is how many candidate decodes were examined; the effective
    search space is ``n_candidates * len(catalogue)``. Returns the raw per-
    comparison probability and the Šidák family-wise adjusted probability. A
    match is evidence only if it is both significant after correction **and**
    backed by a passed prospective test.
    """
    if not catalogue:
        raise FirewallError("catalogue must be non-empty.")
    if not (math.isfinite(match_radius_m) and match_radius_m > 0.0):
        raise FirewallError("match_radius_m must be positive and finite.")
    if n_candidates < 1:
        raise FirewallError("n_candidates must be >= 1.")
    if not (0.0 < alpha < 1.0):
        raise FirewallError("alpha must be in (0, 1).")

    matches = []
    hits = 0
    for entry in catalogue:
        d = great_circle_m(candidate_point, entry.point)
        within = d <= match_radius_m
        if within:
            hits += 1
        matches.append(CatalogueMatch(entry.name, d, within))

    per_comparison_p = _cap_fraction(match_radius_m)
    search_space = n_candidates * len(catalogue)
    # Šidák family-wise probability of >=1 chance hit across the search space.
    adjusted_p = 1.0 - (1.0 - per_comparison_p) ** search_space
    expected_hits = search_space * per_comparison_p
    significant = adjusted_p < alpha
    is_evidence = bool(significant and prospective_test_passed)

    if is_evidence:
        claim = ClaimClass.CALIBRATED_MAPPING.value
        why = ("match is significant after look-everywhere correction and "
               "survived a prospective test")
    elif significant and not prospective_test_passed:
        claim = ClaimClass.OPERATOR_HYPOTHESIS.value
        why = ("match survives the look-everywhere correction but lacks a "
               "prospective test; it is a hypothesis, not evidence")
    else:
        claim = ClaimClass.MATHEMATICAL_TRANSLATION.value
        why = (f"a hit is expected by chance across {search_space} comparisons "
               f"(adjusted p={adjusted_p:.4f}); not significant")

    return FirewallResult(
        matches=tuple(matches),
        hit_count=hits,
        search_space_size=search_space,
        per_comparison_p=per_comparison_p,
        adjusted_p=adjusted_p,
        expected_chance_hits=expected_hits,
        alpha=alpha,
        significant_after_correction=significant,
        prospective_test_passed=prospective_test_passed,
        is_evidence=is_evidence,
        claim_class=claim,
        justification=why,
    )


def assert_catalogue_match_is_evidence(result: FirewallResult) -> None:
    """Treating a catalogue match as evidence is refused unless it earned it.

    Raises via :func:`refuse_catalogue_match_as_evidence` whenever the result
    is not backed by a passed prospective test.
    """
    if not result.prospective_test_passed:
        refuse_catalogue_match_as_evidence()


def catalogue_firewall_report() -> dict:
    """P47 declaration receipt."""
    return {
        "phase_id": "P47",
        "what_this_is": (
            "a geographic catalogue and selection-bias firewall: scoring a "
            "candidate against a catalogue corrects for the look-everywhere "
            "effect (search space = n_candidates x catalogue size) via a Šidák "
            "family-wise adjusted probability, reports the search-space size, "
            "and refuses a famous-site match as evidence without a prospective "
            "test."),
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "look_everywhere_corrected": True,
        "catalogue_is_synthetic": True,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "SELECTION_BIAS_FIREWALL_NO_CATALOGUE_MATCH_AS_EVIDENCE",
    }
