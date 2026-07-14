"""Decay-law fitting, model comparison, and threshold detection
(COH-M10, COH-M12, COH-M14) — exact ports of the normative reference in
tools/generate_golden_coherence.py.

Units: time in s; y in the caller's observable unit. Fits are
deliberately simple (log-linear + coarse grids, scipy-free) so results
are bit-reproducible against the golden manifest; any refined optimizer
must still reproduce the golden winners and delta-AIC signs.
"""

from __future__ import annotations

import math

import numpy as np

from ..provenance import classified, classification_string

__all__ = ["fit_exponential_decay", "model_comparison",
           "threshold_detect_bootstrap"]


@classified("Established", note="COH-M10 helper: log-linear least squares")
def fit_exponential_decay(t: np.ndarray, y: np.ndarray) -> dict:
    """COH-M10. Log-linear least-squares fit y ~= A exp(-t/tau) on samples
    with y > 0. Returns A, tau_s, and RMS residual in log space."""
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    if t.size != y.size or t.size < 2:
        raise ValueError("t and y must be equal-length with >= 2 samples")
    m = y > 0
    if int(np.sum(m)) < 2:
        raise ValueError("need >= 2 positive samples for a log-linear fit")
    slope, intercept = np.polyfit(t[m], np.log(y[m]), 1)
    tau = -1.0 / slope if slope < 0 else float("inf")
    resid = np.log(y[m]) - (slope * t[m] + intercept)
    return {"A": float(np.exp(intercept)), "tau_s": float(tau),
            "log_rms": float(np.sqrt(np.mean(resid ** 2)))}


@classified("Established", sources=("GAN-11",),
            note="COH-M14: AIC/BIC model set {exponential, power law, "
                 "damped oscillatory, no change}; the exponential FORM is "
                 "the GAN-09 analogy (fit form only, coefficient never "
                 "imported); delta-AIC < 2 is a tie")
def model_comparison(t: np.ndarray, y: np.ndarray) -> dict:
    """COH-M14. AIC/BIC comparison of decay-law models fit to (t, y > 0):
        exponential:        y = A exp(-t/tau)                     (k=2)
        power law:          y = A (1 + t/t0)^(-p)                 (k=3)
        damped oscillatory: y = g A exp(-t/tau)|cos(2 pi f t)|+c  (k=4)
        no change:          y = c                                 (k=1)
    Gaussian-residual scores: AIC = n ln(SSR/n) + 2k; BIC with k ln n."""
    t = np.asarray(t, float)
    y = np.asarray(y, float)
    if t.size != y.size or t.size < 4:
        raise ValueError("t and y must be equal-length with >= 4 samples")
    m = y > 0
    t, y = t[m], y[m]
    if t.size < 4:
        raise ValueError("need >= 4 positive samples for model comparison")
    n = t.size
    out: dict = {}

    def score(ssr: float, k: int) -> tuple[float, float]:
        ssr = max(ssr, 1e-300)
        return (n * math.log(ssr / n) + 2 * k,
                n * math.log(ssr / n) + k * math.log(n))

    # exponential (log-linear)
    fe = fit_exponential_decay(t, y)
    pred = fe["A"] * np.exp(-t / fe["tau_s"]) if math.isfinite(fe["tau_s"]) \
        else np.full_like(t, fe["A"])
    a, b = score(float(np.sum((y - pred) ** 2)), 2)
    out["exponential"] = {"AIC": a, "BIC": b, "params": fe}

    # power law: grid over t0, log-linear in p
    best = None
    for t0 in np.geomspace(max(t[1] - t[0], 1e-6), max(t[-1], 1e-3), 25):
        lx = np.log1p(t / t0)
        sl, ic = np.polyfit(lx, np.log(y), 1)
        pred = np.exp(ic) * np.exp(sl * lx)
        ssr = float(np.sum((y - pred) ** 2))
        if best is None or ssr < best[0]:
            best = (ssr, t0, -sl, math.exp(ic))
    a, b = score(best[0], 3)
    out["power_law"] = {"AIC": a, "BIC": b,
                        "params": {"t0_s": best[1], "p": best[2],
                                   "A": best[3]}}

    # damped oscillatory: coarse grid over f, exp fit on residual envelope
    best = None
    for f in np.geomspace(0.5 / (t[-1] - t[0] + 1e-12),
                          0.25 * n / (t[-1] - t[0] + 1e-12), 40):
        osc = np.abs(np.cos(2 * np.pi * f * t))
        env = fe["A"] * np.exp(-t / fe["tau_s"]) if math.isfinite(
            fe["tau_s"]) else np.full_like(t, fe["A"])
        base = env * osc
        denom = float(np.sum(base ** 2))
        g = float(np.sum(base * y) / denom) if denom > 0 else 0.0
        c = float(np.mean(y - g * base))
        pred = g * base + c
        ssr = float(np.sum((y - pred) ** 2))
        if best is None or ssr < best[0]:
            best = (ssr, f, g, c)
    a, b = score(best[0], 4)
    out["damped_oscillatory"] = {"AIC": a, "BIC": b,
                                 "params": {"f_hz": best[1], "gain": best[2],
                                            "offset": best[3]}}

    # no change
    c = float(np.mean(y))
    a, b = score(float(np.sum((y - c) ** 2)), 1)
    out["no_change"] = {"AIC": a, "BIC": b, "params": {"c": c}}

    out["best_by_AIC"] = min((k for k in out if k != "best_by_AIC"),
                             key=lambda k: out[k]["AIC"])
    out["classification"] = classification_string(model_comparison)
    return out


