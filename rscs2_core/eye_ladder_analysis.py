"""Eye post-refinement interpretation (Agent Y01; coverage Y001-Y008)
and calibrated solver resources (Agent Y02; coverage Y009-Y016).

Y01: ladder import, mode tracking by MODE-SHAPE OVERLAP (MAC), not
index; multiple convergence models with model dependence reported;
signed separations; canonical-record immutability; the versioned
verdict record that APPENDS and never replaces.

Y02: the calibrated resource model with confidence ranges, component
breakdown, preflight refusal, and job manifests."""

from __future__ import annotations

import json
import math

import numpy as np

# --- canonical records: immutable, appended-to --------------------------------

CANONICAL_V41 = {
    "record": "v4.1 canonical Eye record",
    "candidate_mm": (-0.295, -0.205, 102.240),
    "station_mm": (-0.447, 0.774, 106.018),
    "separation_mm": 3.906, "halfwidth_mm": 3.08,
    "convergence_shift_mm": 0.353, "cloud_rms_mm": 0.032,
    "tolerance_mm": 1e-6,
    "status": "resolution-limited (halfwidth ~ separation at ~4 mm "
              "spacing); preserved unchanged",
}

V421_LADDER = {
    "record": "v4.2.1 V5 ladder (cl 3.0/2.0/1.5)",
    "levels": {
        "cl3.0": {"spacing_mm": 3.423,
                  "centroid_mm": (0.237, -0.010, 100.986),
                  "f1_hz": 13772.75, "dof": 5394},
        "cl2.0": {"spacing_mm": 2.362,
                  "centroid_mm": (-0.053, -0.038, 99.989),
                  "f1_hz": 13772.38, "dof": 14550},
        "cl1.5": {"spacing_mm": 1.803,
                  "centroid_mm": (-0.048, -0.020, 99.783),
                  "f1_hz": 13772.28, "dof": 30816},
    },
    "verdict": "NEAR_CONVENTIONAL_NODE_BUT_DISTINCT",
    "separation_mm": 6.2976, "halfwidth_mm": 1.8033,
}


class ImmutabilityError(RuntimeError):
    pass


def canonical_record() -> dict:
    """A COPY; the module-level constant is the authority and tests
    verify it cannot be altered through this accessor."""
    return json.loads(json.dumps(CANONICAL_V41))


# --- Y002: mode tracking by shape overlap ---------------------------------------

def mac(phi_a: np.ndarray, phi_b: np.ndarray,
        m: np.ndarray | None = None) -> float:
    """Modal Assurance Criterion:
    MAC = |phi_a^T M phi_b|^2 / ((phi_a^T M phi_a)(phi_b^T M phi_b)).
    Identity mass when M is None (shape-only)."""
    a = np.asarray(phi_a, float).ravel()
    b = np.asarray(phi_b, float).ravel()
    if m is None:
        num = float(a @ b) ** 2
        den = float(a @ a) * float(b @ b)
    else:
        num = float(a @ m @ b) ** 2
        den = float(a @ m @ a) * float(b @ m @ b)
    return num / max(den, 1e-300)


def track_modes(shapes_coarse: list, shapes_fine: list,
                threshold: float = 0.7) -> dict:
    """Assign each coarse mode to its best-MAC fine partner. A best
    match below threshold is reported as LOST/SWITCHED, never
    silently paired; a fine mode claimed twice is a permutation
    conflict and is reported."""
    n_c, n_f = len(shapes_coarse), len(shapes_fine)
    table = np.zeros((n_c, n_f))
    for i, a in enumerate(shapes_coarse):
        for j, b in enumerate(shapes_fine):
            table[i, j] = mac(a, b)
    assignment, conflicts, lost = {}, [], []
    claimed = {}
    for i in range(n_c):
        j = int(np.argmax(table[i]))
        if table[i, j] < threshold:
            lost.append({"coarse_mode": i,
                         "best_mac": float(table[i, j]),
                         "status": "LOST_OR_SWITCHED"})
            continue
        if j in claimed:
            conflicts.append({"fine_mode": j,
                              "claimed_by": [claimed[j], i]})
        claimed[j] = i
        assignment[i] = {"fine_mode": j, "mac": float(table[i, j])}
    return {"assignment": assignment, "lost": lost,
            "conflicts": conflicts, "mac_table": table.tolist(),
            "rule": "mode identity is MAC-based; the index is not "
                    "an identity"}


# --- Y003: convergence models with model dependence -------------------------------

def fit_convergence(spacings: np.ndarray, values: np.ndarray) -> dict:
    """Fit THREE models for value(h) and report all of them:

    - linear:    v = v0 + a h
    - quadratic: v = v0 + a h^2   (expected for linear FE elements)
    - geometric: v_inf from the last three points' ratio

    The spread of the three extrapolated limits IS the model
    dependence, reported as extrapolation_spread — the guard against
    extrapolation laundering."""
    h = np.asarray(spacings, float)
    v = np.asarray(values, float)
    if len(h) < 3:
        return {"insufficient_levels": True}
    lin = np.polyfit(h, v, 1)
    quad = np.polyfit(h ** 2, v, 1)
    d1, d2 = v[-2] - v[-3], v[-1] - v[-2]
    if abs(d1) > 1e-15 and abs(d2 / d1) < 1.0:
        r = d2 / d1
        geo = v[-1] + d2 * r / (1 - r)
    else:
        geo = float("nan")
    limits = {"linear_h": float(lin[1]),
              "quadratic_h2": float(quad[1]),
              "geometric": float(geo)}
    finite = [x for x in limits.values() if math.isfinite(x)]
    spread = max(finite) - min(finite) if len(finite) > 1 else \
        float("nan")
    return {"limits": limits,
            "extrapolation_spread": float(spread),
            "rule": "no single extrapolated limit is quoted without "
                    "the spread across models (Y003)"}


