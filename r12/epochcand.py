"""R12 — four independent clocks, twenty-one orders of magnitude, and no
unique epoch.

Four different clocks are asked, one at a time, "when?" They answer on
scales so far apart that no combination of them names a single epoch.

**Ba-130** is a double-electron-capture nuclide with a half-life of
order ``10^21`` years -- longer than the age of the universe by eleven
orders of magnitude. It is a real chronometer only as an extremely
coarse bound; its half-life is quoted with a large fractional
uncertainty and carried as ``CONVENTIONAL_LITERATURE``.

**Cs-137** is the fission-product radionuclide of :mod:`r11.isotope`,
half-life ``30.05`` years (reused, not redefined). A decades-scale
chronometer, and only under the closed-system declarations that module
already enforces.

**Cs-133** is the SI second: ``9 192 631 770`` Hz *by definition*, zero
uncertainty by definition (reused from :mod:`r11.isotope`). It is a
FREQUENCY STANDARD, not a dating clock. A clock tells you how long, never
how long ago, so :func:`refuse_cs133_as_dating_clock` always raises.

**Astronomical time scales** -- TT, TDB, TAI, UT1, and Ephemeris Time --
are the fourth clock. They are not interchangeable: UTC is made
non-uniform by leap seconds, UT1 tracks the irregular rotation of the
Earth, and differencing two scales by number alone is a category error
that :func:`refuse_mixed_time_scale` refuses.

**The point.** These four span about twenty-one orders of magnitude in
characteristic time -- ``10^21`` years against ``30`` years against the
``~10^-10`` second of the cesium line. :func:`characteristic_times`
returns them and :func:`epoch_span_orders_of_magnitude` computes the
spread. A coarse bound plus a fine phase does not multiply out to a
single epoch: the fine phase is known only modulo one cycle, so an
enormous integer-cycle alias set survives (reusing
:func:`r11.isotope.integer_cycle_aliases`).
:func:`combine_candidates` therefore returns an ALIAS SET / interval
with more than one member, and :func:`refuse_unique_epoch` -- the same
refusal as :mod:`r11.isotope` -- ALWAYS raises.

Nothing here is measured. No sample is counted, no clock is compared, no
observation is timed. The standing verdict is
``EPOCH_CANDIDATES_ENUMERATED_NONE_UNIQUE``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

from r11.isotope import (
    CS133_HYPERFINE_HZ,
    CS133_HYPERFINE_UNCERTAINTY,
    CS137_HALF_LIFE_YEARS,
    CS137_HALF_LIFE_YEARS_EXACT,
    JULIAN_YEAR_S,
    MAX_ENUMERATED_ALIASES,
    IsotopeError,
    integer_cycle_aliases,
)
from r11.isotope import refuse_unique_epoch as _isotope_refuse_unique_epoch


class EpochCandError(RuntimeError):
    """Raised when a clock is asked for an epoch it cannot give."""


# --- claim vocabulary ---------------------------------------------------

class ClaimClass(Enum):
    """How a statement in this module is entitled to be believed."""

    EXACT_IDENTITY = "EXACT_IDENTITY"
    SOURCE_ESTABLISHED_PHYSICS = "SOURCE_ESTABLISHED_PHYSICS"
    REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
    ENGINEERING_CANDIDATE = "ENGINEERING_CANDIDATE"
    RETROSPECTIVE_NUMERIC_MATCH = "RETROSPECTIVE_NUMERIC_MATCH"
    PROSPECTIVE_PREDICTION = "PROSPECTIVE_PREDICTION"
    BENCH_MEASUREMENT = "BENCH_MEASUREMENT"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"


VERDICT = "EPOCH_CANDIDATES_ENUMERATED_NONE_UNIQUE"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"


# --- the four clocks, each a characteristic time ------------------------

class ClockKind(Enum):
    """What kind of statement a clock's characteristic time is."""

    GEOLOGICAL_DECAY = "GEOLOGICAL_DECAY"          # Ba-130 double EC
    DECADES_DECAY = "DECADES_DECAY"                # Cs-137 beta decay
    FREQUENCY_DEFINITION = "FREQUENCY_DEFINITION"  # Cs-133 SI second
    ASTRONOMICAL_TIME_SCALE = "ASTRONOMICAL_TIME_SCALE"


