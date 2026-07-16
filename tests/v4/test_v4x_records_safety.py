"""D01/S01: shared record schemas + safety gates."""
from __future__ import annotations

import pytest

from rscs2_core import research_records as rr


def test_record_factory_common_fields_and_kinds():
    rec = rr.make_record("FrequencyKeyRecord", "F001", "4096 Hz",
                         "computational", "CORE_VALIDATED", ["EST"],
                         frequency_kind="exact_physical_frequency",
                         value_hz=4096.0)
    assert rec["schema_version"] == "rgcs.v4x.record.1"
    assert rec["record_id"] == "F001"
    with pytest.raises(rr.RecordError, match="unknown record kind"):
        rr.make_record("MagicRecord", "X", "x", "l",
                       "CORE_VALIDATED", ["EST"])
    with pytest.raises(rr.RecordError, match="unknown status"):
        rr.make_record("RunRecord", "R1", "r", "l", "TOTALLY_REAL",
                       ["EST"])
    assert len(rr.RECORD_KINDS) == 25


def test_measurement_rules_enforced():
    with pytest.raises(rr.RecordError, match="MEAS record missing"):
        rr.make_record("RawObservationRecord", "O1", "obs", "exp",
                       "EXPERIMENTALLY_MEASURED", ["MEAS"])
    ok = rr.make_record(
        "RawObservationRecord", "O1", "obs", "exp",
        "EXPERIMENTALLY_MEASURED", ["MEAS"],
        raw_hash="a" * 64, instrument="mic-1", calibration_id="c1",
        protocol_version="1", randomization="seeded", blinding="yes",
        safety_gate_id="S-ACOU-1")
    assert ok["raw_hash"]
    with pytest.raises(rr.RecordError, match="synthetic"):
        rr.make_record("RawObservationRecord", "O2", "syn", "exp",
                       "EXPERIMENTALLY_MEASURED", ["MEAS"],
                       synthetic=True, raw_hash="b" * 64,
                       instrument="i", calibration_id="c",
                       protocol_version="1", randomization="r",
                       blinding="b", safety_gate_id="s")
    with pytest.raises(rr.RecordError, match="synthetic"):
        rr.make_record("RunRecord", "R9", "syn run", "exp",
                       "EXPERIMENTALLY_MEASURED", ["ENG"],
                       synthetic=True)


def test_frequency_and_consciousness_rules():
    with pytest.raises(rr.RecordError, match="frequency_kind"):
        rr.make_record("FrequencyKeyRecord", "F0", "x", "comp",
                       "SOURCE_HYPOTHESIS", ["SRC"])
    with pytest.raises(rr.RecordError, match="layer"):
        rr.make_record("ConsciousnessLayerRecord", "C0", "x", "t",
                       "SOURCE_HYPOTHESIS", ["SRC"])
    # myth/metaphor layers capped at SOURCE_HYPOTHESIS
    with pytest.raises(rr.RecordError, match="capped"):
        rr.make_record("ConsciousnessLayerRecord", "C1", "myth", "t",
                       "REDUCED_ORDER_VALIDATED", ["HYP"],
                       layer="private_myth")
    ok = rr.make_record("ConsciousnessLayerRecord", "C2", "kuramoto",
                        "t", "REDUCED_ORDER_VALIDATED", ["DER"],
                        layer="mathematical_model",
                        falsification_condition="n/a")
    assert ok["layer"] == "mathematical_model"


def test_hypothesis_requires_falsification():
    with pytest.raises(rr.RecordError, match="falsification"):
        rr.make_record("HypothesisRecord", "H1", "h", "l",
                       "SOURCE_HYPOTHESIS", ["HYP"])


def test_safety_gate_envelopes():
    ok = rr.safety_gate({"campaign_kind": "acoustic",
                         "declared_limits": {"voltage_v": 12.0,
                                             "spl_dba": 80.0}})
    assert ok["passed"]
    assert ok["required_status"] == \
        "PROTOCOL_READY_HARDWARE_REQUIRED"
    hot = rr.safety_gate({"campaign_kind": "electrode_pulse",
                          "declared_limits": {"voltage_v": 120.0}})
    assert not hot["passed"]
    assert any("30 V" in b for b in hot["blockers"])
    mains = rr.safety_gate({"campaign_kind": "coil",
                            "uses_mains_voltage": True,
                            "declared_limits": {}})
    assert not mains["passed"]


def test_human_subject_gate_blocks_on_ethics():
    out = rr.safety_gate({"campaign_kind": "operator_state",
                          "declared_limits": {"voltage_v": 0.0}})
    assert not out["passed"]
    assert out["required_status"] == "ETHICS_APPROVAL_REQUIRED"
    water = rr.safety_gate({"campaign_kind": "water",
                            "declared_limits": {}})
    assert not water["passed"]          # missing no-ingestion ack
    water_ok = rr.safety_gate({"campaign_kind": "water",
                               "declared_limits": {},
                               "no_ingestion_ack": True})
    assert water_ok["passed"]
