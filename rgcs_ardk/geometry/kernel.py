"""Deterministic geometry kernel shared by PCB and fixture generators."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import math
from typing import Iterable

from rgcs_ardk.params import LOCKS, LockedParameters


@dataclass(frozen=True)
class Point2D:
    x_mm: float
    y_mm: float


@dataclass(frozen=True)
class CircleFeature:
    feature_id: str
    center: Point2D
    diameter_mm: float


@dataclass(frozen=True)
class SectorPolygon:
    index: int
    center_angle_deg: float
    points: tuple[Point2D, ...]


def _rounded(value: float) -> float:
    value = round(value, 6)
    return 0.0 if value == -0.0 else value


def _polar(radius_mm: float, angle_deg: float) -> Point2D:
    angle = math.radians(angle_deg)
    return Point2D(
        _rounded(radius_mm * math.cos(angle)),
        _rounded(radius_mm * math.sin(angle)),
    )


@dataclass(frozen=True)
class AnnularGeometry:
    params: LockedParameters = LOCKS
    mounting_radius_mm: float = 136.0
    mounting_hole_diameter_mm: float = 3.2
    board_compass_radius_mm: float = 136.0

    @property
    def pitch_deg_exact(self) -> Fraction:
        return Fraction(360, self.params.sector_count)

    @property
    def pitch_deg(self) -> float:
        return float(self.pitch_deg_exact)

    def sector_angle_deg(self, index: int) -> float:
        self._check_index(index)
        return float(index * self.pitch_deg_exact)

    def sector_center(self, index: int, radius_mm: float | None = None) -> Point2D:
        return _polar(
            self.params.mean_radius_mm if radius_mm is None else radius_mm,
            self.sector_angle_deg(index),
        )

    def sector_polygon(
        self,
        index: int,
        inner_radius_mm: float,
        outer_radius_mm: float,
        *,
        angular_gap_deg: float = 0.35,
        arc_segments: int = 4,
    ) -> SectorPolygon:
        self._check_index(index)
        if not self.params.inner_radius_mm <= inner_radius_mm < outer_radius_mm <= self.params.outer_radius_mm:
            raise ValueError("sector radii must lie inside the annular board")
        if arc_segments < 1:
            raise ValueError("arc_segments must be positive")
        half_span = (self.pitch_deg - angular_gap_deg) / 2.0
        if half_span <= 0:
            raise ValueError("angular gap consumes the sector")
        center = self.sector_angle_deg(index)
        angles = [
            center - half_span + 2.0 * half_span * i / arc_segments
            for i in range(arc_segments + 1)
        ]
        outer = [_polar(outer_radius_mm, angle) for angle in angles]
        inner = [_polar(inner_radius_mm, angle) for angle in reversed(angles)]
        return SectorPolygon(index, center, tuple(outer + inner))

    def sector_ring(
        self,
        inner_radius_mm: float,
        outer_radius_mm: float,
        **kwargs: float | int,
    ) -> tuple[SectorPolygon, ...]:
        return tuple(
            self.sector_polygon(i, inner_radius_mm, outer_radius_mm, **kwargs)
            for i in range(self.params.sector_count)
        )

    def mounting_holes(self) -> tuple[CircleFeature, ...]:
        return tuple(
            CircleFeature(
                f"MOUNT_{i}",
                _polar(self.mounting_radius_mm, 45.0 + i * 90.0),
                self.mounting_hole_diameter_mm,
            )
            for i in range(4)
        )

    def sector_pickups(self) -> tuple[Point2D, ...]:
        return tuple(self.sector_center(i) for i in range(self.params.sector_count))

    def compass_pickups(self) -> tuple[Point2D, ...]:
        return tuple(_polar(self.board_compass_radius_mm, i * 45.0) for i in range(8))

    def fiducials(self) -> tuple[CircleFeature, ...]:
        indices: Iterable[int] = range(0, self.params.sector_count, 5)
        return tuple(
            CircleFeature(
                f"FID_{index:02d}",
                self.sector_center(index, 140.0),
                1.0,
            )
            for index in indices
        )

    def as_dict(self) -> dict:
        return {
            "sector_count": self.params.sector_count,
            "sector_pitch_deg_exact": "360/37",
            "sector_pitch_deg": self.pitch_deg,
            "outer_diameter_mm": self.params.outer_diameter_mm,
            "inner_diameter_mm": self.params.inner_diameter_mm,
            "inner_outer_ratio_exact": "47/72",
            "mechanical_rotation": False,
            "mounting_holes": [asdict(hole) for hole in self.mounting_holes()],
            "fiducials": [asdict(fiducial) for fiducial in self.fiducials()],
        }

    def _check_index(self, index: int) -> None:
        if not 0 <= index < self.params.sector_count:
            raise ValueError("sector index out of range")
