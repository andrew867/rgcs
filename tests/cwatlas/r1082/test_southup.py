"""P07 — South-Up basis and viewpoint-safe handedness."""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas.r1082 import southup
from cwatlas.r1082.southup import Sense, Viewpoint


# -- focused: handedness consistent across viewpoints -----------------------

def test_same_rotation_from_both_viewpoints_is_identical():
    # The locked equivalence: clockwise from Antarctic == anticlockwise from
    # North-down. The physical matrix must be the same.
    a = southup.rotation_matrix(30.0, Sense.CLOCKWISE,
                                Viewpoint.ANTARCTIC_EXTERNAL)
    b = southup.rotation_matrix(30.0, Sense.ANTICLOCKWISE,
                                Viewpoint.NORTH_DOWN)
    assert np.allclose(a, b)


def test_opposite_senses_from_same_viewpoint_differ():
    cw = southup.rotation_matrix(30.0, Sense.CLOCKWISE,
                                 Viewpoint.ANTARCTIC_EXTERNAL)
    ccw = southup.rotation_matrix(30.0, Sense.ANTICLOCKWISE,
                                  Viewpoint.ANTARCTIC_EXTERNAL)
    assert not np.allclose(cw, ccw)
    # They are inverses of each other (opposite sign rotation).
    assert np.allclose(cw @ ccw, np.eye(3))


def test_positive_rotation_is_clockwise_from_antarctic_anticlockwise_from_north():
    assert southup.describe_sense(30.0, Viewpoint.ANTARCTIC_EXTERNAL) is Sense.CLOCKWISE
    assert southup.describe_sense(30.0, Viewpoint.NORTH_DOWN) is Sense.ANTICLOCKWISE
    # The two views always disagree on the label — that is the point.
    for angle in (-45.0, -1.0, 5.0, 90.0):
        s_ant = southup.describe_sense(angle, Viewpoint.ANTARCTIC_EXTERNAL)
        s_nor = southup.describe_sense(angle, Viewpoint.NORTH_DOWN)
        assert s_ant is not s_nor


def test_rotation_matrices_are_proper_rotations():
    m = southup.rotation_matrix(42.0, Sense.CLOCKWISE,
                                Viewpoint.ANTARCTIC_EXTERNAL)
    assert np.allclose(m.T @ m, np.eye(3))
    assert np.isclose(np.linalg.det(m), 1.0)


# -- negative: rotation without a declared viewpoint is refused -------------

def test_rotation_without_viewpoint_refused():
    with pytest.raises(southup.SouthUpError):
        southup.rotation_matrix(30.0, Sense.CLOCKWISE, None)


def test_describe_without_viewpoint_refused():
    with pytest.raises(southup.SouthUpError):
        southup.describe_sense(30.0, None)


def test_refuse_helper_raises():
    with pytest.raises(southup.SouthUpError):
        southup.refuse_rotation_without_viewpoint()


# -- tangent basis: determinant and orthogonality ---------------------------

def test_tangent_basis_is_orthonormal_right_handed():
    b = southup.tangent_basis(-66.5, 135.0)  # Wilkes centroid
    assert b.is_orthonormal()
    assert np.isclose(b.determinant(), 1.0)


def test_tangent_basis_at_saa_is_orthonormal():
    b = southup.tangent_basis(-25.0, -50.0)  # SAA minimum
    assert b.is_orthonormal()
    assert np.isclose(b.determinant(), 1.0)


def test_south_up_basis_is_proper_rotation_flipping_the_pole():
    m = southup.south_up_basis()
    assert np.isclose(np.linalg.det(m), 1.0)
    # North (+Z) maps to -Z ("south is up").
    assert np.allclose(m @ np.array([0.0, 0.0, 1.0]), np.array([0.0, 0.0, -1.0]))


# -- golden numeric values --------------------------------------------------

def test_golden_90deg_clockwise_from_antarctic():
    m = southup.rotation_matrix(90.0, Sense.CLOCKWISE,
                                Viewpoint.ANTARCTIC_EXTERNAL)
    # Rz(+90): +X -> +Y.
    assert np.allclose(m @ np.array([1.0, 0.0, 0.0]),
                       np.array([0.0, 1.0, 0.0]), atol=1e-12)


# -- determinism ------------------------------------------------------------

def test_rotation_is_deterministic():
    a = southup.rotation_matrix(12.5, Sense.CLOCKWISE, Viewpoint.ANTARCTIC_EXTERNAL)
    b = southup.rotation_matrix(12.5, Sense.CLOCKWISE, Viewpoint.ANTARCTIC_EXTERNAL)
    assert np.array_equal(a, b)


# -- report -----------------------------------------------------------------

def test_report_seals_orientation_and_no_measurement():
    r = southup.southup_report()
    assert r["pole"] == "SOUTH_UP"
    assert r["positive_rotation"] == "CLOCKWISE"
    assert r["rotation_without_viewpoint"] == "REFUSED"
    assert r["measured_here"] == "nothing"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert np.isclose(r["south_up_basis_determinant"], 1.0)
