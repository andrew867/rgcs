"""A06 — the simplicity metric and the statistical null engine.

The programme's central statistical question is:

    Does a predeclared frequency-coordinate system describe an
    independent corpus more simply than chance?

Answering it honestly requires four commitments, all mechanical here:

1. **The metric is frozen before any corpus is seen.** ``METRIC_SPEC``
   is hashed; ``metric_fingerprint()`` returns that hash and the tests
   pin it. If someone edits the metric to make a result prettier, the
   fingerprint changes and the pinned test fails. A metric tuned after
   looking is not a test.

2. **Controls are matched and seeded.** Null frequencies are drawn
   log-uniformly over the *same decade range* as the observed set, so
   the comparison is not secretly about magnitude. Every draw is
   deterministic given the seed.

3. **Multiple comparisons are corrected.** Testing many references,
   radices, and tolerances inflates false positives; Holm-Bonferroni
   (FWER) and Benjamini-Hochberg (FDR) are both provided.

4. **Effect size and uncertainty are reported, never a bare p-value.**
   A permutation test returns the observed statistic, the null
   distribution summary, a standardised effect size, and a bootstrap
   confidence interval.

Simplicity metric (frozen): for a frequency ``f`` and reference
``ref``, reduce the exact ratio ``f/ref = p/q`` to lowest terms and
score ``log2(p) + log2(q)``. This is ordinary rational complexity —
small integer ratios (octaves, fifths, exact folds) score low; generic
values score high. It is declared here, before use, and deliberately
NOT parameterised, so there is nothing to tune.

A low score is a statement about arithmetic. It is never evidence that
a specimen prefers a frequency.
"""

from __future__ import annotations

import hashlib
import math
import random
import statistics
from dataclasses import dataclass, field
from fractions import Fraction

from .units import exact

#: The frozen metric definition. Editing this string changes the
#: fingerprint and fails the pinned test — by design.
METRIC_SPEC = (
    "CSPC-SIMPLICITY-v1: score(f, ref) = log2(p) + log2(q) where "
    "f/ref = p/q in lowest terms (exact Fraction). Lower is simpler. "
    "No free parameters. Frozen 2026-07-18 before corpus evaluation."
)

#: Maximum denominator considered a 'simple' rational for the
#: descriptive rung classifier. Declared with the metric, not tuned.
SIMPLE_DENOMINATOR_MAX = 64


def metric_fingerprint() -> str:
    """sha256 of the frozen metric specification."""
    return hashlib.sha256(METRIC_SPEC.encode("utf-8")).hexdigest()


def simplicity(frequency, reference) -> float:
    """Rational complexity of f/ref: log2(p)+log2(q), lowest terms.

    Exact input, float output — the output is a score for ordering,
    not a physical quantity.
    """
    f = exact(frequency)
    ref = exact(reference)
    if f <= 0 or ref <= 0:
        raise ValueError("frequencies must be positive")
    ratio = Fraction(f, 1) / Fraction(ref, 1)
    return math.log2(ratio.numerator) + math.log2(ratio.denominator)


def corpus_score(frequencies, reference) -> float:
    """Mean simplicity over a corpus (lower = simpler)."""
    vals = [simplicity(f, reference) for f in frequencies]
    if not vals:
        raise ValueError("empty corpus")
    return statistics.fmean(vals)


# --- matched null models -------------------------------------------------

def matched_null_draw(observed, seed: int) -> list:
    """Draw a null set matched on BOTH magnitude range and arithmetic
    granularity.

    Matching only the magnitude range is not enough, and getting this
    wrong silently rigs the test (defect CSPC-D-003): if nulls are
    rounded to a fixed decimal grid they carry denominator 10^6, whose
    rational complexity swamps everything, so every corpus of round
    numbers — including deliberate negative controls — appears
    'simpler than chance'. What is then detected is "real frequency
    tables use round numbers", not structure.

    So each null member reuses the denominator of an observed member:
    if the corpus is integers the null is integers, if a member has
    denominator 100 its counterpart does too. Magnitude is log-uniform
    across the observed range. Deterministic given ``seed``.
    """
    obs = [exact(f) for f in observed]
    if len(obs) < 2:
        raise ValueError("need at least two observed frequencies")
    lo, hi = min(obs), max(obs)
    rng = random.Random(seed)
    lo_l, hi_l = math.log10(float(lo)), math.log10(float(hi))
    out = []
    for member in obs:
        q = member.denominator          # preserve arithmetic granularity
        v = 10 ** rng.uniform(lo_l, hi_l)
        num = round(v * q)
        out.append(Fraction(max(num, 1), q))
    return out


