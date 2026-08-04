"""Public-surface tests for the bounded annular engineering optimizer."""

from __future__ import annotations

from fractions import Fraction

from rgcs_phyrll_v07 import SOURCE_LOCKS
from rgcs_phyrll_v07 import roles
from rgcs_phyrll_v07 import steering_optimizer as optimizer


def test_source_locks_are_exact() -> None:
    assert SOURCE_LOCKS["ring_family"] == 37
    assert SOURCE_LOCKS["running_cells"] == 35
    assert SOURCE_LOCKS["steering_active"] == 33
    assert SOURCE_LOCKS["mechanical_rotation"] is False
    assert SOURCE_LOCKS["carrier_hz"] == 1_683_456
    assert SOURCE_LOCKS["aux_ratio_188_288"] == Fraction(47, 72)


def test_optimizer_reports_bounded_field_asymmetry() -> None:
    result = optimizer.optimize(trials=20)
    assert result["best_lock_compliant"]["active_cells"] == 33
    assert result["best_lock_compliant"]["lock_compliant_33"] is True
    assert all(row["rotation_invariant"] for row in result["rows"])
    assert all(row["computes_force"] is False for row in result["rows"])


def test_no_physical_performance_claimant_exists() -> None:
    assert roles.performance_claimants() == []
