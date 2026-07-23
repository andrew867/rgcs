"""P06 — crystal-derived carrier search: a target-fitted candidate, priced.

A computed crystal mode is offered as the "carrier" behind a grouped
caesium number. The arithmetic is clean, and this module keeps it exact
(``Fraction``) so nothing rounds at a claim boundary. It then prices the
claim, because a carrier chosen **after** the target was known is fitted
to that target and carries no evidential weight until it survives three
things it has not yet survived: a look-elsewhere null, an independent
mode it was not selected on, and a physical correction mechanism that
explains the residual rather than absorbing it.

The high-priority candidate, audited exactly:

    f_crystal            = 13772.28 Hz     (N=7 finest computed first mode)
    f_crystal * 2/3      =  9181.52 Hz
    9192 - 9181.52       =    10.48 Hz     (residual to grouped 9192)
    63/6                 =    10.50 Hz     (= 21/2, exact)
    9181.52 + 63/6       =  9192.02 Hz
    9192 * 3/2           = 13788.00 Hz     (the exact base for 9192)

**A discrepancy in the source pack, stated plainly -- and its
resolution.** The pack originally described 13788.00 Hz as "0.03 Hz below
the finest computational result". It is not. Computed here exactly,

    13788.00 - 13772.28 = 15.72 Hz

so the exact base for 9192 sits **15.72 Hz ABOVE** the finest computed
mode, not 0.03 Hz below it -- a sign error and a factor of ~500 in
magnitude. That correction was reported rather than quietly absorbed, and
the R11 delta then **confirmed and resolved it**: the frequency that
really is 0.03 Hz below the computed mode is a different number
altogether,

    13772.28 - 13772.25 = 0.03 Hz     (exact)

so ``NEAR_MODE_CANDIDATE_HZ = 13772.25`` is the registered 0.03-Hz-below
candidate, and 13788.00 is **not**. Both facts are carried:
``base_difference_hz`` (15.72, the exact base for 9192) and
``near_mode_difference_hz`` (0.03, the 13772.25 candidate). Neither is a
result -- 13772.25 is an arbitrary 0.03 Hz step away from a computed
mode, which is a statement about rounding, not about physics.

**The candidate is target-fitted.** ``2/3`` was chosen after 9192 was in
view. ``is_target_fitted`` records that, ``refuse_carrier_selected_after_
target`` refuses an unlabelled post-hoc selection, and every reported
candidate carries the flag.

**It is no better than chance.** The preregistered search grid -- four
registered base frequencies, four supplied rationals, nine operations
(literal multiplier, inverse multiplier, phase-only modulo, harmonic,
subharmonic, beat against the full Cs-133 frequency, beat against
grouped 9192 / 631 / 770), each overlaid with harmonic and subharmonic
orders 1..8 -- contains over two thousand expressions. With a grid that
large, a *random* target drawn from the same band is matched to the same
0.114% tolerance by SOME expression a large fraction of the time, so
``lookelsewhere_pvalue`` is not small and the verdict is
``NO_BETTER_THAN_CHANCE``. To show the search is not simply blind, a
POWER control plants a target that IS exactly a grid expression and
confirms it is recovered at zero residual.

**Long expressions are worth less.** ``description_length`` charges for
every integer and every operation used, so a match bought with a
convoluted expression is explicitly cheaper evidence than a short one.
The candidate's own expression is short; that is its only virtue, and it
is not enough.

Everything here is arithmetic. Nothing is measured, generated, driven,
or transmitted, and no crystal is claimed to carry anything.
"""

from __future__ import annotations

import bisect
import random
import re
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction

# --- public neutral alias ----------------------------------------------

#: Neutral public name for the audited high-priority candidate.
CRYSTAL_CARRIER_CANDIDATE_A = "CRYSTAL_CARRIER_CANDIDATE_A"

DEFAULT_VERDICT = "CRYSTAL_CARRIER_CANDIDATE_ARITHMETIC_ONLY"


class CarrierError(RuntimeError):
    """Raised when a carrier is given exactness or standing it has not earned."""


# --- the registered frequencies and the supplied rationals -------------

