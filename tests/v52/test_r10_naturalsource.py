"""P03 — natural-quartz source requirement, public translation."""

from __future__ import annotations

import pytest

from r10 import naturalsource as NS


def test_the_primary_lane_is_natural_and_controls_are_mandatory():
    d = NS.design_lanes()
    assert d["primary"] == NS.Lane.NATURAL_GEOLOGICAL_QUARTZ.value
    assert NS.Lane.HYDROTHERMAL_SYNTHETIC_QUARTZ.value in d["controls"]
    assert NS.Lane.FUSED_SILICA.value in d["controls"]
    assert NS.Lane.NONQUARTZ_GLASS.value in d["controls"]
    assert d["verdict"] == "SOURCE_REQUIRED_EXPERIMENTALLY_UNRESOLVED"


def test_public_view_never_emits_the_private_interpretation():
    req = NS.SourceRequirement("R1", private_interpretation="global heart lore")
    pv = req.public_view()
    assert "global heart" not in str(pv)
    assert "lore" not in str(pv)
    assert pv["endorsed_as_materials_science"] is False
    assert pv["evidence_status"] == "SOURCE_REQUIRED_EXPERIMENTALLY_UNRESOLVED"


def test_consciousness_is_not_published_as_materials_science():
    with pytest.raises(NS.NaturalSourceError):
        NS.refuse_publish_consciousness_as_materials_science()


def test_a_synthetic_control_cannot_be_dropped():
    for lane in NS.CONTROL_LANES:
        with pytest.raises(NS.NaturalSourceError):
            NS.refuse_drop_synthetic_control(lane)
    # the natural primary lane is not a control, so it does not raise
    NS.refuse_drop_synthetic_control(NS.Lane.NATURAL_GEOLOGICAL_QUARTZ)


def test_no_natural_superiority_claim():
    with pytest.raises(NS.NaturalSourceError):
        NS.refuse_natural_superiority_claim()


def test_ordinary_differentiators_are_the_first_explanation():
    assert "trace_elements" in NS.ORDINARY_DIFFERENTIATORS
    assert "acoustic_Q" in NS.ORDINARY_DIFFERENTIATORS


def test_report_states_source_required_but_unresolved():
    r = NS.naturalsource_report()
    assert r["verdict"] == "SOURCE_REQUIRED_EXPERIMENTALLY_UNRESOLVED"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "consciousness" in r["what_this_does_not_say"].lower()
