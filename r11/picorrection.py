"""P11 — the pi-correction registry: two relations, priced and capped.

A slope of ``51.843`` degrees sits ``0.0157076...`` degrees above
``atan(sqrt(phi)) = 51.8272923729877525...``. That gap is small, real, and
-- this is the tempting part -- it is almost exactly the bare number
``pi/200 = 0.015707963267948967``::

    atan(sqrt(phi)) + pi/200 = 51.843000336255701...
    51.843                   - 51.843000336255701... = -3.3625570e-07 deg

Seven digits of agreement. The instinct is to call that a derivation. This
module registers the relation, computes every digit of it exactly, and
then prices it -- and the price is high enough that the standing verdict
is ``PI_CORRECTION_REGISTRY_RETROSPECTIVE_ONLY`` and the claim class never
rises above ``RETROSPECTIVE_NUMERIC_MATCH``.

**The registry cannot grow.** The obvious way to turn this into an
unlimited fitting tool is to observe a residual and then invent the
denominator that cancels it. So :data:`FROZEN_DENOMINATORS` is fixed
*before* any residual is scored -- fifteen denominators drawn from
circle-division and binary-division practice -- and
:func:`refuse_new_denominator` raises on every ``k`` outside it. A
registry that admits ``k = 201`` because ``k = 201`` happens to work is
not a registry, it is a curve fit with one free integer.

**The units do not line up, and that is recorded rather than hidden.**
``pi/200`` is a radian-flavoured quantity. As radians it is ``0.9``
degrees exactly -- fifty-seven times the gap it is supposed to close. The
relation works only if the *bare number* ``0.0157079...`` is declared to
be degrees, which is a change of category, not a conversion.
:func:`unit_validity` returns ``UNIT_CATEGORY_MIXED`` for both registered
relations and :func:`refuse_unit_confusion` refuses the claim that the
arithmetic is dimensionally consistent. Mixed units do not kill the
relation; they classify it.

**The decisive test is the precision of the input.** ``51.843`` is quoted
to three decimals, so it stands for the interval ``51.843 +/- 0.0005``.
The relation agrees with it to ``3.36e-07`` degrees -- roughly fifteen
hundred times finer than the number's own precision. Extra agreement
below the input's resolution is not extra evidence: it is agreement with
digits the input never carried. :func:`candidates_within_slack` makes this
concrete by enumerating the simple corrections ``c/N`` (``c`` one of eight
standard constants, ``N`` from 1 to 1000) that land inside the same
interval. There are dozens of them. ``pi/200`` is one member of a crowd
containing ``phi/103``, ``e/173`` and ``sqrt2/90``, and nothing in the
input distinguishes it from any of the others.

**Prospective use is gated.** A relation of this kind can only earn a
higher claim class by predicting numbers it was not fitted to. So
:func:`freeze_predictions` hashes and timestamps at least five statements
before any comparison, :func:`reveal` refuses to open a set that was never
frozen, and :func:`refuse_unfrozen_prediction` refuses the reveal-first,
freeze-later ordering outright.

**The search is not blind.** :func:`power_check` plants a target that IS
``base + pi/k`` for a frozen ``k`` and confirms the scan recovers it at
zero residual. So when the scan reports that ``51.843`` is matched by
dozens of expressions, that is a finding about ``51.843``, not a failure
of the scan.

Nothing here is measured. No object was surveyed, cut, or inspected; the
constants are closed forms evaluated with :mod:`decimal` at sixty digits
and the targets are numbers as supplied. The high-precision arctangent is
reused from :mod:`r11.geominverse` rather than reimplemented.
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import Enum

# The exact-constant machinery is reused, not rebuilt: geominverse already
# carries a Decimal arctangent with argument reduction and a Decimal pi,
# and it already evaluates atan(sqrt(phi)) to sixty digits.
from r11.geominverse import (
    DECIMAL_PRECISION,
    _dec_atan as dec_atan,
    _dec_pi as dec_pi,
    atan_sqrt_phi_deg,
    phi_exact,
)


class PiCorrectionError(ValueError):
    """Raised when the registry is asked to become a fitting tool.

    Covers a denominator outside the frozen set, a claim that the mixed
    units are consistent, a malformed relation or target, a prediction set
    revealed without having been frozen, and any attempt to promote a
    retrospective match above its claim class.
    """


class ClaimClass(Enum):
    """The claim classes this repository is allowed to emit."""

    EXACT_IDENTITY = "EXACT_IDENTITY"
    SOURCE_ESTABLISHED_PHYSICS = "SOURCE_ESTABLISHED_PHYSICS"
    REPOSITORY_COMPUTATIONAL_RESULT = "REPOSITORY_COMPUTATIONAL_RESULT"
    ENGINEERING_CANDIDATE = "ENGINEERING_CANDIDATE"
    RETROSPECTIVE_NUMERIC_MATCH = "RETROSPECTIVE_NUMERIC_MATCH"
    PROSPECTIVE_PREDICTION = "PROSPECTIVE_PREDICTION"
    BENCH_MEASUREMENT = "BENCH_MEASUREMENT"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"


class UnitValidity(Enum):
    """Whether the two sides of a relation are the same kind of quantity."""

    UNIT_CATEGORY_CONSISTENT = "UNIT_CATEGORY_CONSISTENT"
    UNIT_CATEGORY_MIXED = "UNIT_CATEGORY_MIXED"
    UNIT_CATEGORY_UNDECLARED = "UNIT_CATEGORY_UNDECLARED"


class HistoricalPlausibility(Enum):
    """What is known about the relation's provenance. Not much."""

    NOT_ESTABLISHED = "NOT_ESTABLISHED"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    NOT_ASSESSED = "NOT_ASSESSED"


class Preregistration(Enum):
    """When the relation was written down relative to the residual."""

    PREREGISTERED = "PREREGISTERED"
    RETROSPECTIVE = "RETROSPECTIVE"


#: The standing verdict. It is never upgraded by a smaller residual.
VERDICT = "PI_CORRECTION_REGISTRY_RETROSPECTIVE_ONLY"

#: The best claim class any relation in this registry can hold.
MAX_CLAIM_CLASS = ClaimClass.RETROSPECTIVE_NUMERIC_MATCH.value

PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: No mechanism is offered for any correction here, and none is known.
PHYSICAL_MECHANISM_STATUS = ClaimClass.UNSUPPORTED.value


# =======================================================================
# The frozen denominator set
# =======================================================================

#: Denominators fixed BEFORE any residual was scored. They are the
#: ordinary divisions of a circle (50, 60, 72, 90, 100, 120, 144, 180,
#: 200, 240, 360, 1000) and the ordinary binary divisions (192, 256, 512).
#: The set is frozen because the alternative -- choosing ``k`` after
#: seeing the gap -- turns any target into a hit, with the integer doing
#: all the work. Adding to it after the fact is refused.
FROZEN_DENOMINATORS: tuple[int, ...] = (
    50, 60, 72, 90, 100, 120, 144, 180, 192, 200, 240, 256, 360, 512, 1000,
)

#: Why the set was chosen, recorded so the choice can be argued with.
FROZEN_DENOMINATOR_RATIONALE = (
    "circle divisions in common use (50, 60, 72, 90, 100, 120, 144, 180, "
    "200, 240, 360, 1000) plus binary divisions (192, 256, 512). Fixed "
    "before any residual was computed and closed to additions afterwards")

#: Numerator constants available to a correction, also frozen. Eight
#: standard constants; nothing invented for the occasion.
FROZEN_NUMERATOR_CONSTANTS: tuple[str, ...] = (
    "pi", "e", "phi", "sqrt2", "sqrt3", "sqrt5", "ln2", "1",
)

#: How many corrections the frozen registry can express at all.
FROZEN_SEARCH_SPACE_SIZE = (len(FROZEN_NUMERATOR_CONSTANTS)
                            * len(FROZEN_DENOMINATORS))

#: The unfrozen space a reader could reach for if the cap were lifted:
#: the same constants over every denominator up to 1000.
UNFROZEN_MAX_DENOMINATOR = 1000
UNFROZEN_SEARCH_SPACE_SIZE = (len(FROZEN_NUMERATOR_CONSTANTS)
                              * UNFROZEN_MAX_DENOMINATOR)


def frozen_set_hash() -> str:
    """SHA-256 of the frozen sets, so a later edit is visible."""
    payload = "\x1f".join(
        (",".join(str(k) for k in FROZEN_DENOMINATORS),
         ",".join(FROZEN_NUMERATOR_CONSTANTS)))
    return hashlib.sha256(payload.encode()).hexdigest()


#: Computed once at import: the fingerprint of the frozen registry.
FROZEN_SET_HASH = frozen_set_hash()


def is_frozen_denominator(k: int) -> bool:
    """Was ``k`` in the set before any residual was looked at?"""
    if isinstance(k, bool) or not isinstance(k, int):
        raise PiCorrectionError("a denominator must be an integer")
    return int(k) in FROZEN_DENOMINATORS


def refuse_new_denominator(k: int, justification: str = "") -> dict:
    """Refuse any denominator that was not frozen before scoring.

    This is the red-team attack the registry exists to survive: observe a
    residual, then add the denominator that cancels it. With ``k`` free,
    ``c/k`` can be brought within an arbitrary distance of any gap, so a
    "match" found that way measures nothing except that the integers are
    dense. ``k = 201`` is refused for exactly the same reason ``k = 200``
    is allowed: not because one is prettier, but because one was written
    down first.

    A ``k`` that IS in the frozen set is not new, so it is returned with
    its provenance rather than refused.
    """
    if isinstance(k, bool) or not isinstance(k, int):
        raise PiCorrectionError("a denominator must be an integer")
    ki = int(k)
    if ki in FROZEN_DENOMINATORS:
        return {
            "denominator": ki,
            "status": "FROZEN_BEFORE_SCORING",
            "frozen_set_hash": FROZEN_SET_HASH,
            "frozen_set": list(FROZEN_DENOMINATORS),
            "note": ("already in the frozen set, so it is not a new "
                     "denominator and nothing is being added"),
        }
    tail = f" (justification offered: {justification!r})" if justification \
        else ""
    raise PiCorrectionError(
        f"refused: {ki} is not in the frozen denominator set "
        f"{FROZEN_DENOMINATORS}{tail}. The set was fixed before any "
        f"residual was scored (hash {FROZEN_SET_HASH[:16]}...) precisely "
        f"so that a denominator cannot be chosen to cancel a gap that has "
        f"already been seen. With k free, some c/k lands within any "
        f"tolerance of any target, and the 'match' reports the density of "
        f"the rationals rather than anything about the target. Verdict: "
        f"{VERDICT}.")


# =======================================================================
# Exact constants
# =======================================================================

def constant_value(name: str, precision: int = DECIMAL_PRECISION) -> Decimal:
    """One frozen numerator constant, evaluated to ``precision`` digits.

    Every constant is computed from its definition -- ``phi`` from
    ``(1 + sqrt(5))/2``, ``e`` from :meth:`Decimal.exp`, ``ln2`` from
    :meth:`Decimal.ln` -- so none of them is a pre-rounded literal that
    could be blamed later for a residual.
    """
    if name not in FROZEN_NUMERATOR_CONSTANTS:
        raise PiCorrectionError(
            f"{name!r} is not one of the frozen numerator constants "
            f"{FROZEN_NUMERATOR_CONSTANTS}")
    p = int(precision)
    if p < 2:
        raise PiCorrectionError("precision must be at least 2 digits")
    with localcontext() as ctx:
        ctx.prec = p + 10
        if name == "pi":
            value = dec_pi(p + 10)
        elif name == "e":
            value = Decimal(1).exp()
        elif name == "phi":
            value = phi_exact(p + 10)
        elif name == "sqrt2":
            value = Decimal(2).sqrt()
        elif name == "sqrt3":
            value = Decimal(3).sqrt()
        elif name == "sqrt5":
            value = Decimal(5).sqrt()
        elif name == "ln2":
            value = Decimal(2).ln()
        else:                                    # "1"
            value = Decimal(1)
    with localcontext() as ctx:
        ctx.prec = p
        return +value


