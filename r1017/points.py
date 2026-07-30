"""R10.17 — the seed point ledger with declared heights.

Heights are APPROXIMATE PUBLIC ELEVATIONS with explicit uncertainty,
not DEM lookups: no offline DEM is available in this environment. Each
value carries its basis so the shell classification can be tested for
robustness against the stated uncertainty rather than presented as
exact.
"""

from __future__ import annotations

from dataclasses import dataclass, field

#: Roles from the ledger.
STRICT = "strict_surface_anchor"
HOLDOUT = "diagnostic_holdout"
MONITOR = "diagnostic_monitor_not_calibration_initially"


@dataclass(frozen=True)
class SeedPoint:
    point_id: str
    name: str
    lat: float
    lon: float
    height_m: float | None
    height_sigma_m: float | None
    height_basis: str
    role: str
    expected_shell: str
    surface_word: int | None = None
    surface_octal10: str | None = None
    phase: str = "A_holdout"
    notes: str = ""
    variants_m: tuple = ()

    @property
    def has_height(self) -> bool:
        return self.height_m is not None


#: Elevations: approximate published values, metres above mean sea
#: level, with generous uncertainty. Sources are general public
#: knowledge of the sites, NOT a DEM query, and are labelled as such.
SEED_POINTS = (
    SeedPoint("STONEHENGE_ANCHOR", "Stonehenge", 51.178816, -1.82628,
              101.0, 10.0, "APPROXIMATE_PUBLIC_ELEVATION",
              STRICT, "S3_surface_shell_candidate",
              165876523, "1170611453", "A_training",
              "training equality, not independent validation"),
    SeedPoint("ERIE_ANCHOR", "Erie PA", 42.114507, -80.076211,
              190.0, 30.0, "APPROXIMATE_PUBLIC_ELEVATION_LAKE_SHORE",
              STRICT, "S3_surface_shell_candidate",
              167849523, "1200227063", "A_training",
              "Lake Erie surface is about 174 m, so the city sits "
              "above it; public association only, no target claims"),
    SeedPoint("TORONTO_ANCHOR", "Toronto corrected", 43.6532,
              -79.383198, 76.0, 15.0,
              "APPROXIMATE_PUBLIC_ELEVATION_LAKE_SHORE", STRICT,
              "S3_surface_shell_candidate",
              168930443, "1204326213", "A_training",
              "North America F5=5 family"),
    SeedPoint("BALTIC_MONITOR_CANDIDATE",
              "Baltic Sea Anomaly working coordinate",
              55.8666667, 18.6, -91.0, 10.0,
              "SOURCE_DOC_DEPTH_CANDIDATE", MONITOR,
              "outer_surface_or_benthic_monitor_candidate",
              None, None, "B_optional_diagnostic",
              "60 m circular feature; depth variants tested",
              (-91.0, -82.0)),
    SeedPoint("NORTH_SEA_EDGE_CANDIDATE",
              "Claimed North Sea reverse-origin coordinate",
              57.0, 5.0, None, None,
              "UNKNOWN_SEA_SURFACE_OR_SEAFLOOR", HOLDOUT,
              "outer_boundary_edge_monitor_candidate",
              None, None, "A_holdout",
              "height unknown; classified angularly only"),
    SeedPoint("BRODGAR_STONE_CIRCLE", "Ring of Brodgar",
              59.000925, -3.229212, 25.0, 8.0,
              "APPROXIMATE_PUBLIC_ELEVATION", HOLDOUT,
              "S3_surface_shell_candidate", None, None, "A_holdout",
              "Orkney; low-lying"),
    SeedPoint("GOBEKLI_DIAGNOSTIC", "Gobekli Tepe", 37.223242,
              38.922364, 760.0, 20.0, "APPROXIMATE_PUBLIC_ELEVATION",
              HOLDOUT, "S3_surface_shell_candidate", None, None,
              "A_holdout",
              "independent macrocell test; do not force a phi-line"),
    SeedPoint("MCKEAN_CANDIDATE",
              "McKean County / northern Pennsylvania candidate",
              None, None, None, None, "COORDINATE_NOT_RECOMPUTED",
              HOLDOUT, "S3_or_lunar_diagnostic_unresolved",
              167829573, "1200135305", "A_holdout",
              "coordinate not available; surface word carried only"),
)


def with_coordinates():
    return tuple(p for p in SEED_POINTS
                 if p.lat is not None and p.lon is not None)


def training_points():
    return tuple(p for p in SEED_POINTS if p.phase == "A_training")


def height_span_m() -> dict:
    hs = [p.height_m for p in SEED_POINTS if p.has_height]
    return {"min_m": min(hs), "max_m": max(hs),
            "span_m": max(hs) - min(hs),
            "count": len(hs),
            "note": "the full vertical span of every point that has a "
                    "declared height"}
