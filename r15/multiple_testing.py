"""P23 — multiple comparisons and sequential analysis: the look-elsewhere
firewall. Correction and a preregistered stopping rule, NOT a smaller p.

An experiment that sweeps frequencies, angles, transforms, specimens,
sensors and retries is not running one test; it is running many, and the
smallest p-value out of many is small *by construction*. Report that
smallest p without saying how many things were tried and you have
manufactured a result: with ``m`` independent null tests, the probability
that at least one crosses a nominal ``alpha`` is ``1-(1-alpha)**m``, which
approaches certainty as ``m`` grows. The same failure wearing a clock is
*optional stopping*: peek at accumulating data and stop the moment a
threshold is crossed, with no preregistered stopping rule, and noise alone
will cross any fixed line given enough looks. This module makes both moves
mechanical to refuse and supplies the honest alternatives.

**Family-wise and false-discovery control.** Given ``m`` p-values from a
:class:`TestFamily`, three corrections return adjusted significance:
:func:`bonferroni_adjust` and :func:`holm_adjust` control the family-wise
error rate (the chance of *any* false rejection), and
:func:`benjamini_hochberg_adjust` controls the false-discovery rate (the
expected *fraction* of rejections that are false). The power point is that
FDR is not merely conservative: with many nulls and a few true effects it
*recovers the true effects* while holding the false-positive fraction at
``alpha``, where reporting the single smallest uncorrected p inflates the
error to the look-elsewhere probability. Both are demonstrated by
deterministic Monte-Carlo under a fixed seed.

**Sequential analysis.** :func:`alpha_spending` distributes a total error
budget across a preregistered sequence of looks so that the *cumulative*
alpha spent by the final look is exactly the target, and a group-sequential
boundary (:func:`evaluate_sequential`) stops the first time a look's
p-value falls under its own spent-down boundary. Peeking spends alpha:
using the full ``alpha`` at every look (:func:`naive_peeking_fpr`) inflates
the false-positive rate to the look-elsewhere value, while the spent
boundary (:func:`spent_peeking_fpr`) holds it at ``alpha``.

**The refusals.** :func:`refuse_uncorrected_multiple_comparisons` refuses a
significance call over a family of more than one test with no correction;
:func:`refuse_optional_stopping` (reused from R13) refuses a stop on
significance with no preregistered stopping rule; and
:func:`refuse_exploratory_as_confirmatory` refuses to read the best result
of an exploratory scan as a confirmatory p-value, because a contrast chosen
after seeing the ranking was never predicted -- confirmation needs a sealed
preregistration.

Nothing here is measured. Every p-value, z-score and family is a synthetic
fixture or a passed-in input; this module operates no apparatus and
acquires nothing. ``measured_here`` is ``"nothing"`` and
``PHYSICAL_VALIDATION_NOT_CLAIMED``. The strongest thing it produces is a
``SOFTWARE_IMPLEMENTED`` correction and a ``SYNTHETIC_OBSERVATION`` fixture;
a corrected p-value is still not a measurement, and a survived correction is
never, by itself, new physics.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from r15 import claims as C
# EXTEND R13 authorities rather than duplicating them: the optional-stopping
# refusal and the canonical content hash already exist and are reused here.
from r13.preregister import (
    Preregistration,
    refuse_optional_stopping as _r13_refuse_optional_stopping,
    refuse_result_without_prereg as _r13_refuse_result_without_prereg,
)
from r13.serialize import content_hash

#: The standing verdict for this phase.
VERDICT = "MULTIPLE_COMPARISONS_CORRECTED_AND_STOPPING_PREREGISTERED"
MEASURED_HERE = "nothing"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The claim class this module's software output carries. It corrects and
#: schedules; it never measures.
SOFTWARE_CLAIM_CLASS = C.ClaimClass.SOFTWARE_IMPLEMENTED
#: The class of the synthetic p-value / z-score fixtures it generates.
FIXTURE_CLAIM_CLASS = C.ClaimClass.SYNTHETIC_OBSERVATION

#: Version stamp carried on results so an analysis is reproducible.
ANALYSIS_VERSION = "R15.P23.1"


class MultipleTestingError(RuntimeError):
    """Raised on a malformed p-value family, an out-of-range p-value or
    alpha, an uncorrected multiple-comparisons significance call, an
    optional stop with no preregistered rule, or an exploratory result
    offered as a confirmatory one."""


# =======================================================================
# Validation
# =======================================================================

def _check_alpha(alpha: float) -> float:
    if not isinstance(alpha, (int, float)) or isinstance(alpha, bool):
        raise MultipleTestingError("alpha must be a real number")
    a = float(alpha)
    if not (0.0 < a < 1.0):
        raise MultipleTestingError(
            f"alpha must lie in the open interval (0, 1); got {a}")
    return a


def _check_pvalues(pvalues) -> np.ndarray:
    arr = np.asarray(list(pvalues), dtype=float)
    if arr.ndim != 1 or arr.size == 0:
        raise MultipleTestingError(
            "a p-value family must be a non-empty 1-D sequence")
    if not np.all(np.isfinite(arr)):
        raise MultipleTestingError("p-values must be finite")
    if np.any(arr < 0.0) or np.any(arr > 1.0):
        raise MultipleTestingError(
            "every p-value must lie in the closed interval [0, 1]")
    return arr


# =======================================================================
# The test family and its trial accounting
# =======================================================================

@dataclass(frozen=True)
class TestFamily:
    """A family of hypothesis tests actually attempted.

    ``p_values`` and ``labels`` are the reported tests. ``hidden_retries``
    counts trials that were run but not reported -- re-mounts, re-runs,
    extra sensors, extra transforms swept and then dropped. The honest
    number of comparisons to correct against is :meth:`total_trials`, the
    reported tests plus the hidden retries; correcting against only the
    reported count is itself a look-elsewhere error, so the family carries
    the hidden count explicitly."""

    name: str
    p_values: tuple
    labels: tuple = ()
    hidden_retries: int = 0
    analysis_version: str = ANALYSIS_VERSION

    def __post_init__(self) -> None:
        arr = _check_pvalues(self.p_values)
        object.__setattr__(self, "p_values", tuple(float(x) for x in arr))
        if self.labels and len(self.labels) != len(self.p_values):
            raise MultipleTestingError(
                "labels, when supplied, must match the number of p-values")
        if not self.labels:
            object.__setattr__(
                self, "labels",
                tuple(f"H{i}" for i in range(len(self.p_values))))
        if not isinstance(self.hidden_retries, int) or self.hidden_retries < 0:
            raise MultipleTestingError(
                "hidden_retries must be a non-negative integer")

    @property
    def n_reported(self) -> int:
        return len(self.p_values)

    def total_trials(self) -> int:
        """The honest number of comparisons: reported tests plus every
        hidden retry. Corrections must use this, not ``n_reported``."""
        return self.n_reported + self.hidden_retries

    def min_p(self) -> float:
        return min(self.p_values)


def effective_trials(reported: int, hidden_retries: int) -> int:
    """Total comparisons once hidden retries are counted.

    Hidden retries *increase* the trial count and therefore the correction:
    a sweep reported as one test but re-run five times is six comparisons,
    and the look-elsewhere probability is computed against six, not one.
    """
    if not isinstance(reported, int) or reported < 1:
        raise MultipleTestingError("reported must be a positive integer")
    if not isinstance(hidden_retries, int) or hidden_retries < 0:
        raise MultipleTestingError(
            "hidden_retries must be a non-negative integer")
    return reported + hidden_retries


# =======================================================================
# Multiple-comparisons corrections
# =======================================================================

class CorrectionMethod(Enum):
    BONFERRONI = "BONFERRONI"          # controls FWER
    HOLM = "HOLM"                      # controls FWER, step-down, uniformly
                                       # more powerful than Bonferroni
    BENJAMINI_HOCHBERG = "BENJAMINI_HOCHBERG"  # controls FDR, step-up


@dataclass(frozen=True)
class CorrectionResult:
    """The outcome of correcting a family at level ``alpha``.

    ``adjusted`` are the adjusted p-values in the family's original order;
    ``rejected`` flags which hypotheses are declared significant after
    correction. ``n_trials`` is the honest trial count used (including
    hidden retries), so the correction is against everything attempted."""

    method: CorrectionMethod
    alpha: float
    n_trials: int
    adjusted: tuple
    rejected: tuple
    controls: str
    analysis_version: str = ANALYSIS_VERSION

    def n_rejected(self) -> int:
        return int(sum(self.rejected))

    def rejected_labels(self, family: "TestFamily") -> tuple:
        return tuple(lab for lab, r in zip(family.labels, self.rejected) if r)


def _padded(arr: np.ndarray, m: int) -> np.ndarray:
    """Treat a family of ``len(arr)`` reported p-values as ``m`` trials by
    accounting for ``m - len(arr)`` hidden retries as additional (worst
    case, p=1) comparisons. Only the effective multiplier ``m`` matters for
    the adjustment of the reported values, so no fake p-values are invented;
    ``m`` is threaded through as the correction denominator/rank base."""
    return arr  # the multiplier m is passed separately; kept for clarity


def bonferroni_adjust(pvalues, m: int | None = None) -> np.ndarray:
    """Bonferroni-adjusted p-values ``min(m * p, 1)``.

    Controls the family-wise error rate: if every null is true, the chance
    of *any* rejection at level ``alpha`` is at most ``alpha``. ``m``
    defaults to the number of p-values but may be larger to account for
    hidden retries."""
    arr = _check_pvalues(pvalues)
    m = arr.size if m is None else int(m)
    if m < arr.size:
        raise MultipleTestingError(
            "m (total trials) cannot be fewer than the reported p-values")
    return np.minimum(arr * m, 1.0)


def holm_adjust(pvalues, m: int | None = None) -> np.ndarray:
    """Holm step-down adjusted p-values (returned in original order).

    Sort ascending, multiply the k-th smallest by ``m - k + 1``, enforce
    monotonicity, clip at 1. Controls the family-wise error rate and is
    uniformly at least as powerful as Bonferroni."""
    arr = _check_pvalues(pvalues)
    n = arr.size
    m = n if m is None else int(m)
    if m < n:
        raise MultipleTestingError(
            "m (total trials) cannot be fewer than the reported p-values")
    order = np.argsort(arr, kind="mergesort")
    ranked = arr[order]
    factors = (m - np.arange(n)).astype(float)   # m, m-1, ...
    adj_sorted = np.minimum.accumulate(  # enforce non-decreasing from top
        (ranked * factors)[::-1])[::-1]
    adj_sorted = np.minimum(adj_sorted, 1.0)
    out = np.empty(n, dtype=float)
    out[order] = adj_sorted
    return out


def benjamini_hochberg_adjust(pvalues, m: int | None = None) -> np.ndarray:
    """Benjamini-Hochberg FDR-adjusted p-values (original order).

    Sort ascending, scale the k-th smallest by ``m / k``, take the running
    minimum from the largest rank down, clip at 1. Controls the
    false-discovery rate -- the expected fraction of rejections that are
    false -- and is more powerful than FWER control when several effects
    are real."""
    arr = _check_pvalues(pvalues)
    n = arr.size
    m = n if m is None else int(m)
    if m < n:
        raise MultipleTestingError(
            "m (total trials) cannot be fewer than the reported p-values")
    order = np.argsort(arr, kind="mergesort")
    ranked = arr[order]
    ranks = np.arange(1, n + 1)
    scaled = ranked * m / ranks
    adj_sorted = np.minimum.accumulate(scaled[::-1])[::-1]
    adj_sorted = np.minimum(adj_sorted, 1.0)
    out = np.empty(n, dtype=float)
    out[order] = adj_sorted
    return out


_ADJUSTERS = {
    CorrectionMethod.BONFERRONI: (bonferroni_adjust, "FWER"),
    CorrectionMethod.HOLM: (holm_adjust, "FWER"),
    CorrectionMethod.BENJAMINI_HOCHBERG: (benjamini_hochberg_adjust, "FDR"),
}


def correct(family: TestFamily, method: CorrectionMethod,
            alpha: float) -> CorrectionResult:
    """Correct a family and return which hypotheses survive at ``alpha``.

    The correction is applied against ``family.total_trials()`` -- reported
    tests plus hidden retries -- so undisclosed re-runs cannot be hidden
    from the multiplier."""
    if not isinstance(family, TestFamily):
        raise MultipleTestingError("expected a TestFamily")
    if not isinstance(method, CorrectionMethod):
        raise MultipleTestingError("method must be a CorrectionMethod")
    a = _check_alpha(alpha)
    m = family.total_trials()
    adjuster, controls = _ADJUSTERS[method]
    adjusted = adjuster(np.asarray(family.p_values), m=m)
    rejected = adjusted <= a
    return CorrectionResult(
        method=method, alpha=a, n_trials=m,
        adjusted=tuple(float(x) for x in adjusted),
        rejected=tuple(bool(x) for x in rejected),
        controls=controls)


def correction_sensitivity(family: TestFamily, alpha: float) -> dict:
    """Report which hypotheses each correction method rejects.

    Sensitivity to the correction method is itself a result: if the
    conclusion flips between Bonferroni, Holm and Benjamini-Hochberg, the
    finding is fragile and the choice of method must be preregistered, not
    chosen after seeing which one 'works'."""
    rows = {}
    for method in CorrectionMethod:
        res = correct(family, method, alpha)
        rows[method.value] = {
            "controls": res.controls,
            "n_rejected": res.n_rejected(),
            "rejected_labels": list(res.rejected_labels(family)),
        }
    uncorrected = sum(1 for p in family.p_values if p <= alpha)
    n_sets = {frozenset(v["rejected_labels"]) for v in rows.values()}
    return {
        "alpha": _check_alpha(alpha),
        "n_reported": family.n_reported,
        "total_trials": family.total_trials(),
        "uncorrected_n_rejected": uncorrected,
        "by_method": rows,
        "methods_agree": len(n_sets) == 1,
    }


# =======================================================================
# The look-elsewhere effect (multiple-comparisons inflation)
# =======================================================================

def look_elsewhere_probability(m: int, alpha: float) -> float:
    """P(at least one of ``m`` independent null tests crosses ``alpha``).

    ``1-(1-alpha)**m`` -- the analytic look-elsewhere probability. It is
    the false-positive rate you actually run when you report the smallest
    of ``m`` uncorrected p-values, and it climbs toward 1 as ``m`` grows.
    """
    if not isinstance(m, int) or m < 1:
        raise MultipleTestingError("m must be a positive integer")
    a = _check_alpha(alpha)
    return 1.0 - (1.0 - a) ** m


def uncorrected_min_p_fpr(m: int, alpha: float, trials: int = 4000,
                          seed: int = 0) -> float:
    """Monte-Carlo false-positive rate of reporting the smallest of ``m``
    uncorrected p-values, under the global null.

    Draws ``trials`` families of ``m`` uniform(0,1) p-values (every null
    true) and reports the fraction whose *minimum* p falls below ``alpha``.
    Converges to :func:`look_elsewhere_probability`. Deterministic in
    ``seed``."""
    if not isinstance(m, int) or m < 1:
        raise MultipleTestingError("m must be a positive integer")
    a = _check_alpha(alpha)
    rng = np.random.default_rng(seed)
    p = rng.random((int(trials), m))
    return float(np.mean(p.min(axis=1) < a))


def corrected_family_fpr(m: int, alpha: float,
                         method: CorrectionMethod =
                         CorrectionMethod.BONFERRONI,
                         trials: int = 4000, seed: int = 0) -> float:
    """Monte-Carlo family-wise false-positive rate *after* correction.

    Same global-null families as :func:`uncorrected_min_p_fpr`, but the
    fraction with *any* rejection after the given correction. For an FWER
    method this stays at or below ``alpha`` -- the inflation is removed.
    Deterministic in ``seed``."""
    if not isinstance(m, int) or m < 1:
        raise MultipleTestingError("m must be a positive integer")
    a = _check_alpha(alpha)
    adjuster, _ = _ADJUSTERS[method]
    rng = np.random.default_rng(seed)
    fam = rng.random((int(trials), m))
    any_reject = 0
    for row in fam:
        if np.any(adjuster(row, m=m) <= a):
            any_reject += 1
    return any_reject / int(trials)


# =======================================================================
# Synthetic fixtures with known ground truth (for the power tests)
# =======================================================================

@dataclass(frozen=True)
class PlantedFamily:
    """A synthetic family with a known set of true effects, for power tests.

    ``family`` is the p-value family; ``true_effects`` are the indices of
    the hypotheses that are genuinely non-null. This is a
    ``SYNTHETIC_OBSERVATION``: the ground truth is planted, not measured."""

    family: TestFamily
    true_effects: tuple
    claim_class: str = FIXTURE_CLAIM_CLASS.value


def synthetic_planted_family(n_tests: int, n_true: int,
                             true_p: float = 1e-4, seed: int = 0,
                             name: str = "planted") -> PlantedFamily:
    """A family of ``n_tests`` p-values with ``n_true`` planted effects.

    The null hypotheses get uniform(0,1) p-values (true null distribution);
    the ``n_true`` planted effects get a tiny p-value ``true_p``. The
    result is deterministic in ``seed`` and carries its own ground truth so
    a correction's *power* (true effects recovered) and *error* (nulls
    wrongly rejected) can both be measured against the plant."""
    if not (0 <= n_true <= n_tests) or n_tests < 1:
        raise MultipleTestingError("need 0 <= n_true <= n_tests, n_tests >= 1")
    rng = np.random.default_rng(seed)
    p = rng.random(n_tests)
    true_idx = tuple(sorted(
        int(i) for i in rng.choice(n_tests, size=n_true, replace=False))) \
        if n_true else ()
    for i in true_idx:
        p[i] = true_p
    fam = TestFamily(name=name, p_values=tuple(float(x) for x in p))
    return PlantedFamily(family=fam, true_effects=true_idx)


def power_and_error(planted: PlantedFamily, method: CorrectionMethod,
                    alpha: float) -> dict:
    """Recovered true effects and false discoveries after correction.

    ``true_positive_rate`` is the fraction of planted effects rejected
    (power); ``false_discoveries`` is the number of nulls wrongly rejected;
    ``fdr_observed`` is the realised false-discovery proportion. On a
    family with a few strong effects among many nulls, Benjamini-Hochberg
    recovers the effects while holding the false-discovery proportion down
    -- the power point of FDR control."""
    if not isinstance(planted, PlantedFamily):
        raise MultipleTestingError("expected a PlantedFamily")
    res = correct(planted.family, method, alpha)
    truth = set(planted.true_effects)
    rejected = {i for i, r in enumerate(res.rejected) if r}
    tp = len(rejected & truth)
    fp = len(rejected - truth)
    n_true = len(truth)
    return {
        "method": method.value,
        "n_true_effects": n_true,
        "true_positive_rate": (tp / n_true) if n_true else 0.0,
        "false_discoveries": fp,
        "n_rejected": len(rejected),
        "fdr_observed": (fp / len(rejected)) if rejected else 0.0,
    }


# =======================================================================
# Sequential analysis: alpha spending and group-sequential boundaries
# =======================================================================

class SpendingFunction(Enum):
    """How the total error budget is spent across the looks."""

    LINEAR = "LINEAR"                    # spend proportional to information
    POCOCK = "POCOCK"                    # Lan-DeMets Pocock-type
    OBRIEN_FLEMING = "OBRIEN_FLEMING"    # Lan-DeMets O'Brien-Fleming-type


# --- normal helpers (deterministic, no scipy) --------------------------

def _phi(z: float) -> float:
    """Standard normal CDF via the error function."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))


