"""P02/P03 — the nine-density ontology and its two anchors."""

from __future__ import annotations

import pytest

from r10 import density as D


# --- the firewall this module exists for -------------------------------

def test_density_is_not_dimension_or_mass():
    with pytest.raises(D.DimensionConflation):
        D.refuse_dimension_conflation("a 4-dimensional space")
    with pytest.raises(D.DimensionConflation):
        D.refuse_dimension_conflation("kg/m^3")


def test_the_report_leads_with_the_firewall():
    r = D.density_report()
    assert "not mathematical dimension" in r["the_firewall"]


# --- exactly two anchors, everything else honest -----------------------

def test_only_steps_six_and_nine_are_anchored():
    assert set(D.LIGHT_FRACTION_ANCHORS) == {6, 9}
    assert D.LIGHT_FRACTION_ANCHORS[6] == 0.5
    assert D.LIGHT_FRACTION_ANCHORS[9] == 1.0


def test_anchors_come_back_exactly_uninterpolated():
    assert D.anchors_are_respected()
    assert D.light_fraction_point(6) == 0.5
    assert D.light_fraction_point(9) == 1.0


def test_below_the_anchor_the_fraction_is_unsupplied_not_extrapolated():
    """One anchor determines nothing below it. Steps 1-5 must be
    UNSUPPLIED, not a made-up number."""
    for d in range(1, 6):
        est = D.interpolate_light_fraction(d)
        assert est["support"] == "UNSUPPLIED"
        assert est["light_fraction"] is None


def test_between_the_anchors_it_is_model_derived_with_a_band():
    for d in (7, 8):
        est = D.interpolate_light_fraction(d)
        assert est["support"] == "MODEL_DERIVED"
        assert est["uncertainty"] > 0        # a real band, not a point
        assert 0.5 < est["light_fraction"] < 1.0


def test_the_band_reflects_genuine_model_disagreement():
    """Three monotone models, and their spread IS the uncertainty."""
    est = D.interpolate_light_fraction(7)
    assert set(est["models"]) == {"LINEAR", "CONCAVE", "CONVEX"}
    lo, hi = min(est["models"].values()), max(est["models"].values())
    assert est["uncertainty"] == pytest.approx((hi - lo) / 2)


def test_a_point_value_is_refused_where_only_a_band_exists():
    with pytest.raises(D.UnsupportedAnchor):
        D.light_fraction_point(7)      # model-derived
    with pytest.raises(D.UnsupportedAnchor):
        D.light_fraction_point(5)      # unsupplied


def test_all_models_are_monotone_increasing_between_anchors():
    for name, f in D.MONOTONE_MODELS.items():
        vals = [f(d) for d in (6, 7, 8, 9)]
        assert vals == sorted(vals), name
        assert vals[0] == pytest.approx(0.5)
        assert vals[-1] == pytest.approx(1.0)


# --- the ladder as a typed record --------------------------------------

def test_the_ladder_has_nine_steps():
    assert len(D.build_ladder()) == 9
    assert len(D.DENSITY_STEPS) == 9


def test_individuation_is_qualitative_never_a_fraction():
    """The source gives labels, not numbers, for individuation."""
    for v in D.INDIVIDUATION.values():
        assert isinstance(v, str)
    assert D.INDIVIDUATION[9] == "SOURCE_IDENTITY"


def test_the_ladder_is_a_source_claim_not_a_result():
    r = D.density_report()
    assert r["claim_status"] == "SOURCE_CLAIM"
    assert r["measured_here"] == "nothing"


def test_report_does_not_assert_the_ladder_is_real():
    r = D.density_report()
    assert "does not say the ladder is real" in r["what_this_does_not_say"]


def test_bad_density_id_refused():
    with pytest.raises(ValueError):
        D.interpolate_light_fraction(0)
    with pytest.raises(ValueError):
        D.interpolate_light_fraction(10)
