"""P29 — real-time mode tracker: tracking, avoided-crossing branch, refusals."""

from __future__ import annotations

import numpy as np
import pytest

from r15 import mode_tracker as M


def test_tracks_a_planted_drifting_mode():
    tracker = M.ModeTracker(search_hz=60.0)
    controls = np.linspace(0.0, 1.0, 20)
    for x in controls:
        true_f = 1000.0 + 200.0 * x        # the mode drifts with control
        freqs, amp = M.synthetic_spectrum(true_f, fmin=900.0, fmax=1300.0,
                                          seed=1)
        # predict from the last lock (adiabatic); seed with true start
        predicted = tracker.track[-1].frequency if tracker.track else true_f
        pt = tracker.step(x, freqs, amp, predicted)
    traj = np.asarray(tracker.trajectory())
    expected = 1000.0 + 200.0 * controls
    assert tracker.locked_fraction() > 0.9
    assert np.max(np.abs(traj - expected)) < 20.0


def test_avoided_crossing_branches_never_touch():
    x = np.linspace(-5.0, 5.0, 201)
    g = 3.0
    lower, upper = M.avoided_crossing_branches(x, lambda v: v, lambda v: -v, g)
    gap = np.min(upper - lower)
    assert gap == pytest.approx(2 * abs(g), rel=1e-6)   # minimum gap = 2|g|


def test_lock_lost_when_peak_leaves_window():
    tracker = M.ModeTracker(search_hz=10.0, quality_floor=0.25)
    # peak is 500 Hz away from the prediction -> outside the 10 Hz window
    freqs, amp = M.synthetic_spectrum(1500.0, fmin=900.0, fmax=2000.0, seed=2)
    pt = tracker.step(0.0, freqs, amp, predicted=1000.0)
    assert pt.status is M.TrackStatus.LOCK_LOST


def test_branch_hop_and_lock_loss_are_refused():
    with pytest.raises(M.ModeTrackerError):
        M.refuse_branch_hop_as_new_mode()
    with pytest.raises(M.ModeTrackerError):
        M.refuse_lock_loss_as_signal()


def test_determinism():
    a = M.synthetic_spectrum(1000.0, fmin=900.0, fmax=1100.0, seed=5)
    b = M.synthetic_spectrum(1000.0, fmin=900.0, fmax=1100.0, seed=5)
    assert np.array_equal(a[1], b[1])


def test_report_claims_nothing_measured():
    r = M.mode_tracker_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "SYNTHETIC_OBSERVATION"
