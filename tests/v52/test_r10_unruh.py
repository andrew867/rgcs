"""P18 — Unruh temperature, Rindler geometry, and the scale refusal.

The numeric tests are pinned against digits stated independently of
the implementation (2.47e20 m/s^2 for one kelvin, 0.36 mm for the
horizon at that acceleration), so a wrong constant, a dropped 2*pi, or
an h-for-hbar substitution fails them. The structural tests are pinned
against invariants (d*a = c^2, linearity, hyperbolic worldline) that a
sign error or a cosh/sinh swap breaks.
"""

from __future__ import annotations

import math

import pytest

from r10 import unruh as U


# --- constants are the stated ones -------------------------------------

def test_constants_match_the_exact_si_definitions():
    """A transcription error in any of these silently rescales every
    result in the module."""
    assert U.C_M_PER_S == 299_792_458.0
    assert U.PLANCK_J_S == 6.626_070_15e-34
    assert U.BOLTZMANN_J_PER_K == 1.380_649e-23
    assert U.ELEMENTARY_CHARGE_C == 1.602_176_634e-19
    assert U.STANDARD_GRAVITY_M_PER_S2 == 9.806_65


def test_hbar_is_h_over_two_pi_not_h():
    assert U.HBAR_J_S == pytest.approx(1.054_571_817e-34, rel=1e-9)
    assert U.HBAR_J_S != U.PLANCK_J_S


def test_radiation_constant_matches_the_literature_value():
    """a = 4 sigma / c = 7.5657e-16 J m^-3 K^-4."""
    assert U.RADIATION_CONSTANT_J_PER_M3_K4 == pytest.approx(
        7.5657e-16, rel=1e-4)


# --- the Unruh relation -------------------------------------------------

def test_unruh_coefficient_is_about_four_times_ten_to_the_minus_21():
    """hbar / (2 pi c k_B). Dropping the 2*pi makes this 2.55e-20 and
    fails; using h instead of hbar makes it 2.55e-20 and fails."""
    assert U.UNRUH_COEFFICIENT_K_PER_M_PER_S2 == pytest.approx(
        4.055e-21, rel=1e-3)


def test_one_kelvin_needs_about_2_5e20_metres_per_second_squared():
    """The headline number, pinned to digits stated independently of
    the implementation."""
    a = U.acceleration_for_temperature_m_per_s2(1.0)
    assert a == pytest.approx(2.466e20, rel=1e-3)
    assert 2.4e20 < a < 2.5e20


def test_a_millikelvin_needs_about_2_5e17():
    a = U.acceleration_for_temperature_m_per_s2(1e-3)
    assert a == pytest.approx(2.466e17, rel=1e-3)


def test_temperature_is_linear_in_acceleration():
    """Fails for any nonlinear or offset implementation."""
    assert U.unruh_temperature_k(0.0) == 0.0
    base = U.unruh_temperature_k(1e20)
    assert U.unruh_temperature_k(2e20) == pytest.approx(2 * base)
    assert U.unruh_temperature_k(1e10) == pytest.approx(base / 1e10)


def test_temperature_and_acceleration_are_exact_inverses():
    for t in (1e-6, 1e-3, 1.0, 1e6):
        a = U.acceleration_for_temperature_m_per_s2(t)
        assert U.unruh_temperature_k(a) == pytest.approx(t, rel=1e-12)


def test_earth_gravity_gives_about_four_times_ten_to_the_minus_20_kelvin():
    """An independently quotable check: 1 g is ~4e-20 K."""
    assert U.unruh_temperature_k(U.STANDARD_GRAVITY_M_PER_S2) == \
        pytest.approx(3.977e-20, rel=1e-3)


def test_negative_inputs_are_refused():
    with pytest.raises(ValueError):
        U.unruh_temperature_k(-1.0)
    with pytest.raises(ValueError):
        U.acceleration_for_temperature_m_per_s2(-1.0)


# --- Rindler geometry ---------------------------------------------------

def test_horizon_distance_times_acceleration_is_c_squared():
    """The invariant. A factor of 2 or a c-for-c^2 error breaks it."""
    for a in (1.0, 9.80665, 1e6, 2.466e20):
        d = U.rindler_horizon_distance_m(a)
        assert d * a == pytest.approx(U.C_M_PER_S ** 2, rel=1e-12)


def test_horizon_at_one_kelvin_is_about_a_third_of_a_millimetre():
    """A stated, checkable consequence: c^2/a at 2.466e20 m/s^2."""
    a = U.acceleration_for_temperature_m_per_s2(1.0)
    d = U.rindler_horizon_distance_m(a)
    assert d == pytest.approx(3.644e-4, rel=1e-3)
    assert 1e-4 < d < 1e-3