def correction_value(name: str, denominator: int,
                     precision: int = DECIMAL_PRECISION) -> Decimal:
    """``c / N`` as a BARE NUMBER, to ``precision`` digits.

    Bare is the operative word. ``pi/200`` is ``0.015707963267948967``
    and it is added to a quantity in degrees. Whether that is legitimate
    is the subject of :func:`unit_validity`; this function only does the
    division.
    """
    if isinstance(denominator, bool) or not isinstance(denominator, int):
        raise PiCorrectionError("a denominator must be an integer")
    if int(denominator) == 0:
        raise PiCorrectionError("a denominator must be non-zero")
    p = int(precision)
    with localcontext() as ctx:
        ctx.prec = p + 10
        value = constant_value(name, p + 10) / Decimal(int(denominator))
    with localcontext() as ctx:
        ctx.prec = p
        return +value


def atan_one_over_sqrt8_deg(precision: int = DECIMAL_PRECISION) -> Decimal:
    """``atan(1/sqrt(8))`` in degrees -- the C2 control target.

    ``19.4712206344906913...`` degrees. It is a closed-form constant of
    the same family as ``atan(sqrt(phi))``, used here as a target that
    nobody has a historical story about, so that the registry's machinery
    can be exercised on a relation with no narrative attached.
    """
    p = int(precision)
    with localcontext() as ctx:
        ctx.prec = p + 10
        arg = Decimal(1) / Decimal(8).sqrt()
        value = dec_atan(arg, p + 10) * Decimal(180) / dec_pi(p + 10)
    with localcontext() as ctx:
        ctx.prec = p
        return +value


def _base_c1(precision: int) -> Decimal:
    """``atan(sqrt(phi))`` in degrees. Reused from geominverse."""
    return atan_sqrt_phi_deg(precision)


def _base_c2(precision: int) -> Decimal:
    """``63 / (2 phi)`` in degrees-as-declared."""
    p = int(precision)
    with localcontext() as ctx:
        ctx.prec = p + 10
        value = Decimal(63) / (Decimal(2) * phi_exact(p + 10))
    with localcontext() as ctx:
        ctx.prec = p
        return +value


def _target_c1(precision: int) -> Decimal:
    """The supplied slope ``51.843``, exactly as quoted."""
    return Decimal(SUPPLIED_TARGET_C1_STR)


def _target_c2(precision: int) -> Decimal:
    """``atan(1/sqrt(8))`` in degrees."""
    return atan_one_over_sqrt8_deg(precision)


#: The supplied slope, carried as the STRING it was quoted as, because
#: the number of decimals in that string is load-bearing evidence.
SUPPLIED_TARGET_C1_STR = "51.843"

#: Closed-form evaluators, keyed so a relation can name them without
#: carrying callables through a frozen dataclass.
_EVALUATORS: dict[str, object] = {
    "atan(sqrt(phi))": _base_c1,
    "63/(2*phi)": _base_c2,
    "51.843": _target_c1,
    "atan(1/sqrt(8))": _target_c2,
}


# =======================================================================
# A registered relation
# =======================================================================

@dataclass(frozen=True)
class PiRelation:
    """One ``base + c/N`` candidate, with everything that prices it.

    The complexity fields are counted by hand and stored rather than
    parsed, so the description length of a relation is a declared number
    that can be argued with rather than an artefact of a tokenizer.
    """

    relation_id: str
    base_closed_form: str
    numerator_constant: str
    denominator: int
    target_closed_form: str
    target_quoted_str: str            # "" when the target is a closed form
    n_operations: int
    n_constants: int
    preregistration: Preregistration = Preregistration.RETROSPECTIVE
    historical_plausibility: HistoricalPlausibility = \
        HistoricalPlausibility.NOT_ASSESSED
    note: str = ""

    def __post_init__(self) -> None:
        if self.numerator_constant not in FROZEN_NUMERATOR_CONSTANTS:
            raise PiCorrectionError(
                f"{self.numerator_constant!r} is not a frozen numerator "
                f"constant")
        if int(self.denominator) not in FROZEN_DENOMINATORS:
            raise PiCorrectionError(
                f"denominator {self.denominator} is not in the frozen set; "
                f"see refuse_new_denominator")
        for key in (self.base_closed_form, self.target_closed_form):
            if key not in _EVALUATORS:
                raise PiCorrectionError(f"no evaluator for {key!r}")
        if self.n_operations < 1 or self.n_constants < 1:
            raise PiCorrectionError("complexity counts must be positive")

    # --- evaluation ----------------------------------------------------

    def base_deg(self, precision: int = DECIMAL_PRECISION) -> Decimal:
        return _EVALUATORS[self.base_closed_form](int(precision))

    def correction_deg(self, precision: int = DECIMAL_PRECISION) -> Decimal:
        """The bare number ``c/N``, declared to be degrees. See units."""
        return correction_value(self.numerator_constant, self.denominator,
                                int(precision))

    def predicted_deg(self, precision: int = DECIMAL_PRECISION) -> Decimal:
        p = int(precision)
        with localcontext() as ctx:
            ctx.prec = p + 10
            value = self.base_deg(p + 10) + self.correction_deg(p + 10)
        with localcontext() as ctx:
            ctx.prec = p
            return +value

    def target_deg(self, precision: int = DECIMAL_PRECISION) -> Decimal:
        return _EVALUATORS[self.target_closed_form](int(precision))

    def exact_residual(self, precision: int = DECIMAL_PRECISION) -> Decimal:
        """``target - (base + c/N)``, signed, never rounded at the claim."""
        p = int(precision)
        with localcontext() as ctx:
            ctx.prec = p + 10
            value = self.target_deg(p + 10) - self.predicted_deg(p + 10)
        with localcontext() as ctx:
            ctx.prec = p
            return +value

    def relative_residual(self,
                          precision: int = DECIMAL_PRECISION) -> Decimal:
        p = int(precision)
        with localcontext() as ctx:
            ctx.prec = p + 10
            value = self.exact_residual(p + 10) / self.target_deg(p + 10)
        with localcontext() as ctx:
            ctx.prec = p
            return +value

    # --- pricing --------------------------------------------------------

    def expression_text(self) -> str:
        return (f"{self.base_closed_form} + {self.numerator_constant}"
                f"/{self.denominator}")

    def complexity(self) -> int:
        """Description length: operation count plus constant count.

        Longer expressions buy less. An expression assembled from more
        pieces is one of far more expressions that were available, so the
        same residual reached by a longer route is cheaper evidence.
        """
        return int(self.n_operations) + int(self.n_constants)


