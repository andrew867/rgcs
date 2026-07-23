"""R11 — moving-shell observations and binary-to-octal address envelopes.

Every test can fail: the reference conversions are asserted against the
literal reference numbers, the refusals are asserted to raise, and the
lossy envelope is asserted to lose a specific, counted number of bits."""

from __future__ import annotations

import pytest

from r11 import shelladdr as S


# --- Part 1: the moving shell sequence ---------------------------------

REFERENCE = {
    3478: (5597.298432, 1.8785576437760974),
    1903: (3062.581632, 1.4807059218245868),
    1238: (1992.367872, 1.3127240836672824),
}

TOL = 1e-9


def test_mile_is_exactly_1_609344_km():
    assert float(S.MILE_KM) == 1.609344
    assert S.miles_to_km(1) == S.MILE_KM
    assert S.km_to_miles(S.miles_to_km(3478)) == 3478


def test_reference_kilometres_reproduce():
    for miles, (ref_km, _ref_re) in REFERENCE.items():
        got = float(S.miles_to_km(miles))
        assert abs(got - ref_km) < TOL, (miles, got, ref_km)


def test_reference_earth_radii_reproduce():
    for miles, (_ref_km, ref_re) in REFERENCE.items():
        got = float(S.radius_in_earth_radii(miles))
        assert abs(got - ref_re) < TOL, (miles, got, ref_re)


def test_earth_radius_used_is_the_one_that_reproduces():
    # 3958.7613 mi == 6371.0087455872 km, asserted consistently
    assert float(S.EARTH_RADIUS_MI) == 3958.7613
    assert abs(float(S.EARTH_RADIUS_KM) - 6371.0087455872) < 1e-9


def test_rounded_6371_does_not_reproduce_and_is_documented():
    """POWER: a rounded R_E genuinely misses, and the check catches it."""
    chk = S.reference_radius_check()
    assert chk["all_km_match"] is True
    assert chk["all_earth_radii_match"] is True
    assert chk["rounded_6371_reproduces"] is False
    row = chk["rows"][0]
    assert abs(row["rounded_6371_earth_radii"]
               - row["reference_earth_radii"]) > TOL


def test_sequence_is_ordered_inward():
    assert S.is_ordered_inward() is True
    ranges = [int(o.range_miles) for o in S.MOVING_SHELL_SEQUENCE_A]
    assert ranges == [3478, 1903, 1238]


def test_ordered_inward_can_fail():
    outward = tuple(reversed(S.MOVING_SHELL_SEQUENCE_A))
    assert S.is_ordered_inward(outward) is False


def test_timestamps_are_explicitly_none():
    rec = S.sequence_record()
    assert rec["timestamps"] is None
    assert rec["timestamp_class"] == "TIMESTAMPS_MISSING"
    assert rec["order_class"] == "CANDIDATE_ORDER"
    assert rec["derived_kinematics"] is None
    assert all(o.timestamp is None for o in S.MOVING_SHELL_SEQUENCE_A)


def test_refuse_speed_raises():
    with pytest.raises(S.ShellAddrError):
        S.refuse_speed(S.MOVING_SHELL_SEQUENCE_A)


def test_refuse_orbit_raises():
    with pytest.raises(S.ShellAddrError):
        S.refuse_orbit(S.MOVING_SHELL_SEQUENCE_A)


def test_refuse_eta_raises():
    with pytest.raises(S.ShellAddrError):
        S.refuse_eta(S.MOVING_SHELL_SEQUENCE_A)


def test_refuse_reordering_raises():
    with pytest.raises(S.ShellAddrError):
        S.refuse_reordering(S.MOVING_SHELL_SEQUENCE_A, (2, 0, 1))


def test_refusals_say_why():
    with pytest.raises(S.ShellAddrError, match="time difference"):
        S.refuse_speed()
    with pytest.raises(S.ShellAddrError, match="CANDIDATE order"):
        S.refuse_reordering()


# --- Part 2: the address and its renderings ----------------------------

def test_candidate_vector_bit_length_is_39():
    assert S.CANDIDATE_VECTOR_A == 344478312553
    assert S.CANDIDATE_VECTOR_A.bit_length() == 39


def test_octal_and_binary_strings_match_int_conversions():
    v = S.CANDIDATE_VECTOR_A
    assert format(v, "o") == S.CANDIDATE_VECTOR_A_OCTAL
    assert format(v, "b") == S.CANDIDATE_VECTOR_A_BINARY
    assert int(S.CANDIDATE_VECTOR_A_OCTAL, 8) == v
    assert int(S.CANDIDATE_VECTOR_A_BINARY, 2) == v


