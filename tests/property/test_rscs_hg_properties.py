"""Property tests for the HG memory bridge: replay fidelity, transform
consistency, and temporal ordering. These are the machine forms of the
falsifiable software claims H-16 (transform consistency) and H-18
(localization / replay fidelity)."""
from __future__ import annotations

import math

import numpy as np
from hypothesis import given, settings
from hypothesis import strategies as st

from rscs_core.coordinates import (SpatialCoordinate, OrientationFrame,
                                   TimeCoordinate, ModalState)
from rscs_core.memory import hg_store, hg_replay


def _rot_z(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0],
                     [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def _record(deg, ego_xyz):
    frame = OrientationFrame(_rot_z(deg), 1, "world")
    ego = SpatialCoordinate(tuple(float(v) for v in ego_xyz), "ego")
    allo = SpatialCoordinate(tuple(float(v) for v in frame.rotation @ ego.vector),
                             "world")
    return hg_store(allo, ego, frame, TimeCoordinate(0.0),
                    ModalState.from_components([1 + 0j]))


coord = st.floats(min_value=-100, max_value=100, allow_nan=False,
                  allow_infinity=False)
angle = st.integers(min_value=0, max_value=350)


@given(angle, st.tuples(coord, coord, coord))
def test_replay_fidelity(deg, ego_xyz):
    # H-18: replaying into the original frame reproduces the egocentric
    # position; the allocentric anchor is always invariant.
    rec = _record(deg, ego_xyz)
    same = hg_replay(rec, rec.frame)
    assert np.allclose(same.egocentric.vector, rec.egocentric.vector, atol=1e-9)
    assert np.allclose(same.allocentric.vector, rec.allocentric.vector,
                       atol=1e-9)


@given(angle, angle, st.tuples(coord, coord, coord))
@settings(max_examples=50)
def test_transform_consistency(deg1, deg2, ego_xyz):
    # H-16: after replay into ANY query frame, the record stays frame-
    # consistent (allocentric == frame . egocentric) and the allocentric
    # anchor never moves.
    rec = _record(deg1, ego_xyz)
    q = OrientationFrame(_rot_z(deg2), 1, "query")
    rp = hg_replay(rec, q)
    assert rp.frame_consistent(atol_mm=1e-6)
    assert np.allclose(rp.allocentric.vector, rec.allocentric.vector, atol=1e-9)


@given(angle, st.tuples(coord, coord, coord))
def test_replay_roundtrip_returns_home(deg, ego_xyz):
    # Replay into a different frame then back into the original recovers the
    # original egocentric position (transform invertibility).
    rec = _record(deg, ego_xyz)
    other = OrientationFrame(_rot_z((deg + 137) % 360), 1, "other")
    back = hg_replay(hg_replay(rec, other), rec.frame)
    assert np.allclose(back.egocentric.vector, rec.egocentric.vector, atol=1e-9)