def _phi_inv(p: float) -> float:
    """Standard normal quantile (Acklam's rational approximation).

    Deterministic and accurate to ~1e-9 over (0,1); adequate for shaping an
    alpha-spending boundary. Used only for the O'Brien-Fleming spending
    function; the family-wise control property does not depend on it."""
    if not (0.0 < p < 1.0):
        raise MultipleTestingError("quantile argument must be in (0, 1)")
    a = [-3.969683028665376e+01, 2.209460984245205e+02,
         -2.759285104469687e+02, 1.383577518672690e+02,
         -3.066479806614716e+01, 2.506628277459239e+00]
    b = [-5.447609879822406e+01, 1.615858368580409e+02,
         -1.556989798598866e+02, 6.680131188771972e+01,
         -1.328068155288572e+01]
    c = [-7.784894002430293e-03, -3.223964580411365e-01,
         -2.400758277161838e+00, -2.549732539343734e+00,
         4.374664141464968e+00, 2.938163982698783e+00]
    d = [7.784695709041462e-03, 3.224671290700398e-01,
         2.445134137142996e+00, 3.754408661907416e+00]
    plow, phigh = 0.02425, 1 - 0.02425
    if p < plow:
        q = math.sqrt(-2 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q
                + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2 * math.log(1 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q
                 + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r
            + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r
                            + b[4]) * r + 1)


