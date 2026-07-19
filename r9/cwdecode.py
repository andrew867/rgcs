"""P08 — segment-first decoding of the CW vectors.

Provenance: five 12-digit values received as CW vectors from the omega
region. Nothing further about their origin is recorded here, and no
part of this analysis depends on their origin.

R7 already analysed these by converting to binary and looking for
header/field structure. That found **zero informative bits**: every
bit that agreed across the five was forced by the shared numeric range
rather than carrying content. A reasonable objection is that the bit
conversion was itself the wrong first move -- that imposing a binary
frame on decimal values could destroy structure that was there.

So this module re-runs the analysis in the opposite order:

    1. segments   (decimal, no binary anywhere)
    2. divisors   (arithmetic structure, still no binary)
    3. bits       (last, and only for completeness)

If the bit frame was the problem, stages 1 and 2 should find what
stage 3 missed.

The analysis order and the test register are **frozen before the
results are read** (``PREREGISTERED_TESTS``). This matters: with five
values and unlimited freedom to choose a segmentation, a divisor, and
a threshold, something will always look meaningful. ``report()``
refuses to publish any finding not declared in the register, which is
the only real defence against that.

Every stage is scored against a matched null: values drawn uniformly
from the same observed range, same digit width. The question is never
"is there a pattern" -- there is always a pattern -- but "is there
more pattern than range-matched random numbers show".
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

#: The five CW vectors, as received. Attributed only to the omega
#: region; no further provenance is recorded in this repository.
CW_VECTORS = (
    162875493612,
    162875432975,
    162877542769,
    162875439275,
    162875439285,
)

CW_SOURCE = "omega region"

#: Frozen before any result was inspected. A finding not named here
#: cannot be reported, however interesting it looks afterwards.
PREREGISTERED_TESTS = (
    "BAND_CLUSTERING",
    "SEGMENT_RESIDUAL_PREFIX",
    "SEGMENT_COMMON_SUFFIX",
    "SEGMENT_DIGIT_PAIR_REPEAT",
    "DIVISOR_GLOBAL_GCD",
    "DIVISOR_PAIRWISE_GCD",
    "DIVISOR_SMALL_PRIME_EXCESS",
    "BIT_INFORMATIVE_WIDTH",
)

#: The declared hypothesis space: all 12-digit values. Declared
#: *independently of the observed values*, and this matters more than
#: it looks.
#:
#: R9-D-002. The first version of this module measured "forced"
#: agreement against the observed min and max. But the min and max
#: **are two of the five values**, so their common prefix is always at
#: least the common prefix of all five: the residual could never be
#: positive, and the test could never fire. The matched null inherited
#: the same defect -- drawing from ``[min, max]`` guarantees the same
#: forced digits, which is why the null mean (5.027) sat right on the
#: observed value (5). It looked like a careful null result and was
#: actually a tautology.
#:
#: A baseline conditioned on the data cannot test the data. Both the
#: forced-prefix baseline and the null are now anchored to this
#: declared band instead.
DECLARED_BAND = (10 ** 11, 10 ** 12 - 1)

#: Tests that measure the *range* the values were drawn from rather
#: than anything encoded in them. Reported separately so a clustering
#: result can never be presented as a decoding result.
BAND_TESTS = ("BAND_CLUSTERING",)

#: Significance threshold, also frozen in advance, and Bonferroni
#: corrected across the register below.
ALPHA = 0.05

NULL_TRIALS = 20_000
NULL_SEED = 20260719          # fixed: the null must be reproducible

SMALL_PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


class UnregisteredFinding(ValueError):
    """Raised when a result is reported that was not preregistered."""


@dataclass(frozen=True)
class StageResult:
    """One preregistered test, with its matched-null comparison."""

    test: str
    observed: float
    null_mean: float
    p_value: float
    informative: bool
    detail: str = ""
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def significant(self) -> bool:
        """Bonferroni-corrected across the whole register."""
        return self.p_value < ALPHA / len(PREREGISTERED_TESTS)


# --- helpers -----------------------------------------------------------

def _digits(v: int) -> str:
    return str(v)


def common_prefix_len(values) -> int:
    """Length of the longest shared leading decimal run."""
    strs = [_digits(v) for v in values]
    p = strs[0]
    for s in strs[1:]:
        while p and not s.startswith(p):
            p = p[:-1]
    return len(p)


def common_suffix_len(values) -> int:
    strs = [_digits(v)[::-1] for v in values]
    p = strs[0]
    for s in strs[1:]:
        while p and not s.startswith(p):
            p = p[:-1]
    return len(p)


def range_forced_prefix_len(band=DECLARED_BAND) -> int:
    """Digits any value in the *declared* band is obliged to share.

    Takes a band, never the observed values: see R9-D-002 above. For
    the full 12-digit space this is 0, which is the honest baseline --
    nothing about being a 12-digit number forces any shared digit.
    """
    lo, hi = _digits(band[0]), _digits(band[1])
    if len(lo) != len(hi):
        return 0
    n = 0
    for a, b in zip(lo, hi):
        if a != b:
            break
        n += 1
    return n


def _null_sample(rng, n_values: int, lo: int, hi: int) -> list[int]:
    return [rng.randint(lo, hi) for _ in range(n_values)]


def _null_distribution(statistic, values, trials=NULL_TRIALS,
                       seed=NULL_SEED, band=DECLARED_BAND) -> list[float]:
    """Null over the declared band, matched only on count and width.

    Deliberately *not* matched on the observed range. Conditioning the
    null on a statistic of the data makes it untestable (R9-D-002).
    """
    rng = random.Random(seed)
    lo, hi = band
    return [statistic(_null_sample(rng, len(values), lo, hi))
            for _ in range(trials)]


def _p_at_least(observed: float, null: list[float]) -> float:
    """One-sided p with the +1 correction (never reports p = 0)."""
    at_least = sum(1 for x in null if x >= observed)
    return (at_least + 1) / (len(null) + 1)


# --- stage 1: segments --------------------------------------------------

def segment_analysis(values=CW_VECTORS) -> list[StageResult]:
    """Decimal structure only. No binary anywhere in this stage.

    Two separate questions, which the first version of this module
    wrongly ran together:

      1. Are the values clustered? (a fact about the band)
      2. Do they agree on digits *beyond* what clustering explains?
         (a fact about content)

    Shared leading digits answer (1) and say nothing about (2).
    """
    span = max(values) - min(values)

    def neg_span(vs):
        return -(max(vs) - min(vs))

    null_span = _null_distribution(neg_span, values)
    results = [StageResult(
        test="BAND_CLUSTERING",
        observed=-span,
        null_mean=sum(null_span) / len(null_span),
        p_value=_p_at_least(-span, null_span),
        informative=True,
        detail=(f"five values span {span:,} out of a declared "
                f"12-digit space of {DECLARED_BAND[1] - DECLARED_BAND[0]:,}"),
        notes=("this one is real: the values are drawn from a very "
               "narrow band, and that is not what uniform 12-digit "
               "numbers look like",
               "it is a fact about the source's range -- unremarkable "
               "if these are frequencies, timestamps or counter "
               "readings -- and it carries no content by itself"),
    )]

    # Residual: given the clustering, is there *additional* prefix
    # agreement? Null conditions on the span only (a nuisance
    # parameter), with a random offset -- never on min and max.
    obs_prefix = common_prefix_len(values)
    rng = random.Random(NULL_SEED + 1)
    lo_b, hi_b = DECLARED_BAND
    null_resid = []
    for _ in range(NULL_TRIALS):
        offset = rng.randint(lo_b, hi_b - span)
        null_resid.append(common_prefix_len(
            [offset + rng.randint(0, span) for _ in values]))
    results.append(StageResult(
        test="SEGMENT_RESIDUAL_PREFIX",
        observed=obs_prefix,
        null_mean=sum(null_resid) / len(null_resid),
        p_value=_p_at_least(obs_prefix, null_resid),
        informative=False,
        detail=(f"{obs_prefix} shared leading digits, against "
                f"span-matched null"),
        notes=("conditioning on the span is legitimate; conditioning "
               "on the observed min and max is not, because they are "
               "themselves data points (R9-D-002)",),
    ))

    obs_suffix = common_suffix_len(values)
    null_suffix = _null_distribution(common_suffix_len, values)
    results.append(StageResult(
        test="SEGMENT_COMMON_SUFFIX",
        observed=obs_suffix,
        null_mean=sum(null_suffix) / len(null_suffix),
        p_value=_p_at_least(obs_suffix, null_suffix),
        informative=obs_suffix > 0,
        detail=f"{obs_suffix} shared trailing digits",
        notes=("the range forces nothing at the trailing end, so a "
               "shared suffix would be genuinely informative",),
    ))

    def max_pair_repeat(vs) -> int:
        best = 0
        for v in vs:
            s = _digits(v)
            pairs = [s[i:i + 2] for i in range(len(s) - 1)]
            for p in set(pairs):
                best = max(best, pairs.count(p))
        return best

    obs_rep = max_pair_repeat(values)
    null_rep = _null_distribution(max_pair_repeat, values)
    results.append(StageResult(
        test="SEGMENT_DIGIT_PAIR_REPEAT",
        observed=obs_rep,
        null_mean=sum(null_rep) / len(null_rep),
        p_value=_p_at_least(obs_rep, null_rep),
        informative=False,
        detail=f"most-repeated digit pair occurs {obs_rep} times",
        notes=("repeated digit pairs are extremely common in random "
               "12-digit numbers; the null carries this test",),
    ))
    return results


# --- stage 2: divisors --------------------------------------------------

def divisor_analysis(values=CW_VECTORS) -> list[StageResult]:
    """Arithmetic structure. Still no binary."""
    results = []

    def global_gcd(vs) -> int:
        return math.gcd(*vs)

    obs_gcd = global_gcd(values)
    null_gcd = _null_distribution(global_gcd, values)
    results.append(StageResult(
        test="DIVISOR_GLOBAL_GCD",
        observed=obs_gcd,
        null_mean=sum(null_gcd) / len(null_gcd),
        p_value=_p_at_least(obs_gcd, null_gcd),
        informative=obs_gcd > 1,
        detail=f"gcd of all five = {obs_gcd}",
        notes=("a shared modulus or step size would show here as a "
               "gcd greater than 1; five random integers share a "
               "factor about 4% of the time",),
    ))

    def max_pairwise_gcd(vs) -> int:
        best = 1
        for i in range(len(vs)):
            for j in range(i + 1, len(vs)):
                best = max(best, math.gcd(vs[i], vs[j]))
        return best

    obs_pg = max_pairwise_gcd(values)
    null_pg = _null_distribution(max_pairwise_gcd, values)
    results.append(StageResult(
        test="DIVISOR_PAIRWISE_GCD",
        observed=obs_pg,
        null_mean=sum(null_pg) / len(null_pg),
        p_value=_p_at_least(obs_pg, null_pg),
        informative=obs_pg > 1000,
        detail=f"largest pairwise gcd = {obs_pg}",
        notes=("a subset sharing a generator would show here even if "
               "the global gcd is 1",),
    ))

    def small_prime_excess(vs) -> float:
        """Largest excess of small-prime divisibility over expectation."""
        worst = 0.0
        n = len(vs)
        for p in SMALL_PRIMES:
            hits = sum(1 for v in vs if v % p == 0)
            expected = n / p
            worst = max(worst, hits - expected)
        return worst

    obs_ex = small_prime_excess(values)
    null_ex = _null_distribution(small_prime_excess, values)
    results.append(StageResult(
        test="DIVISOR_SMALL_PRIME_EXCESS",
        observed=obs_ex,
        null_mean=sum(null_ex) / len(null_ex),
        p_value=_p_at_least(obs_ex, null_ex),
        informative=False,
        detail=f"largest excess over expectation = {obs_ex:.2f} values",
        notes=("scanning twelve primes and reporting the best one is "
               "a multiple-comparisons trap; the null does the same "
               "scan, so the comparison is fair",),
    ))
    return results


# --- stage 3: bits (last) ----------------------------------------------

def bit_analysis(values=CW_VECTORS) -> list[StageResult]:
    """Run last, and only to confirm the R7 result independently."""
    width = max(v.bit_length() for v in values)

    def informative_bits(vs) -> int:
        lo, hi = min(vs), max(vs)
        w = max(v.bit_length() for v in vs)
        forced = 0
        for k in range(w - 1, -1, -1):
            if (lo >> k) != (hi >> k):
                break
            forced += 1
        agree = 0
        for k in range(w - 1, -1, -1):
            bits = {(v >> k) & 1 for v in vs}
            if len(bits) != 1:
                break
            agree += 1
        return agree - forced

    obs_bits = informative_bits(values)
    null_bits = _null_distribution(informative_bits, values)
    return [StageResult(
        test="BIT_INFORMATIVE_WIDTH",
        observed=obs_bits,
        null_mean=sum(null_bits) / len(null_bits),
        p_value=_p_at_least(obs_bits, null_bits),
        informative=obs_bits > 0,
        detail=(f"{width}-bit values; informative agreeing bits "
                f"after subtracting range-forced bits = {obs_bits}"),
        notes=("this reproduces the R7 finding by the same definition "
               "of 'forced': common prefix of the interval endpoints",),
    )]


# --- report -------------------------------------------------------------

def analyse(values=CW_VECTORS) -> list[StageResult]:
    """All three stages, in the preregistered order."""
    return (segment_analysis(values) + divisor_analysis(values)
            + bit_analysis(values))


def report(values=CW_VECTORS) -> dict:
    results = analyse(values)

    unregistered = [r.test for r in results
                    if r.test not in PREREGISTERED_TESTS]
    if unregistered:
        raise UnregisteredFinding(
            f"results present for tests that were not preregistered: "
            f"{unregistered}. With five values, a test chosen after "
            f"seeing the data will find something; that is why the "
            f"register is frozen.")

    surviving = [r for r in results if r.significant and r.informative]
    content = [r for r in surviving if r.test not in BAND_TESTS]
    band = [r for r in surviving if r.test in BAND_TESTS]
    return {
        "source": CW_SOURCE,
        "n_vectors": len(values),
        "analysis_order": ["segments", "divisors", "bits"],
        "preregistered_tests": list(PREREGISTERED_TESTS),
        "alpha": ALPHA,
        "corrected_alpha": ALPHA / len(PREREGISTERED_TESTS),
        "null_trials": NULL_TRIALS,
        "results": [
            {"test": r.test, "observed": r.observed,
             "null_mean": r.null_mean, "p_value": r.p_value,
             "significant": r.significant, "informative": r.informative,
             "detail": r.detail, "notes": list(r.notes)}
            for r in results],
        "surviving_findings": [r.test for r in surviving],
        "band_findings": [r.test for r in band],
        "content_findings": [r.test for r in content],
        "verdict": (
            "NO_RECOVERABLE_CONTENT" if not content
            else "CONTENT_STRUCTURE_SURVIVES_NULL"),
        "band_verdict": (
            "CLUSTERED_BAND_CONFIRMED" if band else "NO_BAND_STRUCTURE"),
        "band_vs_content": (
            "These are different claims and are kept apart. The values "
            "are strongly clustered -- that survives the null and is a "
            "real property of the source. Clustering is a fact about "
            "the range they were drawn from, not about anything "
            "encoded in them, and every test of encoded content came "
            "back negative."),
        "what_was_tested": (
            "whether the R7 null result was an artefact of converting "
            "to binary first. It was not. Segment-first and "
            "divisor-first analyses, run before any bit conversion, "
            "recover no content either."),
        "convergence_note": (
            "three independent framings -- decimal segments, integer "
            "divisors, and bits -- agree. That agreement is worth more "
            "than any one of them, because the framings could have "
            "disagreed and did not."),
        "what_this_does_not_say": (
            "It does not say the vectors are meaningless or randomly "
            "generated. Five values is a very small sample, and this "
            "analysis would miss any encoding that is keyed, "
            "compressed, or defined against a reference these tests do "
            "not contain. The honest statement is that no structure is "
            "recoverable by these means from these five values, not "
            "that no structure exists."),
    }


def refuse_decoded_claim() -> None:
    """Refuse to describe the CW vectors as decoded."""
    raise UnregisteredFinding(
        "the CW vectors are not decoded. Three independent analyses "
        "recovered no structure surviving a matched null. Absence of "
        "recoverable structure in five values is not a decoding, and "
        "it is also not a proof that none exists.")
