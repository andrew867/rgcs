"""Group C: 37-cell ring math -- locked ratios, theta table, masks.

Plus the structural refusal: the ring module exposes no force,
thrust, torque, or lift callable at all.
"""

from __future__ import annotations

import inspect
import math
from fractions import Fraction

import pytest

from rgcs_workbench.public_cage import ring_model as RM


def test_locked_ratios():
    assert Fraction(188, 288) == Fraction(47, 72)
    assert RM.inner_outer_ratio() == Fraction(47, 72)
    assert RM.EXTERNAL_RESONANCE_HZ == 4096 * 411 == 1_683_456


def test_theta_table():
    table = RM.theta_table()
    assert len(table) == 37
    assert table[0]["theta_rad"] == 0.0
    assert math.isclose(table[1]["theta_rad"] - table[0]["theta_rad"],
                        2 * math.pi / 37)
    assert math.isclose(table[36]["theta_rad"], 72 * math.pi / 37)
    for row in table:
        assert math.isclose(row["theta_deg"],
                            math.degrees(row["theta_rad"]))


def test_masks_hit_the_locked_occupancy_counts():
    assert RM.active_count(RM.running_mask()) == 35
    assert RM.active_count(RM.steering_mask()) == 33
    assert RM.active_count(RM.make_cells()) == 37


def test_profiles_are_distinct_and_units_never_mix():
    assert RM.BENCH_PROFILE["unit"] == "mm"
    assert RM.FIELD_PROFILE["unit"] == "m"
    assert RM.BENCH_PROFILE["name"] != RM.FIELD_PROFILE["name"]
    assert RM.FIELD_PROFILE["status"] == "PROFILE_DECLARED_VALUES_PENDING"


def test_modulated_state_is_the_cosine_state_equation():
    row = RM.modulated_state(0, 0.0, base=2.0, delta=0.5, phi0=0.0)
    assert math.isclose(row["value"], 2.5)          # cos(0) = 1
    row = RM.modulated_state(0, 0.0, base=2.0, delta=0.5,
                             phi0=math.pi)
    assert math.isclose(row["value"], 1.5)
    assert row["claim"] == "RESONATOR_STATE_EQUATION_ONLY"
    with pytest.raises(ValueError):
        RM.modulated_state(0, 0.0, parameter="F")   # no force parameter


def test_direction_agreement_is_the_first_observable():
    cells = RM.steering_mask(open_sector=5)
    commanded = RM.commanded_direction(cells)
    result = RM.direction_agreement(commanded, commanded + 0.05,
                                    tolerance_rad=0.1)
    assert result["agrees"] is True
    result = RM.direction_agreement(commanded, commanded + math.pi,
                                    tolerance_rad=0.1)
    assert result["agrees"] is False
    assert result["claim"] == "DIRECTION_AGREEMENT_ONLY"


def test_wrap_angle_stays_in_range():
    for raw in (-7.0, -math.pi, 0.0, math.pi, 9.42):
        wrapped = RM.wrap_angle(raw)
        assert -math.pi <= wrapped <= math.pi


def test_no_force_thrust_torque_or_lift_callable_exists():
    for name, obj in inspect.getmembers(RM, callable):
        lowered = name.lower()
        for banned in ("force", "thrust", "torque", "lift", "newton"):
            assert banned not in lowered, name