#: Ba-130 double-electron-capture half-life. Of order 10^21 years, quoted
#: with a large fractional uncertainty. This is a genuine measurement of
#: an extraordinarily rare process, carried as CONVENTIONAL_LITERATURE;
#: as a chronometer it is only a very coarse bound.
BA130_HALF_LIFE_YEARS: float = 1.2e21
BA130_HALF_LIFE_REL_UNCERTAINTY: float = 0.20      # ~20%, order-of-mag scale

#: Cs-137 half-life, reused from r11.isotope (30.05 a). Decades scale.
#: Bound here under an explicit name so the four clocks read together.
CS137_DECAY_YEARS: float = CS137_HALF_LIFE_YEARS

#: Cs-133 SI-second period: the reciprocal of the defined hyperfine
#: frequency, ~1.088e-10 s. The frequency is EXACT by definition; the
#: period is its exact reciprocal.
CS133_PERIOD_S_EXACT: Fraction = Fraction(1, CS133_HYPERFINE_HZ)
CS133_PERIOD_S: float = 1.0 / CS133_HYPERFINE_HZ

#: A conventional characteristic time for the astronomical clock: one
#: mean solar day in seconds, the scale on which UT1 and the uniform
#: scales are compared and on which leap seconds are inserted.
ASTRONOMICAL_DAY_S: float = 86400.0

PRIMARY_SOURCES: tuple[str, ...] = (
    "Evaluated Nuclear Structure Data File / NuDat (NNDC): Ba-130 "
    "double-electron-capture half-life of order 10^21 years, measured "
    "with a large fractional uncertainty",
    "BIPM, The International System of Units (SI Brochure), 9th ed. "
    "(2019): the second is the cesium-133 ground-state hyperfine "
    "transition frequency, exactly 9 192 631 770 Hz (a DEFINITION)",
    "Evaluated Nuclear Structure Data File / NuDat (NNDC): Cs-137 "
    "half-life ~30.05 a, beta decay to Ba-137",
    "IERS Conventions; SOFA/IAU time-scale definitions: TT, TDB, TAI, "
    "UT1 and Ephemeris Time are distinct scales, and UTC is made "
    "non-uniform by leap seconds",
)


@dataclass(frozen=True)
class ClockCandidate:
    """One clock, its characteristic time, and the epoch it cannot give."""

    label: str
    nuclide_or_standard: str
    kind: ClockKind
    characteristic_time_s: float
    claim_class: ClaimClass
    relative_uncertainty: float | None
    is_dating_clock: bool
    source_reference: str
    does_not_license: str


def _years_to_seconds(years: float) -> float:
    return float(years) * JULIAN_YEAR_S


BA130 = ClockCandidate(
    label="BA130_GEOLOGICAL_BOUND",
    nuclide_or_standard="Ba-130",
    kind=ClockKind.GEOLOGICAL_DECAY,
    characteristic_time_s=_years_to_seconds(BA130_HALF_LIFE_YEARS),
    claim_class=ClaimClass.SOURCE_ESTABLISHED_PHYSICS,
    relative_uncertainty=BA130_HALF_LIFE_REL_UNCERTAINTY,
    is_dating_clock=True,
    source_reference=PRIMARY_SOURCES[0],
    does_not_license=(
        "a fine epoch. A half-life of order 10^21 years fixes nothing "
        "narrower than 'some fraction of a geological-to-cosmological "
        "span'; it is a coarse bound, never a date"),
)