def _cumulative_spend(t: float, alpha: float,
                      spending: SpendingFunction) -> float:
    """Cumulative alpha spent by information fraction ``t`` in (0, 1]."""
    if spending is SpendingFunction.LINEAR:
        return alpha * t
    if spending is SpendingFunction.POCOCK:
        return alpha * math.log(1.0 + (math.e - 1.0) * t)
    if spending is SpendingFunction.OBRIEN_FLEMING:
        zc = _phi_inv(1.0 - alpha / 2.0)
        return 2.0 * (1.0 - _phi(zc / math.sqrt(t)))
    raise MultipleTestingError("unknown spending function")


@dataclass(frozen=True)
class SpendingSchedule:
    """Per-look nominal boundaries derived from a spending function.

    ``information_fractions`` are the cumulative data fractions at each
    planned look (strictly increasing, last == 1.0). ``cumulative_spend``
    is the total alpha spent through each look, and ``nominal_alpha`` is the
    per-look boundary on the p-value scale under independent looks:
    ``a_k = 1 - (1 - F(t_k)) / (1 - F(t_{k-1}))``, so that
    ``prod_k (1 - a_k) = 1 - F(t_K) = 1 - alpha`` and the overall
    false-positive rate is exactly ``alpha``."""

    alpha: float
    spending: SpendingFunction
    information_fractions: tuple
    cumulative_spend: tuple
    nominal_alpha: tuple
    analysis_version: str = ANALYSIS_VERSION


