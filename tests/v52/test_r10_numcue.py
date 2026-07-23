"""P04 — numeric-cue and search-budget preregistration registry."""

from __future__ import annotations

from fractions import Fraction as F

import pytest

from r10 import numcue as N


def _make(**kw):
    """A prospective cue with sensible defaults, overridable per test."""
    defaults = dict(
        cue_id="CUE_1604", raw_token="1604", parsed_value=F(1604),
        units=None, significant_digits=4, spoken_digits="1-6-0-4",
        timestamp="2026-07-21T00:00:00Z",
        candidate_roles=("YEAR", "FREQUENCY_HZ"),
        allowed_transforms=("IDENTITY", "AS_YEAR"),
        search_budget=2, provenance=N.Provenance.PROSPECTIVE)
    defaults.update(kw)
    return N.register_cue(
        defaults.pop("cue_id"), defaults.pop("raw_token"),
        defaults.pop("parsed_value"), **defaults)


# --- hashing / tamper detection ----------------------------------------

def test_register_freezes_a_hash_that_verifies():
    cue = _make()
    assert cue.hash                       # a hash was computed
    assert N.verify_hash(cue)


def test_mutating_a_committed_field_breaks_the_hash():
    cue = _make()
    cue.parsed_value = F(9999)            # tamper with a committed field
    assert not N.verify_hash(cue)


def test_widening_allowed_transforms_breaks_the_hash():
    cue = _make()
    cue.allowed_transforms = cue.allowed_transforms + ("TIMES_FOUR",)
    assert not N.verify_hash(cue)


# --- transforms within / outside the commitment ------------------------

def test_allowed_transform_within_budget_applies():
    cue = _make()
    N.apply_transform(cue, "IDENTITY", residual=F(0))
    assert cue.applied_transforms == ["IDENTITY"]
    assert cue.status is N.CueStatus.TRANSFORM_APPLIED


def test_unregistered_transform_is_refused():
    cue = _make()
    with pytest.raises(N.NumCueError):
        N.apply_transform(cue, "TIMES_FOUR")


def test_exceeding_the_search_budget_is_refused():
    cue = _make(search_budget=1)
    N.apply_transform(cue, "IDENTITY")
    with pytest.raises(N.NumCueError):
        N.apply_transform(cue, "AS_YEAR")
    assert cue.status is N.CueStatus.BUDGET_EXHAUSTED


def test_refuse_helpers_raise_directly():
    cue = _make()
    with pytest.raises(N.NumCueError):
        N.refuse_unregistered_transform(cue, "TIMES_FOUR")
    with pytest.raises(N.NumCueError):
        N.refuse_budget_exhausted(cue)


# --- retrospective rule ------------------------------------------------

def test_retrospective_cue_with_unregistered_transform_is_refused():
    cue = _make(provenance=N.Provenance.RETROSPECTIVE,
                allowed_transforms=("IDENTITY",))
    assert cue.retrospective and not cue.prospective
    with pytest.raises(N.NumCueError):
        N.apply_transform(cue, "AS_YEAR")


def test_a_preregistered_transform_still_applies_to_a_retrospective_cue():
    cue = _make(provenance=N.Provenance.RETROSPECTIVE,
                allowed_transforms=("IDENTITY",), search_budget=1)
    N.apply_transform(cue, "IDENTITY")
    assert cue.applied_transforms == ["IDENTITY"]


# --- unit invention ----------------------------------------------------

def test_inventing_a_unit_is_refused():
    cue = _make()
    for unit in ("years", "hertz", "kilometres", "degrees"):
        with pytest.raises(N.NumCueError):
            N.refuse_unit_invention(cue, unit)


# --- schema hygiene ----------------------------------------------------

def test_spoken_digits_kept_distinct_from_parsed_value():
    cue = _make()
    assert cue.spoken_digits == "1-6-0-4"
    assert cue.parsed_value == F(1604)
    assert cue.spoken_digits != str(cue.parsed_value)


def test_units_are_none_unless_provided():
    assert _make().units is None
    assert _make(units="hertz").units == "hertz"


def test_default_cues_register_and_verify():
    cues = N.register_default_cues()
    assert set(cues) == {c[0] for c in N.CUE_TOKENS}
    assert all(N.verify_hash(c) for c in cues.values())
    assert all(c.units is None for c in cues.values())


def test_tampered_cue_cannot_be_transformed():
    cue = _make()
    cue.timestamp = "2099-01-01T00:00:00Z"    # tamper
    with pytest.raises(N.NumCueError):
        N.apply_transform(cue, "IDENTITY")


# --- report ------------------------------------------------------------

def test_report_measures_nothing():
    r = N.numcue_report()
    assert r["measured_here"] == "nothing"
    assert r["evidence_class"] == "DERIVED_MATHEMATICS"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["units_all_unresolved"]
    assert r["spoken_distinct_from_value"]
    assert "post-hoc" in r["what_this_does_not_say"]