def test_horizon_at_earth_gravity_is_about_a_light_year():
    """9.17e15 m, i.e. slightly under one light year. This is the
    conventional figure and fails if c^2/a is mis-implemented."""
    d = U.rindler_horizon_distance_m(U.STANDARD_GRAVITY_M_PER_S2)
    assert d == pytest.approx(9.17e15, rel=1e-2)


def test_an_unaccelerated_observer_has_no_horizon():
    with pytest.raises(ValueError):
        U.rindler_horizon_distance_m(0.0)


def test_worldline_starts_on_the_horizon_distance_at_rest():
    t, x = U.rindler_worldline(0.0, 1e20)
    assert t == 0.0
    assert x == pytest.approx(U.rindler_horizon_distance_m(1e20))


def test_worldline_is_a_hyperbola_with_invariant_interval():
    """x^2 - (ct)^2 = (c^2/a)^2 for all proper times. Fails if cosh
    and sinh are swapped, or if a sign is wrong."""
    a = 1e18
    d = U.rindler_horizon_distance_m(a)
    for tau in (0.0, 1e-11, 5e-11, -3e-11):
        t, x = U.rindler_worldline(tau, a)
        assert x ** 2 - (U.C_M_PER_S * t) ** 2 == pytest.approx(
            d ** 2, rel=1e-9)


def test_worldline_never_exceeds_the_speed_of_light():
    a = 1e18
    prev_t, prev_x = U.rindler_worldline(0.0, a)
    for tau in [i * 1e-11 for i in range(1, 20)]:
        t, x = U.rindler_worldline(tau, a)
        v = (x - prev_x) / (t - prev_t)
        assert 0 < v < U.C_M_PER_S
        prev_t, prev_x = t, x


def test_rapidity_grows_linearly_in_proper_time():
    a = 1e18
    assert U.rapidity(0.0, a) == 0.0
    assert U.rapidity(2e-11, a) == pytest.approx(
        2 * U.rapidity(1e-11, a))


def test_characteristic_time_at_one_kelvin_is_picoseconds():
    a = U.acceleration_for_temperature_m_per_s2(1.0)
    assert U.characteristic_proper_time_s(a) == pytest.approx(
        1.216e-12, rel=1e-3)


# --- how a large acceleration is actually obtained ---------------------

def test_plane_wave_field_from_intensity():
    """E = sqrt(2I/(eps0 c)). At 1e18 W/m^2 this is ~2.7e10 V/m."""
    assert U.field_from_intensity_v_per_m(1e18) == pytest.approx(
        2.744e10, rel=1e-3)
    assert U.field_from_intensity_v_per_m(0.0) == 0.0


def test_field_scales_as_the_square_root_of_intensity():
    lo = U.field_from_intensity_v_per_m(1e20)
    hi = U.field_from_intensity_v_per_m(4e20)
    assert hi == pytest.approx(2 * lo)


def test_electron_acceleration_in_a_one_volt_per_metre_field():
    """e/m = 1.759e11 C/kg, the classical specific charge."""
    assert U.electron_acceleration_in_field_m_per_s2(1.0) == \
        pytest.approx(1.7588e11, rel=1e-4)


def test_record_laser_gives_about_1e26_metres_per_second_squared():
    """Computed from the published intensity, not asserted."""
    a = U.record_laser_electron_acceleration_m_per_s2()
    assert a == pytest.approx(1.60e26, rel=1e-2)
    assert 1e26 < a < 1e27


def test_record_laser_unruh_temperature_is_of_order_a_million_kelvin():
    """The honest complication: this one is NOT absurd."""
    t = U.unruh_temperature_k(
        U.record_laser_electron_acceleration_m_per_s2())
    assert 1e5 < t < 1e7


# --- the scale table ---------------------------------------------------

def test_every_scale_row_carries_a_source():
    rows = U.acceleration_scale_table()
    assert rows
    for r in rows:
        assert r.source.strip()


def test_a_scale_row_without_a_source_is_refused():
    """An unsourced number in a comparison table is an invented one."""
    with pytest.raises(ValueError):
        U.AccelerationScale("mystery", 1e10, "BULK_MECHANICAL", "  ")


def test_a_scale_row_with_an_unknown_kind_is_refused():
    with pytest.raises(ValueError):
        U.AccelerationScale("mystery", 1e10, "HANDWAVING", "a source")


def test_requirement_rows_agree_with_the_inverse_function():
    """The table must not drift from the formula it compares against."""
    rows = {r.label: r for r in U.acceleration_scale_table()}
    assert rows["REQUIRED for T = 1 K"].unruh_temperature_k == \
        pytest.approx(1.0, rel=1e-12)
    assert rows["REQUIRED for T = 1 mK"].unruh_temperature_k == \
        pytest.approx(1e-3, rel=1e-12)


