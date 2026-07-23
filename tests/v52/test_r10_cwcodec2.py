"""P07 — the CW packed-decimal / mixed-radix codec V2 with null windows.

Generic 12-digit inputs only; no real CW vector is hardcoded here."""

from __future__ import annotations

import pytest

from r10 import cwcodec2 as C


# generic 12-digit fixtures (NOT the real CW vectors)
GENERIC = (
    100000000000, 123456789012, 999999999999, 314159265358,
    271828182845, 161803398874, 42, 0, 999999999998,
)


# --- packed decimal: 40-bit lossless round-trip ------------------------

def test_pack_unpack_round_trips_many_inputs():
    for n in GENERIC:
        assert C.unpack_decimal(C.pack_decimal(n)) == n


def test_pack_produces_a_40_bit_code():
    for n in GENERIC:
        assert 0 <= C.pack_decimal(n) < (1 << 40)


def test_pack_rejects_out_of_range():
    with pytest.raises(C.CodecError):
        C.pack_decimal(10 ** 12)
    with pytest.raises(C.CodecError):
        C.pack_decimal(-1)


def test_forty_bits_is_the_facts():
    p = C.packed_decimal_bits()
    assert p["bits"] == 40
    assert p["lower_holds"] and p["upper_holds"]


def test_thirty_nine_bits_is_insufficient():
    """39 bits cannot injectively hold 10**12 codes -- pigeonhole."""
    m = C.prove_bit_width_minimal()
    assert m["39_is_insufficient"] is True
    assert m["40_is_sufficient"] is True
    assert m["minimal_bits"] == 40
    assert m["capacity_39_bits"] < m["needed_values"]


# --- mixed radix: header + octal path round-trip -----------------------

def test_header_path_round_trips():
    cases = [
        (0, (0,) * 12),
        (15, (7,) * 12),
        (5, (1, 2, 3, 4, 5, 6, 7, 0, 1, 2, 3, 4)),
    ]
    for header, digits in cases:
        code = C.encode_header_path(header, digits)
        assert C.decode_header_path(code) == (header, digits)


def test_header_path_covers_the_full_40_bit_space():
    # header 0..15 (4 bits) and 12 octal digits (36 bits) => 40 bits
    top = C.encode_header_path(15, (7,) * 12)
    assert top == (1 << 40) - 1


def test_header_path_rejects_bad_fields():
    with pytest.raises(C.CodecError):
        C.encode_header_path(16, (0,) * 12)          # header too big
    with pytest.raises(C.CodecError):
        C.encode_header_path(0, (8,) * 12)           # 8 is not octal
    with pytest.raises(C.CodecError):
        C.encode_header_path(0, (0,) * 11)           # wrong length


def test_packed_and_header_path_are_the_same_40_bits():
    """The mixed-radix view is a relabeling of the packed integer."""
    n = 123456789012
    packed = C.pack_decimal(n)
    header, digits = C.decode_header_path(packed)
    assert C.encode_header_path(header, digits) == packed


# --- null windows ------------------------------------------------------

def test_masked_digits_stay_none_without_a_rule():
    mask = tuple(i in (0, 5, 11) for i in range(12))
    digs = C.masked_digits(123456789012, mask)
    assert digs[0] is None and digs[5] is None and digs[11] is None
    assert digs[1] == 2                              # unmasked untouched


def test_refuse_padding_without_rule_raises():
    mask = tuple(i == 3 for i in range(12))
    with pytest.raises(C.CodecError):
        C.refuse_padding_without_rule(mask)


def test_no_window_does_not_refuse():
    # an all-False mask has nothing to pad and must not raise
    assert C.refuse_padding_without_rule((False,) * 12) is None


def test_encode_vector_with_null_window_keeps_nulls():
    mask = tuple(i in (2, 7) for i in range(12))
    r = C.encode_vector("V", 123456789012, null_mask=mask)
    assert r.packed_integer is None
    assert r.octal_path is None
    assert r.round_trip is None
    assert r.prospective_status == "NULL_UNTIL_RULE_SUPPLIED"
    assert r.null_family == "NULL_WINDOW"


def test_explicit_padding_rule_fills_and_round_trips():
    mask = tuple(i in (2, 7) for i in range(12))
    rule = C.PaddingRule("R", {2: 4, 7: 9})
    r = C.encode_vector("V", 123456789012, null_mask=mask, padding_rule=rule)
    assert r.packed_integer is not None
    assert r.round_trip is True
    assert r.padding_rule == "R"
    assert r.prospective_status == "NO_PREREGISTERED_DECODER"
    # the fill came from the rule, not the raw digit under the mask
    digs = C.masked_digits(123456789012, mask, rule)
    assert digs[2] == 4 and digs[7] == 9


def test_padding_rule_must_cover_the_masked_position():
    mask = tuple(i in (2, 7) for i in range(12))
    rule = C.PaddingRule("R", {2: 4})               # 7 not covered
    with pytest.raises(C.CodecError):
        C.masked_digits(123456789012, mask, rule)


def test_encode_vector_without_window_round_trips():
    r = C.encode_vector("V", 314159265358)
    assert r.round_trip is True
    assert r.raw_decimal == 314159265358
    assert r.header_value is not None and r.octal_path is not None
    assert r.null_family == "NO_NULL_WINDOW"


# --- collision audit ---------------------------------------------------

def test_lossless_codec_has_no_collisions():
    scan = C.collision_scan(GENERIC, transform=C.pack_decimal)
    assert scan["injective"] is True
    assert scan["collisions"] == []
    assert scan["collision_class"] == "INJECTIVE"


def test_a_lossy_map_does_collide():
    """POWER: a truncating map DOES collide and the audit catches it."""
    # these two share their low 11 digits; dropping the top digit collides
    colliding = (123456789012, 923456789012)
    scan = C.collision_scan(colliding, transform=C.lossy_truncating_map)
    assert scan["injective"] is False
    assert scan["collision_class"] == "COLLIDING"
    assert scan["collisions"]


# --- relabeling --------------------------------------------------------

def test_two_radix_views_of_one_number_are_relabelings():
    n = 271828182845
    assert C.is_relabeling(C.octal_view(n), C.binary_view(n)) is True
    assert C.is_relabeling(C.decimal_view(n), C.octal_view(n)) is True


def test_views_of_different_numbers_are_not_relabelings():
    assert C.is_relabeling(C.octal_view(1), C.octal_view(2)) is False


# --- claim discipline --------------------------------------------------

def test_refuse_retrofit_decoding_raises():
    with pytest.raises(C.CodecError):
        C.refuse_retrofit_decoding("looks meaningful")


def test_report_measures_nothing_and_carries_the_verdict():
    r = C.cwcodec2_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["verdict"] == "REVERSIBLE_CODEC_NO_CONTENT"
    assert r["decoder_status"] == "NO_DECODER_IDENTIFIED"
    assert "NO_DECODER_IDENTIFIED, not NO_DECODER_POSSIBLE" in \
        r["what_this_does_not_say"]


def test_report_states_round_trip_is_necessary_not_sufficient():
    r = C.cwcodec2_report()
    w = r["what_this_does_not_say"]
    assert "necessary but never sufficient" in w


def test_result_fingerprint_is_stable():
    r = C.encode_vector("V", 161803398874)
    assert C.result_fingerprint(r) == C.result_fingerprint(r)
