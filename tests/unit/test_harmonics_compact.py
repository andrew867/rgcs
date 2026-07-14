"""Unit tests: rgcs_core.harmonics and rgcs_core.compact_modes
(RGCS-M.8..M.17)."""

from __future__ import annotations

import math

import pytest

from rgcs_core.uncertainty import UncertainValue, default_wave_speed
from rgcs_core.harmonics import (axial_half_wave, ladder_length_mm,
                                 harmonic_classification)
from rgcs_core.compact_modes import (parity_index_set, kappa_chi_hz,
                                     compact_mode_spectrum)


def test_axial_half_wave_is_uncertain_value():
    f = axial_half_wave(154.052734375)
    assert isinstance(f, UncertainValue)
    assert f.u_rel == 0.05           # default u_v (RGCS-M.10)
    assert f.sigma == pytest.approx(f.mean * 0.05)


def test_ladder_length_uncertainty_propagates():
    ln = ladder_length_mm(5)
    assert isinstance(ln, UncertainValue)
    assert ln.u_rel == 0.05          # u(L_N)/L_N = u_v (RGCS-M.11)


def test_harmonic_classification_unambiguous_at_zero_uncertainty():
    hc = harmonic_classification(110.0, wave_speed=6310.0)
    assert hc["harmonic_class_set"] == [7]
    assert not hc["ambiguous"]


def test_harmonic_classification_116mm_is_ambiguous():
    hc = harmonic_classification(116.0)
    assert hc["harmonic_class_set"] == [6, 7]     # RGCS-M.12 golden example
    assert hc["ambiguous"]


def test_parity_odd_never_contains_zero():
    for n_max in (1, 5, 12):
        assert 0 not in parity_index_set("odd", n_max)
        assert all(n % 2 == 1 for n in parity_index_set("odd", n_max))


def test_parity_even_zero_mode_flag():
    assert 0 in parity_index_set("even", 6, include_zero_mode=True)
    assert 0 not in parity_index_set("even", 6, include_zero_mode=False)
    # 'all' respects the flag too.
    assert 0 in parity_index_set("all", 6, include_zero_mode=True)
    assert 0 not in parity_index_set("all", 6, include_zero_mode=False)


def test_zero_mode_excluded_when_base_frequency_zero():
    s = compact_mode_spectrum(0.0, kappa=UncertainValue(1000.0), n_max=6,
                              parity="even", include_zero_mode=True)
    assert all(r["n"] != 0 for r in s["modes"])   # RGCS-M.17 rule 3
    assert not s["zero_mode_present"]


def test_zero_mode_listed_when_base_frequency_positive():
    s = compact_mode_spectrum(500.0, kappa=UncertainValue(1000.0), n_max=6,
                              parity="even", include_zero_mode=True)
    row0 = s["modes"][0]
    assert row0["n"] == 0
    assert row0["frequency"]["mean"] == pytest.approx(500.0)
    s2 = compact_mode_spectrum(500.0, kappa=UncertainValue(1000.0), n_max=6,
                               parity="even", include_zero_mode=False)
    assert all(r["n"] != 0 for r in s2["modes"])  # strict LT template


def test_compact_spectrum_reports_kappa_not_pair():
    s = compact_mode_spectrum(0.0, v_chi=default_wave_speed(),
                              compact_radius_mm=100.0, n_max=3)
    assert "kappa_chi_hz" in s
    assert "identifiability_note" in s
    with pytest.raises(ValueError):
        compact_mode_spectrum(0.0, kappa=UncertainValue(1.0),
                              v_chi=6310.0, compact_radius_mm=100.0)


def test_compact_spectrum_uncertainty_limits():
    # With f_b = 0, u(f_n)/f_n -> u_v (RGCS-M.15).
    s = compact_mode_spectrum(0.0, v_chi=default_wave_speed(),
                              compact_radius_mm=100.0, n_max=4)
    for r in s["modes"]:
        assert r["frequency"]["u_rel"] == pytest.approx(0.05, rel=1e-9)
    # With very large f_b, the compact term barely matters and u -> 0.
    s2 = compact_mode_spectrum(1e6, v_chi=default_wave_speed(),
                               compact_radius_mm=100.0, n_max=1)
    assert s2["modes"][0]["frequency"]["u_rel"] < 0.01


def test_kappa_chi_value():
    k = kappa_chi_hz(6310.0, 100.0)
    assert k.mean == pytest.approx(6310.0 / (2 * math.pi * 0.1))
