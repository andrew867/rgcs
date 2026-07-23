"""P11 — angle reconstruction: could 51.843 have been *derived* this way?

:mod:`r11.picorrection` establishes the arithmetic: ``atan(sqrt(phi)) +
pi/200 = 51.843000336...``, which reproduces the quoted ``51.843`` to
seven digits and is capped at ``RETROSPECTIVE_NUMERIC_MATCH`` because the
target is quoted to three decimals and dozens of equally simple
corrections land inside that slack.

This module asks the next question, which is historical rather than
arithmetical: *at the precision available to someone working with the
tools of the 1960s and 70s, could that expression have been used to
produce the quoted number?* The question is answerable in the direction
of possibility and unanswerable in the direction of fact, and the module
reports both halves.

**Possibility.** The expression is robust. :func:`precision_table`
evaluates it at 3, 4, 5, 6, 7, 8 and 10 significant digits under both
round-half-even and truncation, and it reproduces ``51.843`` for every
precision from five significant digits to eight -- and fails outside that
window in both directions, at three or four digits because it has not yet
resolved the third decimal, at ten because the true value is
``51.84300034`` and the quoted number is not.
:func:`historical_substitution_table` repeats the calculation with period
approximations -- ``phi`` as ``1.618``, ``1.6180``, ``1.61803``, ``pi`` as
``3.14``, ``3.1416``, ``3.14159`` -- and the quoted value survives every
combination that carries ``pi`` to five digits. So a person with a
five-digit table and an arctangent could have produced ``51.843``. That is
a real finding and it is reported as such.

**Impossibility of the negative controls.** A wrong calculator mode does
not produce it: read in radians the arctangent is ``0.9046``, and
converted a second time it is ``2969.5``, neither of which is within
three thousand degrees of the target. :func:`wrong_mode_control` computes
both and confirms the miss, so "they had it in the wrong mode" is
excluded rather than assumed.

**Insufficiency of the slide rule.** Three significant figures is
``+/-0.05`` degrees, and inside that band ``51.843`` is indistinguishable
from ``51.8273`` (the uncorrected golden-ratio angle), from ``51.83``,
from ``51.86`` and from the historically quoted ``51 deg 51 min 51 sec``.
:func:`slide_rule_band` lists them. A slide rule cannot single out this
expression, so slide-rule-era practice cannot be offered as evidence that
this expression is the one that was used.

**And the point.** None of that is authorship. A calculation that *could*
have been done is not a calculation that *was* done, and
:func:`historical_evidence_status` returns ``BLOCKED_MISSING_DATA``: no
patent, paper, notebook, correspondence or period calculator manual
documenting this derivation has been located in this environment.
:func:`refuse_authorship_claim` raises, because inferring intent from
numerical reconstruction is the attack this module exists to block -- it
is how a coincidence becomes an attribution.

**Two different numbers.** ``51.843`` is a decimal the source specified.
``51 deg 51 min 51 sec`` -- a separately quoted cut value -- is
``51.864167`` degrees. They differ by ``0.021`` degrees, about 76
arcseconds. :func:`dms_cut_comparison` keeps them apart; conflating them
would let a match against one be reported as a match against the other.

Nothing here is measured. No artefact was surveyed and no archive was
consulted; the constants are closed forms evaluated with :mod:`decimal`
and the high-precision arctangent is reused from :mod:`r11.geominverse`.
The standing verdict is ``HISTORICAL_DERIVATION_NOT_ESTABLISHED``.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_DOWN, ROUND_HALF_EVEN, localcontext
from enum import Enum
from fractions import Fraction

from r11.geominverse import (
    DECIMAL_PRECISION,
    _dec_atan as dec_atan,
    _dec_pi as dec_pi,
    atan_sqrt_phi_deg,
    sqrt_phi_exact,
)
from r11.picorrection import (
    FROZEN_DENOMINATORS,
    RELATION_C1,
    SUPPLIED_TARGET_C1_STR,
    ClaimClass,
)


class AngleReconError(ValueError):
    """Raised when a reconstruction is asked to establish authorship.

    Also covers a malformed precision request, an unknown rounding mode,
    and any attempt to report the numerical reconstruction as historical
    fact.
    """


class RoundingMode(Enum):
    """How a value is cut down to a stated number of digits."""

    ROUND_HALF_EVEN = "ROUND_HALF_EVEN"
    TRUNCATE = "TRUNCATE"


class EvidenceLocation(Enum):
    """Whether a class of documentary evidence was found here."""

    LOCATED = "LOCATED"
    NOT_LOCATED = "NOT_LOCATED"
    NOT_SEARCHED = "NOT_SEARCHED"


#: The standing verdict. Numerical plausibility never upgrades it.
VERDICT = "HISTORICAL_DERIVATION_NOT_ESTABLISHED"

PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The quoted target, as the string it was quoted as.
QUOTED_TARGET_STR = SUPPLIED_TARGET_C1_STR          # "51.843"
QUOTED_TARGET = Decimal(QUOTED_TARGET_STR)

#: Significant-digit settings the precision table is computed at.
SIG_DIGITS: tuple[int, ...] = (3, 4, 5, 6, 7, 8, 10)

#: Every rounding mode the table is computed under.
ROUNDING_MODES: tuple[RoundingMode, ...] = (
    RoundingMode.ROUND_HALF_EVEN, RoundingMode.TRUNCATE)

#: Period approximations of the two constants. These are the values that
#: appear in ordinary four- and five-figure tables of the era, not values
#: chosen to make the reconstruction work.
HISTORICAL_PHI: tuple[str, ...] = ("1.618", "1.6180", "1.61803")
HISTORICAL_PI: tuple[str, ...] = ("3.14", "3.1416", "3.14159")

#: A slide rule reads to about three significant figures, which on a
#: number near 51.8 is a half-unit of 0.05 degrees.
SLIDE_RULE_SIG_FIGS = 3
SLIDE_RULE_HALF_WIDTH_DEG = Decimal("0.05")

#: The separately quoted cut value, in degrees, minutes and seconds. It is
#: NOT the same number as 51.843 and is never treated as one.
DMS_CUT = (51, 51, 51)


# =======================================================================
# The expression under reconstruction
# =======================================================================

def reconstruction_value(precision: int = DECIMAL_PRECISION) -> Decimal:
    """``atan(sqrt(phi)) + pi/200`` in degrees, at full precision.

    Evaluated through the registered C1 relation so that this module and
    :mod:`r11.picorrection` cannot drift apart.
    """
    return RELATION_C1.predicted_deg(int(precision))


def uncorrected_value(precision: int = DECIMAL_PRECISION) -> Decimal:
    """``atan(sqrt(phi))`` in degrees -- the expression without the term."""
    return atan_sqrt_phi_deg(int(precision))


#: The reconstruction at working precision: 51.84300033625570...
RECONSTRUCTION_DEG = reconstruction_value()
#: The uncorrected angle: 51.82729237298775...
UNCORRECTED_DEG = uncorrected_value()


# =======================================================================
# Precision: at how many digits does the expression still give 51.843?
# =======================================================================

def evaluate_at_precision(expr_value: Decimal | float | str,
                          sig_digits: int,
                          mode: RoundingMode | str
                          = RoundingMode.ROUND_HALF_EVEN) -> Decimal:
    """Cut a value down to ``sig_digits`` significant digits.

    Two modes, because they are the two things a person actually does.
    ``ROUND_HALF_EVEN`` is what a table or a calculator does at its last
    displayed digit; ``TRUNCATE`` is what happens when digits simply run
    out -- a shorter table, a display with fewer places, a value copied
    part-way. They are computed separately rather than assumed equivalent,
    because for a value like ``51.843000336`` they need not agree.
    """
    if isinstance(mode, str):
        try:
            mode = RoundingMode(mode)
        except ValueError as exc:
            raise AngleReconError(f"unknown rounding mode {mode!r}") from exc
    if not isinstance(mode, RoundingMode):
        raise AngleReconError("mode must be a RoundingMode")
    if isinstance(sig_digits, bool) or not isinstance(sig_digits, int):
        raise AngleReconError("sig_digits must be an integer")
    if int(sig_digits) < 1:
        raise AngleReconError("sig_digits must be at least 1")
    value = Decimal(str(expr_value)) if not isinstance(expr_value, Decimal) \
        else expr_value
    with localcontext() as ctx:
        ctx.prec = int(sig_digits)
        ctx.rounding = (ROUND_HALF_EVEN if mode is RoundingMode.ROUND_HALF_EVEN
                        else ROUND_DOWN)
        return +value


def reproduces_quoted(value: Decimal,
                      quoted: Decimal = QUOTED_TARGET) -> bool:
    """Is the cut-down value numerically equal to the quoted number?

    Compared as numbers, so ``51.8430`` counts as ``51.843``: trailing
    zeros are a display choice, not a disagreement.
    """
    return Decimal(value) == Decimal(quoted)


def precision_table(expr_value: Decimal | None = None,
                    quoted: Decimal = QUOTED_TARGET) -> tuple[dict, ...]:
    """The expression at every listed precision, under both modes.

    The window is the finding. Below five significant digits the
    expression has not yet resolved the third decimal and cannot be
    compared to a three-decimal quotation at all; above eight it disagrees,
    because the true value is ``51.84300034`` and the quoted number is
    ``51.843``. In between it reproduces the quotation exactly. A person
    working to five, six, seven or eight digits would have written down
    ``51.843``; a person working to three would not have got there, and a
    person working to ten would have written something else.
    """
    value = RECONSTRUCTION_DEG if expr_value is None else Decimal(expr_value)
    rows: list[dict] = []
    for n in SIG_DIGITS:
        for mode in ROUNDING_MODES:
            cut = evaluate_at_precision(value, n, mode)
            rows.append({
                "sig_digits": n,
                "mode": mode.value,
                "value": str(cut),
                "value_float": float(cut),
                "reproduces_quoted": reproduces_quoted(cut, quoted),
                "quoted": str(quoted),
            })
    return tuple(rows)


def reproducing_sig_digits(mode: RoundingMode
                           = RoundingMode.ROUND_HALF_EVEN) -> tuple[int, ...]:
    """Which listed precisions reproduce the quoted number, in one mode."""
    return tuple(row["sig_digits"] for row in precision_table()
                 if row["mode"] == mode.value and row["reproduces_quoted"])


# =======================================================================
# Historical constant approximations
# =======================================================================

def substituted_value(phi_str: str, pi_str: str,
                      denominator: int = 200,
                      precision: int = 40) -> Decimal:
    """The expression computed with period approximations of phi and pi.

    The approximate ``pi`` is used consistently: for the correction term
    ``pi/N`` *and* for the radian-to-degree conversion, because a person
    with a four-figure table has one value of ``pi``, not two. The
    arctangent itself is computed exactly -- that is what an arctangent
    table supplies, and its own error is a separate question from the
    error in the constants.
    """
    p = int(precision)
    if p < 8:
        raise AngleReconError("substitution needs at least 8 digits")
    with localcontext() as ctx:
        ctx.prec = p
        phi = Decimal(phi_str)
        pi = Decimal(pi_str)
        if phi <= 0 or pi <= 0:
            raise AngleReconError("phi and pi approximations must be "
                                  "positive")
        rad = dec_atan(phi.sqrt(), p)
        value = rad * Decimal(180) / pi + pi / Decimal(int(denominator))
        return +value


def historical_substitution_table(sig_digits: int = 5,
                                  mode: RoundingMode
                                  = RoundingMode.ROUND_HALF_EVEN
                                  ) -> tuple[dict, ...]:
    """The expression under every period approximation of phi and pi.

    Nine combinations. The result survives every one of them that carries
    ``pi`` to five digits or better; it fails only when ``pi`` is taken as
    ``3.14``, which moves the degree conversion by about ``0.026``
    degrees -- some eighty thousand times the residual the whole relation
    rests on.

    So the sensitivity is in ``pi``, not in ``phi``: three digits of the
    golden ratio are enough, three digits of ``pi`` are not.
    """
    rows: list[dict] = []
    for phi_str in HISTORICAL_PHI:
        for pi_str in HISTORICAL_PI:
            value = substituted_value(phi_str, pi_str)
            cut = evaluate_at_precision(value, sig_digits, mode)
            rows.append({
                "phi_approx": phi_str,
                "pi_approx": pi_str,
                "value": float(value),
                "value_exact": str(value),
                "rounded": str(cut),
                "sig_digits": int(sig_digits),
                "mode": mode.value if isinstance(mode, RoundingMode)
                else str(mode),
                "reproduces_quoted": reproduces_quoted(cut),
                "residual_to_quoted_deg": float(QUOTED_TARGET - value),
            })
    return tuple(rows)


def survives_historical_constants(sig_digits: int = 5) -> dict:
    """How many period-constant combinations still give 51.843."""
    rows = historical_substitution_table(sig_digits)
    survive = [r for r in rows if r["reproduces_quoted"]]
    return {
        "n_combinations": len(rows),
        "n_reproducing": len(survive),
        "reproducing": [(r["phi_approx"], r["pi_approx"]) for r in survive],
        "failing": [(r["phi_approx"], r["pi_approx"]) for r in rows
                    if not r["reproduces_quoted"]],
        "sig_digits": int(sig_digits),
        "sensitive_constant": "pi",
        "note": (
            "the reconstruction is robust to period values of phi and to "
            "five-figure pi, and fails only for pi = 3.14. Robustness is a "
            "statement about the arithmetic, not about what anyone did"),
        "verdict": VERDICT,
    }


# =======================================================================
# Negative control: the wrong calculator mode
# =======================================================================

def wrong_mode_control(precision: int = 40) -> dict:
    """Does a degree/radian mode error produce 51.843? No -- by miles.

    Two ways to get the mode wrong, both computed:

    * the arctangent is left in radians and its result read as degrees --
      ``0.9046`` instead of ``51.8273``;
    * a value already in degrees is converted again by ``180/pi`` --
      ``2969.5``.

    Both miss the target by more than fifty degrees, so a mode error is
    excluded as an explanation of ``51.843`` rather than left hanging as a
    possibility. This is a control: if a wrong mode HAD landed near the
    target, the whole reconstruction would have been worthless, because
    two different procedures would produce the same number.
    """
    p = int(precision)
    with localcontext() as ctx:
        ctx.prec = p
        pi = dec_pi(p)
        rad = dec_atan(sqrt_phi_exact(p), p)          # 0.90455689...
        correction = pi / Decimal(200)
        radians_as_degrees = rad + correction
        deg = atan_sqrt_phi_deg(p)
        converted_twice = deg * Decimal(180) / pi + correction
        rows = (
            {
                "mode_error": "RADIANS_LABELLED_DEGREES",
                "description": ("the arctangent is evaluated in radian "
                                "mode and its result read as degrees"),
                "value": float(+radians_as_degrees),
                "value_exact": str(+radians_as_degrees),
                "abs_difference_deg": float(
                    abs(QUOTED_TARGET - radians_as_degrees)),
            },
            {
                "mode_error": "DEGREES_CONVERTED_AGAIN",
                "description": ("a value already in degrees is put through "
                                "the 180/pi conversion a second time"),
                "value": float(+converted_twice),
                "value_exact": str(+converted_twice),
                "abs_difference_deg": float(
                    abs(QUOTED_TARGET - converted_twice)),
            },
        )
    closest = min(row["abs_difference_deg"] for row in rows)
    return {
        "quoted": float(QUOTED_TARGET),
        "correct_value_deg": float(RECONSTRUCTION_DEG),
        "mode_errors": rows,
        "closest_abs_difference_deg": closest,
        "any_reproduces_quoted": bool(closest <= float(
            SLIDE_RULE_HALF_WIDTH_DEG)),
        "control_passed": bool(closest > 1.0),
        "note": (
            "no mode error gets within fifty degrees of the target, so a "
            "wrong calculator mode is excluded as an explanation. The "
            "control matters: a procedure that produced the same number by "
            "accident would make the reconstruction meaningless"),
        "verdict": VERDICT,
    }


# =======================================================================
# The slide-rule band
# =======================================================================

def dms_to_degrees(d: int, m: int, s: int) -> Fraction:
    """Degrees, minutes, seconds as an exact :class:`Fraction`."""
    for name, v in (("degrees", d), ("minutes", m), ("seconds", s)):
        if isinstance(v, bool) or not isinstance(v, int):
            raise AngleReconError(f"{name} must be an integer")
    return Fraction(d) + Fraction(m, 60) + Fraction(s, 3600)


#: 51 deg 51 min 51 sec = 51.86416666... degrees, exactly 62237/1200.
DMS_CUT_DEG = dms_to_degrees(*DMS_CUT)


def slide_rule_band(centre: Decimal = QUOTED_TARGET,
                    half_width: Decimal = SLIDE_RULE_HALF_WIDTH_DEG) -> dict:
    """What a three-figure reading cannot tell apart.

    A slide rule reads about three significant figures. On a number near
    ``51.8`` that is ``+/-0.05`` degrees, and the band ``[51.793,
    51.893]`` contains the uncorrected golden-ratio angle, the quoted
    value, the ``51 deg 51 min 51 sec`` cut value, and any number of round
    decimals besides. Everything in that list reads as the same slide-rule
    result.

    The consequence is the point: slide-rule-era practice cannot be
    offered as evidence for THIS expression, because at slide-rule
    precision this expression is not distinguishable from several others,
    including the one that omits the correction term entirely.
    """
    lo = Decimal(centre) - Decimal(half_width)
    hi = Decimal(centre) + Decimal(half_width)
    candidates = (
        ("atan(sqrt(phi))", Decimal(UNCORRECTED_DEG)),
        ("atan(sqrt(phi)) + pi/200", Decimal(RECONSTRUCTION_DEG)),
        ("51.843 (quoted)", QUOTED_TARGET),
        ("51.83", Decimal("51.83")),
        ("51.86", Decimal("51.86")),
        ("51 deg 51 min 51 sec", Decimal(DMS_CUT_DEG.numerator)
         / Decimal(DMS_CUT_DEG.denominator)),
        ("360/7", Decimal(360) / Decimal(7)),
    )
    inside = [(name, float(v)) for name, v in candidates if lo <= v <= hi]
    return {
        "sig_figs": SLIDE_RULE_SIG_FIGS,
        "centre": float(centre),
        "half_width_deg": float(half_width),
        "band_deg": [float(lo), float(hi)],
        "candidates_considered": [name for name, _ in candidates],
        "indistinguishable_inside_band": inside,
        "n_indistinguishable": len(inside),
        "can_single_out_expression": len(inside) <= 1,
        "resolution_verdict": "CANNOT_SINGLE_OUT",
        "note": (
            "at three significant figures the corrected and uncorrected "
            "expressions read identically, so a slide rule cannot be the "
            "instrument that distinguished them. The correction term is "
            "invisible at the precision of the tool"),
        "verdict": VERDICT,
    }


# =======================================================================
# Alternative hypotheses
# =======================================================================

@dataclass(frozen=True)
class AlternativeHypothesis:
    """One competing way to arrive at a number near 51.84 degrees."""

    label: str
    value_deg: Decimal
    family: str
    exact: bool
    note: str = ""

    def residual_to_quoted(self) -> Decimal:
        return QUOTED_TARGET - Decimal(self.value_deg)

    def as_dict(self) -> dict:
        resid = self.residual_to_quoted()
        return {
            "label": self.label,
            "family": self.family,
            "value_deg": float(self.value_deg),
            "value_deg_exact": str(self.value_deg),
            "residual_to_quoted_deg": float(resid),
            "abs_residual_deg": float(abs(resid)),
            "residual_arcsec": float(resid) * 3600.0,
            "exact_form": self.exact,
            "note": self.note,
        }


def alternatives_table(precision: int = DECIMAL_PRECISION) -> tuple[dict, ...]:
    """Every competing hypothesis, with its residual to the quoted value.

    A reconstruction is only worth anything against a field of
    alternatives. ``360/7`` is the seventh part of a circle, a
    construction with no golden ratio in it at all;
    ``51 deg 51 min 51 sec`` is a separately quoted cut value with a
    repeating-digit character of its own; ``atan(sqrt(phi))`` is the
    uncorrected constant. Then ``atan(sqrt(phi)) + pi/k`` for every frozen
    denominator, so the winning ``k = 200`` is shown alongside the fifteen
    it was chosen from rather than on its own.

    Sorted by absolute residual: the smallest is ``k = 200`` at
    ``3.4e-07``, and the next frozen denominator is nearly two thousand
    times worse.
    """
    p = int(precision)
    rows: list[AlternativeHypothesis] = [
        AlternativeHypothesis(
            "atan(sqrt(phi))", uncorrected_value(p), "GOLDEN_RATIO", True,
            "the uncorrected constant; 56.5 arcseconds below the quoted "
            "value"),
        AlternativeHypothesis(
            "360/7", Decimal(360) / Decimal(7), "CIRCLE_DIVISION", True,
            "the seventh part of a circle; no golden ratio involved"),
        AlternativeHypothesis(
            "51 deg 51 min 51 sec",
            Decimal(DMS_CUT_DEG.numerator) / Decimal(DMS_CUT_DEG.denominator),
            "SEXAGESIMAL", True,
            "a separately quoted cut value, exactly 62237/1200 degrees. A "
            "DIFFERENT number from 51.843, not a rounding of it"),
    ]
    with localcontext() as ctx:
        ctx.prec = p + 10
        base = uncorrected_value(p + 10)
        pi = dec_pi(p + 10)
        for k in FROZEN_DENOMINATORS:
            rows.append(AlternativeHypothesis(
                f"atan(sqrt(phi)) + pi/{k}", +(base + pi / Decimal(k)),
                "PI_CORRECTION", True,
                f"frozen denominator {k}"))
    out = [r.as_dict() for r in rows]
    out.sort(key=lambda d: d["abs_residual_deg"])
    return tuple(out)


def dms_cut_comparison() -> dict:
    """``51.843`` and ``51 deg 51 min 51 sec`` are different numbers.

    ``51.843`` is a decimal the source specified. ``51 deg 51 min 51 sec``
    is ``62237/1200 = 51.8641666...`` degrees. They differ by ``0.0211667``
    degrees -- about 76 arcseconds -- which is more than sixty thousand
    times the residual the pi/200 relation rests on. Treating a match
    against one as a match against the other would move the target by more
    than the entire effect being discussed.
    """
    dms_dec = (Decimal(DMS_CUT_DEG.numerator)
               / Decimal(DMS_CUT_DEG.denominator))
    diff = dms_dec - QUOTED_TARGET
    return {
        "quoted_decimal": float(QUOTED_TARGET),
        "quoted_decimal_str": QUOTED_TARGET_STR,
        "quoted_decimal_provenance": "a decimal the source specified",
        "dms": list(DMS_CUT),
        "dms_text": "51 deg 51 min 51 sec",
        "dms_exact_fraction": f"{DMS_CUT_DEG.numerator}/"
                              f"{DMS_CUT_DEG.denominator}",
        "dms_degrees": float(dms_dec),
        "difference_deg": float(diff),
        "difference_arcsec": float(diff) * 3600.0,
        "same_number": False,
        "do_not_conflate": True,
        "note": (
            "two separately quoted values 0.021 degrees apart. The "
            "sexagesimal one is not a rounding of the decimal one and the "
            "decimal one is not a conversion of the sexagesimal one; a "
            "reconstruction that matches one has not matched the other"),
        "verdict": VERDICT,
    }


# =======================================================================
# The historical evidence -- which is what is actually missing
# =======================================================================

#: The classes of documentary evidence that would be needed to say this
#: expression WAS used, and their status in this environment.
EVIDENCE_CLASSES_SOUGHT: tuple[tuple[str, str], ...] = (
    ("patent", "a filed patent or application stating the derivation"),
    ("paper", "a published paper or technical report deriving the angle"),
    ("notebook", "a design notebook, drawing set or calculation sheet"),
    ("correspondence", "letters or memoranda discussing the choice"),
    ("calculator_manual", "a period calculator or table manual showing the "
                          "procedure"),
    ("interview", "a first-hand account from someone who did the work"),
)


def historical_evidence_record() -> tuple[dict, ...]:
    """What was looked for, and what was found. Nothing was found."""
    return tuple({
        "evidence_class": name,
        "description": desc,
        "status": EvidenceLocation.NOT_LOCATED.value,
        "located_in_this_environment": False,
    } for name, desc in EVIDENCE_CLASSES_SOUGHT)


def historical_evidence_status() -> str:
    """``BLOCKED_MISSING_DATA``. This is the module's actual result.

    Not ``UNSUPPORTED`` -- that would say the claim had been weighed and
    found wanting. The claim cannot be weighed at all: no patent, paper,
    notebook, correspondence, period manual or first-hand account
    documenting this derivation has been located in this environment. The
    arithmetic is available and the archive is not, so the status is
    blocked, and it stays blocked until a document arrives.
    """
    return ClaimClass.BLOCKED_MISSING_DATA.value


def refuse_authorship_claim(claimed_origin: str = "a period designer",
                            evidence: str = "") -> None:
    """Refuse to infer authorship or intent from a numerical match.

    Always. The reconstruction shows that the expression *could* have been
    evaluated with period tools -- that is a statement about arithmetic and
    the arithmetic supports it. Authorship is a different claim: it says
    somebody chose this expression, for this reason, and wrote down its
    result. Nothing in a residual can support that. There are competing
    expressions with comparable residuals, the target's own quoted
    precision cannot separate them, and no document has been located
    linking any of them to a person or a decision.

    What would change this: a dated patent, paper, notebook, drawing set,
    correspondence or period manual in which the derivation appears. Until
    then the status is BLOCKED_MISSING_DATA and the verdict is
    HISTORICAL_DERIVATION_NOT_ESTABLISHED.
    """
    tail = f" (evidence offered: {evidence!r})" if evidence else ""
    raise AngleReconError(
        f"refused: numerical reconstruction cannot establish that "
        f"{claimed_origin!r} derived {QUOTED_TARGET_STR} from "
        f"atan(sqrt(phi)) + pi/200{tail}. That an expression reproduces a "
        f"quoted number at period precision shows the calculation was "
        f"POSSIBLE, not that it was PERFORMED, and not who performed it or "
        f"why. Competing expressions reproduce the same three-decimal "
        f"quotation, the quotation's own precision cannot separate them, "
        f"and the documentary status is "
        f"{ClaimClass.BLOCKED_MISSING_DATA.value}: no patent, paper, "
        f"notebook, correspondence or period calculator manual "
        f"documenting this derivation has been located in this "
        f"environment. Verdict: {VERDICT}.")


# =======================================================================
# The report
# =======================================================================

def anglerecon_report(precision: int = DECIMAL_PRECISION) -> dict:
    """What the reconstruction shows, and the claim it cannot support."""
    table = precision_table()
    subs = survives_historical_constants()
    band = slide_rule_band()
    alts = alternatives_table(precision)
    return {
        "what_this_is": (
            "a precision and plausibility audit of atan(sqrt(phi)) + "
            "pi/200 against the quoted 51.843, asking whether the "
            "calculation was possible with period tools and whether "
            "possibility can establish that it was done"),
        "expression": RELATION_C1.expression_text(),
        "reconstruction_deg": float(RECONSTRUCTION_DEG),
        "reconstruction_deg_exact": str(RECONSTRUCTION_DEG),
        "quoted": QUOTED_TARGET_STR,
        "residual_to_quoted_deg": float(
            QUOTED_TARGET - RECONSTRUCTION_DEG),
        "precision_table": table,
        "reproducing_sig_digits_half_even": list(
            reproducing_sig_digits(RoundingMode.ROUND_HALF_EVEN)),
        "reproducing_sig_digits_truncate": list(
            reproducing_sig_digits(RoundingMode.TRUNCATE)),
        "historical_constants": {
            "phi_approximations": list(HISTORICAL_PHI),
            "pi_approximations": list(HISTORICAL_PI),
            "table": historical_substitution_table(),
            "summary": subs,
        },
        "wrong_mode_control": wrong_mode_control(),
        "slide_rule": band,
        "alternatives": alts,
        "best_alternative": alts[0],
        "runner_up_alternative": alts[1],
        "dms_cut_comparison": dms_cut_comparison(),
        "historical_evidence": list(historical_evidence_record()),
        "historical_evidence_status": historical_evidence_status(),
        "refusals": ["refuse_authorship_claim"],
        "claim_class": ClaimClass.BLOCKED_MISSING_DATA.value,
        "numeric_claim_class": ClaimClass.RETROSPECTIVE_NUMERIC_MATCH.value,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say anyone derived 51.843 from atan(sqrt(phi)) "
            "plus pi/200. It shows the calculation was POSSIBLE at period "
            "precision -- the expression reproduces the quoted value at "
            "five through eight significant digits under both rounding and "
            "truncation, and survives period approximations of phi and of "
            "pi to five figures -- and possibility is not performance. It "
            "does not say a slide rule could have singled the expression "
            "out: at three significant figures the corrected and "
            "uncorrected forms are indistinguishable, along with 51.83, "
            "51.86 and the 51 deg 51 min 51 sec cut value. It does not say "
            "a calculator mode error explains the number; that control was "
            "run and misses by more than fifty degrees. It does not treat "
            "51.843 and 51 deg 51 min 51 sec as the same number -- they "
            "differ by 0.021 degrees, about 76 arcseconds. And it does not "
            "claim authorship, intent or provenance for anyone: no patent, "
            "paper, notebook, correspondence or period calculator manual "
            "documenting this derivation has been located in this "
            "environment, so the historical evidence status is "
            "BLOCKED_MISSING_DATA. Nothing here was measured and no "
            "archive was consulted."),
        "verdict": VERDICT,
    }