def description_length(relation: PiRelation) -> int:
    """Module-level alias for :meth:`PiRelation.complexity`."""
    if not isinstance(relation, PiRelation):
        raise PiCorrectionError("expected a PiRelation")
    return relation.complexity()


# --- the two registered relations --------------------------------------

#: C1 -- the headline. atan(sqrt(phi)) + pi/200 against the quoted 51.843.
#: Operations: atan, sqrt, the division pi/200, the addition = 4.
#: Constants: phi, pi, 200 = 3.
RELATION_C1 = PiRelation(
    relation_id="C1",
    base_closed_form="atan(sqrt(phi))",
    numerator_constant="pi",
    denominator=200,
    target_closed_form="51.843",
    target_quoted_str=SUPPLIED_TARGET_C1_STR,
    n_operations=4,
    n_constants=3,
    preregistration=Preregistration.RETROSPECTIVE,
    historical_plausibility=HistoricalPlausibility.NOT_ESTABLISHED,
    note=("the correction was chosen after the 0.0157 degree gap was in "
          "view, and the target is quoted to three decimals"),
)

#: C2 -- a control with no narrative. 63/(2 phi) + pi/1000 against
#: atan(1/sqrt(8)), a closed-form target quoted to full precision.
#: Operations: the product 2*phi, the division by it, the division
#: pi/1000, the addition = 4. Constants: 63, 2, phi, pi, 1000 = 5.
RELATION_C2 = PiRelation(
    relation_id="C2",
    base_closed_form="63/(2*phi)",
    numerator_constant="pi",
    denominator=1000,
    target_closed_form="atan(1/sqrt(8))",
    target_quoted_str="",
    n_operations=4,
    n_constants=5,
    preregistration=Preregistration.RETROSPECTIVE,
    historical_plausibility=HistoricalPlausibility.NOT_APPLICABLE,
    note=("a control: the target is a closed-form constant carried to "
          "full precision, so the input-precision defence is unavailable "
          "and the residual has to stand on its own. It is 8.4e-06 "
          "degrees -- twenty-five times worse than C1's"),
)

REGISTERED_RELATIONS: tuple[PiRelation, ...] = (RELATION_C1, RELATION_C2)


def get_relation(relation_id: str) -> PiRelation:
    for r in REGISTERED_RELATIONS:
        if r.relation_id == relation_id:
            return r
    raise PiCorrectionError(
        f"no registered relation {relation_id!r}; the registry holds "
        f"{[r.relation_id for r in REGISTERED_RELATIONS]} and is closed")


# =======================================================================
# Units -- load-bearing, and mixed
# =======================================================================

#: pi radians = 180 degrees. Used to show what pi/N would be if the
#: correction were honestly a radian quantity.
DEGREES_PER_HALF_TURN = 180


def unit_validity(relation: PiRelation) -> str:
    """Are the two sides of the relation the same kind of quantity? No.

    ``pi/200`` is a radian-flavoured number: ``pi`` enters trigonometry as
    a half turn, and ``pi/200`` radians is ``0.9`` degrees exactly. The
    relation does not add ``0.9`` degrees. It adds the *bare number*
    ``0.0157079...`` to a quantity expressed in degrees, which requires
    the bare number to be relabelled as degrees on the way in. That is a
    change of category, not a unit conversion, and it is why both
    registered relations return ``UNIT_CATEGORY_MIXED``.

    The label is not a disqualification. Mixed-unit numerology is still
    arithmetic, and the arithmetic reproduces. The label records what the
    arithmetic needed in order to work.
    """
    if not isinstance(relation, PiRelation):
        raise PiCorrectionError("expected a PiRelation")
    return UnitValidity.UNIT_CATEGORY_MIXED.value


def unit_analysis(relation: PiRelation,
                  precision: int = DECIMAL_PRECISION) -> dict:
    """The numbers behind :func:`unit_validity`, spelled out."""
    if not isinstance(relation, PiRelation):
        raise PiCorrectionError("expected a PiRelation")
    p = int(precision)
    bare = relation.correction_deg(p)
    with localcontext() as ctx:
        ctx.prec = p + 10
        # If the correction were honestly radians, it would be this many
        # degrees. For pi/N that is exactly 180/N.
        as_radians_in_deg = (relation.correction_deg(p + 10)
                             * Decimal(DEGREES_PER_HALF_TURN)
                             / dec_pi(p + 10))
        if_converted = relation.base_deg(p + 10) + as_radians_in_deg
        converted_residual = relation.target_deg(p + 10) - if_converted
    return {
        "relation_id": relation.relation_id,
        "unit_validity": unit_validity(relation),
        "correction_expression": (f"{relation.numerator_constant}"
                                  f"/{relation.denominator}"),
        "correction_bare_number": float(bare),
        "correction_bare_number_exact": str(+bare),
        "correction_if_read_as_radians_deg": float(+as_radians_in_deg),
        "base_is_in": "degrees",
        "correction_is_in": "DECLARED_DEGREES_BUT_RADIAN_FLAVOURED",
        "value_if_units_were_honoured_deg": float(+if_converted),
        "residual_if_units_were_honoured_deg": float(+converted_residual),
        "ratio_radian_to_bare": float(
            Decimal(DEGREES_PER_HALF_TURN) / dec_pi(p)),
        "verdict": VERDICT,
        "note": (
            "read as radians the correction is 180/N degrees -- 0.9 "
            "degrees for N=200, 0.18 for N=1000 -- which overshoots the "
            "gap by a factor of about 57.3. The relation therefore "
            "requires the bare number to be CALLED degrees. That is "
            "recorded, not hidden, and it does not by itself refute the "
            "relation: it classifies it"),
    }


