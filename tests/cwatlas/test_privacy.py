"""P02 — private/public corpus boundary tests."""

from __future__ import annotations

import pytest

from cwatlas import privacy as P


def test_private_dir_inactive_by_default(monkeypatch):
    monkeypatch.delenv("CWATLAS_PRIVATE_DIR", raising=False)
    assert P.load_private_records() == []       # public runs touch no private data
    assert P.privacy_report()["private_dir_active"] is False


def test_private_record_cannot_be_exported():
    rec = P.Record("r1", {"narrative": "secret", "x": 1}, P.Sensitivity.PRIVATE)
    with pytest.raises(P.PrivacyError):
        P.assert_exportable(rec)


def test_public_record_is_redacted_on_export():
    rec = P.public_fixture("r2", {"narrative": "n", "lat": 51.0, "lon": -1.0})
    out = P.assert_exportable(rec)
    assert "narrative" not in out          # private field stripped
    assert out["lat"] == 51.0              # public field kept


def test_scan_and_refuse_private_tokens():
    assert P.scan_for_private("clean synthetic text") == []
    assert P.scan_for_private("path C:" + "\\Users\\x")
    with pytest.raises(P.PrivacyError):
        P.refuse_private_in_public("private" + "_do_not_commit/thing")
    P.refuse_private_in_public("a synthetic public fixture")   # no raise


def test_report_ships_no_private_data():
    r = P.privacy_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
