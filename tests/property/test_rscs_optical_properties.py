"""Property tests (hypothesis) for the Agent 06 optical layer."""
from __future__ import annotations

import math

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from rscs_core.coordinates import PolarizationState
from rscs_core.coupling import nonreciprocal_metrics, overlap_integral
from rscs_core.propagation import (beating_length_mm, dispersion_group_delay,
                                   dispersion_phase)

finite = st.floats(allow_nan=False, allow_infinity=False,
                   min_value=-1e6, max_value=1e6)


@given(phi0=finite, dtau=st.floats(-1e-6, 1e-6), db2=st.floats(-1e-18, 1e-18),
       dw=st.floats(-1e9, 1e9))
def test_dispersion_phase_polynomial(phi0, dtau, db2, dw):
    # the operator IS the quadratic polynomial in (w - w0), exactly --
    # compare against the float-representable frequency offset (w0 is large,
    # so (w0 + dw) - w0 need not equal dw exactly)
    w0 = 1.0e15
    dw_repr = (w0 + dw) - w0
    got = dispersion_phase(phi0, dtau, db2, w0 + dw, w0)
    expect = phi0 + dtau * dw_repr + 0.5 * db2 * dw_repr * dw_repr
    assert math.isclose(got, expect, rel_tol=1e-12, abs_tol=1e-9)
    # and the group delay is its exact derivative
    assert math.isclose(dispersion_group_delay(dtau, db2, w0 + dw, w0),
                        dtau + db2 * dw_repr, rel_tol=1e-12, abs_tol=1e-24)


@given(st.integers(2, 64), st.integers(0, 2 ** 31 - 1))
@settings(max_examples=50)
def test_overlap_cauchy_schwarz(n, seed):
    rng = np.random.default_rng(seed)
    a = rng.normal(size=n) + 1j * rng.normal(size=n)
    b = rng.normal(size=n) + 1j * rng.normal(size=n)
    ov = overlap_integral(a, b)
    assert abs(ov) <= 1.0 + 1e-9
    # self-overlap is exactly 1 with zero phase
    self_ov = overlap_integral(a, a)
    assert math.isclose(abs(self_ov), 1.0, rel_tol=1e-12)
    assert math.isclose(self_ov.imag, 0.0, abs_tol=1e-12)


@given(st.floats(-100.0, 100.0), st.floats(1e-3, 1e3), st.floats(1e-3, 1e3))
def test_real_chi_pure_phase(chi_re, k, length):
    # a purely REAL chi_xy breaks phase reciprocity but not amplitude:
    # T ratio must stay exactly 1 (EP-04-03)
    m = nonreciprocal_metrics(complex(chi_re, 0.0), k, length)
    assert math.isclose(m["transmittance_ratio"], 1.0, rel_tol=1e-12)
    assert math.isclose(m["nonreciprocal_phase_rad"], 2.0 * k * length * chi_re,
                        rel_tol=1e-9, abs_tol=1e-9)


@given(st.floats(-1e3, 1e3), st.floats(1e-6, 1e3))
def test_beating_length_positive_and_symmetric(beta_e, diff):
    # use the float-representable difference (beta_e large vs tiny diff
    # cancels catastrophically otherwise)
    diff_repr = (beta_e + diff) - beta_e
    if diff_repr == 0.0:
        return  # degenerate at float precision; rejected by the operator
    lb = beating_length_mm(beta_e, beta_e + diff)
    assert lb > 0
    # symmetric under swapping the supermodes
    assert math.isclose(lb, beating_length_mm(beta_e + diff, beta_e),
                        rel_tol=1e-12)
    assert math.isclose(lb, 2 * math.pi / abs(diff_repr), rel_tol=1e-9)


@given(st.floats(-1.0, 1.0), st.floats(-1.0, 1.0), st.floats(-1.0, 1.0))
def test_jones_stokes_roundtrip_property(s1, s2, s3):
    norm = math.sqrt(s1 * s1 + s2 * s2 + s3 * s3)
    if norm < 1e-6:
        return  # zero vector rejected by construction; not a state
    p = PolarizationState((s1, s2, s3))   # normalizes internally
    back = PolarizationState.from_jones(*p.jones)
    # atol 1e-7: the (psi, chi) parameterization is ill-conditioned for the
    # tiny linear components near the circular poles (s3 -> +/-1); the
    # well-conditioned cases are checked at 1e-12 in the unit test
    assert np.allclose(back.stokes, p.stokes, atol=1e-7)
