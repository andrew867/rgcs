"""P23 -- checksums, versioning, error detection: focused, negative, deterministic."""

from __future__ import annotations

import pytest

from cwatlas import checksums as C

PAYLOAD = "v=1.0.0;codec=CW-GEO-1;body=EARTH;frame=ITRF2020;epoch=2020.0;lat=1;lon=2;h=0;shell=-"


# -- focused ----------------------------------------------------------------

def test_checksum_is_version_tagged():
    tag = C.checksum(PAYLOAD)
    assert tag.startswith(C.CHECKSUM_VERSION + ":")
    assert C.verify(PAYLOAD, tag)


def test_append_and_verify_round_trip():
    vector = C.append_checksum(PAYLOAD)
    assert C.verify_vector(vector)
    payload, tag = C.split_checksum(vector)
    assert payload == PAYLOAD
    assert C.verify(payload, tag)


def test_checksum_is_deterministic():
    assert C.checksum(PAYLOAD) == C.checksum(PAYLOAD)
    assert C.append_checksum(PAYLOAD) == C.append_checksum(PAYLOAD)


# -- negative: corruption detected ------------------------------------------

def test_single_char_corruption_fails_checksum():
    vector = C.append_checksum(PAYLOAD)
    # Flip one character in the payload region.
    corrupted = vector.replace("lat=1", "lat=2", 1)
    assert corrupted != vector
    assert not C.verify_vector(corrupted)


def test_corrupted_tag_fails():
    tag = C.checksum(PAYLOAD)
    bad = tag[:-1] + ("0" if tag[-1] != "0" else "1")
    assert not C.verify(PAYLOAD, bad)


def test_missing_separator_is_not_verifiable():
    assert not C.verify_vector(PAYLOAD)  # no checksum separator at all
    with pytest.raises(C.ChecksumError):
        C.split_checksum(PAYLOAD)


def test_wrong_checksum_version_is_rejected():
    tag = C.checksum(PAYLOAD)
    _, _, digest = tag.partition(":")
    stale = f"cwck0:{digest}"
    assert not C.verify(PAYLOAD, stale)


# -- version markers --------------------------------------------------------

def test_parse_codec_version():
    codec_id, version = C.parse_codec_version(C.append_checksum(PAYLOAD))
    assert codec_id == "CW-GEO-1"
    assert version == "1.0.0"


def test_require_version_passes_on_match():
    C.require_version(C.append_checksum(PAYLOAD), "CW-GEO-1", "1.0.0")


def test_version_mismatch_is_detected():
    vector = C.append_checksum(PAYLOAD)
    with pytest.raises(C.ChecksumError):
        C.require_version(vector, "CW-GEO-1", "2.0.0")
    with pytest.raises(C.ChecksumError):
        C.require_version(vector, "CW-HCM-ICO-1", "1.0.0")


def test_missing_version_marker_is_refused():
    with pytest.raises(C.ChecksumError):
        C.parse_codec_version("lat=1;lon=2")


# -- typo detection (Damm) --------------------------------------------------

def test_damm_check_digit_makes_valid_string():
    digits = "5117888218262150"
    check = C.damm_check_digit(digits)
    assert C.damm_is_valid(digits + str(check))


def test_damm_detects_single_digit_error():
    digits = "5117888218262150"
    check = C.damm_check_digit(digits)
    full = digits + str(check)
    # Corrupt one digit.
    bad = ("6" if full[3] != "6" else "7").join([full[:3], full[4:]])
    assert not C.damm_is_valid(bad)


def test_damm_detects_adjacent_transposition():
    digits = "12345"
    check = C.damm_check_digit(digits)
    full = digits + str(check)
    # Transpose two adjacent, distinct digits inside the payload.
    swapped = full[0] + full[2] + full[1] + full[3:]
    assert swapped != full
    assert not C.damm_is_valid(swapped)


# -- report -----------------------------------------------------------------

def test_report_claims_nothing_physical():
    r = C.checksums_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
