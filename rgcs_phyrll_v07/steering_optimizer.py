"""Ring steering optimizer, v0.7.

The engineering question, verbatim from the correction:

    How do we maximise effective field-centre displacement while obeying
    the 37-family / 35-running / 33-active source locks?

This module answers with |d_eff| and arg alignment. It computes **no
force** -- there is no function here that returns newtons, and success is
defined as |d_eff| up with bounded controls, never as thrust.

Mask families implemented (each a candidate steering configuration):

    single blank                two adjacent blanks
    two separated blanks        near-opposite blanks
    graded current taper        graded phase taper
    capacitive / gap weighting proxy

Per family the report carries: the blank vector S, the weighted
effective displacement d_eff, relative asymmetry |d_eff|/R_h, rotation
invariance, arg(d_eff) vs arg(S) alignment, and a null comparison against
equal-count random masks (or a random permutation of the same weight
multiset for graded families).
"""

from __future__ import annotations

import cmath
import math
import random

from rgcs_phyrll_v06 import ring37 as R

from . import SOURCE_LOCKS

N = SOURCE_LOCKS["ring_family"]                     # 37
STEERING_ACTIVE = SOURCE_LOCKS["steering_active"]   # 33
RUNNING_ACTIVE = 35                                  # 35/37 running


def _phi(k: int) -> float:
    return 2.0 * math.pi * k / N


def weighted_d_eff(weights, hub_radius: float = 1.0) -> complex:
    """d_eff for real or COMPLEX weights (phase tapers are complex)."""
    total = sum(abs(w) for w in weights)
    if total == 0:
        raise ValueError("all-zero weights")
    return hub_radius * sum(w * cmath.exp(1j * _phi(k))
                            for k, w in enumerate(weights)) / total


def _sector_distance(k: int, centre: float) -> float:
    """Angular cell distance from cell k to the (possibly fractional)
    sector centre, wrapped to [0, N/2]."""
    d = abs(k - centre) % N
    return min(d, N - d)


# ---------------------------------------------------------------- families

def family_single_blank():
    return {"mask": R.mask_with_blanks([0]), "weights": None,
            "blanks": [0]}


def family_two_adjacent():
    return {"mask": R.mask_with_blanks([0, 1]), "weights": None,
            "blanks": [0, 1]}


def family_two_separated():
    return {"mask": R.mask_with_blanks([0, 9]), "weights": None,
            "blanks": [0, 9]}


def family_near_opposite():
    return {"mask": R.mask_with_blanks([0, 18]), "weights": None,
            "blanks": [0, 18]}


def _steering_blanks():
    """The 33-active steering lock: four adjacent blanks, one open sector."""
    return [0, 1, 2, 3]


def family_graded_current_taper(depth: float = 0.6, width: float = 4.0):
    """33 active; actives near the open sector run reduced current.

    w_k = a_k * (1 - depth * exp(-(dist/width)^2)) -- a smooth current dip
    toward the open sector, deepening the effective hole without breaking
    the 33-active lock (blanked cells stay fully off).
    """
    blanks = _steering_blanks()
    centre = sum(blanks) / len(blanks)
    mask = R.mask_with_blanks(blanks)
    weights = [a * (1.0 - depth * math.exp(-(_sector_distance(k, centre)
                                             / width) ** 2))
               for k, a in enumerate(mask)]
    return {"mask": mask, "weights": weights, "blanks": blanks}


def family_graded_phase_taper(lag_rad: float = 0.8, width: float = 4.0):
    """33 active; actives near the open sector run phase-lagged.

    w_k = a_k * exp(-i * lag * exp(-(dist/width)^2)): amplitude preserved,
    phase pulled near the sector -- the electronic analogue of leaning the
    mode toward the hole.
    """
    blanks = _steering_blanks()
    centre = sum(blanks) / len(blanks)
    mask = R.mask_with_blanks(blanks)
    weights = [a * cmath.exp(-1j * lag_rad
                             * math.exp(-(_sector_distance(k, centre)
                                          / width) ** 2))
               for k, a in enumerate(mask)]
    return {"mask": mask, "weights": weights, "blanks": blanks}


def family_capacitive_gap_weighting(mod: float = 0.4):
    """33 active; a first-harmonic loading proxy.

    w_k = a_k * (1 + mod * cos(phi_k - phi_sector)): heavier capacitive
    loading opposite the open sector, lighter beside it -- the
    gap-width / loading taper as a weight profile.
    """
    blanks = _steering_blanks()
    centre = sum(blanks) / len(blanks)
    phi_c = _phi(0) + 2.0 * math.pi * centre / N
    mask = R.mask_with_blanks(blanks)
    weights = [a * (1.0 + mod * math.cos(_phi(k) - phi_c - math.pi))
               for k, a in enumerate(mask)]
    return {"mask": mask, "weights": weights, "blanks": blanks}


