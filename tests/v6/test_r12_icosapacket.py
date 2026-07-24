"""R12 — the icosahedral packet grammar F5 | Q22 | S3.

Every test can fail: the five registered vectors are asserted to decode
to the exact face/path/shell/octal listed, the field widths are asserted
to sum to thirty, the refusals are asserted to raise, and the
band-clustering null is asserted to explain the shared prefix while a
planted prefix is asserted to be flagged."""

from __future__ import annotations

import pytest

from r12 import icosapacket as P


# --- field widths ------------------------------------------------------

def test_field_widths_sum_to_thirty():
    w = P.field_widths()
    assert P.FACE_BITS == 5
    assert P.PATH_BITS == 22
    assert P.SHELL_BITS == 3
    assert P.WORD_CAPACITY_BITS == 30
    assert w["word_bits_sum_exactly"] is True
    assert w["face_bits_are_minimal"] is True
    assert w["shell_field_is_exactly_full"] is True
    assert w["octal_digits_exact"] is True
    assert P.WORD_OCTAL_DIGITS == 10


def test_quaternary_path_is_eleven_two_bit_levels():
    assert P.QUATERNARY_LEVELS == 11
    assert P.QUATERNARY_LEVELS * 2 == P.PATH_BITS


def test_shell_field_holds_exactly_eight():
    assert P.SHELL_COUNT == 8
    assert (1 << P.SHELL_BITS) == P.SHELL_COUNT


# --- the five registered vectors, exactly ------------------------------

EXPECTED = {
    165879123: (4, "33012032222", 3, "1170616523"),
    165829763: (4, "33010232100", 3, "1170456203"),
    165874293: (4, "33012011032", 5, "1170605165"),
    165878965: (4, "33012032112", 5, "1170616265"),
    165879253: (4, "33012032322", 5, "1170616725"),
}


@pytest.mark.parametrize("value,expected", list(EXPECTED.items()))
def test_registered_vectors_decode_exactly(value, expected):
    face, path, shell = P.decode(value)
    assert (face, path, shell) == expected[:3]
    assert P.word_octal(value) == expected[3]


def test_registered_vectors_all_verify():
    result = P.verify_registered_vectors()
    assert result["all_verified"] is True
    assert result["count"] == 5


def test_registered_vectors_decode_face_four():
    for value in EXPECTED:
        assert P.decode(value)[0] == 4


# --- encode / decode round trip ----------------------------------------

@pytest.mark.parametrize("value", list(EXPECTED))
def test_encode_decode_round_trip(value):
    face, path, shell = P.decode(value)
    assert P.encode(face, path, shell) == value


def test_encode_decode_round_trip_exhaustive_sample():
    # A deterministic spread across the field space.
    for face in range(P.FACE_COUNT):
        for shell in range(P.SHELL_COUNT):
            path = "".join(str((face + shell + k) % 4)
                           for k in range(P.QUATERNARY_LEVELS))
            word = P.encode(face, path, shell)
            assert P.decode(word) == (face, path, shell)


def test_encode_accepts_int_tuple_path():
    face, path, shell = P.decode(165879123)
    levels = P.path_levels(path)
    assert P.encode(face, levels, shell) == 165879123


# --- face range refusal ------------------------------------------------

@pytest.mark.parametrize("face", [20, 27, 31])
def test_face_at_or_above_twenty_refused_on_encode(face):
    with pytest.raises(P.IcosaPacketError):
        P.encode(face, "0" * 11, 0)


def test_out_of_range_face_word_refused_on_decode():
    # Build a word whose face field is 20 by hand and confirm decode
    # refuses it rather than folding it onto a face.
    word = (20 << (P.PATH_BITS + P.SHELL_BITS)) | 0
    with pytest.raises(P.IcosaPacketError):
        P.decode(word)


