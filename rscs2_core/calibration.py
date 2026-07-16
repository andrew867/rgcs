"""Adaptive calibration, drift tracking, and inverse design (Agent
M8; gates I1-I5).

Raw observations are IMMUTABLE (append-only hash-chained ledger);
fits are deterministic (fixed seeds / deterministic solvers), report
covariance and identifiability instead of hiding it, and can NEVER
change scientific classification, evidence tags, provenance, or raw
data (policy guard). RL is an optional, disabled-by-default adapter."""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field

import numpy as np

GUARDED_FIELDS = ("classification", "evidence_tags", "source_ids",
                  "equation_ids")


class PolicyViolation(RuntimeError):
    pass


# --- immutable observations ------------------------------------------------

@dataclass(frozen=True)
class Observation:
    obs_id: str
    quantity: str
    value: float
    sigma: float
    t_s: float

    def digest(self, prev: str) -> str:
        return hashlib.sha256(
            (prev + json.dumps(
                [self.obs_id, self.quantity, self.value, self.sigma,
                 self.t_s], sort_keys=True)).encode()).hexdigest()


class ObservationLedger:
    """Append-only, hash-chained. No update or delete API exists;
    verify() detects any post-hoc tampering with the record list."""

    def __init__(self):
        self._records: list[Observation] = []
        self._chain: list[str] = []

    def append(self, obs: Observation) -> str:
        prev = self._chain[-1] if self._chain else "GENESIS"
        h = obs.digest(prev)
        self._records.append(obs)
        self._chain.append(h)
        return h

    @property
    def records(self) -> tuple:
        return tuple(self._records)

    def verify(self) -> bool:
        prev = "GENESIS"
        for obs, h in zip(self._records, self._chain):
            if obs.digest(prev) != h:
                return False
            prev = h
        return True


# --- deterministic fitting --------------------------------------------------

def fit_parameters(model_fn, ledger: ObservationLedger,
                   p0: np.ndarray, bounds=None,
                   cond_limit: float = 1e8) -> dict:
    """Weighted least squares via scipy (deterministic trf). Returns
    estimates, covariance, correlation, and an identifiability flag —
    non-identifiability is REPORTED, never hidden (gate I2)."""
    from scipy.optimize import least_squares
    obs = ledger.records
    y = np.array([o.value for o in obs])
    w = 1.0 / np.array([max(o.sigma, 1e-300) for o in obs])
    t = np.array([o.t_s for o in obs])

    def resid(p):
        return (model_fn(t, p) - y) * w

    kw = {}
    if bounds is not None:
        kw["bounds"] = bounds
    r = least_squares(resid, np.asarray(p0, float), method="trf",
                      **kw)
    J = r.jac
    JTJ = J.T @ J
    cond = float(np.linalg.cond(JTJ))
    identifiable = cond < cond_limit
    if identifiable:
        cov = np.linalg.inv(JTJ)
        d = np.sqrt(np.diag(cov))
        corr = cov / np.outer(d, d)
    else:
        cov = np.full_like(JTJ, np.nan)
        corr = np.full_like(JTJ, np.nan)
    return {"estimate": r.x, "success": bool(r.success),
            "covariance": cov,
            "sigma": (np.sqrt(np.diag(cov)) if identifiable
                      else np.full(len(r.x), np.nan)),
            "correlation": corr, "condition_number": cond,
            "identifiable": identifiable,
            "classification": "ENG",
            "note": ("parameter estimate; raw observations untouched"
                     if identifiable else
                     "NON-IDENTIFIABLE parameter combination "
                     f"(cond {cond:.2e} >= {cond_limit:.0e}); no "
                     "single best-fit is reported as trustworthy")}


# --- drift tracking -----------------------------------------------------------

