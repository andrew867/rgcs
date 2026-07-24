"""P40 — the epoch solver: a time consistent with periodic phases is an
ALIAS CLASS, never a unique decoded timestamp.

Several periodic signals are observed. Each has a known period ``P_i``
and an observed phase, and the phase fixes the epoch only *modulo one
whole cycle*: the residue ``t ≡ r_i (mod P_i)`` is all a single periodic
signal can say about ``t``. Combining several such residues is a
generalized Chinese-Remainder / phase-alignment problem, and
:func:`solve_epoch` solves it exactly (rational arithmetic, no floating
drift at a claim boundary).

**Aliasing is the whole point.** A periodic constraint repeats, so the
joint solution set does too: consistent epochs recur at intervals of the
LEAST COMMON MULTIPLE of the periods (the beat period of the system).
:func:`epoch_alias_set` therefore returns MORE THAN ONE candidate epoch
across any window wider than that beat period, and the members are spaced
by exactly that alias period. A single epoch cannot be uniquely decoded
from periodic phases alone: the arithmetic yields a residue class, and a
residue class is a set.

To show the solver is not merely blind, a PLANTED epoch is recovered:
generate the phases a known ``t*`` would produce, hand them back, and the
solver returns ``t*`` modulo the alias period (the POWER control).

Two refusals guard the two ways this could be over-read.
:func:`refuse_epoch_as_unique_time` refuses to report the base solution
as *the* time; it is the first member of an alias class, and the class is
the result. :func:`refuse_phase_match_as_timestamp_authentication`
refuses to read a phase agreement as authentication of an external
source: aligning to a periodic phase proves consistency with a repeating
pattern, not the provenance of a signal.

Every epoch, phase, and window is PASSED IN explicitly. Nothing here
reads a wall clock, so every result is deterministic and reproducible.
The standing verdict is ``EPOCH_SOLVER_ALIAS_LIMITED``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

#: The standing verdict. The solver returns an alias class, not a time.
VERDICT = "EPOCH_SOLVER_ALIAS_LIMITED"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Enumerating an alias set is capped so a pathological window cannot ask
#: for an unbounded list.
MAX_ENUMERATED_EPOCHS = 4096


class EpochSolveError(RuntimeError):
    """Raised when an epoch is asked to be something a periodic phase
    cannot give: a unique time, an authentication, or a solution to an
    inconsistent or malformed set of constraints."""


class ClaimClass(Enum):
    """How a statement in this module is entitled to be believed."""

    DERIVED_ARITHMETIC = "DERIVED_ARITHMETIC"
    ANALYTIC_MODEL = "ANALYTIC_MODEL"
    RETROSPECTIVE_NUMERIC_MATCH = "RETROSPECTIVE_NUMERIC_MATCH"
    BLOCKED_MISSING_INPUT = "BLOCKED_MISSING_INPUT"
    UNSUPPORTED = "UNSUPPORTED"


# --- exact rational helpers --------------------------------------------

def _as_fraction(x: Fraction | float | int) -> Fraction:
    """Exact rational view of a scalar; floats are read exactly."""
    if isinstance(x, Fraction):
        return x
    if isinstance(x, bool):                       # bool is an int; refuse it
        raise EpochSolveError("a period or phase must be a real number")
    if isinstance(x, int):
        return Fraction(x)
    if isinstance(x, float):
        if not math.isfinite(x):
            raise EpochSolveError("a period or phase must be finite")
        return Fraction(x)
    raise EpochSolveError(f"cannot read {x!r} as a rational")


def _rational_lcm(a: Fraction, b: Fraction) -> Fraction:
    """Least common multiple of two positive rationals.

    ``lcm(p1/q1, p2/q2)`` is the smallest positive rational that is an
    integer multiple of both. It is the period at which two phase
    conditions realign -- the beat period of the pair.
    """
    if a <= 0 or b <= 0:
        raise EpochSolveError("rational lcm needs two positive rationals")
    # lcm as (a*b)/gcd, all in exact rational arithmetic.
    g = Fraction(
        math.gcd(a.numerator * b.denominator, b.numerator * a.denominator),
        a.denominator * b.denominator)
    return a * b / g


# --- the constraints ----------------------------------------------------

@dataclass(frozen=True)
class PhaseConstraint:
    """One periodic observation: ``t ≡ phase_offset (mod period)``.

    ``phase_offset`` is the observed residue, in the same time unit as
    ``period`` and in ``[0, period)``. A phase given as a fraction of a
    cycle is turned into an offset by :func:`constraint_from_phase`.
    """

    period: Fraction
    phase_offset: Fraction
    label: str = ""

    def __post_init__(self) -> None:
        p = _as_fraction(self.period)
        o = _as_fraction(self.phase_offset)
        if p <= 0:
            raise EpochSolveError(
                f"period must be positive (got {self.period!r})")
        if not (0 <= o < p):
            raise EpochSolveError(
                f"phase_offset {o} must lie in [0, period={p})")
        object.__setattr__(self, "period", p)
        object.__setattr__(self, "phase_offset", o)


def constraint_from_phase(period: Fraction | float | int,
                          phase_fraction: Fraction | float | int,
                          label: str = "") -> PhaseConstraint:
    """Build a constraint from a phase given as a FRACTION of one cycle.

    ``phase_fraction`` in ``[0, 1)`` means the signal is that fraction of
    the way through its cycle at the epoch, so the offset residue is
    ``phase_fraction * period``.
    """
    p = _as_fraction(period)
    ph = _as_fraction(phase_fraction)
    if not (0 <= ph < 1):
        raise EpochSolveError(
            f"phase_fraction {ph} must lie in [0, 1)")
    return PhaseConstraint(p, ph * p, label=label)


def phase_offset_of(epoch: Fraction | float | int,
                    period: Fraction | float | int) -> Fraction:
    """The residue ``epoch mod period`` a periodic signal would show.

    Exact rational modulo. Used to synthesise the phases a KNOWN epoch
    produces, for the planted-epoch power control.
    """
    t = _as_fraction(epoch)
    p = _as_fraction(period)
    if p <= 0:
        raise EpochSolveError("period must be positive")
    return t - (t // p) * p


# --- generalized Chinese-Remainder over the residues --------------------

def _crt_pair(r1: int, m1: int, r2: int, m2: int) -> tuple[int, int] | None:
    """Combine ``t≡r1 (mod m1)`` and ``t≡r2 (mod m2)`` (moduli need not
    be coprime). Returns ``(r, lcm)`` or ``None`` if inconsistent."""
    g = math.gcd(m1, m2)
    if (r2 - r1) % g != 0:
        return None
    lcm = m1 // g * m2
    # step to add to r1 (in units of m1) to reach r2 modulo m2
    diff = (r2 - r1) // g
    inv = pow(m1 // g, -1, m2 // g)
    k = (diff * inv) % (m2 // g)
    r = (r1 + m1 * k) % lcm
    return r, lcm


@dataclass(frozen=True)
class EpochSolution:
    """The result of solving: a residue class, not a point.

    ``base_epoch`` is the smallest non-negative representative; the full
    solution is ``base_epoch + k * alias_period`` for every integer ``k``.
    ``consistent`` is False when the phases cannot all be satisfied at
    once (then ``base_epoch`` is ``None``).
    """

    base_epoch: Fraction | None
    alias_period: Fraction
    consistent: bool
    n_constraints: int
    periods: tuple[Fraction, ...]
    claim_class: ClaimClass = ClaimClass.DERIVED_ARITHMETIC
    note: str = ""

    def is_unique(self) -> bool:
        """A residue class is never a single time: always False."""
        return False


def alias_period(constraints: tuple[PhaseConstraint, ...] | list) -> Fraction:
    """The beat period at which consistent epochs recur: ``lcm(periods)``.

    This is the spacing of the alias set. It is a property of the
    periods alone -- the phases only pick which residue class, never how
    far apart its members sit.
    """
    cons = tuple(constraints)
    if not cons:
        raise EpochSolveError("need at least one periodic constraint")
    period = cons[0].period
    for c in cons[1:]:
        period = _rational_lcm(period, c.period)
    return period


def solve_epoch(constraints: tuple[PhaseConstraint, ...] | list
                ) -> EpochSolution:
    """Solve for the epoch class consistent with all periodic phases.

    Each constraint contributes ``t ≡ r_i (mod P_i)``. Scaling every
    period and residue by their common denominator turns the system into
    an integer generalized-CRT problem; the solution is a single residue
    modulo ``lcm(P_i)``, scaled back to rational time. The result is a
    CLASS: one representative ``base_epoch`` plus the ``alias_period`` at
    which it repeats. It is never a unique time -- see
    :func:`refuse_epoch_as_unique_time`.
    """
    cons = tuple(constraints)
    if not cons:
        raise EpochSolveError("need at least one periodic constraint")
    periods = tuple(c.period for c in cons)
    alias = alias_period(cons)

    # Common denominator so periods and residues are all integers.
    den = 1
    for c in cons:
        den = den // math.gcd(den, c.period.denominator) * c.period.denominator
        den = den // math.gcd(den, c.phase_offset.denominator) \
            * c.phase_offset.denominator

    r, m = 0, 1                                   # t' ≡ 0 (mod 1) to start
    for c in cons:
        pi = int(c.period * den)
        ri = int(c.phase_offset * den) % pi
        combined = _crt_pair(r, m, ri, pi)
        if combined is None:
            return EpochSolution(
                base_epoch=None,
                alias_period=alias,
                consistent=False,
                n_constraints=len(cons),
                periods=periods,
                note=(
                    "the periodic phases are mutually inconsistent: no "
                    "epoch satisfies them all, so the alias class is "
                    "empty. This is a definite arithmetic result, not a "
                    "date"),
            )
        r, m = combined

    base = Fraction(r, den)
    period_span = Fraction(m, den)                # == alias, by construction
    return EpochSolution(
        base_epoch=base,
        alias_period=period_span,
        consistent=True,
        n_constraints=len(cons),
        periods=periods,
        note=(
            "a residue class: every base_epoch + k*alias_period is an "
            "equally valid solution. The phases select the class; they "
            "cannot select a member"),
    )


def epoch_alias_set(constraints: tuple[PhaseConstraint, ...] | list,
                    window: tuple[Fraction | float | int,
                                  Fraction | float | int],
                    max_members: int = MAX_ENUMERATED_EPOCHS
                    ) -> tuple[Fraction, ...]:
    """Every candidate epoch inside ``window`` -- a SET, not a point.

    Solves the constraints, then walks the residue class
    ``base_epoch + k * alias_period`` across ``[lo, hi]``. For any window
    wider than the alias period this returns MORE THAN ONE epoch, and the
    members are spaced by exactly the alias period. That plurality is the
    deliverable: a periodic phase decodes to a class, and reporting one
    member as the epoch would hide the rest rather than eliminate them.
    """
    lo = _as_fraction(window[0])
    hi = _as_fraction(window[1])
    if hi < lo:
        raise EpochSolveError(
            f"window is inverted: hi ({float(hi):g}) < lo ({float(lo):g})")
    solution = solve_epoch(constraints)
    if not solution.consistent or solution.base_epoch is None:
        return ()
    period = solution.alias_period
    if period <= 0:
        raise EpochSolveError("alias period must be positive")
    # smallest k with base + k*period >= lo
    k = math.ceil((lo - solution.base_epoch) / period)
    out: list[Fraction] = []
    t = solution.base_epoch + k * period
    while t <= hi:
        if t >= lo:
            out.append(t)
        if len(out) > max_members:
            raise EpochSolveError(
                f"window admits more than max_members={max_members} "
                f"alias epochs; narrow the window or raise the cap")
        t += period
    return tuple(out)


def alias_spacing(epochs: tuple[Fraction, ...]) -> tuple[Fraction, ...]:
    """Consecutive gaps in an alias set. For a valid set they are all
    equal to the alias period."""
    return tuple(epochs[i + 1] - epochs[i] for i in range(len(epochs) - 1))


# --- the planted-epoch power control ------------------------------------

def plant_and_recover(planted_epoch: Fraction | float | int,
                      periods: tuple[Fraction | float | int, ...] | list
                      ) -> dict:
    """Plant a known epoch, synthesise its phases, and recover it.

    For each period, the residue a KNOWN ``t*`` produces is
    ``t* mod P``. Handed those residues back with no other information,
    the solver returns ``t*`` reduced into ``[0, alias_period)`` -- i.e.
    ``t*`` modulo the alias period, which is the most any periodic phase
    can pin down. This is the POWER control: the solver DOES recover a
    planted epoch (modulo the alias period), so its failure to name a
    single absolute time elsewhere is a property of periodicity, not a
    weakness of the solver.
    """
    t_star = _as_fraction(planted_epoch)
    ps = [_as_fraction(p) for p in periods]
    if len(ps) < 2:
        raise EpochSolveError(
            "the planted control needs at least two periods to alias over")
    constraints = tuple(
        PhaseConstraint(p, phase_offset_of(t_star, p), label=f"P{i}")
        for i, p in enumerate(ps))
    solution = solve_epoch(constraints)
    alias = solution.alias_period
    expected = t_star - (t_star // alias) * alias   # t* mod alias_period
    recovered = solution.base_epoch
    return {
        "planted_epoch": str(t_star),
        "alias_period": str(alias),
        "expected_epoch_mod_alias": str(expected),
        "recovered_base_epoch": str(recovered),
        "recovered_modulo_alias": recovered == expected,
        "consistent": solution.consistent,
        "claim_class": ClaimClass.DERIVED_ARITHMETIC.value,
        "note": (
            "the solver recovers the planted epoch modulo the alias "
            "period. It cannot recover the absolute epoch, because the "
            "phases repeat every alias period and carry no cycle count"),
    }


# --- the two refusals ---------------------------------------------------

def refuse_epoch_as_unique_time(solution: EpochSolution | None = None,
                                claimed_epoch: object = None) -> None:
    """Refuse to report an epoch solution as a unique decoded timestamp.

    An epoch solved from periodic phases is a residue class:
    ``base_epoch + k * alias_period`` for every integer ``k``. The base
    representative is the FIRST member of that class, not the time. There
    is no arithmetic in a set of periodic phases that names ``k``, so
    quoting the base as *the* epoch discards the rest of the class rather
    than eliminating it. Always raises.
    """
    if solution is not None and not isinstance(solution, EpochSolution):
        raise EpochSolveError(
            "refuse_epoch_as_unique_time takes an EpochSolution or None")
    detail = ""
    if solution is not None:
        detail = (f" The class here is base {solution.base_epoch} + "
                  f"k*{solution.alias_period}.")
    raise EpochSolveError(
        f"refused: an epoch decoded from periodic phases is an ALIAS "
        f"CLASS, not a unique time"
        + (f" (claimed {claimed_epoch!r})" if claimed_epoch is not None
           else "")
        + f".{detail} Consistent solutions recur at the least common "
        f"multiple of the periods -- the alias period -- and no residue "
        f"names the integer number of alias periods that have elapsed. "
        f"Report epoch_alias_set(), including its size and spacing, not a "
        f"single timestamp. " + VERDICT + ".")


def refuse_phase_match_as_timestamp_authentication(
        matched_phase: object = None,
        source: object = None) -> None:
    """Refuse to read a phase agreement as authentication of a source.

    A phase that aligns with a periodic pattern proves the epoch is
    consistent with that repeating pattern -- and consistency with a
    pattern that repeats every alias period is shared by an entire class
    of epochs and by anything else with the same period. It says nothing
    about WHO produced a signal or WHEN, in the sense of provenance. A
    timestamp is authenticated by a chain of custody and a signature over
    content, never by a phase landing where a period says it must. Always
    raises.
    """
    raise EpochSolveError(
        f"refused: a phase match is not timestamp authentication"
        + (f" (source {source!r})" if source is not None else "")
        + (f" (phase {matched_phase!r})" if matched_phase is not None
           else "")
        + ". Aligning to a periodic phase demonstrates consistency with a "
        "pattern that repeats every alias period; every member of that "
        "alias class matches equally, and so would any independent signal "
        "of the same period. Consistency with a repeating pattern is not "
        "provenance: authentication requires a signature over content and "
        "a custody chain, which a phase cannot supply. " + VERDICT + ".")


# --- report -------------------------------------------------------------

def epochsolve_report() -> dict:
    """The standing result: the solver returns alias classes, not times."""
    # A small, fully deterministic worked example: periods 3 and 4, a
    # planted epoch of 7. lcm(3,4)=12, so 7, 19, 31, ... are all valid.
    demo_periods = (Fraction(3), Fraction(4))
    power = plant_and_recover(Fraction(7), demo_periods)
    constraints = (
        PhaseConstraint(Fraction(3), phase_offset_of(Fraction(7),
                                                     Fraction(3))),
        PhaseConstraint(Fraction(4), phase_offset_of(Fraction(7),
                                                     Fraction(4))),
    )
    solution = solve_epoch(constraints)
    aliases = epoch_alias_set(constraints, (Fraction(0), Fraction(40)))
    spacings = alias_spacing(aliases)
    return {
        "what_this_is": (
            "an epoch solver over periodic phase constraints. It returns "
            "the residue class consistent with all phases -- a base epoch "
            "and the alias period at which it repeats -- and never a "
            "unique decoded timestamp"),
        "claim_class": ClaimClass.DERIVED_ARITHMETIC.value,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "example_periods": [str(p) for p in demo_periods],
        "example_alias_period": str(solution.alias_period),
        "example_base_epoch": str(solution.base_epoch),
        "example_alias_set": [str(t) for t in aliases],
        "example_alias_set_size": len(aliases),
        "example_alias_spacings": [str(s) for s in spacings],
        "alias_set_has_more_than_one_member": len(aliases) > 1,
        "spacings_equal_alias_period": all(
            s == solution.alias_period for s in spacings),
        "power_control": power,
        "refusals_available": [
            "refuse_epoch_as_unique_time (always raises)",
            "refuse_phase_match_as_timestamp_authentication (always raises)",
        ],
        "verdict": VERDICT,
        "what_this_does_not_say": (
            "It does not name a unique time, decode a timestamp, or "
            "authenticate a source. A periodic phase fixes an epoch only "
            "modulo one whole cycle, so several phases together fix only "
            "a residue class that recurs at the least common multiple of "
            "the periods -- the alias period. The solver recovers a "
            "PLANTED epoch modulo that alias period (which shows it has "
            "power, not that it decoded an absolute time), and it reports "
            "the class as a set. No wall clock is read anywhere; every "
            "epoch, phase and window is passed in, so every result is "
            "deterministic. Nothing here is measured."),
    }
