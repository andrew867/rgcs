"""P27 — automated sweep controller: axes, ordering, seal, safety, determinism."""

from __future__ import annotations

import pytest

from r15 import sweeps as S

_STRAT = list(S.SweepStrategy)[0]
_MODE = list(S.SweepMode)[0]


def _axis(n=11):
    return S.linear_axis(S.SweepAxisKind.FREQUENCY, 1.0e5, 1.0e6, n, unit="Hz")


def _plan():
    return S.SweepPlan(plan_id="p", axes=(_axis(),), strategy=_STRAT,
                       mode=_MODE, seed=0)


def test_linear_axis_has_requested_point_count():
    ax = _axis(11)
    assert len(ax.values) == 11


def test_log_and_sparse_axes_build():
    lg = S.log_axis(S.SweepAxisKind.FREQUENCY, 1e3, 1e6, 7, unit="Hz")
    sp = S.sparse_axis(S.SweepAxisKind.DRIVE_LEVEL, [0.1, 0.2, 0.5], unit="V")
    assert len(lg.values) == 7
    assert len(sp.values) == 3


def test_plan_orders_points_and_hash_is_deterministic():
    p1, p2 = _plan(), _plan()
    assert p1.plan_hash() == p2.plan_hash()
    assert len(p1.ordered_points()) == len(p1.base_points()) == 11


def test_freeze_seals_and_verifies():
    plan = _plan()
    sealed = S.freeze(plan, epoch=1000)
    assert sealed.verify()
    assert sealed.seal == plan.plan_hash()


def test_safety_bounds_reject_out_of_range():
    b = S.SafetyBounds(lo=0.0, hi=1.0)
    assert b.contains(0.5)
    assert not b.contains(2.0)


def test_report_claims_nothing_measured():
    r = S.sweep_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
