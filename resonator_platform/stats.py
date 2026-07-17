"""Data, statistics, optimization, and preregistration for iterative
tuning (Agent D01) — plus the fabrication/instrument safety contract
(Agent S01) in `safety` below.

The statistical hazards of a trim loop are specific: sequential
testing (every remeasure is a peek), post-selection (report the best
iteration), and scatter-blindness (celebrate a shift smaller than the
remount noise). Each gets a named guard."""

from __future__ import annotations

import math

import numpy as np


class StatsError(RuntimeError):
    pass


def minimum_detectable_shift(remount_scatter_hz: float,
                             fit_uncertainty_hz: float,
                             n_remeasures: int = 1,
                             k_sigma: float = 3.0) -> dict:
    """A trim step can only be claimed if it exceeds
    k * sqrt(scatter^2 + u_fit^2) / sqrt(n): the combined
    repeatability floor. Below it, the honest verdict is
    UNMEASURABLE — and the trim planner must refuse steps that small
    (the fixture module's rule, quantified)."""
    floor = math.hypot(remount_scatter_hz, fit_uncertainty_hz)
    mds = k_sigma * floor / math.sqrt(max(n_remeasures, 1))
    return {"floor_hz": floor, "mds_hz": mds,
            "k_sigma": k_sigma,
            "rule": "a claimed shift below mds_hz is noise wearing "
                    "a result's clothes"}


def sequential_alpha(n_looks: int, alpha_total: float = 0.05) -> dict:
    """Every remeasure in the loop is an interim look. Bonferroni
    spending (conservative, simple, honest): alpha_per_look =
    alpha_total / n_looks."""
    if n_looks < 1:
        raise StatsError("n_looks >= 1")
    return {"n_looks": n_looks, "alpha_total": alpha_total,
            "alpha_per_look": alpha_total / n_looks,
            "note": "Bonferroni is conservative by choice: the trim "
                    "loop's cost asymmetry (irreversible) favours "
                    "false negatives over false positives"}


def preregistration(target_hz: float, band_hz: float,
                    max_iterations: int,
                    remount_scatter_hz: float,
                    fit_uncertainty_hz: float) -> dict:
    """The trim campaign's preregistration record, declared BEFORE the
    first sweep: target, band, iteration cap, the mds floor, and the
    stopping rules. The campaign module writes this to the ledger
    before measuring."""
    mds = minimum_detectable_shift(remount_scatter_hz,
                                   fit_uncertainty_hz)
    if band_hz < mds["mds_hz"]:
        raise StatsError(
            f"acceptance band {band_hz} Hz is tighter than the "
            f"minimum detectable shift {mds['mds_hz']:.2f} Hz: the "
            "campaign cannot verify its own success and must not "
            "start")
    return {"target_hz": target_hz, "band_hz": band_hz,
            "max_iterations": max_iterations,
            "mds": mds,
            "alpha": sequential_alpha(max_iterations + 1),
            "stopping_rules": ["in band (success)",
                               "GuardTripped (mode loss / overshoot "
                               "/ inconsistent)",
                               "no viable candidate (undershoot "
                               "stop)", "iteration cap"],
            "declared_before_first_measurement": True}


def post_selection_guard(iteration_fits: list) -> dict:
    """The reported result is the LAST held-out fit, never the best
    iteration. This function makes that a checked property rather
    than a habit."""
    if not iteration_fits:
        raise StatsError("no fits")
    best = min(range(len(iteration_fits)),
               key=lambda i: abs(iteration_fits[i].get(
                   "error_hz", math.inf)))
    reported = len(iteration_fits) - 1
    return {"reported_index": reported, "best_index": best,
            "post_selected": best != reported and
            abs(iteration_fits[best].get("error_hz", 0)) <
            abs(iteration_fits[reported].get("error_hz", 0)),
            "rule": "report the final held-out fit; if the 'best' "
                    "iteration differs, that is survivorship, not "
                    "success"}


def multi_frequency_search_penalty(n_bands_searched: int,
                                   tolerance_hz: float,
                                   band_width_hz: float) -> dict:
    """Look-elsewhere for multi-frequency target searches, same form
    as the v4.2 frequency-keys null model."""
    p_single = min(1.0, 2 * tolerance_hz / band_width_hz)
    expected = n_bands_searched * p_single
    return {"expected_chance_hits": expected,
            "significant_if_below": 0.05,
            "note": "searching many bands and reporting the hit "
                    "without this penalty is the numerology trap in "
                    "hardware form"}


def bootstrap_ci(values, n_boot: int = 2000, ci: float = 0.95,
                 seed: int = 0) -> dict:
    """Nonparametric CI for small remount/repeatability samples."""
    v = np.asarray(values, float)
    if len(v) < 3:
        raise StatsError("need >= 3 values")
    rng = np.random.default_rng(seed)
    means = np.array([rng.choice(v, len(v)).mean()
                      for _ in range(n_boot)])
    lo, hi = np.percentile(means, [(1 - ci) / 2 * 100,
                                   (1 + ci) / 2 * 100])
    return {"mean": float(v.mean()), "ci": [float(lo), float(hi)],
            "n": len(v)}
