"""P07 — geometry-to-gravity arithmetic firewall."""

from __future__ import annotations

import math

import pytest

import r7
from r7 import gravity as GV


# --- constants and identities ----------------------------------------

def test_joule_equivalent_mass():
    """1 J is 1.11e-17 kg. The whole refutation follows from this."""
    b = GV.EnergyBudget("1 joule", electromagnetic_j=1.0)
    assert b.equivalent_mass_kg == pytest.approx(1.113e-17, rel=1e-3)


def test_schwarzschild_radius_of_a_joule_is_absurdly_small():
    b = GV.EnergyBudget("1 joule", electromagnetic_j=1.0)
    assert b.schwarzschild_radius_m < 1e-43


def test_energy_budget_totals_every_channel():
    b = GV.EnergyBudget("x", electromagnetic_j=1.0,
                        elastic_strain_j=2.0, acoustic_j=3.0,
                        thermal_j=4.0, kinetic_j=5.0,
                        stored_electrical_j=6.0, optical_j=7.0)
    assert b.total_j == 28.0


def test_height_shift_matches_the_known_value():
    """g*h/c^2 at 1 m is 1.09e-16 — the R6 figure, reproduced."""
    assert GV.height_fractional_shift(1.0) == \
        pytest.approx(1.09e-16, rel=0.02)


def test_acceleration_requires_positive_distance():
    with pytest.raises(ValueError):
        GV.gravitational_acceleration(1.0, 0.0)
    with pytest.raises(ValueError):
        GV.potential_fractional_shift(1.0, -1.0)


def test_gap_is_infinite_for_zero_prediction():
    assert GV.orders_of_magnitude_gap(0.0, 1e-19) == math.inf


def test_gap_arithmetic():
    assert GV.orders_of_magnitude_gap(1e-30, 1e-20) == \
        pytest.approx(10.0)


# --- the verdicts -----------------------------------------------------

def test_every_configuration_is_refused_by_arithmetic():
    """The headline. Including the absurd upper bound."""
    rep = GV.full_assessment()
    assert rep["all_refused"]
    for name, row in rep["configurations"].items():
        assert row["status"] == "REFUSED_BY_ARITHMETIC", name


def test_absurd_upper_bound_is_still_refused():
    """Two megajoules -- far beyond anything buildable here."""
    v = GV.assess("ABSURD_UPPER_BOUND")
    assert v.status == "REFUSED_BY_ARITHMETIC"
    assert v.clock_gap_decades > 15


def test_one_millimetre_of_height_beats_the_whole_apparatus():
    """The comparison that makes the scale intuitive."""
    rep = GV.full_assessment()
    assert rep["ratio_1mm_lift_over_best_apparatus"] > 1e15


def test_gap_shrinks_with_energy_but_never_closes():
    a = GV.assess("HANDHELD_CRYSTAL")
    b = GV.assess("BENCH_COIL_DRIVE")
    c = GV.assess("ABSURD_UPPER_BOUND")
    assert a.clock_gap_decades > b.clock_gap_decades > c.clock_gap_decades
    assert c.clock_gap_decades > 6


def test_refusal_explains_the_integration_time():
    """Averaging goes as sqrt(t), so the note must say why patience
    cannot help."""
    v = GV.assess("BENCH_COIL_DRIVE")
    assert "integration" in v.note
    assert "unreachable" in v.note


def test_status_is_always_declared():
    for c in GV.CONFIGURATIONS:
        assert GV.assess(c).status in r7.GRAVITY_STATUSES


def test_unknown_configuration_rejected():
    with pytest.raises(ValueError):
        GV.assess("WARP_CORE")


def test_closer_distance_narrows_the_gap():
    far = GV.assess("ABSURD_UPPER_BOUND", distance_m=1.0)
    near = GV.assess("ABSURD_UPPER_BOUND", distance_m=0.001)
    assert near.clock_gap_decades < far.clock_gap_decades


def test_extreme_parameters_reach_below_floor_but_stay_newtonian():
    """An honest edge the first version of this test got wrong.

    At 1 mm from a 2 MJ energy the *acceleration* gap falls to a few
    decades, because 2 MJ has the equivalent mass of a dust grain and
    Newtonian attraction at 1 mm is not absurdly small. That is real
    physics and the module reports it. It is still ordinary Newtonian
    attraction of an equivalent mass, at an energy this programme
    cannot build or safely operate -- not metric engineering.
    """
    near = GV.assess("ABSURD_UPPER_BOUND", distance_m=0.001)
    assert near.status == "BELOW_SENSOR_FLOOR"
    assert near.acceleration_gap_decades < near.clock_gap_decades
    # the clock channel, which is the metric-relevant one, stays hopeless
    assert near.clock_gap_decades > 15


def test_realistic_configurations_stay_refused_even_at_1mm():
    """Nothing buildable here escapes, at any distance."""
    for c in ("HANDHELD_CRYSTAL", "BENCH_COIL_DRIVE",
              "HIGH_POWER_PULSE"):
        assert GV.assess(c, distance_m=0.001).status == \
            "REFUSED_BY_ARITHMETIC"


def test_using_the_best_instrument_makes_the_refusal_stronger():
    """Refuting against the world's best sensor, not ours."""
    strict = GV.assess("BENCH_COIL_DRIVE",
                       clock_sensor="OPTICAL_CLOCK_FRACTIONAL")
    lax = GV.assess("BENCH_COIL_DRIVE",
                    clock_sensor="OCXO_FRACTIONAL")
    assert strict.clock_gap_decades < lax.clock_gap_decades
    assert strict.status == "REFUSED_BY_ARITHMETIC"


# --- honesty about what the refusal does NOT say ---------------------

def test_report_says_relativity_is_still_testable_at_bench_scale():
    rep = GV.full_assessment()
    assert "does not say relativity is untestable" in \
        rep["what_this_does_not_say"]
    assert "measures Earth's field" in rep["what_this_does_not_say"]


def test_consequence_is_independent_of_the_source_corpus():
    rep = GV.full_assessment()
    assert "does not depend on the crystal" in rep["consequence"]


def test_conventional_effect_is_labelled_newtonian_not_metric():
    """If an effect ever were measurable it is ordinary attraction."""
    huge = GV.EnergyBudget("sun-like", electromagnetic_j=1e45)
    GV.CONFIGURATIONS["_TEST_HUGE"] = huge
    try:
        v = GV.assess("_TEST_HUGE", distance_m=1.0)
        assert v.status == "CONVENTIONAL_EFFECT_MEASURABLE"
        assert "Newtonian" in v.note
    finally:
        del GV.CONFIGURATIONS["_TEST_HUGE"]


def test_metric_actuation_is_refused():
    with pytest.raises(GV.GravityRefused) as e:
        GV.refuse_metric_actuation()
    assert "STORED_ENERGY_IS_SPACETIME_CURVATURE" in str(e.value)
    assert "not by policy" in str(e.value)


def test_sensor_floors_are_documented():
    for name, spec in GV.SENSOR_FLOORS.items():
        assert spec["value"] > 0
        assert spec["unit"]
        assert len(spec["note"]) > 20
