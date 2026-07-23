"""P06 — cesium-137/barium-137 coarse ages, cesium-133 fine phase, and why
the two cesiums are DIFFERENT TYPED SYSTEMS that must never be merged.

The lore reaches for "cesium" and lets one word do two incompatible jobs.
It cannot. **Cs-133 is a CLOCK.** It is the stable, monoisotopic ground
state whose hyperfine transition frequency is *fixed by definition* at
exactly ``9 192 631 770 Hz`` (BIPM SI Brochure, 9th ed.) -- that integer
does not measure anything, it *gives the second its length*, and its
uncertainty is zero by definition. **Cs-137 is a RADIONUCLIDE.** It is an
unstable fission product with a half-life of about ``30.05`` years that
beta-decays to barium-137, and it is a *chronometer* only in the weak,
assumption-laden sense that any parent/daughter pair is: it yields an age
if, and only if, a closed system and a zero initial radiogenic daughter
are DECLARED and defended.

These are different atoms, different physics, different units, different
evidence classes. One is a frequency definition; the other is a decay
statistic. :class:`IsotopeSystem` types them apart and
:func:`refuse_isotope_conflation` refuses to let a shared chemical symbol
merge them. Nothing in this module lets a number that came from the clock
be spent as though it came from the chronometer, or the reverse.

**Part 1 -- the coarse age is a model, not a reading.** For a closed
system with zero initial radiogenic daughter,

    R = N_Ba_rad / N_Cs        t = T_half * log2(1 + R)

which is exact arithmetic on an ``ANALYTIC_MODEL``, not a measurement.
Every term in that "if and only if" is a *declaration the caller owes*:
the initial stable Ba-137 (natural barium is already about 11.2% Ba-137,
so radiogenic and inherited daughter are not separable by assertion),
parent or daughter loss, contamination, the branching data, the
measurement uncertainty, the formation epoch, and the measurement epoch.
:class:`CoarseAgeResult` carries all seven as ``UNDECLARED`` by default
and :func:`refuse_age_without_closed_system_declaration` raises until
they are filled in. Note also that Cs-137 decays about **94.6%** through
the ``Ba-137m`` isomer (which then relaxes to ``Ba-137``) and about
**5.4%** straight to the Ba-137 ground state; evaluations differ in the
last digit, which is exactly why a branching ratio must be DECLARED with
its source rather than assumed.

**Part 2 -- the orientation trap.** A reported ratio is a pair of numbers
and a *convention*, and the convention is not in the numbers. Both
orientations are arithmetically legitimate and they give different ages:

    192/55 = 3.4909090909090907...        55/192 = 0.2864583333333333...

:func:`audit_ratio_orientations` reports BOTH, with exact rationals, and
refuses to pick. :func:`refuse_orientation_chosen_from_desired_year`
exists because the tempting move is to choose whichever orientation lands
on a preferred calendar date -- which is fitting the convention to the
answer, and is not evidence.

**Part 3 -- a fine phase does not date anything.** A coherent carrier
gives a *phase*, and a phase is only known modulo one whole cycle. Handed
a coarse interval ``[t_lo, t_hi]`` and a carrier ``f``, the whole-cycle
count ``n`` is ambiguous across every integer in the interval:
:func:`integer_cycle_aliases` returns them (or, when the count is
astronomically large -- which it always is for the cesium line -- the
count and the ``n``-range rather than a list that could not be held).
A SECOND coherent carrier reduces the alias set the way a Chinese
remainder condition does: the joint solutions repeat at the common period
``1 / gcd(f1, f2)``, so the count falls by a large factor. It does not
fall to one. :func:`aliases_with_second_carrier` shows the drop and shows
that the survivor count stays far above 1 for any realistic interval.

Therefore **a unique six-digit-year epoch is forbidden here.** Naming a
single six-digit year would require an independent coarse anchor *and* a
second coherent observable that together collapse the alias set to a
single admissible ``n``; neither exists in this environment, and an
epoch quoted to six digits from a phase that is ambiguous over billions
of cycles is a precision claim the arithmetic cannot support.
:func:`refuse_unique_epoch` raises.

Nothing here is measured. No sample is counted, no clock is compared, no
spectrum is taken. The default verdict is
``CESIUM_BARIUM_EPOCH_STILL_NON_UNIQUE``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

# --- constants, with provenance ----------------------------------------

#: Cs-133 ground-state hyperfine transition frequency: EXACTLY this
#: integer, by the SI definition of the second (BIPM SI Brochure, 9th
#: ed., 2019). A DEFINITION, not a measurement; zero uncertainty by
#: definition. This is the CLOCK isotope and it is stable.
CS133_HYPERFINE_HZ: int = 9_192_631_770

#: Uncertainty of the above, as a Fraction. Exactly zero, *by
#: definition* -- not "too small to quote".
CS133_HYPERFINE_UNCERTAINTY: Fraction = Fraction(0)

#: Cs-137 half-life in years. This pack uses 30.05 a, the evaluated
#: value carried by the nuclear data references below. It is a measured,
#: evaluated quantity with an uncertainty in its last digits -- unlike
#: the Cs-133 number above, which is a definition.
CS137_HALF_LIFE_YEARS: float = 30.05

#: The same half-life as an exact rational, for arithmetic that must not
#: drift: 30.05 a = 601/20 a.
CS137_HALF_LIFE_YEARS_EXACT: Fraction = Fraction("30.05")

#: Cs-137 beta-decay branching. About 94.6% proceeds via the Ba-137m
#: isomer (T_1/2 ~ 2.55 min, the 661.7 keV gamma), which then relaxes to
#: the Ba-137 GROUND state; about 5.4% goes directly to the ground
#: state. Published evaluations differ in the last digit (94.7/5.3 is
#: also quoted), which is precisely why branching must be DECLARED with
#: its source and never assumed.
BA137M_BRANCH: float = 0.946
BA137_GROUND_BRANCH: float = 0.054

#: Ba-137 is already ~11.2% of NATURAL barium (IUPAC isotopic
#: composition). Radiogenic Ba-137 and inherited stable Ba-137 are the
#: same atom; they are not separable by assertion, which is why
#: ``initial_stable_Ba137`` is a mandatory declaration below.
BA137_NATURAL_ABUNDANCE: float = 0.11232

#: Julian year in seconds (365.25 d), the conventional annum used when
#: a year-valued age has to become a time in seconds.
JULIAN_YEAR_S: int = 31_557_600

#: A conventional laboratory distribution frequency, used ONLY as a
#: modelling stand-in for "a second coherent carrier". No such signal is
#: received, generated, or measured here.
DEFAULT_SECOND_CARRIER_HZ: int = 10_000_000

#: Above this many aliases the set is reported as a count plus an
#: ``n``-range instead of an enumerated tuple.
MAX_ENUMERATED_ALIASES: int = 4096

DEFAULT_VERDICT = "CESIUM_BARIUM_EPOCH_STILL_NON_UNIQUE"
UNDECLARED = "UNDECLARED"

#: Conventional public references. Nuclear structure and decay data are
#: quoted from evaluated compilations; the SI second from BIPM.
PRIMARY_SOURCES: tuple[str, ...] = (
    "BIPM, The International System of Units (SI Brochure), 9th ed. "
    "(2019): the second is defined by the cesium-133 ground-state "
    "hyperfine transition frequency, exactly 9 192 631 770 Hz "
    "(a DEFINITION, zero uncertainty)",
    "Evaluated Nuclear Structure Data File / NuDat (NNDC, Brookhaven "
    "National Laboratory): Cs-137 half-life ~30.05 a; beta decay to "
    "Ba-137m (~94.6%) and to the Ba-137 ground state (~5.4%)",
    "Decay Data Evaluation Project (DDEP/LNHB) recommended data for "
    "Cs-137 / Ba-137m, including the 661.657 keV gamma from the Ba-137m "
    "isomeric transition",
    "IUPAC Commission on Isotopic Abundances and Atomic Weights: "
    "isotopic composition of natural barium (Ba-137 ~11.2%)",
    "G. Faure and T. M. Mensing, Isotopes: Principles and Applications, "
    "3rd ed.: closed-system and initial-daughter assumptions "
    "underlying any parent/daughter age",
    "A. P. Dickin, Radiogenic Isotope Geology, 2nd ed.: open-system "
    "behaviour, daughter loss, and contamination as the standard "
    "failure modes of a single-pair age",
)


class IsotopeError(ValueError):
    """Raised when an isotope system is misused or a claim outruns it."""


# --- the two cesiums, typed apart ---------------------------------------

class IsotopeSystem(Enum):
    """Which cesium is being talked about. They do not mix."""

    CS133_CLOCK = "cs133_clock_definition"        # stable; a FREQUENCY
    CS137_RADIONUCLIDE = "cs137_radionuclide"     # unstable; a DECAY


class EvidenceClass(Enum):
    """What kind of statement a number is."""

    DEFINITION = "DEFINITION"                     # fixed by convention
    ANALYTIC_MODEL = "ANALYTIC_MODEL"             # arithmetic on a model
    EVALUATED_LITERATURE = "EVALUATED_LITERATURE"  # compiled measurement


@dataclass(frozen=True)
class TypedIsotope:
    """One isotope, with the job it is and is not allowed to do."""

    nuclide: str
    system: IsotopeSystem
    evidence_class: EvidenceClass
    stable: bool
    observable: str
    value: Fraction | None
    unit: str
    uncertainty: Fraction | None
    source_reference: str
    does_not_license: str


CS133 = TypedIsotope(
    nuclide="Cs-133",
    system=IsotopeSystem.CS133_CLOCK,
    evidence_class=EvidenceClass.DEFINITION,
    stable=True,
    observable="ground-state hyperfine transition frequency",
    value=Fraction(CS133_HYPERFINE_HZ),
    unit="Hz",
    uncertainty=CS133_HYPERFINE_UNCERTAINTY,     # zero BY DEFINITION
    source_reference=PRIMARY_SOURCES[0],
    does_not_license=(
        "a date, an age, an epoch, or any elapsed time. A frequency "
        "definition fixes the unit of time; it does not tell you where "
        "you are on the time axis"),
)

CS137 = TypedIsotope(
    nuclide="Cs-137",
    system=IsotopeSystem.CS137_RADIONUCLIDE,
    evidence_class=EvidenceClass.EVALUATED_LITERATURE,
    stable=False,
    observable="beta-decay half-life to Ba-137 (via Ba-137m, ~94.6%)",
    value=CS137_HALF_LIFE_YEARS_EXACT,
    unit="a (Julian years)",
    uncertainty=None,                            # evaluation-dependent
    source_reference=PRIMARY_SOURCES[1],
    does_not_license=(
        "a frequency, a phase, or any statement about the SI second. A "
        "decay constant is a statistical rate, not a coherent "
        "oscillation"),
)

TYPED_ISOTOPES = (CS133, CS137)


def refuse_isotope_conflation(a: TypedIsotope, b: TypedIsotope) -> None:
    """Refuse to merge the clock isotope with the radionuclide.

    They share a chemical symbol and nothing else that matters here: one
    is a defined frequency with zero uncertainty, the other an evaluated
    decay rate. Passing a number from one into the other's role is a
    category error, not a shortcut.
    """
    if a.system is b.system:
        raise IsotopeError(
            f"refuse_isotope_conflation compares two DIFFERENT systems; "
            f"{a.nuclide} and {b.nuclide} are both "
            f"{a.system.value} and there is nothing to refuse")
    raise IsotopeError(
        f"{a.nuclide} ({a.system.value}, {a.evidence_class.value}) and "
        f"{b.nuclide} ({b.system.value}, {b.evidence_class.value}) are "
        f"different typed systems and must not be merged. "
        f"{a.nuclide} does not license {a.does_not_license}. "
        f"{b.nuclide} does not license {b.does_not_license}. "
        f"Sharing the element name 'cesium' is a fact about chemistry "
        f"nomenclature, not a bridge between a definition and a decay.")


# --- Part 1: the coarse age ---------------------------------------------

#: The seven declarations a single-pair age owes before it is an age at
#: all. Each defaults to UNDECLARED on CoarseAgeResult.
MANDATORY_DECLARATIONS: tuple[str, ...] = (
    "initial_stable_Ba137",
    "parent_or_daughter_loss",
    "contamination",
    "branching_data",
    "measurement_uncertainty",
    "formation_epoch",
    "measurement_epoch",
)


def _as_fraction(x: Fraction | float | int) -> Fraction:
    """Exact rational view of a ratio-like input."""
    if isinstance(x, Fraction):
        return x
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        if not math.isfinite(x):
            raise IsotopeError("a ratio must be a finite number")
        return Fraction(x)
    raise IsotopeError(f"cannot read {x!r} as a ratio")


def coarse_age(R: Fraction | float | int,
               t_half: float = CS137_HALF_LIFE_YEARS) -> float:
    """Coarse age ``t = T_half * log2(1 + R)`` for ``R = N_Ba_rad/N_Cs``.

    The closed-system, zero-initial-radiogenic-daughter model, and
    nothing more. ``R = 1`` (one radiogenic daughter per surviving
    parent) returns exactly one half-life; ``R = 3`` returns exactly
    two. The number this returns is an ``ANALYTIC_MODEL`` output: it is
    an age only once the declarations in :data:`MANDATORY_DECLARATIONS`
    are supplied, which is what
    :func:`refuse_age_without_closed_system_declaration` enforces.
    """
    if t_half <= 0:
        raise IsotopeError("a half-life must be positive")
    r = float(R)
    if not math.isfinite(r):
        raise IsotopeError("R must be finite")
    if r < 0:
        raise IsotopeError(
            f"R = {r!r}: a daughter/parent number ratio cannot be "
            f"negative; there is no age to compute")
    return t_half * math.log2(1.0 + r)


def age_from_inverse_ratio(
        inv_R: Fraction | float | int,
        t_half: float = CS137_HALF_LIFE_YEARS) -> float:
    """Coarse age from the INVERSE reporting convention ``N_Cs/N_Ba``.

    Some reports quote parent-over-daughter. That is the reciprocal of
    the ratio the model wants, so this is ``coarse_age(1/inv_R)`` -- and
    stating which convention a number arrived in is the caller's job,
    not something the arithmetic can recover. See
    :func:`audit_ratio_orientations`.
    """
    inv = _as_fraction(inv_R)
    if inv <= 0:
        raise IsotopeError(
            f"N_Cs/N_Ba = {inv}: a non-positive parent/daughter ratio "
            f"has no inverse age (zero parent would mean infinite age, "
            f"which is a statement about the model breaking down, not a "
            f"date)")
    return coarse_age(1 / inv, t_half)


@dataclass(frozen=True)
class CoarseAgeResult:
    """A coarse age together with everything it has NOT been told.

    The seven declaration fields default to ``UNDECLARED``. Until they
    are filled, ``age_years`` is arithmetic about a model, not an age
    about a sample.
    """

    ratio_R: Fraction
    ratio_orientation: str                 # "N_Ba_rad/N_Cs" or inverse
    t_half_years: float
    age_years: float
    evidence_class: EvidenceClass = EvidenceClass.ANALYTIC_MODEL
    closed_system_declared: bool = False
    # --- the mandatory declarations, all UNDECLARED by default -------
    initial_stable_Ba137: str | None = UNDECLARED
    parent_or_daughter_loss: str | None = UNDECLARED
    contamination: str | None = UNDECLARED
    branching_data: str | None = UNDECLARED
    measurement_uncertainty: str | None = UNDECLARED
    formation_epoch: str | None = UNDECLARED
    measurement_epoch: str | None = UNDECLARED
    measured_here: str = "nothing"

    def undeclared_fields(self) -> tuple[str, ...]:
        """Which mandatory declarations are still missing."""
        missing = []
        for name in MANDATORY_DECLARATIONS:
            value = getattr(self, name)
            if value is None or value == UNDECLARED or value == "":
                missing.append(name)
        return tuple(missing)

    def is_fully_declared(self) -> bool:
        return self.closed_system_declared and not self.undeclared_fields()


def coarse_age_result(R: Fraction | float | int,
                      t_half: float = CS137_HALF_LIFE_YEARS,
                      orientation: str = "N_Ba_rad/N_Cs",
                      **declarations: object) -> CoarseAgeResult:
    """Build a :class:`CoarseAgeResult`; declarations are opt-in."""
    unknown = set(declarations) - set(MANDATORY_DECLARATIONS) \
        - {"closed_system_declared"}
    if unknown:
        raise IsotopeError(
            f"unknown declaration field(s): {sorted(unknown)}; the "
            f"mandatory set is {list(MANDATORY_DECLARATIONS)}")
    r = _as_fraction(R)
    return CoarseAgeResult(
        ratio_R=r,
        ratio_orientation=orientation,
        t_half_years=t_half,
        age_years=coarse_age(r, t_half),
        **declarations,                        # type: ignore[arg-type]
    )


def refuse_age_without_closed_system_declaration(
        result: CoarseAgeResult) -> dict:
    """Refuse to call the model output an age until the caller declares.

    A single parent/daughter pair yields a date only under a closed
    system with a known initial daughter inventory. Every one of the
    seven fields is a way the number can be wrong by an unbounded
    amount, so none of them may be left to the reader's imagination. If
    all are declared this returns the declaration record; otherwise it
    raises.
    """
    if not isinstance(result, CoarseAgeResult):
        raise IsotopeError(
            "refuse_age_without_closed_system_declaration takes a "
            "CoarseAgeResult")
    missing = result.undeclared_fields()
    if not result.closed_system_declared or missing:
        raise IsotopeError(
            f"cannot report {result.age_years:.6g} a as an AGE. "
            f"closed_system_declared={result.closed_system_declared}; "
            f"undeclared: {list(missing) or 'none'}. "
            f"t = T_half * log2(1 + R) is exact arithmetic on a model "
            f"that assumes a closed system and ZERO initial radiogenic "
            f"Ba-137 -- but natural barium is already about "
            f"{BA137_NATURAL_ABUNDANCE * 100:.1f}% Ba-137, radiogenic "
            f"and inherited daughter are the same atom, parent or "
            f"daughter loss and contamination both bias the ratio "
            f"without leaving a trace in it, the branching (~"
            f"{BA137M_BRANCH * 100:.1f}% via Ba-137m, ~"
            f"{BA137_GROUND_BRANCH * 100:.1f}% direct to ground) must "
            f"come from a cited evaluation, and an age is a DURATION: "
            f"without a formation epoch and a measurement epoch it "
            f"cannot be turned into a calendar date. Declare all "
            f"{len(MANDATORY_DECLARATIONS)} fields and the closed "
            f"system, or the number stays an ANALYTIC_MODEL output.")
    return {
        "age_years": result.age_years,
        "ratio_R": str(result.ratio_R),
        "ratio_orientation": result.ratio_orientation,
        "t_half_years": result.t_half_years,
        "closed_system_declared": True,
        "declarations": {name: getattr(result, name)
                         for name in MANDATORY_DECLARATIONS},
        "evidence_class": result.evidence_class.value,
        "measured_here": "nothing",
        "note": (
            "declared, not verified: this module cannot check any of "
            "these declarations against a sample it never had"),
    }


def branching_note() -> dict:
    """The Cs-137 branching, stated as data to be cited, not assumed."""
    return {
        "via_Ba137m": BA137M_BRANCH,
        "direct_to_Ba137_ground": BA137_GROUND_BRANCH,
        "sums_to_one": abs(
            BA137M_BRANCH + BA137_GROUND_BRANCH - 1.0) < 1e-12,
        "isomer_note": (
            "Ba-137m is an isomeric state that relaxes to the Ba-137 "
            "GROUND state (the 661.7 keV gamma). Both branches end at "
            "Ba-137, so the total daughter inventory is insensitive to "
            "the split -- but any GAMMA-COUNTING measurement sees only "
            "the Ba-137m branch and must be corrected by it"),
        "must_be_declared": (
            "evaluations differ in the last digit (94.6/5.4 vs "
            "94.7/5.3). A branching ratio is cited data, never an "
            "assumption baked into a result"),
        "source_reference": PRIMARY_SOURCES[1],
    }


# --- Part 2: the orientation audit --------------------------------------

@dataclass(frozen=True)
class RatioCandidate:
    """A neutral, public label for a supplied numeric pair.

    The pair is carried as two integers with no claimed referent, no
    units, and no orientation. ``forward`` and ``inverse`` are both
    available because the data does not say which one was meant.
    """

    label: str
    a: int
    b: int
    note: str = ""

    @property
    def forward(self) -> Fraction:
        return Fraction(self.a, self.b)

    @property
    def inverse(self) -> Fraction:
        return Fraction(self.b, self.a)


#: Public neutral alias for the supplied pair. No referent is claimed.
ISOTOPE_RATIO_CANDIDATE_A = RatioCandidate(
    label="ISOTOPE_RATIO_CANDIDATE_A",
    a=192,
    b=55,
    note=("a supplied numeric pair, carried under a neutral label. "
          "192/55 = 3.4909090909090907..., 55/192 = "
          "0.2864583333333333...; which of the two (if either) is a "
          "daughter/parent number ratio is NOT stated by the numbers"),
)


def _orientation_leg(numer: int, denom: int, label: str,
                     t_half: float) -> dict:
    R = Fraction(numer, denom)
    one_plus = 1 + R
    return {
        "orientation": label,
        "ratio_exact": str(R),
        "ratio_float": float(R),
        "one_plus_R_exact": str(one_plus),
        "age_years": coarse_age(R, t_half),
    }


def audit_ratio_orientations(
        a: int, b: int,
        t_half: float = CS137_HALF_LIFE_YEARS) -> dict:
    """Report the age for BOTH orientations of a supplied pair.

    ``R = a/b`` and ``R = b/a`` are both admissible readings of a
    reported ratio, and they give different ages. This returns both,
    with exact rationals, and chooses neither. Choosing requires a
    stated reporting convention from the source -- never a preference
    about the resulting date.
    """
    if a <= 0 or b <= 0:
        raise IsotopeError(
            "an orientation audit needs two positive integers")
    fwd = _orientation_leg(a, b, f"R = {a}/{b}", t_half)
    inv = _orientation_leg(b, a, f"R = {b}/{a}", t_half)
    return {
        "a": a,
        "b": b,
        "t_half_years": t_half,
        "forward": fwd,
        "inverse": inv,
        "ages_differ": fwd["age_years"] != inv["age_years"],
        "age_difference_years": abs(fwd["age_years"] - inv["age_years"]),
        "orientation_chosen": None,
        "orientation_status": "UNDECLARED_BY_DESIGN",
        "coarse_interval_years": (min(fwd["age_years"], inv["age_years"]),
                                  max(fwd["age_years"], inv["age_years"])),
        "verdict": "ORIENTATION_NOT_DETERMINED_BY_THE_DATA",
        "note": (
            "both legs are reported because the pair does not carry its "
            "own convention. The spread between them IS the coarse "
            "uncertainty, and it is not narrowed by preferring one"),
    }


def refuse_orientation_chosen_from_desired_year(
        a: int, b: int,
        desired_year: float | int | None = None,
        t_half: float = CS137_HALF_LIFE_YEARS) -> None:
    """Refuse to pick the orientation that lands on a nicer date.

    Both orientations are arithmetically valid. Selecting between them
    by which one produces a preferred year is choosing the convention
    from the conclusion: the "confirmation" is then guaranteed by
    construction and carries no information.
    """
    audit = audit_ratio_orientations(a, b, t_half)
    raise IsotopeError(
        f"orientation may not be chosen from a desired year "
        f"({desired_year!r}). {audit['forward']['orientation']} gives "
        f"{audit['forward']['age_years']:.6g} a and "
        f"{audit['inverse']['orientation']} gives "
        f"{audit['inverse']['age_years']:.6g} a; both are valid "
        f"arithmetic and the data states no convention. Picking the leg "
        f"whose age lands nearer a preferred date fits the convention "
        f"to the answer -- a free parameter spent on the conclusion, "
        f"which makes the agreement uninformative. Supply the reporting "
        f"convention from the source, or report both.")


# --- Part 3: the fine phase and its aliases ------------------------------

def cs133_definition() -> dict:
    """The clock isotope, reported as a DEFINITION with zero error."""
    return {
        "nuclide": "Cs-133",
        "system": IsotopeSystem.CS133_CLOCK.value,
        "hyperfine_hz": CS133_HYPERFINE_HZ,
        "is_exact_integer": CS133_HYPERFINE_HZ == 9_192_631_770,
        "evidence_class": EvidenceClass.DEFINITION.value,
        "uncertainty": 0,
        "uncertainty_kind": "ZERO_BY_DEFINITION",
        "stable": True,
        "measured_here": "nothing",
        "source_reference": PRIMARY_SOURCES[0],
        "note": (
            "this integer DEFINES the second; it is not a measurement "
            "with an error bar and it is not a date. A clock tells you "
            "how long, never how long ago"),
    }


def rational_gcd(x: Fraction, y: Fraction) -> Fraction:
    """Greatest common divisor of two positive rationals.

    ``gcd(p1/q1, p2/q2) = gcd(p1 q2, p2 q1) / (q1 q2)``. For two
    carriers this is the frequency whose period is the LEAST COMMON
    period of the pair -- the rate at which a joint phase condition
    repeats.
    """
    if x <= 0 or y <= 0:
        raise IsotopeError("rational_gcd needs two positive rationals")
    return Fraction(
        math.gcd(x.numerator * y.denominator, y.numerator * x.denominator),
        x.denominator * y.denominator)


@dataclass(frozen=True)
class AliasSet:
    """The admissible whole-cycle counts over a coarse interval."""

    t_lo_s: Fraction
    t_hi_s: Fraction
    carrier_hz: Fraction
    n_min: int
    n_max: int
    count: int
    enumerated: tuple[int, ...] | None
    truncated: bool
    note: str = ""

    def is_unique(self) -> bool:
        return self.count == 1


def integer_cycle_aliases(
        t_lo: Fraction | float | int,
        t_hi: Fraction | float | int,
        f: Fraction | float | int,
        max_enumerate: int = MAX_ENUMERATED_ALIASES) -> AliasSet:
    """All admissible whole-cycle counts ``n`` for carrier ``f`` on
    ``[t_lo, t_hi]`` (seconds).

    A coherent carrier fixes the phase, and phase is known only modulo a
    whole cycle. Every integer ``n`` with ``t_lo <= n/f <= t_hi`` is an
    admissible cycle count, so the coarse interval times the carrier
    frequency IS the alias count. For the cesium line and any interval
    wider than a nanosecond this is astronomically large; rather than
    building a list that could not be held, the set is then reported as
    its count together with the ``n``-range (``truncated=True``).
    """
    lo, hi, fr = _as_fraction(t_lo), _as_fraction(t_hi), _as_fraction(f)
    if fr <= 0:
        raise IsotopeError("a carrier frequency must be positive")
    if lo < 0:
        raise IsotopeError("a coarse interval cannot start before zero")
    if hi < lo:
        raise IsotopeError(
            f"coarse interval is inverted: t_hi ({float(hi):g} s) < "
            f"t_lo ({float(lo):g} s)")
    n_min = math.ceil(lo * fr)
    n_max = math.floor(hi * fr)
    count = max(0, n_max - n_min + 1)
    if 0 < count <= max_enumerate:
        return AliasSet(lo, hi, fr, n_min, n_max, count,
                        tuple(range(n_min, n_max + 1)), False,
                        "alias set enumerated in full")
    return AliasSet(
        lo, hi, fr, n_min, n_max, count, None, count > max_enumerate,
        (f"alias count {count} exceeds max_enumerate={max_enumerate}; "
         f"reported as a count and an n-range instead of a list")
        if count > max_enumerate else "no admissible integer n")


def aliases_with_second_carrier(
        t_lo: Fraction | float | int,
        t_hi: Fraction | float | int,
        f1: Fraction | float | int = CS133_HYPERFINE_HZ,
        f2: Fraction | float | int = DEFAULT_SECOND_CARRIER_HZ,
        max_enumerate: int = MAX_ENUMERATED_ALIASES) -> dict:
    """Show that a second coherent carrier REDUCES aliases but does not
    make the epoch unique.

    A phase reading on one carrier repeats every ``1/f1``; on a second
    it repeats every ``1/f2``. Times consistent with BOTH readings
    repeat at the least common period of the pair, ``1/gcd(f1, f2)`` --
    the Chinese-remainder structure. So the joint alias set is the alias
    set of an EFFECTIVE carrier at ``gcd(f1, f2)``, and the count drops
    by the factor ``f1 / gcd(f1, f2)``. It drops; it does not reach one.

    The reduction is exact only for commensurate (rational-ratio)
    carriers. For an incommensurate pair the common period is infinite
    in principle, but any real phase reading has a tolerance, and the
    tolerance restores a dense admissible set -- the ambiguity moves,
    it does not vanish.
    """
    a, b = _as_fraction(f1), _as_fraction(f2)
    if a <= 0 or b <= 0:
        raise IsotopeError("carrier frequencies must be positive")
    if a == b:
        raise IsotopeError(
            f"the second carrier ({float(b):g} Hz) equals the first; an "
            f"identical carrier is not a second observable and removes "
            f"no aliases")
    single = integer_cycle_aliases(t_lo, t_hi, a, max_enumerate)
    second = integer_cycle_aliases(t_lo, t_hi, b, max_enumerate)
    f_eff = rational_gcd(a, b)
    joint = integer_cycle_aliases(t_lo, t_hi, f_eff, max_enumerate)
    reduced = joint.count < single.count
    return {
        "carrier_1_hz": str(a),
        "carrier_2_hz": str(b),
        "effective_joint_carrier_hz": str(f_eff),
        "common_period_s": float(1 / f_eff),
        "single_carrier_alias_count": single.count,
        "second_carrier_alias_count": second.count,
        "joint_alias_count": joint.count,
        "joint_n_range": (joint.n_min, joint.n_max),
        "alias_count_reduced": reduced,
        "reduction_factor": (single.count / joint.count
                             if joint.count else float("inf")),
        "unique": joint.is_unique(),
        "still_ambiguous": joint.count > 1,
        "verdict": ("ALIASES_REDUCED_NOT_RESOLVED" if joint.count > 1
                    else "SINGLE_ALIAS_UNDER_THIS_MODEL"),
        "note": (
            "a second coherent carrier is a real constraint and it "
            "removes most aliases, but the survivors repeat at the "
            "common period 1/gcd(f1, f2). For any interval wide enough "
            "to have needed a coarse chronometer in the first place, "
            "the survivor count stays far above one"),
    }


def refuse_unique_epoch(alias_count: int,
                        independent_coarse_anchor: str | None = None,
                        second_coherent_observable: str | None = None,
                        claimed_epoch_year: int | None = None) -> None:
    """Refuse a unique six-digit-year epoch.

    Naming one year requires the alias set to collapse to a single
    admissible whole-cycle count, which in turn requires an independent
    coarse anchor AND a second coherent observable. Neither exists in
    this environment. A six-digit year quoted off a phase that is
    ambiguous over billions of cycles states more digits than the
    arithmetic has.
    """
    if alias_count < 0:
        raise IsotopeError("an alias count cannot be negative")
    anchor_ok = bool(independent_coarse_anchor) \
        and independent_coarse_anchor != UNDECLARED
    second_ok = bool(second_coherent_observable) \
        and second_coherent_observable != UNDECLARED
    if alias_count == 1 and anchor_ok and second_ok:
        return
    missing = []
    if not anchor_ok:
        missing.append("independent_coarse_anchor")
    if not second_ok:
        missing.append("second_coherent_observable")
    if alias_count != 1:
        missing.append(f"alias_count == 1 (have {alias_count})")
    raise IsotopeError(
        f"a unique epoch is refused"
        + (f" (claimed year {claimed_epoch_year!r})"
           if claimed_epoch_year is not None else "")
        + f": {alias_count} admissible whole-cycle counts remain, and "
        f"the following are missing: {missing}. A six-digit year is a "
        f"six-significant-figure claim; it may not be read off a "
        f"coherent phase, because a phase is known only modulo one "
        f"cycle and the coarse interval spans an enormous number of "
        f"them. Collapsing the set needs an INDEPENDENT coarse anchor "
        f"(not the same isotope pair again) and a SECOND coherent "
        f"observable, and even then the survivors repeat at the common "
        f"period. {DEFAULT_VERDICT}.")


# --- report --------------------------------------------------------------

def isotope_report() -> dict:
    """The standing result: two typed systems, and no unique epoch."""
    audit = audit_ratio_orientations(
        ISOTOPE_RATIO_CANDIDATE_A.a, ISOTOPE_RATIO_CANDIDATE_A.b)
    lo_years, hi_years = audit["coarse_interval_years"]
    demo = aliases_with_second_carrier(
        lo_years * JULIAN_YEAR_S, hi_years * JULIAN_YEAR_S)
    undeclared = coarse_age_result(ISOTOPE_RATIO_CANDIDATE_A.forward)
    return {
        "what_this_is": (
            "a Cs-137/Ba-137 coarse-age model, an orientation audit of "
            "a supplied numeric pair, and an integer-cycle alias count "
            "for the Cs-133 fine phase -- three separate arguments, "
            "kept separate"),
        "evidence_class": "ANALYTIC_MODEL_ON_EVALUATED_LITERATURE",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "typed_systems": [
            {"nuclide": t.nuclide,
             "system": t.system.value,
             "evidence_class": t.evidence_class.value,
             "stable": t.stable,
             "observable": t.observable,
             "value": str(t.value) if t.value is not None else None,
             "unit": t.unit,
             "uncertainty": (str(t.uncertainty)
                             if t.uncertainty is not None else None),
             "does_not_license": t.does_not_license,
             "source_reference": t.source_reference}
            for t in TYPED_ISOTOPES],
        "cs133_definition": cs133_definition(),
        "cs137_half_life_years": CS137_HALF_LIFE_YEARS,
        "cs137_half_life_exact": str(CS137_HALF_LIFE_YEARS_EXACT),
        "coarse_age_model": {
            "formula": "t = T_half * log2(1 + R), R = N_Ba_rad / N_Cs",
            "inverse_convention": "R = 1 / (N_Cs / N_Ba)",
            "evidence_class": EvidenceClass.ANALYTIC_MODEL.value,
            "mandatory_declarations": list(MANDATORY_DECLARATIONS),
            "undeclared_by_default": list(undeclared.undeclared_fields()),
            "closed_system_declared": undeclared.closed_system_declared,
            "branching": branching_note(),
            "ba137_natural_abundance": BA137_NATURAL_ABUNDANCE,
        },
        "ratio_candidate": {
            "label": ISOTOPE_RATIO_CANDIDATE_A.label,
            "a": ISOTOPE_RATIO_CANDIDATE_A.a,
            "b": ISOTOPE_RATIO_CANDIDATE_A.b,
            "forward_exact": str(ISOTOPE_RATIO_CANDIDATE_A.forward),
            "inverse_exact": str(ISOTOPE_RATIO_CANDIDATE_A.inverse),
            "note": ISOTOPE_RATIO_CANDIDATE_A.note,
        },
        "orientation_audit": audit,
        "alias_demonstration": demo,
        "refusals_available": [
            "refuse_isotope_conflation (Cs-133 clock vs Cs-137 decay)",
            "refuse_age_without_closed_system_declaration",
            "refuse_orientation_chosen_from_desired_year",
            "refuse_unique_epoch",
        ],
        "primary_sources": list(PRIMARY_SOURCES),
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not count a sample, measure an activity, compare a "
            "clock, or date anything. It does not say that the supplied "
            "pair is an isotope ratio, that either orientation is the "
            "right one, or that the resulting years refer to a calendar "
            "date. It does not merge Cs-133 with Cs-137: one is a "
            "frequency DEFINITION with zero uncertainty and the other "
            "an evaluated decay rate, and a shared element name is not "
            "a bridge between them. Above all it does not name an "
            "epoch: a coherent phase is ambiguous modulo one cycle, a "
            "second carrier reduces the alias set without collapsing "
            "it, and so a unique six-digit year remains forbidden "
            f"({DEFAULT_VERDICT})."),
    }
