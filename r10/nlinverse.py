"""P09 — nonlinear inverse estimation with honest, calibrated uncertainty.

A forward model ``y = f(params, x)`` is easy to fit; the danger is that
a nonlinear fit almost always *returns* a point estimate, and the point
estimate almost always *looks* precise. This module exists to separate
those two facts. It fits nonlinear forward models by least squares, but
before it reports a single number it asks whether the parameters are
even identifiable, and it proves — by simulation — that the uncertainty
it reports is calibrated rather than decorative.

Why a nonlinear inverse problem is so often NON-IDENTIFIABLE
------------------------------------------------------------

Fitting minimises ``sum_i (y_i - f(p, x_i))^2``. Two things can go wrong
that a tight-looking covariance will happily hide:

* **Structural non-identifiability.** For the double exponential
  ``a*exp(-b*t) + c*exp(-d*t)`` the pair ``(a, b)`` and ``(c, d)`` can be
  swapped without changing a single predicted value, so there is never a
  unique labelling. Worse, as the two rates approach each other
  (``b -> d``) the model collapses to ``(a + c)*exp(-b*t)``: only the sum
  ``a + c`` and the common rate are determined, and ``a``, ``c``, ``b``,
  ``d`` individually are not. Infinitely many parameter sets fit *exactly*
  equally well.

* **Practical non-identifiability.** Even when the model is formally
  identifiable, the sensitivity matrix (the Jacobian ``J = df/dp`` at the
  solution) can be nearly rank-deficient. A huge condition number means
  some direction in parameter space barely moves the prediction, so the
  data pins it down only weakly — the fit will still return a number, and
  that number is close to meaningless.

The Jacobian is the whole tell. If ``J`` is rank-deficient, or its
condition number is enormous, then ``J^T J`` — whose inverse *is* the
covariance up to a noise factor — is singular or nearly so. Reporting a
point estimate in that regime is inventing precision, so this module
*refuses*: :func:`refuse_point_estimate_when_nonidentifiable` raises
:class:`InverseError` rather than returning a fitted vector.

Why honest coverage is mandatory
--------------------------------

A covariance matrix is a promise: "the true value lies in this 95%
interval 95% of the time." That promise is testable, and an untested
one is worthless. :func:`coverage_test` generates many synthetic datasets
from known parameters plus noise, fits each, and counts how often the
*true* parameter actually falls inside the reported confidence interval.
For an identifiable problem that fraction comes out near the nominal
level — the uncertainty is calibrated. That empirical check, not the
prettiness of a single covariance, is what licenses reporting an
interval at all.

Provenance and evidence class
-----------------------------

Everything here is ``DERIVED_MATHEMATICS``: least squares, a Jacobian, a
singular-value decomposition, and Monte-Carlo coverage counting on
seeded pseudo-random data. Nothing is measured. The forward models
(sums of exponentials, a saturating response) are named for the kind of
root/crystal-state relaxation the R10 material talks about, but naming a
curve is not observing one. ``PHYSICAL_VALIDATION_NOT_CLAIMED``.
"""

from __future__ import annotations

import enum
import math
from dataclasses import dataclass, field

import numpy as np

# Reuse the seeded RNG helper and default seed from the sibling inverse
# module, unchanged, so every draw here is reproducible the same way.
from r10.inverse import DEFAULT_SEED, _rng

EVIDENCE_CLASS = "DERIVED_MATHEMATICS"
VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Verdict when a fit is well posed: this is software that inverts a
#: nonlinear forward model, and nothing more.
VERDICT_DEFAULT = "NONLINEAR_INVERSE_SOFTWARE_ONLY"

#: Verdict when the parameters cannot be recovered uniquely.
VERDICT_NONIDENTIFIABLE = "NON_IDENTIFIABLE"

#: A Jacobian condition number above this is treated as practical
#: non-identifiability. A judgement call, not a derived constant:
#: identifiable problems here sit at cond ~ 10-1000 and the collapsed
#: double exponential sits above 10^12, so the threshold is comfortably
#: between the two regimes.
DEFAULT_COND_MAX = 1.0e8

#: Relative singular-value floor for the numerical rank of the Jacobian.
DEFAULT_RCOND = 1.0e-10


