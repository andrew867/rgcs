"""P12 — environmental signal logger: alignment, refusals, and power."""

from __future__ import annotations

import numpy as np
import pytest

from r10 import envlog as E


def _line(t, offset=0.0):
    """A simple ramp so linear interpolation is exact and checkable."""
    return t + offset


# --- alignment ----------------------------------------------------------

def test_align_resamples_onto_the_requested_grid():
    t = np.linspace(0.0, 10.0, 21)
    a = E.Stream("a", E.StreamKind.RF, t, _line(t), clock_offset_s=0.0)
    b = E.Stream("b", E.StreamKind.TEMPERATURE, t, _line(t, 5.0),
                 clock_offset_s=0.0)
    al = E.align([a, b], grid_hz=2.0)
    # step is 0.5 s
    assert np.allclose(np.diff(al.grid), 0.5)
    assert al.grid[0] == pytest.approx(0.0)
    assert al.grid[-1] <= 10.0 + 1e-9


def test_a_known_clock_offset_is_corrected():
    """A stream whose clock leads by 2 s is pulled back onto the grid."""
    t = np.linspace(0.0, 10.0, 101)
    # stream a is the reference; a ramp equal to reference-clock time
    a = E.Stream("a", E.StreamKind.RF, t, _line(t), clock_offset_s=0.0)
    # stream b's clock leads by 2 s: its timestamp 5 is really time 3.
    # its value equals its own-clock time, so after correction, at
    # reference time tau the value should read tau + 2.
    b = E.Stream("b", E.StreamKind.MAINS, t, _line(t), clock_offset_s=2.0)
    al = E.align([a, b], grid_hz=5.0)
    tau = al.grid
    assert np.allclose(al.aligned["a"], tau, atol=1e-9)
    assert np.allclose(al.aligned["b"], tau + 2.0, atol=1e-9)


def test_grid_is_the_overlap_intersection():
    ta = np.linspace(0.0, 8.0, 41)
    tb = np.linspace(3.0, 12.0, 46)
    a = E.Stream("a", E.StreamKind.RF, ta, _line(ta), clock_offset_s=0.0)
    b = E.Stream("b", E.StreamKind.OPTICAL, tb, _line(tb), clock_offset_s=0.0)
    al = E.align([a, b], grid_hz=4.0)
    assert al.overlap_start_s == pytest.approx(3.0)
    assert al.overlap_end_s == pytest.approx(8.0)
    assert al.grid[0] >= 3.0 - 1e-9
    assert al.grid[-1] <= 8.0 + 1e-9


# --- POWER: injected lag is recovered -----------------------------------

def test_injected_lag_is_recovered_within_one_grid_step():
    grid_hz = 100.0
    fs = grid_hz * 3.0
    t = np.arange(0.0, 4.0, 1.0 / fs)
    # a chirp: sharply autocorrelated, so the lag is unambiguous
    k = (grid_hz / 4.0 - 2.0) / 4.0
    base = np.sin(2.0 * np.pi * (2.0 * t + 0.5 * k * t * t))
    injected = 0.37
    a = E.Stream("a", E.StreamKind.RF, t, base, clock_offset_s=0.0)
    b = E.Stream("b", E.StreamKind.MAGNETIC, t + injected, base,
                 clock_offset_s=0.0)
    al = E.align([a, b], grid_hz)
    xc = E.cross_correlation(al.aligned["a"], al.aligned["b"])
    lag_samples, lag_s = E.lag_of_peak(xc, grid_hz)
    assert abs(lag_s - injected) <= 1.0 / grid_hz


def test_zero_lag_when_streams_are_identical():
    t = np.linspace(0.0, 5.0, 251)
    rng = np.random.default_rng(7)
    v = rng.standard_normal(t.size)
    a = E.Stream("a", E.StreamKind.RF, t, v, clock_offset_s=0.0)
    b = E.Stream("b", E.StreamKind.ACOUSTIC, t, v, clock_offset_s=0.0)
    al = E.align([a, b], grid_hz=50.0)
    xc = E.cross_correlation(al.aligned["a"], al.aligned["b"])
    lag_samples, _ = E.lag_of_peak(xc, 50.0)
    assert lag_samples == 0