CS137_CLOCK = ClockCandidate(
    label="CS137_DECADES_CLOCK",
    nuclide_or_standard="Cs-137",
    kind=ClockKind.DECADES_DECAY,
    characteristic_time_s=_years_to_seconds(CS137_DECAY_YEARS),
    claim_class=ClaimClass.SOURCE_ESTABLISHED_PHYSICS,
    relative_uncertainty=None,                    # evaluation-dependent
    is_dating_clock=True,
    source_reference=PRIMARY_SOURCES[2],
    does_not_license=(
        "a date without the closed-system and initial-daughter "
        "declarations that r11.isotope already enforces; and not a "
        "frequency"),
)

CS133_CLOCK = ClockCandidate(
    label="CS133_FREQUENCY_STANDARD",
    nuclide_or_standard="Cs-133",
    kind=ClockKind.FREQUENCY_DEFINITION,
    characteristic_time_s=CS133_PERIOD_S,
    claim_class=ClaimClass.EXACT_IDENTITY,
    relative_uncertainty=0.0,                     # zero BY DEFINITION
    is_dating_clock=False,                         # a standard, not a date
    source_reference=PRIMARY_SOURCES[1],
    does_not_license=(
        "an age, an epoch, or any elapsed time. It fixes the unit of "
        "time; it does not tell you where you are on the time axis"),
)

ASTRO_CLOCK = ClockCandidate(
    label="ASTRONOMICAL_TIME_SCALE",
    nuclide_or_standard="TT/TDB/TAI/UT1/ET",
    kind=ClockKind.ASTRONOMICAL_TIME_SCALE,
    characteristic_time_s=ASTRONOMICAL_DAY_S,
    claim_class=ClaimClass.SOURCE_ESTABLISHED_PHYSICS,
    relative_uncertainty=None,
    is_dating_clock=True,
    source_reference=PRIMARY_SOURCES[3],
    does_not_license=(
        "a difference taken between two DIFFERENT scales by number "
        "alone; leap seconds and the Earth's irregular rotation make "
        "the scales non-interchangeable"),
)

#: All four clocks, in descending order of characteristic time.
CLOCKS: tuple[ClockCandidate, ...] = (
    BA130, CS137_CLOCK, ASTRO_CLOCK, CS133_CLOCK)


def characteristic_times() -> dict:
    """The four clocks and their characteristic times, in seconds."""
    return {
        c.label: {
            "nuclide_or_standard": c.nuclide_or_standard,
            "kind": c.kind.value,
            "characteristic_time_s": c.characteristic_time_s,
            "claim_class": c.claim_class.value,
            "relative_uncertainty": c.relative_uncertainty,
            "is_dating_clock": c.is_dating_clock,
        }
        for c in CLOCKS
    }


def epoch_span_orders_of_magnitude() -> float:
    """log10 of (longest characteristic time / shortest), across clocks.

    Ba-130's ~10^21-year half-life against the cesium line's ~10^-10 s
    is a spread of about thirty-one orders of magnitude -- and even
    excluding the frequency standard, the decay clocks alone span more
    than twenty. This is the number that makes a single combined epoch
    hopeless: the clocks are not measuring the same thing at the same
    resolution.
    """
    times = [c.characteristic_time_s for c in CLOCKS]
    t_hi = max(times)
    t_lo = min(times)
    if t_lo <= 0:
        raise EpochCandError("a characteristic time must be positive")
    return math.log10(t_hi / t_lo)


# --- the astronomical time scales ---------------------------------------

class TimeScale(Enum):
    """Distinct astronomical/atomic time scales. They do not subtract."""

    TT = "TERRESTRIAL_TIME"
    TDB = "BARYCENTRIC_DYNAMICAL_TIME"
    TAI = "INTERNATIONAL_ATOMIC_TIME"
    UT1 = "UNIVERSAL_TIME_1"
    ET = "EPHEMERIS_TIME"
    UTC = "COORDINATED_UNIVERSAL_TIME"             # non-uniform: leap seconds


