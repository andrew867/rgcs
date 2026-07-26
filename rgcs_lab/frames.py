"""Normalized quaternion rotations with explicit frame direction."""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .receipts import receipt


@dataclass(frozen=True)
class Quaternion:
    w: float
    x: float
    y: float
    z: float

    def as_array(self) -> np.ndarray:
        return np.array([self.w, self.x, self.y, self.z], dtype=float)

    def norm(self) -> float:
        return float(np.linalg.norm(self.as_array()))

    def normalized(self) -> "Quaternion":
        n = self.norm()
        if n == 0.0:
            raise ValueError("zero quaternion cannot be normalized")
        return Quaternion(*(self.as_array() / n))

    def inverse(self) -> "Quaternion":
        q = self.normalized()
        return Quaternion(q.w, -q.x, -q.y, -q.z)

    def __mul__(self, other: "Quaternion") -> "Quaternion":
        a, b, c, d = self.w, self.x, self.y, self.z
        e, f, g, h = other.w, other.x, other.y, other.z
        return Quaternion(a * e - b * f - c * g - d * h,
                          a * f + b * e + c * h - d * g,
                          a * g - b * h + c * e + d * f,
                          a * h + b * g - c * f + d * e)

    def matrix(self) -> np.ndarray:
        q = self.normalized()
        w, x, y, z = q.w, q.x, q.y, q.z
        return np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ], dtype=float)

    def rotate(self, vector: list[float] | tuple[float, float, float]) -> list[float]:
        return self.matrix().dot(np.asarray(vector, dtype=float)).tolist()


def from_axis_angle(axis: list[float] | tuple[float, float, float],
                    angle_rad: float) -> Quaternion:
    a = np.asarray(axis, dtype=float)
    n = float(np.linalg.norm(a))
    if n == 0.0:
        raise ValueError("axis must be non-zero")
    u = a / n
    half = angle_rad / 2.0
    return Quaternion(math.cos(half), *(math.sin(half) * u)).normalized()


def rotation_receipt(from_frame: str, to_frame: str,
                     axis: list[float], angle_rad: float,
                     vector: list[float] | None = None) -> dict[str, object]:
    q = from_axis_angle(axis, angle_rad)
    inv = q.inverse()
    test_vector = vector or [1.0, 0.0, 0.0]
    rotated = q.rotate(test_vector)
    restored = inv.rotate(rotated)
    result = {
        "from_frame": from_frame,
        "to_frame": to_frame,
        "quaternion": q.as_array().tolist(),
        "axis": axis,
        "angle_rad": angle_rad,
        "angle_degrees": math.degrees(angle_rad),
        "matrix": q.matrix().tolist(),
        "inverse": inv.as_array().tolist(),
        "normalization_error": abs(q.norm() - 1.0),
        "composition_order": "Hamilton product; q_total = q_next * q_previous; active column-vector rotation",
        "input_vector": test_vector,
        "rotated_vector": rotated,
        "round_trip_vector": restored,
        "round_trip_error": float(np.linalg.norm(np.asarray(restored) - np.asarray(test_vector))),
    }
    return receipt(
        "frames", "GREEN", ["EXACT_MATH", "FRAME_ROTATION"],
        {"from_frame": from_frame, "to_frame": to_frame,
         "axis": axis, "angle_rad": angle_rad, "vector": test_vector},
        [{"name": "normalized_hamilton_quaternion", "units": "radians"}],
        result,
        ["tests/rgcs_lab/test_frames.py"],
    )

