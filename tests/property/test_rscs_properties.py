"""Property tests for RSCS coordinates and operators (Hypothesis-driven):
identity/inverse transforms, composition associativity, phase-wrap
invariance, unit round-trips, uncertainty monotonicity, provenance
preservation."""
from __future__ import annotations

import math

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from rscs_core import units as U
from rscs_core.coordinates import (AngularFrequency, ModalState,
                                   OrientationFrame, PhaseCoordinate,
                                   ProvenanceTag, SpatialCoordinate)
from rscs_core import operators as ops

finite = st.floats(allow_nan=False, allow_infinity=False,
                   min_value=-1e6, max_value=1e6)
pos = st.floats(min_value=1.0, max_value=1e5, allow_nan=False,
                allow_infinity=False)


@given(finite)
def test_phase_wrap_invariance(phi):
    # wrapping is idempotent and lands in [0, 2*pi)
    once = PhaseCoordinate(phi).phi_rad
    twice = PhaseCoordinate(once).phi_rad
    assert 0.0 <= once < 2 * math.pi
    assert math.isclose(once, twice, abs_tol=1e-9)


@given(pos)
def test_frequency_roundtrip(f_hz):
    a = AngularFrequency.from_hz(f_hz)
    assert math.isclose(a.f_hz, f_hz, rel_tol=1e-9)


@given(st.integers(min_value=0, max_value=6))
def test_frame_roundtrip(k):
    # rotation about z by k*30deg, then inverse, returns the point
    ang = math.radians(30 * k)
    rot = np.array([[math.cos(ang), -math.sin(ang), 0],
                    [math.sin(ang), math.cos(ang), 0], [0, 0, 1]])
    frame = OrientationFrame(rot, 1, "rz")
    p = SpatialCoordinate((1.0, 2.0, 3.0))
    fwd = ops.frame_transform(p, frame)
    back = ops.frame_transform(fwd, frame.inverse())
    assert np.allclose(back.vector, p.vector, atol=1e-9)


@given(st.lists(finite, min_size=2, max_size=2))
def test_parity_self_inverse(vals):
    s = ModalState(np.array([complex(vals[0]), complex(vals[1])]))
    back = ops.from_parity_basis(ops.to_parity_basis(s))
    assert np.allclose(back.amplitudes, s.amplitudes, atol=1e-9)


@given(st.integers(1, 5))
@settings(max_examples=25)
def test_cascade_associative(n):
    rng = np.random.default_rng(n)
    mats = [rng.standard_normal((2, 2)) + 1j * rng.standard_normal((2, 2))
            for _ in range(3)]
    # (T3 T2) T1 == T3 (T2 T1) -- cascade builds the full ordered product
    left = mats[2] @ (mats[1] @ mats[0])
    right = (mats[2] @ mats[1]) @ mats[0]
    got = ops.cascade(mats)
    assert np.allclose(got, left) and np.allclose(left, right)


@given(st.floats(min_value=0.0, max_value=0.9),
       st.floats(min_value=0.0, max_value=0.9))
def test_uncertainty_monotonic(a, b):
    # adding a term in quadrature never decreases the combined uncertainty
    combined = ops.combine_relative(a, b)
    assert combined >= max(a, b) - 1e-12


@given(st.sampled_from(["EST", "DER", "HYP", "SRC", "ENG"]))
def test_provenance_preserved_through_same_class(cls):
    # propagating a single tag at its own class keeps class and extends path
    t = ProvenanceTag("EP-01-01", cls, ("start",))
    out = ops.propagate_provenance("op", cls, t)
    assert out.claim_class == cls
    assert out.path[0] == "start" and out.path[-1] == "op:op"


@given(pos, pos, st.floats(min_value=0.0, max_value=50.0))
def test_two_mode_splitting_is_2g_at_degeneracy(f, _f2, g):
    # degenerate pair: splitting must equal 2g exactly (within tol)
    r = ops.couple_modes([f, f], [[0.0, g], [g, 0.0]])
    assert math.isclose(r["splitting_hz"], 2 * g, rel_tol=1e-9, abs_tol=1e-9)
