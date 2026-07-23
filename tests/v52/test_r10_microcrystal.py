"""P07 — 13 MHz quartz microcrystal resonator, BVD circuit model only.

The circuit's closed-form results (fs, fp, Q, fs < fp) are shown with
power; the over-claims it invites — an even overtone, a free-space
wavelength used inside quartz — are refused.
"""

from __future__ import annotations

import math

import pytest

from r10 import microcrystal as MC


# --- period and the free-space wavelength arithmetic --------------------

def test_period_at_13mhz():
    assert MC.period_ns() == pytest.approx(76.923076923, abs=1e-6)
    assert MC.period_seconds() == pytest.approx(1.0 / 13_000_000)


def test_freespace_wavelength_arithmetic():
    assert MC.LAMBDA0_M == pytest.approx(23.060958307692, abs=1e-9)
    assert MC.LAMBDA0_QUARTER_M == pytest.approx(5.765239576923, abs=1e-9)
    assert MC.LAMBDA0_QUARTER_M == pytest.approx(MC.LAMBDA0_M / 4.0)


def test_nonpositive_frequency_is_refused():
    with pytest.raises(MC.MicrocrystalError):
        MC.period_seconds(0)
    with pytest.raises(MC.MicrocrystalError):
        MC.freespace_wavelength_m(-1)


# --- the BVD circuit, with power ----------------------------------------

def test_series_resonance_matches_the_analytic_formula():
    """POWER: the computed fs matches 1/(2*pi*sqrt(Lm*Cm)) tightly."""
    lm_h, cm_f = 3.0e-2, 5.0e-15
    fs = MC.bvd_series_resonance_hz(lm_h, cm_f)
    analytic = 1.0 / (2.0 * math.pi * math.sqrt(lm_h * cm_f))
    assert fs == pytest.approx(analytic, rel=1e-12)


def test_recover_lm_round_trips_fs_exactly():
    """POWER: recover Lm from a target fs and Cm, feed it back, get fs."""
    cm_f = 5.0e-15
    fs_target = 13_000_000.0
    lm_h = MC.recover_lm_h(fs_target, cm_f)
    assert MC.bvd_series_resonance_hz(lm_h, cm_f) == pytest.approx(
        fs_target, rel=1e-9)


def test_parallel_resonance_is_above_series():
    fs = 13_000_000.0
    fp = MC.bvd_parallel_resonance_hz(fs, cm_f=5.0e-15, c0_f=3.0e-12)
    assert fp > fs
    # fp = fs*sqrt(1 + Cm/C0)
    assert fp == pytest.approx(fs * math.sqrt(1 + 5.0e-15 / 3.0e-12))


def test_quality_factor_two_equivalent_forms_agree():
    """Q = 2*pi*fs*Lm/Rm == 1/(2*pi*fs*Cm*Rm) on a consistent branch."""
    cm_f, rm_ohm, fs = 5.0e-15, 8.0, 13_000_000.0
    lm_h = MC.recover_lm_h(fs, cm_f)
    q1 = MC.bvd_quality_factor(fs, lm_h, rm_ohm)
    q2 = MC.quality_factor_from_cm(fs, cm_f, rm_ohm)
    assert q1 == pytest.approx(q2, rel=1e-9)


def test_bvd_refuses_nonpositive_parameters():
    with pytest.raises(MC.MicrocrystalError):
        MC.bvd_series_resonance_hz(0.0, 5.0e-15)
    with pytest.raises(MC.MicrocrystalError):
        MC.bvd_quality_factor(13e6, 1.0, 0.0)


# --- the round trip through the schema ----------------------------------

def test_from_bvd_is_self_consistent_and_ordered():
    """A full round trip: build from Lm, Cm, Rm, C0; fs, fp, Q are
    self-consistent and physically ordered (fs < fp)."""
    r = MC.Resonator.from_bvd("MC", lm_h=MC.recover_lm_h(13e6, 5e-15),
                              cm_f=5e-15, rm_ohm=8.0, c0_f=3e-12)
    assert r.fs == pytest.approx(13_000_000.0, rel=1e-9)
    assert r.fp > r.fs
    # Q recomputed from the stored branch agrees with the stored Q
    assert r.Q == pytest.approx(
        MC.quality_factor_from_cm(r.fs, r.Cm, r.Rm), rel=1e-9)


def test_the_13mhz_example_lands_on_target():
    r = MC.make_13mhz_resonator()
    assert r.fs == pytest.approx(13_000_000.0, rel=1e-9)
    assert r.fp > r.fs
    assert r.status == "MODEL_ONLY"


# --- the refusals -------------------------------------------------------

def test_even_overtone_is_refused():
    with pytest.raises(MC.MicrocrystalError):
        MC.Resonator("MC", overtone=2)
    with pytest.raises(MC.MicrocrystalError):
        MC.Resonator("MC", overtone=4)


def test_odd_overtones_are_accepted():
    for n in (1, 3, 5, 7):
        assert MC.Resonator("MC", overtone=n).overtone == n


def test_freespace_wavelength_in_quartz_is_refused():
    """The load-bearing refusal: lambda0 is not the length in quartz,
    even given index, mode, cut, temperature and direction."""
    with pytest.raises(MC.MicrocrystalError):
        MC.refuse_freespace_wavelength_in_quartz(
            refractive_index=1.54, mode="thickness_shear", cut="AT",
            temperature_c=25.0, propagation_direction="thickness")


# --- the Leeson phase-noise shape ---------------------------------------

def test_leeson_regions_are_ordered():
    model = MC.LeesonModel(flicker_corner_hz=1e3, leeson_corner_hz=1e5)
    assert model.region(100.0) is MC.NoiseRegion.FLICKER_FM
    assert model.region(1e4) is MC.NoiseRegion.THERMAL_FM
    assert model.region(1e6) is MC.NoiseRegion.NOISE_FLOOR
    assert model.slope_per_decade(100.0) == -3
    assert model.slope_per_decade(1e4) == -2
    assert model.slope_per_decade(1e6) == 0


def test_leeson_corner_is_half_bandwidth():
    assert MC.leeson_corner_hz(13e6, 100_000.0) == pytest.approx(65.0)


def test_leeson_refuses_bad_input():
    with pytest.raises(MC.MicrocrystalError):
        MC.LeesonModel(flicker_corner_hz=-1.0, leeson_corner_hz=1e5)
    model = MC.LeesonModel(flicker_corner_hz=1e3, leeson_corner_hz=1e5)
    with pytest.raises(MC.MicrocrystalError):
        model.region(0.0)


# --- the report ----------------------------------------------------------

def test_report_claims_no_measurement():
    r = MC.microcrystal_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["verdict"] == "RESONATOR_MODEL_ONLY"


def test_report_does_not_map_frequency_to_a_length_in_quartz():
    w = MC.microcrystal_report()["what_this_does_not_say"]
    assert "acoustic wavelength" in w and "free-space" in w