#: N=7 finest computed first mode, exact as written (344307/25 Hz).
F_CRYSTAL_N7_HZ = Fraction("13772.28")

REGISTERED_BASES: tuple[tuple[str, Fraction], ...] = (
    ("N7_FIRST_MODE", F_CRYSTAL_N7_HZ),
    ("F_4096", Fraction(4096)),
    ("F_20480", Fraction(20480)),
    ("F_32768", Fraction(32768)),
)

#: The supplied rationals, exact.
SUPPLIED_RATIONALS: tuple[Fraction, ...] = (
    Fraction(2, 3), Fraction(3, 4), Fraction(5, 6), Fraction(7, 2),
)

#: Cs-133 ground-state hyperfine transition frequency (SI definition).
CS133_HZ = 9192631770
#: The same digits, grouped as they were spoken.
GROUPED_9192 = 9192
GROUPED_631 = 631
GROUPED_770 = 770
GROUPED_REFS: tuple[int, ...] = (GROUPED_9192, GROUPED_631, GROUPED_770)

#: Harmonic / subharmonic orders overlaid on every core expression.
HARMONIC_ORDERS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 8)

#: Preregistered band random targets are drawn from, and the sampler.
SEARCH_LO_HZ = 1000.0
SEARCH_HI_HZ = 20000.0
N_SAMPLES = 2000
SEED = 13772


class CarrierOp(Enum):
    """How a supplied rational is applied to a registered base frequency."""

    LITERAL_MULTIPLIER = "LITERAL_MULTIPLIER"      # f * r
    INVERSE_MULTIPLIER = "INVERSE_MULTIPLIER"      # f / r
    PHASE_MODULO = "PHASE_MODULO"                  # f mod (f * r)
    HARMONIC = "HARMONIC"                          # f * numerator(r)
    SUBHARMONIC = "SUBHARMONIC"                    # f / denominator(r)
    BEAT_CS133_FULL = "BEAT_CS133_FULL"            # |f*r - 9192631770|
    BEAT_GROUPED = "BEAT_GROUPED"                  # |f*r - 9192|631|770


#: Description-length charge per operation, before integer costs.
OP_COST: dict[CarrierOp, int] = {
    CarrierOp.LITERAL_MULTIPLIER: 2,
    CarrierOp.INVERSE_MULTIPLIER: 3,
    CarrierOp.PHASE_MODULO: 6,
    CarrierOp.HARMONIC: 2,
    CarrierOp.SUBHARMONIC: 2,
    CarrierOp.BEAT_CS133_FULL: 4,
    CarrierOp.BEAT_GROUPED: 4,
}


# --- exact formatting helpers ------------------------------------------

def _decimal_str(x: Fraction) -> str:
    """Exact decimal text when the fraction terminates, else 'p/q'."""
    if x.denominator == 1:
        return str(x.numerator)
    d, twos, fives = x.denominator, 0, 0
    while d % 2 == 0:
        d //= 2
        twos += 1
    while d % 5 == 0:
        d //= 5
        fives += 1
    if d != 1:
        return f"{x.numerator}/{x.denominator}"
    places = max(twos, fives)
    scaled = x.numerator * 10 ** places // x.denominator
    sign = "-" if scaled < 0 else ""
    digits = str(abs(scaled)).rjust(places + 1, "0")
    return f"{sign}{digits[:-places]}.{digits[-places:]}"