def alpha_spending(alpha: float, information_fractions,
                   spending: SpendingFunction = SpendingFunction.POCOCK
                   ) -> SpendingSchedule:
    """Distribute ``alpha`` across looks with an alpha-spending function.

    Peeking spends alpha: each look consumes part of the total budget, the
    cumulative spend rises monotonically to exactly ``alpha`` at the final
    look, and the per-look nominal boundaries are chosen so the overall
    false-positive rate stays at ``alpha`` under independent looks. This is
    what makes sequential testing legitimate -- the budget is fixed in
    advance and merely *allocated* across the looks, not re-spent at each
    one."""
    a = _check_alpha(alpha)
    fr = [float(x) for x in information_fractions]
    if not fr:
        raise MultipleTestingError("need at least one information fraction")
    if any(fr[i] >= fr[i + 1] for i in range(len(fr) - 1)):
        raise MultipleTestingError(
            "information fractions must be strictly increasing")
    if any(t <= 0.0 or t > 1.0 for t in fr):
        raise MultipleTestingError(
            "information fractions must lie in (0, 1]")
    if abs(fr[-1] - 1.0) > 1e-12:
        raise MultipleTestingError(
            "the final information fraction must be 1.0 (all data in)")
    cum = [_cumulative_spend(t, a, spending) for t in fr]
    nominal = []
    prev_prod = 1.0  # prod_{j<k} (1 - a_j) = 1 - F(t_{k-1})
    for f_k in cum:
        surv = 1.0 - f_k               # 1 - F(t_k) = prod_{j<=k}(1 - a_j)
        a_k = 1.0 - surv / prev_prod
        a_k = min(max(a_k, 0.0), 1.0)
        nominal.append(a_k)
        prev_prod = surv
    return SpendingSchedule(
        alpha=a, spending=spending,
        information_fractions=tuple(fr),
        cumulative_spend=tuple(cum),
        nominal_alpha=tuple(nominal))


