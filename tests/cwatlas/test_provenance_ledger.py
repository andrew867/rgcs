"""P04 -- communications and correction ledger tests (synthetic only)."""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from cwatlas import privacy
from cwatlas import provenance_ledger as L

SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "cwatlas" / "schemas" / "provenance_event.schema.json"
)


def _synthetic_entries() -> list:
    """A synthetic comms/correction chronicle -- no private narrative."""
    return [
        {"kind": L.EventKind.MESSAGE, "source_id": "SRC-A", "epoch": 2020.0,
         "raw": "signal alpha 007", "event_id": "m0"},
        {"kind": L.EventKind.MUNDANE_CONTROL, "source_id": "SRC-A",
         "epoch": 2020.1, "raw": "weather is fine", "event_id": "c0"},
        {"kind": L.EventKind.SOURCE_TIMESTAMP, "source_id": "SRC-B",
         "epoch": 2020.2, "raw": "1969-07-20", "event_id": "t0"},
        {"kind": L.EventKind.CORRECTION, "source_id": "SRC-A", "epoch": 2020.3,
         "raw": "signal alpha 070", "corrects": "m0", "event_id": "x0"},
    ]


def test_import_builds_typed_events():
    ledger = L.import_ledger(_synthetic_entries())
    assert len(ledger) == 4
    kinds = [e.kind for e in ledger.events]
    assert kinds == [
        L.EventKind.MESSAGE, L.EventKind.MUNDANE_CONTROL,
        L.EventKind.SOURCE_TIMESTAMP, L.EventKind.CORRECTION]


def test_raw_string_is_immutable_via_hash():
    ledger = L.import_ledger(_synthetic_entries())
    ev = ledger.get("m0")
    # The event is frozen; the raw string cannot be reassigned in place.
    with pytest.raises(dataclasses.FrozenInstanceError):
        ev.raw = "tampered"  # type: ignore[misc]
    # And the hash binds the exact original bytes.
    assert ev.raw_hash == L._sha256("signal alpha 007")
    assert ev.verify_raw()


def test_correction_links_and_does_not_overwrite():
    ledger = L.import_ledger(_synthetic_entries())
    original = ledger.get("m0")
    corrections = ledger.corrections_for("m0")
    assert [c.event_id for c in corrections] == ["x0"]
    # The original event is untouched -- history is preserved, not rewritten.
    assert original.raw == "signal alpha 007"
    assert corrections[0].corrects == "m0"
    assert corrections[0].raw == "signal alpha 070"


def test_correction_must_link_to_a_known_event():
    ledger = L.Ledger()
    with pytest.raises(L.LedgerError):
        ledger.append(L.EventKind.CORRECTION, "SRC", 2020.0, "x",
                      corrects="does-not-exist")


def test_correction_requires_a_link():
    ledger = L.Ledger()
    with pytest.raises(L.LedgerError):
        ledger.append(L.EventKind.CORRECTION, "SRC", 2020.0, "x")


def test_chain_verifies_when_intact():
    ledger = L.import_ledger(_synthetic_entries())
    assert ledger.verify_chain() is True


def test_tampering_a_past_event_breaks_the_chain():
    ledger = L.import_ledger(_synthetic_entries())
    assert ledger.verify_chain() is True
    # Forge a past event's raw string (bypassing the frozen guard).
    victim = ledger.events[0]
    object.__setattr__(victim, "raw", "signal alpha 999")
    assert victim.verify_raw() is False
    assert ledger.verify_chain() is False


def test_tampering_kind_also_breaks_the_chain():
    ledger = L.import_ledger(_synthetic_entries())
    victim = ledger.events[1]
    object.__setattr__(victim, "kind", L.EventKind.MESSAGE)
    assert ledger.verify_chain() is False


def test_import_is_deterministic():
    a = L.import_ledger(_synthetic_entries())
    b = L.import_ledger(_synthetic_entries())
    assert [e.chain_hash for e in a.events] == [e.chain_hash for e in b.events]
    assert a.head() == b.head()


def test_event_dict_conforms_to_schema():
    jsonschema = pytest.importorskip("jsonschema")
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    ledger = L.import_ledger(_synthetic_entries())
    for ev in ledger.events:
        jsonschema.validate(ev.to_event_dict(), schema)


def test_report_claims_nothing_geographic():
    r = L.provenance_ledger_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"


def test_public_fixtures_carry_no_private_tokens():
    # The synthetic corpus used here must trip no private-token scan.
    for entry in _synthetic_entries():
        assert privacy.scan_for_private(entry["raw"]) == []