def test_shell_must_fit_three_bits():
    with pytest.raises(P.IcosaPacketError):
        P.encode(0, "0" * 11, 8)
    # 0..7 are all accepted
    for shell in range(8):
        assert P.decode(P.encode(0, "0" * 11, shell))[2] == shell


def test_path_level_out_of_range_refused():
    with pytest.raises(P.IcosaPacketError):
        P.encode(0, "40000000000", 0)      # a 4 is not quaternary
    with pytest.raises(P.IcosaPacketError):
        P.encode(0, "3301203222", 0)       # only ten levels


# --- both layouts, neither privileged ----------------------------------

def test_layouts_returns_both():
    lys = P.layouts()
    assert len(lys) == 2
    ids = {ly.layout_id for ly in lys}
    assert ids == {"F5_Q22_S3", "H13_L14_S3"}
    for ly in lys:
        assert ly.total_bits == P.WORD_CAPACITY_BITS


def test_alt_layout_field_widths():
    assert P.ALT_HEADER_BITS == 13
    assert P.ALT_LOCAL_BITS == 14
    assert P.ALT_SHELL_BITS == 3
    assert P.ALT_HEADER_BITS + P.ALT_LOCAL_BITS + P.ALT_SHELL_BITS == 30


def test_refuse_single_layout_raises_without_preregistration():
    with pytest.raises(P.IcosaPacketError):
        P.refuse_single_layout()
    with pytest.raises(P.IcosaPacketError):
        P.refuse_single_layout(None)


def test_refuse_single_layout_returns_preregistered():
    ly = P.refuse_single_layout("F5_Q22_S3")
    assert ly.layout_id == "F5_Q22_S3"


def test_refuse_single_layout_rejects_unknown_id():
    with pytest.raises(P.IcosaPacketError):
        P.refuse_single_layout("NOT_A_LAYOUT")


def test_layout_table_has_no_privileged_layout():
    table = P.layout_table(165879123)
    assert table["privileged_layout"] is None
    assert set(table["layouts"]) == {"F5_Q22_S3", "H13_L14_S3"}


# --- the shared prefix and the band null -------------------------------

def test_shared_prefix_is_thirteen_bits():
    assert P.shared_prefix_bits(P.REGISTERED_VALUES) == 13


def test_prefix_expected_from_range_matches_span():
    acc = P.prefix_expected_from_range(P.REGISTERED_VALUES)
    assert acc["span"] == max(P.REGISTERED_VALUES) - min(P.REGISTERED_VALUES) + 1
    # The observed 13-bit prefix does NOT exceed what the band forces.
    assert acc["observed_prefix_bits"] == 13
    assert acc["observed_exceeds_expected"] is False
    assert acc["excess_over_expected"] <= 0


def test_common_prefixes_in_four_bases():
    acc = P.prefix_account()
    assert acc["binary_prefix_bits"] == 13
    assert acc["decimal_prefix"] == "1658"
    assert acc["octal_prefix"] == "1170"
    assert acc["path_prefix"] == "3301"


def test_band_clustering_null_explained_by_range():
    null = P.band_clustering_null(P.REGISTERED_VALUES)
    assert null["verdict"] == "EXPLAINED_BY_RANGE"
    assert null["explained_by_range"] is True
    assert null["p_value"] > P.PREFIX_ALPHA
    # random same-band values share a comparable prefix
    assert null["null_mean_prefix_bits"] >= 12.0


def test_power_control_flags_a_planted_prefix():
    """POWER: a prefix wider than the band explains is detected."""
    power = P.power_control_planted_prefix(prefix_bits=24)
    assert power["detected"] is True
    assert power["explained_by_range"] is False
    assert power["observed_prefix_bits"] >= 24


def test_refuse_prefix_as_content_raises():
    with pytest.raises(P.IcosaPacketError):
        P.refuse_prefix_as_content()
    with pytest.raises(P.IcosaPacketError):
        P.refuse_prefix_as_content(P.REGISTERED_VALUES)


