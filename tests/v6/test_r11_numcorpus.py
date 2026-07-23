"""P0N — the numeric corpus: exact layout, long division, retained nulls."""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from r11 import numcorpus as N


# --- the layout is the datum -------------------------------------------

def test_raw_layout_preserves_leading_zeros():
    layout = N.raw_layout()
    assert "096785" in layout
    assert "0341" in layout
    # the normalised integers must NOT have replaced them
    assert "96785" not in layout
    assert "341" not in layout


def test_raw_layout_preserves_the_parenthesis():
    layout = N.raw_layout()
    assert "(3)44478" in layout
    # the debracketed readings must NOT have replaced the recorded row
    assert "344478" not in layout
    assert "44478" not in layout
    assert sum("44478" in row for row in layout) == 1


def test_grouped_rows_stay_grouped():
    layout = N.raw_layout()
    for row, n_groups in (("4096 12 63 24", 4),
                          ("9192 631 770", 3),
                          ("15 17 23 27 33 34 48", 7),
                          ("23 34 56 72", 4)):
        assert row in layout
        assert len(row.split()) == n_groups
        # never silently concatenated into one numeral
        assert row.replace(" ", "") not in layout


def test_layout_row_count_and_decimal_trailing_zero():
    assert len(N.raw_layout()) == 21
    assert "8.300" in N.raw_layout()          # trailing zeros retained
    assert "1.876" in N.raw_layout()
    assert "30.05" in N.raw_layout()


def test_corpus_hash_changes_when_a_row_is_regrouped():
    regrouped = tuple("4096122324" if r == "4096 12 63 24" else r
                      for r in N.raw_layout())
    assert N.corpus_hash(regrouped) != N.corpus_hash()


def test_refuse_regrouping_raises():
    with pytest.raises(N.CorpusError):
        N.refuse_regrouping("4096 12 63 24", "4096122324")


# --- parsing: failures retained, never dropped -------------------------

def test_bracketed_entry_is_retained_as_ambiguous():
    e = N.parse_entry("(3)44478")
    assert e.status is N.ParseStatus.PARSE_AMBIGUOUS
    assert e.value is None
    assert e.raw == "(3)44478"       # verbatim, bracket intact
    assert not e.parsed


def test_grouped_entry_is_retained_with_its_groups():
    e = N.parse_entry("15 17 23 27 33 34 48")
    assert e.status is N.ParseStatus.PARSE_GROUPED
    assert e.value is None
    assert e.groups == ("15", "17", "23", "27", "33", "34", "48")


def test_failed_parses_are_returned_not_dropped():
    failed = N.failed_parses()
    raws = [e.raw for e in failed]
    assert "(3)44478" in raws
    assert "4096 12 63 24" in raws
    assert "9192 631 770" in raws
    assert "15 17 23 27 33 34 48" in raws
    assert "23 34 56 72" in raws
    assert len(failed) == 5
    # and every failed row is still a row of the corpus
    assert all(r in N.raw_layout() for r in raws)


def test_every_row_is_accounted_for():
    summary = N.parse_summary()
    assert summary["rows"] == len(N.raw_layout())
    assert summary["all_rows_retained"]
    assert summary["retained_unparsed"] == 5
    assert len(N.entries()) == len(N.raw_layout())


def test_leading_zero_entry_parses_but_keeps_its_raw_form():
    e = N.parse_entry("096785")
    assert e.status is N.ParseStatus.PARSE_INTEGER
    assert e.value == F(96785)
    assert e.raw == "096785"
    assert e.leading_zeros == 1
    assert N.parse_entry("0341").leading_zeros == 1
    assert N.parse_entry("8697").leading_zeros == 0


def test_ratio_and_decimal_rows_parse():
    assert N.parse_entry("37/53").value == F(37, 53)
    assert N.parse_entry("51/84").value == F(51, 84)
    assert N.parse_entry("8.300").status is N.ParseStatus.PARSE_DECIMAL
    assert N.parse_entry("8.300").value == F(83, 10)
    assert N.parse_entry("8.300").declared_digits == 4   # precision as written


# --- long division: the repetend finder actually works -----------------

def test_repetend_of_one_third():
    d = N.decimal_expansion(F(1, 3))
    assert d.prefix == "0."
    assert d.repetend == "3"
    assert not d.terminating


def test_repetend_of_one_seventh():
    d = N.decimal_expansion(F(1, 7))
    assert d.prefix == "0."
    assert d.repetend == "142857"
    assert d.period == 6


def test_one_half_terminates_with_an_empty_repetend():
    d = N.decimal_expansion(F(1, 2))
    assert d.prefix == "0.5"
    assert d.repetend == ""
    assert d.terminating


def test_mixed_prefix_and_repetend():
    d = N.decimal_expansion(F(1, 6))          # 0.1666...
    assert d.prefix == "0.1"
    assert d.repetend == "6"


def test_repetend_reconstructs_the_value_digits():
    # POWER: the finder is checked against float expansion, not itself.
    d = N.decimal_expansion(F(37, 53))
    assert d.rendered(cycles=1).startswith("0.698113")
    assert d.period == 13                      # 53 has a 13-digit period


# --- factorisation -----------------------------------------------------

def test_denominator_factorization_of_55_and_192():
    assert N.prime_factorization(55) == {5: 1, 11: 1}
    assert N.prime_factorization(192) == {2: 6, 3: 1}
    assert N.factorization_string({2: 6, 3: 1}) == "2^6*3"
    fwd = N.audit_fraction(192, 55)["forward"]
    assert fwd["denominator_factorization"] == {5: 1, 11: 1}
    inv = N.audit_fraction(192, 55)["inverse"]
    assert inv["denominator_factorization"] == {2: 6, 3: 1}


