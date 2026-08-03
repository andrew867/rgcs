"""37-cell ring masks: blank vector S and effective displacement d_eff.

    phi_k = 2*pi*k/37
    S     = sum_k (1 - a_k) * exp(i*phi_k)          (blanks only)
    d_eff = R_h * sum_k w_k * exp(i*phi_k) / sum_k w_k

S is a pure geometry statement about where the blanks sit. It carries no
force: a nonzero S says the blank pattern has a direction, nothing more.
All outputs are MODEL_OUTPUT.
"""

from __future__ import annotations

import cmath
import math

N_CELLS = 37


def phases(n: int = N_CELLS) -> list:
    return [2.0 * math.pi * k / n for k in range(n)]


def mask_all_active(n: int = N_CELLS) -> list:
    return [1] * n


def mask_with_blanks(blanks, n: int = N_CELLS) -> list:
    a = [1] * n
    for b in blanks:
        a[b % n] = 0
    return a


def blank_vector(mask, n: int = N_CELLS) -> complex:
    """S over the blanks. Empty blank set gives exactly 0."""
    return sum((1 - a) * cmath.exp(1j * p)
               for a, p in zip(mask, phases(n)))


def effective_displacement(weights, hub_radius: float,
                           n: int = N_CELLS) -> complex:
    total = sum(weights)
    if total == 0:
        raise ValueError("all-zero weights have no centroid")
    return hub_radius * sum(w * cmath.exp(1j * p)
                            for w, p in zip(weights, phases(n))) / total


def steering_direction_deg(mask, n: int = N_CELLS):
    """arg(S) in degrees, or None when S vanishes (nothing to steer by)."""
    s = blank_vector(mask, n)
    if abs(s) < 1e-12:
        return None
    return math.degrees(cmath.phase(s)) % 360.0


def rotate_mask(mask, steps: int) -> list:
    steps %= len(mask)
    return mask[-steps:] + mask[:-steps]


def mask_suite(n: int = N_CELLS) -> dict:
    """The required v0.6 mask set, computed in one deterministic pass."""
    suite = {
        "all_active_37": mask_all_active(n),
        "nominal_35_adjacent_blanks": mask_with_blanks([0, 1], n),
        "nominal_35_opposite_blanks": mask_with_blanks([0, n // 2], n),
        "steering_33_adjacent": mask_with_blanks([0, 1, 2, 3], n),
        "steering_33_spread": mask_with_blanks([0, 9, 18, 27], n),
    }
    out = {}
    for name, mask in suite.items():
        s = blank_vector(mask, n)
        out[name] = {"mask_active": sum(mask), "S_abs": abs(s),
                     "S_arg_deg": steering_direction_deg(mask, n),
                     "claim": "MODEL_OUTPUT"}
    return out


def randomized_null(n_blanks: int, trials: int, seed: int = 371,
                    n: int = N_CELLS) -> dict:
    """|S| distribution for random masks with the SAME active count.

    The null control: a structured blank pattern only means something if
    its |S| is unusual against random placements of the same number of
    blanks.
    """
    import random
    rng = random.Random(seed)
    mags = []
    for _ in range(trials):
        blanks = rng.sample(range(n), n_blanks)
        mags.append(abs(blank_vector(mask_with_blanks(blanks, n), n)))
    mags.sort()
    return {"n_blanks": n_blanks, "trials": trials,
            "mean_abs_S": sum(mags) / trials,
            "median_abs_S": mags[trials // 2],
            "max_abs_S": mags[-1], "claim": "MODEL_OUTPUT"}


__all__ = ["N_CELLS", "phases", "mask_all_active", "mask_with_blanks",
           "blank_vector", "effective_displacement",
           "steering_direction_deg", "rotate_mask", "mask_suite",
           "randomized_null"]