def refuse_unit_confusion(relation: PiRelation = RELATION_C1,
                          claimed_consistent: bool = True) -> None:
    """Refuse the claim that the mixed-unit arithmetic is consistent.

    Always. A claim of dimensional consistency is a claim that ``pi/200``
    entered the sum as the angle it denotes, and it did not: as an angle
    it is ``0.9`` degrees, which would put the sum at ``52.727`` degrees
    and miss the target by nearly a degree. The relation needs the bare
    number, and needing the bare number is what
    ``UNIT_CATEGORY_MIXED`` means.
    """
    if not isinstance(relation, PiRelation):
        raise PiCorrectionError("expected a PiRelation")
    a = unit_analysis(relation)
    raise PiCorrectionError(
        f"refused: {relation.expression_text()} is not dimensionally "
        f"consistent (claimed_consistent={bool(claimed_consistent)}). The "
        f"correction {a['correction_expression']} enters as the bare "
        f"number {a['correction_bare_number']!r} declared to be degrees. "
        f"Read as the angle it denotes it is "
        f"{a['correction_if_read_as_radians_deg']!r} degrees, which puts "
        f"the sum at {a['value_if_units_were_honoured_deg']!r} degrees and "
        f"misses the target by "
        f"{a['residual_if_units_were_honoured_deg']!r} degrees. The "
        f"relation is registered as "
        f"{UnitValidity.UNIT_CATEGORY_MIXED.value}, which is a "
        f"classification and not a conversion. Verdict: {VERDICT}.")


# =======================================================================
# Input precision -- the decisive test
# =======================================================================

def input_precision_slack(target_str: str) -> float:
    """Half-unit-in-the-last-place implied by how the target was quoted.

    ``"51.843"`` carries three decimals, so it stands for the interval
    ``51.843 +/- 0.0005``. Everything below that interval is a digit the
    input never had, and a relation cannot be credited for agreeing with
    digits that were never supplied.

    Returned as a float because it is a tolerance, not a claim; the exact
    value is available from :func:`input_precision_slack_exact`.
    """
    return float(input_precision_slack_exact(target_str))


def input_precision_slack_exact(target_str: str) -> Decimal:
    """:func:`input_precision_slack` as an exact :class:`Decimal`."""
    if not isinstance(target_str, str):
        raise PiCorrectionError(
            "the target must be passed as the STRING it was quoted as; the "
            "number of decimals is the evidence")
    text = target_str.strip()
    if not text:
        raise PiCorrectionError("empty target string")
    try:
        Decimal(text)
    except Exception as exc:                      # pragma: no cover - guard
        raise PiCorrectionError(f"{target_str!r} is not a number") from exc
    if "e" in text.lower():
        raise PiCorrectionError(
            "exponent notation hides the quoted precision; pass the "
            "target as it was written")
    decimals = len(text.split(".", 1)[1]) if "." in text else 0
    return Decimal(5).scaleb(-(decimals + 1))


def quoted_decimals(target_str: str) -> int:
    """How many decimals the target was quoted to."""
    input_precision_slack_exact(target_str)       # validation
    text = target_str.strip()
    return len(text.split(".", 1)[1]) if "." in text else 0


def candidates_within_slack(target: float | str | Decimal
                            = SUPPLIED_TARGET_C1_STR,
                            slack: float | Decimal | None = None,
                            base_closed_form: str = "atan(sqrt(phi))",
                            max_denominator: int
                            = UNFROZEN_MAX_DENOMINATOR,
                            precision: int = 40) -> dict:
    """How many simple ``c/N`` corrections land inside the input's slack?

    The relation says ``base + c/N`` reproduces the target. The target is
    known only to within ``slack``. So the honest question is not "how
    close does ``pi/200`` get" but "how many corrections get inside the
    interval the target actually occupies" -- because every one of them
    reproduces the target exactly as well as the input can tell.

    ``c`` ranges over the eight frozen constants and ``N`` over
    ``1..max_denominator``. Every ``c/N`` with

        ``|base + c/N - target| <= slack``

    is counted. There are dozens. ``pi/200`` is among them, and so are
    ``phi/103``, ``e/173`` and ``sqrt2/90``; the input cannot separate
    them, and neither can anyone quoting it.
    """
    p = int(precision)
    if int(max_denominator) < 1:
        raise PiCorrectionError("max_denominator must be at least 1")
    if isinstance(target, str):
        target_dec = Decimal(target.strip())
        if slack is None:
            slack = input_precision_slack_exact(target)
    else:
        target_dec = Decimal(str(target))
    if slack is None:
        raise PiCorrectionError(
            "a numeric target carries no quoted precision; pass the slack "
            "explicitly or pass the target as the string it was quoted as")
    slack_dec = Decimal(str(slack))
    if slack_dec < 0:
        raise PiCorrectionError("slack must be non-negative")
    if base_closed_form not in _EVALUATORS:
        raise PiCorrectionError(f"no evaluator for {base_closed_form!r}")

    with localcontext() as ctx:
        ctx.prec = p
        base = Decimal(_EVALUATORS[base_closed_form](p))
        gap = target_dec - base
        lo = gap - slack_dec
        hi = gap + slack_dec
        members: list[dict] = []
        for name in FROZEN_NUMERATOR_CONSTANTS:
            c = constant_value(name, p)
            for n in range(1, int(max_denominator) + 1):
                v = c / Decimal(n)
                if lo <= v <= hi:
                    members.append({
                        "correction": f"{name}/{n}",
                        "constant": name,
                        "denominator": n,
                        "value": float(v),
                        "predicted_deg": float(base + v),
                        "residual_deg": float(target_dec - base - v),
                        "in_frozen_set": n in FROZEN_DENOMINATORS,
                    })

    best = min(members, key=lambda m: abs(m["residual_deg"])) \
        if members else None
    return {
        "target": str(target),
        "target_value": float(target_dec),
        "base_closed_form": base_closed_form,
        "base_deg": float(base),
        "gap_to_close_deg": float(gap),
        "slack": float(slack_dec),
        "interval_deg": [float(target_dec - slack_dec),
                         float(target_dec + slack_dec)],
        "constants_searched": list(FROZEN_NUMERATOR_CONSTANTS),
        "max_denominator": int(max_denominator),
        "search_space_size": (len(FROZEN_NUMERATOR_CONSTANTS)
                              * int(max_denominator)),
        "count": len(members),
        "members": members,
        "best_member": best,
        "contains_pi_over_200": any(m["correction"] == "pi/200"
                                    for m in members),
        "distinct_constants": sorted({m["constant"] for m in members}),
        "verdict": VERDICT,
        "note": (
            "every listed correction reproduces the target as well as the "
            "target's own quoted precision can tell. A count in the dozens "
            "means the relation identifies a neighbourhood, not an "
            "expression"),
    }