def test_factorization_rejects_zero():
    with pytest.raises(N.CorpusError):
        N.prime_factorization(0)


# --- phase and the 15-degree lattice -----------------------------------

def test_seven_halves_is_half_a_turn_180_degrees_sector_12():
    fwd = N.audit_fraction(7, 2)["forward"]
    assert fwd["phase_turns"] == "1/2"
    assert fwd["degrees"] == "180"
    assert fwd["sector"]["on_15_degree_lattice"]
    assert fwd["sector"]["sector_index_int"] == 12


def test_a_fraction_off_the_lattice_is_flagged():
    fwd = N.audit_fraction(37, 53)["forward"]
    assert not fwd["sector"]["on_15_degree_lattice"]
    assert fwd["sector"]["sector_index_int"] is None


# --- the 4096 ladder ---------------------------------------------------

def test_three_quarters_lands_exactly_on_the_4096_ladder():
    ladder = N.audit_fraction(3, 4)["forward"]["ladder_4096"]
    assert ladder["is_integer"]
    assert ladder["integer"] == 3072
    assert ladder["value_times_base"] == "3072"
    assert ladder["flag"] == "ON_LADDER"


def test_a_fraction_off_the_ladder_is_flagged():
    ladder = N.audit_fraction(37, 53)["forward"]["ladder_4096"]
    assert not ladder["is_integer"]
    assert ladder["integer"] is None
    assert ladder["flag"] == "OFF_LADDER_NOT_AN_INTEGER"


# --- the isotope reading, both orientations ----------------------------

def test_192_over_55_and_55_over_192_give_different_ages():
    iso = N.audit_fraction(192, 55)["isotope_interpretation"]
    assert iso["forward_age"] != iso["inverse_age"]
    assert iso["orientations_differ"]
    assert iso["status"] == "INTERPRETATION_NOT_MEASUREMENT"
    flipped = N.audit_fraction(55, 192)["isotope_interpretation"]
    assert flipped["forward_age"] == pytest.approx(iso["inverse_age"])
    assert flipped["inverse_age"] == pytest.approx(iso["forward_age"])


def test_isotope_age_uses_the_declared_scale_and_log2():
    import math
    assert N.isotope_age(F(1)) == pytest.approx(30.05 * math.log2(2.0))
    assert N.isotope_age(F(0)) == 0.0


def test_isotope_refuses_a_zero_term():
    with pytest.raises(N.CorpusError):
        N.isotope_both_orientations(0, 5)


# --- complexity and its null -------------------------------------------

def test_complexity_and_null_are_reported_for_each_audited_fraction():
    for a, b in N.AUDIT_PAIRS:
        fwd = N.audit_fraction(a, b)["forward"]
        assert isinstance(fwd["expression_complexity"], int)
        p = fwd["null"]["share_at_least_as_simple"]
        assert 0.0 <= p <= 1.0


def test_a_simpler_fraction_has_lower_complexity():
    assert (N.expression_complexity(F(3, 4))
            < N.expression_complexity(F(37, 53)))


# --- unit status --------------------------------------------------------

def test_unit_status_is_undeclared_by_default():
    assert N.unit_status() is N.UnitStatus.UNDECLARED
    assert N.audit_fraction(37, 53)["unit_status"] == "UNDECLARED"
    assert (N.unit_status("hertz", "hertz")
            is N.UnitStatus.DECLARED_CONSISTENT)
    assert (N.unit_status("hertz", "metres")
            is N.UnitStatus.DECLARED_INCONSISTENT)


# --- refusals -----------------------------------------------------------

def test_refuse_retired_sequence_raises_for_a_registered_sequence():
    retired = sorted(N.RETIRED_SEQUENCES)[0]
    with pytest.raises(N.CorpusError):
        N.refuse_retired_sequence(retired)


def test_refuse_retired_sequence_raises_for_anything_else_too():
    with pytest.raises(N.CorpusError):
        N.refuse_retired_sequence("1234567890")


def test_audit_refuses_a_zero_term():
    with pytest.raises(N.CorpusError):
        N.audit_fraction(5, 0)
    with pytest.raises(N.CorpusError):
        N.audit_fraction(0, 5)


# --- the scheduled audit -----------------------------------------------

def test_all_scheduled_pairs_are_audited():
    audits = N.audit_all()
    for a, b in ((37, 53), (51, 84), (192, 55), (55, 192), (2, 3),
                 (3, 4), (5, 6), (7, 2), (63, 6)):
        assert f"{a}/{b}" in audits
    assert len(N.audit_summary()) == len(N.AUDIT_PAIRS)


def test_51_over_84_reduces_and_63_over_6_is_an_integer_ratio():
    assert N.audit_fraction(51, 84)["forward"]["reduced"] == "17/28"
    assert N.audit_fraction(63, 6)["forward"]["reduced"] == "21/2"


# --- report -------------------------------------------------------------

def test_report_measures_nothing_and_identifies_no_decoder():
    r = N.numcorpus_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == N.EVIDENCE_CLASS
    assert r["verdict"] == "NUMERIC_CORPUS_AUDITED_NO_DECODER_IDENTIFIED"
    assert "decoder" in r["what_this_does_not_say"]
    assert r["raw_layout"] == list(N.raw_layout())
    assert r["failed_parses"]
