"""A03 — exact N=7 geometry and the one-seventh phase identity."""

from __future__ import annotations

from fractions import Fraction

import pytest

from r11 import n7geom as G


# --- THE IDENTITY, proved symbolically ---------------------------------

def test_the_identity_is_exact_for_n7():
    """f * 2L/v = 1/7 turn EXACTLY -- Fraction, not float."""
    turns = G.round_trip_phase_turns(G.V_PROXY_M_S, G.F_KEY_HZ, 7)
    assert turns == Fraction(1, 7)
    assert isinstance(turns, Fraction)
    assert G.round_trip_phase_degrees(7) == Fraction(360, 7)


@pytest.mark.parametrize("n", range(1, 25))
@pytest.mark.parametrize("f", [8, 4096, 32768])
@pytest.mark.parametrize("v", [Fraction(6310), Fraction(3000),
                               Fraction(12345, 7)])
def test_the_identity_is_independent_of_v_and_f(n, f, v):
    """v and f cancel identically. This is why it cannot fail -- and why
    it is a definition rather than a discovery."""
    assert G.round_trip_phase_turns(v, Fraction(f), n) == Fraction(1, n)
    assert G.identity_holds(v, Fraction(f), n)


def test_round_trip_time_equals_one_over_nf():
    """2L/v = 1/(N f) exactly."""
    for n in (1, 3, 7, 24):
        t = G.round_trip_time(G.V_PROXY_M_S, G.F_KEY_HZ, n).value
        assert t == 1 / (n * G.F_KEY_HZ)


# --- the frozen numbers ------------------------------------------------

def test_frozen_n7_geometry_reproduces_the_pack():
    g = G.n7_geometry()
    assert g["length_mm"] == pytest.approx(110.03766741071429, rel=1e-12)
    assert g["one_way_us"] == pytest.approx(17.43861607142857, rel=1e-12)
    assert g["round_trip_us"] == pytest.approx(34.87723214285714, rel=1e-12)
    assert g["round_trip_degrees"] == pytest.approx(51.42857142857142,
                                                    rel=1e-12)
    assert g["wavelength_m"] == pytest.approx(1.5405273437500, rel=1e-12)
    assert g["identity_holds"] is True


def test_wavelength_and_length_relation():
    lam = G.wavelength(G.V_PROXY_M_S, G.F_KEY_HZ).value
    L = G.half_wave_length(G.V_PROXY_M_S, G.F_KEY_HZ, 7).value
    assert L == lam / 14            # lambda / (2N), N = 7


def test_frequency_from_length_inverts_half_wave_length():
    L = G.half_wave_length(G.V_PROXY_M_S, G.F_KEY_HZ, 7).value
    f = G.frequency_from_length(G.V_PROXY_M_S, L, 7).value
    assert f == G.F_KEY_HZ


# --- unit discipline ---------------------------------------------------

def test_microseconds_are_never_compared_with_hertz():
    t = G.Quantity(Fraction(1, 1000), G.Unit.SECOND)
    f = G.Quantity(Fraction(4096), G.Unit.HERTZ)
    with pytest.raises(G.N7GeomError):
        G.refuse_unit_comparison(t, f)


def test_millimetres_are_never_compared_with_degrees():
    L = G.Quantity(Fraction(110), G.Unit.MILLIMETRE)
    a = G.Quantity(Fraction(360, 7), G.Unit.DEGREE)
    with pytest.raises(G.N7GeomError):
        G.refuse_unit_comparison(L, a)


def test_compatible_units_are_allowed():
    a = G.Quantity(Fraction(1, 7), G.Unit.TURN)
    b = G.Quantity(Fraction(360, 7), G.Unit.DEGREE)
    assert G.refuse_unit_comparison(a, b) is G.Unit.TURN


def test_float_input_is_refused():
    with pytest.raises(G.N7GeomError):
        G.Quantity(0.1428, G.Unit.TURN)      # type: ignore[arg-type]


# --- the refusals that matter ------------------------------------------

def test_the_identity_may_not_be_read_as_evidence():
    with pytest.raises(G.N7GeomError):
        G.refuse_identity_as_evidence()


def test_the_scalar_model_is_not_a_specimen_prediction():
    with pytest.raises(G.N7GeomError):
        G.refuse_scalar_model_as_specimen_prediction()


def test_bad_n_is_refused():
    with pytest.raises(G.N7GeomError):
        G.half_wave_length(G.V_PROXY_M_S, G.F_KEY_HZ, 0)
    with pytest.raises(G.N7GeomError):
        G.round_trip_phase_degrees(0)


# --- the sweep ---------------------------------------------------------

def test_the_sweep_shows_the_identity_is_universal():
    rows = G.geometry_sweep()
    assert len(rows) == 24 * 13
    assert all(r["identity_holds"] for r in rows)
    # and the length genuinely varies, so the sweep is not trivial
    assert len({r["length_mm"] for r in rows}) > 100


def test_report_states_the_identity_cannot_fail():
    r = G.n7geom_report()
    assert r["claim_class"] == "EXACT_IDENTITY"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "cannot fail" in r["what_this_does_not_say"]
    assert r["verdict"] == "N7_PHASE_IDENTITY_EXACT_BY_CONSTRUCTION"