def test_vector_consistency_reports_all_four_agree():
    c = S.vector_consistency()
    assert c["all_consistent"] is True
    assert c["bit_length"] == 39
    assert c["decimal_digits"] == 12
    assert c["fits_40_bit_payload"] is True


def test_vector_consistency_can_fail():
    """POWER: a wrong octal string is detected, not waved through."""
    c = S.vector_consistency(octal="5006440364152")
    assert c["octal_matches"] is False
    assert c["all_consistent"] is False


# --- envelope 1: 42-bit decimal preserving -----------------------------

def test_envelope42_round_trips_exactly():
    for header in range(4):
        for v in (0, 1, S.CANDIDATE_VECTOR_A, 10 ** 12 - 1, 999999999999):
            s = S.encode_envelope42(v, header)
            assert S.decode_envelope42(s) == (header, v)


def test_envelope42_serializes_to_exactly_14_octal_digits():
    for v in (0, S.CANDIDATE_VECTOR_A, 10 ** 12 - 1):
        s = S.encode_envelope42(v, 3)
        assert len(s) == 14
        assert set(s) <= set("01234567")
    assert S.ENV42_OCTAL_DIGITS * 3 == S.ENV42_TOTAL_BITS == 42


def test_envelope42_account_is_lossless():
    a = S.envelope42_account()
    assert a["loss_class"] == "LOSSLESS"
    assert a["bits_lost"] == 0
    assert a["round_trip"] is True
    assert a["serialized_length"] == 14
    assert a["lower_holds"] and a["upper_holds"]


def test_envelope42_rejects_bad_fields():
    with pytest.raises(S.ShellAddrError):
        S.encode_envelope42(10 ** 12)                # too large
    with pytest.raises(S.ShellAddrError):
        S.encode_envelope42(-1)
    with pytest.raises(S.ShellAddrError):
        S.encode_envelope42(1, 4)                    # header is 2 bits
    with pytest.raises(S.ShellAddrError):
        S.decode_envelope42("5006440364151")         # 13 digits, not 14


# --- envelope 2: 36-bit HCM-native, LOSSY ------------------------------

def test_envelope36_loses_three_bits_and_accounts_for_them():
    a = S.envelope36_loss_account()
    assert a["loss_class"] == "LOSSY"
    assert a["bits_required"] == 39
    assert a["bits_available"] == 36
    assert a["bits_lost"] == 3
    assert a["bits_lost"] > 0
    assert a["aliasing_factor"] == 8
    assert a["exact_round_trip"] is False
    assert "most significant" in a["what_is_truncated"]


def test_envelope36_serializes_to_12_octal_digits_and_does_not_recover():
    s = S.encode_envelope36()
    assert len(s) == 12
    assert set(s) <= set("01234567")
    assert S.decode_envelope36(s) != S.CANDIDATE_VECTOR_A
    assert S.decode_envelope36(s) == S.CANDIDATE_VECTOR_A & ((1 << 36) - 1)


def test_envelope36_is_lossless_for_a_small_value():
    """POWER: the accounting is value-dependent, not hardcoded."""
    a = S.envelope36_loss_account(12345)
    assert a["bits_lost"] == 0
    assert a["loss_class"] == "LOSSLESS"
    assert a["exact_round_trip"] is True


def test_refuse_lossy_as_lossless_raises():
    with pytest.raises(S.ShellAddrError):
        S.refuse_lossy_as_lossless(S.CANDIDATE_VECTOR_A)


def test_refuse_lossy_as_lossless_names_the_lost_bits():
    with pytest.raises(S.ShellAddrError, match="3 high bit"):
        S.refuse_lossy_as_lossless()


# --- envelope 3: seven-field mixed radix -------------------------------

def test_mixed_radix_has_seven_declared_fields():
    assert len(S.MIXED_RADIX_FIELDS) == 7
    assert S.MIXED_RADIX_FIELD_NAMES == (
        "shell", "face", "local_coord", "phase", "epoch_class",
        "parity", "revision")
    assert all(r > 1 for _n, r in S.MIXED_RADIX_FIELDS)


def test_mixed_radix_round_trips_exactly():
    cases = [
        (0,) * 7,
        (7, 5, 67108863, 3, 2, 1, 15),
        (3, 1, 12345, 2, 0, 1, 9),
    ]
    for fields in cases:
        code = S.mixed_radix_encode(fields)
        assert S.mixed_radix_decode(code) == fields


def test_mixed_radix_round_trips_the_candidate_vector():
    v = S.CANDIDATE_VECTOR_A
    fields = S.mixed_radix_decode(v)
    assert len(fields) == 7
    assert S.mixed_radix_encode(fields) == v
    a = S.mixed_radix_account(v)
    assert a["round_trip"] is True
    assert a["bits_lost"] == 0
    assert a["field_count"] == 7
    assert a["capacity"] > v