def _exact_mod(x: Fraction, m: Fraction) -> Fraction:
    """Exact x mod m for positive m (Fraction floor division is exact)."""
    if m <= 0:
        raise CarrierError("phase modulus must be positive")
    return x - (x // m) * m


# --- one expression in the grid ----------------------------------------

@dataclass(frozen=True)
class CarrierExpression:
    """A single candidate expression: base, rational, operation, order.

    ``harmonic_n``/``harmonic_up`` overlay a harmonic (xN) or subharmonic
    (/N) order on the core value, so the same core expression appears at
    every preregistered order rather than only the one that happened to
    land near a target.
    """

    base_id: str
    base_hz: Fraction
    rational: Fraction
    op: CarrierOp
    harmonic_n: int = 1
    harmonic_up: bool = True
    beat_ref: int | None = None

    def core_value(self) -> Fraction:
        f, r = self.base_hz, self.rational
        if self.op is CarrierOp.LITERAL_MULTIPLIER:
            return f * r
        if self.op is CarrierOp.INVERSE_MULTIPLIER:
            return f / r
        if self.op is CarrierOp.PHASE_MODULO:
            return _exact_mod(f, f * r)
        if self.op is CarrierOp.HARMONIC:
            return f * r.numerator
        if self.op is CarrierOp.SUBHARMONIC:
            return f / r.denominator
        if self.op in (CarrierOp.BEAT_CS133_FULL, CarrierOp.BEAT_GROUPED):
            if self.beat_ref is None:
                raise CarrierError("beat operation needs a reference")
            return abs(f * r - Fraction(self.beat_ref))
        raise CarrierError(f"unknown operation {self.op!r}")

    def value(self) -> Fraction:
        """Exact value of the whole expression, harmonic order included."""
        v = self.core_value()
        if self.harmonic_n == 1:
            return v
        return (v * self.harmonic_n if self.harmonic_up
                else v / self.harmonic_n)

    def text(self) -> str:
        """Human-readable exact expression, e.g. '13772.28 * 2/3'."""
        f = _decimal_str(self.base_hz)
        r = f"{self.rational.numerator}/{self.rational.denominator}"
        if self.op is CarrierOp.LITERAL_MULTIPLIER:
            core = f"{f} * {r}"
        elif self.op is CarrierOp.INVERSE_MULTIPLIER:
            core = f"{f} / ({r})"
        elif self.op is CarrierOp.PHASE_MODULO:
            core = f"{f} mod ({f} * {r})"
        elif self.op is CarrierOp.HARMONIC:
            core = f"{f} * {self.rational.numerator}"
        elif self.op is CarrierOp.SUBHARMONIC:
            core = f"{f} / {self.rational.denominator}"
        else:
            core = f"|{f} * {r} - {self.beat_ref}|"
        if self.harmonic_n == 1:
            return core
        return (f"({core}) * {self.harmonic_n}" if self.harmonic_up
                else f"({core}) / {self.harmonic_n}")


# --- description length: long expressions buy less --------------------

def _int_cost(n: int) -> int:
    """Bits needed for an integer literal; bigger integers cost more."""
    return max(1, abs(int(n)).bit_length())


def description_length(expr: CarrierExpression | str) -> int:
    """Complexity penalty for an expression.

    More operations and larger integers mean a higher description
    length. A "match" found with a long expression is worth less than
    the same match found with a short one, because a long expression is
    one of far more expressions that were available to try.
    """
    if isinstance(expr, str):
        cost = sum(_int_cost(int(tok.replace(".", "").lstrip("0") or "0"))
                   for tok in re.findall(r"\d+(?:\.\d+)?", expr))
        cost += 2 * len(re.findall(r"[*/+\-%|]|mod", expr))
        return cost
    cost = (_int_cost(expr.base_hz.numerator)
            + _int_cost(expr.base_hz.denominator)
            + _int_cost(expr.rational.numerator)
            + _int_cost(expr.rational.denominator)
            + OP_COST[expr.op])
    if expr.beat_ref is not None:
        cost += _int_cost(expr.beat_ref)
    if expr.harmonic_n != 1:
        cost += 2 + _int_cost(expr.harmonic_n)
    return cost


# --- target fitting: labelled, or refused ------------------------------

def is_target_fitted(selected_after_seeing_target: bool) -> bool:
    """A carrier chosen after the target was in view is target-fitted.

    This is not a judgement about intent. It is bookkeeping: a selection
    made with the answer visible cannot also be evidence for the answer.
    """
    return bool(selected_after_seeing_target)


def refuse_carrier_selected_after_target(
        expression_text: str = "13772.28 * 2/3",
        target_hz: float | int | Fraction = GROUPED_9192,
        label_applied: bool = False) -> None:
    """Refuse an unlabelled post-hoc carrier selection."""
    if label_applied:
        raise CarrierError(
            f"{expression_text} is labelled TARGET_FITTED against "
            f"{target_hz}, which is the only condition under which it may "
            f"be reported at all. It is still not evidence: the label "
            f"records the debt, it does not pay it.")
    raise CarrierError(
        f"{expression_text} was selected after {target_hz} was in view. "
        f"A rational chosen to land near a known target is fitted to that "
        f"target and carries no evidential weight. It may be reported "
        f"only with target_fitted=True, and only alongside its residual, "
        f"its description length, and its look-elsewhere p-value.")


# --- the preregistered grid --------------------------------------------

def build_grid() -> tuple[CarrierExpression, ...]:
    """Enumerate every preregistered expression, once, in fixed order."""
    out: list[CarrierExpression] = []
    for base_id, f in REGISTERED_BASES:
        for r in SUPPLIED_RATIONALS:
            cores: list[tuple[CarrierOp, int | None]] = [
                (CarrierOp.LITERAL_MULTIPLIER, None),
                (CarrierOp.INVERSE_MULTIPLIER, None),
                (CarrierOp.PHASE_MODULO, None),
                (CarrierOp.HARMONIC, None),
                (CarrierOp.SUBHARMONIC, None),
                (CarrierOp.BEAT_CS133_FULL, CS133_HZ),
            ]
            cores += [(CarrierOp.BEAT_GROUPED, g) for g in GROUPED_REFS]
            for op, ref in cores:
                for n in HARMONIC_ORDERS:
                    for up in ((True,) if n == 1 else (True, False)):
                        e = CarrierExpression(base_id, f, r, op, n, up, ref)
                        if e.value() > 0:
                            out.append(e)
    return tuple(out)


GRID: tuple[CarrierExpression, ...] = build_grid()

#: Float shadow of the grid, sorted, for the sampling loop only. Every
#: reported residual is recomputed exactly from the Fractions.
_GRID_FLOATS: tuple[float, ...] = tuple(sorted(float(e.value())
                                               for e in GRID))


def grid_size() -> int:
    return len(GRID)


def _best_rel_float(target: float) -> float:
    """Smallest relative residual over the grid, float, via bisect."""
    if target <= 0:
        raise CarrierError("target must be positive")
    i = bisect.bisect_left(_GRID_FLOATS, target)
    best = float("inf")
    for j in (i - 1, i, i + 1):
        if 0 <= j < len(_GRID_FLOATS):
            best = min(best, abs(target - _GRID_FLOATS[j]) / target)
    return best


def best_grid_hit(target_hz: float | int | Fraction) -> dict:
    """Closest grid expression to the target, exactly where possible.

    Ties on residual are broken by description length: the shortest
    expression that achieves the residual is the one reported.
    """
    t = Fraction(target_hz) if not isinstance(target_hz, float) \
        else Fraction(target_hz).limit_denominator(10 ** 12)
    if t <= 0:
        raise CarrierError("target must be positive")
    best: CarrierExpression | None = None
    best_rel: Fraction | None = None
    best_dl = 0
    for e in GRID:
        rel = abs(t - e.value()) / t
        dl = description_length(e)
        if best_rel is None or rel < best_rel or (rel == best_rel
                                                  and dl < best_dl):
            best, best_rel, best_dl = e, rel, dl
    assert best is not None and best_rel is not None
    return {
        "expression": best.text(),
        "value_exact": str(best.value()),
        "value_float": float(best.value()),
        "op": best.op.value,
        "base_id": best.base_id,
        "residual_exact": str(t - best.value()),
        "residual_float": float(t - best.value()),
        "relative_residual": float(best_rel),
        "relative_residual_exact": str(best_rel),
        "description_length": best_dl,
        "is_exact_hit": best_rel == 0,
    }


# --- the audited high-priority candidate -------------------------------

#: 13772.28 * 2/3 = 9181.52 exactly.
F_TIMES_TWO_THIRDS = F_CRYSTAL_N7_HZ * Fraction(2, 3)
#: 9192 - 9181.52 = 10.48 exactly.
RESIDUAL_TO_9192 = Fraction(GROUPED_9192) - F_TIMES_TWO_THIRDS
#: 63/6 = 21/2 = 10.5 exactly.
SIXTY_THREE_SIXTHS = Fraction(63, 6)
#: 9181.52 + 63/6 = 9192.02 exactly.
CORRECTED_SUM = F_TIMES_TWO_THIRDS + SIXTY_THREE_SIXTHS
#: 9192 * 3/2 = 13788 exactly -- the base that would give 9192 exactly.
EXACT_BASE_FOR_9192 = Fraction(GROUPED_9192) * Fraction(3, 2)
#: 13788 - 13772.28 = 15.72 exactly. The pack originally said the exact
#: base was "0.03 Hz below" the computed mode; it is 15.72 Hz ABOVE.
BASE_DIFFERENCE = EXACT_BASE_FOR_9192 - F_CRYSTAL_N7_HZ

#: The R11 delta resolved the "0.03 Hz below" figure: it belongs to a
#: different frequency entirely. 13772.28 - 13772.25 = 0.03 exactly.
#: Registered as arithmetic only -- a 0.03 Hz step from a computed mode
#: is a statement about rounding, not a physical carrier.
NEAR_MODE_CANDIDATE_HZ = Fraction(1377225, 100)          # 13772.25
NEAR_MODE_DIFFERENCE = F_CRYSTAL_N7_HZ - NEAR_MODE_CANDIDATE_HZ   # 3/100

#: Observed relative residual of the candidate against grouped 9192.
OBSERVED_REL_RESIDUAL = float(RESIDUAL_TO_9192 / Fraction(GROUPED_9192))

#: The candidate expression itself, as a grid member.
CANDIDATE_A_EXPRESSION = CarrierExpression(
    "N7_FIRST_MODE", F_CRYSTAL_N7_HZ, Fraction(2, 3),
    CarrierOp.LITERAL_MULTIPLIER)


def audit_high_priority_candidate() -> dict:
    """Every step of the candidate arithmetic, exact, with the discrepancy."""
    return {
        "candidate_id": CRYSTAL_CARRIER_CANDIDATE_A,
        "f_crystal_hz": _decimal_str(F_CRYSTAL_N7_HZ),            # 13772.28
        "f_crystal_exact": str(F_CRYSTAL_N7_HZ),                  # 344307/25
        "times_two_thirds_hz": _decimal_str(F_TIMES_TWO_THIRDS),  # 9181.52
        "times_two_thirds_exact": str(F_TIMES_TWO_THIRDS),
        "grouped_target": GROUPED_9192,
        "residual_to_9192_hz": _decimal_str(RESIDUAL_TO_9192),    # 10.48
        "residual_to_9192_exact": str(RESIDUAL_TO_9192),          # 262/25
        "sixty_three_sixths": str(SIXTY_THREE_SIXTHS),            # 21/2
        "sixty_three_sixths_hz": _decimal_str(SIXTY_THREE_SIXTHS),  # 10.50
        "sixty_three_sixths_is_exact": True,
        "corrected_sum_hz": _decimal_str(CORRECTED_SUM),          # 9192.02
        "corrected_sum_overshoot_hz": _decimal_str(
            CORRECTED_SUM - GROUPED_9192),                        # 0.02
        "exact_base_for_9192_hz": _decimal_str(EXACT_BASE_FOR_9192),  # 13788
        "exact_base_is_exact": EXACT_BASE_FOR_9192.denominator == 1,
        "base_difference_hz": _decimal_str(BASE_DIFFERENCE),      # 15.72
        "base_difference_exact": str(BASE_DIFFERENCE),            # 393/25
        "base_difference_sign": "EXACT_BASE_IS_ABOVE_COMPUTED_MODE",
        # the R11 delta's resolution of the "0.03 Hz below" figure
        "near_mode_candidate_hz": _decimal_str(NEAR_MODE_CANDIDATE_HZ),
        "near_mode_difference_hz": _decimal_str(NEAR_MODE_DIFFERENCE),
        "near_mode_difference_exact": str(NEAR_MODE_DIFFERENCE),   # 3/100
        "near_mode_note": (
            "13772.25 Hz is the frequency that really is 0.03 Hz below the "
            "computed mode 13772.28 Hz; 13788.00 Hz is not. Registered as "
            "arithmetic only: a 0.03 Hz step from a computed mode is a "
            "statement about rounding, not a physical carrier"),
        "relative_residual": OBSERVED_REL_RESIDUAL,
        "relative_residual_percent": OBSERVED_REL_RESIDUAL * 100,
        "target_fitted": True,
        "pack_discrepancy": (
            "the source pack describes 13788.00 Hz as '0.03 Hz below the "
            "finest computational result'. Computed exactly here, "
            "13788.00 - 13772.28 = 15.72 Hz, so the exact base for 9192 "
            "lies 15.72 Hz ABOVE the computed mode -- wrong in sign and "
            "by a factor of about 500 in magnitude. The 0.03 figure most "
            "closely resembles the 9192.02 - 9192 = 0.02 Hz overshoot at "
            "the other end of the chain. The pack figure is not adopted; "
            "15.72 Hz is the value this module reports. RESOLVED by the "
            "R11 delta: the frequency that really is 0.03 Hz below the "
            "computed mode is 13772.25 Hz (see near_mode_candidate_hz), "
            "not 13788.00 Hz"),
        "pack_discrepancy_status": "RESOLVED_CORRECTED_CANDIDATE_REGISTERED",
        "note": (
            "every step above is exact rational arithmetic and every step "
            "reproduces. That is all it is: 2/3 was chosen after 9192 was "
            "in view, so the chain is fitted to its target"),
    }


# --- the look-elsewhere null, with a power control ---------------------

def lookelsewhere_pvalue(target_hz: float | int | Fraction = GROUPED_9192,
                         tol_rel: float | None = None,
                         n_samples: int = N_SAMPLES,
                         seed: int = SEED,
                         lo_hz: float = SEARCH_LO_HZ,
                         hi_hz: float = SEARCH_HI_HZ) -> dict:
    """How often does chance land as close to a RANDOM target as we did?

    Draw ``n_samples`` targets uniformly from the preregistered band and
    count the fraction for which SOME grid expression falls within
    ``tol_rel`` (default: the observed 10.48/9192 residual). A large p
    means the candidate's match is what a grid this size produces
    anyway.
    """
    if tol_rel is None:
        tol_rel = OBSERVED_REL_RESIDUAL
    if tol_rel < 0:
        raise CarrierError("tolerance must be non-negative")
    rng = random.Random(seed)
    hits = 0
    for _ in range(n_samples):
        t = rng.uniform(lo_hz, hi_hz)
        if _best_rel_float(t) <= tol_rel:
            hits += 1
    p = hits / n_samples
    return {
        "target_hz": float(target_hz),
        "tol_rel": tol_rel,
        "tol_rel_percent": tol_rel * 100,
        "search_band_hz": [lo_hz, hi_hz],
        "grid_size": grid_size(),
        "n_samples": n_samples,
        "hits": hits,
        "p_value": p,
        "observed_best_hit": best_grid_hit(target_hz),
        "verdict": ("NO_BETTER_THAN_CHANCE" if p > 0.05
                    else "BETTER_THAN_CHANCE"),
        "note": (
            "a grid of this size matches a random target to the observed "
            "tolerance far more often than 1 in 20, so landing near 9192 "
            "is what the search does, not what the crystal says"),
    }


#: The planted signal for the power control: exactly a grid expression,
#: 4096 * 3/4 = 3072, taken at harmonic order 5 -> 15360 Hz exactly.
PLANTED_EXPRESSION = CarrierExpression(
    "F_4096", Fraction(4096), Fraction(3, 4),
    CarrierOp.LITERAL_MULTIPLIER, 5, True)
PLANTED_TARGET_HZ = PLANTED_EXPRESSION.value()


def power_check() -> dict:
    """Plant an exact grid expression and confirm the search recovers it."""
    hit = best_grid_hit(PLANTED_TARGET_HZ)
    return {
        "planted_expression": PLANTED_EXPRESSION.text(),
        "planted_target_hz": str(PLANTED_TARGET_HZ),
        "recovered": hit,
        "recovered_value_equals_planted":
            Fraction(hit["value_exact"]) == PLANTED_TARGET_HZ,
        "detected": hit["relative_residual"] == 0.0,
        "note": (
            "the search recovers a planted exact expression at zero "
            "residual, so it has the power to detect a real hit. That it "
            "calls the 9192 candidate chance is a finding, not blindness"),
    }


# --- reported candidates -----------------------------------------------

@dataclass(frozen=True)
class CarrierCandidate:
    """A reported candidate. It never travels without its price tags."""

    candidate_id: str
    expression: CarrierExpression
    target_hz: Fraction
    target_fitted: bool
    lookelsewhere_p: float

    def as_dict(self) -> dict:
        v = self.expression.value()
        resid = self.target_hz - v
        rel = abs(resid) / self.target_hz
        return {
            "candidate_id": self.candidate_id,
            "expression": self.expression.text(),
            "value_exact": str(v),
            "value_hz": float(v),
            "target_hz": float(self.target_hz),
            "residual_exact": str(resid),
            "residual_hz": float(resid),
            "residual_is_exact_arithmetic": True,
            "relative_residual": float(rel),
            "description_length": description_length(self.expression),
            "target_fitted": self.target_fitted,
            "lookelsewhere_p": self.lookelsewhere_p,
            "verdict": DEFAULT_VERDICT,
        }


def search_carriers(target_hz: float | int | Fraction = GROUPED_9192,
                    top_n: int = 5,
                    selected_after_seeing_target: bool = True,
                    lookelsewhere_p: float | None = None) -> list[dict]:
    """Rank grid expressions against a target, cheapest residual first.

    Every returned candidate carries its exact expression, its residual
    (exact), its description length, its target-fitted flag, and the
    look-elsewhere p-value for the search that produced it.
    """
    if top_n <= 0:
        raise CarrierError("top_n must be positive")
    t = Fraction(target_hz) if not isinstance(target_hz, float) \
        else Fraction(target_hz).limit_denominator(10 ** 12)
    if t <= 0:
        raise CarrierError("target must be positive")
    if lookelsewhere_p is None:
        lookelsewhere_p = lookelsewhere_pvalue(t)["p_value"]
    fitted = is_target_fitted(selected_after_seeing_target)
    scored = sorted(
        GRID,
        key=lambda e: (abs(t - e.value()) / t, description_length(e),
                       e.text()))
    return [CarrierCandidate(CRYSTAL_CARRIER_CANDIDATE_A, e, t, fitted,
                             lookelsewhere_p).as_dict()
            for e in scored[:top_n]]


def carrier_report() -> dict:
    lee = lookelsewhere_pvalue()
    candidate = CarrierCandidate(
        CRYSTAL_CARRIER_CANDIDATE_A, CANDIDATE_A_EXPRESSION,
        Fraction(GROUPED_9192), is_target_fitted(True), lee["p_value"])
    return {
        "public_alias": CRYSTAL_CARRIER_CANDIDATE_A,
        "audit": audit_high_priority_candidate(),
        "candidate": candidate.as_dict(),
        "grid_size": grid_size(),
        "lookelsewhere": lee,
        "power": power_check(),
        "what_would_change_this": (
            "an independent computed mode the rational was not selected "
            "on, a look-elsewhere p that survives the full grid, and a "
            "physical mechanism that predicts the 10.48 Hz correction "
            "instead of absorbing it into a chosen fraction"),
        "evidence_class": "DERIVED_MATHEMATICS",
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "verdict": DEFAULT_VERDICT,
        "what_this_does_not_say": (
            "It does not say a crystal carries, generates, or locks to "
            "any caesium frequency; that 13772.28 Hz is physically "
            "privileged; that 2/3 is anything but a fraction chosen after "
            "the target was known; or that 63/6 corrects anything. The "
            "arithmetic is exact and reproduces, the residual to grouped "
            "9192 is 10.48 Hz, the exact base for 9192 is 15.72 Hz above "
            "the computed mode (not 0.03 Hz below it, as the source pack "
            "states), and the look-elsewhere p-value says a grid this "
            "large finds a match like this by chance."),
    }
