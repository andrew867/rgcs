"""R12 — an IGRF-14 magnetic-root certificate AT AN EXPLICIT EPOCH, and
the coefficient set that is not in this repository.

R11's :mod:`r11.planetroot` established that a magnetic root is
BODY-SPECIFIC and EPOCH-SPECIFIC. This module takes the second adjective
literally for one body and one model.

**The model.** IGRF-14 is the fourteenth generation International
Geomagnetic Reference Field, the IAGA working-group product released for
the 2025 epoch (2024/2025). It describes the Earth's main field by
Gauss coefficients to spherical-harmonic degree and order 13, with a
secular-variation forecast to degree 8, and it is declared valid over
1900-2030. Within that span the coefficients are not all of one kind:
the retrospective sets through 2020 are **definitive** (DGRF), the
main-field set at the 2025 epoch is **provisional** and will be revised,
and everything after 2025 is a **linear secular-variation
extrapolation** whose error grows with the distance from the last fitted
epoch. That is conventional literature; it is carried here as
``SOURCE_ESTABLISHED_PHYSICS``, not as a repository finding.

**The epoch is mandatory, and it is load-bearing.** Earth has an active
core dynamo (``INTRINSIC_DYNAMO_FIELD`` in the R11 taxonomy), so the
Earth-style root constructions are legitimate here in a way they are not
on Mars or the Moon -- but that same dynamo is why the field will not
hold still. Between two epochs a declared root moves by the secular
variation times the elapsed time, exactly:
:func:`drift_between` computes it. A root quoted with no epoch is
therefore ambiguous by that amount, which is why
:func:`refuse_root_without_epoch` raises: **a root with no epoch is not
a root.** :func:`refuse_extrapolated_as_definitive` raises for the
matching reason -- a position computed in the 2025-2030 extrapolation
window carries the forecast's growing uncertainty and may not be
relabelled definitive by leaving the label off.

**The coefficients are not bundled.** No numerical IGRF-14 Gauss
coefficient set ships in this repository. :data:`GRID_STATUS` is
``BLOCKED_MISSING_DATA``, :func:`magnetic_root` returns at best
``ROOT_CANDIDATE_REQUIRES_REAL_COEFFICIENTS``, and
:func:`refuse_root_identification` ALWAYS raises. Nothing here locates
anything on the Earth.

Nothing here is measured. No magnetometer is read, no survey is used,
no site is visited. The standing verdict is
``IGRF14_ROOT_CERTIFICATE_EPOCH_BOUND_GRID_BLOCKED``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from decimal import Decimal
from enum import Enum

import numpy as np

from r11.earthface import MagneticScalar
from r11.planetroot import (
    BODIES,
    FieldClass,
    PlanetaryRootCertificate,
    PlanetRootError,
    RootMethod,
    certify_root,
    refuse_earth_method_on_non_dynamo_body,
    refuse_timeless_root,
    resolve_body,
)


class Igrf14Error(RuntimeError):
    """Raised when an IGRF-14 root is asked to outrun its epoch or its data."""


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


#: Everything this module says about the IGRF itself is literature.
SOURCE_CLASS = "CONVENTIONAL_LITERATURE"

VERDICT = "IGRF14_ROOT_CERTIFICATE_EPOCH_BOUND_GRID_BLOCKED"
PHYSICAL_VALIDATION = "PHYSICAL_VALIDATION_NOT_CLAIMED"

#: Neutral public alias for the root this module can specify but not find.
IGRF14_ROOT_CANDIDATE_A = "IGRF14_ROOT_CANDIDATE_A"

#: What :func:`magnetic_root` returns at best. Never an identified root.
ROOT_CANDIDATE_STATUS = "ROOT_CANDIDATE_REQUIRES_REAL_COEFFICIENTS"

#: No numerical IGRF-14 Gauss coefficient set is bundled here.
GRID_STATUS = ClaimClass.BLOCKED_MISSING_DATA.value


# --- the model, from literature ----------------------------------------

MODEL_GENERATION = "IGRF-14"

#: IGRF-14 declared validity span (decimal years).
IGRF14_EPOCH_MIN = 1900.0
IGRF14_EPOCH_MAX = 2030.0

#: Retrospective sets through this epoch are DEFINITIVE (DGRF).
IGRF14_DEFINITIVE_THROUGH = 2020.0

#: The main-field set at this epoch is PROVISIONAL; it will be revised.
IGRF14_PROVISIONAL_EPOCH = 2025.0

#: Beyond the provisional epoch the field is a linear secular-variation
#: forecast, i.e. the final five-year window of the declared span.
IGRF14_EXTRAPOLATION_WINDOW = (IGRF14_PROVISIONAL_EPOCH, IGRF14_EPOCH_MAX)

#: Spherical-harmonic truncation: main field to 13, secular variation
#: to 8.
MAIN_FIELD_MAX_DEGREE = 13
SECULAR_VARIATION_MAX_DEGREE = 8

#: The body. Earth is INTRINSIC_DYNAMO_FIELD in the R11 taxonomy, which
#: is exactly why the Earth-style constructions are legitimate here.
BODY_ID = "EARTH"

PRIMARY_SOURCES: tuple[str, ...] = (
    "International Association of Geomagnetism and Aeronomy (IAGA), "
    "Division V, Working Group V-MOD: International Geomagnetic "
    "Reference Field, 14th generation (IGRF-14), released 2024/2025 for "
    "the 2025 epoch; main field to spherical-harmonic degree and order "
    "13, secular variation to degree 8, declared valid 1900-2030",
    "IGRF/DGRF convention: retrospective coefficient sets are made "
    "DEFINITIVE (DGRF) once enough data has accumulated; the newest "
    "main-field epoch is PROVISIONAL and is revised at the next "
    "generation",
    "IGRF secular-variation forecast: the final five-year window of a "
    "generation is a linear extrapolation whose error grows with "
    "elapsed time since the last fitted epoch",
    "BIPM/IUGG conventions for geodetic reference: a geomagnetic model "
    "value requires a declared reference surface, altitude and epoch "
    "before it is a value at all",
)


class CoefficientSet(Enum):
    """Which kind of IGRF-14 coefficient set an epoch draws on."""

    DEFINITIVE = "DEFINITIVE"
    PROVISIONAL = "PROVISIONAL"
    EXTRAPOLATED = "EXTRAPOLATED"


class EpochValidity(Enum):
    """The four answers :func:`epoch_validity` may give."""

    DEFINITIVE = "DEFINITIVE"
    PROVISIONAL = "PROVISIONAL"
    EXTRAPOLATED = "EXTRAPOLATED"
    OUT_OF_RANGE = "OUT_OF_RANGE"


def _as_year(year: float | int | str | Decimal) -> float:
    """Read a decimal year, or refuse."""
    try:
        y = float(year)
    except (TypeError, ValueError) as exc:
        raise Igrf14Error(
            f"epoch {year!r} is not a decimal year; a geomagnetic model "
            f"with no readable epoch has no value") from exc
    if not math.isfinite(y):
        raise Igrf14Error("an epoch must be a finite decimal year")
    return y


def epoch_validity(year: float | int | str | Decimal) -> EpochValidity:
    """Classify a decimal year against the IGRF-14 1900-2030 span.

    ``1900 <= y <= 2020`` is DEFINITIVE (the DGRF retrospective sets);
    ``2020 < y <= 2025`` is PROVISIONAL (the newest fitted main field,
    which the next generation will revise); ``2025 < y <= 2030`` is
    EXTRAPOLATED (the secular-variation forecast window); anything else
    is OUT_OF_RANGE. Outside the span IGRF-14 is not merely uncertain,
    it is undefined.
    """
    y = _as_year(year)
    if y < IGRF14_EPOCH_MIN or y > IGRF14_EPOCH_MAX:
        return EpochValidity.OUT_OF_RANGE
    if y <= IGRF14_DEFINITIVE_THROUGH:
        return EpochValidity.DEFINITIVE
    if y <= IGRF14_PROVISIONAL_EPOCH:
        return EpochValidity.PROVISIONAL
    return EpochValidity.EXTRAPOLATED


def coefficient_set_for(year: float | int | str | Decimal) -> CoefficientSet:
    """The coefficient set an in-range epoch draws on. Refuses out of range."""
    validity = epoch_validity(year)
    if validity is EpochValidity.OUT_OF_RANGE:
        raise Igrf14Error(
            f"epoch {_as_year(year)!r} lies outside the declared "
            f"{MODEL_GENERATION} span "
            f"[{IGRF14_EPOCH_MIN:.1f}, {IGRF14_EPOCH_MAX:.1f}]. Outside "
            f"that span the model has no coefficient set at all; "
            f"evaluating it there is extrapolation past the "
            f"extrapolation, not a value.")
    return CoefficientSet(validity.value)


def in_extrapolation_window(year: float | int | str | Decimal) -> bool:
    """True when the epoch falls in the final secular-variation window."""
    return epoch_validity(year) is EpochValidity.EXTRAPOLATED


# --- the certificate ----------------------------------------------------

#: Temporal-stability vocabulary that admits motion. Earth's main field
#: is in this set by physics, not by choice.
DRIFTING_STABILITY = "DRIFTS_SECULAR"

#: Default declared frame conventions, so that the certificate can be
#: handed to the R11 machinery without inventing anything silently.
DEFAULT_BODY_FIXED_FRAME = "EARTH_BODY_FIXED_IAU"
DEFAULT_REFERENCE_SURFACE = "WGS84_REFERENCE_ELLIPSOID"
DEFAULT_PRIME_MERIDIAN = "IERS_REFERENCE_MERIDIAN"
DEFAULT_SHAPE_MODEL = "WGS84_ELLIPSOID"
DEFAULT_ROTATION_AXIS = (0.0, 0.0, 1.0)

#: Sign-rule vocabulary. A gradient zero is a line, so the arrow along
#: it must be declared (this is the R11 earthface discipline, carried).
SIGN_RULES: tuple[str, ...] = (
    "POSITIVE_GRADIENT_DIRECTION",
    "NEGATIVE_GRADIENT_DIRECTION",
    "BOTH_SIGNS_RETAINED",
)


@dataclass(frozen=True)
class Igrf14Certificate:
    """An IGRF-14 root certificate, at an EXPLICIT epoch.

    This extends the R11 :class:`~r11.planetroot.PlanetaryRootCertificate`
    rather than replacing it: :meth:`as_planetary_certificate` hands the
    same declarations back to the R11 validator, which refuses to call
    the result timeless. Every field below is required, and
    ``epoch_decimal_year`` is required *first*: the field drifts, so an
    epochless root is not an under-documented root, it is not a root.
    """

    epoch_decimal_year: float | None
    coefficient_set: CoefficientSet
    gradient_scalar: MagneticScalar
    sign_rule: str
    handedness: str
    uncertainty_nT: float
    altitude_km: float = 0.0
    degree: int = MAIN_FIELD_MAX_DEGREE
    order: int = MAIN_FIELD_MAX_DEGREE
    model_generation: str = MODEL_GENERATION
    body_id: str = BODY_ID
    body_fixed_frame: str = DEFAULT_BODY_FIXED_FRAME
    reference_surface: str = DEFAULT_REFERENCE_SURFACE
    prime_meridian: str = DEFAULT_PRIME_MERIDIAN
    shape_model: str = DEFAULT_SHAPE_MODEL
    rotation_axis: tuple = DEFAULT_ROTATION_AXIS
    field_class: FieldClass = FieldClass.INTRINSIC_DYNAMO_FIELD
    temporal_stability: str = DRIFTING_STABILITY
    claim_class: ClaimClass = ClaimClass.SOURCE_ESTABLISHED_PHYSICS

    def __post_init__(self) -> None:
        if self.epoch_decimal_year is None:
            refuse_root_without_epoch(
                model_generation=self.model_generation,
                context="Igrf14Certificate construction")
        year = _as_year(self.epoch_decimal_year)
        validity = epoch_validity(year)
        if validity is EpochValidity.OUT_OF_RANGE:
            raise Igrf14Error(
                f"epoch {year} is outside the declared "
                f"{self.model_generation} span "
                f"[{IGRF14_EPOCH_MIN:.1f}, {IGRF14_EPOCH_MAX:.1f}]; "
                f"there is no coefficient set to certify against")
        if not isinstance(self.coefficient_set, CoefficientSet):
            raise Igrf14Error(
                "coefficient_set must be a CoefficientSet member "
                "(DEFINITIVE, PROVISIONAL or EXTRAPOLATED)")
        actual = CoefficientSet(validity.value)
        if self.coefficient_set is not actual:
            if self.coefficient_set is CoefficientSet.DEFINITIVE \
                    and validity is EpochValidity.EXTRAPOLATED:
                refuse_extrapolated_as_definitive(
                    year, declared=self.coefficient_set)
            raise Igrf14Error(
                f"epoch {year} draws on the {actual.value} coefficient "
                f"set, not the declared {self.coefficient_set.value}. "
                f"The label is part of the uncertainty budget, so it is "
                f"not the caller's to choose.")
        if not isinstance(self.gradient_scalar, MagneticScalar):
            raise Igrf14Error(
                "gradient_scalar must be an r11.earthface.MagneticScalar "
                "member; 'the magnetic gradient' is six different "
                "gradients until one scalar is named")
        if self.sign_rule not in SIGN_RULES:
            raise Igrf14Error(
                f"sign_rule must be one of {list(SIGN_RULES)}; a zero "
                f"direction is a line and both arrows lie on it")
        if self.handedness not in ("RIGHT", "LEFT"):
            raise Igrf14Error("handedness must be RIGHT or LEFT")
        if not (self.uncertainty_nT > 0):
            raise Igrf14Error(
                "uncertainty_nT must be positive; a root with zero "
                "stated uncertainty claims an exactness no field model "
                "supports")
        if not 1 <= int(self.degree) <= MAIN_FIELD_MAX_DEGREE:
            raise Igrf14Error(
                f"{self.model_generation} main-field degree must lie in "
                f"1..{MAIN_FIELD_MAX_DEGREE}")
        if not 0 <= int(self.order) <= int(self.degree):
            raise Igrf14Error("order must lie in 0..degree")
        if self.altitude_km < 0:
            raise Igrf14Error(
                "altitude_km must be non-negative; the field falls off "
                "with altitude, so an undeclared altitude is an "
                "undeclared field value")
        if not isinstance(self.field_class, FieldClass):
            raise Igrf14Error("field_class must be a FieldClass member")
        if not self.temporal_stability:
            raise Igrf14Error("temporal_stability must be declared")

    # -- reuse of the R11 certificate ----------------------------------

    def as_planetary_certificate(self) -> PlanetaryRootCertificate:
        """The same declarations, in the R11 certificate shape."""
        return PlanetaryRootCertificate(
            body_id=self.body_id,
            body_fixed_frame=self.body_fixed_frame,
            rotation_axis=tuple(self.rotation_axis),
            prime_meridian=self.prime_meridian,
            shape_model=self.shape_model,
            reference_surface_or_pressure_level=self.reference_surface,
            magnetic_model=(
                f"{self.model_generation} "
                f"(n={self.degree}, m={self.order}, "
                f"{self.coefficient_set.value})"),
            magnetic_model_epoch=f"{float(self.epoch_decimal_year):.4f}",
            field_class=self.field_class,
            altitude=float(self.altitude_km),
            scalar_or_vector_feature=self.gradient_scalar.value,
            critical_point_or_contour_rule=(
                "HORIZONTAL_GRADIENT_ZERO_OF_THE_DECLARED_SCALAR"),
            zero_direction=self.sign_rule,
            handedness=self.handedness,
            uncertainty=float(self.uncertainty_nT),
            temporal_stability=self.temporal_stability,
        )

    def at_epoch(self, year: float) -> "Igrf14Certificate":
        """The same declarations moved to another epoch, relabelled."""
        return replace(self, epoch_decimal_year=float(year),
                       coefficient_set=coefficient_set_for(year))


def default_certificate(epoch_decimal_year: float = 2020.0
                        ) -> Igrf14Certificate:
    """A fully declared certificate, for exercising the module."""
    return Igrf14Certificate(
        epoch_decimal_year=float(epoch_decimal_year),
        coefficient_set=coefficient_set_for(epoch_decimal_year),
        gradient_scalar=MagneticScalar.TOTAL_INTENSITY,
        sign_rule="BOTH_SIGNS_RETAINED",
        handedness="RIGHT",
        uncertainty_nT=150.0,
        altitude_km=0.0,
    )


def certify_epoch_bound(cert: Igrf14Certificate) -> dict:
    """Validate the certificate as EPOCH-BOUND, never as timeless.

    The R11 validator is run on the same declarations and is *expected*
    to refuse: Earth's main field has secular variation, so
    ``temporal_stability`` is a drifting value and
    :func:`~r11.planetroot.refuse_timeless_root` fires. That refusal is
    the result, and it is recorded rather than routed around.
    """
    if not isinstance(cert, Igrf14Certificate):
        raise Igrf14Error("certify_epoch_bound needs an Igrf14Certificate")
    planetary = cert.as_planetary_certificate()
    try:
        certify_root(planetary)
    except PlanetRootError as exc:
        r11_refusal = str(exc)
    else:                                            # pragma: no cover
        raise Igrf14Error(
            "the R11 validator did not refuse this root the word "
            "'timeless'. Earth's main field has secular variation, so "
            "an IGRF-14 root is epoch-bound by physics; a certificate "
            "that passes as timeless has had its temporal_stability "
            "mislabelled.")
    return {
        "model_generation": cert.model_generation,
        "body_id": cert.body_id,
        "field_class": cert.field_class.value,
        "epoch_decimal_year": float(cert.epoch_decimal_year),
        "epoch_validity": epoch_validity(cert.epoch_decimal_year).value,
        "coefficient_set": cert.coefficient_set.value,
        "degree": int(cert.degree),
        "order": int(cert.order),
        "altitude_km": float(cert.altitude_km),
        "gradient_scalar": cert.gradient_scalar.value,
        "sign_rule": cert.sign_rule,
        "handedness": cert.handedness,
        "uncertainty_nT": float(cert.uncertainty_nT),
        "timeless": False,
        "epoch_bound": True,
        "valid_only_for": (
            f"{cert.model_generation} "
            f"{cert.coefficient_set.value} at epoch "
            f"{float(cert.epoch_decimal_year):.4f}, altitude "
            f"{cert.altitude_km} km, uncertainty "
            f"{cert.uncertainty_nT} nT"),
        "r11_timeless_refusal": r11_refusal,
        "claim_class": ClaimClass.SOURCE_ESTABLISHED_PHYSICS.value,
        "grid_status": GRID_STATUS,
        "measured_here": "nothing",
    }


# --- secular variation: why the epoch is load-bearing -------------------

#: A conventional order-of-magnitude for main-field secular variation at
#: the surface, used only as a stand-in when a caller wants one. No
#: IGRF-14 secular-variation coefficient is bundled here.
NOMINAL_SV_NT_PER_YEAR = 50.0


def drift_between(epoch_a: float, epoch_b: float,
                  sv_nT_per_year: float = NOMINAL_SV_NT_PER_YEAR) -> dict:
    """How far a declared root's field value moves between two epochs.

    ``drift = sv * (epoch_b - epoch_a)``, exactly. Equal epochs give
    zero drift. A non-zero secular variation over a non-zero span gives
    a non-zero drift, and **that number is the ambiguity carried by any
    root quoted without an epoch**: the reader cannot tell which of the
    two values was meant, and the difference is not a rounding error.
    """
    a = _as_year(epoch_a)
    b = _as_year(epoch_b)
    for label, y in (("epoch_a", a), ("epoch_b", b)):
        if epoch_validity(y) is EpochValidity.OUT_OF_RANGE:
            raise Igrf14Error(
                f"{label} = {y} lies outside the {MODEL_GENERATION} span "
                f"[{IGRF14_EPOCH_MIN:.1f}, {IGRF14_EPOCH_MAX:.1f}]; the "
                f"model states no field there to drift")
    sv = float(sv_nT_per_year)
    if not math.isfinite(sv):
        raise Igrf14Error("secular variation must be a finite rate")
    delta_years = b - a
    signed = sv * delta_years
    drift = abs(signed)
    return {
        "epoch_a": a,
        "epoch_b": b,
        "delta_years": delta_years,
        "sv_nT_per_year": sv,
        "signed_drift_nT": signed,
        "drift_nT": drift,
        "epochs_equal": a == b,
        "epoch_a_validity": epoch_validity(a).value,
        "epoch_b_validity": epoch_validity(b).value,
        "root_ambiguous_without_epoch": drift > 0.0,
        "ambiguity_nT_if_epoch_omitted": drift,
        "claim_class": ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value,
        "note": (
            "arithmetic on a declared secular-variation rate. It says "
            "how much an epochless quotation could be wrong by; it does "
            "not report any field value"),
    }


def epochless_ambiguity(sv_nT_per_year: float = NOMINAL_SV_NT_PER_YEAR,
                        span_years: float = 10.0) -> dict:
    """The band a root quoted without an epoch could lie anywhere in."""
    if span_years <= 0:
        raise Igrf14Error("an ambiguity span must be positive")
    d = drift_between(2015.0, 2015.0 + float(span_years), sv_nT_per_year)
    return {
        "span_years": float(span_years),
        "sv_nT_per_year": float(sv_nT_per_year),
        "ambiguity_nT": d["drift_nT"],
        "epoch_declared": False,
        "verdict": ("EPOCHLESS_ROOT_AMBIGUOUS"
                    if d["drift_nT"] > 0 else "NO_DRIFT_UNDER_ZERO_SV"),
        "claim_class": ClaimClass.REPOSITORY_COMPUTATIONAL_RESULT.value,
    }


# --- the body check, reusing R11 ----------------------------------------

def require_dynamo_body(body: str = BODY_ID,
                        method: RootMethod = RootMethod.RADIAL_FIELD_EXTREMUM
                        ) -> dict:
    """Confirm the body actually has an internally generated field.

    Earth is ``INTRINSIC_DYNAMO_FIELD``, so the Earth-style construction
    is legitimate here -- which is precisely what R11 refused on Mars,
    the Moon and Venus. The R11 refusal is reused verbatim rather than
    reimplemented; only the exception type is translated.
    """
    try:
        model = resolve_body(body)
    except PlanetRootError as exc:
        raise Igrf14Error(str(exc)) from exc
    if model.field_class is not FieldClass.INTRINSIC_DYNAMO_FIELD:
        try:
            refuse_earth_method_on_non_dynamo_body(model, method)
        except PlanetRootError as exc:
            raise Igrf14Error(
                f"{MODEL_GENERATION} is an Earth main-field model. "
                f"{exc}") from exc
    return {
        "body_id": model.body_id,
        "field_class": model.field_class.value,
        "has_global_dynamo": model.has_global_dynamo,
        "earth_method_legitimate_here": True,
        "why": (
            "an internally generated dynamo field is what an IGRF-style "
            "spherical-harmonic main-field model describes; on a "
            "crustal-remanent or induced field the same arithmetic "
            "would name a different physical thing"),
        "claim_class": ClaimClass.SOURCE_ESTABLISHED_PHYSICS.value,
    }


# --- the root that cannot be computed -----------------------------------

def magnetic_root(cert: Igrf14Certificate,
                  coefficients: np.ndarray | None = None) -> dict:
    """A root request against IGRF-14. Returns a CANDIDATE, never a root.

    No numerical IGRF-14 Gauss coefficient set is bundled in this
    repository, so there is nothing to evaluate. Supplying an array of
    caller-provided numbers does not change the answer: those are not
    IGRF-14 coefficients merely because they were passed to this
    function, and their provenance is not something this module can
    check. The status is always
    ``ROOT_CANDIDATE_REQUIRES_REAL_COEFFICIENTS``.
    """
    record = certify_epoch_bound(cert)
    body = require_dynamo_body(cert.body_id)
    supplied = coefficients is not None
    n_supplied = int(np.asarray(coefficients).size) if supplied else 0
    return {
        "root_status": ROOT_CANDIDATE_STATUS,
        "status": ROOT_CANDIDATE_STATUS,
        "candidate_alias": IGRF14_ROOT_CANDIDATE_A,
        "identified": False,
        "latitude_deg": None,
        "longitude_deg": None,
        "grid_status": GRID_STATUS,
        "coefficients_bundled": False,
        "coefficients_supplied_by_caller": supplied,
        "n_supplied_values": n_supplied,
        "body": body,
        "certificate": record,
        "claim_class": ClaimClass.BLOCKED_MISSING_DATA.value,
        "why_blocked": (
            "no numerical IGRF-14 Gauss coefficient set ships in this "
            "repository. Without coefficients there is no field, "
            "without a field there is no gradient, and without a "
            "gradient there is no root -- only the specification of "
            "one"),
        "what_would_unblock_it": (
            "the published IGRF-14 coefficient set for the declared "
            "epoch, with its stated uncertainties, obtained from the "
            "issuing body and carried with its provenance"),
        "verdict": VERDICT,
    }


# --- load-bearing refusals ---------------------------------------------

def refuse_root_without_epoch(model_generation: str = MODEL_GENERATION,
                              context: str = "") -> None:
    """A root with no epoch is not a root. Always raises.

    The Earth's main field has secular variation of order tens of nT per
    year, and its features migrate. A position or field value quoted
    with no epoch is ambiguous by the drift across whatever span the
    reader assumes, and no amount of decimal places recovers the missing
    year.
    """
    tail = f" ({context})" if context else ""
    raise Igrf14Error(
        f"refused: a {model_generation} root was requested with no "
        f"epoch{tail}. epoch_decimal_year is MANDATORY. The main field "
        f"drifts -- secular variation of order "
        f"{NOMINAL_SV_NT_PER_YEAR:g} nT per year at the surface, dip "
        f"poles that migrate, a model that is revised every five years "
        f"-- so 'the IGRF root' names a different point in every year "
        f"it could have meant. An epochless root is not an "
        f"under-documented root; it is not a root. Declare the decimal "
        f"year, the coefficient set, the altitude and the uncertainty, "
        f"or use drift_between() to see how large the ambiguity is.")


def refuse_extrapolated_as_definitive(
        epoch_decimal_year: float,
        declared: CoefficientSet = CoefficientSet.DEFINITIVE) -> dict:
    """An extrapolated root may not be labelled definitive.

    Returns the (consistent) label record when the declaration matches
    what the epoch actually draws on; raises when a definitive label is
    claimed for an epoch in the secular-variation forecast window, or
    for the provisional epoch that the next generation will revise.
    """
    year = _as_year(epoch_decimal_year)
    validity = epoch_validity(year)
    if validity is EpochValidity.OUT_OF_RANGE:
        raise Igrf14Error(
            f"refused: epoch {year} is outside the {MODEL_GENERATION} "
            f"span, so no coefficient-set label applies to it at all")
    if not isinstance(declared, CoefficientSet):
        raise Igrf14Error(
            "declared must be a CoefficientSet member")
    actual = CoefficientSet(validity.value)
    if declared is actual:
        return {
            "epoch_decimal_year": year,
            "declared": declared.value,
            "actual": actual.value,
            "consistent": True,
            "claim_class": ClaimClass.SOURCE_ESTABLISHED_PHYSICS.value,
        }
    if declared is CoefficientSet.DEFINITIVE:
        window_lo, window_hi = IGRF14_EXTRAPOLATION_WINDOW
        raise Igrf14Error(
            f"refused: epoch {year} draws on the {actual.value} "
            f"coefficient set and may not be labelled DEFINITIVE. "
            f"Through {IGRF14_DEFINITIVE_THROUGH:.0f} the retrospective "
            f"sets are definitive; the {IGRF14_PROVISIONAL_EPOCH:.0f} "
            f"main field is PROVISIONAL and the next generation revises "
            f"it; and {window_lo:.0f}-{window_hi:.0f} is a linear "
            f"secular-variation EXTRAPOLATION whose uncertainty grows "
            f"with elapsed time since the last fitted epoch. Relabelling "
            f"a forecast as definitive does not shrink its error bar, it "
            f"hides it -- and every downstream position inherits the "
            f"understated uncertainty without warning.")
    raise Igrf14Error(
        f"refused: epoch {year} draws on the {actual.value} coefficient "
        f"set, not the declared {declared.value}. The coefficient-set "
        f"label is part of the uncertainty budget and is fixed by the "
        f"epoch, not by the caller.")


def refuse_root_identification(candidate: str = IGRF14_ROOT_CANDIDATE_A,
                               latitude_deg: float | None = None,
                               longitude_deg: float | None = None) -> None:
    """No root is identified here. ALWAYS raises.

    There is no bundled coefficient set, so there is no evaluated field,
    so there is no located extremum, contour or zero. Any coordinate
    offered as "the IGRF-14 root" would have been produced by something
    other than IGRF-14.
    """
    where = ""
    if latitude_deg is not None or longitude_deg is not None:
        where = f" at ({latitude_deg}, {longitude_deg})"
    raise Igrf14Error(
        f"refused: {candidate} may not be reported as an identified "
        f"root{where}. {GRID_STATUS}: no numerical {MODEL_GENERATION} "
        f"Gauss coefficient set ships in this repository, so no field "
        f"has been evaluated, no gradient has been taken and no "
        f"extremum has been located. The most this module can return is "
        f"{ROOT_CANDIDATE_STATUS} -- a fully declared specification of "
        f"what would have to be computed, at a stated epoch, with a "
        f"stated altitude and a stated uncertainty. A specification is "
        f"not a finding, and an epoch-bound candidate is not an "
        f"address.")


def refuse_timeless_igrf_root(cert: Igrf14Certificate) -> None:
    """Reuse of the R11 timeless refusal, for an IGRF certificate."""
    if not isinstance(cert, Igrf14Certificate):
        raise Igrf14Error("refuse_timeless_igrf_root needs an Igrf14Certificate")
    try:
        refuse_timeless_root(cert.as_planetary_certificate())
    except PlanetRootError as exc:
        raise Igrf14Error(str(exc)) from exc
    raise Igrf14Error(                               # pragma: no cover
        "the R11 refusal did not fire; an IGRF-14 root is epoch-bound "
        "by physics and must never certify as timeless")


# --- report --------------------------------------------------------------

def igrf14root_report() -> dict:
    """The standing result: epoch-bound specification, blocked grid."""
    cert = default_certificate(2020.0)
    ten_year = drift_between(2015.0, 2025.0)
    same = drift_between(2020.0, 2020.0)
    root = magnetic_root(cert)
    return {
        "what_this_is": (
            "an IGRF-14 magnetic-root certificate at an explicit epoch, "
            "extending the R11 planetary-root certificate with the "
            "model generation, the coefficient set, the "
            "spherical-harmonic truncation, the altitude, the gradient "
            "scalar, the sign rule, the handedness and the uncertainty "
            "-- plus the secular-variation arithmetic that shows why "
            "the epoch cannot be left out"),
        "model_generation": MODEL_GENERATION,
        "source_class": SOURCE_CLASS,
        "claim_class": ClaimClass.SOURCE_ESTABLISHED_PHYSICS.value,
        "validity_span": [IGRF14_EPOCH_MIN, IGRF14_EPOCH_MAX],
        "definitive_through": IGRF14_DEFINITIVE_THROUGH,
        "provisional_epoch": IGRF14_PROVISIONAL_EPOCH,
        "extrapolation_window": list(IGRF14_EXTRAPOLATION_WINDOW),
        "main_field_max_degree": MAIN_FIELD_MAX_DEGREE,
        "secular_variation_max_degree": SECULAR_VARIATION_MAX_DEGREE,
        "epoch_validity_examples": {
            "1905.0": epoch_validity(1905.0).value,
            "2020.0": epoch_validity(2020.0).value,
            "2028.0": epoch_validity(2028.0).value,
            "1850.0": epoch_validity(1850.0).value,
        },
        "body": require_dynamo_body(BODY_ID),
        "body_field_classes": {k: v.field_class.value
                               for k, v in BODIES.items()},
        "certificate": certify_epoch_bound(cert),
        "drift_over_ten_years": ten_year,
        "drift_for_equal_epochs": same,
        "epochless_ambiguity": epochless_ambiguity(),
        "grid_status": GRID_STATUS,
        "root_request": {k: root[k] for k in
                         ("root_status", "identified", "grid_status",
                          "coefficients_bundled", "why_blocked")},
        "candidate_alias": IGRF14_ROOT_CANDIDATE_A,
        "refusals_available": [
            "refuse_root_without_epoch (always raises)",
            "refuse_extrapolated_as_definitive",
            "refuse_root_identification (always raises)",
            "refuse_timeless_igrf_root (reuses r11.planetroot)",
        ],
        "primary_sources": list(PRIMARY_SOURCES),
        "measured_here": "nothing",
        "physical_validation": PHYSICAL_VALIDATION,
        "what_this_does_not_say": (
            "It does not locate the Earth's magnetic root, does not "
            "evaluate the IGRF-14 field anywhere, and does not report a "
            "field value, a declination, or a coordinate. No IGRF-14 "
            "Gauss coefficient set is bundled here, so the grid is "
            "BLOCKED_MISSING_DATA and the best available answer is a "
            "specification of what would have to be computed. It does "
            "not call any root timeless: the main field has secular "
            "variation, so a root is valid for a stated epoch and no "
            "longer, and a root quoted without an epoch is ambiguous by "
            "the drift across whatever span the reader assumes. It does "
            "not treat the 2025-2030 forecast window as definitive, and "
            "it does not measure anything."),
        "verdict": VERDICT,
    }
