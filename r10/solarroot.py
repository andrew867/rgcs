"""P04 — a dynamic solar root from emission-origin centroids.

The Tier-A instruction: *when devising the root location for the sun,
look for the origins of solar flares and other ejections and emissions,
the centroid will help you.*

So the candidate solar root's primary direction is a **weighted centroid
of emission origins** on the solar sphere:

    c_sun(t) = sum_i w_i r_hat_i  /  | sum_i w_i r_hat_i |

The engine computes it, but three disciplines keep it honest:

1. **The roll comes from an independent axis**, never chosen to improve a
   downstream Earth/Moon/Mars match. The solar rotation axis (or magnetic
   dipole candidate) supplies the second direction; the centroid supplies
   the first. Choosing roll to fit a destination is exactly the
   look-elsewhere sin this project keeps catching.

2. **The result is dynamic, with uncertainty** -- one interval of events
   gives one centroid with a spread, not an eternal solar point. Shuffle
   the event weights or scramble their times and the centroid moves the
   way a genuine signal should not survive: the shuffled-event null
   measures whether the observed clustering exceeds chance.

3. **A planted centroid is recovered** (power), and shuffled events are
   not (null). Both are required, or the pipeline proves nothing.

Real flare/CME catalog ingestion needs a data source this environment
does not have; that step is a declared BLOCKED receipt. The engine, the
transforms, the nulls, and the power check are complete and tested on
synthetic events.
"""

from __future__ import annotations

import numpy as np


class SolarRootError(ValueError):
    """Raised on malformed emission input."""


#: Weight families to test separately (never blended silently).
WEIGHT_FAMILIES = ("EQUAL", "XRAY_FLUENCE", "PEAK_FLUX",
                   "MAGNETIC_FLUX", "CME_KINETIC", "DURATION")


def heliographic_to_unit(lat_deg, lon_deg) -> np.ndarray:
    """Heliographic (Stonyhurst-like) lat/lon to a unit vector."""
    lat, lon = np.radians(lat_deg), np.radians(lon_deg)
    return np.array([np.cos(lat) * np.cos(lon),
                     np.cos(lat) * np.sin(lon),
                     np.sin(lat)])


def emission_centroid(unit_vectors: np.ndarray,
                      weights: np.ndarray | None = None) -> dict:
    """Weighted centroid direction on the sphere, with a spread."""
    v = np.asarray(unit_vectors, float)
    if v.ndim != 2 or v.shape[1] != 3:
        raise SolarRootError("need an (N,3) array of unit vectors")
    w = (np.ones(len(v)) if weights is None
         else np.asarray(weights, float))
    if len(w) != len(v):
        raise SolarRootError("weights and vectors differ in length")
    if np.any(w < 0):
        raise SolarRootError("weights must be non-negative")
    s = (w[:, None] * v).sum(axis=0)
    norm = np.linalg.norm(s)
    if norm == 0:
        raise SolarRootError("centroid is undefined (vectors cancel)")
    c = s / norm
    # resultant length R in [0,1]: 1 = tight, 0 = uniform
    resultant = norm / w.sum()
    return {
        "centroid": c,
        "resultant_length": float(resultant),
        "angular_spread_deg": float(np.degrees(np.arccos(
            np.clip(resultant, -1, 1)))),
        "n_events": len(v),
    }


def solar_root_direction(unit_vectors, rotation_axis,
                         weights=None) -> dict:
    """Primary from the centroid, roll from an INDEPENDENT axis.

    The rotation axis is supplied, not fitted. If it is parallel to the
    centroid the roll is still unfixed and the caller must supply a
    different independent direction.
    """
    cen = emission_centroid(unit_vectors, weights)
    primary = cen["centroid"]
    axis = np.asarray(rotation_axis, float)
    axis = axis / np.linalg.norm(axis)
    if abs(np.dot(primary, axis)) > 1 - 1e-6:
        return {"determined": False,
                "why": "rotation axis parallel to centroid; roll unfixed",
                "centroid": primary}
    return {"determined": True, "primary": primary,
            "roll_reference": axis, "resultant_length":
            cen["resultant_length"]}


def _random_sphere(n, rng):
    v = rng.standard_normal((n, 3))
    return v / np.linalg.norm(v, axis=1, keepdims=True)


def shuffled_event_null(unit_vectors, weights, *, trials=2000,
                        seed=20260722) -> dict:
    """Does the observed clustering beat shuffled weights?

    Shuffling the weight-to-event assignment destroys any real
    weight/position correlation while preserving the marginal
    distributions. If the observed resultant is not beaten, the
    weighting adds nothing.
    """
    rng = np.random.default_rng(seed)
    v = np.asarray(unit_vectors, float)
    w = np.asarray(weights, float)
    obs = emission_centroid(v, w)["resultant_length"]
    at_least = 0
    for _ in range(trials):
        wp = rng.permutation(w)
        if emission_centroid(v, wp)["resultant_length"] >= obs:
            at_least += 1
    p = (at_least + 1) / (trials + 1)
    return {"observed_resultant": obs, "p_value": p,
            "verdict": ("WEIGHTING_INFORMATIVE" if p < 0.05
                        else "WEIGHTING_NOT_INFORMATIVE")}


def planted_centroid_power(true_dir, *, n=40, concentration=8.0,
                           trials=200, seed=7) -> dict:
    """Can the engine recover a planted centroid direction?

    Events are drawn clustered around `true_dir`; recovery is the angle
    between the estimated and true centroid. Power = fraction recovered
    within tolerance.
    """
    rng = np.random.default_rng(seed)
    t = np.asarray(true_dir, float)
    t = t / np.linalg.norm(t)
    errs = []
    for _ in range(trials):
        pts = t + rng.standard_normal((n, 3)) / concentration
        pts = pts / np.linalg.norm(pts, axis=1, keepdims=True)
        est = emission_centroid(pts)["centroid"]
        errs.append(np.degrees(np.arccos(np.clip(np.dot(est, t), -1, 1))))
    errs = np.array(errs)
    return {"median_error_deg": float(np.median(errs)),
            "fraction_within_10deg": float(np.mean(errs < 10)),
            "has_power": bool(np.median(errs) < 10)}


REAL_CATALOG_STATUS = {
    "status": "BLOCKED_NO_DATA_SOURCE",
    "why": ("real flare/CME catalog ingestion (GOES X-ray, SDO/AIA EUV, "
            "LASCO CME, active-region magnetograms) needs a data feed "
            "this environment does not have. The engine, transforms, "
            "nulls and power check are complete and tested on synthetic "
            "events; ingesting a real catalog is a future step"),
    "not_faked": ("no real catalog result is reported, and no solar "
                  "root is claimed as physical"),
}


def solar_root_report() -> dict:
    return {
        "primary_from": "weighted emission-origin centroid",
        "roll_from": "independent rotation/dipole axis, never fitted",
        "weight_families": list(WEIGHT_FAMILIES),
        "real_catalog": REAL_CATALOG_STATUS,
        "verdict": "ROOT_CANDIDATE_ONLY",
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "what_this_does_not_say": (
            "It does not locate the Sun's root, and it does not claim a "
            "physical centre. It builds a candidate direction from "
            "emission origins with an independently chosen roll and an "
            "uncertainty, dynamic in time, and refuses to pick the roll "
            "to flatter any Earth/Moon/Mars match."),
    }
