"""The frozen calibration is *applied*, not merely declared (non-cosmetic).

R10.8.2 fits one azimuth per family against the two sealed anchors and seals it
in the freeze receipt. Earlier, ``geocode_forward`` read no per-family
orientation from the real ``FrozenCalibration`` and silently fell back to the
identity rotation, so a "calibrated" decode was indistinguishable from an
uncalibrated one. These tests pin the wiring:

* the frozen profile exposes a proper (orthonormal, det +1) rotation per family;
* decoding the Stonehenge *training* vector under the real frozen profile
  applies each family's fitted rotation, so the placement differs from the
  identity/uncalibrated placement;
* and — the honest part — even the best family reproduces the training anchor
  only to within its sealed angular residual (hundreds of km on the surface),
  never a manufactured point-hit. A single azimuth cannot align two arbitrary
  anchor directions, so the atlas renders an alias set, not a Stonehenge pin.
  This is the guard against a future overfit / famous-place reward.
"""

from __future__ import annotations

import math

import numpy as np

from cwatlas.r1082 import (
    calibration_fit,
    calibration_freeze,
    geocode_forward,
)

STONEHENGE_LATLON = (51.1789, -1.8262)
STONEHENGE_TRAINING_VECTOR = "165876523"


def _haversine_km(a, b) -> float:
    r = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    dla, dlo = la2 - la1, lo2 - lo1
    h = (math.sin(dla / 2) ** 2
         + math.cos(la1) * math.cos(la2) * math.sin(dlo / 2) ** 2)
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def _frozen():
    return calibration_freeze.freeze_calibration(calibration_fit.fit_all())


def test_frozen_profile_exposes_one_proper_rotation_per_family():
    fz = _frozen()
    mats = fz.orientation_matrix_by_family()
    assert set(mats) == set(fz.retained_families)
    for name, m in mats.items():
        a = np.asarray(m, dtype=float)
        assert a.shape == (3, 3)
        # orthonormal, det +1 (a proper rotation), about +Z
        assert np.allclose(a @ a.T, np.eye(3), atol=1e-9), name
        assert abs(float(np.linalg.det(a)) - 1.0) < 1e-9, name


def test_calibration_is_applied_not_identity():
    """The wired decode must differ from the identity/uncalibrated decode."""
    fz = _frozen()
    wired = geocode_forward.geocode(
        STONEHENGE_TRAINING_VECTOR, frozen_profile=fz, shell=3)
    uncalibrated = geocode_forward.geocode(
        STONEHENGE_TRAINING_VECTOR, frozen_profile=None, shell=3)

    def _by_family(g):
        return {c.family_name: (c.latitude_deg, c.longitude_deg)
                for c in g.candidates}

    w, u = _by_family(wired), _by_family(uncalibrated)
    shared = set(w) & set(u)
    assert shared, "expected overlapping families to compare"
    # at least one family's placement moves once the fitted rotation is applied
    moved = [name for name in shared
             if _haversine_km(w[name], u[name]) > 1.0]
    assert moved, ("the frozen calibration changed no placement — the fitted "
                   "orientation is not being applied (cosmetic calibration)")


def test_best_family_reproduces_anchor_only_to_its_fit_residual():
    """Honest bound: the fit is applied, but a single azimuth cannot place the
    training anchor on Stonehenge. Best family lands within its sealed residual
    (hundreds of km), and no family lands on a point-hit."""
    fit = calibration_fit.fit_all()
    fz = calibration_freeze.freeze_calibration(fit)
    g = geocode_forward.geocode(
        STONEHENGE_TRAINING_VECTOR, frozen_profile=fz, shell=3)

    dists = {c.family_name: _haversine_km(
        (c.latitude_deg, c.longitude_deg), STONEHENGE_LATLON)
        for c in g.candidates}
    best_family = min(dists, key=dists.get)
    best_km = dists[best_family]

    # The applied rotation brings the best family "near" (within ~1000 km),
    # consistent with its sealed angular residual — but NOT onto Stonehenge.
    # 1 deg of arc ~ 111 km; the best fit residual is several degrees.
    best_fit = min(fit.fits, key=lambda f: f.stonehenge_residual_rad)
    expected_km = math.degrees(best_fit.stonehenge_residual_rad) * 111.0
    assert best_km < expected_km + 200.0, (best_km, expected_km)
    assert best_km > 100.0, (
        "best family reproduced the training anchor to <100 km: a single "
        "azimuth should not achieve a point-hit on two anchors — check for an "
        "overfit / famous-place reward")

    # And it is rendered as an alias set, never a lone confident pin.
    assert g.result_type == "CANDIDATE_ALIAS_SET"