def precision_audit(relation: PiRelation = RELATION_C1,
                    precision: int = DECIMAL_PRECISION) -> dict:
    """The decisive comparison: agreement against the input's own slack.

    C1 agrees to ``3.36e-07`` degrees with a number quoted to
    ``+/-0.0005``. The agreement is therefore roughly fifteen hundred
    times finer than the input's resolution. That ratio is not a measure
    of how good the relation is; it is a measure of how much of the
    agreement is unfalsifiable. Digits below the input's precision cannot
    discriminate between candidate expressions, and
    :func:`candidates_within_slack` counts how many candidates they fail
    to discriminate.
    """
    if not isinstance(relation, PiRelation):
        raise PiCorrectionError("expected a PiRelation")
    if not relation.target_quoted_str:
        return {
            "relation_id": relation.relation_id,
            "target_is_quoted_decimal": False,
            "input_precision_slack": None,
            "note": ("the target is a closed-form constant carried to full "
                     "precision, so there is no quoted slack to hide in "
                     "and the residual stands on its own"),
            "exact_residual_deg": float(relation.exact_residual(precision)),
            "verdict": VERDICT,
        }
    p = int(precision)
    slack = input_precision_slack_exact(relation.target_quoted_str)
    resid = abs(relation.exact_residual(p))
    with localcontext() as ctx:
        ctx.prec = 30
        ratio = (slack / resid) if resid != 0 else Decimal("Infinity")
    cands = candidates_within_slack(relation.target_quoted_str, slack,
                                    relation.base_closed_form)
    return {
        "relation_id": relation.relation_id,
        "target_is_quoted_decimal": True,
        "target_quoted": relation.target_quoted_str,
        "quoted_decimals": quoted_decimals(relation.target_quoted_str),
        "input_precision_slack": float(slack),
        "exact_residual_deg": float(relation.exact_residual(p)),
        "abs_residual_deg": float(resid),
        "agreement_finer_than_input_by_factor": float(ratio),
        "extra_precision_is_informative": False,
        "candidates_within_slack": cands["count"],
        "example_indistinguishable": [m["correction"] for m in
                                      cands["members"][:8]],
        "claim_class": ClaimClass.RETROSPECTIVE_NUMERIC_MATCH.value,
        "verdict": VERDICT,
        "note": (
            "the relation agrees with the target far below the precision "
            "the target was quoted to. Agreement below the input's "
            "resolution cannot distinguish pi/200 from any of the other "
            "corrections that land in the same interval, so the extra "
            "digits are not informative and the claim class is capped at "
            "RETROSPECTIVE_NUMERIC_MATCH"),
    }


# =======================================================================
# The scan, and the power control that shows it works
# =======================================================================

def best_frozen_correction(target: float | str | Decimal,
                           base_closed_form: str = "atan(sqrt(phi))",
                           precision: int = DECIMAL_PRECISION) -> dict:
    """Closest ``c/N`` in the FROZEN registry to a target. Exact residual.

    Ties are broken by the shorter description: a correction reached with
    a smaller denominator is cheaper than the same residual reached with a
    larger one.
    """
    p = int(precision)
    if base_closed_form not in _EVALUATORS:
        raise PiCorrectionError(f"no evaluator for {base_closed_form!r}")
    target_dec = Decimal(str(target))
    with localcontext() as ctx:
        ctx.prec = p
        base = Decimal(_EVALUATORS[base_closed_form](p))
        best: dict | None = None
        for name in FROZEN_NUMERATOR_CONSTANTS:
            c = constant_value(name, p)
            for n in FROZEN_DENOMINATORS:
                v = c / Decimal(n)
                resid = target_dec - base - v
                key = (abs(resid), n)
                if best is None or key < best["_key"]:
                    best = {
                        "_key": key,
                        "correction": f"{name}/{n}",
                        "constant": name,
                        "denominator": n,
                        "predicted_deg": float(base + v),
                        "predicted_deg_exact": str(base + v),
                        "residual_deg": float(resid),
                        "residual_deg_exact": str(resid),
                        "abs_residual_deg": float(abs(resid)),
                    }
    assert best is not None
    best.pop("_key")
    best["target"] = float(target_dec)
    best["base_closed_form"] = base_closed_form
    best["search_space_size"] = FROZEN_SEARCH_SPACE_SIZE
    return best


#: The planted relation for the power control: a target constructed to BE
#: ``atan(sqrt(phi)) + pi/144`` exactly, at working precision. 144 is in
#: the frozen set and is not the C1 denominator, so recovering it is a
#: statement about the scan rather than about 51.843.
PLANTED_CONSTANT = "pi"
PLANTED_DENOMINATOR = 144


def planted_target(precision: int = DECIMAL_PRECISION) -> Decimal:
    """``atan(sqrt(phi)) + pi/144``, exact at ``precision`` digits."""
    p = int(precision)
    with localcontext() as ctx:
        ctx.prec = p + 10
        value = (_base_c1(p + 10)
                 + correction_value(PLANTED_CONSTANT, PLANTED_DENOMINATOR,
                                    p + 10))
    with localcontext() as ctx:
        ctx.prec = p
        return +value


