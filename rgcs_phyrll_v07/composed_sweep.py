"""Composed loading + phase-lag 2-D sweep, v0.7 follow-on.

The single-knob result was: capacitive/gap loading is the strongest
MAGNITUDE knob (|d_eff| 0.283) and phase lag is the only DIRECTION knob
(rotates d_eff ~25 deg off the blank axis, at magnitude cost). This
module composes them and sweeps the 2-D grid

    w_k = a_k * (1 + mod*cos(phi_k - phi_c - pi))          (loading)
              * exp(-i * lag * exp(-(dist_k/width)^2))      (phase)

under the unchanged source locks (37 family, 33 active, blanks [0..3],
no rotation). Everything is |d_eff| and direction; **no force is
computed**, and the equal-resource null (same weight multiset, shuffled
arrangement) runs at every grid point.

The deliverable is the drive recipe: max |d_eff| overall, and the Pareto
frontier of |d_eff| against direction offset from the blank axis --
i.e. what magnitude the ring keeps when you ask it to point somewhere
other than straight at the hole.
"""

from __future__ import annotations

import cmath
import math
import random

from rgcs_phyrll_v06 import ring37 as R

from .steering_optimizer import (N, STEERING_ACTIVE, _phi,
                                 _sector_distance, _steering_blanks,
                                 weighted_d_eff)


def composed_weights(mod: float, lag_rad: float,
                     width: float = 4.0) -> list:
    """The composed family. mod=0 reduces to the pure phase taper;
    lag=0 reduces to the pure capacitive/gap loading family."""
    blanks = _steering_blanks()
    centre = sum(blanks) / len(blanks)
    phi_c = _phi(0) + 2.0 * math.pi * centre / N
    mask = R.mask_with_blanks(blanks)
    out = []
    for k, a in enumerate(mask):
        loading = 1.0 + mod * math.cos(_phi(k) - phi_c - math.pi)
        phase = cmath.exp(-1j * lag_rad
                          * math.exp(-(_sector_distance(k, centre)
                                       / width) ** 2))
        out.append(a * loading * phase)
    return out


def _blank_axis_deg() -> float:
    """Direction of the open sector (the S vector of the blanks)."""
    s = R.blank_vector(R.mask_with_blanks(_steering_blanks()))
    return math.degrees(cmath.phase(s)) % 360.0


def _null_p95(weights, trials: int, rng) -> float:
    w = list(weights)
    mags = []
    for _ in range(trials):
        rng.shuffle(w)
        mags.append(abs(weighted_d_eff(w)))
    mags.sort()
    return mags[int(0.95 * trials)]


def evaluate_point(mod: float, lag_rad: float, width: float = 4.0,
                   trials: int = 200, seed: int = 7237) -> dict:
    w = composed_weights(mod, lag_rad, width)
    d = weighted_d_eff(w)
    active = sum(1 for x in w if abs(x) > 0)
    axis = _blank_axis_deg()
    arg_d = math.degrees(cmath.phase(d)) % 360.0 if abs(d) > 1e-12 else None
    # offset from the ANTI-blank axis (where amplitude families point).
    offset = None
    if arg_d is not None:
        anti = (axis + 180.0) % 360.0
        offset = abs((arg_d - anti + 180.0) % 360.0 - 180.0)
    p95 = _null_p95(w, trials, random.Random(seed))
    rot = 7
    d_rot = weighted_d_eff(w[-rot:] + w[:-rot])
    return {"mod": mod, "lag_rad": lag_rad,
            "active_cells": active,
            "lock_compliant_33": active == STEERING_ACTIVE,
            "abs_d_eff": abs(d),
            "arg_d_eff_deg": arg_d,
            "direction_offset_deg": offset,
            "null_p95": p95,
            "beats_null_p95": abs(d) > p95 + 1e-9,
            "rotation_invariant": abs(abs(d_rot) - abs(d)) < 1e-9,
            "computes_force": False}


def sweep(mods=None, lags=None, width: float = 4.0,
          trials: int = 200) -> dict:
    """The 2-D grid, plus the maximum and the direction/magnitude Pareto."""
    mods = mods if mods is not None else [round(0.1 * i, 2)
                                          for i in range(10)]      # 0..0.9
    lags = lags if lags is not None else [round(0.25 * i, 2)
                                          for i in range(11)]      # 0..2.5
    rows = [evaluate_point(m, l, width, trials)
            for m in mods for l in lags]

    best = max(rows, key=lambda r: r["abs_d_eff"])

    # Pareto: per 5-degree direction-offset bin, the best magnitude.
    frontier = {}
    for r in rows:
        if r["direction_offset_deg"] is None:
            continue
        b = int(r["direction_offset_deg"] // 5) * 5
        if b not in frontier or r["abs_d_eff"] > frontier[b]["abs_d_eff"]:
            frontier[b] = r
    pareto = [frontier[b] for b in sorted(frontier)]

    return {"grid_mods": mods, "grid_lags": lags, "width": width,
            "rows": rows, "best": best, "pareto": pareto,
            "single_knob_baselines": {
                "capacitive_gap_weighting(mod=0.4)":
                    abs(weighted_d_eff(composed_weights(0.4, 0.0, width))),
                "graded_phase_taper(lag=0.8)":
                    abs(weighted_d_eff(composed_weights(0.0, 0.8, width))),
            },
            "success_metric": "|d_eff| and steerable direction under "
                              "locks; NOT force",
            "claim": "MODEL_OUTPUT"}


#: Amplitude floor for the 33-active lock to hold IN EFFECT, not just in
#: name. The unconstrained sweep rises monotonically toward mod -> 1 and
#: lag beyond pi because at those extremes the near-sector "active" cells
#: run at ~0.13 amplitude and past anti-phase -- nominally active, de
#: facto blanked. That is a loophole in the lock, not a better drive. The
#: floor declares: an active cell must carry at least half amplitude.
#: With first-harmonic loading, min|w| = 1 - mod, so the floor bounds
#: mod <= 0.5; lag is bounded to [0, pi] (beyond pi the nearest cells
#: overshoot anti-phase, the same de facto blanking by phase).
ACTIVE_AMPLITUDE_FLOOR = 0.5
LAG_BOUND_RAD = math.pi


def min_active_amplitude(weights) -> float:
    return min(abs(w) for w in weights if abs(w) > 0)


def constrained_optimum(trials: int = 300) -> dict:
    """Best composed drive with the lock held in effect.

    Searches mod in [0, 0.5] x lag in [0, pi] and verifies the floor on
    the winner rather than assuming the mod-bound implies it.
    """
    best = None
    for m in [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]:
        for l in [0.0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, LAG_BOUND_RAD]:
            r = evaluate_point(m, l, trials=trials)
            r["min_active_amplitude"] = min_active_amplitude(
                composed_weights(m, l))
            if r["min_active_amplitude"] < ACTIVE_AMPLITUDE_FLOOR:
                r["floor_violated"] = True
                continue
            r["floor_violated"] = False
            if best is None or r["abs_d_eff"] > best["abs_d_eff"]:
                best = r
    best["constraint"] = (f"|w_active| >= {ACTIVE_AMPLITUDE_FLOOR}, "
                          f"lag <= pi")
    return best


__all__ = ["composed_weights", "evaluate_point", "sweep",
           "ACTIVE_AMPLITUDE_FLOOR", "LAG_BOUND_RAD",
           "min_active_amplitude", "constrained_optimum"]
