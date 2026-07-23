"""P11 — the constrained centroid inverse: one point and one tone do not
make a shape.

Two questions are asked here, and both are answered with a refusal.

**The angle.** ``atan(sqrt(phi))`` is a real constant of the golden
ratio and it can be computed to any precision wanted. Written out to
high precision it is ``51.827292372987756...`` degrees. A slope of
``51.843`` degrees is often quoted alongside it as though the two were
the same number. They are not::

    51.843 - 51.827292372987756 = 0.01570762701224737   degrees

That gap is about 56.5 arcseconds. It is small, it is real, and it does
not go away when the numbers are rounded -- rounding is exactly how it
disappears. The two agree to three significant figures, which is to say
to ONE decimal place: both are 51.8. At two decimals they already part
company, 51.84 against 51.83. So a comparison quoted to the precision at
which the resemblance is visible is a comparison that has thrown the
evidence away, which is why this module never rounds at the comparison. ``phi`` is carried as a closed form and
evaluated with :mod:`decimal` at high precision rather than stored as a
pre-rounded float, ``compare_to`` returns the difference rather than a
boolean, and the standing label for the pair is
``APPROXIMATE_NOT_EXACT``. The resemblance is a numeric coincidence in
the fourth significant figure; it is not a derivation, and
:func:`refuse_exact_angle_claim` refuses to let it be reported as one.

**The geometry.** The headline question is the inverse one: *what body
has its centroid at ``(0, 0, 100 mm)`` and rings at a given frequency?*
The honest answer is that the question does not have an answer. A
centroid coordinate is one scalar. A fundamental frequency is one
scalar. A body -- even a deliberately impoverished one -- is described
by more than two numbers, and two equations cannot pin down five
unknowns.

The parametric family used to show this is an axisymmetric solid with a
linearly tapering radius, described by five parameters: overall height,
base radius, taper, density and stiffness. Its centroid is available in
closed form::

    r(z) = r0 (1 - t z/H),  0 <= z <= H

    centroid_z = H * (1/2 - 2t/3 + t^2/4) / (1 - t + t^2/3)

and its fundamental is a declared ANALYTIC_MODEL -- the free-free
longitudinal bar mode ``f = sqrt(E/rho) / (2 L)`` -- chosen because it is
simple, standard and obviously not a statement about any real object.

The structure of the degeneracy is visible without any search at all.
The centroid depends on ``H`` and the taper and on nothing else: it is
blind to the radius, the density and the stiffness. The frequency
depends on ``H`` and on the *ratio* ``E/rho``: it is blind to the taper,
to the radius, and to any rescaling of ``E`` and ``rho`` that leaves
their ratio alone. So the base radius moves neither constraint at all --
its Jacobian column is identically zero -- and the two constraints
together fix a two-dimensional slice of a five-dimensional family. What
is left is a **three-parameter continuum of solutions**, every member of
which meets both constraints exactly.

:func:`solve_inverse` therefore runs a genuine multi-start search and
returns what the search finds: a **SOLUTION FAMILY**, not a solution.
:func:`solution_family` returns many demonstrably different parameter
sets that all satisfy both constraints to tolerance;
:func:`identifiability` computes the constraint Jacobian and reports its
rank deficiency, in the same terms a nonlinear inverse problem is judged
by; and :func:`refuse_unique_geometry` raises rather than hand back one
member of the continuum as "the" body.

That the solver works is checked separately, and it must be: a solver
that found nothing would produce the same headline for the wrong reason.
A parameter set is planted, its centroid and frequency are computed from
it, and the search is asked to recover a body meeting those constraints.
It does -- immediately and repeatedly, at many different points. The
recovery is the POWER control; the multiplicity is the result.

Nothing here is measured. No object was weighed, balanced, struck or
listened to. The centroid is an integral over a declared shape, the
frequency is a textbook one-line mode estimate, and no physical
validation is claimed. The standing verdict is
``CENTROID_INVERSE_UNDERDETERMINED``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from decimal import Decimal, localcontext
from enum import Enum

import numpy as np


class GeomInverseError(ValueError):
    """Raised when the inverse is asked for more than it contains.

    Covers an exactness claim for the ``51.843`` degree slope, a malformed
    parameter set, an unreachable constraint pair, and any request for a
    unique geometry from a centroid plus one frequency.
    """


class ScientificType(Enum):
    """The evidence classes this module is allowed to emit."""

    ESTABLISHED_SOURCE = "ESTABLISHED_SOURCE"
    DERIVED_ARITHMETIC = "DERIVED_ARITHMETIC"
    ANALYTIC_MODEL = "ANALYTIC_MODEL"
    NUMERICAL_SIMULATION = "NUMERICAL_SIMULATION"
    SOURCE_CLAIM = "SOURCE_CLAIM"
    CANDIDATE_HYPOTHESIS = "CANDIDATE_HYPOTHESIS"
    UNSUPPORTED = "UNSUPPORTED"
    BLOCKED_MISSING_DATA = "BLOCKED_MISSING_DATA"


#: Part 1 -- the golden-ratio angle -- is closed-form arithmetic.
EVIDENCE_CLASS_CONSTANTS = ScientificType.DERIVED_ARITHMETIC.value
#: Part 2 -- the parametric body and its mode -- is a declared model.
EVIDENCE_CLASS_FAMILY = ScientificType.ANALYTIC_MODEL.value
#: Both, in the order they appear.
EVIDENCE_CLASS = (EVIDENCE_CLASS_CONSTANTS, EVIDENCE_CLASS_FAMILY)

PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: The standing verdict. It is never upgraded to a shape.
VERDICT = "CENTROID_INVERSE_UNDERDETERMINED"

#: The standing label for the 51.843 degree comparison.
ANGLE_VERDICT = "APPROXIMATE_NOT_EXACT"

#: The label the comparison would carry if the two numbers were equal.
ANGLE_VERDICT_IF_EQUAL = "EXACT"


# =======================================================================
# Part 1 -- phi, atan(sqrt(phi)), and a gap that must not be rounded away
# =======================================================================

#: Working precision for the exact constants, in decimal digits. Far more
#: than a float carries, so the float values below are conclusions of the
#: high-precision computation rather than the source of it.
DECIMAL_PRECISION = 60

#: The closed form. Carried as text so the constant is a *definition*
#: that gets evaluated, never a literal that gets trusted.
PHI_CLOSED_FORM = "(1 + sqrt(5)) / 2"
SQRT_PHI_CLOSED_FORM = "sqrt((1 + sqrt(5)) / 2)"
ATAN_SQRT_PHI_CLOSED_FORM = "atan(sqrt((1 + sqrt(5)) / 2)) in degrees"

#: The supplied slope, as supplied. Compared, never rounded to.
SUPPLIED_ANGLE_DEG = 51.843


def _dec_pi(precision: int = DECIMAL_PRECISION) -> Decimal:
    """pi to ``precision`` digits, by the standard series. No literals."""
    with localcontext() as ctx:
        ctx.prec = precision + 10
        lasts, t, s, n, na, d, da = 0, Decimal(3), 3, 1, 0, 0, 24
        while s != lasts:
            lasts = s
            n, na = n + na, na + 8
            d, da = d + da, da + 32
            t = (t * n) / d
            s += t
    with localcontext() as ctx:
        ctx.prec = precision
        return +s


def _dec_atan(x: Decimal, precision: int = DECIMAL_PRECISION) -> Decimal:
    """arctan of a Decimal, in radians, to ``precision`` digits.

    The Taylor series for arctan is useless at ``x ~ 1.27``, so the
    argument is halved repeatedly with
    ``atan(x) = 2 atan(x / (1 + sqrt(1 + x^2)))`` until it is small
    enough for the series to converge quickly, and the result is scaled
    back by the same power of two.
    """
    with localcontext() as ctx:
        ctx.prec = precision + 15
        v = Decimal(x)
        halvings = 0
        limit = Decimal(1).scaleb(-2)          # 0.01
        while abs(v) > limit:
            v = v / (Decimal(1) + (Decimal(1) + v * v).sqrt())
            halvings += 1
            if halvings > 200:                 # pragma: no cover - guard
                raise GeomInverseError("arctan argument reduction diverged")
        v2 = v * v
        term = v
        total = v
        k = 1
        floor = Decimal(1).scaleb(-(precision + 10))
        while True:
            term = -term * v2
            k += 2
            step = term / k
            total += step
            if abs(step) < floor:
                break
        result = total * (2 ** halvings)
    with localcontext() as ctx:
        ctx.prec = precision
        return +result


def phi_exact(precision: int = DECIMAL_PRECISION) -> Decimal:
    """``(1 + sqrt(5)) / 2`` evaluated to ``precision`` decimal digits.

    Evaluated from the closed form every time. Nothing about phi is
    stored as a pre-rounded decimal literal, because a rounded literal
    presented as an exact constant is the precise error this module
    exists to refuse.
    """
    if int(precision) < 2:
        raise GeomInverseError("precision must be at least 2 digits")
    with localcontext() as ctx:
        ctx.prec = int(precision) + 10
        value = (Decimal(1) + Decimal(5).sqrt()) / Decimal(2)
    with localcontext() as ctx:
        ctx.prec = int(precision)
        return +value


def sqrt_phi_exact(precision: int = DECIMAL_PRECISION) -> Decimal:
    """``sqrt(phi)`` to ``precision`` decimal digits."""
    with localcontext() as ctx:
        ctx.prec = int(precision) + 10
        value = phi_exact(int(precision) + 10).sqrt()
    with localcontext() as ctx:
        ctx.prec = int(precision)
        return +value


def atan_sqrt_phi_rad(precision: int = DECIMAL_PRECISION) -> Decimal:
    """``atan(sqrt(phi))`` in radians, to ``precision`` digits."""
    p = int(precision)
    with localcontext() as ctx:
        ctx.prec = p + 10
        value = _dec_atan(sqrt_phi_exact(p + 10), p + 10)
    with localcontext() as ctx:
        ctx.prec = p
        return +value


def atan_sqrt_phi_deg(precision: int = DECIMAL_PRECISION) -> Decimal:
    """``atan(sqrt(phi))`` in DEGREES, to ``precision`` digits.

    To seventeen significant figures this is ``51.827292372987756``
    degrees, which is a computed value and not an assumed one.
    """
    p = int(precision)
    with localcontext() as ctx:
        ctx.prec = p + 10
        value = atan_sqrt_phi_rad(p + 10) * Decimal(180) / _dec_pi(p + 10)
    with localcontext() as ctx:
        ctx.prec = p
        return +value


#: Float shadows of the constants, for arithmetic that has to be done in
#: floats. ``PHI`` and ``SQRT_PHI`` are the high-precision values
#: narrowed at the last moment, never hand-typed decimals; they agree
#: bit for bit with the ordinary double-precision route.
PHI = float(phi_exact())
SQRT_PHI = float(sqrt_phi_exact())

#: The angle in degrees by the ordinary double-precision route, which is
#: what any reader reproduces: ``degrees(atan(sqrt(phi)))``.
ATAN_SQRT_PHI_DEG = math.degrees(math.atan(SQRT_PHI))

#: The same angle at :data:`DECIMAL_PRECISION` digits.
ATAN_SQRT_PHI_DEG_EXACT = atan_sqrt_phi_deg()

#: The two disagree in the last unit in the last place -- the float chain
#: carries three roundings (sqrt, atan, the degree conversion) and the
#: decimal chain carries none that matter. The gap is a few parts in 1e-15
#: degrees, which is a hundred million times smaller than the gap to
#: 51.843 and a thousand times smaller than the last digit either value
#: is quoted to. It is recorded rather than hidden because a float that
#: is one ulp away from the true value is exactly the reason a constant
#: like this is carried as a closed form and not as a literal.
ATAN_SQRT_PHI_FLOAT_VS_EXACT_DEG = float(
    Decimal(repr(ATAN_SQRT_PHI_DEG)) - ATAN_SQRT_PHI_DEG_EXACT)


def compare_to(supplied_deg: float = SUPPLIED_ANGLE_DEG,
               precision: int = DECIMAL_PRECISION) -> dict:
    """Compare a supplied slope against ``atan(sqrt(phi))``. No rounding.

    Returns the signed difference in degrees, the same difference in
    arcseconds, the relative difference, and a verdict. The verdict is
    ``EXACT`` only if the two numbers are equal at the working precision;
    for ``51.843`` degrees they differ in the fourth significant figure --
    they share only ``51.8`` -- and the verdict is
    ``APPROXIMATE_NOT_EXACT``.

    The difference is reported both as a float -- so it can be checked
    against the value a reader gets from ordinary double arithmetic --
    and as a high-precision decimal, so that neither representation can
    be blamed for the gap.
    """
    if isinstance(supplied_deg, bool) or not isinstance(
            supplied_deg, (int, float, Decimal, str)):
        raise GeomInverseError("supplied angle must be a real number")
    p = int(precision)
    exact_deg = atan_sqrt_phi_deg(p)
    supplied_float = float(supplied_deg)
    with localcontext() as ctx:
        ctx.prec = p + 10
        supplied_dec = Decimal(str(supplied_deg))
        diff_dec = supplied_dec - exact_deg
        rel_dec = diff_dec / exact_deg
        equal = diff_dec == 0
    # The float difference, computed the ordinary way, for reproducibility.
    diff_float = supplied_float - ATAN_SQRT_PHI_DEG
    return {
        "supplied_deg": supplied_float,
        "exact_closed_form": ATAN_SQRT_PHI_CLOSED_FORM,
        "exact_deg": ATAN_SQRT_PHI_DEG,
        "exact_deg_high_precision": str(+exact_deg),
        "difference_deg": diff_float,
        "difference_deg_high_precision": str(+diff_dec),
        "difference_arcsec": diff_float * 3600.0,
        "relative_difference": float(rel_dec),
        "equal": bool(equal),
        "float_vs_high_precision_deg": ATAN_SQRT_PHI_FLOAT_VS_EXACT_DEG,
        "agree_to_significant_figures": 3,
        "agree_to_decimal_places": 1,
        "verdict": ANGLE_VERDICT_IF_EQUAL if equal else ANGLE_VERDICT,
        "note": (
            "the two numbers agree to three significant figures -- one "
            "decimal place, 51.8 -- and part company in the fourth. "
            "Rounding to that precision makes the gap vanish from the "
            "page; it does not make it vanish from the numbers"),
    }


#: The headline comparison, computed once at import.
SUPPLIED_ANGLE_COMPARISON = compare_to(SUPPLIED_ANGLE_DEG)


def refuse_exact_angle_claim(supplied_deg: float = SUPPLIED_ANGLE_DEG,
                             claimed_exact: bool = True) -> None:
    """Refuse the claim that ``51.843`` degrees *is* ``atan(sqrt(phi))``.

    It is not. The two differ by about ``0.0157`` degrees -- about 56.5
    arcseconds -- and that difference is a fact about the numbers, not an
    artefact of how they were printed. The two share only ``51.8``:
    rounding both to one decimal place and observing that they now match
    is not a check, it is the removal of the only evidence there was.

    The resemblance is the well-known Great Pyramid slope coincidence:
    the quoted face angle of that structure sits near ``atan(sqrt(phi))``,
    and the nearness is regularly reported as though the angle had been
    derived from the golden ratio. Treated as arithmetic it is a
    coincidence in the fourth significant figure, and arithmetic is the
    only thing this module has. Treated as a derivation it would need an
    independent reason why that constant, in that unit, should have been
    the design target, plus a stated tolerance fixed before the
    comparison rather than after it. Neither is offered here, because
    neither is known here.
    """
    cmp = compare_to(supplied_deg)
    raise GeomInverseError(
        f"refused: {cmp['supplied_deg']} degrees is NOT "
        f"atan(sqrt(phi)) = {cmp['exact_deg_high_precision']} degrees. "
        f"The difference is {cmp['difference_deg']!r} degrees "
        f"({cmp['difference_arcsec']:.2f} arcseconds), a relative "
        f"difference of {cmp['relative_difference']:.3e}. That gap is "
        f"real and must not be rounded away: it survives at every "
        f"precision and disappears only when the two values are rounded "
        f"to the one decimal place they share. This is a numeric "
        f"coincidence in the fourth "
        f"significant figure, not a derivation of one number from the "
        f"other, and it is registered as {ANGLE_VERDICT}. "
        f"claimed_exact={bool(claimed_exact)} is refused either way: the "
        f"honest report is the difference, not the resemblance.")


# =======================================================================
# Part 2 -- the parametric family
# =======================================================================

#: Field order of the parameter vector. Fixed: the Jacobian columns and
#: every reported sensitivity are indexed by it.
PARAM_NAMES = (
    "height_mm",
    "base_radius_mm",
    "taper",
    "density_kg_m3",
    "youngs_modulus_pa",
)

N_PARAMS = len(PARAM_NAMES)

#: The two scalar constraints. Two. That is the whole problem.
CONSTRAINT_NAMES = ("centroid_z_mm", "fundamental_frequency_hz")
N_CONSTRAINTS = len(CONSTRAINT_NAMES)

#: A taper of 1 would pinch the top to a point and beyond it the radius
#: would go negative, so the family stops short of it.
TAPER_MAX = 0.95

#: The declared target: a centroid at (0, 0, 100 mm) on the axis.
DEFAULT_TARGET_CENTROID_MM = 100.0
#: A declared target frequency. Neutral: it fixes a number so the search
#: has something to solve, and it stands for nothing.
DEFAULT_TARGET_FREQ_HZ = 12500.0

#: Relative residual at which a parameter set counts as meeting both
#: constraints.
DEFAULT_TOLERANCE = 1.0e-9
#: Relative singular-value floor for the numerical rank of the Jacobian.
DEFAULT_RCOND = 1.0e-10
#: Two solutions are DIFFERENT when some parameter differs by more than
#: this in relative terms. Deliberately wide: near-copies must not be
#: counted as a family.
DEFAULT_DISTINCT_TOL = 0.05

DEFAULT_SEED = 20260723


@dataclass(frozen=True)
class BodyParams:
    """One member of the axisymmetric family.

    The solid is generated by revolving ``r(z) = r0 (1 - t z / H)`` about
    the z axis for ``0 <= z <= H``: a right circular cylinder when the
    taper is zero, a frustum otherwise. Density and stiffness are carried
    as parameters because the frequency constraint needs them, not
    because any material is being claimed.
    """

    height_mm: float
    base_radius_mm: float
    taper: float
    density_kg_m3: float
    youngs_modulus_pa: float

    def __post_init__(self) -> None:
        for name in PARAM_NAMES:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise GeomInverseError(f"{name} must be a real number")
            if not math.isfinite(float(value)):
                raise GeomInverseError(f"{name} must be finite")
        for name in ("height_mm", "base_radius_mm", "density_kg_m3",
                     "youngs_modulus_pa"):
            if float(getattr(self, name)) <= 0.0:
                raise GeomInverseError(f"{name} must be positive")
        if not 0.0 <= float(self.taper) <= TAPER_MAX:
            raise GeomInverseError(
                f"taper must lie in [0, {TAPER_MAX}]; beyond it the "
                f"radius would reach zero or go negative")

    def as_vector(self) -> np.ndarray:
        return np.array([float(getattr(self, n)) for n in PARAM_NAMES],
                        dtype=float)

    def as_dict(self) -> dict:
        return {n: float(getattr(self, n)) for n in PARAM_NAMES}


def params_from_vector(vector) -> BodyParams:
    """Build a :class:`BodyParams` from a length-5 vector."""
    v = np.asarray(vector, dtype=float)
    if v.shape != (N_PARAMS,):
        raise GeomInverseError(
            f"parameter vector must have {N_PARAMS} entries "
            f"({', '.join(PARAM_NAMES)})")
    return BodyParams(*(float(x) for x in v))


# --- the two forward maps ----------------------------------------------

def _taper_moment_ratio(taper: float) -> tuple:
    """``(numerator, denominator)`` of the centroid's taper factor.

    With ``u = z/H`` the volume integral is
    ``A(t) = int_0^1 (1 - t u)^2 du = 1 - t + t^2/3`` and the first
    moment is ``B(t) = int_0^1 u (1 - t u)^2 du = 1/2 - 2t/3 + t^2/4``.
    Both quadratics have negative discriminant, so both are positive for
    every real taper and the ratio never blows up.
    """
    t = float(taper)
    a = 1.0 - t + t * t / 3.0
    b = 0.5 - 2.0 * t / 3.0 + t * t / 4.0
    if a <= 0.0:                                # pragma: no cover - guard
        raise GeomInverseError("degenerate taper: zero volume integral")
    return b, a


def centroid_z(params: BodyParams) -> float:
    """Axial centroid of the solid, in millimetres. Closed form.

    ``centroid_z = H * B(t) / A(t)``. Note what is *absent*: the base
    radius scales ``r(z)`` uniformly and so cancels out of the ratio, and
    the density is uniform and so cancels too. The centroid sees the
    height and the taper and nothing else -- one equation in two
    unknowns before the frequency is even mentioned.
    """
    if not isinstance(params, BodyParams):
        raise GeomInverseError("expected a BodyParams")
    b, a = _taper_moment_ratio(params.taper)
    return float(params.height_mm) * b / a


def volume_mm3(params: BodyParams) -> float:
    """Volume of the solid in cubic millimetres. Reported, not constrained."""
    if not isinstance(params, BodyParams):
        raise GeomInverseError("expected a BodyParams")
    _b, a = _taper_moment_ratio(params.taper)
    r0 = float(params.base_radius_mm)
    return math.pi * r0 * r0 * float(params.height_mm) * a


def fundamental_frequency(params: BodyParams) -> float:
    """Fundamental longitudinal bar mode, in hertz. ANALYTIC_MODEL.

    ``f = sqrt(E / rho) / (2 L)`` with ``L`` the height in metres: the
    textbook free-free longitudinal fundamental of a slender uniform bar.
    It is used here because it is standard, one line long, and plainly a
    model rather than a measurement -- it ignores the taper, the radius,
    Poisson coupling, boundary conditions and every real effect. Swapping
    it for a better estimator would change the numbers and not one
    conclusion, because the conclusion comes from counting equations.

    Note what is absent again: the taper and the radius do not appear,
    and ``E`` and ``rho`` enter only through their ratio. Doubling both
    leaves the frequency untouched.
    """
    if not isinstance(params, BodyParams):
        raise GeomInverseError("expected a BodyParams")
    length_m = float(params.height_mm) / 1000.0
    if length_m <= 0.0:                         # pragma: no cover - guard
        raise GeomInverseError("height must be positive")
    speed = math.sqrt(float(params.youngs_modulus_pa)
                      / float(params.density_kg_m3))
    return speed / (2.0 * length_m)


def forward(params: BodyParams) -> np.ndarray:
    """The two constrained quantities, in the fixed constraint order."""
    return np.array([centroid_z(params), fundamental_frequency(params)],
                    dtype=float)


def wave_speed_m_s(params: BodyParams) -> float:
    """``sqrt(E/rho)``. The only combination of E and rho the mode sees."""
    return math.sqrt(float(params.youngs_modulus_pa)
                     / float(params.density_kg_m3))


# --- the search space, transformed so bounds cannot be violated --------

_LOGIT_CLAMP = 8.0


def _to_free(params: BodyParams) -> np.ndarray:
    """Parameters -> unconstrained coordinates for the search.

    Positive quantities are searched in logs and the taper through a
    logistic, so no step can produce a negative height or a taper past
    the pinch point. The search never has to reject a proposal.
    """
    t = min(max(float(params.taper), 1e-9), TAPER_MAX * (1.0 - 1e-9))
    frac = t / TAPER_MAX
    return np.array([
        math.log(float(params.height_mm)),
        math.log(float(params.base_radius_mm)),
        math.log(frac / (1.0 - frac)),
        math.log(float(params.density_kg_m3)),
        math.log(float(params.youngs_modulus_pa)),
    ], dtype=float)


def _from_free(q) -> BodyParams:
    """Unconstrained coordinates -> parameters."""
    v = np.asarray(q, dtype=float)
    if v.shape != (N_PARAMS,):
        raise GeomInverseError(f"free vector must have {N_PARAMS} entries")
    z = float(np.clip(v[2], -_LOGIT_CLAMP, _LOGIT_CLAMP))
    taper = TAPER_MAX / (1.0 + math.exp(-z))
    return BodyParams(
        height_mm=math.exp(float(np.clip(v[0], -50.0, 50.0))),
        base_radius_mm=math.exp(float(np.clip(v[1], -50.0, 50.0))),
        taper=taper,
        density_kg_m3=math.exp(float(np.clip(v[3], -50.0, 90.0))),
        youngs_modulus_pa=math.exp(float(np.clip(v[4], -50.0, 90.0))),
    )


def relative_residuals(params: BodyParams,
                       target_centroid_mm: float = DEFAULT_TARGET_CENTROID_MM,
                       target_freq_hz: float = DEFAULT_TARGET_FREQ_HZ
                       ) -> np.ndarray:
    """Signed relative miss on each constraint, in constraint order."""
    if float(target_centroid_mm) <= 0.0 or float(target_freq_hz) <= 0.0:
        raise GeomInverseError("both targets must be positive")
    got = forward(params)
    want = np.array([float(target_centroid_mm), float(target_freq_hz)],
                    dtype=float)
    return (got - want) / want


def meets_constraints(params: BodyParams,
                      target_centroid_mm: float = DEFAULT_TARGET_CENTROID_MM,
                      target_freq_hz: float = DEFAULT_TARGET_FREQ_HZ,
                      tolerance: float = DEFAULT_TOLERANCE) -> bool:
    """True when both relative residuals are within ``tolerance``."""
    r = relative_residuals(params, target_centroid_mm, target_freq_hz)
    return bool(np.max(np.abs(r)) <= float(tolerance))


# --- the Jacobian and identifiability ----------------------------------

def constraint_jacobian(params: BodyParams, eps: float = 1e-6) -> np.ndarray:
    """``J[i, k] = d(constraint_i) / d(param_k)``, relative-scaled.

    A 2 x 5 matrix: two constraints, five parameters. Both the
    constraints and the parameters are scaled by their own magnitudes, so
    the singular values compare like with like rather than comparing
    millimetres against pascals. Central differences, as in any
    nonlinear-inverse identifiability check, so the same routine works
    for any forward map the family is later given.
    """
    if not isinstance(params, BodyParams):
        raise GeomInverseError("expected a BodyParams")
    p = params.as_vector()
    base = forward(params)
    if np.any(base == 0.0):                     # pragma: no cover - guard
        raise GeomInverseError("a constraint value of zero has no scale")
    j = np.zeros((N_CONSTRAINTS, N_PARAMS), dtype=float)
    for k, name in enumerate(PARAM_NAMES):
        scale = abs(float(p[k])) if p[k] != 0.0 else 1.0
        h = float(eps) * scale
        if name == "taper":
            h = min(h if h > 0 else float(eps), 1e-4)
            hi = min(float(p[k]) + h, TAPER_MAX)
            lo = max(float(p[k]) - h, 0.0)
        else:
            hi = float(p[k]) + h
            lo = max(float(p[k]) - h, 1e-300)
        if hi == lo:                            # pragma: no cover - guard
            continue
        pp = p.copy()
        pm = p.copy()
        pp[k] = hi
        pm[k] = lo
        up = forward(params_from_vector(pp))
        dn = forward(params_from_vector(pm))
        j[:, k] = (up - dn) / (hi - lo) * scale / base
    return j


def identifiability(params: BodyParams | None = None,
                    rcond: float = DEFAULT_RCOND) -> dict:
    """Can the five parameters be recovered from the two constraints?

    No. The question is settled by counting before any matrix is formed:
    a 2 x 5 Jacobian has rank at most 2, so at least three directions in
    parameter space leave both constraints unchanged. The singular value
    decomposition is computed anyway, because it says *which* directions
    are free and shows that the deficiency is structural rather than a
    matter of ill conditioning: the base-radius column is identically
    zero, not merely small.

    The reasoning is the standard one for a nonlinear inverse problem --
    form the sensitivity matrix at the point, look at its rank, and
    refuse a point estimate when it is deficient. Here the deficiency
    does not depend on where the point is.
    """
    p = DEFAULT_PLANTED_PARAMS if params is None else params
    j = constraint_jacobian(p)
    sv = np.linalg.svd(j, compute_uv=False)
    smax = float(sv[0]) if sv.size else 0.0
    tol = float(rcond) * smax
    rank = int((sv > tol).sum())
    smin = float(sv[-1]) if sv.size else 0.0
    cond = (smax / smin) if smin > 0.0 else math.inf
    column_norms = np.linalg.norm(j, axis=0)
    zero_cols = tuple(PARAM_NAMES[k] for k in range(N_PARAMS)
                      if float(column_norms[k]) <= tol)
    return {
        "n_params": N_PARAMS,
        "n_constraints": N_CONSTRAINTS,
        "param_names": list(PARAM_NAMES),
        "constraint_names": list(CONSTRAINT_NAMES),
        "jacobian_shape": list(j.shape),
        "rank": rank,
        "rank_deficiency": N_PARAMS - rank,
        "null_space_dimension": N_PARAMS - rank,
        "singular_values": [float(s) for s in sv],
        "condition_number": cond,
        "column_norms": {PARAM_NAMES[k]: float(column_norms[k])
                         for k in range(N_PARAMS)},
        "zero_sensitivity_params": list(zero_cols),
        "identifiable": bool(rank >= N_PARAMS),
        "verdict": "NON_IDENTIFIABLE" if rank < N_PARAMS else "IDENTIFIABLE",
        "why": (
            "two scalar constraints cannot determine five parameters. The "
            "Jacobian is 2 x 5, so its rank is at most 2 and at least "
            "three parameter directions move nothing. The deficiency is "
            "structural: the base radius cancels out of the centroid and "
            "does not enter the mode estimate at all, the taper does not "
            "enter the frequency, and E and rho appear only through "
            "their ratio"),
        "what_this_does_not_say": (
            "that a better forward model would fix it. A richer model "
            "would add parameters, not constraints, and the deficiency "
            "would widen. What closes a rank gap is more independent "
            "measurements, not a more elaborate body"),
    }


# --- the search --------------------------------------------------------

def _free_jacobian(q: np.ndarray, want: np.ndarray,
                   eps: float = 1e-7) -> np.ndarray:
    """Central-difference Jacobian of the residual in search coordinates."""
    n = q.size
    j = np.empty((N_CONSTRAINTS, n), dtype=float)
    for k in range(n):
        h = eps * max(1.0, abs(float(q[k])))
        qp = q.copy()
        qm = q.copy()
        qp[k] += h
        qm[k] -= h
        rp = (forward(_from_free(qp)) - want) / want
        rm = (forward(_from_free(qm)) - want) / want
        j[:, k] = (rp - rm) / (2.0 * h)
    return j


def _solve_from(start: BodyParams, want: np.ndarray,
                tolerance: float = DEFAULT_TOLERANCE,
                max_iter: int = 200) -> tuple:
    """Gauss-Newton from one start. Returns ``(params, residual, ok)``.

    The step is the minimum-norm solution ``dq = -pinv(J) r``. That is
    the right step for an underdetermined system and it is also the tell:
    a pseudo-inverse is needed precisely because ``J`` has a null space,
    and the step it returns is the one that moves *least* while meeting
    the constraints. Which member of the solution set a run lands on is
    therefore decided by where it started, not by the data.
    """
    q = _to_free(start)
    r = (forward(_from_free(q)) - want) / want
    norm = float(np.max(np.abs(r)))
    for _ in range(int(max_iter)):
        if norm <= float(tolerance):
            return _from_free(q), norm, True
        j = _free_jacobian(q, want)
        try:
            dq = -np.linalg.pinv(j, rcond=1e-12) @ r
        except np.linalg.LinAlgError:           # pragma: no cover - guard
            break
        if not np.all(np.isfinite(dq)):         # pragma: no cover - guard
            break
        step = 1.0
        improved = False
        for _ in range(40):
            qn = q + step * dq
            try:
                rn = (forward(_from_free(qn)) - want) / want
            except GeomInverseError:            # pragma: no cover - guard
                step *= 0.5
                continue
            nn = float(np.max(np.abs(rn)))
            if np.isfinite(nn) and nn < norm:
                q, r, norm = qn, rn, nn
                improved = True
                break
            step *= 0.5
        if not improved:
            break
    return _from_free(q), norm, bool(norm <= float(tolerance))


def _random_start(rng: np.random.Generator) -> BodyParams:
    """A start drawn log-uniformly across the declared search box."""
    return BodyParams(
        height_mm=float(math.exp(rng.uniform(math.log(120.0),
                                             math.log(420.0)))),
        base_radius_mm=float(math.exp(rng.uniform(math.log(4.0),
                                                  math.log(80.0)))),
        taper=float(rng.uniform(0.02, 0.90)),
        density_kg_m3=float(math.exp(rng.uniform(math.log(800.0),
                                                 math.log(9000.0)))),
        youngs_modulus_pa=float(math.exp(rng.uniform(math.log(1.0e9),
                                                     math.log(4.0e11)))),
    )


def _is_distinct(candidate: BodyParams, kept: list,
                 distinct_tol: float) -> bool:
    cv = candidate.as_vector()
    for other in kept:
        ov = other.as_vector()
        rel = np.max(np.abs(cv - ov) / np.maximum(np.abs(ov), 1e-300))
        if float(rel) <= float(distinct_tol):
            return False
    return True


def solve_inverse(target_centroid_mm: float = DEFAULT_TARGET_CENTROID_MM,
                  target_freq_hz: float = DEFAULT_TARGET_FREQ_HZ,
                  restarts: int = 24,
                  seed: int = DEFAULT_SEED,
                  tolerance: float = DEFAULT_TOLERANCE,
                  distinct_tol: float = DEFAULT_DISTINCT_TOL) -> dict:
    """Search the family for bodies whose centroid and mode hit the targets.

    This is a real search: ``restarts`` independent starts are drawn from
    the declared box and each is refined by minimum-norm Gauss-Newton
    until both relative residuals are inside ``tolerance``. It works --
    that is the POWER half, and :func:`power_check` plants a body and
    confirms the search recovers one meeting its constraints.

    What comes back is a **family**. Every restart that converges lands
    on a different body, all of them satisfying both constraints to the
    same tolerance, because the constraint set is a three-dimensional
    surface in a five-dimensional space and there is nothing in the
    problem to prefer one point of it over another. The dictionary
    reports ``unique_solution: False`` and the verdict
    ``CENTROID_INVERSE_UNDERDETERMINED``. Callers wanting one answer are
    directed to :func:`refuse_unique_geometry`, which will not give them
    one.
    """
    c = float(target_centroid_mm)
    f = float(target_freq_hz)
    if c <= 0.0 or f <= 0.0:
        raise GeomInverseError("both targets must be positive")
    if int(restarts) < 1:
        raise GeomInverseError("restarts must be at least 1")
    want = np.array([c, f], dtype=float)
    rng = np.random.default_rng(int(seed))

    solutions: list = []
    residuals: list = []
    converged = 0
    for _ in range(int(restarts)):
        start = _random_start(rng)
        params, resid, ok = _solve_from(start, want, tolerance)
        if not ok:
            continue
        converged += 1
        if _is_distinct(params, solutions, distinct_tol):
            solutions.append(params)
            residuals.append(resid)

    if not solutions:
        raise GeomInverseError(
            f"no member of the declared family reaches centroid {c} mm "
            f"and {f} Hz within {tolerance}; the constraint pair is "
            f"outside the search box, which is a statement about the box "
            f"and not a uniqueness result")

    return {
        "target_centroid_mm": c,
        "target_freq_hz": f,
        "target_centroid_point_mm": (0.0, 0.0, c),
        "restarts": int(restarts),
        "converged_runs": converged,
        "solutions": tuple(solutions),
        "solution_dicts": [s.as_dict() for s in solutions],
        "n_distinct_solutions": len(solutions),
        "max_relative_residual": float(max(residuals)),
        "tolerance": float(tolerance),
        "distinct_tol": float(distinct_tol),
        "unique_solution": False,
        "solution_set_dimension": N_PARAMS - N_CONSTRAINTS,
        "identifiability": identifiability(solutions[0]),
        "evidence_class": EVIDENCE_CLASS_FAMILY,
        "verdict": VERDICT,
        "note": (
            "every listed body satisfies both constraints to the same "
            "tolerance. The list is a sample of a three-parameter "
            "continuum, not a shortlist to choose from"),
    }


def solution_family(target_centroid_mm: float = DEFAULT_TARGET_CENTROID_MM,
                    target_freq_hz: float = DEFAULT_TARGET_FREQ_HZ,
                    count: int = 6,
                    seed: int = DEFAULT_SEED,
                    tolerance: float = DEFAULT_TOLERANCE,
                    distinct_tol: float = DEFAULT_DISTINCT_TOL) -> tuple:
    """At least ``count`` genuinely different bodies meeting both constraints.

    The members are not perturbations of one another. They differ in
    height, in taper, in radius, in density and in stiffness -- by
    factors, not by percentages -- and each satisfies the centroid and
    the frequency to the same tolerance as every other. That is what an
    underdetermined inverse looks like when it is written down instead of
    being collapsed to its first row.
    """
    if int(count) < 1:
        raise GeomInverseError("count must be at least 1")
    restarts = max(8, int(count) * 6)
    for _ in range(6):
        result = solve_inverse(target_centroid_mm, target_freq_hz,
                               restarts=restarts, seed=seed,
                               tolerance=tolerance,
                               distinct_tol=distinct_tol)
        members = result["solutions"]
        if len(members) >= int(count):
            return tuple(members[:int(count)])
        restarts *= 2
        seed = int(seed) + 1
    return tuple(members)


def family_spread(members: tuple) -> dict:
    """How far apart the members of a family are, parameter by parameter."""
    rows = tuple(members)
    if len(rows) < 2:
        raise GeomInverseError("a spread needs at least two members")
    v = np.array([m.as_vector() for m in rows], dtype=float)
    lo = v.min(axis=0)
    hi = v.max(axis=0)
    return {
        "n_members": len(rows),
        "min": {PARAM_NAMES[k]: float(lo[k]) for k in range(N_PARAMS)},
        "max": {PARAM_NAMES[k]: float(hi[k]) for k in range(N_PARAMS)},
        "ratio_max_over_min": {
            PARAM_NAMES[k]: (float(hi[k] / lo[k]) if lo[k] > 0 else math.inf)
            for k in range(N_PARAMS)},
    }


# --- the planted control -----------------------------------------------

#: A body planted to exercise the solver. Its numbers are ordinary and
#: stand for nothing; the point of it is that its centroid and mode are
#: computed FROM it, so the search is asked a question with a known
#: answer -- and then shown to have many more.
DEFAULT_PLANTED_PARAMS = BodyParams(
    height_mm=240.0,
    base_radius_mm=18.0,
    taper=0.35,
    density_kg_m3=2700.0,
    youngs_modulus_pa=7.0e10,
)


def power_check(params: BodyParams = DEFAULT_PLANTED_PARAMS,
                restarts: int = 24,
                seed: int = DEFAULT_SEED,
                tolerance: float = DEFAULT_TOLERANCE) -> dict:
    """Plant a body, compute its constraints, and recover a body meeting them.

    The POWER control. If the search could not find a body when one
    demonstrably exists, then finding many would prove nothing -- the
    multiplicity would just be noise. It finds one on the first restart
    and then keeps finding more, all different, which is the finding.

    Note the phrasing: the search recovers *a* body meeting the planted
    body's constraints, not *the* planted body. It has no way to prefer
    the planted one, and neither does the data.
    """
    target_c = centroid_z(params)
    target_f = fundamental_frequency(params)
    result = solve_inverse(target_c, target_f, restarts=restarts, seed=seed,
                           tolerance=tolerance)
    best = result["solutions"][0]
    planted_ok = meets_constraints(params, target_c, target_f, tolerance)
    recovered_ok = meets_constraints(best, target_c, target_f, tolerance)
    pv = params.as_vector()
    bv = best.as_vector()
    rel = np.abs(bv - pv) / np.maximum(np.abs(pv), 1e-300)
    return {
        "planted_params": params.as_dict(),
        "planted_centroid_mm": target_c,
        "planted_frequency_hz": target_f,
        "planted_meets_its_own_constraints": bool(planted_ok),
        "recovered_params": best.as_dict(),
        "recovered_meets_constraints": bool(recovered_ok),
        "recovered_centroid_mm": centroid_z(best),
        "recovered_frequency_hz": fundamental_frequency(best),
        "max_relative_param_difference": float(np.max(rel)),
        "recovered_equals_planted": bool(np.max(rel) <= 1e-6),
        "n_distinct_solutions": result["n_distinct_solutions"],
        "detected": bool(recovered_ok),
        "note": (
            "the search recovers a body meeting the planted constraints, "
            "so it has the power to solve this inverse when a solution "
            "exists. It does not recover the planted body in particular, "
            "and nothing in the problem says it should"),
    }


# --- the headline refusal ----------------------------------------------

def refuse_unique_geometry(target_centroid_mm: float =
                           DEFAULT_TARGET_CENTROID_MM,
                           target_freq_hz: float = DEFAULT_TARGET_FREQ_HZ,
                           evidence: str = "") -> None:
    """Refuse to report one geometry from a centroid and one frequency.

    Always. Not "unless the residual is small", not "unless the search
    converged cleanly", not "unless the family looks physically
    plausible". The refusal is not about the quality of the fit; it is
    about the arithmetic of the question. Two scalars were supplied and
    five are needed, so any single body that gets reported was chosen by
    the starting point of the search, by the bounds of the box, or by
    whoever liked the look of it -- and none of those is the data.

    A unique geometry becomes reportable when three further independent
    constraints arrive: a second and third centroid coordinate under a
    known orientation, a mass or a volume, a second and third modal
    frequency, a measured density. Until then the deliverable is the
    SOLUTION FAMILY, and its size is the honest measure of how little the
    two constraints pinned down.
    """
    tail = f" ({evidence})" if evidence else ""
    raise GeomInverseError(
        f"refused: no unique geometry may be reported from a centroid at "
        f"(0, 0, {float(target_centroid_mm)} mm) plus a single frequency "
        f"of {float(target_freq_hz)} Hz{tail}. That is {N_CONSTRAINTS} "
        f"scalar constraints against {N_PARAMS} parameters, so the "
        f"constraint Jacobian is {N_CONSTRAINTS} x {N_PARAMS}, its rank "
        f"is at most {N_CONSTRAINTS}, and a "
        f"{N_PARAMS - N_CONSTRAINTS}-parameter continuum of bodies meets "
        f"both exactly. The base radius does not appear in either "
        f"constraint at all. Any single body returned here would be a "
        f"report of the solver's starting point, not of the constraints. "
        f"Use solution_family() and report all of it, with its size. "
        f"Verdict: {VERDICT}.")


# =======================================================================
# The report
# =======================================================================

def geominverse_report(seed: int = DEFAULT_SEED) -> dict:
    """What this module computes, and the two things it will not say."""
    angle = compare_to(SUPPLIED_ANGLE_DEG)
    power = power_check(seed=seed)
    family = solution_family(seed=seed)
    ident = identifiability(family[0])
    return {
        "what_this_is": (
            "a closed-form audit of atan(sqrt(phi)) against a supplied "
            "slope, and a constrained inverse that is shown to be "
            "underdetermined by returning the family of bodies meeting a "
            "centroid and one frequency rather than a body"),
        "exact_constants": {
            "phi_closed_form": PHI_CLOSED_FORM,
            "phi": PHI,
            "phi_high_precision": str(phi_exact()),
            "sqrt_phi_closed_form": SQRT_PHI_CLOSED_FORM,
            "sqrt_phi": SQRT_PHI,
            "sqrt_phi_high_precision": str(sqrt_phi_exact()),
            "atan_sqrt_phi_closed_form": ATAN_SQRT_PHI_CLOSED_FORM,
            "atan_sqrt_phi_deg": ATAN_SQRT_PHI_DEG,
            "atan_sqrt_phi_deg_high_precision": str(ATAN_SQRT_PHI_DEG_EXACT),
            "atan_sqrt_phi_float_vs_high_precision_deg":
                ATAN_SQRT_PHI_FLOAT_VS_EXACT_DEG,
            "decimal_precision": DECIMAL_PRECISION,
            "evidence_class": EVIDENCE_CLASS_CONSTANTS,
        },
        "angle_comparison": angle,
        "angle_verdict": angle["verdict"],
        "parametric_family": {
            "param_names": list(PARAM_NAMES),
            "n_params": N_PARAMS,
            "constraint_names": list(CONSTRAINT_NAMES),
            "n_constraints": N_CONSTRAINTS,
            "centroid_closed_form":
                "H * (1/2 - 2t/3 + t^2/4) / (1 - t + t^2/3)",
            "frequency_model": "f = sqrt(E/rho) / (2 L), free-free "
                               "longitudinal bar fundamental",
            "evidence_class": EVIDENCE_CLASS_FAMILY,
        },
        "target": {
            "centroid_mm": (0.0, 0.0, DEFAULT_TARGET_CENTROID_MM),
            "frequency_hz": DEFAULT_TARGET_FREQ_HZ,
        },
        "power_control": power,
        "solution_family": {
            "n_members": len(family),
            "members": [m.as_dict() for m in family],
            "spread": family_spread(family),
            "all_meet_constraints": all(
                meets_constraints(m) for m in family),
        },
        "identifiability": ident,
        "refusals": [
            "refuse_exact_angle_claim",
            "refuse_unique_geometry",
        ],
        "evidence_class": list(EVIDENCE_CLASS),
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not say that 51.843 degrees is atan(sqrt(phi)): the "
            "two differ by about 0.0157 degrees, about 56.5 arcseconds, "
            "and that gap is arithmetic rather than rounding. It does not "
            "say the resemblance means anything; a coincidence in the "
            "fourth significant figure is a coincidence, not a "
            "derivation. It does not say any object exists with the "
            "centroid or the frequency used here, that the bar-mode "
            "formula describes any real body, or that any of the "
            "parameter sets returned is the right one -- there is no "
            "right one, which is the result. Nothing was weighed, "
            "balanced, struck or listened to; the centroid is an integral "
            "over a declared shape and the frequency is a one-line "
            "analytic estimate. Two scalar constraints against five "
            "parameters leave a three-parameter continuum, so the "
            "deliverable is the SOLUTION FAMILY and its size. This is "
            "underdetermination, not impossibility: three further "
            "independent constraints would close it."),
        "verdict": VERDICT,
    }
