"""P02 — CW vector decoder and its null.

The tests that matter are the ones asserting the headline observation
carries no information. A decoder that could only ever say "yes, this
looks like a protocol" would pass every syntactic test in this file.
"""

from __future__ import annotations

import pytest

import r7
from r7 import cw


VALS = cw.as_ints()


# --- source integrity -------------------------------------------------

def test_sources_preserved_as_strings():
    """Integer conversion destroys leading zeros, so the string is the
    artifact and the integer is derived."""
    for s in cw.SOURCE_STRINGS:
        assert isinstance(s, str)
        assert len(s) == 12


def test_all_five_are_38_bit():
    assert [v.bit_length() for v in VALS] == [38] * 5


def test_identity_holds():
    assert 38 == 2 + 3 * 12 == 2 + 6 * 6


# --- the arithmetic that settles it ----------------------------------

def test_forced_never_exceeds_observed():
    """The consistency check that caught the original bug.

    More bits cannot be *forced* identical than are *observed*
    identical. When this failed (16 forced vs 15 observed) it exposed
    that the span shortcut was wrong.
    """
    assert cw.forced_common_bits(VALS) <= cw.observed_common_bits(VALS)


def test_span_shortcut_is_wrong_on_a_straddle():
    """127 and 128 span 1 and share no leading bits at all."""
    assert cw.forced_common_bits((127, 128), 8) == 0
    naive = 8 - (128 - 127).bit_length()
    assert naive == 7 and naive != 0


def test_identical_values_force_full_width():
    assert cw.forced_common_bits((5, 5), 38) == 38


def test_single_value_rejected():
    with pytest.raises(ValueError):
        cw.forced_common_bits((1,))


def test_fifteen_leading_bits_are_forced():
    assert cw.forced_common_bits(VALS) == 15
    assert cw.observed_common_bits(VALS) == 15


def test_header_and_first_field_lie_inside_the_forced_prefix():
    """2 + 12 = 14 bits, entirely inside the 15 forced bits."""
    rep = cw.parse_report(VALS, 2, 12, 3, "HEADER2_PLUS_3X12")
    assert rep.header_is_forced
    assert 0 in rep.constant_fields_forced
    assert rep.constant_fields_informative == ()


def test_the_observation_carries_zero_informative_bits():
    """The headline result of P02."""
    rep = cw.parse_report(VALS, 2, 12, 3, "HEADER2_PLUS_3X12")
    assert rep.informative_bits == 0


def test_six_by_six_parse_is_equally_uninformative():
    rep = cw.parse_report(VALS, 2, 6, 6, "HEADER2_PLUS_6X6")
    assert rep.header_is_forced
    assert rep.constant_fields_informative == ()


def test_reported_fields_match_the_pack_analysis():
    """Reproduce the pack's own table, so the refutation is of the
    actual numbers and not a different parse."""
    rep = cw.parse_report(VALS, 2, 12, 3, "HEADER2_PLUS_3X12")
    assert set(rep.headers) == {0b10}
    assert [f[0] for f in rep.fields] == [1516] * 5
    assert rep.fields[0] == (1516, 556, 3308)
    assert rep.fields[1] == (1516, 542, 15)


def test_split_rejects_inconsistent_widths():
    with pytest.raises(ValueError):
        cw.split_fields(VALS[0], 2, 12, 4)


# --- the matched null -------------------------------------------------

def test_random_integers_reproduce_the_structure():
    """The null that ends the discussion.

    Integers drawn uniformly from the same interval, with no encoding
    at all, show the same constant header and constant leading field.
    """
    null = cw.shared_prefix_null(VALS, 2, 12, 3, n_draws=2000,
                                 seed=1)
    assert null["p_both"] == 1.0


def test_null_is_deterministic_under_seed():
    a = cw.shared_prefix_null(VALS, 2, 12, 3, n_draws=500, seed=7)
    b = cw.shared_prefix_null(VALS, 2, 12, 3, n_draws=500, seed=7)
    assert a == b


