"""P45 — Known-anchor calibration MODE.

Given ``(source_vector, known_point)`` anchor pairs, fit the parameters of a
source-semantics transform and score its fit. The mode implements System
Contract **invariant 5**: geographic labels and known destinations remain
*sealed* during transform selection. The fitter operates on numeric anchor
data only — it never sees the human-readable geographic label while choosing a
transform, and it scores the fit *after* selection is frozen.

The governance rule (claim/privacy boundary): a retrospective fit is **not** a
calibrated mapping. A calibration produced by fitting to anchors is, at most,
an ``OPERATOR_HYPOTHESIS``. It is promoted to ``CALIBRATED_MAPPING`` only after
a **prospective known-destination challenge** — the transform is frozen, then a
new anchor is decoded once, and only then is its known point revealed and
scored. Retrospective fit alone never reaches ``CALIBRATED_MAPPING``.

Pure arithmetic. Nothing here measures anything; anchors and epochs are passed
in. The transform family is a synthetic affine map from an abstract source
vector space to ``(latitude, longitude)`` degrees; no source vector is claimed
to identify a real location.

    SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Sequence, Tuple

import numpy as np

from cwatlas.claims import ClaimClass, ClaimError

#: Mean Earth radius (metres) for great-circle residual reporting.
_EARTH_RADIUS_M = 6_371_000.0


class CalibrationError(ValueError):
    """Raised on an invalid, underdetermined, or out-of-order calibration.

    An explicit result state, never a silent guess.
    """


class SealError(ClaimError):
    """Raised when sealed geographic labels are accessed before release.

    Enforces invariant 5: the fitter must not see the geographic label while
    choosing a transform.
    """


def refuse_retrospective_fit_as_calibrated(*_a, **_k) -> None:
    """A retrospective fit is not a calibrated mapping."""
    raise ClaimError(
        "refused: a retrospective fit to known anchors is at most an "
        "OPERATOR_HYPOTHESIS. Promotion to CALIBRATED_MAPPING requires a "
        "prospective known-destination challenge — freeze the transform, "
        "decode a new anchor once, then reveal and score its known point.")


def refuse_label_peek(*_a, **_k) -> None:
    """Geographic labels are sealed during transform selection (invariant 5)."""
    raise SealError(
        "refused: geographic labels are sealed during transform selection. "
        "The fitter chooses a transform from numeric anchor data only; labels "
        "may be revealed for reporting after the calibration is frozen.")


@dataclass(frozen=True)
class Anchor:
    """A calibration anchor: a source vector, a known point, and a label.

    ``source_vector`` is an abstract numeric vector. ``known_point`` is
    ``(latitude_deg, longitude_deg)``. ``label`` is a human-readable
    geographic label that is **sealed** during transform selection.
    """

    source_vector: Tuple[float, ...]
    known_point: Tuple[float, float]
    label: str = ""

    def __post_init__(self) -> None:
        v = tuple(float(x) for x in self.source_vector)
        if not v:
            raise CalibrationError("source_vector must be non-empty.")
        if not all(math.isfinite(x) for x in v):
            raise CalibrationError("source_vector must be finite.")
        lat, lon = float(self.known_point[0]), float(self.known_point[1])
        if not (math.isfinite(lat) and math.isfinite(lon)):
            raise CalibrationError("known_point must be two finite floats.")
        if not (-90.0 <= lat <= 90.0):
            raise CalibrationError(f"latitude must be in [-90, 90], got {lat}.")
        object.__setattr__(self, "source_vector", v)
        object.__setattr__(self, "known_point", (lat, lon))


class SealedAnchorSet:
    """A set of anchors whose geographic labels are sealed for selection.

    The fitter reads :meth:`selection_inputs` — numeric arrays with **no**
    labels. Labels are only reachable through :meth:`revealed_labels`, which
    refuses until :meth:`freeze` marks the transform selection complete. This
    structurally enforces invariant 5.
    """

    def __init__(self, anchors: Sequence[Anchor],
                 *, _allow_empty: bool = False) -> None:
        anchors = tuple(anchors)
        if not anchors and not _allow_empty:
            raise CalibrationError("a calibration needs at least one anchor.")
        dim = len(anchors[0].source_vector) if anchors else 0
        if any(len(a.source_vector) != dim for a in anchors):
            raise CalibrationError("all source vectors must share one dimension.")
        self._anchors = anchors
        self._dim = dim
        self._frozen = False

    @property
    def dim(self) -> int:
        return self._dim

    def __len__(self) -> int:
        return len(self._anchors)

    def split(self, holdout: int) -> Tuple["SealedAnchorSet", "SealedAnchorSet"]:
        """Deterministic train/holdout split (holdout = last ``holdout`` anchors)."""
        if not (0 <= holdout < len(self._anchors)):
            raise CalibrationError(
                f"holdout must be in [0, {len(self._anchors)}), got {holdout}.")
        cut = len(self._anchors) - holdout
        return (SealedAnchorSet(self._anchors[:cut]),
                SealedAnchorSet(self._anchors[cut:], _allow_empty=True))

    def selection_inputs(self) -> Tuple[np.ndarray, np.ndarray]:
        """Numeric anchor data for the fitter: ``(X, Y)``, no labels.

        ``X`` is ``(n, dim)`` source vectors; ``Y`` is ``(n, 2)`` known points.
        """
        X = np.array([a.source_vector for a in self._anchors], dtype=float)
        Y = np.array([a.known_point for a in self._anchors], dtype=float)
        return X, Y

    def freeze(self) -> None:
        """Mark transform selection complete; labels may now be revealed."""
        self._frozen = True

    def revealed_labels(self) -> Tuple[str, ...]:
        """Geographic labels — refused unless the selection is frozen."""
        if not self._frozen:
            refuse_label_peek()
        return tuple(a.label for a in self._anchors)


@dataclass(frozen=True)
class AffineTransform:
    """A synthetic affine source-semantics transform: ``point = A v + b``.

    ``A`` is ``2 x dim`` (rows: latitude, longitude); ``b`` is length 2. Stored
    as exact python tuples alongside any displayed decimals.
    """

    A: Tuple[Tuple[float, ...], ...]
    b: Tuple[float, float]
    dim: int

    def apply(self, source_vector: Sequence[float]) -> Tuple[float, float]:
        v = np.array([float(x) for x in source_vector], dtype=float)
        if v.shape != (self.dim,):
            raise CalibrationError(
                f"source_vector has dim {v.shape}, transform expects {self.dim}.")
        A = np.array(self.A, dtype=float)
        b = np.array(self.b, dtype=float)
        lat, lon = (A @ v + b).tolist()
        return (float(lat), float(lon))


@dataclass(frozen=True)
class CalibrationResult:
    """A frozen calibration: a fitted transform and its scored fit.

    Always ``OPERATOR_HYPOTHESIS`` — a retrospective fit, never a calibrated
    mapping. The claim class only advances via a prospective challenge.
    """

    transform: AffineTransform
    train_rms_m: float
    holdout_rms_m: float
    n_train: int
    n_holdout: int
    claim_class: str = ClaimClass.OPERATOR_HYPOTHESIS.value
    frozen: bool = True
    labels_sealed_during_selection: bool = True

    def predict(self, source_vector: Sequence[float]) -> Tuple[float, float]:
        return self.transform.apply(source_vector)


@dataclass(frozen=True)
class ChallengeResult:
    """The outcome of a prospective known-destination challenge."""

    predicted_point: Tuple[float, float]
    revealed_point: Tuple[float, float]
    residual_m: float
    tolerance_m: float
    passed: bool
    claim_class: str
    justification: str


def great_circle_m(p: Tuple[float, float], q: Tuple[float, float]) -> float:
    """Great-circle distance in metres between ``(lat, lon)`` points (degrees)."""
    lat1, lon1 = math.radians(p[0]), math.radians(p[1])
    lat2, lon2 = math.radians(q[0]), math.radians(q[1])
    dlat, dlon = lat2 - lat1, lon2 - lon1
    a = (math.sin(dlat / 2.0) ** 2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2.0) ** 2)
    return 2.0 * _EARTH_RADIUS_M * math.asin(min(1.0, math.sqrt(a)))


def _rms_residual(transform: AffineTransform,
                  anchor_set: SealedAnchorSet) -> float:
    if len(anchor_set) == 0:
        return 0.0
    X, Y = anchor_set.selection_inputs()
    total = 0.0
    for v, point in zip(X, Y):
        pred = transform.apply(v)
        d = great_circle_m(pred, (float(point[0]), float(point[1])))
        total += d * d
    return math.sqrt(total / len(anchor_set))


def fit_transform(anchor_set: SealedAnchorSet) -> AffineTransform:
    """Fit an affine transform to numeric anchor data by least squares.

    Reads only :meth:`SealedAnchorSet.selection_inputs` — no geographic label
    reaches this fitter (invariant 5). Refuses an underdetermined system.
    """
    X, Y = anchor_set.selection_inputs()
    n, dim = X.shape
    if n < dim + 1:
        raise CalibrationError(
            f"underdetermined: fitting a {dim}-D affine transform needs at "
            f"least {dim + 1} anchors, got {n}. Returning an explicit refusal "
            f"rather than a guessed transform.")
    design = np.hstack([X, np.ones((n, 1))])  # [v | 1]
    coeffs, *_ = np.linalg.lstsq(design, Y, rcond=None)  # (dim+1, 2)
    A = coeffs[:dim, :].T  # (2, dim)
    b = coeffs[dim, :]     # (2,)
    return AffineTransform(
        A=tuple(tuple(float(x) for x in row) for row in A),
        b=(float(b[0]), float(b[1])),
        dim=dim,
    )


def fit_calibration(anchor_set: SealedAnchorSet,
                    holdout: int = 0) -> CalibrationResult:
    """Fit and score a calibration in sealed MODE.

    1. Split the anchors deterministically into train / holdout.
    2. Fit the transform on the training anchors — labels sealed.
    3. Freeze selection, then score train and holdout fit.

    The result is an ``OPERATOR_HYPOTHESIS``. It never reaches
    ``CALIBRATED_MAPPING`` without a prospective challenge.
    """
    train, hold = anchor_set.split(holdout)
    transform = fit_transform(train)          # labels sealed during selection
    anchor_set.freeze()                       # selection complete
    train.freeze()
    hold.freeze()
    return CalibrationResult(
        transform=transform,
        train_rms_m=_rms_residual(transform, train),
        holdout_rms_m=_rms_residual(transform, hold),
        n_train=len(train),
        n_holdout=len(hold),
    )


def prospective_challenge(calibration: CalibrationResult,
                          challenge_source_vector: Sequence[float],
                          revealed_point: Tuple[float, float],
                          tolerance_m: float,
                          training_anchors: Optional[SealedAnchorSet] = None
                          ) -> ChallengeResult:
    """Run a prospective known-destination challenge against a frozen calibration.

    The transform must already be frozen (it is, by construction). The predicted
    point is computed **before** ``revealed_point`` is scored. On success the
    result is promoted to ``CALIBRATED_MAPPING``; otherwise it stays
    ``OPERATOR_HYPOTHESIS``. If the challenge vector duplicates a training
    anchor, the challenge is not prospective and is refused.
    """
    if not calibration.frozen:
        refuse_retrospective_fit_as_calibrated()
    if not (math.isfinite(tolerance_m) and tolerance_m > 0.0):
        raise CalibrationError("tolerance_m must be positive and finite.")
    v = tuple(float(x) for x in challenge_source_vector)
    if training_anchors is not None:
        X, _ = training_anchors.selection_inputs()
        if any(np.allclose(v, row) for row in X):
            raise CalibrationError(
                "refused: the challenge vector duplicates a training anchor; a "
                "challenge must be prospective (unseen) to be admissible.")
    predicted = calibration.predict(v)
    revealed = (float(revealed_point[0]), float(revealed_point[1]))
    residual = great_circle_m(predicted, revealed)
    passed = residual <= tolerance_m
    if passed:
        claim = ClaimClass.CALIBRATED_MAPPING.value
        why = ("prospective known-destination challenge passed within "
               f"tolerance ({residual:.1f} m <= {tolerance_m:.1f} m)")
    else:
        claim = ClaimClass.OPERATOR_HYPOTHESIS.value
        why = ("prospective challenge missed tolerance "
               f"({residual:.1f} m > {tolerance_m:.1f} m); remains a hypothesis")
    return ChallengeResult(
        predicted_point=predicted,
        revealed_point=revealed,
        residual_m=residual,
        tolerance_m=float(tolerance_m),
        passed=passed,
        claim_class=claim,
        justification=why,
    )


def calibration_report() -> dict:
    """P45 declaration receipt."""
    return {
        "phase_id": "P45",
        "what_this_is": (
            "known-anchor calibration MODE: fit a synthetic affine source-"
            "semantics transform to (source_vector, known_point) anchors with "
            "geographic labels sealed during transform selection (invariant "
            "5), score train/holdout fit, and promote to CALIBRATED_MAPPING "
            "only after a prospective known-destination challenge."),
        "claim_class": ClaimClass.OPERATOR_HYPOTHESIS.value,
        "labels_sealed_during_selection": True,
        "retrospective_fit_is_calibrated": False,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "source_vector_geographic_semantics": "NOT_CLAIMED",
        "verdict": "KNOWN_ANCHOR_CALIBRATION_SEALED_NO_RETROSPECTIVE_PROMOTION",
    }
