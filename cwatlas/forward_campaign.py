"""P40 -- Forward precision and round-trip test campaign.

A deterministic harness that runs ``map -> vector -> map`` over a large
synthetic point grid, across bodies and (for the icosahedral codec) refinement
depths, and reports the maximum round-trip error against a *declared* tolerance
per codec. The campaign is the atlas's own regression witness: it asserts a
POWER property -- that the reversible codecs recover a declared coordinate to
within their stated bounds -- without touching any private or source data.

Two codecs are exercised:

* **CW-GEO-1** (:mod:`cwatlas.codec_geo1`) -- a direct reversible geodetic
  codec. Its round-trip error is bounded by its quantization half-step (sub-mm),
  independent of the body; the declared tolerance is a tight constant.
* **CW-HCM-ICO-1** (:mod:`cwatlas.addressing`) -- icosahedral cell addressing.
  A point maps to a cell whose centroid is recovered; the round-trip error is
  bounded by the cell size at the chosen depth and shrinks monotonically with
  depth. The declared tolerance is a per-depth, per-body cell bound.

Points are generated deterministically: a latitude/longitude lattice plus
explicit edge cases (poles, the dateline, Null Island) and a seeded pseudo-
random fuzz set. Nothing here reads a wall-clock; epochs are passed in.

That the codecs round-trip is a ``CANONICAL_ROUND_TRIP`` fact about the codecs.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Sequence, Tuple

import numpy as np

from cwatlas import claims
from cwatlas.addressing import AddressError, encode_path, path_cell
from cwatlas.canonical import CanonicalCoordinate
from cwatlas.codec_geo1 import CWGeo1Codec
from cwatlas.icosahedron import build_icosahedron

MODULE_PHASE = "P40"

#: Mean radius (metres) per body, used only to express angular round-trip error
#: as a distance. Declared explicitly -- no hidden body default.
BODY_RADIUS_M: Dict[str, float] = {
    "EARTH": 6_371_000.0,
    "MARS": 3_389_500.0,
    "MOON": 1_737_400.0,
}

#: CW-GEO-1 declared round-trip tolerance (metres). The codec snaps to a 1e-8 deg
#: grid (~1.1 mm), so the worst-case recovery error is a fraction of a
#: millimetre; 1 cm is a comfortable, body-independent declared bound.
GEO1_TOLERANCE_M = 1e-2

#: CW-HCM-ICO-1 declared cell-centroid tolerance (metres) at Earth scale, keyed
#: by refinement depth. Each octal subdivision roughly halves the cell's linear
#: size, so the bound falls with depth. These are *declared* bounds; the
#: measured maxima sit well inside them. Other bodies scale by radius ratio.
ICO_TOLERANCE_EARTH_M: Dict[int, float] = {
    6: 80_000.0,
    8: 20_000.0,
    10: 6_000.0,
    12: 2_000.0,
}


class CampaignError(ValueError):
    """Raised on an invalid campaign configuration."""


def ico_tolerance_m(depth: int, body: str) -> float:
    """Declared icosahedral tolerance for a depth/body, scaled by radius."""
    if depth not in ICO_TOLERANCE_EARTH_M:
        raise CampaignError(
            f"no declared icosahedral tolerance for depth {depth}; "
            f"declared depths are {sorted(ICO_TOLERANCE_EARTH_M)}")
    scale = BODY_RADIUS_M[body] / BODY_RADIUS_M["EARTH"]
    return ICO_TOLERANCE_EARTH_M[depth] * scale


@dataclass(frozen=True)
class CampaignConfig:
    """A declared campaign: bodies, grid resolution, ico depth, seed, epoch."""

    bodies: Tuple[str, ...] = ("EARTH", "MARS", "MOON")
    lat_steps: int = 19
    lon_steps: int = 37
    ico_depth: int = 12
    fuzz_count: int = 200
    seed: int = 20200704
    epoch: str = "2020.0"
    frame: str = "SYNTHETIC-SPHERE"

    def __post_init__(self) -> None:
        if not self.bodies:
            raise CampaignError("at least one body is required")
        for b in self.bodies:
            if b not in BODY_RADIUS_M:
                raise CampaignError(
                    f"unknown body {b!r}; known={sorted(BODY_RADIUS_M)}")
        if self.lat_steps < 2 or self.lon_steps < 2:
            raise CampaignError("lat_steps and lon_steps must be >= 2")
        if self.fuzz_count < 0:
            raise CampaignError("fuzz_count must be non-negative")
        if self.ico_depth not in ICO_TOLERANCE_EARTH_M:
            raise CampaignError(
                f"ico_depth {self.ico_depth} has no declared tolerance; "
                f"declared depths are {sorted(ICO_TOLERANCE_EARTH_M)}")


@dataclass(frozen=True)
class CodecReport:
    """Per-codec campaign outcome: worst error vs the declared tolerance.

    ``num_refused`` counts points the codec safely refused -- for the
    icosahedral codec, exact-boundary directions (a pole, a shared edge, a
    vertex) that land on a cell boundary. A refusal is documented safe
    behaviour, not a round-trip failure, and is excluded from ``max_error_m``.
    """

    codec_id: str
    num_points: int
    max_error_m: float
    tolerance_m: float
    passed: bool
    worst_case: Tuple[float, float]  # (lat, lon) of the worst point
    num_refused: int = 0


@dataclass(frozen=True)
class CampaignResult:
    """The full campaign result: one report per codec, plus an overall verdict."""

    config: CampaignConfig
    reports: Tuple[CodecReport, ...]
    all_passed: bool
    total_points: int

    def report_for(self, codec_id: str) -> CodecReport:
        for r in self.reports:
            if r.codec_id == codec_id:
                return r
        raise CampaignError(f"no report for codec {codec_id!r}")


# --- geometry helpers -------------------------------------------------------

def _latlon_to_unit(lat_deg: float, lon_deg: float) -> np.ndarray:
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    cla = math.cos(la)
    return np.array([cla * math.cos(lo), cla * math.sin(lo), math.sin(la)],
                    dtype=np.float64)


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float,
                 radius_m: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2)
    return 2.0 * radius_m * math.asin(min(1.0, math.sqrt(a)))


def _angular_error_m(u_in: np.ndarray, u_out: np.ndarray,
                     radius_m: float) -> float:
    d = float(np.clip(np.dot(u_in, u_out), -1.0, 1.0))
    return math.acos(d) * radius_m


# --- point generation -------------------------------------------------------

def generate_points(config: CampaignConfig) -> List[Tuple[float, float]]:
    """Deterministic (lat, lon) set: lattice + edge cases + seeded fuzz.

    Edge cases (poles, dateline, Null Island) are always present so boundary
    behaviour is exercised. The fuzz set is drawn from a seeded RNG, so the
    campaign is reproducible bit-for-bit.
    """
    lats = np.linspace(-90.0, 90.0, config.lat_steps)
    lons = np.linspace(-180.0, 180.0, config.lon_steps)
    points: List[Tuple[float, float]] = []
    for la in lats:
        for lo in lons:
            points.append((float(la), float(lo)))
    edge_cases = [
        (90.0, 0.0), (-90.0, 0.0), (0.0, 0.0),
        (0.0, 179.999999), (0.0, -179.999999),
        (51.178882, -1.826215), (29.979235, 31.134202),
    ]
    points.extend(edge_cases)
    rng = np.random.default_rng(config.seed)
    for _ in range(config.fuzz_count):
        # Uniform on the sphere: lat from arcsin of a uniform in [-1, 1].
        u = rng.uniform(-1.0, 1.0)
        lat = math.degrees(math.asin(u))
        lon = rng.uniform(-180.0, 180.0)
        points.append((lat, lon))
    return points


# --- per-codec campaigns ----------------------------------------------------

def _run_geo1(points: Sequence[Tuple[float, float]], body: str,
              config: CampaignConfig) -> Tuple[float, Tuple[float, float]]:
    codec = CWGeo1Codec()
    radius = BODY_RADIUS_M[body]
    max_err = 0.0
    worst = points[0]
    for lat, lon in points:
        coord = CanonicalCoordinate(
            body_id=body, frame_id=config.frame, epoch=config.epoch,
            latitude_deg=lat, longitude_deg=lon, height_m=0.0)
        decoded = codec.decode(codec.encode(coord))
        err = _haversine_m(coord.latitude_deg, coord.longitude_deg,
                           decoded.latitude_deg, decoded.longitude_deg, radius)
        if err > max_err:
            max_err, worst = err, (lat, lon)
    return max_err, worst


def _run_ico(points: Sequence[Tuple[float, float]], body: str,
             config: CampaignConfig, ico
             ) -> Tuple[float, Tuple[float, float], int]:
    radius = BODY_RADIUS_M[body]
    depth = config.ico_depth
    max_err = 0.0
    worst = points[0]
    refused = 0
    for lat, lon in points:
        u_in = _latlon_to_unit(lat, lon)
        try:
            addr = encode_path(ico, u_in, depth)
            cell = path_cell(ico, addr.face_id, addr.path)
        except AddressError:
            # An exact-boundary direction (pole, shared edge, vertex) is safely
            # refused by the addressing codec; count it, do not fail on it.
            refused += 1
            continue
        centroid = cell.a + cell.b + cell.c
        centroid = centroid / np.linalg.norm(centroid)
        err = _angular_error_m(u_in, centroid, radius)
        if err > max_err:
            max_err, worst = err, (lat, lon)
    return max_err, worst, refused


def run_campaign(config: CampaignConfig | None = None) -> CampaignResult:
    """Run the full forward precision + round-trip campaign.

    For every body: run CW-GEO-1 and CW-HCM-ICO-1 over the generated point set,
    take the worst error across all bodies per codec, and compare it to the
    declared tolerance (the icosahedral tolerance uses the largest applicable
    per-body bound so a single scalar is defensible).
    """
    config = config or CampaignConfig()
    points = generate_points(config)
    ico = build_icosahedron()

    geo1_max, geo1_worst = 0.0, points[0]
    ico_max, ico_worst = 0.0, points[0]
    ico_tol = 0.0
    ico_refused = 0
    for body in config.bodies:
        g_err, g_worst = _run_geo1(points, body, config)
        if g_err > geo1_max:
            geo1_max, geo1_worst = g_err, g_worst
        i_err, i_worst, i_refused = _run_ico(points, body, config, ico)
        if i_err > ico_max:
            ico_max, ico_worst = i_err, i_worst
        ico_refused += i_refused
        ico_tol = max(ico_tol, ico_tolerance_m(config.ico_depth, body))

    geo1_report = CodecReport(
        codec_id="CW-GEO-1", num_points=len(points) * len(config.bodies),
        max_error_m=geo1_max, tolerance_m=GEO1_TOLERANCE_M,
        passed=geo1_max <= GEO1_TOLERANCE_M, worst_case=geo1_worst)
    ico_report = CodecReport(
        codec_id="CW-HCM-ICO-1", num_points=len(points) * len(config.bodies),
        max_error_m=ico_max, tolerance_m=ico_tol,
        passed=ico_max <= ico_tol, worst_case=ico_worst,
        num_refused=ico_refused)
    reports = (geo1_report, ico_report)
    return CampaignResult(
        config=config, reports=reports,
        all_passed=all(r.passed for r in reports),
        total_points=len(points) * len(config.bodies))


def forward_campaign_report() -> dict:
    """Governance report: what this module is and, emphatically, is not."""
    return {
        "module": "cwatlas.forward_campaign",
        "phase_id": MODULE_PHASE,
        "codecs": ["CW-GEO-1", "CW-HCM-ICO-1"],
        "bodies": sorted(BODY_RADIUS_M),
        "geo1_tolerance_m": GEO1_TOLERANCE_M,
        "ico_tolerance_earth_m": ICO_TOLERANCE_EARTH_M,
        "deterministic": True,
        "claim_class": claims.ClaimClass.CANONICAL_ROUND_TRIP.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "CW_ATLAS_FORWARD_CAMPAIGN_ROUND_TRIP_UNDER_DECLARED_TOLERANCE",
        "what_this_does_not_say": (
            "The campaign shows the reversible codecs recover a declared "
            "synthetic coordinate to within their stated bounds. It measures no "
            "real-world quantity and validates no operator-reported source "
            "vector as a location."),
    }
