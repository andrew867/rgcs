"""P33 — statistical and methods appendices."""

from __future__ import annotations

import pytest

from r15 import appendices as A


def test_appendix_entries_every_one_has_a_null_model():
    entries = A.build_appendix()
    assert len(entries) >= 2
    assert all(e.null_model for e in entries)


def test_entry_without_null_is_refused():
    with pytest.raises(A.AppendixError):
        A.AppendixEntry("Results", "t-test", "", "none")
    with pytest.raises(A.AppendixError):
        A.refuse_appendix_without_null("Results")


def test_report_claims_nothing_measured():
    r = A.appendices_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
