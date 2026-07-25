"""P55 — privacy narrative versus public export separation.

POWER: a bundle of synthetic public records exports cleanly with private fields
redacted. Negative: a PRIVATE record is refused; a private path/identity token
buried in any field (including nested) is refused; the export never carries a
private field. Deterministic.
"""

from __future__ import annotations

import pytest

from cwatlas import export_separation as X
from cwatlas import privacy
from cwatlas.privacy import Sensitivity


def _public(record_id, payload):
    return privacy.public_fixture(record_id, payload)


# --- POWER --------------------------------------------------------------------

def test_public_records_export_cleanly():
    recs = [
        _public("r1", {"vector": "SYN-0001", "score": 0.5, "narrative": "SECRET"}),
        _public("r2", {"vector": "SYN-0002", "region": "synthetic-cell-7"}),
    ]
    bundle = X.build_public_export(recs)
    assert bundle["item_count"] == 2
    # The private field was stripped from the exported payload.
    assert "narrative" not in bundle["items"][0]["payload"]
    assert bundle["items"][0]["payload"]["vector"] == "SYN-0001"
    assert X.assert_export_clean(bundle) is True


def test_partition_separates_without_exporting():
    pub = _public("r1", {"vector": "SYN-1"})
    priv = privacy.load_private_records()  # empty without the env var
    recs = [pub] + priv
    public, private = X.partition(recs)
    assert public == [pub]
    assert private == []


# --- Negative: private content refused ----------------------------------------

def test_private_record_refused():
    priv = privacy.Record("p1", {"vector": "x"}, Sensitivity.PRIVATE)
    with pytest.raises(X.ExportError):
        X.build_public_export([priv])


def test_private_token_in_field_refused():
    # A forbidden path token embedded in an otherwise-public field.
    token = "one" + "drive - green"
    rec = _public("r1", {"note": f"exported from {token}/data"})
    with pytest.raises(X.ExportError):
        X.build_public_export([rec])


def test_private_token_nested_refused():
    token = "private" + "_do_not_commit"
    rec = _public("r1", {"meta": {"paths": ["ok", token]}})
    with pytest.raises(X.ExportError):
        X.build_public_export([rec])


def test_export_never_carries_private_fields():
    rec = _public("r1", {
        "vector": "SYN-1",
        "prediction": "leak",
        "personal_location": "leak",
        "operator_name": "leak",
    })
    bundle = X.build_public_export([rec])
    payload = bundle["items"][0]["payload"]
    for f in ("prediction", "personal_location", "operator_name"):
        assert f not in payload


def test_assert_export_clean_rejects_non_synthetic_item():
    bundle = {"items": [{"record_id": "x", "sensitivity": "PRIVATE",
                          "payload": {}}]}
    with pytest.raises(X.ExportError):
        X.assert_export_clean(bundle)


# --- Determinism --------------------------------------------------------------

def test_export_is_deterministic():
    recs = [_public("r1", {"vector": "SYN-1", "score": 1})]
    assert X.build_public_export(recs) == X.build_public_export(recs)


def test_report_declares_boundary():
    r = X.export_separation_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert "narrative" in r["private_fields"]
