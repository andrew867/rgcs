"""R13 — the IGRF root as an orientation reference: attitude recovered up
to the field-axis ambiguity (POWER), the field-value alias locus, the
epoch drift, and the source/uniqueness refusals."""

from __future__ import annotations

import math

import numpy as np
import pytest

from r13 import magroot as M


# --- orientation from a single field vector, up to the axis ambiguity ---

def test_orientation_recovers_a_planted_attitude_direction():
    """POWER: the recovered attitude reproduces the measured field vector."""
    ref = M.field_direction_at(40.0, -105.0, 2020.0)
    R_true = M.rotation_about_axis((0.3, -0.7, 0.6), 0.9)
    measured = R_true.T @ ref            # field as seen in the body frame
    out = M.orientation_from_field(ref, measured)
    R = np.array(out["rotation"])
    # the recovered attitude maps the measured vector back onto the reference
    assert np.allclose(R @ measured, ref, atol=1e-9)
    assert out["residual_max_abs"] < 1e-9


def test_orientation_is_only_fixed_up_to_a_turn_about_the_field_axis():
    """The undetermined degree of freedom is real: adding any turn about
    the field axis leaves the measured vector unchanged."""
    ref = M.field_direction_at(-20.0, 60.0, 2020.0)
    R_true = M.rotation_about_axis((1.0, 0.2, -0.4), 0.5)
    measured = R_true.T @ ref
    out = M.orientation_from_field(ref, measured)
    R = np.array(out["rotation"])
    assert out["undetermined_dof"] == 1
    assert out["ambiguity"] == "ROTATION_ABOUT_FIELD_AXIS_UNDETERMINED"
    # compose the recovered attitude with a spin about the reference axis:
    # it is a different attitude that produces the identical measurement
    for angle in (0.3, 1.7, -2.0):
        spin = M.rotation_about_axis(ref, angle)
        R2 = spin @ R
        assert np.allclose(R2 @ measured, ref, atol=1e-9)
        assert not np.allclose(R2, R, atol=1e-6)


def test_shortest_arc_rotation_maps_one_direction_to_another():
    a = np.array([1.0, 0.0, 0.0])
    b = np.array([0.0, 1.0, 0.0])
    R = M.shortest_arc_rotation(a, b)
    assert np.allclose(R @ a, b, atol=1e-12)
    # a proper rotation: orthogonal, determinant +1
    assert np.allclose(R @ R.T, np.eye(3), atol=1e-12)
    assert abs(float(np.linalg.det(R)) - 1.0) < 1e-12


def test_refuse_full_attitude_from_single_vector_always_raises():
    with pytest.raises(M.MagRootError, match="three"):
        M.refuse_full_attitude_from_single_vector()


# --- a field value is consistent with a locus, not a point --------------

def test_root_alias_set_has_more_than_one_member():
    target = M.axial_total_intensity(35.0)
    aliases = M.root_alias_set(target)
    assert len(aliases) > 1


def test_every_alias_reproduces_the_same_field_intensity():
    """A whole set of locations shares one intensity -- the point of the
    alias: a magnetic condition does not decode a location."""
    target = M.axial_total_intensity(52.0)
    aliases = M.root_alias_set(target, n_longitudes=8)
    assert len(aliases) > 1
    for cand in aliases:
        recovered = M.axial_total_intensity(cand["lat_deg"])
        assert recovered == pytest.approx(target, rel=1e-9)
    # the set spans more than one longitude (longitude is unconstrained)
    lons = {round(c["lon_deg"], 6) for c in aliases}
    assert len(lons) > 1


def test_root_alias_set_refuses_too_few_longitudes():
    with pytest.raises(M.MagRootError):
        M.root_alias_set(M.axial_total_intensity(10.0), n_longitudes=1)


def test_root_alias_set_refuses_an_unachievable_intensity():
    with pytest.raises(M.MagRootError):
        M.root_alias_set(10.0 * M.AXIAL_MOMENT_NT)


def test_refuse_root_as_unique_location_always_raises():
    with pytest.raises(M.MagRootError, match="LOCUS"):
        M.refuse_root_as_unique_location(30000.0)


# --- the field changes with epoch (secular variation) -------------------

def test_field_changes_with_epoch():
    out = M.field_changes_with_epoch(40.0, -105.0, 2020.0, 2026.0)
    assert out["field_moved"] is True
    assert out["vector_difference_nT"] > 0.0


def test_field_vector_differs_between_two_epochs():
    a = M.field_vector_at(12.0, 77.0, 2020.0)
    b = M.field_vector_at(12.0, 77.0, 2026.0)
    assert not np.allclose(a, b)


# --- matching a field value is not authenticating a source --------------

def test_refuse_field_match_as_source_always_raises():
    with pytest.raises(M.MagRootError, match="authenticate"):
        M.refuse_field_match_as_source(30000.0, 30000.0)


# --- the report ---------------------------------------------------------

def test_report_carries_verdict_and_claim_discipline():
    r = M.magroot_report()
    assert r["verdict"] == "IGRF_ROOT_AND_ORIENTATION_ALIAS_LIMITED"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "ANALYTIC_MODEL"
    assert r["alias_set_has_many_members"] is True
    assert r["field_changes_with_epoch"] is True
    assert r["orientation"]["undetermined_dof"] == 1
    assert "what_this_does_not_say" in r