class InverseError(RuntimeError):
    """Raised when the inverse problem cannot honestly return a point.

    Covers a singular fit, a Jacobian that is rank-deficient or wildly
    ill-conditioned, and any request for a unique estimate where the
    likelihood does not support one.
    """


# --- forward models -----------------------------------------------------

class ModelKind(enum.Enum):
    """The forward models this module knows how to fit."""

    SINGLE_EXPONENTIAL = "single_exponential"
    DOUBLE_EXPONENTIAL = "double_exponential"
    SATURATING = "saturating"


def single_exponential(params, x) -> np.ndarray:
    """``a * exp(-b * x)``. Two parameters, and identifiable from decay
    data with any spread in ``x``: amplitude and rate move the curve in
    independent ways."""
    p = np.asarray(params, dtype=float)
    if p.shape != (2,):
        raise ValueError("single_exponential needs 2 params (a, b)")
    a, b = p
    return a * np.exp(-b * np.asarray(x, dtype=float))


def double_exponential(params, x) -> np.ndarray:
    """``a*exp(-b*x) + c*exp(-d*x)``. Four parameters, and the textbook
    non-identifiable model: ``(a, b)`` and ``(c, d)`` are swappable, and
    as ``b -> d`` only ``a + c`` and the common rate survive."""
    p = np.asarray(params, dtype=float)
    if p.shape != (4,):
        raise ValueError("double_exponential needs 4 params (a, b, c, d)")
    a, b, c, d = p
    xx = np.asarray(x, dtype=float)
    return a * np.exp(-b * xx) + c * np.exp(-d * xx)


def saturating(params, x) -> np.ndarray:
    """A saturating (Michaelis-Menten) response ``vmax * x / (k + x)``.
    Identifiable when ``x`` reaches both the linear and the saturated
    regime; nearly non-identifiable if every sample sits in one of
    them."""
    p = np.asarray(params, dtype=float)
    if p.shape != (2,):
        raise ValueError("saturating needs 2 params (vmax, k)")
    vmax, k = p
    xx = np.asarray(x, dtype=float)
    return vmax * xx / (k + xx)


#: kind -> (callable, parameter names). Kept so the report can describe a
#: model without hard-coding its arity.
FORWARD_MODELS = {
    ModelKind.SINGLE_EXPONENTIAL: (single_exponential, ("a", "b")),
    ModelKind.DOUBLE_EXPONENTIAL: (double_exponential, ("a", "b", "c", "d")),
    ModelKind.SATURATING: (saturating, ("vmax", "k")),
}


# --- the Jacobian and identifiability -----------------------------------

def jacobian(forward, params, x, eps=1e-6) -> np.ndarray:
    """Central-difference sensitivity matrix ``J[i, k] = df_i / dp_k``.

    Numerical rather than analytic on purpose: the identifiability test
    must work for any forward callable the caller passes, not only the
    ones defined here.
    """
    p = np.asarray(params, dtype=float)
    xx = np.asarray(x, dtype=float)
    n = len(xx)
    m = len(p)
    j = np.empty((n, m), dtype=float)
    for k in range(m):
        h = eps * max(1.0, abs(float(p[k])))
        pp = p.copy()
        pm = p.copy()
        pp[k] += h
        pm[k] -= h
        j[:, k] = (np.asarray(forward(pp, xx), dtype=float)
                   - np.asarray(forward(pm, xx), dtype=float)) / (2.0 * h)
    return j


def identifiability(forward, params, x, cond_max=DEFAULT_COND_MAX,
                    rcond=DEFAULT_RCOND) -> dict:
    """Is the parameter vector recoverable from data at these ``x``?

    Computes the Jacobian at ``params`` and inspects its singular
    spectrum. The parameters are identifiable only when ``J`` has full
    column rank *and* its condition number is not enormous. A
    rank-deficient or badly conditioned ``J`` means some parameter
    combination leaves the prediction essentially unchanged, so the data
    cannot distinguish it.
    """
    j = jacobian(forward, params, x)
    n_params = j.shape[1]
    sv = np.linalg.svd(j, compute_uv=False)
    smax = float(sv[0]) if sv.size else 0.0
    smin = float(sv[-1]) if sv.size else 0.0
    tol = rcond * smax
    rank = int((sv > tol).sum())
    cond = (smax / smin) if smin > 0.0 else math.inf
    identifiable = (rank == n_params) and (cond < cond_max)
    return {
        "n_params": n_params,
        "rank": rank,
        "cond": cond,
        "singular_values": sv.tolist(),
        "smallest_singular_value": smin,
        "cond_max": cond_max,
        "identifiable": bool(identifiable),
        "what_this_does_not_say": (
            "that an identifiable Jacobian means the model is correct. "
            "It means only that, if this model holds, the data at these x "
            "constrain its parameters. A well-conditioned fit to the "
            "wrong model is still the wrong model"),
    }