@dataclass(frozen=True)
class SequentialDecision:
    """The result of running p-values through a spent-down boundary."""

    stopped: bool
    stop_look: int          # 1-based look at which it stopped, else -1
    reject: bool            # rejected the null at the stop
    boundaries: tuple
    analysis_version: str = ANALYSIS_VERSION


def evaluate_sequential(schedule: SpendingSchedule, look_pvalues
                        ) -> SequentialDecision:
    """Walk the looks, stopping the first time ``p_k <= nominal_alpha_k``.

    Each look is tested against *its own* spent-down boundary, not the full
    ``alpha``. If no look crosses, the sequence ends without rejecting.
    Because the boundaries were allocated so the overall false-positive rate
    is ``alpha``, this stop is legitimate even though the data were looked at
    repeatedly."""
    if not isinstance(schedule, SpendingSchedule):
        raise MultipleTestingError("expected a SpendingSchedule")
    ps = _check_pvalues(look_pvalues)
    if ps.size != len(schedule.nominal_alpha):
        raise MultipleTestingError(
            "number of look p-values must match the number of looks")
    for k, (p, a_k) in enumerate(zip(ps, schedule.nominal_alpha), start=1):
        if p <= a_k:
            return SequentialDecision(
                stopped=True, stop_look=k, reject=True,
                boundaries=schedule.nominal_alpha)
    return SequentialDecision(
        stopped=False, stop_look=-1, reject=False,
        boundaries=schedule.nominal_alpha)


