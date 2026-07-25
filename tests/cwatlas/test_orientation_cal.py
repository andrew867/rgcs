"""P30 — Kabsch calibration recovers a planted rotation; degeneracy refused."""

from __future__ import annotations

import numpy as np
import pytest

from cwatlas import orientation_cal as OC
from cwatlas.claims import ClaimClass
from cwatlas.earth_frame import get_profile


def _synthetic_control(seed: int = 7, n: int = 12) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(scale=1.0e6, size=(n, 3))


# --- POWER: a planted rotation is recovered -----------------------------------

def test_recovers_planted_orientation_profile_rotation():
    profile = get_profile("IERS-NOMINAL@2.0.0")
    r_true = profile.rotation_matrix()
    source = _synthetic_control()
    target = (r_true @ source.T).T  # planted: rotate the control cloud

    cal = OC.calibrate_orientation(source, target, profile)
    r_hat = cal.as_matrix()

    assert np.allclose(r_hat, r_true, atol=1e-9)
    assert cal.rmsd_train == pytest.approx(0.0, abs=1e-6)
    # Provenance: which profile + version was used is recorded.
    assert cal.profile_key == "IERS-NOMINAL@2.0.0"
    assert cal.profile_version == "2.0.0"
    assert cal.n_train == source.shape[0]


def test_recovered_rotation_is_a_proper_rotation():
    profile = get_profile("IERS-NOMINAL@1.0.0")
    source = _synthetic_control(seed=11)
    target = (profile.rotation_matrix() @ source.T).T
    r = OC.solve_rotation(source, target)
    assert np.linalg.det(r) == pytest.approx(1.0, abs=1e-9)
    assert np.allclose(r @ r.T, np.eye(3), atol=1e-9)


# --- Freeze, then score holdouts without retuning -----------------------------

def test_frozen_calibration_scores_holdout_without_retuning():
    profile = get_profile("IERS-NOMINAL@2.0.0")
    r_true = profile.rotation_matrix()
    train = _synthetic_control(seed=1, n=8)
    hold = _synthetic_control(seed=2, n=8)
    cal = OC.calibrate_orientation(train, (r_true @ train.T).T, profile)
    rmsd = OC.score_holdout(cal, hold, (r_true @ hold.T).T)
    assert rmsd == pytest.approx(0.0, abs=1e-6)


# --- Negative: degenerate / underdetermined configs are refused ---------------

def test_too_few_points_is_refused():
    with pytest.raises(OC.CalibrationError):
        OC.solve_rotation([[0, 0, 0], [1, 0, 0]], [[0, 0, 0], [1, 0, 0]])


def test_collinear_points_are_refused():
    line = np.array([[t, 2 * t, 3 * t] for t in range(5)], dtype=float)
    with pytest.raises(OC.CalibrationError):
        OC.solve_rotation(line, line)


def test_coplanar_points_are_refused():
    # All z = 0: a plane, rank 2 -> ambiguous full rotation.
    plane = np.array([[1, 0, 0], [0, 1, 0], [1, 1, 0], [2, 3, 0]], dtype=float)
    with pytest.raises(OC.CalibrationError):
        OC.solve_rotation(plane, plane)


def test_mismatched_shapes_refused():
    with pytest.raises(OC.CalibrationError):
        OC.solve_rotation(_synthetic_control(n=4), _synthetic_control(n=5))


def test_calibrate_requires_orientation_profile():
    src = _synthetic_control()
    with pytest.raises(OC.CalibrationError):
        OC.calibrate_orientation(src, src, "not-a-profile")


# --- Determinism + report -----------------------------------------------------

def test_solve_is_deterministic():
    profile = get_profile("IERS-NOMINAL@2.0.0")
    source = _synthetic_control(seed=3)
    target = (profile.rotation_matrix() @ source.T).T
    r1 = OC.solve_rotation(source, target)
    r2 = OC.solve_rotation(source, target)
    assert np.array_equal(r1, r2)


def test_report_claims_nothing_physical():
    r = OC.orientation_cal_report()
    assert r["phase_id"] == "P30"
    assert r["claim_class"] == ClaimClass.CANONICAL_ROUND_TRIP.value
    assert r["known_destination_used_to_choose_transform"] is False
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"


def test_import_surface():
    from cwatlas import orientation_cal  # noqa: F401
