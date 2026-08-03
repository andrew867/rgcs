"""v0.6 ring masks -- S, d_eff, steering, and the required mask suite."""

from __future__ import annotations

import cmath
import math

import pytest

from rgcs_phyrll_v06 import ring37 as R


def test_all_active_gives_exactly_zero_S():
    assert R.blank_vector(R.mask_all_active()) == 0


def test_equal_weights_give_zero_displacement():
    """Sum of all 37 roots of unity vanishes, so a uniform ring has no
    centroid offset."""
    d = R.effective_displacement([1.0] * 37, hub_radius=2.5)
    assert abs(d) < 1e-12


def test_adjacent_blanks_give_strong_S():
    s = abs(R.blank_vector(R.mask_with_blanks([0, 1])))
    assert s == pytest.approx(2.0 * math.cos(math.pi / 37), abs=1e-9)
    assert s > 1.9


def test_near_opposite_blanks_cancel_more_strongly():
    """37 is odd so exact opposition does not exist; k=0 and k=18 are the
    closest pair and nearly cancel."""
    adjacent = abs(R.blank_vector(R.mask_with_blanks([0, 1])))
    opposite = abs(R.blank_vector(R.mask_with_blanks([0, 18])))
    assert opposite < adjacent / 10.0


def test_steering_direction_follows_arg_S():
    mask = R.mask_with_blanks([5])
    expect = math.degrees(2 * math.pi * 5 / 37)
    assert R.steering_direction_deg(mask) == pytest.approx(expect)


def test_steering_is_none_when_S_vanishes():
    assert R.steering_direction_deg(R.mask_all_active()) is None


def test_rotating_a_mask_rotates_arg_S_by_the_cell_pitch():
    base = R.mask_with_blanks([0, 1, 2, 3])
    rot = R.rotate_mask(base, 7)
    d = (R.steering_direction_deg(rot)
         - R.steering_direction_deg(base)) % 360.0
    assert d == pytest.approx(math.degrees(2 * math.pi * 7 / 37), abs=1e-9)


def test_rotation_preserves_S_magnitude():
    base = R.mask_with_blanks([0, 9, 18, 27])
    for k in (1, 12, 30):
        assert abs(R.blank_vector(R.rotate_mask(base, k))) == pytest.approx(
            abs(R.blank_vector(base)), abs=1e-12)


def test_the_required_mask_suite_is_complete_and_consistent():
    suite = R.mask_suite()
    assert suite["all_active_37"]["mask_active"] == 37
    assert suite["all_active_37"]["S_abs"] == 0
    assert suite["nominal_35_adjacent_blanks"]["mask_active"] == 35
    assert suite["steering_33_adjacent"]["mask_active"] == 33
    assert (suite["steering_33_adjacent"]["S_abs"]
            > suite["steering_33_spread"]["S_abs"])


def test_randomized_null_uses_equal_active_count_and_bounds_S():
    null = R.randomized_null(2, trials=300)
    assert null["n_blanks"] == 2
    # two blanks can never exceed |S| = 2
    assert null["max_abs_S"] <= 2.0 + 1e-12
    # adjacent placement is the extreme of the 2-blank family
    adjacent = abs(R.blank_vector(R.mask_with_blanks([0, 1])))
    assert null["max_abs_S"] <= adjacent + 1e-9


def test_zero_weights_are_refused():
    with pytest.raises(ValueError):
        R.effective_displacement([0] * 37, 1.0)


def test_d_eff_matches_the_declared_formula():
    w = [1.0] * 37
    w[4] = 3.0
    manual = 2.0 * sum(wk * cmath.exp(1j * 2 * math.pi * k / 37)
                       for k, wk in enumerate(w)) / sum(w)
    assert R.effective_displacement(w, 2.0) == pytest.approx(manual)
