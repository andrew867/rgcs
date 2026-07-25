"""P40 -- forward campaign: POWER (error under tolerance), determinism, refusals."""

from __future__ import annotations

import pytest

from cwatlas import forward_campaign as fc
from cwatlas.claims import ClaimClass


def _small(**kw) -> fc.CampaignConfig:
    base = dict(bodies=("EARTH", "MARS"), lat_steps=7, lon_steps=9,
                ico_depth=12, fuzz_count=20)
    base.update(kw)
    return fc.CampaignConfig(**base)


# --- POWER: round-trip error under declared tolerance -----------------------

def test_geo1_round_trip_under_tolerance():
    res = fc.run_campaign(_small())
    geo1 = res.report_for("CW-GEO-1")
    assert geo1.max_error_m <= geo1.tolerance_m
    assert geo1.passed is True
    assert geo1.max_error_m < 0.01  # sub-centimetre, as declared


def test_ico_round_trip_under_tolerance():
    res = fc.run_campaign(_small())
    ico = res.report_for("CW-HCM-ICO-1")
    assert ico.max_error_m <= ico.tolerance_m
    assert ico.passed is True


def test_campaign_all_passed():
    res = fc.run_campaign(_small())
    assert res.all_passed is True
    assert res.total_points > 0


# --- POWER: error shrinks with icosahedral depth ----------------------------

def test_ico_error_decreases_with_depth():
    e8 = fc.run_campaign(_small(ico_depth=8, bodies=("EARTH",))) \
        .report_for("CW-HCM-ICO-1").max_error_m
    e10 = fc.run_campaign(_small(ico_depth=10, bodies=("EARTH",))) \
        .report_for("CW-HCM-ICO-1").max_error_m
    e12 = fc.run_campaign(_small(ico_depth=12, bodies=("EARTH",))) \
        .report_for("CW-HCM-ICO-1").max_error_m
    assert e8 > e10 > e12


def test_declared_tolerance_scales_with_depth():
    assert (fc.ico_tolerance_m(8, "EARTH")
            > fc.ico_tolerance_m(10, "EARTH")
            > fc.ico_tolerance_m(12, "EARTH"))


def test_tolerance_scales_with_body_radius():
    # A smaller body has a proportionally smaller metric cell bound.
    assert fc.ico_tolerance_m(12, "MARS") < fc.ico_tolerance_m(12, "EARTH")


# --- determinism ------------------------------------------------------------

def test_campaign_is_deterministic():
    a = fc.run_campaign(_small())
    b = fc.run_campaign(_small())
    assert a.report_for("CW-GEO-1").max_error_m == \
        b.report_for("CW-GEO-1").max_error_m
    assert a.report_for("CW-HCM-ICO-1").max_error_m == \
        b.report_for("CW-HCM-ICO-1").max_error_m
    assert a.total_points == b.total_points


def test_point_generation_deterministic():
    cfg = _small()
    assert fc.generate_points(cfg) == fc.generate_points(cfg)


def test_edge_cases_present():
    pts = fc.generate_points(_small())
    assert (90.0, 0.0) in pts and (-90.0, 0.0) in pts and (0.0, 0.0) in pts


# --- refusals are counted, not fatal ----------------------------------------

def test_boundary_points_refused_not_failed():
    # Exact-boundary directions may be safely refused by the ico codec; the
    # campaign still passes and records the count.
    res = fc.run_campaign(_small())
    ico = res.report_for("CW-HCM-ICO-1")
    assert ico.num_refused >= 0
    assert ico.passed is True


# --- negative: invalid config -----------------------------------------------

def test_unknown_body_refused():
    with pytest.raises(fc.CampaignError):
        fc.CampaignConfig(bodies=("PLUTO",))


def test_undeclared_depth_refused():
    with pytest.raises(fc.CampaignError):
        fc.CampaignConfig(ico_depth=7)


def test_too_few_steps_refused():
    with pytest.raises(fc.CampaignError):
        fc.CampaignConfig(lat_steps=1)


def test_ico_tolerance_unknown_depth_refused():
    with pytest.raises(fc.CampaignError):
        fc.ico_tolerance_m(99, "EARTH")


# --- governance report ------------------------------------------------------

def test_report_shape():
    r = fc.forward_campaign_report()
    assert r["claim_class"] == ClaimClass.CANONICAL_ROUND_TRIP.value
    assert r["measured_here"] == "nothing"
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["deterministic"] is True