def track_drift(model_fn, ledger: ObservationLedger, p0, window: int,
                alert_sigma: float = 4.0) -> dict:
    """Windowed re-fits over the time-ordered ledger; residual event
    stream with threshold alerts. Raw observations are never mutated
    (the ledger has no mutation API; verify() re-checked here)."""
    assert ledger.verify(), "ledger tampering detected"
    obs = sorted(ledger.records, key=lambda o: o.t_s)
    fits, events = [], []
    p = np.asarray(p0, float)
    for i in range(0, len(obs) - window + 1, window):
        sub = ObservationLedger()
        for o in obs[i:i + window]:
            sub.append(o)
        f = fit_parameters(model_fn, sub, p)
        fits.append({"t_start_s": obs[i].t_s,
                     "estimate": f["estimate"].tolist(),
                     "sigma": f["sigma"].tolist()})
        if len(fits) > 1 and f["identifiable"]:
            prev = np.array(fits[-2]["estimate"])
            sig = np.array(f["sigma"])
            jump = np.abs(f["estimate"] - prev) / np.maximum(sig,
                                                             1e-300)
            if np.any(jump > alert_sigma):
                events.append({"t_s": obs[i].t_s,
                               "jump_sigma": float(jump.max())})
        p = f["estimate"]
    return {"window_fits": fits, "alerts": events,
            "ledger_intact": ledger.verify()}


# --- inverse design ------------------------------------------------------------

def inverse_design(objective_fn, bounds: list, n_starts: int = 8,
                   seed: int = 20260716, tol: float = 1e-9) -> dict:
    """Deterministic multi-start local search; returns a DIVERSE
    candidate set and a nonuniqueness report; impossible objectives
    yield an honest failure record."""
    from scipy.optimize import minimize
    rng = np.random.default_rng(seed)
    lo = np.array([b[0] for b in bounds])
    hi = np.array([b[1] for b in bounds])
    cands = []
    for _ in range(n_starts):
        x0 = lo + (hi - lo) * rng.random(len(bounds))
        r = minimize(objective_fn, x0, bounds=bounds,
                     method="L-BFGS-B")
        cands.append({"x": r.x, "f": float(r.fun),
                      "success": bool(r.success)})
    cands.sort(key=lambda c: c["f"])
    best = cands[0]
    distinct = [best]
    for c in cands[1:]:
        if all(np.linalg.norm(c["x"] - d["x"])
               > 1e-3 * np.linalg.norm(hi - lo) for d in distinct) \
                and c["f"] < best["f"] * 1.5 + 1e-12:
            distinct.append(c)
    feasible = best["success"] and math.isfinite(best["f"])
    return {"best": best, "candidates": distinct,
            "nonunique": len(distinct) > 1,
            "feasible": feasible,
            "note": None if feasible else
            "objective infeasible/unbounded on the given domain — "
            "reported, not disguised as success"}


# --- policy guard ---------------------------------------------------------------

def guarded_update(envelope: dict, updates: dict) -> dict:
    """Apply optimizer-produced updates to a result envelope. Any
    attempt to touch classification/evidence/provenance raises (gate
    I4); value updates are allowed only into 'calibration' keys."""
    for k in updates:
        if k in GUARDED_FIELDS:
            raise PolicyViolation(
                f"optimizer may not modify '{k}' — scientific "
                "classification and provenance are immutable to fits")
        if not k.startswith("calibration"):
            raise PolicyViolation(
                f"optimizer writes are confined to calibration.* "
                f"keys, got '{k}'")
    out = dict(envelope)
    out.update(updates)
    return out


# --- optional RL adapter ----------------------------------------------------------

def rl_control_adapter(enabled: bool = False, n_arms: int = 4,
                       horizon: int = 500, seed: int = 1):
    """OFF by default (gate I5): raises unless explicitly enabled.
    When enabled, runs a small deterministic-seed bandit SIMULATION
    and reports against a fixed-arm baseline. Classification ENG /
    experimental; never on any release-critical path."""
    if not enabled:
        raise PolicyViolation(
            "RL adapter is disabled by default and cannot block or "
            "gate any core result; enable explicitly for simulation "
            "experiments only")
    rng = np.random.default_rng(seed)
    means = rng.random(n_arms)
    counts = np.zeros(n_arms)
    values = np.zeros(n_arms)
    reward_rl = 0.0
    for t in range(horizon):
        eps = max(0.05, 1.0 / (t + 1))
        a = int(rng.integers(n_arms)) if rng.random() < eps else \
            int(np.argmax(values))
        r = means[a] + 0.1 * rng.standard_normal()
        counts[a] += 1
        values[a] += (r - values[a]) / counts[a]
        reward_rl += r
    baseline = horizon * means[0]          # fixed-arm comparator
    return {"classification": "ENG",
            "reward_rl": reward_rl, "reward_baseline": float(baseline),
            "beats_baseline": bool(reward_rl > baseline),
            "note": "small SIMULATION only; control-architecture "
                    "precedent (SRC-V4-08); no QEC physics claim"}
