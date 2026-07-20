"""S04/S05/S08 — the public conventional-science chronology."""

from __future__ import annotations

import pytest

from r10 import chronology as C


# --- date-type separation ----------------------------------------------

def test_the_nine_date_roles_are_kept_separate():
    assert len(C.DATE_ROLES) == 9
    assert "publication" in C.DATE_ROLES
    assert "retrieval" in C.DATE_ROLES
    assert "project_derivation" in C.DATE_ROLES


def test_a_dated_field_validates_role_and_precision():
    with pytest.raises(C.ChronologyError):
        C.DatedField("made_up_role", "2020", "YEAR_ONLY")
    with pytest.raises(C.ChronologyError):
        C.DatedField("publication", "2020", "PRETTY_SURE")


def test_only_exact_dates_are_strict():
    assert C.DatedField("publication", "1930-12-04", "EXACT_DATE").strict
    assert C.DatedField("event_start", "2020-01-01T00:00Z",
                        "EXACT_TIMESTAMP").strict
    assert not C.DatedField("publication", "1912", "YEAR_ONLY").strict
    assert not C.DatedField("event_start", "1930s", "INFERRED_RANGE").strict


# --- the strict-timeline gate ------------------------------------------

def test_only_exactly_dated_events_enter_the_strict_timeline():
    """Pauli's 1930 letter is exactly dated and enters; the year-only
    events do not. A year is not a strict date."""
    strict = C.strict_timeline()
    keys = {e.key for e in strict}
    assert "pauli_1930" in keys
    assert "coblentz_1912" not in keys      # year-only


def test_year_only_events_are_still_in_the_full_ledger():
    """Excluded from the strict timeline is not excluded from the
    record -- they remain searchable, just not strictly ordered."""
    full = {e.key for e in C.full_ledger()}
    assert "coblentz_1912" in full
    assert "silver_2026" in full


def test_the_full_ledger_is_ordered_by_year():
    years = [e.sort_year for e in C.full_ledger()]
    assert years == sorted(years)


def test_every_event_is_public_and_conventional():
    """This ledger must contain no private-corpus material."""
    for e in C.CONVENTIONAL_EVENTS:
        assert e.public
        assert e.evidence_class == "CONVENTIONAL_LITERATURE"


def test_the_beta_decay_sequence_is_in_the_right_order():
    order = [e.key for e in C.full_ledger()]
    assert order.index("chadwick_1914") < order.index("pauli_1930")
    assert order.index("pauli_1930") < order.index("fermi_1934")


def test_the_firefly_correction_postdates_the_overestimate():
    order = [e.key for e in C.full_ledger()]
    assert order.index("coblentz_1912") < order.index("silver_2026")


# --- S08: possible access, not influence -------------------------------

def test_access_edges_run_only_forward_in_time():
    for e in C.possible_access_edges():
        early = [x for x in C.CONVENTIONAL_EVENTS if x.key == e.earlier][0]
        late = [x for x in C.CONVENTIONAL_EVENTS if x.key == e.later][0]
        assert early.sort_year < late.sort_year


def test_access_edges_are_labelled_as_opportunity_not_influence():
    e = C.possible_access_edges()[0]
    assert "possible access only" in e.as_record()["means"]


def test_the_earliest_event_has_no_incoming_access_edge():
    edges = C.possible_access_edges()
    earliest = min(C.CONVENTIONAL_EVENTS, key=lambda e: e.sort_year or 9999)
    assert not any(e.later == earliest.key for e in edges)


# --- chronology is not causality ---------------------------------------

def test_a_causal_claim_from_precedence_is_refused():
    with pytest.raises(C.CausalClaimRefused) as e:
        C.refuse_causal_claim("coblentz_1912", "silver_2026")
    msg = str(e.value)
    assert "Precedence is not causation" in msg
    assert "possible access and nothing more" in msg


def test_report_states_the_scope_and_the_firewall():
    r = C.chronology_report()
    assert "private repository" in r["scope"]
    assert "cannot establish causation" in r["chronology_is_not_causality"]
    assert r["measured_here"] == "nothing"


def test_report_counts_are_consistent():
    r = C.chronology_report()
    assert r["conventional_events"] == len(C.CONVENTIONAL_EVENTS)
    assert r["in_strict_timeline"] == len(C.strict_timeline())
    assert r["in_strict_timeline"] < r["conventional_events"]
