"""P05 — frozen phase-frame mathematics, exact, residuals shown."""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from r10 import phaseframes as P


# --- the frozen quantities are exact -----------------------------------

def test_4096_is_two_to_the_twelfth():
    assert P.FREQ_4096 == 2 ** 12


def test_20_48_is_exactly_4096_over_200():
    assert P.FREQ_20_48 == F(512, 25)
    assert float(P.FREQ_20_48) == 20.48


def test_the_periods_are_exact_dyadic_values():
    assert P.periods_are_exact()
    assert float(P.PERIOD_4096_S) * 1e6 == 244.140625
    assert float(P.PERIOD_20_48_S) * 1e3 == 48.828125


def test_q_is_exact():
    assert P.Q == F(925, 4096)
    assert float(P.Q) == 0.225830078125     # exact dyadic


# --- the ratio match is approximate, and says so -----------------------

def test_the_ratio_match_is_not_exact():
    r = P.ratio_residual()
    assert not r["are_equal"]
    assert r["verdict"] == "APPROXIMATE_NOT_EXACT"


def test_the_residual_is_computed_exactly():
    r = P.ratio_residual()
    assert r["residual_exact"] == str(F(4096, 925) - F(8300, 1876))
    assert r["residual_exact"] == "1649/433825"


def test_the_relative_residual_is_about_point_zero_eight_six_percent():
    r = P.ratio_residual()
    assert r["relative_residual_percent"] == pytest.approx(0.0858, abs=1e-3)


def test_calling_the_ratio_exact_is_refused():
    with pytest.raises(P.ExactnessError) as e:
        P.refuse_exact_ratio_claim()
    msg = str(e.value)
    assert "are not equal" in msg
    assert "1649/433825" in msg


# --- exact frame residuals ---------------------------------------------

def test_an_exact_multiple_has_zero_residual():
    r = P.frame_residual(4096, 20.48 if False else F(512, 25))
    assert r["exact_multiple"]
    assert r["residual_exact"] == "0"


def test_a_non_multiple_keeps_its_exact_residual():
    r = P.frame_residual(925, 4096)
    assert not r["exact_multiple"]
    assert F(r["residual_exact"]) != 0
    # residual is exact, not a rounded float
    assert F(r["residual_exact"]) == F(925, 4096) - round(F(925, 4096))


def test_zero_frame_refused():
    with pytest.raises(ValueError):
        P.frame_residual(100, 0)


# --- other frozen facts -------------------------------------------------

def test_reluctance_wheel_rpm():
    assert P.reluctance_wheel_rpm(200, 4096) == F(12288, 10)
    assert float(P.reluctance_wheel_rpm(200, 4096)) == 1228.8


def test_reluctance_wheel_refuses_bad_input():
    with pytest.raises(ValueError):
        P.reluctance_wheel_rpm(0, 4096)


def test_slate_24_fold_is_fifteen_degrees():
    assert P.slate_division_degrees(24) == 15


def test_925_root_three_is_labelled_inexact():
    r = P.nine_two_five_root_three()
    assert not r["is_exact"]
    assert r["value"] == pytest.approx(1602.147, abs=1e-3)
    assert "irrational" in r["note"]


# --- claim discipline --------------------------------------------------

def test_report_disclaims_privilege():
    r = P.phaseframe_report()
    w = r["what_this_does_not_say"]
    assert "physically\nprivileged" in w or "physically privileged" in w
    assert "coincidence at that level" in w
    assert r["measured_here"] == "nothing"
