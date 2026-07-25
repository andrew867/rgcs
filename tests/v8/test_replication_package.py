"""P35 — replication package and external handoff."""

from __future__ import annotations

import pytest

from r15 import replication_package as RP


def test_manifest_covers_r15_modules_and_hashes_are_deterministic():
    m1 = RP.build_manifest(".")
    m2 = RP.build_manifest(".")
    assert len(m1.files) >= 30           # the r15 module set
    assert m1.files == m2.files          # per-file hashes deterministic
    assert m1.content_hash() == m2.content_hash()
    assert len(m1.schemas) >= 11
    assert len(m1.receipts) >= 30


def test_private_content_is_refused():
    with pytest.raises(RP.ReplicationPackageError):
        RP.refuse_package_with_private_content("path C:" + "\\Users\\x")


def test_scan_flags_private_tokens_and_passes_clean_text():
    assert RP.scan_for_private("clean synthetic fixture text") == []
    assert RP.scan_for_private("private" + "_do_not_commit here")


def test_report_claims_nothing_measured():
    r = RP.replication_package_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
