"""P12 — Cs-Ba epoch profile registry.

Half-life / decay / phase-wrap / epoch-origin / uncertainty behaviour, the
separateness of the isotope lanes (none proven, none selected), and the
mandatory conventional timestamp. Deterministic throughout.
"""

from __future__ import annotations

import math

import pytest

from cwatlas.r1082 import epoch_profiles as ep
from cwatlas.r1082.claims import R1082ClaimError

_UTC = {"timescale": "UTC", "value": "2000-01-01T00:00:00Z"}


# -- five distinct, separate lanes ------------------------------------------

def test_five_distinct_profiles():
    assert len(list(ep.EpochProfileId)) == 5
    assert len(ep.PROFILE_REGISTRY) == 5
    ids = {p.profile_id for p in ep.PROFILE_REGISTRY.values()}
    assert ids == set(ep.EpochProfileId)


def test_constants_and_ontology_are_separate_fields():
    prof = ep.get_profile(ep.EpochProfileId.CS137_DECAY_ENVELOPE)
    # physical constants live apart from the source interpretation
    assert isinstance(prof.constants, ep.IsotopeConstants)
    assert isinstance(prof.ontology, ep.SourceOntology)
    assert prof.constants.isotope == "Cs-137"
    assert "envelope" in prof.ontology.interpretation


# -- half-life / decay ------------------------------------------------------

def test_cs137_half_at_one_half_life():
    frac = ep.cs137_decay_envelope(ep.CS137_HALF_LIFE_S)["remaining_fraction"]
    assert frac == pytest.approx(0.5)


def test_cs137_quarter_at_two_half_lives():
    frac = ep.cs137_decay_envelope(2 * ep.CS137_HALF_LIFE_S)["remaining_fraction"]
    assert frac == pytest.approx(0.25)


def test_ba137_daughter_equals_parent_at_one_half_life():
    ratio = ep.ba137_daughter_ratio(
        ep.CS137_HALF_LIFE_S)["daughter_parent_ratio"]
    assert ratio == pytest.approx(1.0)


def test_ba130_parent_full_on_human_scale():
    frac = ep.ba130_parent_full(1e9)["remaining_fraction"]  # ~32 years
    assert frac > 0.999999999


# -- phase wrap -------------------------------------------------------------

def test_cs133_phase_in_unit_interval():
    for t in (0.123456789, 1.5, 42.0):
        p = ep.cs133_fine_phase(t)["phase"]
        assert 0.0 <= p < 1.0


def test_cs133_phase_wraps_by_whole_cycles():
    t = 0.123456789
    p1 = ep.cs133_fine_phase(t)["phase"]
    p2 = ep.cs133_fine_phase(t + 3.0 / ep.CS133_HYPERFINE_HZ)["phase"]
    assert p1 == pytest.approx(p2, abs=1e-6)


# -- epoch origin -----------------------------------------------------------

def test_epoch_origin_zero_state():
    assert ep.cs133_fine_phase(0.0)["phase"] == 0.0
    assert ep.cs137_decay_envelope(0.0)["remaining_fraction"] == 1.0
    assert ep.ba137_daughter_ratio(0.0)["daughter_parent_ratio"] == 0.0
    assert ep.ba130_parent_full(0.0)["remaining_fraction"] == 1.0


# -- uncertainty ------------------------------------------------------------

def test_uncertainty_present_for_decay_lanes_zero_for_si():
    # the SI-defined Cs-133 frequency has zero relative uncertainty
    assert ep.get_profile(
        ep.EpochProfileId.CS133_FINE_PHASE).constants.uncertainty_rel == 0.0
    # the measured half-life lanes carry a positive relative uncertainty
    for pid in (ep.EpochProfileId.CS137_DECAY_ENVELOPE,
                ep.EpochProfileId.BA137_DAUGHTER_RATIO,
                ep.EpochProfileId.BA130_PARENT_FULL):
        assert ep.get_profile(pid).constants.uncertainty_rel > 0.0


# -- composite / variable depth ---------------------------------------------

def test_composite_full_and_short():
    full = ep.composite_variable_depth(1.0, full=True)
    short = ep.composite_variable_depth(1.0, full=False)
    assert "fine" in full and "coarse" in full
    assert "fine" not in short and "coarse" in short


# -- no lane proven, no lane selected ---------------------------------------

def test_lane_cannot_be_marked_proven():
    prof = ep.get_profile(ep.EpochProfileId.CS137_DECAY_ENVELOPE)
    assert prof.proven is False
    with pytest.raises(R1082ClaimError):
        ep.EpochProfile(prof.profile_id, prof.constants, prof.ontology,
                        proven=True)


def test_silent_lane_selection_refused():
    with pytest.raises(R1082ClaimError):
        ep.refuse_lane_selected()


def test_compare_reports_all_lanes_without_selecting():
    report = ep.compare_profiles(ep.CS137_HALF_LIFE_S)
    assert report["selected"] is None
    assert set(report["lanes"]) == {p.value for p in ep.EpochProfileId}
    assert all(not lane["proven"] for lane in report["lanes"].values())


# -- conventional timestamp mandatory ---------------------------------------

def test_certificate_requires_conventional_timestamp():
    cert = ep.build_certificate(
        ep.EpochProfileId.CS137_DECAY_ENVELOPE, 1.0, conventional_epoch=_UTC)
    assert cert["conventional_epoch"]["timescale"] == "UTC"
    assert cert["compressed_epoch"]["profile"] == "CS137_DECAY_ENVELOPE"
    # isotope constants and source ontology remain separate fields
    assert "isotope_constants" in cert and "source_ontology" in cert


@pytest.mark.parametrize("bad", [{}, {"value": "x"},
                                 {"timescale": "GPS", "value": "x"},
                                 {"timescale": "UTC"}])
def test_certificate_refuses_missing_or_bad_timescale(bad):
    with pytest.raises(R1082ClaimError):
        ep.build_certificate(ep.EpochProfileId.CS133_FINE_PHASE, 1.0,
                             conventional_epoch=bad)


# -- determinism + report ---------------------------------------------------

def test_determinism():
    a = ep.compare_profiles(12345.0)
    b = ep.compare_profiles(12345.0)
    assert a == b
    assert not math.isnan(
        a["lanes"]["CS137_DECAY_ENVELOPE"]["value"]["remaining_fraction"])


def test_report_seals_claims():
    r = ep.epoch_profiles_report()
    assert r["measured_here"] == "nothing"
    assert r["no_lane_proven"] is True and r["no_lane_selected"] is True
    assert r["conventional_timestamp_mandatory"] is True
    assert len(r["profiles"]) == 5
