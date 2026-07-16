"""Agent M8: calibration / drift / inverse design tests (gates I1-I5)."""
from __future__ import annotations

import numpy as np
import pytest

from rscs2_core import calibration as cal


def _ledger(f0=1000.0, slope=0.0, sigma=0.05, n=60, seed=3):
    rng = np.random.default_rng(seed)
    led = cal.ObservationLedger()
    for i in range(n):
        t = float(i)
        led.append(cal.Observation(f"o{i}", "freq_hz",
                                   f0 + slope * t
                                   + sigma * rng.standard_normal(),
                                   sigma, t))
    return led


def _model(t, p):
    return p[0] + p[1] * t


def test_deterministic_fit_and_recovery():
    """Gate I1: repeated fit reproduces bit-identically; synthetic
    parameters recovered within uncertainty."""
    led = _ledger(f0=1234.5, slope=0.02)
    a = cal.fit_parameters(_model, led, [1000.0, 0.0])
    b = cal.fit_parameters(_model, led, [1000.0, 0.0])
    assert np.array_equal(a["estimate"], b["estimate"])
    assert a["identifiable"]
    assert abs(a["estimate"][0] - 1234.5) < 4 * a["sigma"][0]
    assert abs(a["estimate"][1] - 0.02) < 4 * a["sigma"][1]


def test_non_identifiability_reported_not_hidden():
    """Gate I2: perfectly correlated parameters are flagged."""
    led = _ledger()

    def degenerate(t, p):
        return (p[0] + p[1]) + 0.0 * t       # only the sum matters
    out = cal.fit_parameters(degenerate, led, [500.0, 500.0])
    assert not out["identifiable"]
    assert "NON-IDENTIFIABLE" in out["note"]
    assert np.isnan(out["sigma"]).all()


def test_ledger_immutable_and_tamper_detected():
    led = _ledger(n=10)
    assert led.verify()
    with pytest.raises(AttributeError):
        led.records[0].value = 999.0          # frozen dataclass
    assert not hasattr(led, "update") and not hasattr(led, "delete")
    led._records[3] = cal.Observation("evil", "freq_hz", 1.0, 1.0,
                                      3.0)    # simulated tampering
    assert not led.verify()                   # chain catches it


def test_drift_tracking_alerts_without_mutation():
    """Gate I3: synthetic drift onset produces an alert; the raw
    ledger stays intact."""
    rng = np.random.default_rng(5)
    led = cal.ObservationLedger()
    for i in range(120):
        f = 1000.0 if i < 60 else 1002.0      # step drift
        led.append(cal.Observation(f"o{i}", "freq_hz",
                                   f + 0.05 * rng.standard_normal(),
                                   0.05, float(i)))
    out = cal.track_drift(lambda t, p: p[0] + 0 * t, led, [1000.0],
                          window=20)
    assert out["alerts"], "drift not detected"
    assert out["ledger_intact"]


def test_inverse_design_diversity_and_impossible_objective():
    # two symmetric minima -> nonunique candidates
    f = lambda x: (x[0] ** 2 - 1.0) ** 2 + 0.1 * x[1] ** 2
    out = cal.inverse_design(f, [(-2, 2), (-1, 1)])
    assert out["feasible"]
    assert out["nonunique"]
    xs = sorted(c["x"][0] for c in out["candidates"])
    assert xs[0] < -0.9 and xs[-1] > 0.9      # both wells found
    # deterministic
    out2 = cal.inverse_design(f, [(-2, 2), (-1, 1)])
    assert np.array_equal(out["best"]["x"], out2["best"]["x"])
    # NaN objective -> honest infeasibility
    bad = cal.inverse_design(lambda x: float("nan"), [(-1, 1)])
    assert not bad["feasible"] and "reported" in bad["note"]


def test_policy_guard_blocks_classification_changes():
    """Gate I4."""
    env = {"classification": "REDUCED_ORDER_VALIDATED",
           "evidence_tags": ["DER"], "value": 1.0}
    with pytest.raises(cal.PolicyViolation, match="immutable"):
        cal.guarded_update(env, {"classification": "CORE_VALIDATED"})
    with pytest.raises(cal.PolicyViolation, match="confined"):
        cal.guarded_update(env, {"value": 2.0})
    ok = cal.guarded_update(env, {"calibration.fitted_f0": 1001.2})
    assert ok["classification"] == "REDUCED_ORDER_VALIDATED"
    assert ok["calibration.fitted_f0"] == 1001.2


def test_rl_disabled_by_default_and_simulation_only():
    """Gate I5."""
    with pytest.raises(cal.PolicyViolation, match="disabled by "
                                                  "default"):
        cal.rl_control_adapter()
    out = cal.rl_control_adapter(enabled=True)
    assert out["classification"] == "ENG"
    assert "SIMULATION" in out["note"]
    assert "reward_baseline" in out