def test_mixed_radix_top_code_is_capacity_minus_one():
    top = tuple(r - 1 for _n, r in S.MIXED_RADIX_FIELDS)
    assert S.mixed_radix_encode(top) == S.mixed_radix_capacity() - 1


def test_mixed_radix_rejects_out_of_range_fields():
    with pytest.raises(S.ShellAddrError):
        S.mixed_radix_encode((8, 0, 0, 0, 0, 0, 0))     # shell radix 8
    with pytest.raises(S.ShellAddrError):
        S.mixed_radix_encode((0, 0, 0, 0, 0, 2, 0))     # parity radix 2
    with pytest.raises(S.ShellAddrError):
        S.mixed_radix_encode((0, 0, 0, 0, 0, 0))        # six fields


# --- envelope 4: negative controls -------------------------------------

def test_bcd_round_trips_and_is_wider_than_the_packed_form():
    v = S.CANDIDATE_VECTOR_A
    bits = S.bcd_encode(v)
    assert len(bits) == 48
    assert S.bcd_decode(bits) == v
    assert len(bits) > S.ENV42_PAYLOAD_BITS


def test_reversal_control_round_trips_and_is_an_involution():
    v = S.CANDIDATE_VECTOR_A
    r = S.reverse_control(v)
    assert S.reverse_control_invert(r) == v
    assert S.reverse_control(S.reverse_control_invert(r)) == r


def test_negative_control_account_states_they_reveal_nothing():
    a = S.negative_control_account()
    assert a["bcd_round_trip"] is True
    assert a["reversal_round_trip"] is True
    assert a["reversal_is_involution"] is True
    assert "nothing" in a["why_controls"]


def test_bcd_rejects_an_invalid_nibble():
    bad = "1111" + "0000" * 11
    with pytest.raises(S.ShellAddrError):
        S.bcd_decode(bad)


# --- octal hygiene -----------------------------------------------------

def test_refuse_decimal_digits_as_octal_raises_on_8_or_9():
    with pytest.raises(S.ShellAddrError):
        S.refuse_decimal_digits_as_octal("344478312553")     # has 8
    with pytest.raises(S.ShellAddrError):
        S.refuse_decimal_digits_as_octal("109")              # has 9
    with pytest.raises(S.ShellAddrError, match="not octal symbols"):
        S.refuse_decimal_digits_as_octal("89")


def test_a_clean_octal_string_is_not_refused():
    assert S.refuse_decimal_digits_as_octal("5006440364151") is None
    assert S.parse_octal("5006440364151") == S.CANDIDATE_VECTOR_A


def test_parse_octal_refuses_a_decimal_string():
    with pytest.raises(S.ShellAddrError):
        S.parse_octal(str(S.CANDIDATE_VECTOR_A))


# --- no retrofit -------------------------------------------------------

def test_refuse_header_semantics_from_target_raises():
    with pytest.raises(S.ShellAddrError):
        S.refuse_header_semantics_from_target(S.CANDIDATE_VECTOR_A,
                                              header=0)


def test_refuse_header_semantics_points_at_synthetic_holdouts():
    with pytest.raises(S.ShellAddrError, match="SYNTHETIC holdouts"):
        S.refuse_header_semantics_from_target()


def test_synthetic_holdouts_are_deterministic_and_not_the_target():
    a = S.synthetic_holdout_vectors(8)
    b = S.synthetic_holdout_vectors(8)
    assert a == b
    assert len(set(a)) == 8
    assert S.CANDIDATE_VECTOR_A not in a
    assert all(0 <= v < 10 ** 12 for v in a)


# --- fingerprint and report --------------------------------------------

def test_address_fingerprint_is_stable_and_value_sensitive():
    f1 = S.address_fingerprint()
    assert f1 == S.address_fingerprint()
    assert f1 != S.address_fingerprint(S.CANDIDATE_VECTOR_A + 1)


def test_report_measures_nothing_and_carries_the_verdict():
    r = S.shelladdr_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == \
        "MOVING_SHELL_SEQUENCE_RETAINED_WITHOUT_KINEMATICS"
    assert r["evidence_class"]


def test_report_states_what_it_does_not_say():
    w = S.shelladdr_report()["what_this_does_not_say"]
    assert "MISSING timestamps" in w
    assert "necessary but never sufficient" in w
    assert "CANDIDATE order" in w


def test_report_lists_every_refusal():
    r = S.shelladdr_report()
    for name in ("refuse_speed", "refuse_orbit", "refuse_eta",
                 "refuse_reordering", "refuse_lossy_as_lossless",
                 "refuse_decimal_digits_as_octal",
                 "refuse_header_semantics_from_target"):
        assert name in r["refusals"]
        assert callable(getattr(S, name))