# --- collision audit ---------------------------------------------------

def test_collision_scan_finds_none_on_registered():
    scan = P.collision_scan(P.REGISTERED_VALUES)
    assert scan["injective"] is True
    assert scan["collision_count"] == 0


def test_collision_scan_finds_none_on_wide_sample():
    words = [P.encode(f, "".join(str((f + k) % 4)
                                 for k in range(11)), s)
             for f in range(P.FACE_COUNT) for s in range(P.SHELL_COUNT)]
    scan = P.collision_scan(words)
    assert scan["injective"] is True
    assert scan["distinct_decodes"] == len(words)


# --- octal hygiene -----------------------------------------------------

def test_refuse_decimal_digits_as_octal_raises_on_8_and_9():
    with pytest.raises(P.IcosaPacketError):
        P.refuse_decimal_digits_as_octal("1170618523")   # contains 8
    with pytest.raises(P.IcosaPacketError):
        P.refuse_decimal_digits_as_octal("1170916523")   # contains 9


def test_refuse_decimal_digits_as_octal_accepts_valid_octal():
    # A clean octal string does not raise.
    P.refuse_decimal_digits_as_octal("1170616523")


def test_octal_round_trip_via_parse():
    for value in EXPECTED:
        octal = P.word_octal(value)
        assert P.parse_octal_word(octal) == value


# --- geographic decode discipline --------------------------------------

def test_refuse_geographic_decode_always_raises():
    with pytest.raises(P.IcosaPacketError):
        P.refuse_geographic_decode()
    with pytest.raises(P.IcosaPacketError):
        P.refuse_geographic_decode(165879123)


def test_decode_to_location_raises_with_any_prerequisite_unfrozen():
    # Default: nothing frozen.
    with pytest.raises(P.IcosaPacketError):
        P.decode_to_location(165879123)
    # Four of five frozen still raises.
    almost = P.DecodePrerequisites(
        face_numbering="FN_A", body_orientation="BO_A",
        magnetic_root="MR_A", handedness="RIGHT")     # shell_projection None
    assert almost.unfrozen() == ("shell_projection",)
    with pytest.raises(P.IcosaPacketError):
        P.decode_to_location(165879123, almost)


def test_decode_to_location_all_frozen_still_grammar_only():
    frozen = P.DecodePrerequisites(
        face_numbering="FN_A", body_orientation="BO_A",
        magnetic_root="MR_A", handedness="RIGHT",
        shell_projection="SP_A")
    assert frozen.all_frozen() is True
    result = P.decode_to_location(165879123, frozen)
    assert result["status"] == "GRAMMAR_ONLY_NO_GEOGRAPHIC_CLAIM"
    assert result["latitude"] is None
    assert result["longitude"] is None
    assert result["face"] == 4


def test_five_prerequisites_named():
    assert P.DECODE_PREREQUISITE_FIELDS == (
        "face_numbering", "body_orientation", "magnetic_root",
        "handedness", "shell_projection")
    assert len(P.DECODE_PREREQUISITE_FIELDS) == 5


# --- report ------------------------------------------------------------

def test_report_shape_and_verdict():
    rep = P.icosapacket_report()
    assert rep["verdict"] == (
        "ICOSAHEDRAL_PACKET_GRAMMAR_VALID_NOT_A_GEOGRAPHIC_DECODER")
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["claim_class"] in {c.value for c in P.ClaimClass}
    assert rep["registered_vectors"]["all_verified"] is True
    assert rep["band_clustering_null"]["verdict"] == "EXPLAINED_BY_RANGE"
    assert rep["privileged_layout"] is None
    assert "what_this_does_not_say" in rep


def test_no_private_content_in_module():
    import r12.icosapacket as mod
    text = open(mod.__file__, encoding="utf-8").read().lower()
    for bad in ("c:\\users", "private_do_not_commit", "andrew"):
        assert bad not in text
