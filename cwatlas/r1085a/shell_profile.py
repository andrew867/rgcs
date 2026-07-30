"""R10.8.5A §1 — ShellProfile: mean epoch-dependent shell thicknesses.

The shell ontology (indices 0..8, shell-3 zero at the average-land
surface) comes from :mod:`cwatlas.shells`; the 3-bit S3 register lesson
(an index is not a radius until basis, origin and law are declared)
comes from :mod:`r12.shells8`. This module declares the missing third
ingredient — thickness — as a **bounded candidate family**, because no
corpus value fixes the shell thicknesses. Every candidate is fully
declared before any vector is projected, every candidate's result is
retained, and no thickness is ever fitted to a source vector
(``no free per-vector offsets``).

Radial semantics (locked): the operational stack runs from the shell-3
inner boundary (the land-zero surface, :mod:`cwatlas.r1085a.land_zero`)
outward through shell 8, whose outer boundary is the **outermost
operational boundary**. Within shell ``s``, ``zeta = 0`` at the inner
boundary, ``zeta = 1`` at the outer boundary, and Z increases from
inner to outer.

Nothing here is measured. Thickness values are ENGINEERING_CANDIDATE
numbers; the physical shell structure itself is
``PHYSICAL_VALIDATION_NOT_CLAIMED``.
"""

from __future__ import annotations

from dataclasses import dataclass

from cwatlas.claims import ClaimError

#: Operational shells, inner to outer. Shell 3's inner boundary is the
#: land-zero surface; shells 0..2 are below it and are NOT part of the
#: outer-in operational stack (the corpus gives them no thickness).
OPERATIONAL_SHELLS = (3, 4, 5, 6, 7, 8)

#: Reference epoch (decimal year) at which candidate thicknesses are quoted.
T0_YEAR = 2025.0


@dataclass(frozen=True)
class ShellBand:
    """One shell's mean thickness at T0 and its linear epoch rate."""

    shell_id: int
    mean_thickness_km_t0: float
    rate_km_per_year: float

    def thickness_km(self, epoch_year: float) -> float:
        dt = float(epoch_year) - T0_YEAR
        value = self.mean_thickness_km_t0 + self.rate_km_per_year * dt
        if value <= 0:
            raise ClaimError(
                f"shell {self.shell_id}: thickness {value} km non-positive "
                f"at epoch {epoch_year}; the linear rate model is outside "
                f"its validity — refuse rather than clamp.")
        return value


@dataclass(frozen=True)
class ShellProfile:
    """A full declared thickness profile for the operational stack.

    ``provenance`` states where the numbers come from; none come from a
    source vector, and the constructor refuses a profile that does not
    cover exactly the operational shells.
    """

    profile_id: str
    bands: tuple[ShellBand, ...]
    provenance: str

    def __post_init__(self) -> None:
        ids = tuple(b.shell_id for b in self.bands)
        if ids != OPERATIONAL_SHELLS:
            raise ClaimError(
                f"profile {self.profile_id}: bands must cover shells "
                f"{OPERATIONAL_SHELLS} in order, got {ids}")

    def band(self, shell_id: int) -> ShellBand:
        for b in self.bands:
            if b.shell_id == shell_id:
                return b
        raise ClaimError(
            f"shell {shell_id} is not in the operational stack "
            f"{OPERATIONAL_SHELLS}; shells 0..2 sit below the land-zero "
            f"surface and carry no declared thickness.")

    def thicknesses_km(self, epoch_year: float) -> dict[int, float]:
        return {b.shell_id: b.thickness_km(epoch_year) for b in self.bands}

    def stack_height_km(self, epoch_year: float) -> float:
        """Land-zero surface up to the outermost operational boundary."""
        return sum(self.thicknesses_km(epoch_year).values())

    def outer_stack_above_km(self, shell_id: int,
                             epoch_year: float) -> float:
        """Sum of complete-shell thicknesses strictly outside ``shell_id``."""
        self.band(shell_id)
        return sum(b.thickness_km(epoch_year) for b in self.bands
                   if b.shell_id > shell_id)

    def inner_stack_below_km(self, shell_id: int,
                             epoch_year: float) -> float:
        """Land-zero surface up to ``shell_id``'s inner boundary."""
        self.band(shell_id)
        return sum(b.thickness_km(epoch_year) for b in self.bands
                   if b.shell_id < shell_id)


def _profile(pid: str, note: str,
             rows: list[tuple[int, float, float]]) -> ShellProfile:
    return ShellProfile(
        profile_id=pid,
        bands=tuple(ShellBand(s, t, r) for s, t, r in rows),
        provenance=note)


#: The bounded candidate family. Declared BEFORE projection; all retained.
CANDIDATE_PROFILES: tuple[ShellProfile, ...] = (
    _profile(
        "UNIFORM_100KM_V1",
        "engineering candidate: six equal 100 km bands, no epoch rate; "
        "the maximum-ignorance member of the family.",
        [(s, 100.0, 0.0) for s in OPERATIONAL_SHELLS]),
    _profile(
        "ATMOSPHERIC_LADDER_V1",
        "engineering candidate: bands echo conventional atmospheric "
        "layering above the land-zero surface (troposphere ~12 km, "
        "stratosphere ~38 km, mesosphere ~35 km, lower/upper thermosphere "
        "~515 km split, exosphere band 400 km). Thermosphere band carries "
        "a small negative rate as a stand-in for solar-cycle/secular "
        "contraction (declared, not fitted). SOURCE_ESTABLISHED_PHYSICS "
        "for the layer altitudes; the shell mapping is a candidate only.",
        [(3, 12.0, 0.0), (4, 38.0, 0.0), (5, 35.0, 0.0),
         (6, 215.0, -0.05), (7, 300.0, -0.05), (8, 400.0, 0.0)]),
    _profile(
        "GEOMETRIC_DOUBLING_V1",
        "engineering candidate: thickness doubles per shell from 25 km "
        "(25, 50, 100, 200, 400, 800), no epoch rate; the geometric "
        "member, echoing r12.shells8.SpacingLaw.GEOMETRIC.",
        [(3, 25.0, 0.0), (4, 50.0, 0.0), (5, 100.0, 0.0),
         (6, 200.0, 0.0), (7, 400.0, 0.0), (8, 800.0, 0.0)]),
)

_BY_ID = {p.profile_id: p for p in CANDIDATE_PROFILES}


def profile(profile_id: str) -> ShellProfile:
    try:
        return _BY_ID[profile_id]
    except KeyError:
        raise ClaimError(
            f"unknown shell profile {profile_id!r}; declared candidates: "
            f"{sorted(_BY_ID)}") from None


def refuse_fitted_thickness(*_a, **_k) -> None:
    """Refuse any thickness derived from a source vector.

    A thickness fitted so a chosen vector lands somewhere pleasing is a
    per-vector offset wearing a different name. The family above is
    closed: project under every member, retain every result, add none.
    """
    raise ClaimError(
        "refused: shell thicknesses are declared candidates, never fitted "
        "to a source vector. Extending the family requires a new declared "
        "member with provenance, before any projection that uses it.")
