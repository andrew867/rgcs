"""P03 — sky-observation reconstruction (anonymized public engine)."""

from __future__ import annotations

import pytest

from r10 import skytrack as SK


def _k(span=40.0, dur=9.0, steady=True, silent=True, const=True,
       bright=True):
    return SK.Kinematics(span, dur, steady, silent, const, bright)


def test_no_geometry_means_insufficient_geometry():
    r = SK.assess_observation(_k(span=None, dur=None))
    assert r["verdict"] == "INSUFFICIENT_GEOMETRY"
    assert not r["identity_claimed"]


def test_a_steady_silent_transit_never_becomes_identified():
    """The load-bearing rule: consistent-with is not identified."""
    r = SK.assess_observation(_k())
    assert r["verdict"] == "UNIDENTIFIED_OBSERVATION"
    assert not r["identity_claimed"]
    assert r["catalog_match"] == "NO_CATALOG_MATCH_RUN"


def test_steady_silent_constant_speed_leads_to_satellite_candidate():
    """~40 deg in 9 s, steady, silent -> satellite is the leading
    ordinary hypothesis (not a conclusion)."""
    r = SK.assess_observation(_k())
    assert r["leading_ordinary_candidate"] == "SATELLITE_CANDIDATE"


def test_blinking_shifts_toward_aircraft():
    r = SK.rank_ordinary_candidates(_k(steady=False))
    assert r["leading"] == "AIRCRAFT_CANDIDATE"


def test_a_barely_moving_light_leads_to_astronomical():
    r = SK.rank_ordinary_candidates(_k(span=0.2, dur=9.0))
    assert r["leading"] == "ASTRONOMICAL_CANDIDATE"


def test_a_fast_brief_streak_leads_to_meteor():
    r = SK.rank_ordinary_candidates(_k(span=45.0, dur=1.0))
    assert r["leading"] == "METEOR_CANDIDATE"


def test_angular_speed_is_span_over_duration():
    k = _k(span=45.0, dur=9.0)
    assert k.angular_speed_deg_s == pytest.approx(5.0)
    assert _k(span=None, dur=9.0).angular_speed_deg_s is None


def test_classifying_without_a_catalog_is_refused():
    for identity in ("extraterrestrial craft", "satellite", "aircraft"):
        with pytest.raises(SK.ObservationError):
            SK.refuse_identity_without_catalog(identity)


def test_the_engine_holds_no_specific_observation():
    r = SK.skytrack_report()
    assert "holds\nno personal observation" in r["what_this_does_not_say"] \
        or "holds no personal observation" in r["what_this_does_not_say"]
    assert r["default_verdict"] == "UNIDENTIFIED_OBSERVATION"
    assert r["measured_here"] == "nothing"


def test_it_neither_asserts_nor_excludes_the_exotic():
    r = SK.assess_observation(_k())
    assert "no exotic\nidentity is asserted or excluded" in r["note"] or \
        "no exotic identity is asserted or excluded" in r["note"]