def naive_peeking_fpr(n_looks: int, alpha: float, trials: int = 4000,
                      seed: int = 0) -> float:
    """False-positive rate of peeking with the FULL alpha at every look.

    Under the null each look yields an independent uniform p-value; the
    naive analyst rejects the first time any of them falls under the full
    ``alpha``. The realised rate is the look-elsewhere probability
    ``1-(1-alpha)**n_looks`` -- the inflation optional stopping buys.
    Deterministic in ``seed``."""
    if not isinstance(n_looks, int) or n_looks < 1:
        raise MultipleTestingError("n_looks must be a positive integer")
    a = _check_alpha(alpha)
    rng = np.random.default_rng(seed)
    p = rng.random((int(trials), n_looks))
    return float(np.mean(np.any(p < a, axis=1)))


def spent_peeking_fpr(schedule: SpendingSchedule, trials: int = 4000,
                      seed: int = 0) -> float:
    """False-positive rate of peeking against a spent-down boundary.

    Same null looks as :func:`naive_peeking_fpr`, but each look is tested
    against its own :class:`SpendingSchedule` boundary. The realised rate
    stays at ``alpha`` -- the spend is what controls it. Deterministic in
    ``seed``."""
    if not isinstance(schedule, SpendingSchedule):
        raise MultipleTestingError("expected a SpendingSchedule")
    n_looks = len(schedule.nominal_alpha)
    rng = np.random.default_rng(seed)
    p = rng.random((int(trials), n_looks))
    bounds = np.asarray(schedule.nominal_alpha)
    return float(np.mean(np.any(p <= bounds, axis=1)))


