"""P01/P02 — verified quartz-growth timeline and the classified-link refusal."""

from __future__ import annotations

from datetime import date

import pytest

from r10 import quartzhistory as QH


def test_the_timeline_is_chronologically_ordered():
    assert QH.timeline_is_ordered()


def test_the_three_required_verdicts():
    v = QH.verify_timeline()
    assert v["postwar_quartz_industrial_timeline"] == \
        "POSTWAR_QUARTZ_INDUSTRIAL_TIMELINE_VERIFIED"
    assert v["defense_company_overlap"] == "DEFENSE_COMPANY_OVERLAP_VERIFIED"
    assert v["classified_technology_link"] == \
        "CLASSIFIED_TECHNOLOGY_LINK_NOT_ESTABLISHED"


def test_key_patents_are_present_with_sourced_dates():
    ids = {p.patent_id for p in QH.TIMELINE}
    assert "US2675303A" in ids and "US2785058A" in ids
    us2675 = next(p for p in QH.TIMELINE if p.patent_id == "US2675303A")
    assert us2675.grant_date == date(1954, 4, 13)
    assert us2675.assignee_at_filing == "Clevite"


def test_dates_are_sourced_not_independently_verified():
    for p in QH.TIMELINE:
        assert p.source_quality in (QH.SourceQuality.PRIMARY_RECORD_SECONDHAND,
                                    QH.SourceQuality.PRIMARY_RECORD,
                                    QH.SourceQuality.SECONDARY)


def test_a_patent_requires_an_id():
    with pytest.raises(QH.HistoryError):
        QH.CrystalGrowthPatent("", "US", "t", (), "a", None, None, None, None)


def test_the_classified_link_is_refused():
    with pytest.raises(QH.HistoryError):
        QH.refuse_classified_link()


def test_chronology_is_not_causation():
    with pytest.raises(QH.HistoryError):
        QH.refuse_chronology_as_causation()


def test_milestone_date_is_the_represented_milestone():
    # a granted patent is placed on the timeline at its grant date
    p = QH.CrystalGrowthPatent("x", "US", "t", (), "a",
                               date(1952, 4, 28), date(1952, 4, 28),
                               date(1957, 3, 12), date(1957, 3, 12))
    assert p.milestone_date == date(1957, 3, 12)


def test_report_verifies_history_but_not_a_hidden_lineage():
    r = QH.quartzhistory_report()
    assert r["evidence_class"] == "HISTORICAL_FACT"
    assert r["measured_here"] == "nothing"
    assert "classified" in r["what_this_does_not_say"].lower()
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
