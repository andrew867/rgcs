"""P01 — the fractional phase alphabet, exact, and its one-channel loss."""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from r11 import phasealpha as P


# --- the four rows, exact ----------------------------------------------

EXPECTED_ROWS = {
    # pair: (literal, phase mod 1 turn, degrees, 15-degree sector)
    "23": (F(2, 3), F(2, 3), F(240), 16),
    "34": (F(3, 4), F(3, 4), F(270), 18),
    "56": (F(5, 6), F(5, 6), F(300), 20),
    "72": (F(7, 2), F(1, 2), F(180), 12),
}


@pytest.mark.parametrize("pair", sorted(EXPECTED_ROWS))
def test_each_row_is_exact(pair):
    lit, phase, deg, sector = EXPECTED_ROWS[pair]
    s = P.symbol(pair)
    assert s.literal == lit
    assert s.phase_turns == phase
    assert s.degrees == deg
    assert s.sector == sector


def test_seven_halves_reduces_to_a_half_turn_at_180_degrees():
    s = P.symbol("72")
    assert s.literal == F(7, 2)
    assert s.phase_turns == F(1, 2)          # the key reduction
    assert s.degrees == F(180)
    assert s.sector == 12
    assert s.reduces


def test_the_other_three_do_not_reduce():
    assert not any(P.symbol(p).reduces for p in ("23", "34", "56"))


def test_the_alphabet_has_four_symbols_and_a_neutral_name():
    assert len(P.PHASE_ALPHABET_A) == 4
    assert [s.pair for s in P.PHASE_ALPHABET_A] == ["23", "34", "56", "72"]


def test_all_four_land_on_the_15_degree_lattice():
    assert P.on_15_degree_lattice()
    assert P.SECTOR_DEGREES == F(15)
    assert P.SECTOR_COUNT == 24
    assert all(0 <= s.sector < 24 for s in P.PHASE_ALPHABET_A)


def test_degrees_are_phase_times_360_exactly():
    for s in P.PHASE_ALPHABET_A:
        assert s.degrees == s.phase_turns * 360
        assert isinstance(s.degrees, F)


def test_a_phase_off_the_lattice_has_no_sector():
    with pytest.raises(P.PhaseAlphaError):
        P.sector_15deg(F(7))                 # 7 degrees, not a multiple of 15


# --- times_192: literal vs phase ---------------------------------------

EXPECTED_192 = {
    # pair: (literal*192, phase*192, do they agree?)
    "23": (F(128), F(128), True),
    "34": (F(144), F(144), True),
    "56": (F(160), F(160), True),
    "72": (F(672), F(96), False),
}


@pytest.mark.parametrize("pair", sorted(EXPECTED_192))
def test_times_192_literal_and_phase(pair):
    lit192, phase192, agree = EXPECTED_192[pair]
    s = P.symbol(pair)
    assert s.literal_times_192 == lit192
    assert s.phase_times_192 == phase192
    assert (s.literal_times_192 == s.phase_times_192) is agree


def test_seven_halves_is_the_only_row_where_the_scalings_differ():
    s = P.symbol("72")
    assert s.literal_times_192 == 672
    assert s.phase_times_192 == 96
    assert s.literal_times_192 != s.phase_times_192
    differing = [t["pair"] for t in P.alphabet_table()
                 if not t["literal_and_phase_scalings_agree"]]
    assert differing == ["72"]


# --- cos^2 / sin^2 ------------------------------------------------------

EXPECTED_QUADRATIC = {
    "23": (0.25, 0.75),      # 240 deg
    "34": (0.0, 1.0),        # 270 deg
    "56": (0.25, 0.75),      # 300 deg
    "72": (1.0, 0.0),        # 180 deg
}


@pytest.mark.parametrize("pair", sorted(EXPECTED_QUADRATIC))
def test_quadratic_projections(pair):
    assert P.quadratic_projections(P.symbol(pair)) == EXPECTED_QUADRATIC[pair]


def test_quadratic_projections_sum_to_one():
    for s in P.PHASE_ALPHABET_A:
        c2, s2 = P.quadratic_projections(s)
        assert c2 + s2 == pytest.approx(1.0)


# --- the required negative result --------------------------------------

def test_240_and_300_degrees_share_a_quadratic_value():
    assert (P.quadratic_projections(P.symbol("23"))[0]
            == P.quadratic_projections(P.symbol("56"))[0] == 0.25)


def test_the_degeneracy_names_the_colliding_pair():
    d = P.quadratic_channel_degeneracy()
    assert d["colliding_pair"] == ("23", "56")
    assert d["colliding_degrees"] == (240.0, 300.0)
    assert d["shared_cos_squared"] == 0.25
    assert d["symbols_in"] == 4
    assert d["distinct_values_out"] == 3
    assert d["verdict"] == "SINGLE_QUADRATIC_CHANNEL_INSUFFICIENT"