# =======================================================================
# The refusals
# =======================================================================

def refuse_uncorrected_multiple_comparisons(family: TestFamily, *,
                                            corrected: bool = False) -> dict:
    """Refuse a significance call over many tests with no correction.

    A family of more than one test (counting hidden retries) cannot report
    the smallest raw p-value as significant: that p is small by
    construction, and the true false-positive rate is the look-elsewhere
    probability. Correct the family (Bonferroni, Holm or Benjamini-Hochberg)
    first. A single test needs no correction and is allowed through."""
    if not isinstance(family, TestFamily):
        raise MultipleTestingError("expected a TestFamily")
    m = family.total_trials()
    if m > 1 and not corrected:
        raise MultipleTestingError(
            f"refused: this family ran {m} comparisons "
            f"({family.n_reported} reported + {family.hidden_retries} hidden "
            f"retries) and no correction was applied. Reporting the smallest "
            f"p-value (min={family.min_p():.3g}) as significant is a "
            f"look-elsewhere error: with {m} tests the probability that at "
            f"least one null crosses alpha is 1-(1-alpha)^{m}, not alpha. "
            f"Apply Bonferroni, Holm or Benjamini-Hochberg over all {m} "
            f"trials before calling anything significant.")
    return {
        "total_trials": m,
        "corrected": bool(corrected),
        "single_test": m == 1,
        "allowed": True,
    }


def refuse_optional_stopping(prereg: Preregistration | None = None, *,
                             peeked_and_stopped: bool = True) -> dict:
    """Refuse a stop on significance with no preregistered stopping rule.

    Delegates to the R13 authority so there is a single truth for the
    optional-stopping refusal across the platform: peeking at accumulating
    data and stopping the moment a threshold is crossed, with no
    preregistered stopping rule or alpha-spending boundary, inflates the
    false-positive rate without limit. A preregistered rule -- a fixed n, a
    sequential boundary, or an alpha-spending schedule -- is what makes the
    sequential test legitimate."""
    return _r13_refuse_optional_stopping(
        prereg, peeked_and_stopped=peeked_and_stopped)


def refuse_exploratory_as_confirmatory(sealed_commitment: str | None = None, *,
                                       scanned_family: TestFamily | None = None
                                       ) -> None:
    """Refuse to read the best result of an exploratory scan as confirmatory.

    Ranking a family of tests and reporting the top hit is exploration: the
    contrast was chosen *after* seeing the data, so its p-value is not a
    confirmatory p-value no matter how small. Confirmation requires a
    contrast fixed in advance -- a sealed preregistration naming the single
    comparison to be tested. Delegates the seal check to the R13
    authority."""
    m = scanned_family.total_trials() if isinstance(scanned_family,
                                                    TestFamily) else "many"
    try:
        _r13_refuse_result_without_prereg(sealed_commitment,
                                          claim="confirmatory")
    except Exception as exc:  # re-raise in this module's error type
        raise MultipleTestingError(
            f"refused: an exploratory scan over {m} tests cannot yield a "
            f"confirmatory p-value. The reported contrast was selected after "
            f"seeing the ranking, so it was never predicted -- it can only "
            f"generate a hypothesis, not confirm one. Preregister the single "
            f"contrast and seal it before looking; then it can be tested as "
            f"confirmatory. ({exc})") from exc


# =======================================================================
# Diagnostics
# =======================================================================

@dataclass(frozen=True)
class Diagnostics:
    """Flags for pathological inputs that make a p-value untrustworthy."""

    extreme_z_indices: tuple
    low_null_variance: bool
    null_variance: float
    max_abs_z: float
    analysis_version: str = ANALYSIS_VERSION


def diagnose(z_scores, null_variance: float, *, z_flag: float = 6.0,
             var_floor: float = 1e-6) -> Diagnostics:
    """Flag extreme z-scores and a collapsed null variance.

    An implausibly large |z| (default > 6) or a near-zero null variance is
    almost always a broken null model or a numerical artefact, not a real
    effect: a vanishing null variance makes every deviation look enormous
    and inflates z without bound. These are diagnostics to *stop and check
    the null*, not detections."""
    z = np.asarray(list(z_scores), dtype=float)
    if z.size == 0 or not np.all(np.isfinite(z)):
        raise MultipleTestingError("z_scores must be finite and non-empty")
    if not isinstance(null_variance, (int, float)) or \
            not math.isfinite(null_variance) or null_variance < 0:
        raise MultipleTestingError("null_variance must be finite and >= 0")
    extreme = tuple(int(i) for i in np.nonzero(np.abs(z) > z_flag)[0])
    return Diagnostics(
        extreme_z_indices=extreme,
        low_null_variance=bool(null_variance < var_floor),
        null_variance=float(null_variance),
        max_abs_z=float(np.max(np.abs(z))))


