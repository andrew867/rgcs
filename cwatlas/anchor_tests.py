"""P46 — Synthetic anchor tests and planted-signal recovery.

The public baseline for calibration is **synthetic controls**: a hidden
synthetic ``source_vector -> point`` mapping is planted, and the P45 pipeline is
run to check whether it can *recover* that mapping (POWER). No private data and
no real coordinates are used.

"Stonehenge" appears here only as a **named synthetic control** — a
user-reported labeled candidate, never a decoded site. All governance runs
through :mod:`cwatlas.claims`:

* :func:`cwatlas.claims.refuse_site_decoded` raises if any code asserts a real
  site was decoded from the vector family;
* :func:`cwatlas.claims.refuse_close_match_as_intent` raises if a close
  arithmetic proximity to the synthetic control is treated as intended
  encoding.

The synthetic anchors below use **invented** coordinates, not the real
coordinates of any site, person, or place.

Pure arithmetic and deterministic (all randomness is seeded).

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence, Tuple

import numpy as np

from cwatlas import claims
from cwatlas.calibration import (
    Anchor,
    AffineTransform,
    CalibrationResult,
    SealedAnchorSet,
    fit_calibration,
)
from cwatlas.claims import ClaimClass

#: A named synthetic control. It is NOT the real Stonehenge and decodes nothing.
STONEHENGE_SYNTHETIC_LABEL = "Stonehenge (NAMED SYNTHETIC CONTROL — NOT A DECODE)"
#: Invented, obviously-synthetic coordinates for the control (not a real site).
STONEHENGE_SYNTHETIC_POINT: Tuple[float, float] = (12.5, 34.25)


@dataclass(frozen=True)
class PlantedSignal:
    """A hidden synthetic mapping planted into anchors for a recovery test."""

    true_transform: AffineTransform
    anchors: Tuple[Anchor, ...]
    dim: int
    noise_m: float


@dataclass(frozen=True)
class RecoveryResult:
    """The outcome of trying to recover a planted signal (POWER)."""

    recovered_transform: AffineTransform
    max_param_abs_error: float
    holdout_rms_m: float
    recovered: bool
    claim_class: str = ClaimClass.MATHEMATICAL_TRANSLATION.value


def _planted_transform(dim: int, seed: int) -> AffineTransform:
    """Deterministically construct a hidden true affine transform."""
    rng = np.random.default_rng(seed)
    # Small coefficients so predicted points stay in valid degree ranges.
    A = rng.uniform(-0.5, 0.5, size=(2, dim))
    b = np.array([rng.uniform(-10.0, 10.0), rng.uniform(-20.0, 20.0)])
    return AffineTransform(
        A=tuple(tuple(float(x) for x in row) for row in A),
        b=(float(b[0]), float(b[1])),
        dim=dim,
    )


def plant_signal(n_anchors: int = 12, dim: int = 3, seed: int = 20260725,
                 noise_deg: float = 0.0) -> PlantedSignal:
    """Plant a hidden synthetic ``source_vector -> point`` mapping.

    Generates ``n_anchors`` synthetic source vectors, applies a hidden true
    affine transform to produce known points, and optionally adds seeded noise.
    Deterministic for a fixed seed.
    """
    if n_anchors < dim + 2:
        raise ValueError("need at least dim+2 anchors for a train/holdout split.")
    rng = np.random.default_rng(seed + 1)
    true = _planted_transform(dim, seed)
    anchors = []
    for i in range(n_anchors):
        v = rng.uniform(-1.0, 1.0, size=dim)
        lat, lon = true.apply(v)
        if noise_deg:
            lat += float(rng.normal(0.0, noise_deg))
            lon += float(rng.normal(0.0, noise_deg))
        lat = max(-90.0, min(90.0, lat))
        anchors.append(Anchor(
            source_vector=tuple(float(x) for x in v),
            known_point=(lat, lon),
            label=f"synthetic-anchor-{i:02d}",
        ))
    # Approximate metres-per-degree for reporting the noise scale.
    return PlantedSignal(
        true_transform=true,
        anchors=tuple(anchors),
        dim=dim,
        noise_m=noise_deg * 111_320.0,
    )


def recover_signal(planted: PlantedSignal, holdout: int = 3,
                   param_tolerance: float = 1e-6) -> RecoveryResult:
    """Run the P45 calibration pipeline and check planted-signal recovery.

    POWER test: with a well-posed planted mapping the fitted transform should
    reproduce the planted coefficients (within tolerance under zero noise) and
    predict the holdout anchors accurately.
    """
    sealed = SealedAnchorSet(planted.anchors)
    calibration = fit_calibration(sealed, holdout=holdout)
    max_err = _max_param_error(planted.true_transform,
                               calibration.transform)
    recovered = max_err <= param_tolerance
    return RecoveryResult(
        recovered_transform=calibration.transform,
        max_param_abs_error=max_err,
        holdout_rms_m=calibration.holdout_rms_m,
        recovered=recovered,
    )


def _max_param_error(a: AffineTransform, b: AffineTransform) -> float:
    if a.dim != b.dim:
        return float("inf")
    ea = np.abs(np.array(a.A) - np.array(b.A)).max()
    eb = np.abs(np.array(a.b) - np.array(b.b)).max()
    return float(max(ea, eb))


def stonehenge_synthetic_anchor() -> Anchor:
    """Return the named synthetic Stonehenge control anchor.

    A user-reported labeled candidate for testing only. Its coordinates are
    invented and it decodes nothing.
    """
    return Anchor(
        source_vector=(0.1, 0.2, 0.3),
        known_point=STONEHENGE_SYNTHETIC_POINT,
        label=STONEHENGE_SYNTHETIC_LABEL,
    )


def assert_site_decoded(site: str = "Stonehenge", *, assert_real: bool = True
                        ) -> None:
    """Attempting to assert a real site was decoded is always refused.

    This is the guard the red team calls: no real site is decoded from the
    vector family, so this delegates to
    :func:`cwatlas.claims.refuse_site_decoded` and always raises.
    """
    if assert_real:
        claims.refuse_site_decoded(site)


def close_match_is_not_intent(predicted: Tuple[float, float],
                              synthetic_control: Tuple[float, float],
                              radius_m: float = 5_000.0) -> None:
    """A close arithmetic match to the synthetic control is not intent.

    Even when a prediction lands arithmetically near the named synthetic
    control, that proximity does not establish intended encoding — it is
    refused via :func:`cwatlas.claims.refuse_close_match_as_intent`.
    """
    from cwatlas.calibration import great_circle_m
    if great_circle_m(predicted, synthetic_control) <= radius_m:
        claims.refuse_close_match_as_intent()


def anchor_tests_report() -> dict:
    """P46 declaration receipt."""
    return {
        "phase_id": "P46",
        "what_this_is": (
            "synthetic anchor controls and a planted-signal recovery test: a "
            "hidden synthetic source_vector->point mapping is planted and the "
            "P45 pipeline recovers it (POWER); 'Stonehenge' is a named "
            "synthetic control only — no real site is decoded and a close "
            "arithmetic match is not intent."),
        "claim_class": ClaimClass.MATHEMATICAL_TRANSLATION.value,
        "stonehenge_is": "NAMED_SYNTHETIC_CONTROL_NOT_A_DECODE",
        "synthetic_coordinates": True,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "PLANTED_SIGNAL_RECOVERED_NO_SITE_DECODED",
    }