def test_a_single_quadratic_channel_cannot_recover_the_symbols():
    assert P.symbols_recoverable(P.SINGLE_QUADRATIC_CHANNEL) is False
    assert P.symbols_recoverable(P.ChannelModel.QUADRATIC_ZEEMAN) is False


def test_signed_and_phase_sensitive_channels_can():
    for model in (P.ChannelModel.SIGNED_QUADRATURE,
                  P.ChannelModel.ORTHOGONAL_FIELD_AXES,
                  P.ChannelModel.IQ_MICROWAVE,
                  P.ChannelModel.RAMSEY_ZONES):
        assert P.symbols_recoverable(model) is True


def test_only_the_quadratic_model_loses_symbols():
    table = P.recoverability_table()
    losing = [name for name, ok in table.items() if not ok]
    assert losing == [P.ChannelModel.QUADRATIC_ZEEMAN.value]


def test_the_quadratic_pair_is_not_two_independent_channels():
    r = P.quadratic_zeeman(P.symbol("23"))
    assert r.phase_sensitive is False
    assert r.values[1] == pytest.approx(1 - r.values[0])


def test_refuse_single_quadratic_channel_raises():
    with pytest.raises(P.PhaseAlphaError) as exc:
        P.refuse_single_quadratic_channel("all four symbols survive")
    assert "single quadratic channel" in str(exc.value)


def test_unknown_channel_model_is_refused():
    with pytest.raises(P.PhaseAlphaError):
        P.symbols_recoverable("OPTICAL_TELEPATHY")


# --- the two meanings of 7/2 -------------------------------------------

def test_refuse_spin_phase_conflation_raises():
    with pytest.raises(P.PhaseAlphaError) as exc:
        P.refuse_spin_phase_conflation(F(7, 2), "supplied phase symbol")
    msg = str(exc.value)
    assert "nuclear spin" in msg
    assert P.CANDIDATE_CORRESPONDENCE in msg


def test_the_correspondence_is_a_candidate_only():
    c = P.seven_halves_correspondence()
    assert c["numerically_equal"] is True
    assert c["same_kind_of_quantity"] is False
    assert c["status"] == "CANDIDATE_CORRESPONDENCE"
    assert c["meanings"]["NUCLEAR_SPIN_I"]["degrees"] is None
    assert c["meanings"]["RATIONAL_PHASE"]["degrees"] == 180.0


# --- frequency vs angular frequency ------------------------------------

def test_omega_and_f_round_trip():
    f = P.Quantity(4096.0, P.Unit.CYCLES_PER_SECOND)
    omega = P.angular_frequency(f)
    assert omega.unit is P.Unit.RADIANS_PER_SECOND
    assert omega.value == pytest.approx(2 * 3.141592653589793 * 4096.0)
    back = P.ordinary_frequency(omega)
    assert back.unit is P.Unit.CYCLES_PER_SECOND
    assert back.value == pytest.approx(4096.0)


def test_the_conversions_check_their_input_unit():
    with pytest.raises(P.PhaseAlphaError):
        P.angular_frequency(P.Quantity(1.0, P.Unit.RADIANS_PER_SECOND))
    with pytest.raises(P.PhaseAlphaError):
        P.ordinary_frequency(P.Quantity(1.0, P.Unit.CYCLES_PER_SECOND))


def test_refuse_unit_confusion_raises_across_unit_kinds():
    deg = P.Quantity(180.0, P.Unit.DEGREES)
    hz = P.Quantity(180.0, P.Unit.CYCLES_PER_SECOND)
    with pytest.raises(P.PhaseAlphaError):
        P.refuse_unit_confusion(deg, hz)
    with pytest.raises(P.PhaseAlphaError):
        P.refuse_unit_confusion(P.Quantity(0.5, P.Unit.TURNS), deg)


def test_matching_units_are_allowed_through():
    a = P.Quantity(180.0, P.Unit.DEGREES)
    b = P.Quantity(240.0, P.Unit.DEGREES)
    assert P.refuse_unit_confusion(a, b) is P.Unit.DEGREES


# --- the report ---------------------------------------------------------

def test_report_measures_nothing_and_claims_no_validation():
    r = P.phasealpha_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"]
    assert "does not say" in r["what_this_does_not_say"]


def test_report_verdict():
    assert P.phasealpha_report()["verdict"] == (
        "FRACTIONAL_PHASE_ALPHABET_SPECIFIABLE")
    assert P.VERDICT == "FRACTIONAL_PHASE_ALPHABET_SPECIFIABLE"


def test_report_carries_the_alphabet_and_the_negative_result():
    r = P.phasealpha_report()
    assert [row["pair"] for row in r["alphabet"]] == ["23", "34", "56", "72"]
    assert r["on_15_degree_lattice"] is True
    assert r["quadratic_degeneracy"]["colliding_pair"] == ("23", "56")
    assert r["recoverability"][
        P.ChannelModel.QUADRATIC_ZEEMAN.value] is False
