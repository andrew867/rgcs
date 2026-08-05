"""MOD-003 crystal measurement objects -- the six spec tests."""

from __future__ import annotations

import uuid

import pytest

from rgcs_workbench.public_cage import claim_firewall as CF
from rgcs_workbench.public_cage import crystal_objects as CO


def _specimen(**overrides):
    record = {
        "specimen_id": str(uuid.uuid4()),
        "material": "natural quartz",
        "mass": "142 g",
        "dimensions": "60 x 30 x 25 mm",
        "cut_geometry": "natural point, unpolished",
        "orientation_estimate": "c-axis within 10 degrees of long axis",
        "fixture_description": "PLA cradle, foam damping",
    }
    record.update(overrides)
    return record


def _measurement(**overrides):
    record = {
        "specimen_id": str(uuid.uuid4()),
        "drive_frequency": 20480.0,
        "drive_amplitude": "0.2 A constant current",
        "sensor_type": "3-axis magnetometer",
        "temperature": 21.4,
        "humidity": 41.0,
        "clock_source": "GPS-disciplined 10 MHz",
        "raw_file_hash": "a" * 64,
        "processed_receipt_hash": "b" * 64,
    }
    record.update(overrides)
    return record


def test_1_specimen_requires_uuid_and_context():
    assert CO.validate_specimen(_specimen()) == []
    assert any("UUID" in p for p in
               CO.validate_specimen(_specimen(specimen_id="rock-1")))
    missing = CO.validate_specimen({"specimen_id": str(uuid.uuid4())})
    assert len(missing) == len(CO.SPECIMEN_REQUIRED_FIELDS) - 1


def test_2_every_transfer_measurement_has_raw_and_processed_hashes():
    assert CO.validate_transfer_measurement(_measurement()) == []
    for field in ("raw_file_hash", "processed_receipt_hash"):
        problems = CO.validate_transfer_measurement(
            _measurement(**{field: ""}))
        assert any(field in p for p in problems)
        problems = CO.validate_transfer_measurement(
            _measurement(**{field: "deadbeef"}))
        assert any("too short" in p for p in problems)


def test_3_computed_values_are_marked_computational():
    value = CO.computed_value(
        "doubled_green_nm", 532.5383831689123,
        inputs={"ir_nm": 1065.076766337825, "operation": "divide by 2"})
    assert value["evidence_class"] == CO.COMPUTATIONAL_MARK
    assert value["bench_measured"] is False
    with pytest.raises(ValueError):
        CO.computed_value("orphan", 1.0, inputs={})


def test_4_no_bench_claim_without_bench_receipt():
    with pytest.raises(CO.BenchReceiptRequired):
        CO.bench_claim("transfer peak at 20.48 kHz", bench_receipts=None)
    with pytest.raises(CO.BenchReceiptRequired):
        CO.bench_claim("transfer peak at 20.48 kHz", bench_receipts=[])
    row = CO.bench_claim("transfer peak at 20.48 kHz",
                         bench_receipts=["sha256:" + "c" * 64])
    assert row["independently_replicated"] is False


def test_5_no_physical_effect_promoted_from_source_language_alone():
    """The refusal message itself names the rule."""
    try:
        CO.bench_claim("source says the crystal responds", None)
    except CO.BenchReceiptRequired as err:
        assert "source language" in str(err)
    else:
        pytest.fail("bench claim without receipt must raise")


def test_6_no_healing_consciousness_or_propulsion_claim_in_public_docs():
    """Cage-owned public surface: those words appear only in refusals."""
    for path in CF.cage_public_surface(
            __import__("pathlib").Path(__file__).resolve().parents[2]):
        text = path.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()
        for idx, line in enumerate(lines):
            lowered = line.lower()
            for word in ("healing", "consciousness"):
                if word in lowered:
                    window = " ".join(lines[max(0, idx - 12):idx + 1]).lower()
                    assert any(m in window for m in
                               ("not", "refus", "does not", "no ",
                                "quarantin", "gated", "isolated")), (
                        f"{path}:{idx + 1} uses '{word}' outside a "
                        f"refusal context")
