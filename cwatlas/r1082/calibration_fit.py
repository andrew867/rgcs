"""P18 — Two-anchor orientation and token/family calibration fit.

Only two anchors are sealed: the **Wilkes fixed root** (the face-centre binding,
the first correspondence) and the **Stonehenge training anchor** (the
vector-to-location record, the second correspondence, P17). This module fits the
remaining *low-parameter* calibration against those two — and no others:

* the **orientation angle** ``theta`` about the body mean-rotation axis
  (South-Up ``+Z``) — the single continuous free parameter (locked topology and
  handedness are *not* reopened);
* the **spatialization family** selection (P15) — a discrete choice among the
  bounded four (``F1..F4``).

Degrees of freedom versus anchors (made explicit, required work #5):

* one continuous parameter (``theta``) is fit against two spherical
  correspondences (four scalar constraints) → the continuous fit is
  **OVER-determined** and its residual is generally non-zero;
* the discrete family choice is **UNDER-determined**: two anchors cannot certify
  one of four codec families. So this module **never silently picks one** — it
  returns the whole **ranked, retained alias set** and refuses to collapse it to
  a single measured pick.

The closed-form ``theta`` is the Wahba problem restricted to a single axis:
maximise ``A cos(theta) + B sin(theta)`` with ``A = sum(cx*tx + cy*ty)``,
``B = sum(cx*ty - cy*tx)`` over the correspondences, giving
``theta* = atan2(B, A)`` (pure numpy, no ``scipy.optimize``). ``hypot(A, B)`` is
the conditioning: near zero the azimuth is ill-determined.

Every result is a ``CALIBRATED_CANDIDATE`` at most — never measured, never
source-origin-validated. See :mod:`cwatlas.r1082.claims`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple

import numpy as np

from cwatlas.r1082 import claims, spatialization, stonehenge_anchor, wilkes
from cwatlas.r1082.partition import build_partition

CALIBRATION_CODEC_ID = "CW-R1082-CALFIT"
CALIBRATION_CODEC_VERSION = "1.0.0"

#: The single continuous free parameter fit here (orientation angle).
CONTINUOUS_PARAMETERS = 1

#: The number of sealed anchors (Wilkes fixed root + Stonehenge).
ANCHOR_COUNT = 2

#: Each spherical correspondence supplies two scalar constraints.
SCALAR_CONSTRAINTS = ANCHOR_COUNT * 2

#: Conditioning below this (``hypot(A, B)``) marks an ill-determined azimuth.
_CONDITIONING_FLOOR = 1e-6


class CalibrationError(ValueError):
    """Raised on an overparameterised or ill-posed calibration request."""


def refuse_overparameterized(n_parameters: int,
                             n_constraints: int = SCALAR_CONSTRAINTS) -> None:
    """Reject a fit that asks for more parameters than the anchors constrain.

    Two anchors give at most :data:`SCALAR_CONSTRAINTS` scalar constraints.
    Requesting more free parameters than that is an overparameterised fit and is
    refused (required work #5: reject overparameterized fits).
    """
    if n_parameters > n_constraints:
        raise CalibrationError(
            f"refused: an overparameterised fit ({n_parameters} free "
            f"parameters) against only {n_constraints} scalar constraints from "
            f"{ANCHOR_COUNT} anchors. The locked calibration fits at most the "
            f"orientation angle plus a discrete family choice; do not invent "
            f"free parameters the anchors cannot determine.")


def _unit(v) -> np.ndarray:
    a = np.asarray(v, dtype=float).reshape(-1)
    n = float(np.linalg.norm(a))
    if n < 1e-15:
        raise CalibrationError("degenerate zero-length direction")
    return a / n


def _rot_z(theta_rad: float) -> np.ndarray:
    c, s = math.cos(theta_rad), math.sin(theta_rad)
    return np.array([[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]], dtype=float)


def _angle_between(a: np.ndarray, b: np.ndarray) -> float:
    d = float(np.clip(np.dot(a, b), -1.0, 1.0))
    return math.acos(d)


def _solve_axis_rotation(
        pairs: Tuple[Tuple[np.ndarray, np.ndarray], ...]) -> Tuple[float, float]:
    """Closed-form best ``theta`` about ``+Z`` and the conditioning ``hypot``.

    Maximises ``sum <Rz(theta) c, t>`` = ``A cos(theta) + B sin(theta)``.
    """
    A = B = 0.0
    for c, t in pairs:
        A += c[0] * t[0] + c[1] * t[1]
        B += c[0] * t[1] - c[1] * t[0]
    return math.atan2(B, A), math.hypot(A, B)


@dataclass(frozen=True)
class FamilyFit:
    """The two-anchor orientation fit for one spatialization family.

    Attributes
    ----------
    family_name:
        The bounded-ensemble family this fit is for.
    theta_deg, theta_rad:
        The best orientation angle about the body mean-rotation axis.
    wilkes_residual_rad, stonehenge_residual_rad:
        Per-anchor angular residuals after applying the fitted rotation.
    combined_rms_rad:
        Root-mean-square of the per-anchor residuals (the ranking key).
    conditioning:
        ``hypot(A, B)`` of the axis-rotation solve; near zero is ill-determined.
    well_conditioned:
        Whether the azimuth is determined above :data:`_CONDITIONING_FLOOR`.
    """

    family_name: str
    theta_deg: float
    theta_rad: float
    wilkes_residual_rad: float
    stonehenge_residual_rad: float
    combined_rms_rad: float
    conditioning: float
    well_conditioned: bool

    def to_dict(self) -> dict:
        return {
            "family_name": self.family_name,
            "theta_deg": self.theta_deg,
            "wilkes_residual_deg": math.degrees(self.wilkes_residual_rad),
            "stonehenge_residual_deg": math.degrees(self.stonehenge_residual_rad),
            "combined_rms_deg": math.degrees(self.combined_rms_rad),
            "conditioning": self.conditioning,
            "well_conditioned": self.well_conditioned,
        }


def fit_family(family: spatialization.SpatializationFamily,
               anchor: stonehenge_anchor.StonehengeAnchor,
               ensemble: wilkes.WilkesEnsemble,
               *, ico=None) -> FamilyFit:
    """Fit the orientation angle for one family against the two sealed anchors.

    The Wilkes correspondence is the root face-centre direction versus the
    selected Wilkes centroid direction (the fixed-root binding). The Stonehenge
    correspondence is the family's mapped route centroid versus the synthetic
    public anchor direction. A single rotation about ``+Z`` is fit jointly to
    both; residuals are reported per anchor (never averaged away silently).
    """
    if ico is None:
        ico = build_partition().ico
    # First correspondence: Wilkes fixed-root face-centre binding.
    c_wilkes = _unit(ensemble.root_face_center_direction())
    t_wilkes = _unit(ensemble.selected().centroid_unit_vector())
    # Second correspondence: Stonehenge vector-to-location under this family.
    sp = family.map_route(anchor.tokens, ico=ico)
    c_stone = _unit(sp.centroid)
    t_stone = _unit(anchor.anchor_unit_vector())

    pairs = ((c_wilkes, t_wilkes), (c_stone, t_stone))
    theta, cond = _solve_axis_rotation(pairs)
    rot = _rot_z(theta)
    r_wilkes = _angle_between(rot @ c_wilkes, t_wilkes)
    r_stone = _angle_between(rot @ c_stone, t_stone)
    rms = math.sqrt((r_wilkes ** 2 + r_stone ** 2) / 2.0)
    return FamilyFit(
        family_name=family.name,
        theta_deg=math.degrees(theta),
        theta_rad=theta,
        wilkes_residual_rad=r_wilkes,
        stonehenge_residual_rad=r_stone,
        combined_rms_rad=rms,
        conditioning=cond,
        well_conditioned=cond > _CONDITIONING_FLOOR,
    )


@dataclass(frozen=True)
class CalibrationFit:
    """The full two-anchor fit across the bounded family ensemble.

    ``fits`` is the ranked tuple (best combined residual first). The family
    choice is structurally **UNDER-determined** by two anchors, so the whole
    ranked set is retained; :meth:`refuse_single_measured_pick` refuses any
    collapse to one measured winner.
    """

    fits: Tuple[FamilyFit, ...]
    anchor_count: int = ANCHOR_COUNT
    continuous_parameters: int = CONTINUOUS_PARAMETERS

    def best(self) -> FamilyFit:
        """The top-ranked family — a CANDIDATE only, not a sealed selection."""
        return self.fits[0]

    def ranked_names(self) -> Tuple[str, ...]:
        return tuple(f.family_name for f in self.fits)

    def retained(self, band_rad: Optional[float] = None) -> Tuple[FamilyFit, ...]:
        """Families retained as candidates.

        With ``band_rad=None`` (the default governance stance) the entire ranked
        set is retained: two anchors cannot exclude any of four families. With a
        band, families within ``band_rad`` of the best combined residual are
        retained — and tied families are *always* retained together (they are
        indistinguishable to the anchors).
        """
        if band_rad is None:
            return self.fits
        best = self.fits[0].combined_rms_rad
        return tuple(f for f in self.fits
                     if f.combined_rms_rad <= best + band_rad)

    def result_class(self) -> str:
        """The family-level result class.

        Two anchors under-determine the discrete family choice, so the result is
        always an alias set / under-determined — never a single measured point.
        """
        return claims.ResultClass.CANDIDATE_ALIAS_SET.value

    def refuse_single_measured_pick(self, *_a, **_k) -> None:
        """Refuse collapsing the retained alias set to one measured pick."""
        claims.refuse_candidate_as_measured()

    def dof_report(self) -> dict:
        """Explicit over/under-determination accounting (required work #5)."""
        return {
            "continuous_parameters_fitted": self.continuous_parameters,
            "orientation_axis": "BODY_MEAN_ROTATION_AXIS_SOUTH_UP_PLUS_Z",
            "discrete_family_choices": len(self.fits),
            "anchor_count": self.anchor_count,
            "scalar_constraints": self.anchor_count * 2,
            "continuous_determination": (
                "OVER_DETERMINED"
                if self.anchor_count * 2 > self.continuous_parameters
                else "UNDER_DETERMINED"),
            "family_determination": "UNDER_DETERMINED",
            "reason": (
                "one orientation angle is fit against four scalar constraints "
                "(over-determined), but two anchors cannot certify one of four "
                "discrete families (under-determined) — the whole ranked set is "
                "retained, never collapsed to a single measured pick"),
        }


def fit_all(anchor: Optional[stonehenge_anchor.StonehengeAnchor] = None,
            ensemble: Optional[wilkes.WilkesEnsemble] = None,
            *, ico=None) -> CalibrationFit:
    """Fit every bounded family against the two sealed anchors, ranked.

    Uses the P17 Stonehenge anchor and the default Wilkes ensemble unless the
    caller supplies them. The returned :class:`CalibrationFit` is ranked by
    combined residual but retains the whole set.
    """
    if anchor is None:
        anchor = stonehenge_anchor.build_anchor()
    if ensemble is None:
        ensemble = wilkes.default_ensemble()
    if ico is None:
        ico = build_partition().ico
    fits = tuple(fit_family(fam, anchor, ensemble, ico=ico)
                 for fam in spatialization.FAMILIES)
    ranked = tuple(sorted(fits, key=lambda f: (f.combined_rms_rad,
                                               f.family_name)))
    return CalibrationFit(fits=ranked)


def calibration_fit_report() -> dict:
    """P18 declaration receipt. Two anchors; nothing measured; no silent pick."""
    fit = fit_all()
    return {
        "phase_id": "P18",
        "tranche": "T05",
        "what_this_is": (
            "the two-anchor orientation and family calibration fit: one "
            "orientation angle about the body axis is fit against the Wilkes "
            "fixed-root and Stonehenge correspondences for each of the four "
            "spatialization families; residuals are reported per family and the "
            "whole ranked set is retained."),
        "codec_id": CALIBRATION_CODEC_ID,
        "codec_version": CALIBRATION_CODEC_VERSION,
        "anchors": ["WILKES_FIXED_ROOT", stonehenge_anchor.STONEHENGE_FIXTURE_ID],
        "ranking": [f.to_dict() for f in fit.fits],
        "ranked_family_order": list(fit.ranked_names()),
        "degrees_of_freedom": fit.dof_report(),
        "family_result_class": fit.result_class(),
        "silent_single_pick": "REFUSED",
        "overparameterized_fit": "REFUSED",
        "evidence_class": claims.EvidenceClass.CALIBRATED_CANDIDATE.value,
        "max_evidence": claims.MAX_CANDIDATE_EVIDENCE.value,
        "measured_here": "nothing",
        "physical_validation": "PHYSICAL_VALIDATION_NOT_CLAIMED",
        "physical_effects": "PHYSICAL_EFFECTS_NOT_CLAIMED",
        "source_origin": "SOURCE_ORIGIN_NOT_VALIDATED",
        "verdict": "TWO_ANCHOR_FIT_RANKED_RETAINED_SET_NO_SILENT_PICK",
        "what_this_does_not_say": (
            "The fit selects an orientation angle under a declared family, but "
            "two anchors under-determine the family choice. The result is a "
            "CALIBRATED_CANDIDATE alias set, not a measured selection and not a "
            "validated source origin."),
    }
