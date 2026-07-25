"""P44 -- alias ranking, regions, and heatmaps (ambiguity without fake precision).

The final stage of the inverse decoder. A legacy search (P43) returns an alias
set of 0..N candidates; this module (1) **ranks** them by *predeclared* rules
only, and (2) where a unique point is unavailable, expresses the ambiguity as a
**region** or a **heatmap** -- reusing :mod:`cwatlas.uncertainty` -- with an
explicit area and search-space accounting. Architecture spec, Decode behavior:

    insufficient calibration -> region, heatmap, or refusal, never invented precision

Ranking is by two predeclared quantities and a deterministic tie-break:

1. **score** (relative admissibility, higher first);
2. **description length** in bits, ``log2(search_space_count)`` -- the minimum
   description length of the candidate's input space; a *smaller* search space
   is a *shorter* description and ranks higher when scores tie;
3. **codec id** (ascending), so the order is fully deterministic.

Nothing here collapses a region to a point without an explicit justification:
that is invented precision, and it is a typed refusal routed through
:func:`cwatlas.uncertainty.refuse_invented_precision`.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED

Deterministic; epochs and centres are passed in. No wall-clock.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from cwatlas import claims, uncertainty
from cwatlas.codec_registry import AliasCandidate, AliasSet
from cwatlas.uncertainty import ErrorRegion

#: The single predeclared ranking rule. Ranking never consults a known
#: destination or any evidence outside these fields (invariant: no
#: destination-driven selection).
RANKING_RULE = "score_desc__description_length_asc__codec_id_asc"


class AliasRegionError(ValueError):
    """Raised on an invalid ranking / region request."""


def description_length_bits(search_space_count: int) -> float:
    """Minimum description length of a candidate's input space, in bits.

    ``log2(search_space_count)``. An unknown (``<= 0``) count has no finite
    description length and sorts last (``+inf``).
    """
    if search_space_count <= 0:
        return math.inf
    return math.log2(search_space_count)


@dataclass(frozen=True)
class RankedAlias:
    """One candidate with its rank and the predeclared sort quantities."""

    rank: int
    candidate: AliasCandidate
    score: float
    description_length_bits: float
    codec_id: str

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "codec_id": self.codec_id,
            "score": self.score,
            "description_length_bits": self.description_length_bits,
            "candidate": self.candidate.to_dict(),
        }


def rank_aliases(alias_set: AliasSet) -> Tuple[RankedAlias, ...]:
    """Rank an alias set by the predeclared rule (see :data:`RANKING_RULE`).

    Deterministic and stable: higher score first; on a tie, shorter description
    length (smaller search space) first; on a further tie, ascending codec id.
    Ranks are ``1..N``. An empty set yields an empty tuple.
    """
    if not isinstance(alias_set, AliasSet):
        raise AliasRegionError("expected an AliasSet")

    def sort_key(c: AliasCandidate):
        # numpy negation keeps the "higher score first" intent explicit while
        # sorting ascending on the tuple.
        return (
            -float(c.score),
            description_length_bits(c.search_space_count),
            c.codec_id,
        )

    ordered = sorted(alias_set.candidates, key=sort_key)
    return tuple(
        RankedAlias(
            rank=i + 1,
            candidate=c,
            score=float(c.score),
            description_length_bits=description_length_bits(c.search_space_count),
            codec_id=c.codec_id,
        )
        for i, c in enumerate(ordered)
    )


@dataclass(frozen=True)
class HeatmapCell:
    """One ranked alias, its error region, and its normalized weight."""

    ranked: RankedAlias
    region: ErrorRegion
    weight: float

    def to_dict(self) -> dict:
        return {
            "rank": self.ranked.rank,
            "codec_id": self.ranked.codec_id,
            "weight": self.weight,
            "area_m2": self.region.area_m2,
            "search_space_count": self.region.search_space_count,
        }


@dataclass(frozen=True)
class AliasHeatmap:
    """A weighted set of error regions over one centre -- ambiguity, mapped.

    Produced when a unique point is unavailable. Weights are the normalized
    scores (they sum to 1 over a non-empty heatmap). ``total_area_m2`` and
    ``search_space_total`` make the residual ambiguity explicit rather than
    hiding it behind a single pin.
    """

    center: Tuple[float, float]
    cells: Tuple[HeatmapCell, ...]
    total_area_m2: float
    search_space_total: int

    def is_empty(self) -> bool:
        return not self.cells

    def to_dict(self) -> dict:
        return {
            "center": list(self.center),
            "count": len(self.cells),
            "total_area_m2": self.total_area_m2,
            "search_space_total": self.search_space_total,
            "cells": [c.to_dict() for c in self.cells],
        }


def region_for_uncertainty(
    center: Tuple[float, float],
    input_sigma_m: float,
    quantization_m: float,
    cell_size_m: float,
    *,
    k_sigma: float = uncertainty.DEFAULT_K_SIGMA,
    justification: str = "",
) -> ErrorRegion:
    """A circular error region for one candidate (reuses P32 uncertainty).

    Thin, explicit wrapper over :func:`cwatlas.uncertainty.propagate_circle`:
    the area scales with the supplied uncertainty, and a collapse to a point
    without justification is refused there.
    """
    return uncertainty.propagate_circle(
        center=center,
        input_sigma_m=input_sigma_m,
        quantization_m=quantization_m,
        cell_size_m=cell_size_m,
        k_sigma=k_sigma,
        justification=justification,
    )


def alias_heatmap(
    ranked: Tuple[RankedAlias, ...],
    center: Tuple[float, float],
    *,
    per_alias_sigma_m: float,
    quantization_m: float,
    cell_size_m: float,
    k_sigma: float = uncertainty.DEFAULT_K_SIGMA,
) -> AliasHeatmap:
    """Build a weighted heatmap of error regions from ranked aliases.

    Each candidate gets a circular region whose input sigma scales with its own
    ``uncertainty`` (``per_alias_sigma_m * uncertainty``) so a weaker candidate
    spreads over a larger area. Weights are normalized scores. Never collapses
    to a point.
    """
    if not ranked:
        return AliasHeatmap(center=(float(center[0]), float(center[1])),
                            cells=(), total_area_m2=0.0, search_space_total=0)
    if not math.isfinite(per_alias_sigma_m) or per_alias_sigma_m <= 0.0:
        raise AliasRegionError("per_alias_sigma_m must be positive and finite")

    scores = np.array([r.score for r in ranked], dtype=float)
    score_sum = float(scores.sum())
    if score_sum <= 0.0:
        # Degenerate scores -> uniform weights, still no invented precision.
        weights = np.full(len(ranked), 1.0 / len(ranked))
    else:
        weights = scores / score_sum

    cells = []
    for r, w in zip(ranked, weights):
        cand_sigma = per_alias_sigma_m * float(r.candidate.uncertainty)
        # A zero-uncertainty candidate still gets the quantization floor via the
        # quantization term, so the region never collapses to a point.
        region = region_for_uncertainty(
            center=center,
            input_sigma_m=cand_sigma,
            quantization_m=quantization_m,
            cell_size_m=cell_size_m,
            k_sigma=k_sigma,
        )
        cells.append(HeatmapCell(ranked=r, region=region, weight=float(w)))

    total_area = float(np.sum([c.region.area_m2 for c in cells]))
    search_total = int(sum(
        c.ranked.candidate.search_space_count
        for c in cells
        if c.ranked.candidate.search_space_count > 0
    ))
    return AliasHeatmap(
        center=(float(center[0]), float(center[1])),
        cells=tuple(cells),
        total_area_m2=total_area,
        search_space_total=search_total,
    )


def collapse_region_to_point(
    region: ErrorRegion,
    *,
    justification: str,
) -> dict:
    """Collapse a region to its centre point -- only with a justification.

    Without a non-empty ``justification`` this is invented precision and is
    refused via :func:`cwatlas.uncertainty.refuse_invented_precision`. With one,
    the caller has taken explicit responsibility for the collapse, which is
    recorded on the returned point.
    """
    if not justification:
        uncertainty.refuse_invented_precision()  # always raises
    return {
        "latitude_deg": region.center[0],
        "longitude_deg": region.center[1],
        "collapsed_from_area_m2": region.area_m2,
        "justification": justification,
    }


def resolve_alias_set(
    alias_set: AliasSet,
    center: Tuple[float, float],
    *,
    per_alias_sigma_m: float,
    quantization_m: float,
    cell_size_m: float,
    k_sigma: float = uncertainty.DEFAULT_K_SIGMA,
) -> Tuple[Tuple[RankedAlias, ...], Optional[AliasHeatmap]]:
    """Rank an alias set and express residual ambiguity as a heatmap.

    Returns ``(ranked, heatmap)``. The heatmap is ``None`` for an empty alias
    set (there is nothing to map -- a refusal upstream), otherwise a weighted
    region heatmap. A unique point is never invented from a multi-candidate set.
    """
    ranked = rank_aliases(alias_set)
    if not ranked:
        return ranked, None
    heatmap = alias_heatmap(
        ranked, center,
        per_alias_sigma_m=per_alias_sigma_m,
        quantization_m=quantization_m,
        cell_size_m=cell_size_m,
        k_sigma=k_sigma,
    )
    return ranked, heatmap


def alias_regions_report() -> dict:
    """P44 declaration receipt. Ranked ambiguity, mapped without fake precision."""
    return {
        "module": "cwatlas.alias_regions",
        "phase_id": "P44",
        "tranche": "T06",
        "ranking_rule": RANKING_RULE,
        "region_kinds": [k.value for k in uncertainty.RegionKind],
        "decode_behavior": (
            "insufficient calibration -> region, heatmap, or refusal, never "
            "invented precision; region area scales with uncertainty"),
        "claim_class": claims.ClaimClass.LEGACY_ALIAS_CANDIDATE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "ALIAS_RANKING_REGIONS_HEATMAPS_NO_INVENTED_PRECISION",
        "what_this_does_not_say": (
            "Ranking orders candidates by predeclared score and description "
            "length only; it never consults a known destination and never "
            "promotes the top-ranked alias to a decoded location. A region or "
            "heatmap is expressed ambiguity, not a pin, and it is never "
            "collapsed to a point without an explicit justification."),
    }
