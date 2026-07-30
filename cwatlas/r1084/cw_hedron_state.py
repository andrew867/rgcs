"""Typed recursive decode state (R10.8.4 §2).

Source-face IDs and physical mesh-array indices are distinct types; a
``SurfaceTriangleState`` is exact (Fraction chart coordinates in the parent
face), so containment ``T_{j+1} subset T_j`` and ``I_{j+1} subset I_j`` are
provable identities, not float comparisons.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction


@dataclass(frozen=True)
class SourceFaceID:
    """A face label as used by the source lane / a codebook (0..19)."""

    value: int

    def __post_init__(self):
        if not 0 <= self.value <= 19:
            raise ValueError(f"source face id out of range: {self.value}")


@dataclass(frozen=True)
class PhysicalMeshFaceID:
    """A mesh-array face index of the canonical icosahedron (0..19).

    Never interchangeable with :class:`SourceFaceID`; conversion happens only
    through an explicit codebook permutation.
    """

    value: int

    def __post_init__(self):
        if not 0 <= self.value <= 19:
            raise ValueError(f"mesh face id out of range: {self.value}")


@dataclass(frozen=True)
class SurfaceTriangleState:
    """Current spherical-triangle surface cell, exact in the parent chart.

    ``corners`` are three (u, v) Fractions in the chart
    ``P(u, v) = A + u (B - A) + v (C - A)`` of the ordered physical face
    ``(A, B, C)``. ``orientation`` is +1 (same as face) or -1 (folded /
    DOWN child). ``depth`` counts applied surface refinements.
    """

    corners: tuple[tuple[Fraction, Fraction], ...]
    orientation: int
    depth: int

    def contains(self, u: Fraction, v: Fraction) -> bool:
        """Exact point-in-triangle by rational sign tests (edges included)."""
        (u0, v0), (u1, v1), (u2, v2) = self.corners
        d = (u1 - u0) * (v2 - v0) - (u2 - u0) * (v1 - v0)
        a = ((u - u0) * (v2 - v0) - (u2 - u0) * (v - v0)) / d
        b = ((u1 - u0) * (v - v0) - (u - u0) * (v1 - v0)) / d
        return a >= 0 and b >= 0 and a + b <= 1

    def contains_triangle(self, child: "SurfaceTriangleState") -> bool:
        return all(self.contains(u, v) for u, v in child.corners)


@dataclass(frozen=True)
class RadialInterval:
    """Exact half-open radial interval [r_min, r_max) in km."""

    r_min: Fraction
    r_max: Fraction

    def __post_init__(self):
        if not self.r_min < self.r_max:
            raise ValueError("empty radial interval")

    def contains_interval(self, child: "RadialInterval") -> bool:
        return self.r_min <= child.r_min and child.r_max <= self.r_max

    def contains_radius(self, r_km) -> bool:
        return self.r_min <= Fraction(r_km).limit_denominator(10**9) \
            < self.r_max

    @property
    def thickness(self) -> Fraction:
        return self.r_max - self.r_min

    @property
    def midpoint(self) -> Fraction:
        return (self.r_min + self.r_max) / 2


@dataclass(frozen=True)
class RadialShellState:
    """Radial state at one level: interval + declared root profile id."""

    interval: RadialInterval
    root_profile: str
    depth: int


@dataclass(frozen=True)
class EarthFrameState:
    """The locked frame context a decode ran under."""

    family: str
    codebook: str
    source_face: SourceFaceID
    mesh_face: PhysicalMeshFaceID
    vertex_order: tuple[int, int, int]
    profile_id: str = "EARTH_ROOT_D_V1"


@dataclass(frozen=True)
class UncertaintyCertificate:
    """Explicit three-dimensional uncertainty of a decoded region."""

    surface_max_radius_km: float
    radial_thickness_km: float
    effective_3d_scale_km: float
    axis_depths: tuple[int, int, int]
    partial_level_axes: tuple[str, ...]


@dataclass(frozen=True)
class DecodedRegion:
    """Final decoded cell: spherical polygon + radial interval (a region,
    never a bare point)."""

    surface: SurfaceTriangleState
    radial: RadialShellState
    polygon_latlon: tuple[tuple[float, float], ...]
    uncertainty: UncertaintyCertificate


@dataclass(frozen=True)
class DecodedPointCandidate:
    """Labelled representative only — the centroid of a region. Carrying
    this type is an admission of coarseness, not a location claim."""

    lat_deg: float
    lon_deg: float
    height_km_interval: tuple[float, float]
    label: str = "REPRESENTATIVE_CENTROID_NOT_A_MEASURED_POINT"


@dataclass
class RecursiveDecodeTrace:
    """Complete per-level record of one decode."""

    raw: str
    frame: EarthFrameState
    compensation: str
    levels: list = field(default_factory=list)      # per-level dict records
    region: DecodedRegion | None = None
    representative: DecodedPointCandidate | None = None