# =======================================================================
# Determinism helper
# =======================================================================

def family_digest(family: TestFamily) -> str:
    """A stable content hash of a family, via the R13 canonical serializer.

    Two families with identical content hash identically; any change to a
    p-value, a label or the hidden-retry count changes the digest."""
    if not isinstance(family, TestFamily):
        raise MultipleTestingError("expected a TestFamily")
    return content_hash({
        "name": family.name,
        "p_values": list(family.p_values),
        "labels": list(family.labels),
        "hidden_retries": family.hidden_retries,
        "analysis_version": family.analysis_version,
    })


# =======================================================================
# The report
# =======================================================================

def multiple_testing_report() -> dict:
    """The standing result: correction plus a preregistered stopping rule."""
    alpha = 0.05
    # A worked planted family: 3 true effects among 40 nulls.
    planted = synthetic_planted_family(n_tests=40, n_true=3, true_p=1e-5,
                                        seed=23, name="report")
    bh = power_and_error(planted, CorrectionMethod.BENJAMINI_HOCHBERG, alpha)
    bonf = power_and_error(planted, CorrectionMethod.BONFERRONI, alpha)
    # The look-elsewhere inflation for the same family size.
    m = planted.family.total_trials()
    le = look_elsewhere_probability(m, alpha)
    le_sim = uncorrected_min_p_fpr(m, alpha, trials=3000, seed=1)
    fwer_sim = corrected_family_fpr(m, alpha,
                                    CorrectionMethod.BONFERRONI,
                                    trials=3000, seed=1)
    # A worked sequential schedule over four looks.
    schedule = alpha_spending(alpha, [0.25, 0.5, 0.75, 1.0],
                              SpendingFunction.POCOCK)
    naive = naive_peeking_fpr(4, alpha, trials=3000, seed=2)
    spent = spent_peeking_fpr(schedule, trials=3000, seed=2)
    return {
        "what_this_is": (
            "a multiple-comparisons and sequential-analysis firewall: "
            "family-wise (Bonferroni, Holm) and false-discovery "
            "(Benjamini-Hochberg) correction, an alpha-spending sequential "
            "boundary, and refusals of uncorrected multiple comparisons, "
            "optional stopping, and exploratory-as-confirmatory"),
        "corrections": [m.value for m in CorrectionMethod],
        "spending_functions": [s.value for s in SpendingFunction],
        "worked_example": {
            "family_size": m,
            "n_true_effects": len(planted.true_effects),
            "bh_true_positive_rate": bh["true_positive_rate"],
            "bh_false_discoveries": bh["false_discoveries"],
            "bonferroni_true_positive_rate": bonf["true_positive_rate"],
            "look_elsewhere_probability": le,
            "look_elsewhere_fpr_simulated": le_sim,
            "fwer_after_correction_simulated": fwer_sim,
        },
        "sequential_example": {
            "information_fractions": list(schedule.information_fractions),
            "cumulative_spend": list(schedule.cumulative_spend),
            "per_look_nominal_alpha": list(schedule.nominal_alpha),
            "final_cumulative_spend": schedule.cumulative_spend[-1],
            "naive_peeking_fpr": naive,
            "spent_boundary_fpr": spent,
        },
        "refusals": [
            "refuse_uncorrected_multiple_comparisons",
            "refuse_optional_stopping",
            "refuse_exploratory_as_confirmatory",
        ],
        "claim_class": SOFTWARE_CLAIM_CLASS.value,
        "measured_here": MEASURED_HERE,
        "physical_validation": PHYSICAL_VALIDATION,
        "analysis_version": ANALYSIS_VERSION,
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not say any corrected result is a measurement, and it "
            "does not say a survived correction is real: correcting p-values "
            "and spending alpha are bookkeeping about how many things were "
            "tried and in what order, not evidence that any effect exists. "
            "The look-elsewhere and optional-stopping inflations are "
            "demonstrated on synthetic null data; the corrections remove the "
            "inflation but confirm nothing. A confirmatory claim still needs "
            "a preregistered contrast and, above all, physical data -- none "
            "of which exists here. Nothing is measured; measured_here is "
            "nothing and PHYSICAL_VALIDATION_NOT_CLAIMED."),
    }