def signed_separation(a_mm, b_mm) -> dict:
    """Y004: signed axial and transverse components, plus magnitude."""
    a = np.asarray(a_mm, float)
    b = np.asarray(b_mm, float)
    d = b - a
    return {"dx_mm": float(d[0]), "dy_mm": float(d[1]),
            "dz_mm": float(d[2]),
            "transverse_mm": float(np.hypot(d[0], d[1])),
            "magnitude_mm": float(np.linalg.norm(d))}


def ladder_interpretation() -> dict:
    """Y005/Y006: the versioned interpretation of the V5 ladder,
    appended to (never replacing) the canonical records."""
    lv = V421_LADDER["levels"]
    hs = np.array([lv[k]["spacing_mm"] for k in lv])
    zs = np.array([lv[k]["centroid_mm"][2] for k in lv])
    fs = np.array([lv[k]["f1_hz"] for k in lv])
    zfit = fit_convergence(hs, zs)
    ffit = fit_convergence(hs, fs)
    return {
        "canonical_v41": canonical_record(),
        "v421_ladder": json.loads(json.dumps(V421_LADDER)),
        "z_convergence": zfit,
        "f_convergence": ffit,
        "drift_vs_canonical": [
            signed_separation(CANONICAL_V41["candidate_mm"],
                              lv[k]["centroid_mm"])["magnitude_mm"]
            for k in lv],
        "drift_vs_station": [
            signed_separation(CANONICAL_V41["station_mm"],
                              lv[k]["centroid_mm"])["magnitude_mm"]
            for k in lv],
        "verdict": {
            "classification": V421_LADDER["verdict"],
            "scope": "computational comparison resolved FOR THIS "
                     "IMPLEMENTED IDEALIZED MODEL; the physical Eye "
                     "hypothesis remains open and untested",
            "language_rule": "say 'the refined detection pipeline "
                             "did not identify a persistent "
                             "corresponding cluster near z=102.24 mm "
                             "under the tested configuration' — "
                             "never 'there is no cluster'",
        },
        "supersedes": None,
        "appends_to": ["v4.1 canonical record", "v4.2.0 preliminary "
                       "ladder", "v4.2.1 V5 ladder"],
    }


# --- Y02: calibrated resource model -----------------------------------------------

# measured calibration points: (dof, peak_gb). The cl=1.5 point is a
# real observation; the smaller ones are bounded by process overhead.
CALIBRATION = [(5394, 0.6), (14550, 2.8), (30816, 13.9)]


def memory_model() -> dict:
    """Fit peak = k * dof^p on the measured points; report the fit
    exponent AND the residuals — a two-point power law through noisy
    data is exactly how the 150x mistake happened, so the model
    carries its own uncertainty."""
    d = np.array([c[0] for c in CALIBRATION], float)
    g = np.array([c[1] for c in CALIBRATION], float)
    p, logk = np.polyfit(np.log(d), np.log(g), 1)
    pred = np.exp(logk) * d ** p
    resid = np.max(np.abs(np.log(pred / g)))
    return {"exponent": float(p), "k": float(np.exp(logk)),
            "max_log_residual": float(resid),
            "calibration_points": CALIBRATION,
            "history": "the first estimator used p=1.5 (2-D rule) "
                       "and was wrong by ~150x; preserved as defect "
                       "V4X-D-005-adjacent in the v4.2.1 register"}


def predict_memory_gb(dof: float, confidence: float = 2.0) -> dict:
    """Point prediction with a multiplicative confidence band from
    the calibration residual (Y011: a range, not one number)."""
    m = memory_model()
    point = m["k"] * dof ** m["exponent"]
    band = math.exp(confidence * m["max_log_residual"])
    return {"dof": dof, "point_gb": point,
            "low_gb": point / band, "high_gb": point * band,
            "confidence_band_factor": band}


def preflight(dof: float, machine_ram_gb: float = 31.6,
              safety_fraction: float = 0.6) -> dict:
    """Y014: refuse a solve whose HIGH estimate exceeds the safety
    fraction of machine RAM. Refusal is the success path here."""
    p = predict_memory_gb(dof)
    limit = machine_ram_gb * safety_fraction
    ok = p["high_gb"] <= limit
    return {**p, "machine_ram_gb": machine_ram_gb,
            "limit_gb": limit, "approved": bool(ok),
            "action": "PROCEED" if ok else
            "REFUSED — projected high estimate "
            f"{p['high_gb']:.1f} GB exceeds the {limit:.1f} GB "
            "safety limit; package for a larger machine (Y015)"}


def job_manifest(clmax_mm: float, dof_estimate: int,
                 n_modes: int = 8) -> dict:
    """Y015: a reproducible job package for remote/HPC execution."""
    p = predict_memory_gb(dof_estimate)
    return {"schema": "rgcs.eye.job/1",
            "geometry": "ideal_n7 (crystal110.build_crystal)",
            "clmax_mm": clmax_mm, "n_modes": 6 + n_modes,
            "solver": "scipy shift-invert LU (default) | LOBPCG "
                      "candidate (Y012)",
            "expected_dof": dof_estimate,
            "expected_memory_gb": [p["low_gb"], p["high_gb"]],
            "command": f"python tools/v4x_eye_refinement_v5.py "
                       f"--deep --budget 86400",
            "checkpointing": "per-level incremental writes "
                             "(refinement_levels_v5_partial.json)",
            "outputs": ["refinement_ladder_v5.json"]}
