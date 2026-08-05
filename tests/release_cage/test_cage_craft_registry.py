"""MOD-006 craft-path hypothesis registry -- the six spec tests."""

from __future__ import annotations

import pytest

from rgcs_workbench.public_cage import craft_path_registry as CPR


def _source_record(**overrides):
    record = {
        "status": "SOURCE_REPORTED",
        "statement": "annular aperture with 37 angular cells",
        "source_id": "SRC-EXAMPLE-001",
        "source_type": "VIDEO_TRANSCRIPT",
        "capture_datetime": "2026-07-30T00:00:00Z",
    }
    record.update(overrides)
    return record


def test_1_no_record_validated_without_bench_and_replication_receipts():
    reg = CPR.CraftPathRegistry()
    with pytest.raises(CPR.ValidationRefused):
        reg.add_record({"status": "BENCH_MEASURED", "statement": "x"})
    with pytest.raises(CPR.ValidationRefused):
        reg.add_record({"status": "INDEPENDENTLY_REPLICATED",
                        "statement": "x"})
    entry = reg.add_record(_source_record())
    with pytest.raises(CPR.ValidationRefused):
        reg.promote_with_receipts(entry["registry_index"],
                                  bench_receipt=None,
                                  replication_receipt=None)
    measured = reg.promote_with_receipts(
        entry["registry_index"], bench_receipt="sha256:" + "d" * 64,
        replication_receipt=None)
    assert measured["status"] == "BENCH_MEASURED"
    replicated = reg.promote_with_receipts(
        measured["registry_index"], bench_receipt="sha256:" + "d" * 64,
        replication_receipt="sha256:" + "e" * 64)
    assert replicated["status"] == "INDEPENDENTLY_REPLICATED"


def test_2_source_attributed_records_must_have_provenance():
    reg = CPR.CraftPathRegistry()
    record = _source_record()
    del record["capture_datetime"]
    with pytest.raises(ValueError, match="provenance"):
        reg.add_record(record)


def test_3_derived_arithmetic_must_identify_inputs():
    reg = CPR.CraftPathRegistry()
    with pytest.raises(ValueError, match="inputs"):
        reg.add_record({"status": "DERIVED_ARITHMETIC",
                        "statement": "sector angle 9.7297 degrees"})
    entry = reg.add_record({
        "status": "DERIVED_ARITHMETIC",
        "statement": "sector angle = 360 / 37",
        "inputs": {"degrees_per_turn": 360, "sector_count": 37},
    })
    assert entry["registry_index"] == 0


def test_4_superseded_records_remain_append_only():
    reg = CPR.CraftPathRegistry()
    first = reg.add_record(_source_record())
    reg.supersede(first["registry_index"],
                  _source_record(statement="corrected cell count"))
    records = reg.records()
    assert len(records) == 2
    assert records[0]["status"] == "SUPERSEDED"
    assert records[0]["statement"] == ("annular aperture with 37 "
                                       "angular cells")


def test_5_frequency_spine_roles_remain_separated():
    assert CPR.spine_roles_are_separated()
    values = {e["value_hz"] for e in CPR.FREQUENCY_SPINE}
    assert {4096.0, 1683456.0, 20480.0, 40960.0} <= values
    assert 13183593.75 in values


def test_6_no_power_to_thrust_public_path_exists():
    """The registry module exposes no callable that converts power to
    a force quantity; refusal is structural, not behavioral."""
    import inspect
    for name, obj in inspect.getmembers(CPR, callable):
        signature = str(inspect.signature(obj)) if inspect.isfunction(obj) else ""
        for banned in ("watt", "thrust", "newton", "force"):
            assert banned not in name.lower()
            assert banned not in signature.lower()


def test_unknown_status_is_refused_with_the_ladder_named():
    reg = CPR.CraftPathRegistry()
    with pytest.raises(ValueError, match="SOURCE_REPORTED"):
        reg.add_record({"status": "TOTALLY_VALIDATED"})
