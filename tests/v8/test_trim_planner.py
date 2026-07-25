"""P30 — laser-trim planning simulator: convergence, no overshoot, safety, blocking."""

from __future__ import annotations

import pytest

from r15 import trim_planner as T


def test_simulated_trim_loop_converges_without_overshoot():
    result = T.simulate_trim_loop(detune_hz=500.0, tolerance_hz=1.0)
    assert abs(result["residual_hz"]) <= 1.0
    assert result["converged"] is True
    assert result["overshoot"] is False


def test_trim_model_mass_frequency_inverse():
    model = T.TrimModel.from_frequency(1.0e7)
    dm = model.removed_mass_for_delta_f(100.0)   # raise f by 100 Hz
    df = model.delta_f_for_removed_mass(dm)
    assert df == pytest.approx(100.0, rel=1e-6)


def test_keep_out_zone_blocks_a_site():
    env = T.LaserSafetyEnvelope(
        keep_out_zones=(T.KeepOutZone(name="electrode", cx_mm=0.0, cy_mm=0.0,
                                      radius_mm=1.0),))
    inside = T.TrimSite(site_id="s", feature=list(T.FeatureType)[0],
                        x_mm=0.0, y_mm=0.0)
    with pytest.raises(T.KeepOutViolation):
        env.check_site(inside)


def test_plan_is_not_an_executed_trim():
    with pytest.raises(T.TrimPlannerError):
        T.refuse_plan_as_executed_trim()


def test_overshoot_plan_is_refused():
    with pytest.raises(T.TrimPlannerError):
        T.refuse_overshoot_plan(f_target_hz=1.0e7, f_after_hz=1.0e7 - 50.0)


def test_report_claims_nothing_measured():
    r = T.trim_planner_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
