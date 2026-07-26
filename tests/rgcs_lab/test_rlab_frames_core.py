import math

import numpy as np

from rgcs_lab.frames import from_axis_angle, rotation_receipt


def test_quaternion_identity_inverse_and_norm():
    q = from_axis_angle([0, 0, 1], math.pi / 2)
    v = [1.0, 0.0, 0.0]
    rotated = q.rotate(v)
    assert np.allclose(rotated, [0.0, 1.0, 0.0], atol=1e-12)
    assert np.allclose(q.inverse().rotate(rotated), v, atol=1e-12)
    assert abs(np.linalg.norm(rotated) - np.linalg.norm(v)) < 1e-12


def test_quaternion_noncommutative_and_receipt_roundtrip():
    qx = from_axis_angle([1, 0, 0], math.pi / 2)
    qy = from_axis_angle([0, 1, 0], math.pi / 2)
    assert not np.allclose((qx * qy).as_array(), (qy * qx).as_array())
    rec = rotation_receipt("a", "b", [0, 0, 1], 2 * math.pi)
    assert rec["result"]["round_trip_error"] < 1e-12
    assert rec["result"]["normalization_error"] < 1e-12

