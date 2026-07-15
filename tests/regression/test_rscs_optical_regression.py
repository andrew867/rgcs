"""Regression tests tying the Agent 06 optical operators back to the frozen
v2/RSCS results (conservative-extension discipline):

- the Autler-Townes dressed splitting G corresponds to the frozen
  coupled-mode 2g hybrid splitting (RGCS-M.24; K = i*2*pi*g convention);
- reversing a symmetric transfer-matrix cascade is reciprocal (null),
  while an asymmetric-phase cascade shows the swap-on-reversal signature --
  the D6-003 posture in matrix form;
- quartz acousto-optic M2 uses the Agent 05 anisotropic X-axis speed
  (cross-layer consistency, RSCS-O.17 <-> rgcs_core.optics).
"""
from __future__ import annotations

import math

import numpy as np

from rscs_core.coupling import couple_modes
from rscs_core.observation import autler_townes_response
from rscs_core.propagation import cascade, reverse_cascade


def test_ats_matches_coupled_mode_splitting():
    # Frozen coupled-mode model: degenerate pair, g = 10 Hz -> hybrid
    # frequencies split by 2g = 20 Hz (RGCS-M.24, QA-D-04 convention).
    g_hz = 10.0
    cm = couple_modes([1000.0, 1000.0], [[0.0, g_hz], [g_hz, 0.0]])
    split_hz = cm["splitting_hz"]
    assert math.isclose(split_hz, 2 * g_hz, rel_tol=1e-12)

    # The ATS lineshape with G = 2*pi*(2g) rad/s must peak at the SAME two
    # frequencies: +/- g Hz about the carrier.
    g_rad_s = 2 * math.pi * split_hz
    kappa = 2 * math.pi * 0.5              # narrow lines, resolvable
    d = np.linspace(-2 * g_rad_s, 2 * g_rad_s, 80001)
    r = autler_townes_response(d, kappa, g_rad_s)
    peaks = d[1:-1][(r[1:-1] > r[:-2]) & (r[1:-1] > r[2:])]
    assert len(peaks) == 2
    peak_hz = peaks / (2 * math.pi)
    assert math.isclose(peak_hz[1] - peak_hz[0], split_hz, rel_tol=1e-3)
    assert math.isclose(peak_hz[1], g_hz, rel_tol=1e-3)


def _section(phase_even: float, phase_odd: float) -> np.ndarray:
    return np.diag([np.exp(1j * phase_even), np.exp(1j * phase_odd)])


def test_symmetric_cascade_is_reciprocal():
    # identical sections in both parities: reversal changes nothing
    # measurable -- the D6-003 null in transfer-matrix form
    mats = [_section(0.3, 0.3), _section(1.1, 1.1)]
    fwd = cascade(mats)
    bwd = reverse_cascade(mats)
    assert np.allclose(np.abs(fwd), np.abs(bwd), atol=1e-12)
    assert np.allclose(fwd, bwd, atol=1e-12)


def test_asymmetric_cascade_swap_signature():
    # parity-asymmetric phases: reversal swaps the diagonal -- the
    # EP-06-03 nonreciprocity signature (math only, no quartz claim)
    mats = [_section(0.3, 1.2)]
    fwd = cascade(mats)
    bwd = reverse_cascade(mats)
    assert np.allclose(bwd, np.diag([fwd[1, 1], fwd[0, 0]]), atol=1e-12)
    assert not np.allclose(fwd, bwd, atol=1e-9)


def test_quartz_m2_uses_agent05_anisotropy():
    from rgcs_core.anisotropy import AXIS_X, wave_speeds
    from rgcs_core.optics import (QUARTZ_N_O, QUARTZ_PHOTOELASTIC,
                                  acousto_optic_m2, quartz_acousto_optic_m2)
    from rgcs_core.anisotropy import ALPHA_QUARTZ_DENSITY_KG_M3
    v_x = wave_speeds(AXIS_X)["v_quasi_long_m_s"]
    assert math.isclose(v_x, math.sqrt(86.6e9 / ALPHA_QUARTZ_DENSITY_KG_M3),
                        rel_tol=1e-9)
    expect = acousto_optic_m2(QUARTZ_N_O, QUARTZ_PHOTOELASTIC["p11"],
                              ALPHA_QUARTZ_DENSITY_KG_M3, v_x)
    assert math.isclose(quartz_acousto_optic_m2(), expect, rel_tol=1e-12)
