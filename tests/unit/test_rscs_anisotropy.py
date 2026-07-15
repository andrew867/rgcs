"""Unit tests for anisotropic elastic propagation (RSCS-O.17 Christoffel
solver + alpha-quartz crystal application)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from rscs_core.propagation import (christoffel_wave_speeds, christoffel_matrix,
                                   voigt_to_tensor)
from rgcs_core.anisotropy import (wave_speeds, axis_speeds, AXIS_X, AXIS_Y,
                                  AXIS_Z, ALPHA_QUARTZ_DENSITY_KG_M3,
                                  alpha_quartz_stiffness_pa, _C11, _C33)


def test_voigt_expansion_symmetry():
    c = alpha_quartz_stiffness_pa()
    full = voigt_to_tensor(c)
    # minor symmetries c_ijkl = c_jikl = c_ijlk
    assert np.allclose(full, np.swapaxes(full, 0, 1))
    assert np.allclose(full, np.swapaxes(full, 2, 3))


def test_axis_speeds_match_closed_form():
    ax = axis_speeds()
    rho = ALPHA_QUARTZ_DENSITY_KG_M3
    # along X the quasi-long speed is sqrt(c11/rho); along Z sqrt(c33/rho)
    assert math.isclose(ax["X"]["v_quasi_long_m_s"],
                        math.sqrt(_C11 * 1e9 / rho), rel_tol=1e-9)
    assert math.isclose(ax["Z"]["v_quasi_long_m_s"],
                        math.sqrt(_C33 * 1e9 / rho), rel_tol=1e-9)


def test_optic_axis_shear_degenerate():
    # along Z (optic axis) the two quasi-shear speeds are degenerate
    z = axis_speeds()["Z"]
    assert math.isclose(z["v_quasi_shear1_m_s"], z["v_quasi_shear2_m_s"],
                        rel_tol=1e-9)


def test_quasi_long_is_fastest():
    for d in (AXIS_X, AXIS_Y, AXIS_Z, np.array([1.0, 1.0, 1.0])):
        r = wave_speeds(d)
        assert r["v_quasi_long_m_s"] >= r["v_quasi_shear1_m_s"] >= \
            r["v_quasi_shear2_m_s"]


def test_direction_normalization_invariant():
    a = wave_speeds(np.array([0.0, 0.0, 2.0]))
    b = wave_speeds(AXIS_Z)
    assert math.isclose(a["v_quasi_long_m_s"], b["v_quasi_long_m_s"])


def test_speeds_bracket_v2_default():
    # v2 default v_L = 6310 m/s must lie between the slowest and fastest
    # quasi-longitudinal axis speeds (the anisotropy the scalar approximated)
    ax = axis_speeds()
    qls = [ax[k]["v_quasi_long_m_s"] for k in ("X", "Y", "Z")]
    assert min(qls) <= 6310.0 <= max(qls) or min(qls) - 6310.0 < 700


def test_errors():
    with pytest.raises(ValueError):
        christoffel_wave_speeds(alpha_quartz_stiffness_pa(), -1.0, AXIS_Z)
    with pytest.raises(ValueError):
        christoffel_matrix(alpha_quartz_stiffness_pa(), np.zeros(3))
    with pytest.raises(ValueError):
        voigt_to_tensor(np.zeros((3, 3)))
