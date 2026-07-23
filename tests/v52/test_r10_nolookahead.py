"""P02 — no-look-ahead is a self-report unless independently captured."""

from __future__ import annotations

import pytest

from r10 import nolookahead as N


def _window(**over):
    base = dict(
        session_id="SESSION_ALIAS",
        session_onset_local="2026-07-20T09:00",
        session_onset_utc="2026-07-20T13:00:00+00:00",
        clock_first_checked_utc="2026-07-20T13:00:00+00:00",
        minute_rollover_ambiguity=False,
        search_start_utc="",
        prior_media_exposure=(),
        independently_captured=False,
    )
    base.update(over)
    return N.ProvenanceWindow(**base)


# --- classify_independence --------------------------------------------

def test_self_report_without_external_capture():
    w = _window(independently_captured=False)
    assert (N.classify_independence(w)
            is N.Independence.NO_LOOKAHEAD_SELF_REPORT)


def test_independently_captured_with_external_capture():
    w = _window(independently_captured=True)
    assert (N.classify_independence(w)
            is N.Independence.INDEPENDENTLY_CAPTURED)


# --- refuse_prove_from_self_report ------------------------------------

def test_proving_from_a_self_report_is_refused():
    with pytest.raises(N.NoLookaheadError):
        N.refuse_prove_from_self_report(_window(independently_captured=False))


def test_proving_is_allowed_when_independently_captured():
    # returns without raising
    N.refuse_prove_from_self_report(_window(independently_captured=True))


# --- is_potentially_contaminated --------------------------------------

def test_cue_after_search_start_is_contaminated():
    flag, reason = N.is_potentially_contaminated(
        cue_time_utc="2026-07-20T13:30:00+00:00",
        search_start_utc="2026-07-20T13:00:00+00:00",
        prior_media_exposure=(),
    )
    assert flag is True
    assert "search" in reason


def test_cue_matching_prior_media_is_contaminated():
    flag, reason = N.is_potentially_contaminated(
        cue_time_utc="a red tetrahedron over water",
        search_start_utc="",
        prior_media_exposure=("red tetrahedron",),
    )
    assert flag is True
    assert "prior media" in reason


def test_clean_prospective_cue_is_not_contaminated():
    flag, reason = N.is_potentially_contaminated(
        cue_time_utc="2026-07-20T12:00:00+00:00",
        search_start_utc="2026-07-20T13:00:00+00:00",  # search later
        prior_media_exposure=("an unrelated memory",),
    )
    assert flag is False
    assert "prospective" in reason


# --- onset_uncertainty_s ----------------------------------------------

def test_uncertainty_is_zero_for_a_clean_window():
    assert N.onset_uncertainty_s(_window()) == 0.0


def test_minute_rollover_widens_uncertainty():
    clean = N.onset_uncertainty_s(_window(minute_rollover_ambiguity=False))
    rolled = N.onset_uncertainty_s(_window(minute_rollover_ambiguity=True))
    assert rolled == clean + N.MINUTE_ROLLOVER_S
    assert rolled > clean


def test_late_clock_check_widens_uncertainty():
    w = _window(
        session_onset_utc="2026-07-20T13:00:00+00:00",
        clock_first_checked_utc="2026-07-20T13:02:00+00:00",  # 120 s late
    )
    assert N.onset_uncertainty_s(w) == pytest.approx(120.0)


def test_late_check_and_rollover_compound():
    w = _window(
        session_onset_utc="2026-07-20T13:00:00+00:00",
        clock_first_checked_utc="2026-07-20T13:02:00+00:00",
        minute_rollover_ambiguity=True,
    )
    assert N.onset_uncertainty_s(w) == pytest.approx(180.0)


# --- report -----------------------------------------------------------

def test_report_measures_nothing_and_self_reports():
    r = N.nolookahead_report(_window(independently_captured=False))
    assert r["measured_here"] == "nothing"
    assert r["evidence_class"] == "OPERATOR_NOTE"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["verdict"] == "NO_LOOKAHEAD_SELF_REPORT"
    assert r["self_report_only"] is True
    assert "prior exposure" in r["what_this_does_not_say"]


def test_report_upgrades_verdict_only_with_capture():
    r = N.nolookahead_report(_window(independently_captured=True))
    assert r["verdict"] == "INDEPENDENTLY_CAPTURED"
    assert r["self_report_only"] is False


def test_default_report_never_claims_proven():
    r = N.nolookahead_report()
    assert r["verdict"] == "NO_LOOKAHEAD_SELF_REPORT"
    assert r["verdict"] != "NO_LOOKAHEAD_PROVEN"