def power_check(precision: int = DECIMAL_PRECISION) -> dict:
    """Plant an exact relation and confirm the scan recovers it at ~0.

    Without this the registry's headline would be ambiguous: a scan that
    found nothing would report the same "no distinguished expression"
    result for the wrong reason. The scan finds the planted correction at
    a residual of zero to the working precision, so its report about
    ``51.843`` -- that dozens of corrections are indistinguishable -- is a
    finding about the target and not a failure of the search.
    """
    p = int(precision)
    target = planted_target(p)
    hit = best_frozen_correction(target, "atan(sqrt(phi))", p)
    expected = f"{PLANTED_CONSTANT}/{PLANTED_DENOMINATOR}"
    return {
        "planted_correction": expected,
        "planted_target_deg": float(target),
        "planted_target_exact": str(target),
        "recovered": hit,
        "recovered_correction": hit["correction"],
        "recovered_equals_planted": hit["correction"] == expected,
        "abs_residual_deg": hit["abs_residual_deg"],
        "detected": (hit["correction"] == expected
                     and hit["abs_residual_deg"] < 1e-30),
        "note": (
            "the scan recovers a planted exact correction at zero "
            "residual, so it has the power to single out an expression "
            "when one is genuinely singled out. That it cannot single one "
            "out for 51.843 is a finding about 51.843"),
    }


# =======================================================================
# Prospective use: freeze first, or not at all
# =======================================================================

#: A prediction set smaller than this is not a test, it is an anecdote.
MIN_PREDICTIONS = 5


@dataclass(frozen=True)
class FrozenPredictionSet:
    """Predictions hashed and timestamped before any comparison."""

    set_id: str
    predictions: tuple[str, ...]
    frozen_at_unix: float
    prereg_hash: str
    claim_class: str = ClaimClass.PROSPECTIVE_PREDICTION.value

    def as_dict(self) -> dict:
        return {
            "set_id": self.set_id,
            "predictions": list(self.predictions),
            "n_predictions": len(self.predictions),
            "frozen_at_unix": self.frozen_at_unix,
            "prereg_hash": self.prereg_hash,
            "claim_class": self.claim_class,
        }


def _prereg_hash(set_id: str, predictions: tuple[str, ...],
                 frozen_at_unix: float) -> str:
    payload = "\x1f".join((set_id, f"{frozen_at_unix:.6f}", *predictions))
    return hashlib.sha256(payload.encode()).hexdigest()


#: The freeze registry. Append-only within a process: a set is frozen
#: once and never rewritten, because a rewritable freeze is not one.
_FROZEN_SETS: dict[str, FrozenPredictionSet] = {}


def freeze_predictions(preds, set_id: str = "PI_CORRECTION_PROSPECTIVE_1"
                       ) -> FrozenPredictionSet:
    """Hash and timestamp at least five predictions BEFORE comparison.

    This is the only route by which a pi-correction relation could ever
    reach ``PROSPECTIVE_PREDICTION``. It requires statements that were
    written down before their targets were known, in a quantity large
    enough that one lucky hit does not carry the set.
    """
    if isinstance(preds, str):
        raise PiCorrectionError(
            "predictions must be a sequence of statements, not one string")
    items = tuple(str(p).strip() for p in preds)
    if any(not p for p in items):
        raise PiCorrectionError("a prediction may not be empty")
    if len(items) < MIN_PREDICTIONS:
        raise PiCorrectionError(
            f"a prospective set needs at least {MIN_PREDICTIONS} "
            f"predictions; {len(items)} were offered. Fewer than that and "
            f"a single coincidence carries the whole result")
    if len(set(items)) != len(items):
        raise PiCorrectionError(
            "duplicate predictions inflate the count without adding a test")
    if set_id in _FROZEN_SETS:
        raise PiCorrectionError(
            f"{set_id!r} is already frozen; a freeze that can be rewritten "
            f"is not a freeze. Choose a new set_id")
    frozen_at = time.time()
    record = FrozenPredictionSet(
        set_id=str(set_id),
        predictions=items,
        frozen_at_unix=frozen_at,
        prereg_hash=_prereg_hash(str(set_id), items, frozen_at),
    )
    _FROZEN_SETS[str(set_id)] = record
    return record


def is_frozen(set_id: str) -> bool:
    """Was this set_id frozen in this process?"""
    return str(set_id) in _FROZEN_SETS


def frozen_set(set_id: str) -> FrozenPredictionSet:
    """The frozen record, or a refusal."""
    if not is_frozen(set_id):
        refuse_unfrozen_prediction(set_id=str(set_id))
    return _FROZEN_SETS[str(set_id)]


def reveal(set_id: str, predictions=None) -> dict:
    """Open a frozen set. Refuses anything that was never frozen.

    If ``predictions`` are supplied they are re-hashed and checked against
    the frozen hash, so a set cannot be quietly edited between the freeze
    and the reveal. Outcomes are not available in this environment, so
    every prediction is returned ``AWAITING_OUTCOME``: freezing is the
    part that can be done honestly here, scoring is not.
    """
    record = frozen_set(set_id)
    if predictions is not None:
        items = tuple(str(p).strip() for p in predictions)
        if _prereg_hash(record.set_id, items,
                        record.frozen_at_unix) != record.prereg_hash:
            raise PiCorrectionError(
                f"refused: the predictions offered for {record.set_id!r} do "
                f"not hash to the frozen value {record.prereg_hash[:16]}..."
                f" A set edited between the freeze and the reveal is a "
                f"retrospective set wearing a timestamp")
    return {
        "set_id": record.set_id,
        "prereg_hash": record.prereg_hash,
        "frozen_at_unix": record.frozen_at_unix,
        "predictions": list(record.predictions),
        "n_predictions": len(record.predictions),
        "hash_verified": predictions is not None,
        "outcome_status": "AWAITING_OUTCOME",
        "claim_class": ClaimClass.PROSPECTIVE_PREDICTION.value,
        "note": ("frozen before comparison. No outcome is available in "
                 "this environment, so nothing is scored and nothing is "
                 "claimed"),
    }


def refuse_unfrozen_prediction(statement: str = "",
                               set_id: str = "") -> None:
    """Refuse a prediction revealed without having been frozen first.

    A statement produced after its target is in view is a description, not
    a prediction, however it is phrased. The freeze is what makes the
    difference, and it cannot be applied retroactively: that is the whole
    content of the word.
    """
    tail = f" statement={statement!r}" if statement else ""
    raise PiCorrectionError(
        f"refused: prediction set {set_id!r} was never frozen.{tail} A "
        f"prediction must be hashed and timestamped by "
        f"freeze_predictions() -- at least {MIN_PREDICTIONS} statements -- "
        f"BEFORE any comparison is made. Revealing first and freezing "
        f"afterwards produces a RETROSPECTIVE_NUMERIC_MATCH wearing the "
        f"label PROSPECTIVE_PREDICTION, which is the substitution this "
        f"registry exists to block. Verdict: {VERDICT}.")


