"""P52 — Multiple-hypothesis and description-length scoring.

The best *raw* match is rarely the best *explanation*. A codec with enough free
parameters can drive its residual to zero on any target — an ornate
retrospective fit — and if you searched a large space of such codecs, the
prettiest hit is expected by chance. This module charges both costs: the
**description length** (how many bits it takes to specify the codec, its
parameters, and the residual it leaves) and the **multiplicity** of the search
(a multiple-comparison correction over the whole search space). A compact
mapping that predicts is preferred over an elaborate one that merely fits.

Description length (a two-part MDL):

    L(candidate) = codec_bits + param_bits + residual_bits

Fewer bits is a better explanation. A candidate that fits the target exactly but
needs many bits to specify its parameters can lose to one that fits slightly
worse but is far cheaper to describe — the shorter description generalizes.

Multiplicity: a raw p-value that looks significant must be corrected for the
number of hypotheses examined. Three corrections are provided —

* **Bonferroni**: ``p_adj = min(1, p * m)`` — the most conservative;
* **Šidák**: ``p_adj = 1 - (1 - p)^m`` — exact under independence;
* **Benjamini–Hochberg**: controls the false-discovery rate across a family.

The governance rule: :func:`refuse_uncorrected_multiplicity` refuses any claim
that a match is significant when no multiple-comparison correction has been
applied over the search space. An uncorrected p-value in a large search is a
look-everywhere artefact, not evidence.

Everything here is arithmetic over bit counts and probabilities; nothing is
measured.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Sequence, Tuple

from cwatlas.claims import ClaimClass, ClaimError
from cwatlas.search_space import SearchSpace

#: Default family-wise significance threshold.
DEFAULT_ALPHA = 0.05


class MDLError(ValueError):
    """Raised on an invalid MDL / correction request. Explicit result state."""


class Correction(Enum):
    """The multiple-comparison corrections available."""

    BONFERRONI = "BONFERRONI"
    SIDAK = "SIDAK"
    BENJAMINI_HOCHBERG = "BENJAMINI_HOCHBERG"


def refuse_uncorrected_multiplicity(*_a, **_k) -> None:
    """Refuse a significance claim made without a multiplicity correction.

    A raw p-value that clears ``alpha`` means nothing once it is the best of a
    large search: across ``m`` hypotheses a chance hit below ``alpha`` is
    expected. A match may be called significant only after a correction over the
    search space has been applied.
    """
    raise ClaimError(
        "refused: a match was called significant without correcting for the "
        "number of hypotheses searched. The best raw p-value in a large space "
        "is a look-everywhere artefact; apply a Bonferroni, Šidák, or "
        "Benjamini–Hochberg correction over the search space before claiming "
        "significance.")


# --------------------------------------------------------------------------- #
# Description length
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class Candidate:
    """A hypothesis: a codec, its parameters, the residual it leaves, a p-value.

    ``codec_bits`` specifies which codec, ``param_bits`` its parameters, and
    ``residual_bits`` the leftover the codec did not explain. ``p_value`` is the
    raw per-comparison probability of a match this good by chance.
    """

    name: str
    codec_bits: float
    param_bits: float
    residual_bits: float
    p_value: float

    def __post_init__(self) -> None:
        for f in ("codec_bits", "param_bits", "residual_bits"):
            v = getattr(self, f)
            if not (math.isfinite(v) and v >= 0.0):
                raise MDLError(f"{f} must be a finite non-negative number")
        if not (0.0 <= self.p_value <= 1.0):
            raise MDLError("p_value must be in [0, 1]")

    def description_length(self) -> float:
        """Total bits to specify this candidate (lower is a better explanation)."""
        return self.codec_bits + self.param_bits + self.residual_bits


def description_length_bits(codec_bits: float, param_bits: float,
                            residual_bits: float) -> float:
    """The two-part MDL: ``codec_bits + param_bits + residual_bits``."""
    for name, v in (("codec_bits", codec_bits), ("param_bits", param_bits),
                    ("residual_bits", residual_bits)):
        if not (math.isfinite(v) and v >= 0.0):
            raise MDLError(f"{name} must be finite and non-negative")
    return codec_bits + param_bits + residual_bits


# --------------------------------------------------------------------------- #
# Multiple-comparison corrections
# --------------------------------------------------------------------------- #

def bonferroni(p: float, m: int) -> float:
    """Bonferroni-adjusted p-value: ``min(1, p * m)``."""
    if m < 1:
        raise MDLError("m (number of hypotheses) must be >= 1")
    return min(1.0, p * m)


def sidak(p: float, m: int) -> float:
    """Šidák-adjusted p-value: ``1 - (1 - p)^m`` (exact under independence)."""
    if m < 1:
        raise MDLError("m (number of hypotheses) must be >= 1")
    return 1.0 - (1.0 - p) ** m


def benjamini_hochberg(pvalues: Sequence[float],
                       alpha: float = DEFAULT_ALPHA) -> Tuple[bool, ...]:
    """Benjamini–Hochberg FDR decisions for a family of p-values.

    Returns, in the input order, a boolean per hypothesis: True where the
    hypothesis is rejected (declared a discovery) at false-discovery-rate
    ``alpha``. Controls the expected fraction of false discoveries rather than
    the family-wise error rate, so it is less conservative than Bonferroni.
    """
    ps = list(pvalues)
    m = len(ps)
    if m == 0:
        raise MDLError("benjamini_hochberg needs at least one p-value")
    if not (0.0 < alpha < 1.0):
        raise MDLError("alpha must be in (0, 1)")
    order = sorted(range(m), key=lambda i: ps[i])
    max_k = -1
    for rank, idx in enumerate(order, start=1):
        if ps[idx] <= (rank / m) * alpha:
            max_k = rank
    reject = [False] * m
    if max_k > 0:
        for rank, idx in enumerate(order, start=1):
            if rank <= max_k:
                reject[idx] = True
    return tuple(reject)


def correct_pvalue(p: float, m: int, method: Correction) -> float:
    """Apply a single-value correction (Bonferroni or Šidák) for ``m`` tests."""
    if not (0.0 <= p <= 1.0):
        raise MDLError("p must be in [0, 1]")
    if method is Correction.BONFERRONI:
        return bonferroni(p, m)
    if method is Correction.SIDAK:
        return sidak(p, m)
    raise MDLError(
        "Benjamini–Hochberg operates on a family of p-values; use "
        "benjamini_hochberg() or select_best_explanation() instead.")


# --------------------------------------------------------------------------- #
# Best explanation = compact + surviving multiplicity
# --------------------------------------------------------------------------- #

@dataclass(frozen=True)
class ExplanationResult:
    """The best explanation among candidates once complexity + multiplicity charge.

    ``best_raw`` is the candidate with the smallest raw residual (the prettiest
    fit); ``best_explanation`` is the candidate with the smallest description
    length among those that survive the multiplicity correction. They need not be
    the same candidate — that is the whole point.
    """

    best_raw: str
    best_explanation: str | None
    search_space_total: int
    method: str
    alpha: float
    corrected_pvalues: dict
    survivors: Tuple[str, ...]
    description_lengths: dict
    claim_class: str
    justification: str


def select_best_explanation(candidates: Sequence[Candidate],
                            search_space: SearchSpace,
                            method: Correction = Correction.SIDAK,
                            alpha: float = DEFAULT_ALPHA) -> ExplanationResult:
    """Choose the best explanation, charging description length and multiplicity.

    1. The multiplicity ``m`` is the total size of ``search_space``.
    2. Each candidate's raw p-value is corrected for ``m`` (or the family is run
       through Benjamini–Hochberg).
    3. Among the candidates that survive the correction, the one with the
       smallest description length is the best explanation.

    The candidate with the smallest raw residual (``best_raw``) is reported too,
    to make explicit that the prettiest fit is not necessarily the best
    explanation once complexity and multiplicity are charged.
    """
    cands = list(candidates)
    if not cands:
        raise MDLError("need at least one candidate")
    if not isinstance(search_space, SearchSpace):
        raise MDLError("search_space must be a SearchSpace")
    m = search_space.total()

    best_raw = min(cands, key=lambda c: c.residual_bits).name

    if method is Correction.BENJAMINI_HOCHBERG:
        decisions = benjamini_hochberg([c.p_value for c in cands], alpha)
        survivors = tuple(c.name for c, keep in zip(cands, decisions) if keep)
        corrected = {c.name: c.p_value for c in cands}  # BH decides, not adjusts
    else:
        corrected = {c.name: correct_pvalue(c.p_value, m, method) for c in cands}
        survivors = tuple(c.name for c in cands if corrected[c.name] < alpha)

    dls = {c.name: c.description_length() for c in cands}
    if survivors:
        best_explanation = min(
            (c for c in cands if c.name in survivors),
            key=lambda c: c.description_length()).name
        why = (f"among {len(survivors)} candidate(s) surviving the {method.value} "
               f"correction over {m} hypotheses, the shortest description "
               f"({dls[best_explanation]:.1f} bits) is the best explanation; the "
               f"smallest raw residual belonged to {best_raw!r}")
    else:
        best_explanation = None
        why = (f"no candidate survived the {method.value} correction over {m} "
               f"hypotheses; the best raw match ({best_raw!r}) is a look-"
               f"everywhere artefact, not an explanation")

    return ExplanationResult(
        best_raw=best_raw,
        best_explanation=best_explanation,
        search_space_total=m,
        method=method.value,
        alpha=alpha,
        corrected_pvalues=corrected,
        survivors=survivors,
        description_lengths=dls,
        claim_class=ClaimClass.MATHEMATICAL_TRANSLATION.value,
        justification=why,
    )


def mdl_report() -> dict:
    """P52 declaration receipt. Compact + corrected beats ornate + raw."""
    space = SearchSpace({"codecs": 4, "frames": 3, "depths": 8,
                         "catalogue": 5, "transforms": 6})
    # An ornate codec with a near-zero residual but many parameter bits, and a
    # compact codec with a slightly larger residual but far fewer bits.
    ornate = Candidate("ornate_fit", codec_bits=8.0, param_bits=220.0,
                       residual_bits=0.5, p_value=0.002)
    compact = Candidate("compact_map", codec_bits=8.0, param_bits=24.0,
                        residual_bits=9.0, p_value=1e-6)
    noise = Candidate("noisy_guess", codec_bits=8.0, param_bits=40.0,
                      residual_bits=60.0, p_value=0.04)
    result = select_best_explanation([ornate, compact, noise], space,
                                     method=Correction.SIDAK)
    return {
        "phase_id": "P52",
        "tranche": "T07",
        "what_this_is": (
            "multiple-hypothesis and description-length scoring: a candidate is "
            "scored by minimum description length (bits to specify codec + "
            "parameters + residual), and its raw p-value is corrected for the "
            "number of hypotheses searched (Bonferroni / Šidák / Benjamini–"
            "Hochberg); the best raw match is not the best explanation once "
            "complexity and multiplicity are charged."),
        "search_space_total": space.total(),
        "best_raw_match": result.best_raw,
        "best_explanation": result.best_explanation,
        "description_lengths_bits": result.description_lengths,
        "corrected_pvalues": result.corrected_pvalues,
        "survivors": list(result.survivors),
        "correction_method": result.method,
        "corrections_available": [c.value for c in Correction],
        "refusals": ["refuse_uncorrected_multiplicity"],
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": ("GREEN_R10_8_1_P52_MULTIPLE_HYPOTHESIS_AND_"
                    "DESCRIPTION_LENGTH_SCORING"),
        "what_this_does_not_say": (
            "It does not say any candidate is a decode. It charges the two costs "
            "a retrospective fit hides: the bits to describe an ornate codec, "
            "and the multiplicity of the search that found it. A compact mapping "
            "that survives correction beats an elaborate one with a smaller raw "
            "residual, and a significance claim made without a multiplicity "
            "correction is refused. All values are illustrative; nothing is "
            "measured and no physical validation is claimed."),
    }


__all__ = [
    "MDLError", "Correction", "DEFAULT_ALPHA",
    "refuse_uncorrected_multiplicity", "Candidate", "description_length_bits",
    "bonferroni", "sidak", "benjamini_hochberg", "correct_pvalue",
    "ExplanationResult", "select_best_explanation", "mdl_report",
]
