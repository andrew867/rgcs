"""P03 — root reference and the differential clock link.

R7's priority experiment. The tests that matter are the ones showing
the claim ceiling is a floor, not a patience problem.
"""

from __future__ import annotations

import math

import pytest

import r7
from r7 import clocklink as CL


def _root(**kw) -> CL.RootReference:
    base = dict(source_id="R0", root_class="OCXO", f0_hz=10e6,
                phi0_rad=0.0, t0_s=0.0, time_scale="TAI",
                adev_1s=1e-12, flicker_floor=1e-13, holdover_s=3600.0)
    base.update(kw)
    return CL.RootReference(**base)


# --- root reference ---------------------------------------------------

def test_root_requires_declared_class_and_scale():
    with pytest.raises(ValueError):
        _root(root_class="MAGIC")
    with pytest.raises(ValueError):
        _root(time_scale="WALLCLOCK")


def test_root_rejects_nonpositive_frequency():
    with pytest.raises(ValueError):
        _root(f0_hz=0.0)


def test_flicker_floor_cannot_beat_short_term():
    with pytest.raises(ValueError):
        _root(adev_1s=1e-14, flicker_floor=1e-12)


def test_4096_is_derived_not_fundamental():
    """core/01: 4096 Hz may be derived from the root and need not be
    the physical root oscillator."""
    r = _root(f0_hz=4096.0 * 2441)
    d = r.derive(4096.0)
    assert d["integer_ratio"]
    assert d["divisor"] == 2441
    assert "not itself a root" in d["note"]


def test_non_integer_ratio_makes_the_synthesizer_part_of_the_authority():
    d = _root(f0_hz=10e6).derive(4096.0)
    assert not d["integer_ratio"]
    assert "phase authority" in d["note"]


def test_no_source_is_declared_fundamental():
    roots = CL.candidate_roots()
    assert len(roots) >= 8
    assert set(roots) <= set(r7.ROOT_CLASSES) | {"GPSDO"}


def test_root_selection_is_by_requirement_and_budget():
    cheap = CL.select_root(1e-13, budget_usd=1000)
    assert cheap["selected"] == "OCXO"
    rich = CL.select_root(1e-15, budget_usd=1e9)
    assert rich["selected"] in ("CAESIUM", "HYDROGEN_MASER", "OPTICAL")


def test_impossible_requirement_returns_no_viable_root():
    out = CL.select_root(1e-25)
    assert out["selected"] is None
    assert out["status"] == "NO_VIABLE_ROOT"


# --- Allan deviation --------------------------------------------------

def test_adev_model_averages_then_hits_the_floor():
    a = CL.adev_model(1e-12, 1e-13, 1.0)
    b = CL.adev_model(1e-12, 1e-13, 100.0)
    c = CL.adev_model(1e-12, 1e-13, 1e9)
    assert a == pytest.approx(1e-12)
    assert b == pytest.approx(1e-13)      # 1e-12/10 = 1e-13, at floor
    assert c == pytest.approx(1e-13)      # floor, not lower


def test_adev_model_rejects_nonpositive_tau():
    with pytest.raises(ValueError):
        CL.adev_model(1e-12, 1e-13, 0.0)


def test_overlapping_adev_recovers_white_fm_scaling():
    """The estimator must reproduce the 1/sqrt(tau) law it will later
    be used to check hardware against."""
    y = CL.simulate_frequency_series(1e-12, 4000, 1.0, seed=42)
    a1 = CL.overlapping_adev(y, 1.0, 1)
    a16 = CL.overlapping_adev(y, 1.0, 16)
    # white FM: adev falls as 1/sqrt(m); allow generous estimator noise
    assert a16 == pytest.approx(a1 / 4.0, rel=0.4)


def test_overlapping_adev_rejects_oversized_averaging_factor():
    y = CL.simulate_frequency_series(1e-12, 50, 1.0, seed=1)
    with pytest.raises(ValueError):
        CL.overlapping_adev(y, 1.0, 40)


def test_simulation_is_reproducible():
    a = CL.simulate_frequency_series(1e-12, 100, 1.0, seed=7)
    b = CL.simulate_frequency_series(1e-12, 100, 1.0, seed=7)
    assert a == b


# --- the claim ceiling ------------------------------------------------

