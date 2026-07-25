"""R15 P05 — the low-cost orientation solver.

POWER: a planted orientation is recovered from cheap synthetic observations
within the error budget. Negatives/refusals: the point-group-32 symmetry
alias set is not unique, the 180-degree optic-axis ambiguity stays explicit,
handedness is not inferred from achiral data, noise beyond the budget is
refused, and a no-XRD certificate is capped. Plus determinism and the
schema-valid error budget.
"""

from __future__ import annotations

import json
import os

import numpy as np
import pytest

from r15 import claims as C
from r15 import orientation as O

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _planted(handedness=O.Handedness.RIGHT):
    from r13.magroot import rotation_about_axis
    c = rotation_about_axis((0.2, -0.5, 0.84), 0.6) @ np.array([0.0, 0.0, 1.0])
    return O.OrientationState(tuple(float(x) for x in c), 37.0, handedness)


# --- POWER: a planted orientation is recovered --------------------------

def test_planted_orientation_is_recovered_within_budget():
    planted = _planted()
    budget = O.build_error_budget()
    obs = O.forward_observation(planted, noise_deg=0.2, seed=7)
    sol = O.solve_orientation(obs, budget)
    # the recovered c-axis matches the planted one as a line (sign-free)
    err = O.line_angle(sol.recovered.c_axis, planted.c_axis)
    assert err <= sol.expanded_uncertainty_deg
    assert sol.within_budget is True
    assert sol.residual_deg <= sol.expanded_uncertainty_deg


def test_recovered_tilt_matches_planted_tilt():
    planted = _planted()
    obs = O.forward_observation(planted, noise_deg=0.1, seed=1)
    sol = O.solve_orientation(obs)
    planted_tilt = O.angle_between(planted.c_axis, (0.0, 0.0, 1.0))
    planted_tilt = min(planted_tilt, 180.0 - planted_tilt)
    assert abs(sol.recovered_tilt_deg - planted_tilt) <= sol.expanded_uncertainty_deg


def test_noiseless_recovery_is_essentially_exact():
    planted = _planted()
    obs = O.forward_observation(planted, noise_deg=0.0, seed=0)
    sol = O.solve_orientation(obs)
    assert O.line_angle(sol.recovered.c_axis, planted.c_axis) < 1e-6
    assert sol.residual_deg < 1e-6


# --- the 180-degree optic-axis ambiguity stays explicit -----------------

def test_optic_axis_is_a_line_both_signs_in_alias_set():
    planted = _planted()
    rays = O.distinct_c_axes(planted)
    assert len(rays) == 2  # +c and -c
    a, b = np.array(rays[0]), np.array(rays[1])
    # the two rays are antiparallel: the same undirected optic-axis line
    assert O.line_angle(a, b) < 1e-6
    assert O.angle_between(a, b) > 179.0


def test_refuse_optic_axis_polarity_always_raises():
    with pytest.raises(O.OrientationError, match="undirected line"):
        O.refuse_optic_axis_polarity()


def test_aliased_orientations_give_identical_observations():
    """The symmetry aliases are indistinguishable on the cheap bench: the
    180-degree (and full 32) ambiguity is real, not a labelling quirk."""
    planted = _planted()
    base = O.forward_observation(planted, noise_deg=0.0, seed=0)
    base_set = sorted(tuple(round(x, 9) for x in n) for n in base.facet_normals)
    for ali in O.alias_set(planted):
        obs = O.forward_observation(ali, noise_deg=0.0, seed=0)
        this_set = sorted(tuple(round(x, 9) for x in n)
                          for n in obs.facet_normals)
        assert this_set == base_set
        assert abs(obs.optic_axis_tilt_deg - base.optic_axis_tilt_deg) < 1e-9


# --- the symmetry alias set is not a unique orientation -----------------

def test_alias_set_has_six_members():
    planted = _planted()
    aliases = O.alias_set(planted)
    assert len(aliases) == 6  # the six proper rotations of point group 32


def test_refuse_orientation_as_unique_raises():
    planted = _planted()
    with pytest.raises(O.OrientationError, match="alias set"):
        O.refuse_orientation_as_unique(planted)


def test_solution_reports_the_alias_size():
    planted = _planted()
    sol = O.solve_orientation(O.forward_observation(planted, seed=0))
    assert sol.alias_size == 6
    assert not sol.recovered.handedness is O.Handedness.RIGHT  # never claimed


# --- handedness is not inferred from the c-axis alone -------------------

def test_handedness_is_never_recovered_regardless_of_plant():
    for hand in (O.Handedness.RIGHT, O.Handedness.LEFT):
        planted = _planted(hand)
        sol = O.solve_orientation(O.forward_observation(planted, seed=2))
        assert sol.recovered.handedness is O.Handedness.UNDETERMINED


def test_enantiomorphs_are_indistinguishable_on_the_bench():
    right = _planted(O.Handedness.RIGHT)
    left = O.OrientationState(right.c_axis, right.a_azimuth_deg,
                              O.Handedness.LEFT)
    o_r = O.forward_observation(right, noise_deg=0.0, seed=0)
    o_l = O.forward_observation(left, noise_deg=0.0, seed=0)
    assert o_r.facet_normals == o_l.facet_normals
    assert o_r.extinction_azimuth_deg == o_l.extinction_azimuth_deg


def test_refuse_handedness_from_geometry_always_raises():
    with pytest.raises(O.OrientationError, match="handedness"):
        O.refuse_handedness_from_geometry()


