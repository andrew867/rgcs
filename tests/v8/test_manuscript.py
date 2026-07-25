"""P31 — experiment manuscript generator."""

from __future__ import annotations

import pytest

from r15 import manuscript as MS


def test_manuscript_assembles_from_reports_deterministically():
    m1 = MS.generate_manuscript()
    m2 = MS.generate_manuscript()
    assert m1.content_hash() == m2.content_hash()
    text = m1.to_text()
    assert "Non-claims" in text and "synthetic" in text.lower()


def test_collect_reports_all_claim_nothing_measured():
    reports = MS.collect_reports()
    assert len(reports) >= 15
    assert all(r["measured_here"] == "nothing" for r in reports.values())


def test_claim_beyond_evidence_is_refused():
    with pytest.raises(MS.ManuscriptError):
        MS.refuse_claim_beyond_evidence("PHYSICAL_MEASUREMENT")
    # a software claim class is allowed
    MS.refuse_claim_beyond_evidence("SYNTHETIC_OBSERVATION")


def test_report_claims_nothing_measured():
    r = MS.manuscript_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