def test_one_metre_target_matches_the_known_shift():
    assert CL.height_fractional_shift(1.0) == \
        pytest.approx(1.09e-16, rel=0.02)


def test_consumer_quartz_cannot_resolve_a_metre_ever():
    """The headline. Not slow -- impossible."""
    for osc in ("QUARTZ_XO", "TCXO", "OCXO"):
        r = CL.height_resolution(osc)
        assert not r.resolvable
        assert r.status == "UNRESOLVABLE_AT_ANY_INTEGRATION_TIME"
        assert r.tau_required_s is None


def test_the_refusal_names_the_floor_not_impatience():
    r = CL.height_resolution("OCXO")
    assert "never with this hardware" in r.note
    assert "flicker floor" in r.note


def test_optical_on_fibre_resolves_a_metre_quickly():
    r = CL.height_resolution("OPTICAL", link="FIBRE_STABILIZED")
    assert r.resolvable
    assert r.tau_required_s < 60.0


def test_optical_on_coax_is_link_limited_and_fails():
    """Buying a better clock without a better link buys nothing."""
    r = CL.height_resolution("OPTICAL", link="COAX_SHORT")
    assert not r.resolvable
    assert CL.limiter("OPTICAL", "COAX_SHORT") == "LINK_LIMITED"


def test_ocxo_is_oscillator_limited_on_good_links():
    for lk in ("COAX_SHORT", "FIBRE_STABILIZED", "GPS_COMMON_VIEW"):
        assert CL.limiter("OCXO", lk) == "OSCILLATOR_LIMITED"


def test_even_an_ocxo_is_link_limited_on_a_bad_link():
    """The bottleneck is a property of the pairing, not the clock.

    An undisciplined wireless link at 1e-11 dominates even a modest
    OCXO, and a long coax is comparable to it. Asserting "the OCXO is
    always oscillator-limited" would have been wrong.
    """
    assert CL.limiter("OCXO", "WIRELESS_UNDISCIPLINED") == \
        "LINK_LIMITED"
    assert CL.limiter("OCXO", "COAX_LONG") == "COMPARABLE_CONTRIBUTIONS"


def test_bottleneck_moves_between_regimes():
    rep = CL.ceiling_report()
    assert rep["link_limited_pairings"]
    assert "buys nothing" in rep["bottleneck_note"]


def test_ceiling_report_lists_quartz_as_unresolvable():
    rep = CL.ceiling_report()
    assert set(rep["consumer_quartz_unresolvable"]) == \
        {"QUARTZ_XO", "TCXO", "OCXO"}


def test_ceiling_states_what_the_experiment_still_delivers():
    rep = CL.ceiling_report()
    delivers = rep["what_the_experiment_still_delivers"]
    assert len(delivers) >= 5
    assert any("instrument floor" in d for d in delivers)
    assert "no amount of modelling substitutes" in rep["why_run_it_anyway"]


def test_taller_target_is_easier():
    near = CL.height_resolution("CAESIUM", target_height_m=1.0)
    far = CL.height_resolution("CAESIUM", target_height_m=10_000.0)
    assert far.target_fractional > near.target_fractional


def test_height_claim_is_refused_for_weak_hardware():
    with pytest.raises(CL.ClockRefused) as e:
        CL.refuse_height_claim("OCXO", 1.0)
    assert "cannot resolve" in str(e.value)


def test_unknown_oscillator_or_link_rejected():
    with pytest.raises(ValueError):
        CL.height_resolution("PULSAR")
    with pytest.raises(ValueError):
        CL.height_resolution("OCXO", link="CARRIER_PIGEON")


# --- configurations ---------------------------------------------------

def test_all_nine_configurations_declared():
    assert len(CL.CONFIGURATIONS) == 9
    assert CL.CONFIGURATIONS[0] == "COMMON_SOURCE_SPLIT"
    assert "SHAM_INSERTION" in CL.CONFIGURATIONS


def test_cheapest_configuration_comes_first():
    """The instrument-floor baseline is the one that must run first."""
    assert CL.CONFIGURATIONS[0] == "COMMON_SOURCE_SPLIT"
    assert CL.CONFIGURATIONS[1] == "ONE_SYNTHESIZER_TWO_OUTPUTS"


def test_transfer_links_are_documented():
    for name, spec in CL.TRANSFER_LINKS.items():
        assert spec["frac_uncertainty"] > 0
        assert len(spec["note"]) > 10