def test_certificate_does_not_determine_handedness():
    cert = O.generate_orientation_certificate(_planted())
    assert cert["handedness_determined"] is False
    assert cert["recovered"]["handedness"] == "UNDETERMINED"


# --- noise beyond the budget is refused ---------------------------------

def test_noise_beyond_budget_is_refused():
    planted = _planted()
    obs = O.forward_observation(planted, noise_deg=12.0, seed=4)
    with pytest.raises(O.OrientationError, match="exceeds the expanded"):
        O.solve_orientation(obs)


def test_noise_within_budget_is_accepted():
    planted = _planted()
    obs = O.forward_observation(planted, noise_deg=0.5, seed=4)
    sol = O.solve_orientation(obs)
    assert sol.within_budget is True


# --- no-XRD certificates are capped -------------------------------------

def test_certificate_confidence_is_capped_without_xrd():
    cert = O.generate_orientation_certificate(
        _planted(), requested_confidence=O.ConfidenceLevel.XRD_CONFIRMED)
    assert cert["confidence"] == O.NO_XRD_CONFIDENCE_CAP.name
    assert cert["confidence"] == "PRESUMPTIVE"
    assert cert["confidence_capped_by_no_xrd"] is True
    assert cert["unique_orientation_claimed"] is False


def test_cap_confidence_without_xrd_function():
    assert O.cap_confidence_without_xrd(
        O.ConfidenceLevel.XRD_REPLICATED) is O.NO_XRD_CONFIDENCE_CAP
    assert O.cap_confidence_without_xrd(
        O.ConfidenceLevel.SCREENING) is O.ConfidenceLevel.SCREENING


def test_refuse_confirmed_certificate_without_xrd_raises():
    with pytest.raises(O.OrientationError, match="requires"):
        O.refuse_certificate_confirmed_without_xrd(
            O.ConfidenceLevel.XRD_CONFIRMED)


def test_additional_evidence_names_the_upgrades():
    upgrades = O.additional_evidence_to_upgrade()
    assert len(upgrades) >= 3
    ambiguities = {u["ambiguity"] for u in upgrades}
    assert O.SYMMETRY_ALIAS_AMBIGUITY in ambiguities
    assert O.OPTIC_AXIS_LINE_AMBIGUITY in ambiguities
    assert O.HANDEDNESS_AMBIGUITY in ambiguities
    assert all(u["status"] == "PREREGISTERED_NOT_RUN" for u in upgrades)


# --- error budget conforms to the schema --------------------------------

def test_error_budget_conforms_to_schema():
    import jsonschema
    schema_path = os.path.join(_REPO, "r15", "schemas",
                               "error_budget.schema.json")
    with open(schema_path) as fh:
        schema = json.load(fh)
    budget = O.build_error_budget()
    jsonschema.validate(budget, schema)
    assert budget["combination_method"] == "root_sum_of_squares"
    assert budget["combined_uncertainty"] > 0.0


# --- determinism --------------------------------------------------------

def test_forward_observation_is_deterministic():
    planted = _planted()
    o1 = O.forward_observation(planted, noise_deg=0.7, seed=11)
    o2 = O.forward_observation(planted, noise_deg=0.7, seed=11)
    assert o1.facet_normals == o2.facet_normals
    assert o1.extinction_azimuth_deg == o2.extinction_azimuth_deg
    assert o1.optic_axis_tilt_deg == o2.optic_axis_tilt_deg


def test_different_seeds_give_different_noise():
    planted = _planted()
    o1 = O.forward_observation(planted, noise_deg=0.7, seed=11)
    o2 = O.forward_observation(planted, noise_deg=0.7, seed=12)
    assert o1.facet_normals != o2.facet_normals


def test_solve_is_deterministic():
    planted = _planted()
    obs = O.forward_observation(planted, noise_deg=0.3, seed=9)
    s1 = O.solve_orientation(obs)
    s2 = O.solve_orientation(obs)
    assert s1.recovered.c_axis == s2.recovered.c_axis
    assert s1.residual_deg == s2.residual_deg


# --- real acquisition is unavailable ------------------------------------

def test_real_acquisition_mode_is_refused():
    with pytest.raises(O.OrientationError, match="REAL"):
        O.forward_observation(_planted(), mode=O.AcquisitionMode.REAL)


# --- governance: nothing is measured ------------------------------------

def test_report_claims_nothing_measured():
    r = O.orientation_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["recovery_claim_class"] == "MODEL_PREDICTION"
    assert r["observation_claim_class"] == "SYNTHETIC_OBSERVATION"
    assert r["verdict"] == O.VERDICT


def test_claim_classes_are_software_reachable_only():
    # the recovered orientation and the observations are software classes;
    # neither is a measurement class
    rec = C.ClaimClass(O.RECOVERY_CLAIM_CLASS)
    obs = C.ClaimClass(O.OBSERVATION_CLAIM_CLASS)
    assert rec in C.SOFTWARE_CLASSES
    assert obs in C.SOFTWARE_CLASSES
    assert rec not in C.MEASUREMENT_CLASSES
    assert obs not in C.MEASUREMENT_CLASSES


def test_certificate_evidence_is_capped_below_physical():
    cert = O.generate_orientation_certificate(_planted())
    # no instrument/calibration/specimen binding -> evidence cannot reach E4
    assert cert["evidence_level"] in ("E1", "E2", "E3")
    assert cert["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
