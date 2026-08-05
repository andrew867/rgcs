"""Imported public-safe record data -- every record passes its own gate.

The craft-path seed records load through CraftPathRegistry.add_record
(the validating door), and the archive seed records must pass
validate_record with zero problems. Nothing imported may carry a
measured, replicated, or verified status.
"""

from __future__ import annotations

from rgcs_workbench.public_cage import archive_schema as AS
from rgcs_workbench.public_cage import craft_path_registry as CPR


def test_craft_path_seed_records_load_through_the_validating_door():
    registry = CPR.load_public_records()
    records = registry.records()
    assert len(records) >= 9
    ids = [r["record_id"] for r in records]
    assert len(ids) == len(set(ids)), "duplicate record ids"


def test_no_imported_craft_record_claims_measurement_or_replication():
    for record in CPR.load_public_records().records():
        assert record["status"] not in ("BENCH_MEASURED",
                                        "INDEPENDENTLY_REPLICATED")


def test_craft_seed_covers_the_public_safe_spine_and_refusals():
    records = CPR.load_public_records().records()
    statuses = {r["status"] for r in records}
    assert "REFUSED_PUBLIC_CLAIM" in statuses
    assert "DERIVED_ARITHMETIC" in statuses
    spine_record = next(r for r in records
                        if r["status"] == "ENGINEERING_TRANSLATION")
    for value in ("4096", "1683456", "13183593.75", "20480", "40960"):
        assert value in spine_record["statement"]


def test_derived_seed_records_reproduce_arithmetically():
    for record in CPR.load_public_records().records():
        if record["status"] != "DERIVED_ARITHMETIC":
            continue
        inputs = record["inputs"]
        if "multiplier" in inputs:
            assert (inputs["phase_authority_hz"] * inputs["multiplier"]
                    == 1683456)
        if "degrees_per_turn" in inputs:
            assert abs(inputs["degrees_per_turn"] / inputs["sector_count"]
                       - 9.72972972972973) < 1e-12


def test_archive_seed_records_all_validate():
    records = AS.load_public_records()
    assert len(records) >= 4
    ids = [r["record_id"] for r in records]
    assert len(ids) == len(set(ids))


def test_no_imported_archive_record_is_community_or_verified():
    for record in AS.load_public_records():
        assert record["source_type"] != "COMMUNITY_SUBMISSION_UNVERIFIED"
        assert record.get("verified") is not True
        assert "claim_boundary" in record


def test_operator_note_hashes_match_their_embedded_text():
    import hashlib
    for record in AS.load_public_records():
        if record.get("note_text"):
            expected = hashlib.sha256(
                record["note_text"].encode("utf-8")).hexdigest()
            assert record["operator_note_hash"] == expected
