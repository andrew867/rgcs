"""P03 -- private provenance and source-registry import."""

from __future__ import annotations

import json

import pytest

from cwatlas import privacy
from cwatlas.r1082 import claims
from cwatlas.r1082 import source_import as SI

# A fixed epoch (decimal year), passed in -- never a wall-clock read.
EPOCH = 2020.5


def _public_import():
    imp = SI.SourceImport()
    # Synthetic vectors referenced by opaque fixture ids only.
    imp.register_vector("SRC_SYN_0001", "165892743", [1, 65, 89, 27, 43],
                        epoch=EPOCH, narrative={"notes": "synthetic note"})
    imp.register_vector("SRC_SYN_0002", "2736598321", [27, 36, 59, 83, 21],
                        epoch=EPOCH)
    imp.register_stonehenge_anchor()
    return imp


def test_body_status_unknown_unless_assigned():
    imp = _public_import()
    rec = imp.vectors[0]
    assert rec.body_status is SI.BodyStatus.UNKNOWN
    assert rec.body is None
    # Explicit assignment flips the status.
    imp.register_vector("SRC_SYN_0003", "165876523", [1, 65, 87, 65, 23],
                        epoch=EPOCH, body="EARTH")
    assigned = imp.vectors[-1]
    assert assigned.body_status is SI.BodyStatus.ASSIGNED
    assert assigned.body == "EARTH"


def test_stonehenge_referenced_by_opaque_id_only():
    imp = _public_import()
    (anchor,) = imp.anchors
    assert anchor.fixture_id == SI.STONEHENGE_FIXTURE_ID == "STONEHENGE_PRIVATE_001"
    assert anchor.use is SI.RecordUse.TRAINING_ANCHOR
    # No raw vector or narrative label appears anywhere in the projection.
    proj = anchor.public_projection()
    blob = json.dumps(proj)
    assert "Stonehenge" not in blob
    assert "165876523" not in blob


def test_narrative_is_never_exported():
    imp = _public_import()
    rec = imp.vectors[0]  # carries a private "notes" narrative
    projection = rec.assert_exportable()
    assert "notes" not in projection
    assert "narrative" not in projection
    assert "raw" not in projection  # raw source string never exported
    blob = json.dumps(imp.export_public())
    assert "synthetic note" not in blob


def test_private_record_export_is_refused():
    rec = SI.SourceVectorRecord(
        fixture_id="SRC_PRIV_0001",
        raw="165892743",
        tokens=(1, 65, 89, 27, 43),
        raw_hash=SI._sha256("165892743"),
        sensitivity=privacy.Sensitivity.PRIVATE,
        _private={"narrative": "a private story"},
    )
    with pytest.raises(privacy.PrivacyError):
        rec.assert_exportable()


def test_private_dir_ignore_rule(monkeypatch, tmp_path):
    # Absent CWATLAS_PRIVATE_DIR the private adapter yields nothing.
    monkeypatch.delenv("CWATLAS_PRIVATE_DIR", raising=False)
    empty = SI.SourceImport.from_private(epoch=EPOCH)
    assert len(empty) == 0

    # With the ignored path set, records load but stay PRIVATE and narrative
    # never crosses into a public export.
    (tmp_path / "recs.json").write_text(json.dumps([
        {"raw": "165892743", "tokens": [1, 65, 89, 27, 43],
         "notes": "private only", "label": "secret place"},
    ]), encoding="utf-8")
    monkeypatch.setenv("CWATLAS_PRIVATE_DIR", str(tmp_path))
    imp = SI.SourceImport.from_private(epoch=EPOCH)
    assert len(imp) == 1
    assert imp.vectors[0].is_private()
    with pytest.raises(privacy.PrivacyError):
        imp.export_public()  # a private record refuses public export


def test_provenance_ledger_is_hash_chained_and_deterministic():
    a = _public_import()
    b = _public_import()
    # Same synthetic inputs, same epoch -> identical ledger head (deterministic).
    assert a.ledger.head() == b.ledger.head()
    assert a.ledger.verify_chain() is True
    assert len(a.ledger) == 2  # one event per registered vector


def test_report_seals_origin_and_privacy():
    r = SI.source_import_report()
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["measured_here"] == "nothing"
    assert r["stonehenge_fixture_id"] == "STONEHENGE_PRIVATE_001"
    assert r["body_status_default"] == "unknown"
    assert "narrative" in r["narrative_fields_never_exported"]