@dataclass(frozen=True)
class NullResult:
    observed_statistic: float
    null_mean: float
    null_sd: float
    n_null: int
    p_value: float
    effect_size: float          # standardised (obs - null_mean)/null_sd
    ci95: tuple
    seed: int
    metric_fingerprint: str
    interpretation: str
    evidence_class: str = "NUMERICAL_SIMULATION"

    def to_dict(self) -> dict:
        return {"observed_statistic": self.observed_statistic,
                "null_mean": self.null_mean, "null_sd": self.null_sd,
                "n_null": self.n_null, "p_value": self.p_value,
                "effect_size": self.effect_size,
                "ci95_low": self.ci95[0], "ci95_high": self.ci95[1],
                "seed": self.seed,
                "metric_fingerprint": self.metric_fingerprint,
                "interpretation": self.interpretation,
                "evidence_class": self.evidence_class}


def permutation_test(observed, reference, n_null: int = 2000,
                     seed: int = 20260718) -> NullResult:
    """Is the observed corpus simpler than matched random frequencies?

    One-sided: we ask whether observed simplicity is LOWER (simpler)
    than the null. Returns effect size and a bootstrap CI alongside the
    p-value, because a p-value alone hides how small an effect is.
    """
    obs_stat = corpus_score(observed, reference)
    null_stats = []
    for i in range(n_null):
        draw = matched_null_draw(observed, seed + i)
        null_stats.append(corpus_score(draw, reference))
    null_mean = statistics.fmean(null_stats)
    null_sd = statistics.pstdev(null_stats) or float("inf")
    # one-sided p: fraction of null at least as simple as observed
    at_least_as_simple = sum(1 for s in null_stats if s <= obs_stat)
    p = (at_least_as_simple + 1) / (n_null + 1)   # add-one, never 0
    effect = (obs_stat - null_mean) / null_sd if null_sd else 0.0
    lo, hi = _bootstrap_ci(null_stats)
    if p > 0.05:
        interp = ("NULL NOT REJECTED: the corpus is not simpler than "
                  "range-matched random frequencies under this metric. "
                  "This is a first-class result.")
    else:
        interp = ("Observed corpus scores simpler than matched nulls "
                  "(p={:.4g}, effect={:.2f} SD). This is a statement "
                  "about arithmetic under a frozen metric, NOT evidence "
                  "of any physical preference or coupling.").format(
                      p, effect)
    return NullResult(obs_stat, null_mean, null_sd, n_null, p, effect,
                      (lo, hi), seed, metric_fingerprint(), interp)


def _bootstrap_ci(samples, alpha: float = 0.05) -> tuple:
    s = sorted(samples)
    n = len(s)
    lo = s[max(0, int(alpha / 2 * n))]
    hi = s[min(n - 1, int((1 - alpha / 2) * n))]
    return (lo, hi)


# --- multiple comparison correction -------------------------------------

def holm_bonferroni(pvalues: dict, alpha: float = 0.05) -> dict:
    """Family-wise error control. Returns per-test adjusted p and
    rejection decision."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    out, running = {}, 0.0
    for i, (k, p) in enumerate(items):
        adj = min(1.0, max(running, (m - i) * p))
        running = adj
        out[k] = {"p_raw": p, "p_adjusted": adj,
                  "reject_at_alpha": adj <= alpha, "method": "holm"}
    return out


def benjamini_hochberg(pvalues: dict, alpha: float = 0.05) -> dict:
    """False-discovery-rate control."""
    items = sorted(pvalues.items(), key=lambda kv: kv[1])
    m = len(items)
    out, prev = {}, 1.0
    for i in range(m - 1, -1, -1):
        k, p = items[i]
        adj = min(prev, p * m / (i + 1))
        prev = adj
        out[k] = {"p_raw": p, "p_adjusted": adj,
                  "reject_at_alpha": adj <= alpha, "method": "bh"}
    return out


def family_report(pvalues: dict, alpha: float = 0.05) -> dict:
    """Both corrections plus an explicit statement of how many tests
    were run — the number that makes an uncorrected p meaningless."""
    holm = holm_bonferroni(pvalues, alpha)
    bh = benjamini_hochberg(pvalues, alpha)
    return {
        "n_tests": len(pvalues),
        "alpha": alpha,
        "holm": holm,
        "benjamini_hochberg": bh,
        "any_survives_fwer": any(v["reject_at_alpha"]
                                 for v in holm.values()),
        "any_survives_fdr": any(v["reject_at_alpha"]
                                for v in bh.values()),
        "note": "an uncorrected p-value from a family of "
                f"{len(pvalues)} tests is not a result",
        "evidence_class": "NUMERICAL_SIMULATION",
    }