def test_every_bulk_mechanical_row_is_below_a_picokelvin():
    """The bulk verdict, stated as an assertion. Fails the moment any
    rotating or mechanical apparatus reaches even 1e-12 K."""
    for r in U.acceleration_scale_table():
        if r.kind == "BULK_MECHANICAL":
            assert r.unruh_temperature_k < 1e-12


def test_every_bulk_row_falls_short_of_one_kelvin_by_over_1e13():
    need = U.acceleration_for_temperature_m_per_s2(1.0)
    for r in U.acceleration_scale_table():
        if r.kind == "BULK_MECHANICAL":
            assert need / r.acceleration_m_per_s2 > 1e13


def test_single_charge_rows_beat_every_bulk_row_by_orders_of_magnitude():
    bulk = max(r.acceleration_m_per_s2
               for r in U.acceleration_scale_table()
               if r.kind == "BULK_MECHANICAL")
    charge = min(r.acceleration_m_per_s2
                 for r in U.acceleration_scale_table()
                 if r.kind == "SINGLE_CHARGE")
    assert charge / bulk > 1e15


def test_scale_verdict_keeps_the_two_cases_apart():
    """Running them together would misrepresent both."""
    v = U.scale_verdict()
    assert v["bulk_verdict"] == "HOPELESS_BY_FOURTEEN_ORDERS_OF_MAGNITUDE"
    assert v["single_charge_verdict"] == \
        "NOT_HOPELESS_AS_A_DETECTION_TARGET"
    assert v["bulk_mechanical_shortfall"] > 1e14
    assert v["single_charge_temperature_k"] > 1e5


def test_scale_verdict_numbers_are_the_computed_ones():
    v = U.scale_verdict()
    assert v["acceleration_for_1_k"] == pytest.approx(2.466e20, rel=1e-3)
    assert v["rindler_horizon_at_1_k_m"] == pytest.approx(
        3.644e-4, rel=1e-3)
    assert v["bulk_mechanical_temperature_k"] == pytest.approx(
        4.055e-15, rel=1e-3)


# --- the energy-source refusal -----------------------------------------

def test_the_driving_field_dwarfs_the_bath_it_induces():
    """The quantitative core of the refusal, at the most favourable
    laboratory conditions that exist."""
    b = U.unruh_energy_budget()
    assert b["drive_to_bath_ratio"] > 1e9
    assert b["driving_field_energy_density_j_per_m3"] > \
        b["unruh_bath_energy_density_j_per_m3"]


def test_thermal_energy_density_follows_the_fourth_power():
    """Fails for any power other than four."""
    u1 = U.thermal_energy_density_j_per_m3(100.0)
    u2 = U.thermal_energy_density_j_per_m3(200.0)
    assert u2 / u1 == pytest.approx(16.0)
    assert U.thermal_energy_density_j_per_m3(0.0) == 0.0


def test_bath_energy_density_at_one_kelvin_is_the_blackbody_value():
    assert U.thermal_energy_density_j_per_m3(1.0) == pytest.approx(
        7.5657e-16, rel=1e-4)


def test_unruh_as_an_energy_source_is_refused_unconditionally():
    with pytest.raises(U.UnruhClaimRefused) as e:
        U.refuse_unruh_as_energy_source()
    msg = str(e.value)
    assert "SCALE" in msg and "BUDGET" in msg and "FRAME" in msg


def test_no_arguments_make_the_energy_source_claim_permitted():
    """A conditional refusal is not a refusal."""
    for args, kwargs in (((1e30,), {}),
                         ((), {"permitted": True}),
                         ((), {"acceleration": 1e26, "override": True})):
        with pytest.raises(U.UnruhClaimRefused):
            U.refuse_unruh_as_energy_source(*args, **kwargs)


def test_the_horizon_is_refused_as_a_place():
    with pytest.raises(U.UnruhClaimRefused) as e:
        U.refuse_horizon_as_a_place()
    assert "observer-dependent" in str(e.value)


# --- claim hygiene ------------------------------------------------------

def test_verdict_disclaims_observation_and_measurement():
    v = U.scale_verdict()
    assert v["measured_here"] == "nothing"
    assert "has not been directly detected" in v["what_this_does_not_say"]
    assert "quartz resonator" in v["what_this_does_not_say"]


def test_verdict_names_its_sources():
    v = U.scale_verdict()
    joined = " ".join(v["sources"])
    assert "Unruh" in joined and "1976" in joined


def test_budget_states_frame_dependence():
    b = U.unruh_energy_budget()
    assert "Minkowski vacuum" in b["frame_dependence"]
    assert b["measured_here"] == "nothing"