FAMILIES = {
    "single_blank": family_single_blank,
    "two_adjacent_blanks": family_two_adjacent,
    "two_separated_blanks": family_two_separated,
    "near_opposite_blanks": family_near_opposite,
    "graded_current_taper": family_graded_current_taper,
    "graded_phase_taper": family_graded_phase_taper,
    "capacitive_gap_weighting": family_capacitive_gap_weighting,
}


# ---------------------------------------------------------------- metrics

def _null_for(weights, mask, trials: int, rng) -> dict:
    """Null: same resource, random arrangement.

    Binary families: random blanks of equal count. Graded families: a
    random permutation of the SAME weight multiset, so the null holds the
    total drive fixed and randomises only the arrangement.
    """
    mags = []
    if weights is None:
        n_blanks = mask.count(0)
        for _ in range(trials):
            blanks = rng.sample(range(N), n_blanks)
            m = R.mask_with_blanks(blanks)
            mags.append(abs(weighted_d_eff([float(a) for a in m])))
    else:
        w = list(weights)
        for _ in range(trials):
            rng.shuffle(w)
            mags.append(abs(weighted_d_eff(w)))
    mags.sort()
    return {"trials": trials, "null_mean": sum(mags) / trials,
            "null_p95": mags[int(0.95 * trials)], "null_max": mags[-1]}


def evaluate_family(name: str, trials: int = 400, seed: int = 3772) -> dict:
    fam = FAMILIES[name]()
    mask, weights = fam["mask"], fam["weights"]
    eff = weights if weights is not None else [float(a) for a in mask]
    d = weighted_d_eff(eff)
    s = R.blank_vector(mask)
    active = sum(mask)

    # rotation invariance: rotating the configuration rotates d_eff.
    rot = 7
    if weights is None:
        d_rot = weighted_d_eff([float(a) for a in R.rotate_mask(mask, rot)])
    else:
        d_rot = weighted_d_eff(weights[-rot:] + weights[:-rot])
    rot_ok = abs(abs(d_rot) - abs(d)) < 1e-9

    align = None
    if abs(s) > 1e-12 and abs(d) > 1e-12:
        align = math.degrees(abs(cmath.phase(d * s.conjugate())))
        # d_eff points at the surviving current, S at the blanks: for a
        # symmetric hole they are ANTI-aligned. Report distance from 180.
        align = abs(180.0 - align)

    null = _null_for(weights, mask, trials, random.Random(seed))
    return {
        "family": name, "active_cells": active,
        "lock_compliant_33": active == STEERING_ACTIVE,
        "lock_compliant_35": active == RUNNING_ACTIVE,
        "abs_S": abs(s),
        "abs_d_eff": abs(d),
        "relative_asymmetry": abs(d),           # hub_radius = 1
        "arg_d_eff_deg": (math.degrees(cmath.phase(d)) % 360.0
                          if abs(d) > 1e-12 else None),
        "anti_alignment_error_deg": align,
        "rotation_invariant": rot_ok,
        **null,
        # Strictly-greater with a tolerance: a single-blank family's null
        # is a point mass (every placement is a rotation of every other),
        # so equality there must read as NOT beating the null rather than
        # winning by floating-point noise.
        "beats_null_p95": abs(d) > null["null_p95"] + 1e-9,
        "null_degenerate": null["null_max"] - null["null_mean"] < 1e-9,
        "computes_force": False,
        "claim": "MODEL_OUTPUT",
    }


def optimize(trials: int = 400) -> dict:
    """Evaluate every family; rank the lock-compliant 33-active ones."""
    rows = [evaluate_family(name, trials) for name in FAMILIES]
    compliant = [r for r in rows if r["lock_compliant_33"]]
    compliant.sort(key=lambda r: -r["abs_d_eff"])
    return {"rows": rows,
            "lock_compliant_ranking": [r["family"] for r in compliant],
            "best_lock_compliant": compliant[0] if compliant else None,
            "success_metric": "|d_eff| under source locks; NOT force",
            "bench_metrics_pending": ("delta_B magnitude",
                                      "arg(delta_B) vs arg(S)",
                                      "thermal/vibration/electrostatic "
                                      "controls bounded"),
            "claim": "MODEL_OUTPUT"}


__all__ = ["N", "STEERING_ACTIVE", "RUNNING_ACTIVE", "weighted_d_eff",
           "FAMILIES", "evaluate_family", "optimize"]