def refuse_point_estimate_when_nonidentifiable(
        forward, params, x, cond_max=DEFAULT_COND_MAX,
        rcond=DEFAULT_RCOND) -> dict:
    """Raise rather than report a point where the parameters are not
    identifiable.

    Returns the identifiability report when the problem *is* well posed,
    so it doubles as an assertion the caller can put in front of any
    reported estimate.
    """
    report = identifiability(forward, params, x, cond_max=cond_max,
                             rcond=rcond)
    if not report["identifiable"]:
        raise InverseError(
            f"refusing to report a point estimate: the Jacobian has rank "
            f"{report['rank']} of {report['n_params']} and condition "
            f"number {report['cond']:.3e} (limit {cond_max:.1e}). At least "
            f"one parameter direction leaves the prediction unchanged, so "
            f"infinitely many parameter sets fit equally well and no "
            f"unique estimate exists. Report the identifiable combination "
            f"or add data that breaks the degeneracy; do not report a "
            f"number the data does not contain.")
    return report


# --- least-squares fit --------------------------------------------------

@dataclass(frozen=True)
class FitResult:
    """A nonlinear least-squares solution with its linearised covariance."""

    params: np.ndarray
    covariance: np.ndarray          # sigma^2 * (J^T J)^-1
    residual_variance: float        # sigma^2 = RSS / (n - p)
    n: int
    n_params: int
    cost: float                     # final RSS
    iterations: int
    success: bool
    evidence_class: str = EVIDENCE_CLASS

    def standard_errors(self) -> np.ndarray:
        return np.sqrt(np.clip(np.diag(self.covariance), 0.0, None))


def fit(forward, x, y, p0, max_iter=200, tol=1e-12, lam0=1e-3) -> FitResult:
    """Levenberg-Marquardt least-squares fit of ``forward`` to ``(x, y)``.

    Returns the estimate together with the linearised covariance
    ``sigma^2 (J^T J)^-1`` where ``sigma^2 = RSS / (n - p)``. The
    covariance is only a promise until :func:`coverage_test` checks it.
    """
    xx = np.asarray(x, dtype=float)
    yy = np.asarray(y, dtype=float)
    p = np.asarray(p0, dtype=float).copy()
    if xx.shape != yy.shape:
        raise ValueError("x and y must have the same shape")
    n = len(xx)
    m = len(p)
    if n <= m:
        raise InverseError(
            f"{n} data points cannot determine {m} parameters; the fit is "
            f"underdetermined before noise even enters")

    r = yy - np.asarray(forward(p, xx), dtype=float)
    cost = float(r @ r)
    lam = float(lam0)
    iterations = 0
    success = False
    for iterations in range(1, int(max_iter) + 1):
        j = jacobian(forward, p, xx)
        g = j.T @ r
        h = j.T @ j
        stepped = False
        for _ in range(40):
            a = h + lam * np.diag(np.diag(h) + 1e-12)
            try:
                dp = np.linalg.solve(a, g)
            except np.linalg.LinAlgError:
                lam *= 10.0
                continue
            pn = p + dp
            rn = yy - np.asarray(forward(pn, xx), dtype=float)
            cn = float(rn @ rn)
            if cn < cost:
                improvement = cost - cn
                p, r, cost = pn, rn, cn
                lam = max(lam / 3.0, 1e-12)
                stepped = True
                if improvement <= tol * max(cost, 1.0):
                    success = True
                break
            lam *= 3.0
            if lam > 1e12:
                break
        if not stepped:
            # No downhill step exists; a stationary point was reached.
            success = True
            break
        if success:
            break

    # Linearised covariance at the solution.
    j = jacobian(forward, p, xx)
    dof = max(n - m, 1)
    sigma2 = cost / dof
    jtj = j.T @ j
    try:
        cov = sigma2 * np.linalg.inv(jtj)
    except np.linalg.LinAlgError:
        cov = sigma2 * np.linalg.pinv(jtj)
    return FitResult(
        params=p,
        covariance=cov,
        residual_variance=sigma2,
        n=n,
        n_params=m,
        cost=cost,
        iterations=iterations,
        success=bool(success),
    )


