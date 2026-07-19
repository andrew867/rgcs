"""P07 — CW ontology and the unit-collision firewall."""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from r10 import cwontology as O


# --- the three senses --------------------------------------------------

def test_only_the_carrier_sense_has_a_frequency():
    """A code word is an index. A modulation mode is a mode. Neither
    is a quantity in hertz."""
    assert O.CW_SENSES["CW_CARRIER_WAVE"]["has_frequency"]
    assert not O.CW_SENSES["CW_CODE_WORD"]["has_frequency"]
    assert not O.CW_SENSES["CW_CONTINUOUS_WAVE"]["has_frequency"]
    assert O.cw_ontology_report()["senses_with_frequency"] == \
        ["CW_CARRIER_WAVE"]


def test_every_sense_declares_a_dimension():
    for name, spec in O.CW_SENSES.items():
        assert spec["dimension"] in O.DIMENSIONS, name
        assert spec["meaning"]


# --- unit collisions ---------------------------------------------------

def test_same_digits_different_dimension_is_a_collision():
    """Contract rule 3, as an exception rather than a footnote."""
    code = O.TypedValue(F(144), "DIMENSIONLESS", "codebook index")
    freq = O.TypedValue(F(144), "FREQUENCY_HZ", "measured")
    with pytest.raises(O.UnitCollision) as e:
        code.same_as(freq)
    assert "UNIT_COLLISION" in str(e.value)
    assert "not evidence" in str(e.value)


def test_collision_report_describes_without_comparing():
    code = O.TypedValue(F(144), "DIMENSIONLESS", "index")
    bins = O.TypedValue(F(144), "PHASE_BIN", "bin index")
    r = O.collision_report(code, bins)
    assert r["verdict"] == "UNIT_COLLISION"
    assert r["numerically_equal"]        # the digits do match
    assert not r["comparable"]           # and that is not a finding
    assert "about notation" in r["note"]


def test_same_dimension_compares_normally():
    a = O.TypedValue(F(144), "FREQUENCY_HZ", "x")
    b = O.TypedValue(F(144), "FREQUENCY_HZ", "y")
    c = O.TypedValue(F(145), "FREQUENCY_HZ", "z")
    assert a.same_as(b)
    assert not a.same_as(c)
    assert O.collision_report(a, b)["verdict"] == "COMPARABLE"


def test_typed_values_stay_exact():
    v = O.TypedValue(F(1, 3), "FREQUENCY_HZ", "x")
    assert isinstance(v.value, F)
    assert v.value == F(1, 3)


def test_unknown_dimension_refused():
    with pytest.raises(ValueError):
        O.TypedValue(F(1), "FURLONGS_PER_FORTNIGHT", "x")


# --- untyped decimals --------------------------------------------------

def test_an_untyped_decimal_cannot_become_a_frequency():
    with pytest.raises(O.UntypedValue) as e:
        O.refuse_untyped_as_frequency("144.000")
    msg = str(e.value)
    assert "without a unit" in msg
    assert "decimal separator" in msg


def test_the_cw_set_is_left_untyped():
    """No unit was recorded, so none is assigned."""
    t = O.CW_SET_TYPING
    assert t["dimension"] == "DIMENSIONLESS"
    assert t["status"] == "UNTYPED_DECIMAL"
    assert t["sense"] == "CW_UNSPECIFIED"
    assert "not hertz" in t["note"]


def test_typed_cw_set_carries_no_frequency():
    for v in O.typed_cw_set():
        assert v.dimension == "DIMENSIONLESS"


def test_cw_values_cannot_be_compared_to_frequencies():
    cw = O.typed_cw_set()[0]
    hz = O.TypedValue(F(1516), "FREQUENCY_HZ", "hypothetical")
    with pytest.raises(O.UnitCollision):
        cw.same_as(hz)


# --- attribution and claim discipline ----------------------------------

def test_attribution_stays_at_region_granularity():
    assert O.CW_SET_TYPING["attribution"] == "from the omega region"


def test_report_does_not_deny_that_a_unit_exists():
    """'No unit recorded' is not 'no unit exists'."""
    w = O.cw_ontology_report()["what_this_does_not_say"]
    assert "does not say the values have no unit in reality" in w
    assert "inventing the evidence" in w
