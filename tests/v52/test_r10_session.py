"""P01 — append-only session ingest with source/operator separation."""

from __future__ import annotations

import pytest

from r10 import session as S


def _src(eid="e1", sid="sess", status="RAW_SOURCE_RECORD"):
    return S.SessionEvent(
        eid, sid, S.Provenance.SRC_JH, "normalized source text", status,
        "09:17", "America/Chicago", "2026-07-22T14:17Z",
        raw_text_private="the raw private words", publication_class="PRIVATE_ONLY")


def _ag(eid="a1", sid="sess", note=S.AGNoteType.DIRECT_NOTE):
    return S.SessionEvent(
        eid, sid, S.Provenance.AG, "an operator note", "OPERATOR_NOTE",
        "14:11", "America/Chicago", "2026-07-22T19:11Z",
        ag_note_type=note, publication_class="PRIVATE_ONLY")


def test_source_record_may_not_carry_an_ag_note_type():
    with pytest.raises(S.SessionError):
        S.SessionEvent("e", "s", S.Provenance.SRC_LS, "t", "SOURCE_CLAIM",
                       "1", "tz", "u", ag_note_type=S.AGNoteType.PARAPHRASE)


def test_ag_record_must_declare_a_note_type():
    with pytest.raises(S.SessionError):
        S.SessionEvent("e", "s", S.Provenance.AG, "t", "OPERATOR_NOTE",
                       "1", "tz", "u")  # no ag_note_type


def test_bad_evidence_status_refused():
    with pytest.raises(S.SessionError):
        S.SessionEvent("e", "s", S.Provenance.SRC_JH, "t", "TOTALLY_MADE_UP",
                       "1", "tz", "u")


def test_public_view_never_emits_raw_or_private_text():
    e = _src()
    pv = e.public_view()
    assert "raw private words" not in str(pv)
    assert "normalized source text" not in str(pv)   # PRIVATE_ONLY withholds
    assert pv["normalized_text"] == "WITHHELD_PRIVATE"
    assert pv["raw_text_present"] is True
    assert pv["endorsed"] is False


def test_public_view_emits_text_only_when_not_private():
    e = S.SessionEvent("e", "s", S.Provenance.SRC_JH, "shareable", "SOURCE_CLAIM",
                       "1", "tz", "u", publication_class="PUBLIC_SUMMARY")
    assert e.public_view()["normalized_text"] == "shareable"


def test_log_is_append_only_no_overwrite():
    log = S.SessionLog("sess")
    log.append(_src("e1"))
    with pytest.raises(S.SessionError):
        log.append(_src("e1"))            # duplicate id
    with pytest.raises(S.SessionError):
        log.refuse_overwrite("e1")


def test_correction_must_reference_an_existing_event():
    log = S.SessionLog("sess")
    log.append(_src("e1"))
    corr = S.SessionEvent("e2", "sess", S.Provenance.SRC_JH, "fixed",
                          "RAW_SOURCE_RECORD", "1", "tz", "u",
                          correction=True, corrects="e1")
    log.append(corr)                      # ok
    assert len(log.events) == 2
    bad = S.SessionEvent("e3", "sess", S.Provenance.SRC_JH, "x",
                         "RAW_SOURCE_RECORD", "1", "tz", "u",
                         correction=True, corrects="nope")
    with pytest.raises(S.SessionError):
        log.append(bad)


def test_correction_without_reference_refused():
    with pytest.raises(S.SessionError):
        S.SessionEvent("e", "s", S.Provenance.SRC_JH, "t", "RAW_SOURCE_RECORD",
                       "1", "tz", "u", correction=True)


def test_source_and_operator_streams_stay_distinct():
    log = S.SessionLog("sess")
    log.append(_src("e1"))
    log.append(_ag("a1"))
    assert len(log.source_events()) == 1
    assert len(log.operator_events()) == 1
    with pytest.raises(S.SessionError):
        S.refuse_merge_source_into_ag(_src("e1"), _ag("a1"))


def test_content_hash_is_stable_and_sensitive():
    e = _src("e1")
    h = e.content_hash
    assert h == _src("e1").content_hash
    assert h != _src("e1", status="SOURCE_CLAIM").content_hash


def test_report_endorses_nothing():
    r = S.session_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "SRC_JH" in r["provenance_classes"] and "AG" in r["provenance_classes"]
