"""P32 — Coordinate uncertainty and error regions.

Propagates two sources of coordinate uncertainty — the codec's **quantization**
step and the caller-supplied **input sigma** — into an explicit error region:
a circle, an ellipse, or a cell polygon. Each region carries its area and a
**search-space count** (how many cells of a declared size it spans). This is
what a vector -> map decode returns when calibration is missing: a region or a
heatmap, never invented precision (architecture spec: "insufficient calibration
-> region, heatmap, or refusal, never invented precision").

The governance rule: **invented precision is refused.** A region may not
collapse to a point (zero area) unless the caller supplies an explicit
justification. Silent point precision — a decode presented as an exact pin with
no supporting calibration — is a typed refusal.

Quantization is combined as a uniform-quantizer standard deviation
(``step / sqrt(12)``) in quadrature with the input sigma. Regions are treated as
locally planar (metres about the given centre); area is in square metres.

Pure arithmetic. Nothing here measures anything; every input is passed in.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Tuple

from cwatlas.claims import ClaimClass, ClaimError

#: Uniform-quantizer standard deviation factor: sigma = step / sqrt(12).
_QUANT_SIGMA_FACTOR = 1.0 / math.sqrt(12.0)
#: Default confidence multiplier (k-sigma) for a region radius.
DEFAULT_K_SIGMA = 2.0


class UncertaintyError(ValueError):
    """Raised on an invalid uncertainty input.

    An explicit result state, never a silent guess.
    """


class RegionKind(Enum):
    """The kind of error region."""

    CIRCLE = "CIRCLE"
    ELLIPSE = "ELLIPSE"
    CELL_POLYGON = "CELL_POLYGON"


@dataclass(frozen=True)
class ErrorRegion:
    """An error region about a centre coordinate, with area and search space.

    ``center`` is ``(latitude_deg, longitude_deg)``. Metric parameters
    (``radius_m``, ``semi_major_m``, ``semi_minor_m``, polygon vertices) are in
    metres about the centre. ``search_space_count`` is the number of declared
    cells the region spans.
    """

    kind: RegionKind
    center: Tuple[float, float]
    area_m2: float
    search_space_count: int
    combined_sigma_m: float
    k_sigma: float
    cell_size_m: float
    justification: str
    radius_m: Optional[float] = None
    semi_major_m: Optional[float] = None
    semi_minor_m: Optional[float] = None
    orientation_deg: Optional[float] = None
    vertices_m: Tuple[Tuple[float, float], ...] = field(default_factory=tuple)


def combine_sigma(input_sigma_m: float, quantization_m: float) -> float:
    """Combine input sigma with the quantization sigma in quadrature.

    The quantization contributes ``step / sqrt(12)`` (uniform quantizer).
    """
    if not math.isfinite(input_sigma_m) or input_sigma_m < 0.0:
        raise UncertaintyError("input_sigma_m must be finite and non-negative.")
    if not math.isfinite(quantization_m) or quantization_m < 0.0:
        raise UncertaintyError("quantization_m must be finite and non-negative.")
    quant_sigma = quantization_m * _QUANT_SIGMA_FACTOR
    return math.hypot(input_sigma_m, quant_sigma)


def _validate_center(center: Tuple[float, float]) -> Tuple[float, float]:
    lat, lon = float(center[0]), float(center[1])
    if not (math.isfinite(lat) and math.isfinite(lon)):
        raise UncertaintyError("center must be two finite floats.")
    if not (-90.0 <= lat <= 90.0):
        raise UncertaintyError(f"center latitude must be in [-90, 90], got {lat}.")
    return (lat, lon)


def _validate_cell_size(cell_size_m: float) -> float:
    if not math.isfinite(cell_size_m) or cell_size_m <= 0.0:
        raise UncertaintyError("cell_size_m must be positive and finite.")
    return float(cell_size_m)


def _guard_invented_precision(area_m2: float, justification: str) -> None:
    """Refuse a zero-area (point) region unless it is explicitly justified."""
    if area_m2 <= 0.0 and not justification:
        refuse_invented_precision()


def refuse_invented_precision(*_a, **_k) -> None:
    """A region collapsed to a point without justification is refused."""
    raise ClaimError(
        "refused: invented precision. An error region collapsed to a point "
        "(zero area) asserts exact precision the data do not support. A decode "
        "without calibration returns a region, a heatmap, or a refusal — never "
        "a silent exact pin. Supply an explicit justification to declare a "
        "genuinely point-sized region.")


def propagate_circle(
    center: Tuple[float, float],
    input_sigma_m: float,
    quantization_m: float,
    cell_size_m: float,
    k_sigma: float = DEFAULT_K_SIGMA,
    justification: str = "",
) -> ErrorRegion:
    """Propagate uncertainty into a circular error region.

    Radius = ``k_sigma * combined_sigma``. Area = ``pi r^2``. Refuses invented
    precision if the region collapses to a point without justification.
    """
    lat, lon = _validate_center(center)
    cell = _validate_cell_size(cell_size_m)
    if not math.isfinite(k_sigma) or k_sigma <= 0.0:
        raise UncertaintyError("k_sigma must be positive and finite.")
    sigma = combine_sigma(input_sigma_m, quantization_m)
    radius = k_sigma * sigma
    area = math.pi * radius * radius
    _guard_invented_precision(area, justification)
    return ErrorRegion(
        kind=RegionKind.CIRCLE,
        center=(lat, lon),
        area_m2=area,
        search_space_count=_search_space_count(area, cell),
        combined_sigma_m=sigma,
        k_sigma=k_sigma,
        cell_size_m=cell,
        justification=justification,
        radius_m=radius,
    )


def propagate_ellipse(
    center: Tuple[float, float],
    sigma_major_m: float,
    sigma_minor_m: float,
    orientation_deg: float,
    quantization_m: float,
    cell_size_m: float,
    k_sigma: float = DEFAULT_K_SIGMA,
    justification: str = "",
) -> ErrorRegion:
    """Propagate anisotropic uncertainty into an elliptical error region.

    Each axis combines its input sigma with the quantization sigma in
    quadrature. Area = ``pi a b`` for semi-axes ``a = k*sigma_major``,
    ``b = k*sigma_minor``.
    """
    lat, lon = _validate_center(center)
    cell = _validate_cell_size(cell_size_m)
    if not math.isfinite(k_sigma) or k_sigma <= 0.0:
        raise UncertaintyError("k_sigma must be positive and finite.")
    if not math.isfinite(orientation_deg):
        raise UncertaintyError("orientation_deg must be finite.")
    sig_a = combine_sigma(sigma_major_m, quantization_m)
    sig_b = combine_sigma(sigma_minor_m, quantization_m)
    semi_major = k_sigma * sig_a
    semi_minor = k_sigma * sig_b
    area = math.pi * semi_major * semi_minor
    _guard_invented_precision(area, justification)
    combined = math.hypot(sig_a, sig_b)
    return ErrorRegion(
        kind=RegionKind.ELLIPSE,
        center=(lat, lon),
        area_m2=area,
        search_space_count=_search_space_count(area, cell),
        combined_sigma_m=combined,
        k_sigma=k_sigma,
        cell_size_m=cell,
        justification=justification,
        semi_major_m=semi_major,
        semi_minor_m=semi_minor,
        orientation_deg=float(orientation_deg),
    )


def cell_polygon(
    center: Tuple[float, float],
    cell_size_m: float,
    justification: str = "quantization cell footprint",
) -> ErrorRegion:
    """A square cell-polygon region of one quantization cell about the centre.

    The region is the codec cell itself: a square of side ``cell_size_m``. Its
    non-zero area is justified by the quantization footprint.
    """
    lat, lon = _validate_center(center)
    cell = _validate_cell_size(cell_size_m)
    half = cell / 2.0
    vertices = (
        (-half, -half), (half, -half), (half, half), (-half, half),
    )
    area = cell * cell
    _guard_invented_precision(area, justification)
    quant_sigma = cell * _QUANT_SIGMA_FACTOR
    return ErrorRegion(
        kind=RegionKind.CELL_POLYGON,
        center=(lat, lon),
        area_m2=area,
        search_space_count=_search_space_count(area, cell),
        combined_sigma_m=quant_sigma,
        k_sigma=1.0,
        cell_size_m=cell,
        justification=justification,
        vertices_m=vertices,
    )


def _search_space_count(area_m2: float, cell_size_m: float) -> int:
    """Number of declared cells spanned by a region area (at least 1)."""
    cell_area = cell_size_m * cell_size_m
    return max(1, int(math.ceil(area_m2 / cell_area)))


def uncertainty_report() -> dict:
    """P32 declaration receipt. Records the region discipline."""
    return {
        "phase_id": "P32",
        "what_this_is": (
            "propagation of quantization (step/sqrt(12)) and input sigma into "
            "circular, elliptical, or cell-polygon error regions, each with an "
            "area and a search-space count; a vector->map decode without "
            "calibration returns a region or heatmap, never invented "
            "precision."),
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "region_kinds": [k.value for k in RegionKind],
        "quantization_sigma_factor": _QUANT_SIGMA_FACTOR,
        "default_k_sigma": DEFAULT_K_SIGMA,
        "invented_precision_refused": True,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "UNCERTAINTY_REGIONS_WITH_SEARCH_SPACE_NO_INVENTED_PRECISION",
    }
