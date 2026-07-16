"""Agent M6: dynamic boundary / mixing / energy / symmetry tests
(gates F1-F5)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs2_core import dynamic_boundary as db, fem


# --- schedules (gate F1) ---------------------------------------------------

def test_typed_schedules_serialize_and_validate():
    s = db.BoundarySchedule("mechanical_support", "ramp", 0.0, 1e9,
                            t_switch_s=1e-3, duration_s=2e-3)
    v = s.value(np.array([0.0, 2e-3, 5e-3]))
    assert v[0] == 0.0 and v[1] == pytest.approx(0.5e9) \
        and v[2] == 1e9
    sud = db.BoundarySchedule("electrical_potential", "sudden",
                              0.0, 5.0, t_switch_s=1e-3)
    assert sud.value(0.5e-3) == 0.0 and sud.value(2e-3) == 5.0
    with pytest.raises(ValueError, match="unknown schedule kind"):
        db.BoundarySchedule("thermal_hack", "sudden", 0, 1, 0)
    with pytest.raises(ValueError, match="ramp requires"):
        db.BoundarySchedule("optical_condition", "ramp", 0, 1, 0)
    # switching-rate measure: sudden >> 1, slow ramp << 1
    fast = sud.switching_rate_measure(1e-3)
    slow = s.switching_rate_measure(1e-6)
    assert fast > 1e6 and slow < 1e-2


# --- modal projection (gate F2) ---------------------------------------------

def _cantilever(spring=0.0):
    mesh = fem.box_mesh((0.08, 0.01, 0.01), (10, 2, 2))
    prob = fem.assemble_isotropic(mesh, 210e9, 0.3, 7850.0)
    if spring > 0:
        prob = fem.add_elastic_support(
            prob, lambda x: np.isclose(x[0], 0.08), spring)
    fixed = prob.basis.get_dofs(
        lambda x: np.isclose(x[0], 0.0)).flatten()
    sol = fem.solve_modes(prob, 6, fixed_dofs=fixed)
    return prob, sol


def test_no_change_identity_and_mixing_regimes():
    prob, sol = _cantilever()
    mix0 = db.mode_mixing_matrix(prob, sol, sol)
    assert np.allclose(mix0, np.eye(mix0.shape[0]), atol=1e-8)
    # adiabatic proxy: a WEAK end spring barely mixes modes
    _, sol_soft = _cantilever(spring=1e5)
    mix_soft = db.mode_mixing_matrix(prob, sol, sol_soft)
    off_soft = np.max(np.abs(mix_soft - np.diag(np.diag(mix_soft))))
    assert off_soft < 0.05
    # sudden strong spring mixes substantially
    _, sol_hard = _cantilever(spring=1e12)
    mix_hard = db.mode_mixing_matrix(prob, sol, sol_hard)
    off_hard = np.max(np.abs(mix_hard - np.diag(np.diag(mix_hard))))
    assert off_hard > 5 * off_soft
    # state projection: norms bounded by completeness
    c = db.project_state(mix_hard, np.array([1.0, 0, 0, 0, 0, 0]))
    assert np.linalg.norm(c) <= 1.0 + 1e-9


def test_degenerate_subspace_rotation_invariance():
    """The square cantilever's bending pair is degenerate: individual
    overlaps are basis-arbitrary but the SUBSPACE overlap is 1."""
    prob, sol = _cantilever()
    # re-solve (deterministic, same basis) then rotate the pair by
    # an arbitrary angle to emulate a different degenerate basis
    modes2 = sol["modes"].copy()
    th = 0.7
    R = np.array([[math.cos(th), -math.sin(th)],
                  [math.sin(th), math.cos(th)]])
    modes2[:, 0:2] = modes2[:, 0:2] @ R
    sol2 = dict(sol)
    sol2["modes"] = modes2
    mix = db.mode_mixing_matrix(prob, sol, sol2)
    ov = db.degenerate_subspace_overlap(mix, [0, 1], [0, 1])
    assert ov == pytest.approx(1.0, abs=1e-9)
    # while the individual diagonal entries are NOT 1
    assert abs(mix[0, 0]) < 0.99


# --- work-energy (gate F3) ---------------------------------------------------

def test_oscillator_work_energy_closure_sudden_and_adiabatic():
    w1, w2 = 2 * math.pi * 50.0, 2 * math.pi * 80.0
    # SUDDEN: switch at a moment of max displacement (v=0):
    # E2/E1 = w2^2/w1^2 exactly
    quarter = 0.25 * (2 * math.pi / w1)   # x = x0? start at x0, v=0
    sud = db.oscillator_schedule(
        lambda t: np.where(np.asarray(t) < 1e-4, w1, w2),
        x0=1.0, v0=0.0, t_end_s=0.3, n=120_000)
    assert sud["closure_rel_err"] < 1e-3          # ledger closes
    e0 = sud["energy_j"][0]
    ef = sud["energy_j"][-1]
    # switch happens within the first 1e-4 s (x ~ x0): expected ratio
    assert ef / e0 == pytest.approx((w2 / w1) ** 2, rel=2e-3)
    # ADIABATIC: slow ramp conserves E/w
    ramp = db.oscillator_schedule(
        lambda t: w1 + (w2 - w1) * np.clip(np.asarray(t) / 0.3, 0, 1),
        x0=1.0, v0=0.0, t_end_s=0.3, n=120_000)
    inv = ramp["adiabatic_invariant"]
    assert abs(inv[-1] - inv[0]) / inv[0] < 0.02
    assert ramp["closure_rel_err"] < 1e-3


# --- symmetry lowering (gate F4) ----------------------------------------------

def test_symmetry_lowering_splits_pair_reproducibly():
    out = db.symmetry_lowering_sweep([0.0, 0.01, 0.02, 0.04])
    rows = out["sweep"]
    assert rows[0]["rel_split"] < 5e-3          # symmetric: degenerate
    splits = [r["rel_split"] for r in rows]
    assert splits == sorted(splits)             # monotone in eps
    # near-linear regime: doubling eps ~ doubles the split
    assert splits[2] / max(splits[1], 1e-12) == pytest.approx(2.0,
                                                              rel=0.3)
    # participation bounded
    for r in rows:
        assert 0.0 < r["participation"] <= 1.0
    # continuation: consecutive first modes stay correlated
    for r in rows[1:]:
        assert r["mode_correlation_prev"] is None or \
            r["mode_correlation_prev"] > 0.2
    assert "NO" in out["note"] and "tunnelling" in out["note"]


# --- interfaces + wording (gate F5) --------------------------------------------

def test_tunnelling_interface_only_and_no_forbidden_wording():
    rec = db.tunnelling_interface_record({"kind": "double_well"})
    assert rec["classification"] == "INTERFACE_ONLY"
    assert "no tunnelling computation" in rec["note"]
    # every public OUTPUT of this module is free of the forbidden
    # claim wordings (the module keeps them only as a prohibition list)
    outputs = [str(rec),
               str(db.symmetry_lowering_sweep([0.0])["note"]),
               str(db.BoundarySchedule("mechanical_support", "sudden",
                                       0, 1, 0).__dict__)]
    for text in outputs:
        for phrase in db.FORBIDDEN_WORDINGS:
            assert phrase not in text.lower(), phrase
