"""P06 — root frames and roll identifiability."""

from __future__ import annotations

import numpy as np
import pytest

from r10 import rootframe as RF


def _root(sec=(0, 1, 0), hand="RIGHT"):
    return RF.RootFrame("r", "EARTH_MOON", "Earth", None, "2026-07-22Z",
                        (1, 0, 0), sec, hand, (0, 0, 0), 1.0,
                        "CALCULATED", "OMEGA_REGION_SOURCE", "MATH")


def test_a_single_direction_root_is_underdetermined():
    with pytest.raises(RF.RootUnderdetermined):
        RF.RootFrame("bad", "SOLAR", "Sun", None, "2026", (1, 0, 0),
                     None, "RIGHT", (0, 0, 0), 1.0, "CALCULATED", "x", "y")


def test_parallel_directions_leave_roll_unfixed():
    with pytest.raises(RF.RootUnderdetermined):
        RF.orientation_from_two_directions((1, 0, 0), (2, 0, 0))


def test_two_directions_determine_an_orthonormal_frame():
    R = _root().orientation()
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-9)
    assert np.isclose(np.linalg.det(R), 1.0)


def test_quaternion_round_trips_the_matrix():
    r = _root((0.3, 1, 0.2))
    q = r.quaternion()
    assert np.isclose(np.linalg.norm(q), 1.0)
    assert np.allclose(RF.quaternion_to_matrix(q), r.orientation(),
                       atol=1e-9)


def test_left_handedness_flips_determinant():
    assert np.isclose(np.linalg.det(_root(hand="RIGHT").orientation()), 1.0)
    assert np.isclose(np.linalg.det(_root(hand="LEFT").orientation()), -1.0)


def test_bad_root_fields_are_refused():
    with pytest.raises(RF.RootError):
        RF.RootFrame("r", "S", "b", None, "", (1, 0, 0), (0, 1, 0),
                     "RIGHT", (0, 0, 0), 1.0, "C", "x", "y")   # no epoch
    with pytest.raises(RF.RootError):
        _root(hand="SIDEWAYS")


def test_single_direction_refusal_names_calibration_vs_frame():
    with pytest.raises(RF.RootUnderdetermined) as e:
        RF.refuse_single_direction_root("solar")
    assert "Latitude and longitude are calibration" in str(e.value)


def test_report_states_the_rule():
    r = RF.rootframe_report()
    assert r["single_direction_verdict"] == "ROOT_UNDERDETERMINED"
    assert r["measured_here"] == "nothing"
