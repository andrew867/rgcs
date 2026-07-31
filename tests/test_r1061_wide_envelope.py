"""R10.61 -- golden fixture tests for the wide-envelope codec.

The spec's quoted values are asserted, not trusted. If the parser ever
stops reproducing them these fail rather than silently re-framing.
"""

import pytest

from rgcs_archive import (FORBIDDEN_CLASSES, RESULT_CLASSES, text_lanes,
                          wide_envelope as W)


# ------------------------------------------------- golden fixture

def test_exact_decimal_record():
    assert W.FIXTURE_RECORD == "1687549873523387598456323376543328567433"
    assert len(W.FIXTURE_RECORD) == 40


def test_exact_stripped_payload():
    f = W.strip_framing(W.FIXTURE_RECORD)
    assert f["payload_decimal"] == "8754987352338759845632337654332856743"
    assert f["payload_digits"] == 37
    assert f["header"] == "16" and f["terminal"] == "3"


def test_123_significant_payload_bits():
    p = W.parse_record(W.FIXTURE_RECORD)
    assert p["significant_bits"] == 123


def test_126_bit_left_padded_envelope():
    p = W.parse_record(W.FIXTURE_RECORD)
    assert p["padded_width_bits"] == 126
    assert p["pad_bits"] == 3
    assert W.legal_width(126)


def test_the_pad_convention_is_recorded_because_123_is_also_legal():
    """123 = 21 + 3(34) is itself legal; the spec still pads to 126.

    That is a real choice, not arithmetic, and it changes D from 34 to 35.
    """
    p = W.parse_record(W.FIXTURE_RECORD)
    assert W.legal_width(123)
    assert p["significant_bits_are_themselves_a_legal_width"] is True
    assert p["pad_convention"] == "REQUIRE_AT_LEAST_ONE_PAD_BIT"
    assert W.next_legal_width(123, require_pad=False) == 123
    assert W.next_legal_width(123, require_pad=True) == 126


def test_exact_42_digit_octal_payload():
    p = W.parse_record(W.FIXTURE_RECORD)
    assert p["payload_octal"] == \
        "064542306375724625654273330377576404214647"
    assert p["octal_digits"] == 42


def test_D_equals_35():
    p = W.parse_record(W.FIXTURE_RECORD)
    assert p["D"] == 35
    assert p["padded_width_bits"] == 21 + 3 * p["D"]


def test_exactly_36_legal_splits():
    p = W.parse_record(W.FIXTURE_RECORD)
    splits = W.enumerate_splits(p["payload_octal"])
    assert p["legal_splits"] == 36
    assert len(splits) == 36
    assert [s["d_left"] for s in splits] == list(range(36))


def test_no_accidental_four_word_authority():
    """The record is ONE envelope. Four-block segmentations were an
    artifact of leaving the framing bits in."""
    p = W.parse_record(W.FIXTURE_RECORD)
    assert p["result_class"] == "RGCS_ENVELOPE_CANDIDATE"
    assert p["header_count_in_record"] == 1
    for s in W.enumerate_splits(p["payload_octal"]):
        assert s["authority"] == "STRUCTURAL_PARSE_ONLY"


def test_no_split_is_selected():
    p = W.parse_record(W.FIXTURE_RECORD)
    assert p["selected_split"] is None
    splits = W.enumerate_splits(p["payload_octal"])
    assert not any("rank" in s or "score" in s for s in splits)


def test_fixture_receipt_reproduces_every_quoted_value():
    r = W.fixture_receipt()
    assert r["all_match"]
    assert all(c["match"] for c in r["checks"].values())


# --------------------------------------- the superseded R10.63 payload

def test_the_superseded_payload_is_recorded_and_rejected():
    """R10.63 stripped the terminal in octal space. Different number."""
    p = W.parse_record(W.FIXTURE_RECORD)
    assert W.SUPERSEDED_PAYLOAD_OCTAL != p["payload_octal"]
    assert len(W.SUPERSEDED_PAYLOAD_OCTAL) == 42        # same length!
    assert "octal space" in W.SUPERSEDED_REASON
    r = W.fixture_receipt()
    assert r["superseded_payload_rejected"] == W.SUPERSEDED_PAYLOAD_OCTAL