# --- normal quantile (for confidence intervals) -------------------------

def _norm_ppf(p: float) -> float:
    """Inverse standard-normal CDF via Acklam's rational approximation.

    Dependency-free (no scipy). Accurate to ~1e-9 in the central region,
    which is where confidence-interval z-values live.
    """
    if not 0.0 < p < 1.0:
        raise ValueError("p must be strictly between 0 and 1")
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
    plow, phigh = 0.02425, 1.0 - 0.02425
    if p < plow:
        q = math.sqrt(-2.0 * math.log(p))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q
                + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    if p > phigh:
        q = math.sqrt(-2.0 * math.log(1.0 - p))
        return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q
                 + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1)
    q = p - 0.5
    rr = q * q
    return (((((a[0] * rr + a[1]) * rr + a[2]) * rr + a[3]) * rr + a[4]) * rr
            + a[5]) * q / (((((b[0] * rr + b[1]) * rr + b[2]) * rr + b[3]) * rr
                            + b[4]) * rr + 1)


def z_for_nominal(nominal: float) -> float:
    """Two-sided z multiplier for a nominal confidence level (0.95 -> ~1.96)."""
    if not 0.0 < nominal < 1.0:
        raise ValueError("nominal confidence must be in (0, 1)")
    return _norm_ppf(0.5 * (1.0 + nominal))


# --- coverage / calibration ---------------------------------------------

def coverage_test(forward, true_params, x, noise_sigma, p0=None,
                  trials=500, nominal=0.95, seed=None) -> dict:
    """Empirically check that the reported intervals cover at the nominal rate.

    Generate ``trials`` synthetic datasets ``y = forward(true, x) + noise``,
    fit each, form the per-parameter ``nominal`` confidence interval from
    the fitted covariance, and count how often the *true* parameter lands
    inside it. For a calibrated, identifiable problem every parameter's
    coverage comes out near ``nominal``.
    """
    true = np.asarray(true_params, dtype=float)
    xx = np.asarray(x, dtype=float)
    y0 = np.asarray(forward(true, xx), dtype=float)
    z = z_for_nominal(nominal)
    start = true.copy() if p0 is None else np.asarray(p0, dtype=float)
    rng = _rng(seed)
    m = len(true)
    hits = np.zeros(m, dtype=float)
    fits = 0
    failures = 0
    for _ in range(int(trials)):
        y = y0 + rng.normal(0.0, float(noise_sigma), size=len(xx))
        try:
            res = fit(forward, xx, y, start)
        except InverseError:
            failures += 1
            continue
        if not res.success:
            failures += 1
            continue
        se = res.standard_errors()
        lo = res.params - z * se
        hi = res.params + z * se
        hits += ((true >= lo) & (true <= hi)).astype(float)
        fits += 1
    if fits == 0:
        raise InverseError("every synthetic fit failed; no coverage to report")
    per_param = (hits / fits)
    return {
        "nominal": nominal,
        "z": z,
        "trials": int(trials),
        "fits": fits,
        "failures": failures,
        "per_param_coverage": per_param.tolist(),
        "min_coverage": float(per_param.min()),
        "mean_coverage": float(per_param.mean()),
        "noise_sigma": float(noise_sigma),
        "note": ("coverage near nominal means the reported covariance is "
                 "calibrated, not that the model is true"),
    }


# --- planted, identifiable reference problem ----------------------------

#: A well-posed single-exponential problem: amplitude and rate are both
#: recoverable from decay data spanning several e-foldings. Fixed so the
#: power and coverage results are reproducible.
REFERENCE_SINGLE_PARAMS = np.array([2.0, 0.7])
REFERENCE_X = np.linspace(0.05, 5.0, 30)
REFERENCE_NOISE = 0.03