def test_null_probabilities_are_probabilities():
    null = cw.shared_prefix_null(VALS, 2, 12, 3, n_draws=500, seed=3)
    for k in ("p_constant_header", "p_constant_field0", "p_both"):
        assert 0.0 <= null[k] <= 1.0


def test_a_wide_interval_does_not_force_structure():
    """Sanity: the null only returns 1.0 because the span is narrow."""
    wide = (1, 2 ** 37, 2 ** 36, 3, 2 ** 35)
    null = cw.shared_prefix_null(wide, 2, 12, 3, n_draws=500, seed=5)
    assert null["p_both"] < 0.5


# --- decoder law ------------------------------------------------------

def test_all_hypotheses_are_reported():
    rep = cw.all_parses()
    assert len(rep["hypotheses_frozen"]) == len(cw.PARSE_HYPOTHESES)
    assert "UNRELATED_LABELS" in rep["hypotheses_frozen"]
    assert "ENCRYPTED_OR_PSEUDORANDOM" in rep["hypotheses_frozen"]


def test_decimal_alternatives_are_reported():
    seg = cw.decimal_segments()
    assert seg["162875493612"]["triplets"] == [162, 875, 493, 612]
    assert seg["162875493612"]["pairs"][0] == 16


def test_identity_note_says_every_38_bit_value_admits_the_parse():
    rep = cw.all_parses()
    assert "EVERY 38-bit value" in rep["identity_note"]


def test_decoder_is_frozen_by_digest():
    a = cw.FrozenDecoder("X", 2, 12, 3)
    b = cw.FrozenDecoder("X", 2, 12, 3)
    c = cw.FrozenDecoder("X", 2, 6, 6)
    assert a.digest() == b.digest()
    assert a.digest() != c.digest()


def test_decode_reports_no_semantics():
    out = cw.FROZEN_DECODERS[0].decode(VALS[0])
    assert out["semantics"] is None
    assert "syntax only" in out["note"]


def test_field_reassignment_is_refused():
    with pytest.raises(cw.CWRefused) as e:
        cw.reassign_fields()
    assert "frozen" in str(e.value)


# --- promotion --------------------------------------------------------

def test_retrospective_cannot_promote_without_prospective_vectors():
    assert cw.promote("CW_PARSE_RETROSPECTIVE") == \
        "CW_PARSE_RETROSPECTIVE"


def test_prospective_vectors_allow_one_step_only():
    assert cw.promote("CW_PARSE_RETROSPECTIVE",
                      prospective_vectors=5) == \
        "CW_PARSE_PROSPECTIVE_SUPPORT"


def test_semantics_needs_command_correlation_and_replication():
    s = "CW_PARSE_PROSPECTIVE_SUPPORT"
    assert cw.promote(s) == s
    assert cw.promote(s, controlled_command_correlation=True) == s
    assert cw.promote(s, controlled_command_correlation=True,
                      independent_replication=True) == \
        "CW_SEMANTICS_CONFIRMED"


def test_unknown_status_rejected():
    with pytest.raises(ValueError):
        cw.promote("CW_OBVIOUSLY_ALIEN")


def test_ladder_has_a_rejection_terminal():
    assert "CW_SEMANTICS_REJECTED" in r7.CW_STATUSES


# --- headline ---------------------------------------------------------

def test_status_report_ceiling_is_retrospective():
    rep = cw.status_report()
    assert rep["status"] == "CW_PARSE_RETROSPECTIVE"
    assert rep["ceiling"] == "CW_PARSE_RETROSPECTIVE"


def test_status_report_states_it_discriminates_nothing():
    rep = cw.status_report()
    assert rep["informative_bits"] == 0
    assert "not at all" in rep["verdict"]


def test_status_report_says_what_would_settle_it():
    rep = cw.status_report()
    assert "Prospective" in rep["what_would_settle_it"]
    assert "Nothing retrospective" in rep["what_would_settle_it"]


def test_forbidden_collapse_is_declared():
    assert "SHARED_PREFIX_IS_SHARED_PROTOCOL" in r7.FORBIDDEN_COLLAPSES
    assert "PARSE_COMPATIBILITY_IS_ENCODING" in r7.FORBIDDEN_COLLAPSES
