"""P09 — SI time/frequency standards, modelled from primary sources."""

from __future__ import annotations

from fractions import Fraction

import numpy as np
import pytest

from r10 import timebase as T


# --- the SI second is an exact definition, not a measurement ------------

def test_cesium_hyperfine_is_the_exact_defining_integer():
    assert T.CS_HYPERFINE_HZ == 9_192_631_770
    assert isinstance(T.CS_HYPERFINE_HZ, int)


def test_the_si_second_is_treated_as_a_definition_with_zero_uncertainty():
    d = T.si_second_definition()
    assert d["cs_hyperfine_hz"] == 9_192_631_770
    assert d["is_exact_integer"]
    assert d["uncertainty"] == 0
    assert d["uncertainty_kind"] == "ZERO_BY_DEFINITION"
    assert d["measured_here"] == "nothing"
    # the canonical Timebase carries the definition, uncertainty exactly 0
    assert T.CESIUM_SI_SECOND.uncertainty == Fraction(0)
    assert T.CESIUM_SI_SECOND.measured_frequency is None
    assert T.CESIUM_SI_SECOND.source_type is T.SourceType.DEFINITION


# --- vacuum wavelength is exact arithmetic ------------------------------

def test_vacuum_wavelength_of_cesium_line_is_about_3p26_cm():
    lam = T.vacuum_wavelength_m(T.CS_HYPERFINE_HZ)
    # c / f = 299792458 / 9192631770 ~ 0.032612 m
    assert lam == pytest.approx(0.0326, abs=5e-4)


def test_vacuum_wavelength_matches_c_over_f_exactly():
    lam = T.vacuum_wavelength_m(T.CS_HYPERFINE_HZ)
    assert lam == pytest.approx(T.C_M_PER_S / T.CS_HYPERFINE_HZ, rel=1e-12)


def test_nonpositive_frequency_has_no_wavelength():
    with pytest.raises(T.TimebaseError):
        T.vacuum_wavelength_m(0)


# --- POWER: the Allan estimator recovers the white-FM slope -------------

def test_allan_deviation_recovers_tau_minus_half_on_white_fm():
    """White frequency noise: sigma_y(tau) proportional to tau^{-1/2}.

    Plant iid Gaussian fractional-frequency samples (white FM) and check
    the log-log slope of sigma_y(tau) vs tau is close to -0.5. If the
    estimator had no power, the slope would not track the theory.
    """
    rng = np.random.default_rng(20260723)
    y = rng.normal(0.0, 1e-11, size=8192)        # white FM
    tau0 = 1.0
    factors = [1, 2, 4, 8, 16, 32, 64]
    sweep = T.allan_deviation_sweep(y, tau0, factors)

    log_tau = np.log(np.asarray(sweep["tau"]))
    log_adev = np.log(np.asarray(sweep["adev"]))
    slope = np.polyfit(log_tau, log_adev, 1)[0]
    assert slope == pytest.approx(-0.5, abs=0.06)


def test_allan_variance_halves_scaling_is_monotone_decreasing():
    """For white FM the ADEV strictly falls as tau grows."""
    rng = np.random.default_rng(1)
    y = rng.normal(0.0, 1.0, size=4096)
    adevs = [T.overlapping_allan_deviation(y, 1.0, m) for m in (1, 2, 4, 8)]
    assert all(a > b for a, b in zip(adevs, adevs[1:]))


def test_allan_deviation_refuses_a_too_short_series():
    with pytest.raises(T.TimebaseError):
        T.overlapping_allan_deviation([0.1, 0.2, 0.3], tau0=1.0, m=5)


# --- REFUSALS -----------------------------------------------------------

def test_medium_wavelength_without_an_index_is_refused():
    with pytest.raises(T.TimebaseError):
        T.refuse_medium_wavelength_without_index(T.CS_HYPERFINE_HZ)


def test_reading_a_nominal_frequency_as_measured_is_refused():
    with pytest.raises(T.TimebaseError):
        T.refuse_nominal_as_measured(T.CESIUM_FOUNTAIN_MODEL)
    # even the definition, which has a nominal value, is not a measurement
    with pytest.raises(T.TimebaseError):
        T.refuse_nominal_as_measured(T.CESIUM_SI_SECOND)


def test_a_timebase_with_a_measured_value_but_wrong_status_is_rejected():
    with pytest.raises(T.TimebaseError):
        T.Timebase(
            timebase_id="BAD",
            source_type=T.SourceType.RUBIDIUM,
            nominal_frequency=Fraction(10_000_000),
            measured_frequency=Fraction(10_000_001),   # set...
            uncertainty=None,
            phase_noise=None,
            Allan_deviation=None,
            temperature=None,
            aging=None,
            wavelength_model="vacuum",
            medium="vacuum",
            primary_source_reference="x",
            calibration_date=None,
            status="NOMINAL",                           # ...but not MEASURED
        )


# --- the report is honest -----------------------------------------------

def test_report_is_model_only_and_blocked_on_live_data():
    r = T.timebase_report()
    assert r["measured_here"] == "nothing"
    assert r["verdict"] == "STANDARDS_MODEL_ONLY"
    assert r["evidence_class"] == "CONVENTIONAL_LITERATURE"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["live_measured_data_status"] == "BLOCKED_NO_DATA_SOURCE"


def test_report_lists_real_primary_sources():
    r = T.timebase_report()
    srcs = r["primary_sources"]
    assert isinstance(srcs, list) and len(srcs) >= 3
    joined = " ".join(srcs)
    assert "BIPM" in joined
    assert "9 192 631 770" in joined
    assert "NIST" in joined


def test_report_wavelength_matches_the_function():
    r = T.timebase_report()
    assert r["cesium_vacuum_wavelength_m"] == pytest.approx(
        T.vacuum_wavelength_m(T.CS_HYPERFINE_HZ), rel=1e-12)


def test_report_says_what_it_does_not_say():
    r = T.timebase_report()
    w = r["what_this_does_not_say"]
    assert "nominal" in w and "not a measurement" in w
    assert "BLOCKED_NO_DATA_SOURCE" in w
