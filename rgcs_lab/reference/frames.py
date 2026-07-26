"""Quaternion frame reference — unit quaternions, ordered composition."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Quat:
    w: float
    x: float
    y: float
    z: float

    def norm(self) -> float:
        return math.sqrt(self.w * self.w + self.x * self.x
                         + self.y * self.y + self.z * self.z)

    def normalized(self) -> "Quat":
        n = self.norm()
        if n == 0:
            raise ValueError("zero quaternion cannot be normalized")
        return Quat(self.w / n, self.x / n, self.y / n, self.z / n)

    def conjugate(self) -> "Quat":
        return Quat(self.w, -self.x, -self.y, -self.z)

    def inverse(self) -> "Quat":
        n2 = self.w * self.w + self.x * self.x + self.y * self.y + self.z * self.z
        if n2 == 0:
            raise ValueError("zero quaternion has no inverse")
        c = self.conjugate()
        return Quat(c.w / n2, c.x / n2, c.y / n2, c.z / n2)

    def mul(self, other: "Quat") -> "Quat":
        # Hamilton product; composition applies `other` first when used as q_total = a*b*...
        a, b = self, other
        return Quat(
            a.w * b.w - a.x * b.x - a.y * b.y - a.z * b.z,
            a.w * b.x + a.x * b.w + a.y * b.z - a.z * b.y,
            a.w * b.y - a.x * b.z + a.y * b.w + a.z * b.x,
            a.w * b.z + a.x * b.y - a.y * b.x + a.z * b.w,
        )

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.w, self.x, self.y, self.z)

    def matrix(self) -> list[list[float]]:
        w, x, y, z = self.normalized().as_tuple()
        return [
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ]


def from_axis_angle(axis: tuple[float, float, float], angle_rad: float) -> Quat:
    x, y, z = axis
    n = math.sqrt(x * x + y * y + z * z)
    if n == 0:
        raise ValueError("axis must be non-zero")
    x, y, z = x / n, y / n, z / n
    s = math.sin(angle_rad / 2.0)
    return Quat(math.cos(angle_rad / 2.0), x * s, y * s, z * s).normalized()


def rotate_vector(q: Quat, v: tuple[float, float, float]) -> tuple[float, float, float]:
    qv = Quat(0.0, v[0], v[1], v[2])
    r = q.mul(qv).mul(q.inverse())
    return (r.x, r.y, r.z)


EARTH_SOUTH_UP = {
    "from_frame": "earth-enu-candidate",
    "to_frame": "earth-south-up-candidate",
    "steps": [
        ("q_conventional_body", from_axis_angle((0, 0, 1), 0.0)),
        ("q_south_up", from_axis_angle((1, 0, 0), math.pi)),
        ("q_fixed_anchor", from_axis_angle((0, 1, 0), 0.0)),
        ("q_epoch_phase", from_axis_angle((0, 0, 1), 0.0)),
        ("q_ground", from_axis_angle((0, 0, 1), 0.0)),
        ("q_source_face_to_mesh", from_axis_angle((0, 1, 0), 0.0)),
        ("q_local", from_axis_angle((0, 0, 1), 0.0)),
    ],
    "composition_order": "q_total = q_conventional_body * ... * q_local (rightmost applied first)",
}


def compose_named(example: str = "earth-south-up") -> dict:
    if example != "earth-south-up":
        raise ValueError(f"unknown frame example: {example}")
    steps = EARTH_SOUTH_UP["steps"]
    total = Quat(1, 0, 0, 0)
    # Apply rightmost first: multiply from the right.
    for _name, q in reversed(steps):
        total = total.mul(q)
    total = total.normalized()
    inv = total.inverse().normalized()
    basis = {
        "e1": rotate_vector(total, (1, 0, 0)),
        "e2": rotate_vector(total, (0, 1, 0)),
        "e3": rotate_vector(total, (0, 0, 1)),
    }
    round_trip = {
        "e1": rotate_vector(inv, basis["e1"]),
        "e2": rotate_vector(inv, basis["e2"]),
        "e3": rotate_vector(inv, basis["e3"]),
    }
    axis, angle = _to_axis_angle(total)
    return {
        "example": example,
        "from_frame": EARTH_SOUTH_UP["from_frame"],
        "to_frame": EARTH_SOUTH_UP["to_frame"],
        "composition_order": EARTH_SOUTH_UP["composition_order"],
        "quaternion": list(total.as_tuple()),
        "inverse": list(inv.as_tuple()),
        "axis": list(axis),
        "angle_rad": angle,
        "matrix": total.matrix(),
        "normalization_error": abs(total.norm() - 1.0),
        "basis_out": basis,
        "round_trip_basis": round_trip,
        "sign_alias_equivalent": True,
    }


def _to_axis_angle(q: Quat) -> tuple[tuple[float, float, float], float]:
    q = q.normalized()
    w = max(-1.0, min(1.0, q.w))
    angle = 2.0 * math.acos(w)
    s = math.sqrt(max(0.0, 1.0 - w * w))
    if s < 1e-12:
        return (1.0, 0.0, 0.0), angle
    return (q.x / s, q.y / s, q.z / s), angle
