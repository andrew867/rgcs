"""P07 — octave relation, 1<->8 bridge, and the "infinite octave"."""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from r9 import octave as O


# --- exactness ---------------------------------------------------------

def test_octave_ratio_is_exactly_two():
    assert O.OCTAVE_RATIO == F(2, 1)
    assert isinstance(O.OCTAVE_RATIO, F)


def test_octave_arithmetic_stays_exact():
    """No float creeps in: a third of a hertz stays a third."""
    f = F(1, 3)
    assert O.octave_up(f, 3) == F(8, 3)
    assert O.octave_up(f, -2) == F(1, 12)
    assert isinstance(O.octave_up(f), F)


def test_octave_up_and_down_round_trip():
    f = F(440)
    assert O.octave_up(O.octave_up(f, 7), -7) == f


def test_equivalence_is_exact_not_tolerant():
    assert O.are_octave_equivalent(F(440), F(880))
    assert O.are_octave_equivalent(F(440), F(440) / 1024)
    assert not O.are_octave_equivalent(F(440), F(660))
    # a cent away from an octave is not an octave
    assert not O.are_octave_equivalent(F(88000), F(44001))


def test_equivalence_is_reflexive_symmetric_transitive():
    a, b, c = F(100), F(200), F(400)
    assert O.are_octave_equivalent(a, a)
    assert O.are_octave_equivalent(a, b) == O.are_octave_equivalent(b, a)
    assert O.are_octave_equivalent(a, b) and O.are_octave_equivalent(b, c)
    assert O.are_octave_equivalent(a, c)


def test_pitch_class_folds_into_one_octave():
    for f in (F(440), F(880), F(1760), F(55), F(440) / 8):
        pc = O.pitch_class(f, F(440))
        assert F(440) <= pc < F(880)
        assert O.are_octave_equivalent(pc, f)


def test_pitch_class_is_idempotent():
    pc = O.pitch_class(F(1234), F(440))
    assert O.pitch_class(pc, F(440)) == pc


def test_octave_number():
    assert O.octave_number(F(880), F(440)) == 1
    assert O.octave_number(F(440), F(440)) == 0
    assert O.octave_number(F(220), F(440)) == -1


def test_nonpositive_frequencies_refused():
    for bad in (F(0), F(-1)):
        with pytest.raises(ValueError):
            O.octave_up(bad)
        with pytest.raises(ValueError):
            O.pitch_class(bad, F(440))
        with pytest.raises(ValueError):
            O.are_octave_equivalent(bad, F(440))


# --- the 1<->8 bridge --------------------------------------------------

def test_scale_has_seven_degrees_not_eight():
    """The load-bearing fact. '8' is one of them named twice."""
    assert O.DIATONIC_DEGREES == 7
    assert len(O.DIATONIC_STEPS) == 7


def test_seven_steps_close_the_octave_exactly():
    assert O.verify_steps_close_the_octave()
    assert sum(O.DIATONIC_STEPS) == 12


def test_bridge_is_true_but_trivial():
    b = O.one_to_eight_bridge()
    assert b["status"] == "TRUE_BUT_TRIVIAL"
    assert "inclusive counting" in b["explanation"]


def test_bridge_denies_an_eighth_element():
    b = O.one_to_eight_bridge()
    assert "not an eighth element" in b["what_it_is_not"]
    assert "No mechanism is needed" in b["what_it_is_not"]


# --- the "infinite octave" ---------------------------------------------

def test_infinite_is_true_as_maths_and_false_as_physics():
    c = O.infinite_octave_claim()
    assert c["mathematical_status"] == "TRUE"
    assert c["physical_status"] == "FALSE"


def test_physical_span_is_finite_and_about_two_hundred_octaves():
    s = O.physical_octave_span()
    assert s["verdict"] == "FINITE"
    assert 195 < s["octaves_available"] < 210


def test_span_bounds_are_the_stated_ones():
    s = O.physical_octave_span()
    assert s["highest_hz"] == O.PLANCK_FREQUENCY_HZ
    assert s["lowest_hz"] == pytest.approx(1.0 / O.UNIVERSE_AGE_S)
    assert "Planck" in s["highest_basis"]
    assert "age of the universe" in s["lowest_basis"]


def test_both_halves_of_the_resolution_are_kept():
    """Neither 'it's just numerology' nor 'it's infinite'."""
    c = O.infinite_octave_claim()
    r = c["resolution"]
    assert "true about the number line" in r
    assert "false about the world" in r


def test_source_is_not_licensed_as_a_place():
    c = O.infinite_octave_claim()
    n = c["what_this_does_not_license"]
    assert "not license treating" in n
    assert "energy reservoir" in n


def test_source_as_physical_location_is_refused():
    with pytest.raises(O.OctaveClaimRefused) as e:
        O.refuse_source_as_physical_location()
    assert "not physical locations" in str(e.value)


# --- ledger discipline -------------------------------------------------

def test_ledger_keeps_three_claims_apart():
    L = O.source_octave_ledger()
    assert L["one_to_eight"]["status"] == "TRUE_BUT_TRIVIAL"
    assert L["infinite_octave"]["mathematical_status"] == "TRUE"
    assert L["octave_is_exact"]
    assert "Keeping the three apart" in L["summary"]


def test_ledger_claims_no_measurement():
    L = O.source_octave_ledger()
    assert L["measured_here"] == "nothing"
    assert L["evidence_class"] == "ARITHMETIC_AND_LITERATURE_BOUNDS"
