"""Composed loading + phase-lag sweep -- consistency, nulls, and the
lock-loophole finding codified as tests."""

from __future__ import annotations

import math

import pytest

from rgcs_phyrll_v07 import composed_sweep as CS
from rgcs_phyrll_v07 import steering_optimizer as SO


def test_mod_zero_reduces_to_the_pure_phase_family():
    a = CS.composed_weights(0.0, 0.8)
    b = SO.family_graded_phase_taper(0.8, 4.0)["weights"]
    assert all(abs(x - y) < 1e-12 for x, y in zip(a, b))


def test_lag_zero_reduces_to_the_pure_loading_family():
    a = CS.composed_weights(0.4, 0.0)
    b = SO.family_capacitive_gap_weighting(0.4)["weights"]
    assert all(abs(x - y) < 1e-12 for x, y in zip(a, b))


def test_every_grid_point_is_lock33_rotation_invariant_and_forceless():
    res = CS.sweep(mods=[0.0, 0.3], lags=[0.0, 1.0, 2.0], trials=100)
    for r in res["rows"]:
        assert r["lock_compliant_33"] is True
        assert r["rotation_invariant"] is True
        assert r["computes_force"] is False


def test_composition_beats_both_single_knobs():
    res = CS.sweep(mods=[0.0, 0.4], lags=[0.0, 2.5], trials=100)
    base = res["single_knob_baselines"]
    assert res["best"]["abs_d_eff"] > max(base.values())


def test_every_evaluated_point_beats_its_equal_resource_null():
    res = CS.sweep(mods=[0.1, 0.4], lags=[0.5, 2.0], trials=150)
    assert all(r["beats_null_p95"] for r in res["rows"])


def test_the_unconstrained_maximum_is_a_boundary_artifact():
    """|d_eff| rises monotonically in mod at high lag -- the optimizer is
    walking toward de facto blanking, so an interior optimum does not
    exist without the amplitude floor."""
    vals = [CS.evaluate_point(m, 2.5, trials=50)["abs_d_eff"]
            for m in (0.3, 0.6, 0.9)]
    assert vals[0] < vals[1] < vals[2]
    assert CS.min_active_amplitude(CS.composed_weights(0.9, 2.5)) < 0.2


def test_the_amplitude_floor_is_declared_and_enforced():
    assert CS.ACTIVE_AMPLITUDE_FLOOR == 0.5
    best = CS.constrained_optimum(trials=100)
    assert best["floor_violated"] is False
    assert best["min_active_amplitude"] >= CS.ACTIVE_AMPLITUDE_FLOOR
    assert best["lag_rad"] <= CS.LAG_BOUND_RAD + 1e-9


def test_constrained_optimum_still_beats_the_single_knob_best():
    best = CS.constrained_optimum(trials=100)
    single = abs(SO.weighted_d_eff(
        SO.family_capacitive_gap_weighting(0.4)["weights"]))
    assert best["abs_d_eff"] > 1.3 * single


def test_loading_at_the_floor_keeps_half_amplitude():
    assert CS.min_active_amplitude(
        CS.composed_weights(0.5, math.pi)) >= 0.5