def refuse_claim_upgrade(relation: PiRelation = RELATION_C1,
                         claimed_class: str =
                         ClaimClass.SOURCE_ESTABLISHED_PHYSICS.value
                         ) -> None:
    """Refuse to promote a registered relation above its cap."""
    raise PiCorrectionError(
        f"refused: relation {relation.relation_id} may not be reported as "
        f"{claimed_class}. It is a retrospective arithmetic match with "
        f"mixed units, no mechanism, and a residual finer than its own "
        f"input's precision. Its cap is {MAX_CLAIM_CLASS} and the only "
        f"route past it is a frozen prospective set that survives its "
        f"outcomes. Verdict: {VERDICT}.")


# =======================================================================
# Per-relation report
# =======================================================================

def relation_report(relation: PiRelation,
                    precision: int = DECIMAL_PRECISION) -> dict:
    """Everything a registered relation must carry when it is quoted."""
    if not isinstance(relation, PiRelation):
        raise PiCorrectionError("expected a PiRelation")
    p = int(precision)
    resid = relation.exact_residual(p)
    rel = relation.relative_residual(p)
    return {
        "relation_id": relation.relation_id,
        "expression": relation.expression_text(),
        "base_closed_form": relation.base_closed_form,
        "base_deg": float(relation.base_deg(p)),
        "base_deg_exact": str(relation.base_deg(p)),
        "correction": (f"{relation.numerator_constant}"
                       f"/{relation.denominator}"),
        "correction_deg": float(relation.correction_deg(p)),
        "correction_deg_exact": str(relation.correction_deg(p)),
        "predicted_deg": float(relation.predicted_deg(p)),
        "predicted_deg_exact": str(relation.predicted_deg(p)),
        "target_closed_form": relation.target_closed_form,
        "target_quoted_str": relation.target_quoted_str,
        "target_deg": float(relation.target_deg(p)),
        "target_deg_exact": str(relation.target_deg(p)),
        "exact_residual": float(resid),
        "exact_residual_str": str(resid),
        "relative_residual": float(rel),
        "search_space_size": FROZEN_SEARCH_SPACE_SIZE,
        "unfrozen_search_space_size": UNFROZEN_SEARCH_SPACE_SIZE,
        "complexity": relation.complexity(),
        "complexity_breakdown": {
            "n_operations": relation.n_operations,
            "n_constants": relation.n_constants,
        },
        "preregistered_or_retrospective": relation.preregistration.value,
        "unit_validity": unit_validity(relation),
        "unit_analysis": unit_analysis(relation, p),
        "historical_plausibility": relation.historical_plausibility.value,
        "physical_mechanism_status": PHYSICAL_MECHANISM_STATUS,
        "input_precision": precision_audit(relation, p),
        "claim_class": ClaimClass.RETROSPECTIVE_NUMERIC_MATCH.value,
        "verdict": VERDICT,
        "note": relation.note,
    }


def picorrection_report(precision: int = DECIMAL_PRECISION) -> dict:
    """The registry, its cap, and the reasons the cap is where it is."""
    relations = [relation_report(r, precision) for r in REGISTERED_RELATIONS]
    audit = precision_audit(RELATION_C1, precision)
    return {
        "what_this_is": (
            "a closed registry of pi-correction candidates, each priced by "
            "its residual, its search space, its description length, its "
            "unit validity, and -- decisively -- the precision of the "
            "input it is compared against"),
        "frozen_denominators": list(FROZEN_DENOMINATORS),
        "frozen_numerator_constants": list(FROZEN_NUMERATOR_CONSTANTS),
        "frozen_denominator_rationale": FROZEN_DENOMINATOR_RATIONALE,
        "frozen_set_hash": FROZEN_SET_HASH,
        "search_space_size": FROZEN_SEARCH_SPACE_SIZE,
        "registry_size": len(REGISTERED_RELATIONS),
        "relations": relations,
        "input_precision_audit": audit,
        "candidates_within_slack": audit.get("candidates_within_slack"),
        "power_control": power_check(precision),
        "prospective_gate": {
            "min_predictions": MIN_PREDICTIONS,
            "mechanism": "freeze_predictions() then reveal()",
            "frozen_sets_in_process": sorted(_FROZEN_SETS),
            "outcome_status": "AWAITING_OUTCOME",
        },
        "refusals": [
            "refuse_new_denominator",
            "refuse_unit_confusion",
            "refuse_unfrozen_prediction",
            "refuse_claim_upgrade",
        ],
        "claim_class": ClaimClass.RETROSPECTIVE_NUMERIC_MATCH.value,
        "max_claim_class": MAX_CLAIM_CLASS,
        "physical_mechanism_status": PHYSICAL_MECHANISM_STATUS,
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say that 51.843 degrees was derived from "
            "atan(sqrt(phi)) plus pi/200, that pi/200 is a correction to "
            "anything, or that any physical mechanism produces it -- the "
            "mechanism status is UNSUPPORTED and no mechanism is offered. "
            "It does not say the seven-digit agreement is evidence: the "
            "target is quoted to three decimals, so it carries "
            "+/-0.0005 degrees of slack, the agreement is about fifteen "
            "hundred times finer than that, and dozens of equally simple "
            "corrections land inside the same interval -- pi/200 cannot be "
            "distinguished from phi/103, e/173 or sqrt2/90 by the input. "
            "It does not say the arithmetic is dimensionally consistent: "
            "pi/200 is a bare number declared to be degrees, and as an "
            "angle it would be 0.9 degrees, so both relations are "
            "UNIT_CATEGORY_MIXED. It does not permit the registry to grow: "
            "the denominators were frozen before scoring and additions are "
            "refused. And it does not claim any prospective standing -- no "
            "prediction set has been frozen and scored, and until one is, "
            "the claim class is capped at RETROSPECTIVE_NUMERIC_MATCH. "
            "Nothing here was measured."),
        "verdict": VERDICT,
    }
