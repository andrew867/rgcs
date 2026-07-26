"""R10.8.5A §2 — the shell-3 zero: an average-land-height surface.

The bottom of shell 3 is referenced to **average land height along the
gravity-defined vertical** — explicitly NOT:

* mean sea level (untested substitute — the two differ by the mean land
  elevation itself, several hundred metres);
* a spherical Earth radius;
* geometric distance from Earth's centre;
* raw WGS84 ellipsoidal altitude;
* the ellipsoid normal direction.

Each banned substitute has a named refusal so the production path
cannot drift onto it silently.

The mean land elevation is carried as a two-member declared family —
the classic hypsographic value and the modern DEM-era value — because
the literature itself carries both. Both are retained; neither is
fitted to any vector. SOURCE_ESTABLISHED_PHYSICS for the elevations;
the shell-3 binding is the operator's locked declaration.
"""

from __future__ import annotations

from dataclasses import dataclass

from cwatlas.claims import ClaimError

#: Declared mean-land-elevation candidates, metres above mean sea level.
#: 840 m: classic hypsographic value (Kossinna lineage, widely quoted).
#: 797 m: modern DEM-derived estimate (ETOPO-era hypsometry).
MEAN_LAND_ELEVATION_CANDIDATES_M: dict[str, float] = {
    "CLASSIC_HYPSOGRAPHIC_840M": 840.0,
    "MODERN_DEM_797M": 797.0,
}

#: The default member used when a single number is needed for a receipt;
#: the projection sweep still runs both.
DEFAULT_LAND_REFERENCE = "CLASSIC_HYPSOGRAPHIC_840M"


@dataclass(frozen=True)
class LandZeroReference:
    """The declared shell-3 zero surface.

    ``epoch_year`` is carried because the reference is defined as
    epoch-appropriate; with no declared secular land-elevation rate the
    value is epoch-constant, and that constancy is itself declared here
    rather than assumed silently.
    """

    reference_id: str
    mean_land_elevation_m: float
    epoch_year: float
    vertical: str = "GRAVITY_VERTICAL"

    def __post_init__(self) -> None:
        if self.reference_id not in MEAN_LAND_ELEVATION_CANDIDATES_M:
            raise ClaimError(
                f"unknown land reference {self.reference_id!r}; declared: "
                f"{sorted(MEAN_LAND_ELEVATION_CANDIDATES_M)}")
        if self.vertical != "GRAVITY_VERTICAL":
            raise ClaimError(
                "the shell-3 zero is measured along GRAVITY_VERTICAL; "
                f"{self.vertical!r} is refused (see the named refusals).")


def land_zero(reference_id: str = DEFAULT_LAND_REFERENCE,
              epoch_year: float = 2025.0) -> LandZeroReference:
    return LandZeroReference(
        reference_id=reference_id,
        mean_land_elevation_m=MEAN_LAND_ELEVATION_CANDIDATES_M[reference_id],
        epoch_year=float(epoch_year))


def all_land_zero_candidates(epoch_year: float = 2025.0
                             ) -> tuple[LandZeroReference, ...]:
    return tuple(land_zero(rid, epoch_year)
                 for rid in sorted(MEAN_LAND_ELEVATION_CANDIDATES_M))


# --- named refusals for the banned substitutes -------------------------

def refuse_mean_sea_level_zero(*_a, **_k) -> None:
    """MSL is not the shell-3 zero and may not stand in for it untested."""
    raise ClaimError(
        "refused: mean sea level is not the shell-3 zero. The locked "
        "reference is the average land-height surface along gravity "
        "vertical; substituting MSL shifts the zero by the mean land "
        "elevation itself (~0.8 km) and is banned without an explicit "
        "declared test.")


def refuse_spherical_radius_zero(*_a, **_k) -> None:
    """A spherical Earth radius is not the shell-3 zero."""
    raise ClaimError(
        "refused: a spherical mean radius is not the shell-3 zero. The "
        "reference surface is gravity-defined; a sphere is neither an "
        "equipotential nor tied to land height.")


def refuse_geocentric_distance_zero(*_a, **_k) -> None:
    """Geometric distance from Earth's centre is not the shell-3 zero."""
    raise ClaimError(
        "refused: geometric distance from Earth's centre is not the "
        "shell-3 zero, and the core is not the reference authority — the "
        "outer-shell geometry is (the physical core may be offset "
        "relative to the magnetic structure and ellipsoidal figure).")


def refuse_wgs84_altitude_zero(*_a, **_k) -> None:
    """Raw WGS84 ellipsoidal altitude is not the shell-3 zero."""
    raise ClaimError(
        "refused: raw WGS84 ellipsoidal altitude is not the shell-3 "
        "zero. The ellipsoid is a reference figure, not a gravity-"
        "defined land surface; its normal is likewise not the vertical "
        "(see gravity_field_line.GRAVITY_VERTICAL).")


def msl_substitution_delta_m(reference_id: str = DEFAULT_LAND_REFERENCE
                             ) -> float:
    """The declared error an untested MSL substitution would introduce."""
    return MEAN_LAND_ELEVATION_CANDIDATES_M[reference_id]