#: Scales made non-uniform by leap seconds. A numeric difference across a
#: leap second is not an elapsed duration.
NON_UNIFORM_SCALES = frozenset({TimeScale.UT1, TimeScale.UTC})


def refuse_mixed_time_scale(a: TimeScale, b: TimeScale) -> None:
    """Refuse to difference two DIFFERENT time scales by number alone.

    Same-scale differences are fine and return ``None`` without raising;
    cross-scale differences raise. TAI is uniform atomic time, UT1
    tracks the irregular rotation of the Earth, and their difference is
    a slowly varying, tabulated quantity -- not a constant and not
    recoverable from two bare numbers. Subtracting a UT1 reading from a
    TAI reading as if they shared an origin and a rate silently injects
    the whole DUT1/leap-second history as an error.
    """
    if not isinstance(a, TimeScale) or not isinstance(b, TimeScale):
        raise EpochCandError(
            "refuse_mixed_time_scale takes two TimeScale members")
    if a is b:
        return None
    non_uniform = sorted(
        s.name for s in (a, b) if s in NON_UNIFORM_SCALES)
    raise EpochCandError(
        f"refused: {a.name} ({a.value}) and {b.name} ({b.value}) are "
        f"different time scales and may not be differenced by number "
        f"alone. "
        + (f"{', '.join(non_uniform)} is made non-uniform by leap "
           f"seconds and the Earth's irregular rotation, so a bare "
           f"numeric difference is not an elapsed duration. "
           if non_uniform else
           "The scales differ in rate and origin, so a bare numeric "
           "difference conflates two different time axes. ")
        + "Convert both to one uniform scale (TAI, or TT) with the "
        "tabulated offsets (DUT1, the leap-second table, TDB-TT "
        "periodic terms) before subtracting. A number is not a time "
        "until its scale is declared.")


def time_scales() -> dict:
    """The scales this module distinguishes, and which are non-uniform."""
    return {
        "scales": {s.name: s.value for s in TimeScale},
        "non_uniform": sorted(s.name for s in NON_UNIFORM_SCALES),
        "note": (
            "UTC and UT1 are non-uniform; TT, TDB, TAI and ET are the "
            "uniform/dynamical scales. Differencing across scales "
            "requires the tabulated offsets, never a bare subtraction"),
        "claim_class": ClaimClass.SOURCE_ESTABLISHED_PHYSICS.value,
    }


# --- Cs-133 is a standard, not a dating clock ---------------------------

def cs133_frequency_standard() -> dict:
    """The clock isotope, as a DEFINITION with zero uncertainty."""
    return {
        "nuclide": "Cs-133",
        "hyperfine_hz": CS133_HYPERFINE_HZ,
        "is_exact_integer": CS133_HYPERFINE_HZ == 9_192_631_770,
        "period_s_exact": str(CS133_PERIOD_S_EXACT),
        "uncertainty": str(CS133_HYPERFINE_UNCERTAINTY),
        "uncertainty_kind": "ZERO_BY_DEFINITION",
        "claim_class": ClaimClass.EXACT_IDENTITY.value,
        "is_dating_clock": False,
        "source_reference": PRIMARY_SOURCES[1],
        "note": (
            "this integer DEFINES the second; it is a frequency "
            "standard, not a chronometer. A clock tells you how long, "
            "never how long ago"),
    }


def refuse_cs133_as_dating_clock(claimed_epoch_year: int | None = None
                                 ) -> None:
    """Cs-133 is the SI second, not a way to date anything. Always raises.

    The hyperfine frequency is fixed by definition with zero
    uncertainty. That makes it the ideal *ruler* for durations and the
    worst possible *dating* clock: it has no decay, no initial state, no
    zero epoch -- nothing that changes with time and could mark a
    position on the time axis.
    """
    raise EpochCandError(
        f"refused: Cs-133 may not be used as a dating clock"
        + (f" (claimed year {claimed_epoch_year!r})"
           if claimed_epoch_year is not None else "")
        + f". Its hyperfine transition frequency is {CS133_HYPERFINE_HZ} "
        f"Hz EXACTLY, fixed by the SI definition of the second with "
        f"zero uncertainty. A dating clock needs something that evolves "
        f"-- a decay, a cooling, a phase that accumulates from a known "
        f"start -- and a defined, unchanging frequency has none of "
        f"that. It measures how long; it cannot measure how long ago. "
        f"Use Cs-137 (decades) or Ba-130 (geological) for a coarse age, "
        f"and see refuse_unique_epoch for why even those do not name a "
        f"single year.")


