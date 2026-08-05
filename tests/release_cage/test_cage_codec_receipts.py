"""MOD-001 codec receipts -- the seven spec tests, wired for real.

Backed by rgcs_coordinate.codecs.variable_length_36 (structural parse
only; no physical endpoint anywhere in this lane).
"""

from __future__ import annotations

import pytest

from rgcs_coordinate.codecs import variable_length_36 as VL
from rgcs_workbench.public_cage import codec_receipts as CR


SAMPLE_FIELDS = [
    # (root, surface, path, epoch_groups, check)
    (0, 0, 0, (), 0),
    (5, 129, 3000, (), 7),
    (15, 255, 4095, (1,), 3),
    (7, 42, 1234, (2, 5), 6),
    (9, 200, 4000, (1, 2, 3), 0),
]


@pytest.mark.parametrize("root,surface,path,groups,check", SAMPLE_FIELDS)
def test_1_every_legal_parse_round_trips(root, surface, path, groups, check):
    word = VL.encode(root, surface, path, groups, check)
    receipt = CR.parse_receipt(word.value, width_bits=word.width_bits)
    assert receipt["legal_parse_status"] == CR.STATUS_LEGAL
    assert receipt["round_trip_ok"] is True
    assert receipt["round_trip_value"] == word.value


@pytest.mark.parametrize("bad_call", [
    lambda: CR.parse_receipt(-1),
    lambda: CR.parse_receipt(1 << 40),
    lambda: CR.parse_receipt(5, width_bits=28),
    lambda: CR.parse_receipt("12345"),
])
def test_2_every_rejected_parse_has_an_explicit_reason(bad_call):
    receipt = bad_call()
    assert receipt["legal_parse_status"] == CR.STATUS_REJECTED
    assert receipt["reject_reason"], "rejection must state its reason"
    assert receipt["receipt_hash"]


def test_3_no_parser_silently_changes_field_boundaries():
    word = VL.encode(11, 77, 2049, (4,), 5)
    receipt = CR.parse_receipt(word.value, width_bits=word.width_bits)
    split = receipt["candidate_field_split"]
    assert split == {"root": 11, "surface": 77, "path": 2049,
                     "epoch_groups": [4], "check_group": 5}
    bounds = receipt["field_boundaries"]
    assert bounds["root"] == [0, 4]
    assert bounds["surface"] == [4, 12]
    assert bounds["path"] == [12, 24]
    assert bounds["tail"][1] == word.width_bits


def test_4_fixed_width_diagnostic_parses_stay_marked_diagnostic():
    value = VL.encode(1, 2, 3, (), 4).value  # fits in 27 bits
    forced = CR.parse_receipt(value, width_bits=36)
    assert forced["framing"] == CR.FRAMING_DIAGNOSTIC
    natural = CR.parse_receipt(value)
    assert natural["framing"] == CR.FRAMING_INFERRED


def test_5_variable_depth_parses_emit_boundary_receipts():
    for groups in ((), (1,), (1, 2), (1, 2, 3)):
        word = VL.encode(3, 4, 5, groups, 6)
        receipt = CR.parse_receipt(word.value, width_bits=word.width_bits)
        assert receipt["field_boundaries"]["tail_bits"] == 3 * (len(groups) + 1)
        assert receipt["octal_stream"]
        assert receipt["binary_payload"] == word.bits


def test_6_raw_vectors_are_never_overwritten_by_corrections():
    ledger = CR.CorrectionLedger()
    raw = VL.encode(2, 3, 4, (), 1).value
    fixed = VL.encode(2, 3, 5, (), 1).value
    ledger.record_raw(raw, note="as received")
    ledger.record_correction(raw, fixed, reason="transcription slip in P12")
    assert raw in ledger.raw_values()
    kinds = [e["kind"] for e in ledger.entries()]
    assert kinds == ["RAW", "CORRECTED"]


def test_7_superseded_vectors_remain_in_the_ledger():
    ledger = CR.CorrectionLedger()
    raw = VL.encode(8, 9, 10, (7,), 2).value
    ledger.record_raw(raw)
    ledger.record_correction(raw, raw + 8, reason="check group re-read")
    raw_entry = ledger.entries()[0]
    assert raw_entry["status"] == "SUPERSEDED"
    assert raw_entry["value"] == raw
    with pytest.raises(ValueError):
        ledger.record_correction(raw + 999, raw, reason="never recorded")
    with pytest.raises(ValueError):
        ledger.record_correction(raw, raw + 16, reason="")


def test_receipts_carry_no_physical_projection():
    word = VL.encode(1, 1, 1, (), 1)
    receipt = CR.parse_receipt(word.value, width_bits=word.width_bits)
    assert receipt["physical_projection_status"] == "NOT_PERFORMED"
