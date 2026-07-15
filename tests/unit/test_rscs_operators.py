"""Unit tests for RSCS-O.* operators: types, correctness on small inputs,
and error handling."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs_core.coordinates import (SpatialCoordinate, OrientationFrame,
                                   ModalState, PolarizationState,
                                   SelectionCoordinate, GroupDelay, Wavevector)
from rscs_core import operators as ops


def test_frame_transform_identity():
    p = SpatialCoordinate((1.0, 2.0, 3.0))
    out = ops.frame_transform(p, OrientationFrame.identity())
    assert np.allclose(out.vector, p.vector)


def test_frame_transform_type_error():
    with pytest.raises(TypeError):
        ops.frame_transform((1, 2, 3), OrientationFrame.identity())


def test_parity_diagonalizes_degenerate():
    # For a degenerate pair the even/odd states are the hybrid eigenstates.
    s = ModalState.from_components([1 + 0j, 0 + 0j])
    even_odd = ops.to_parity_basis(s)
    assert np.allclose(np.abs(even_odd.amplitudes),
                       [1 / math.sqrt(2), 1 / math.sqrt(2)])


def test_cascade_unitary():
    # product of unitary matrices is unitary
    theta = 0.3
    rot = np.array([[math.cos(theta), -math.sin(theta)],
                    [math.sin(theta), math.cos(theta)]], dtype=complex)
    out = ops.cascade([rot, rot, rot])
    assert ops.is_unitary(out)


def test_reverse_cascade_swaps_rows():
    m = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=complex)
    fwd = ops.cascade([m])
    bwd = ops.reverse_cascade([m])
    # swap-on-reversal: bwd = X m X, so off-diagonal <-> and diag <->
    assert math.isclose(bwd[0, 0].real, fwd[1, 1].real)
    assert math.isclose(bwd[0, 1].real, fwd[1, 0].real)


def test_phase_match():
    r = ops.phase_match(1.0, 0.5, 1.5)
    assert r["matched"] and math.isclose(r["delta_q_rad_mm"], 0.0)
    r2 = ops.phase_match(1.0, 0.5, 2.0)
    assert not r2["matched"]


def test_group_delay_balance():
    g = GroupDelay([1e-9, 3e-9, 2e-9])
    bal = ops.balance_group_delay(g)
    assert math.isclose(float(np.mean(bal.tau_g_s)), 0.0, abs_tol=1e-18)
    # imbalance preserved
    assert math.isclose(bal.imbalance_s, g.imbalance_s)


def test_state_prep_occupancy():
    pol = PolarizationState.sigma_plus()
    sel = SelectionCoordinate(0.0, 1.0)
    psi = ops.prepare_two_level(pol, sel)
    assert math.isclose(psi.total_occupancy, 1.0, rel_tol=1e-12)


def test_dB_metrics():
    assert math.isclose(ops.insertion_loss_db(1.0), 0.0, abs_tol=1e-12)
    assert math.isclose(ops.isolation_db(0.001), 30.0, rel_tol=1e-9)
    assert math.isclose(ops.nonreciprocal_contrast_db(1.0, 0.001), 30.0,
                        rel_tol=1e-9)
    with pytest.raises(ValueError):
        ops.insertion_loss_db(0.0)


def test_operators_map_complete():
    assert set(ops.OPERATORS) == {f"RSCS-O.{i}" for i in range(1, 14)}


def test_coupling_rejects_asymmetric():
    with pytest.raises(ValueError):
        ops.couple_modes([1000.0, 1000.0], [[0.0, 10.0], [5.0, 0.0]])