# ------------------------------------------------------- properties

def test_dL_plus_dR_always_equals_D():
    p = W.parse_record(W.FIXTURE_RECORD)
    for s in W.enumerate_splits(p["payload_octal"]):
        assert s["d_left"] + s["d_right"] == p["D"]
        assert len(s["chain_left"]) + len(s["chain_right"]) == p["D"]


def test_padding_removal_restores_the_original_payload_integer():
    p = W.parse_record(W.FIXTURE_RECORD)
    assert int(p["payload_octal"], 8) == p["payload_int"]
    assert int(p["payload_decimal"]) == p["payload_int"]


def test_core_fields_fit_their_declared_widths():
    p = W.parse_record(W.FIXTURE_RECORD)
    for s in W.enumerate_splits(p["payload_octal"]):
        assert 0 <= s["E3"] < 8                    # 3 bits
        for k in ("S_tor", "S_pol", "S_rad"):
            assert 0 <= s[k] < 64                  # 6 bits


def test_bit_ranges_tile_the_payload_without_gaps():
    p = W.parse_record(W.FIXTURE_RECORD)
    n = p["padded_width_bits"]
    for s in W.enumerate_splits(p["payload_octal"]):
        assert s["bits_chain_left"][0] == 0
        assert s["bits_chain_left"][1] == s["bits_core"][0]
        assert s["bits_core"][1] == s["bits_chain_right"][0]
        assert s["bits_chain_right"][1] == n


def test_reversed_chains_are_recorded_for_both_directions():
    p = W.parse_record(W.FIXTURE_RECORD)
    s = W.split_at(p["payload_octal"], 17)
    assert s["chain_left_reversed"] == s["chain_left"][::-1]
    assert s["chain_right_reversed"] == s["chain_right"][::-1]


def test_width_law_holds_for_a_range_of_D():
    for d in range(0, 60):
        w = 21 + 3 * d
        assert W.legal_width(w)
        assert not W.legal_width(w + 1)
        assert not W.legal_width(w + 2)


# ------------------------------------------------------ guard rails

def test_records_without_framing_are_refused():
    with pytest.raises(W.EnvelopeError, match="header"):
        W.parse_record("99999999999999999993")
    with pytest.raises(W.EnvelopeError, match="terminal"):
        W.parse_record("1687549873523387598456323376543328567439")
    with pytest.raises(W.EnvelopeError, match="not a decimal"):
        W.parse_record("16abc3")


def test_out_of_range_split_is_refused():
    p = W.parse_record(W.FIXTURE_RECORD)
    with pytest.raises(W.EnvelopeError):
        W.split_at(p["payload_octal"], 99)


def test_there_is_no_discovery_state():
    for bad in FORBIDDEN_CLASSES:
        assert bad not in RESULT_CLASSES


# --------------------------------------------------- text lanes

def test_text_lanes_run_but_do_not_promote_plaintext():
    """Regression expectation: no conventional text survives the null."""
    p = W.parse_record(W.FIXTURE_RECORD)
    a = text_lanes.assess(p["payload_octal"], trials=60)
    assert a["hypotheses_searched"] > 100
    assert a["survives_null"] is False
    assert a["result_class"] == "NULL_COMPATIBLE"


def test_radix50_uses_three_chars_per_sixteen_bits():
    bits = "0" * 16
    assert len(text_lanes.decode(bits, "radix50")) == 3


def test_cdc_and_dec_six_bit_tables_are_distinct():
    bits = "".join(format(v, "06b") for v in range(1, 20))
    assert text_lanes.decode(bits, "sixbit_dec") != \
        text_lanes.decode(bits, "cdc_display")


def test_scoring_rejects_a_printable_but_meaningless_string():
    s = text_lanes.score("3UDDB-50PA_FTPP]>(JP\")")
    assert s["printable"] == 1.0          # printable...
    assert s["trigrams"] == 0             # ...and still not text