def test_internal_demo_recovers_its_lag():
    d = E._sync_demo()
    assert d["within_one_step"]


# --- REFUSALS -----------------------------------------------------------

def test_correlating_an_unknown_offset_is_refused():
    t = np.linspace(0.0, 4.0, 41)
    a = E.Stream("a", E.StreamKind.RF, t, _line(t), clock_offset_s=0.0)
    b = E.Stream("b", E.StreamKind.OPERATOR, t, _line(t), clock_offset_s=None)
    with pytest.raises(E.EnvLogError):
        E.refuse_correlation_without_sync([a, b])


def test_align_refuses_an_unsynchronized_stream():
    t = np.linspace(0.0, 4.0, 41)
    a = E.Stream("a", E.StreamKind.RF, t, _line(t), clock_offset_s=0.0)
    b = E.Stream("b", E.StreamKind.DEVICE, t, _line(t), clock_offset_s=None)
    with pytest.raises(E.EnvLogError):
        E.align([a, b], grid_hz=5.0)


def test_corrected_timestamps_refuse_unknown_offset():
    t = np.linspace(0.0, 4.0, 41)
    s = E.Stream("s", E.StreamKind.OPERATOR, t, _line(t), clock_offset_s=None)
    assert not s.is_synchronized
    with pytest.raises(E.EnvLogError):
        s.corrected_timestamps()


def test_non_overlapping_streams_are_refused():
    ta = np.linspace(0.0, 4.0, 41)
    tb = np.linspace(10.0, 14.0, 41)
    a = E.Stream("a", E.StreamKind.RF, ta, _line(ta), clock_offset_s=0.0)
    b = E.Stream("b", E.StreamKind.MAINS, tb, _line(tb), clock_offset_s=0.0)
    with pytest.raises(E.EnvLogError):
        E.align([a, b], grid_hz=5.0)


def test_offset_that_destroys_overlap_is_refused():
    """Two streams that overlap on their own clocks but not after
    offset correction must not be aligned (no extrapolation)."""
    t = np.linspace(0.0, 4.0, 41)
    a = E.Stream("a", E.StreamKind.RF, t, _line(t), clock_offset_s=0.0)
    # b's clock leads by 100 s, so its corrected span is [-100, -96]
    b = E.Stream("b", E.StreamKind.MAGNETIC, t, _line(t), clock_offset_s=100.0)
    with pytest.raises(E.EnvLogError):
        E.align([a, b], grid_hz=5.0)


def test_cross_correlation_requires_equal_length():
    with pytest.raises(E.EnvLogError):
        E.cross_correlation(np.zeros(10), np.zeros(9))


def test_stream_rejects_nonmonotonic_timestamps():
    t = np.array([0.0, 1.0, 0.5, 2.0])
    with pytest.raises(E.EnvLogError):
        E.Stream("bad", E.StreamKind.RF, t, t, clock_offset_s=0.0)


def test_stream_rejects_mismatched_lengths():
    with pytest.raises(E.EnvLogError):
        E.Stream("bad", E.StreamKind.RF, np.arange(5.0), np.arange(4.0),
                 clock_offset_s=0.0)


# --- report -------------------------------------------------------------

def test_report_measures_nothing():
    r = E.envlog_report()
    assert r["measured_here"] == "nothing"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"


def test_report_names_the_firewall_and_what_it_does_not_say():
    r = E.envlog_report()
    assert "what_this_does_not_say" in r
    w = r["what_this_does_not_say"]
    assert "correlated" in w
    assert isinstance(r["the_firewalls"], list) and r["the_firewalls"]