@classified("Established", sources=("KOS-09",),
            note="COH-M12: Established resampling methodology; the "
                 "midpoint-crossing estimator is a Derived choice, biased "
                 "for soft transitions; thresholds are ALWAYS "
                 "setup-specific and never reused across apparatus")
def threshold_detect_bootstrap(x: np.ndarray, y_runs: np.ndarray,
                               n_boot: int = 500,
                               seed: int = 0) -> dict:
    """COH-M12. Threshold (change-point) detection with bootstrap CI.
    x: control-parameter grid, shape (nx,); y_runs: order-parameter
    samples, shape (nx, nruns). Estimator: x* where the run-mean crosses
    the midpoint between its min and max plateaus (linear interpolation).
    Bootstrap: resample runs with replacement, n_boot times, seeded;
    percentile 2.5/97.5 CI."""
    if n_boot < 1:
        raise ValueError("n_boot must be >= 1")
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float)
    y = np.asarray(y_runs, float)
    if y.ndim != 2 or y.shape[0] != x.size or x.size < 2:
        raise ValueError("y_runs must have shape (len(x), n_runs), "
                         "len(x) >= 2")

    def crossing(mean_curve: np.ndarray) -> float:
        lo, hi = float(mean_curve.min()), float(mean_curve.max())
        mid = 0.5 * (lo + hi)
        above = np.where(mean_curve >= mid)[0]
        if not above.size or above[0] == 0:
            return float(x[0])
        i = above[0]
        y0, y1 = mean_curve[i - 1], mean_curve[i]
        frac = (mid - y0) / (y1 - y0) if y1 != y0 else 0.5
        return float(x[i - 1] + frac * (x[i] - x[i - 1]))

    est = crossing(y.mean(axis=1))
    boots = np.empty(n_boot)
    nruns = y.shape[1]
    for b in range(n_boot):
        idx = rng.integers(0, nruns, size=nruns)
        boots[b] = crossing(y[:, idx].mean(axis=1))
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"threshold": est, "ci_lo": float(lo), "ci_hi": float(hi),
            "n_boot": n_boot, "seed": seed,
            "note": "setup-specific; midpoint estimator is biased for "
                    "soft transitions",
            "classification":
                classification_string(threshold_detect_bootstrap)}