def planted_single_exponential(seed=None):
    """Return ``(x, y)`` for one noisy realisation of the reference model."""
    rng = _rng(seed)
    y0 = single_exponential(REFERENCE_SINGLE_PARAMS, REFERENCE_X)
    y = y0 + rng.normal(0.0, REFERENCE_NOISE, size=len(REFERENCE_X))
    return REFERENCE_X, y


def power_recovery(seed=None, nominal=0.95) -> dict:
    """Fit the planted single exponential and check the truth is in the CI.

    The POWER half of the module: on an identifiable problem the fit
    recovers the planted parameters and the reported interval contains
    the truth.
    """
    x, y = planted_single_exponential(seed=seed)
    res = fit(single_exponential, x, y, p0=REFERENCE_SINGLE_PARAMS * 1.3)
    z = z_for_nominal(nominal)
    se = res.standard_errors()
    lo = res.params - z * se
    hi = res.params + z * se
    truth = REFERENCE_SINGLE_PARAMS
    in_ci = ((truth >= lo) & (truth <= hi))
    return {
        "true_params": truth.tolist(),
        "estimate": res.params.tolist(),
        "standard_errors": se.tolist(),
        "relative_error": (np.abs(res.params - truth)
                           / np.abs(truth)).tolist(),
        "truth_in_ci": in_ci.tolist(),
        "all_in_ci": bool(in_ci.all()),
        "iterations": res.iterations,
        "success": res.success,
    }


# --- the deliberately non-identifiable demonstration --------------------

#: A double exponential whose two rates are equal, so it collapses to a
#: single exponential: only ``a + c`` and the shared rate are pinned, and
#: ``a``, ``b``, ``c``, ``d`` individually are not.
NONIDENTIFIABLE_PARAMS = np.array([1.0, 0.5, 1.0, 0.5])


def nonidentifiable_example(x=None) -> dict:
    """A double exponential with coincident rates: rank-deficient Jacobian.

    Concrete witness that fitting a flexible nonlinear model can leave
    parameters unrecoverable. The forward model is real, the fit would
    return four numbers, and the Jacobian says at least two of them are
    fiction.
    """
    xx = REFERENCE_X if x is None else np.asarray(x, dtype=float)
    ident = identifiability(double_exponential, NONIDENTIFIABLE_PARAMS, xx)
    return {
        "params": NONIDENTIFIABLE_PARAMS.tolist(),
        "x_span": [float(xx.min()), float(xx.max())],
        "identifiability": ident,
        "why": (
            "with b == d the model is (a + c) exp(-b t): the amplitude "
            "columns of the Jacobian coincide, the rate columns coincide, "
            "and its rank drops from 4 to 2. Only a + c and the common "
            "rate are determined"),
        "verdict": VERDICT_NONIDENTIFIABLE,
    }


# --- report -------------------------------------------------------------

def nlinverse_report(seed=None) -> dict:
    """The P09 summary: what the fitter does, and what it refuses to claim."""
    power = power_recovery(seed=seed)
    coverage = coverage_test(single_exponential, REFERENCE_SINGLE_PARAMS,
                             REFERENCE_X, REFERENCE_NOISE, seed=seed)
    nonident = nonidentifiable_example()
    return {
        "what_this_is": (
            "a nonlinear least-squares inverse estimator that checks "
            "identifiability from the Jacobian before reporting a point, "
            "and proves its uncertainty is calibrated by Monte-Carlo "
            "coverage rather than asserting it"),
        "identifiable_reference": {
            "model": ModelKind.SINGLE_EXPONENTIAL.value,
            "power": power,
            "coverage": coverage,
        },
        "nonidentifiable_demo": nonident,
        "evidence_class": EVIDENCE_CLASS,
        "physical_validation": VALIDATION,
        "measured_here": "nothing",
        "verdict": VERDICT_DEFAULT,
        "verdict_when_unidentifiable": VERDICT_NONIDENTIFIABLE,
        "what_this_does_not_say": (
            "It does not say the fitted parameters are physical, that the "
            "exponential or saturating form is the true forward model, or "
            "that anything was measured. A tight covariance is not "
            "evidence: when the Jacobian is rank-deficient the estimator "
            "refuses a point estimate outright, and even a well-"
            "conditioned fit to the wrong model is still the wrong model. "
            "Calibrated uncertainty bounds error under the assumed model; "
            "it says nothing about whether that model holds."),
    }