# --- combining the candidates: an alias set, never a point --------------

@dataclass(frozen=True)
class EpochInterval:
    """A coarse interval plus the fine-phase alias count over it."""

    t_lo_s: float
    t_hi_s: float
    carrier_hz: int
    alias_count: int
    n_min: int
    n_max: int
    members: tuple[str, ...]
    unique: bool
    note: str = ""


#: A deliberately narrow default coarse interval (one Cs-137 half-life
#: wide, near the present), just to show the alias set is huge even so.
DEFAULT_COARSE_LO_YEARS: float = 0.0
DEFAULT_COARSE_HI_YEARS: float = CS137_HALF_LIFE_YEARS


def combine_candidates(
        coarse_lo_years: float = DEFAULT_COARSE_LO_YEARS,
        coarse_hi_years: float = DEFAULT_COARSE_HI_YEARS,
        fine_carrier_hz: int = CS133_HYPERFINE_HZ,
        max_enumerate: int = MAX_ENUMERATED_ALIASES) -> EpochInterval:
    """Combine a coarse bound with a fine phase. Returns an ALIAS SET.

    A coarse decay bound gives an interval ``[t_lo, t_hi]``. A coherent
    fine carrier gives a phase, and a phase is known only modulo one
    whole cycle, so the whole-cycle count ``n`` is ambiguous across
    every integer in the interval. This defers to
    :func:`r11.isotope.integer_cycle_aliases`, which returns that count
    (astronomically large for the cesium line) together with the
    ``n``-range. The result carries **more than one member** -- the two
    interval endpoints at least, and the full alias count -- because a
    coarse bound plus a fine phase still leaves integer-cycle aliases.
    """
    if coarse_hi_years < coarse_lo_years:
        raise EpochCandError(
            f"coarse interval is inverted: t_hi ({coarse_hi_years}) < "
            f"t_lo ({coarse_lo_years})")
    if coarse_hi_years <= coarse_lo_years:
        raise EpochCandError(
            "a coarse bound must have positive width, or there is "
            "nothing to alias over")
    lo_s = _years_to_seconds(coarse_lo_years)
    hi_s = _years_to_seconds(coarse_hi_years)
    aliases = integer_cycle_aliases(lo_s, hi_s, fine_carrier_hz,
                                    max_enumerate)
    members = (
        f"INTERVAL_LO={coarse_lo_years:g}_years",
        f"INTERVAL_HI={coarse_hi_years:g}_years",
        f"ALIAS_COUNT={aliases.count}",
        f"N_RANGE=[{aliases.n_min},{aliases.n_max}]",
    )
    return EpochInterval(
        t_lo_s=lo_s,
        t_hi_s=hi_s,
        carrier_hz=int(fine_carrier_hz),
        alias_count=aliases.count,
        n_min=aliases.n_min,
        n_max=aliases.n_max,
        members=members,
        unique=aliases.is_unique(),
        note=(
            "the coarse bound gives the interval; the fine carrier is "
            "ambiguous modulo one cycle, so the whole-cycle count is an "
            "enormous alias set over that interval. More than one "
            "candidate survives, so this is an interval, not a date"),
    )


