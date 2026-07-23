"""P17 — sky-event / collective-observation correlation.

A correlation is a coincidence rate, never an identification. These tests
exercise the coincidence tests, the fixed refusal, the null+power
discipline, the multiplicity penalty, and the report's guarantees.
"""

from __future__ import annotations

import pytest

from r10 import skycorr as SC
from r10.skycorr import CatalogEvent, EventKind, ObsWindow


def _win(start=1000.0, end=1010.0, az=None, el=None):
    return ObsWindow(start, end, az, el)


def _evt(eid="E", t=1005.0, kind=EventKind.SATELLITE, az=None, el=None):
    return CatalogEvent(eid, t, kind, az, el)


# --- temporal match ----------------------------------------------------

def test_temporal_match_inside_window():
    assert SC.temporal_match(_win(), _evt(t=1005.0), tol_s=1.0)


def test_temporal_match_within_tolerance_of_edge():
    # 3 s past the window end, tolerance 5 -> matches; tolerance 1 -> not
    assert SC.temporal_match(_win(), _evt(t=1013.0), tol_s=5.0)
    assert not SC.temporal_match(_win(), _evt(t=1013.0), tol_s=1.0)


def test_temporal_match_outside_tolerance():
    assert not SC.temporal_match(_win(), _evt(t=2000.0), tol_s=10.0)


def test_negative_tolerance_is_refused():
    with pytest.raises(SC.SkyCorrError):
        SC.temporal_match(_win(), _evt(), tol_s=-1.0)


# --- angular match -----------------------------------------------------

def test_angular_match_is_none_without_directions():
    # temporal-only data: no angular constraint applies
    assert SC.angular_match(_win(), _evt(), ang_tol_deg=5.0) is None


def test_angular_match_within_and_outside_tolerance():
    w = _win(az=100.0, el=30.0)
    near = _evt(az=102.0, el=31.0)
    far = _evt(az=200.0, el=10.0)
    assert SC.angular_match(w, near, ang_tol_deg=5.0) is True
    assert SC.angular_match(w, far, ang_tol_deg=5.0) is False


def test_angular_separation_is_symmetric_and_zero_on_identity():
    assert SC.angular_separation_deg(50, 20, 50, 20) == pytest.approx(0.0)
    a = SC.angular_separation_deg(10, 5, 40, 25)
    b = SC.angular_separation_deg(40, 25, 10, 5)
    assert a == pytest.approx(b)


# --- correlate returns matches but never identifies --------------------

def test_correlate_finds_matches_but_stays_unidentified():
    windows = [_win(start=0, end=10), _win(start=100, end=110)]
    catalog = [_evt("A", t=5.0), _evt("B", t=105.0), _evt("C", t=9999.0)]
    r = SC.correlate(windows, catalog, tol_s=2.0)
    assert r["match_count"] == 2                     # A and B, not C
    assert r["verdict"] == "UNIDENTIFIED_CORRELATION_ONLY"
    assert r["identity_claimed"] is False
    assert all(m.identity_claimed is False for m in r["matches"])


def test_correlate_respects_angular_constraint_when_present():
    # same time, but one event is far off in direction
    windows = [_win(start=0, end=10, az=100.0, el=30.0)]
    catalog = [_evt("near", t=5.0, az=101.0, el=30.0),
               _evt("far", t=5.0, az=250.0, el=5.0)]
    r = SC.correlate(windows, catalog, tol_s=2.0, ang_tol_deg=5.0)
    ids = {m.event_id for m in r["matches"]}
    assert ids == {"near"}


def test_refuse_identity_from_correlation_raises():
    windows = [_win(start=0, end=10)]
    catalog = [_evt("A", t=5.0)]
    r = SC.correlate(windows, catalog, tol_s=2.0)
    with pytest.raises(SC.SkyCorrError):
        SC.refuse_identity_from_correlation(r["matches"][0])
    with pytest.raises(SC.SkyCorrError):
        SC.refuse_identity_from_correlation({"event_id": "A"})


# --- NULL (control) ----------------------------------------------------

def test_null_random_times_give_p_not_small():
    # many short windows scattered over a long span, and a catalog of
    # events at unrelated times -> observed count is typical of chance.
    windows = [_win(start=float(i * 1000), end=float(i * 1000 + 5))
               for i in range(8)]
    rng = __import__("numpy").random.default_rng(1)
    catalog = [_evt(f"E{i}", t=float(rng.uniform(0, 8000)))
               for i in range(20)]
    r = SC.time_shuffled_null(windows, catalog, tol_s=5.0, trials=1500)
    assert r["p_value"] > 0.05
    assert r["exceeds_null"] is False
    assert r["verdict"] == "UNIDENTIFIED_CORRELATION_ONLY"


# --- POWER -------------------------------------------------------------

def test_power_planted_coincidences_give_small_p():
    # windows scattered over a long span; plant an event dead-centre in
    # EVERY window so the observed match count sits far above the null.
    windows = [_win(start=float(i * 1000), end=float(i * 1000 + 5))
               for i in range(8)]
    catalog = [_evt(f"P{i}", t=float(i * 1000 + 2.5)) for i in range(8)]
    r = SC.time_shuffled_null(windows, catalog, tol_s=1.0, trials=1500)
    assert r["observed_match_count"] == 8
    assert r["observed_match_count"] > r["null_mean"]
    assert r["p_value"] < 0.05
    assert r["exceeds_null"] is True


def test_null_requires_windows_and_events():
    with pytest.raises(SC.SkyCorrError):
        SC.time_shuffled_null([], [_evt()], tol_s=1.0)
    with pytest.raises(SC.SkyCorrError):
        SC.time_shuffled_null([_win()], [], tol_s=1.0)


# --- multiplicity ------------------------------------------------------

def test_multiplicity_correction_penalizes_wide_search():
    r = SC.multiplicity_correct(0.01, n_events_searched=20)
    assert r["corrected_p"] == pytest.approx(0.20)
    assert r["survives_at_0_05"] is False
    survivor = SC.multiplicity_correct(0.001, n_events_searched=10)
    assert survivor["corrected_p"] == pytest.approx(0.01)
    assert survivor["survives_at_0_05"] is True


def test_multiplicity_clamps_and_validates():
    assert SC.multiplicity_correct(0.5, 100)["corrected_p"] == 1.0
    with pytest.raises(SC.SkyCorrError):
        SC.multiplicity_correct(1.5, 1)
    with pytest.raises(SC.SkyCorrError):
        SC.multiplicity_correct(0.1, 0)


# --- consistency with skytrack -----------------------------------------

def test_kinematic_context_does_not_upgrade_identity():
    k = SC.Kinematics(angular_span_deg=40.0, duration_s=9.0, steady=True,
                      silent=True, constant_speed=True,
                      brighter_than_stars=True)
    r = SC.kinematic_context(k)
    assert r["skytrack_verdict"] == "UNIDENTIFIED_OBSERVATION"
    assert r["correlation_verdict"] == "UNIDENTIFIED_CORRELATION_ONLY"
    assert r["correlation_upgrades_identity"] is False


# --- input validation --------------------------------------------------

def test_backwards_window_is_refused():
    with pytest.raises(SC.SkyCorrError):
        ObsWindow(100.0, 50.0)


# --- report ------------------------------------------------------------

def test_report_measures_nothing_and_holds_no_observation():
    r = SC.skycorr_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["verdict"] == "UNIDENTIFIED_CORRELATION_ONLY"
    assert r["holds_specific_observation"] is False
    assert "identif" in r["what_this_does_not_say"].lower()
