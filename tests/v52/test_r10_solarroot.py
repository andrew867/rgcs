"""P04 — solar-emission-centroid root, nulls, and power."""

from __future__ import annotations

import numpy as np
import pytest

from r10 import solarroot as S


def test_heliographic_to_unit_is_unit():
    v = S.heliographic_to_unit(20, 45)
    assert np.isclose(np.linalg.norm(v), 1.0)


def test_centroid_of_a_tight_cluster_points_at_it():
    rng = np.random.default_rng(1)
    pts = np.array([0, 0, 1.0]) + rng.standard_normal((30, 3)) / 10
    pts = pts / np.linalg.norm(pts, axis=1, keepdims=True)
    c = S.emission_centroid(pts)
    assert np.dot(c["centroid"], [0, 0, 1]) > 0.95
    assert c["resultant_length"] > 0.9


def test_cancelling_vectors_have_no_centroid():
    with pytest.raises(S.SolarRootError):
        S.emission_centroid(np.array([[1, 0, 0], [-1, 0, 0.0]]))


def test_negative_weights_refused():
    with pytest.raises(S.SolarRootError):
        S.emission_centroid(np.array([[0, 0, 1.0]]), np.array([-1.0]))


def test_roll_from_parallel_axis_is_undetermined():
    r = S.solar_root_direction(np.array([[0, 0, 1.0]] * 3), [0, 0, 1])
    assert not r["determined"]


def test_roll_from_independent_axis_is_determined():
    rng = np.random.default_rng(2)
    pts = np.array([0, 0, 1.0]) + rng.standard_normal((20, 3)) / 10
    pts = pts / np.linalg.norm(pts, axis=1, keepdims=True)
    r = S.solar_root_direction(pts, [1, 0, 0])
    assert r["determined"]


def test_the_engine_recovers_a_planted_centroid():
    """Power: a real cluster must be found."""
    pw = S.planted_centroid_power([0, 0, 1])
    assert pw["has_power"]
    assert pw["median_error_deg"] < 10


def test_shuffling_equal_weights_is_a_no_op():
    """Control: with equal weights, weight-shuffling changes nothing."""
    rng = np.random.default_rng(3)
    v = np.array([0, 0, 1.0]) + rng.standard_normal((20, 3)) / 8
    v = v / np.linalg.norm(v, axis=1, keepdims=True)
    n = S.shuffled_event_null(v, np.ones(20), trials=300)
    assert n["p_value"] > 0.5
    assert n["verdict"] == "WEIGHTING_NOT_INFORMATIVE"


def test_real_catalog_is_declared_blocked_not_faked():
    s = S.REAL_CATALOG_STATUS
    assert s["status"] == "BLOCKED_NO_DATA_SOURCE"
    assert "no real catalog result is reported" in s["not_faked"]


def test_report_is_root_candidate_only():
    r = S.solar_root_report()
    assert r["verdict"] == "ROOT_CANDIDATE_ONLY"
    assert r["measured_here"] == "nothing"