def refuse_unique_epoch(alias_count: int | None = None,
                        independent_coarse_anchor: str | None = None,
                        second_coherent_observable: str | None = None,
                        claimed_epoch_year: int | None = None) -> None:
    """Refuse a unique epoch. ALWAYS raises, consistent with r11.isotope.

    This wraps :func:`r11.isotope.refuse_unique_epoch`. That function
    admits one narrow escape: an alias count of exactly one *plus* an
    independent coarse anchor *plus* a second coherent observable. None
    of those three holds in this environment -- the alias count is
    astronomically large, there is no independent anchor, and there is
    no second coherent observable bundled here -- so the escape can
    never open and this refusal always fires. When called with no
    arguments it defaults to the (huge) alias count of the default
    combined candidate.
    """
    if alias_count is None:
        alias_count = combine_candidates().alias_count
    if alias_count < 0:
        raise EpochCandError("an alias count cannot be negative")
    try:
        _isotope_refuse_unique_epoch(
            alias_count,
            independent_coarse_anchor=independent_coarse_anchor,
            second_coherent_observable=second_coherent_observable,
            claimed_epoch_year=claimed_epoch_year)
    except IsotopeError as exc:
        raise EpochCandError(
            f"{exc} Across the four clocks here -- Ba-130 (~10^21 a), "
            f"Cs-137 (30.05 a), the Cs-133 frequency standard, and the "
            f"astronomical time scales -- no combination collapses the "
            f"alias set to one admissible count. {VERDICT}.") from exc
    raise EpochCandError(                            # pragma: no cover
        "a unique epoch was not refused; in this environment the alias "
        "count is never one and no independent second observable is "
        "bundled, so the r11.isotope escape can never open. "
        f"{VERDICT}.")


# --- report --------------------------------------------------------------

def epochcand_report() -> dict:
    """The standing result: four clocks enumerated, none unique."""
    combined = combine_candidates()
    spread = epoch_span_orders_of_magnitude()
    return {
        "what_this_is": (
            "four independent clocks -- Ba-130 double electron capture "
            "(~10^21 years), Cs-137 beta decay (30.05 years), the "
            "Cs-133 SI-second frequency standard, and the astronomical "
            "time scales -- enumerated as epoch candidates, none of "
            "which yields a unique epoch"),
        "claim_class": ClaimClass.SOURCE_ESTABLISHED_PHYSICS.value,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "clocks": characteristic_times(),
        "ba130_half_life_years": BA130_HALF_LIFE_YEARS,
        "ba130_half_life_rel_uncertainty": BA130_HALF_LIFE_REL_UNCERTAINTY,
        "cs137_half_life_years": CS137_DECAY_YEARS,
        "cs137_half_life_exact": str(CS137_HALF_LIFE_YEARS_EXACT),
        "cs133_frequency_standard": cs133_frequency_standard(),
        "time_scales": time_scales(),
        "epoch_span_orders_of_magnitude": spread,
        "spread_exceeds_twenty": spread > 20.0,
        "combined_candidate": {
            "t_lo_s": combined.t_lo_s,
            "t_hi_s": combined.t_hi_s,
            "carrier_hz": combined.carrier_hz,
            "alias_count": combined.alias_count,
            "n_range": [combined.n_min, combined.n_max],
            "members": list(combined.members),
            "unique": combined.unique,
            "note": combined.note,
        },
        "refusals_available": [
            "refuse_cs133_as_dating_clock (always raises)",
            "refuse_mixed_time_scale (raises across scales)",
            "refuse_unique_epoch (always raises; wraps r11.isotope)",
        ],
        "primary_sources": list(PRIMARY_SOURCES),
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not date anything, count a sample, compare a clock, "
            "or time an observation. It does not name an epoch: the four "
            "clocks span about twenty-one orders of magnitude and more "
            "in characteristic time, a coarse bound plus a fine phase "
            "still leaves an astronomically large integer-cycle alias "
            "set, and no independent second coherent observable is "
            "bundled to collapse it. It does not treat Cs-133 as a "
            "dating clock -- a defined frequency measures how long, "
            "never how long ago -- and it does not difference two "
            "astronomical time scales by number alone."),
    }
