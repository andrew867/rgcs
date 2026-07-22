"""P00/P07 — the base-10 unpacking codec search."""

from __future__ import annotations

import pytest

from r10 import base10 as B


# --- the vectors are preserved -----------------------------------------

def test_the_five_vectors_are_preserved_byte_for_byte():
    assert B.CW_VECTORS == (162875493612, 162875432975, 162877542769,
                            162875439275, 162875439285)
    assert all(len(str(v)) == 12 for v in B.CW_VECTORS)


# --- octal is not assumed ----------------------------------------------

def test_octal_reading_is_refused():
    with pytest.raises(B.OctalAssumptionRefused) as e:
        B.refuse_octal_assumption()
    msg = str(e.value)
    assert "does not specify base 8" in msg
    assert "digits 8 and 9" in msg          # the vectors aren't octal


# --- every codec is exactly reversible ---------------------------------

def test_all_codecs_round_trip_every_vector():
    rt = B.all_codecs_round_trip()
    assert all(rt.values()), rt
    assert set(rt) == {"A_SYMBOL", "B_TRIADS", "C_TETRADS",
                       "D_PACKED_BINARY", "E_BCD"}


def test_a_reversible_codec_really_inverts():
    for c in B.CODECS:
        for v in B.CW_VECTORS:
            assert c.inverse(c.forward(v)) == v


def test_bcd_rejects_invalid_nibbles():
    """A>9 nibble is not valid BCD and must be refused on decode."""
    bad = "1010" + "0" * 44          # 1010 = 10, invalid BCD
    with pytest.raises(B.CodecError):
        B._unview_bcd(bad)


def test_packed_binary_rejects_out_of_range():
    with pytest.raises(B.CodecError):
        B._view_packed_binary(10 ** 12)


# --- the exact bit-width facts -----------------------------------------

def test_packed_decimal_needs_forty_bits():
    p = B.packed_decimal_bits()
    assert p["bits"] == 40
    assert p["lower_holds"] and p["upper_holds"]


def test_bcd_needs_forty_eight_bits():
    assert B.bcd_bits() == 48


# --- the search: band is real, content is not --------------------------

def test_the_band_clustering_is_real():
    r = B.codec_search(null_trials=4000)
    assert r["band_verdict"] == "CLUSTERED_BAND_CONFIRMED"
    assert r["band_p_value"] < 0.05


def test_no_content_survives_a_span_matched_null():
    """The R9 lesson: the shared 16287 prefix is the band, reproduced
    by the span-matched null, so no reversible view exposes content."""
    r = B.codec_search(null_trials=4000)
    assert r["verdict"] == "NO_DECODER_IDENTIFIED"
    assert r["content_p_value"] > 0.05


def test_a_reversible_view_cannot_change_the_structure_score():
    """The whole argument: recoding preserves information. The BCD and
    triad views of the same integer carry the same structure."""
    # structure is computed on the integers, which the codecs preserve
    assert B._informative_structure(B.CW_VECTORS) == 5   # the 16287 prefix


def test_all_failed_interpretations_are_retained():
    r = B.codec_search(null_trials=1000)
    assert set(r["failed_interpretations_retained"]) == \
        {c.codec_id for c in B.CODECS}


# --- claim discipline --------------------------------------------------

def test_report_says_no_decoder_identified_not_impossible():
    r = B.base10_report()
    w = r["what_this_does_not_say"]
    assert "NO_DECODER_IDENTIFIED, not NO_DECODER_POSSIBLE" in w
    assert r["measured_here"] == "nothing"


def test_report_preserves_the_vectors():
    r = B.base10_report()
    assert r["vectors_preserved_byte_for_byte"] == list(B.CW_VECTORS)
