"""P07 — the direct/reciprocal frame of alpha-quartz, tested exactly."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import crystalframe as F


def test_dual_identity_ai_dot_bj_is_two_pi_delta():
    frame = F.LatticeFrame()
    m = frame.metric_dual_identity()
    assert np.allclose(m, 2.0 * math.pi * np.eye(3), atol=1e-9)
    # POWER: an off-diagonal must genuinely be zero, not merely small by
    # accident — perturb the reciprocal basis and the identity must fail.
    bad = m.copy()
    bad[0, 1] = 2.0 * math.pi
    assert not np.allclose(bad, 2.0 * math.pi * np.eye(3), atol=1e-9)


def test_volume_matches_analytic_hexagonal_form():
    frame = F.LatticeFrame()
    assert frame.cell_volume() == pytest.approx(frame.analytic_volume(),
                                                rel=1e-12)
    # and the analytic form really is (sqrt(3)/2) a^2 c
    expect = math.sqrt(3.0) / 2.0 * frame.a ** 2 * frame.c
    assert frame.cell_volume() == pytest.approx(expect, rel=1e-12)


def test_volume_differs_from_a_wrong_formula():
    # guard against a formula that happens to be close: cubic a^2 c is not it
    frame = F.LatticeFrame()
    assert frame.cell_volume() != pytest.approx(frame.a ** 2 * frame.c,
                                                rel=1e-3)


@pytest.mark.parametrize("hkl", [(1, 0, 0), (1, 1, 0), (0, 0, 1),
                                 (1, 0, 1), (2, 1, 0)])
def test_d_spacing_matches_analytic_inverse_d_squared(hkl):
    frame = F.LatticeFrame()
    h, k, l = hkl
    d = frame.d_spacing(h, k, l)
    inv_d2 = frame.analytic_inverse_d_squared(h, k, l)
    assert (1.0 / d ** 2) == pytest.approx(inv_d2, rel=1e-10)


def test_zero_reflection_is_refused():
    with pytest.raises(F.CrystalFrameError):
        F.LatticeFrame().d_spacing(0, 0, 0)


def test_cartesian_fractional_round_trip():
    frame = F.LatticeFrame()
    frac = np.array([0.31, 0.72, 0.15])
    cart = frame.to_cartesian(frac)
    back = frame.to_fractional(cart)
    assert np.allclose(back, frac, atol=1e-10)
    # POWER: the map is not the identity — Cartesian differs from fractional
    assert not np.allclose(cart, frac, atol=1e-3)


def test_symmetry_operators_are_proper_rotations():
    ops = F.LatticeFrame().symmetry_operators()
    assert len(ops) == 6
    for R in ops:
        assert np.allclose(R.T @ R, np.eye(3), atol=1e-12)   # orthogonal
        assert np.linalg.det(R) == pytest.approx(1.0, abs=1e-12)  # proper


def test_three_fold_cubed_is_identity():
    ops = F.LatticeFrame().symmetry_operators()
    three_fold = ops[1]                       # first 3-fold about c
    assert np.allclose(np.linalg.matrix_power(three_fold, 3), np.eye(3),
                       atol=1e-12)
    # and it is not already the identity at first power
    assert not np.allclose(three_fold, np.eye(3), atol=1e-3)


def test_non_positive_lattice_constant_is_refused():
    with pytest.raises(F.CrystalFrameError):
        F.LatticeFrame(a=0.0)
    with pytest.raises(F.CrystalFrameError):
        F.LatticeFrame(c=-1.0)


def test_refuse_frame_as_measurement_raises():
    with pytest.raises(F.CrystalFrameError):
        F.refuse_frame_as_measurement()


def test_report_verdict_and_no_measurement():
    r = F.crystalframe_report()
    assert r["verdict"] == "DIRECT_AND_RECIPROCAL_FRAME_CONSISTENT"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "SOURCE_ESTABLISHED_PHYSICS"
    assert r["lattice_constant_class"] == "CONVENTIONAL_LITERATURE"
    assert "what_this_does_not_say" in r
