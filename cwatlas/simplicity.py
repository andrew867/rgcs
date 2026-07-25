"""P53 — Representation versus relational simplicity.

A mapping can look "simple" for two very different reasons:

* **Representation-only simplicity.** The values happen to be *round* in a
  chosen representation — a lucky base, a lucky unit scale. "The numbers line
  up in base-100" is the canonical trap: multiply everything by ``100**3`` and
  the digits acquire trailing zeros, but nothing structural is being said. That
  roundedness evaporates the moment the values are re-represented in a base
  coprime to the chosen base (for example base 7 or base 3).

* **Relational simplicity.** The *relations among* the values are simple —
  small-integer ratios, a clean linear ladder — and that structure **survives
  re-representation**. Ratios are invariant under a unit rescale, and the
  simplicity of a rational is invariant under a base change. Structure that
  survives is genuine; roundedness that does not is decorative.

This module scores both. Relational simplicity, being invariant, is *credited*
(a :class:`~cwatlas.claims.ClaimClass.MATHEMATICAL_TRANSLATION` at most — never
geographic). Representation-only simplicity is **flagged, not credited**: an
arithmetic coincidence in a chosen base is not evidence of meaning.

Pure arithmetic and deterministic. No wall-clock, no measurement; every value
is passed in.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Sequence, Tuple

from cwatlas.claims import ClaimClass, ClaimError

#: Default panel of bases used to test whether roundedness survives
#: re-representation. Includes bases coprime to 10/100 (7, 3) so that a value
#: that is merely round in base-10/100 is exposed as representation-only.
DEFAULT_PANEL_BASES: Tuple[int, ...] = (10, 100, 7, 3, 2)

#: Default thresholds. A mapping is credited as relationally simple only when
#: its invariant relational score clears ``REL_THRESHOLD``; it is flagged as
#: representation-only when it looks simple in the chosen base
#: (``REP_THRESHOLD``) but its relations do not.
REL_THRESHOLD = 0.5
REP_THRESHOLD = 0.5


class SimplicityError(ValueError):
    """Raised on malformed or underdetermined simplicity inputs.

    An explicit result state, never a silent guess.
    """


class SimplicityClass(Enum):
    """The three possible simplicity verdicts."""

    RELATIONAL_SIMPLICITY = "RELATIONAL_SIMPLICITY"
    REPRESENTATION_ONLY = "REPRESENTATION_ONLY"
    NO_SIMPLICITY = "NO_SIMPLICITY"


def refuse_representation_simplicity_as_meaning(*_a, **_k) -> None:
    """A representation-only coincidence is not evidence of meaning."""
    raise ClaimError(
        "refused: that a set of values is round in a chosen base or unit "
        "(e.g. 'the numbers line up in base-100') is a property of the chosen "
        "representation, not of the mapping. It evaporates under re-"
        "representation and may not be credited as relational structure or "
        "as source meaning.")


def _base_digits(n: int, base: int) -> List[int]:
    """Digits of ``|n|`` in ``base`` (most-significant first)."""
    if base < 2:
        raise SimplicityError(f"base must be >= 2, got {base}.")
    n = abs(int(n))
    if n == 0:
        return [0]
    out: List[int] = []
    while n > 0:
        out.append(n % base)
        n //= base
    out.reverse()
    return out


def _trailing_zero_frac(n: int, base: int) -> float:
    """Fraction of trailing-zero digits of ``n`` in ``base`` (roundedness)."""
    digits = _base_digits(n, base)
    if len(digits) == 1 and digits[0] == 0:
        return 1.0  # zero is trivially round
    tz = 0
    for d in reversed(digits):
        if d == 0:
            tz += 1
        else:
            break
    return tz / len(digits)


def _simple_ratio_score(x: float, max_den: int = 16, tol: float = 1e-9) -> float:
    """Score how close ``x`` is to a *simple* rational ``p/q`` (small p+q).

    Returns ``2/(p+q)`` for the simplest admissible ratio (so ``1/1`` scores
    ``1.0``, ``2/1`` and ``1/2`` score ``0.667``) or ``0.0`` if no small-
    denominator rational lands within ``tol``. Invariant under unit rescale and
    base change, so it measures *relational* rather than representational
    simplicity.
    """
    x = abs(float(x))
    if not math.isfinite(x) or x == 0.0:
        return 0.0
    best = 0.0
    for q in range(1, max_den + 1):
        p = round(x * q)
        if p <= 0:
            continue
        if abs(x - p / q) <= tol * max(1.0, x):
            best = max(best, 2.0 / (p + q))
    return best


@dataclass(frozen=True)
class SimplicityScore:
    """A typed simplicity assessment of one mapping's values.

    ``representation_score`` is roundedness in the chosen base;
    ``invariant_score`` is the *minimum* roundedness across the re-representation
    panel (how much roundedness survives); ``relational_score`` is the
    invariant small-ratio structure. ``flagged`` marks representation-only
    "simplicity" that must not be credited.
    """

    representation_score: float
    invariant_score: float
    relational_score: float
    simplicity_class: SimplicityClass
    flagged: bool
    claim_class: str
    justification: str
    chosen_base: int
    panel_bases: Tuple[int, ...]


def representation_simplicity(values: Sequence[float], base: int,
                              scale: float = 1.0) -> float:
    """Mean roundedness (trailing-zero fraction) of values in ``base``.

    ``scale`` models a unit choice: values are multiplied then rounded to the
    nearest integer before digit counting. High score == the values look round
    in this particular representation.
    """
    vals = _validate_values(values)
    if not (math.isfinite(scale) and scale != 0.0):
        raise SimplicityError("scale must be finite and non-zero.")
    fracs = [_trailing_zero_frac(round(v * scale), base) for v in vals]
    return sum(fracs) / len(fracs)


def relational_simplicity(values: Sequence[float]) -> float:
    """Invariant relational simplicity: mean small-ratio score of the ladder.

    Uses the ratios of consecutive sorted distinct magnitudes. Because ratios
    are invariant under unit rescale and the simplicity of a rational is
    invariant under base change, this survives re-representation.
    """
    vals = _validate_values(values)
    mags = sorted({abs(v) for v in vals if v != 0.0})
    if len(mags) < 2:
        raise SimplicityError(
            "relational simplicity needs at least two distinct non-zero "
            "magnitudes to form a ratio.")
    scores = [_simple_ratio_score(mags[i + 1] / mags[i])
              for i in range(len(mags) - 1)]
    return sum(scores) / len(scores)


def _validate_values(values: Sequence[float]) -> List[float]:
    vals = [float(v) for v in values]
    if len(vals) < 2:
        raise SimplicityError("need at least two values.")
    if not all(math.isfinite(v) for v in vals):
        raise SimplicityError("all values must be finite.")
    return vals


def assess_simplicity(values: Sequence[float], *, chosen_base: int = 100,
                      panel_bases: Sequence[int] | None = None,
                      rel_threshold: float = REL_THRESHOLD,
                      rep_threshold: float = REP_THRESHOLD) -> SimplicityScore:
    """Classify a mapping's simplicity as relational, representation-only, or none.

    * If the invariant relational structure clears ``rel_threshold`` the mapping
      is credited as ``RELATIONAL_SIMPLICITY`` (survives re-representation).
    * Else, if it merely looks round in ``chosen_base`` (>= ``rep_threshold``)
      while its relations do not, it is ``REPRESENTATION_ONLY`` and **flagged**.
    * Otherwise ``NO_SIMPLICITY``.
    """
    vals = _validate_values(values)
    panel = tuple(panel_bases) if panel_bases is not None else DEFAULT_PANEL_BASES
    if chosen_base < 2 or any(b < 2 for b in panel):
        raise SimplicityError("all bases must be >= 2.")

    rep = representation_simplicity(vals, chosen_base)
    invariant = min(representation_simplicity(vals, b) for b in panel)
    rel = relational_simplicity(vals)

    if rel >= rel_threshold:
        cls = SimplicityClass.RELATIONAL_SIMPLICITY
        flagged = False
        claim = ClaimClass.MATHEMATICAL_TRANSLATION.value
        why = (f"relational structure survives re-representation "
               f"(relational_score={rel:.3f} >= {rel_threshold}); credited as "
               f"a mathematical relation, not a geographic claim.")
    elif rep >= rep_threshold:
        cls = SimplicityClass.REPRESENTATION_ONLY
        flagged = True
        claim = ClaimClass.OPERATOR_HYPOTHESIS.value
        why = (f"looks round in base-{chosen_base} "
               f"(representation_score={rep:.3f}) but relations are not simple "
               f"(relational_score={rel:.3f}); roundedness collapses under re-"
               f"representation (invariant_score={invariant:.3f}). FLAGGED as "
               f"representation-only; not credited.")
    else:
        cls = SimplicityClass.NO_SIMPLICITY
        flagged = False
        claim = ClaimClass.OPERATOR_HYPOTHESIS.value
        why = (f"neither round in base-{chosen_base} "
               f"(representation_score={rep:.3f}) nor relationally simple "
               f"(relational_score={rel:.3f}).")

    return SimplicityScore(
        representation_score=rep,
        invariant_score=invariant,
        relational_score=rel,
        simplicity_class=cls,
        flagged=flagged,
        claim_class=claim,
        justification=why,
        chosen_base=chosen_base,
        panel_bases=panel,
    )


def simplicity_report() -> dict:
    """P53 declaration receipt."""
    return {
        "phase_id": "P53",
        "what_this_is": (
            "representation-versus-relational simplicity: score whether a "
            "mapping is simple only in a chosen base/unit (representation-only, "
            "flagged) or has relational structure that survives re-"
            "representation (credited as a mathematical relation)."),
        "panel_bases": list(DEFAULT_PANEL_BASES),
        "rel_threshold": REL_THRESHOLD,
        "rep_threshold": REP_THRESHOLD,
        "representation_only_is_credited": False,
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "REPRESENTATION_VS_RELATIONAL_SIMPLICITY_SEPARATED",
        "what_this_does_not_say": (
            "That values are round in some base or unit says nothing about "
            "meaning; representation-only simplicity is flagged and never "
            "credited. A surviving relational structure is a mathematical "
            "relation only, not a geographic or physical claim."),
    }
