"""P53 — representation versus relational simplicity.

POWER: a small-integer ladder is relationally simple and that structure
survives re-representation, so it is credited. Negative: values that are round
only in a lucky base (multiples of a power of ten) are flagged as
representation-only and never credited; their roundedness collapses under a
coprime base. Deterministic.
"""

from __future__ import annotations

import pytest

from cwatlas import simplicity as S
from cwatlas.claims import ClaimClass, ClaimError


# --- POWER: relational simplicity survives re-representation -------------------

def test_integer_ladder_is_relational_and_credited():
    # Ratios all 2/1 — simple relations, invariant under base/unit change.
    score = S.assess_simplicity([2, 4, 8, 16, 32])
    assert score.simplicity_class is S.SimplicityClass.RELATIONAL_SIMPLICITY
    assert score.flagged is False
    assert score.claim_class == ClaimClass.MATHEMATICAL_TRANSLATION.value
    assert score.relational_score >= S.REL_THRESHOLD


def test_relational_score_survives_unit_rescale():
    # A unit rescale changes representation roundedness but not the ratios.
    base = [3.0, 6.0, 12.0, 24.0]
    rescaled = [x * 7.31 for x in base]
    assert S.relational_simplicity(base) == pytest.approx(
        S.relational_simplicity(rescaled))


def test_relational_ladder_credited_even_when_not_round():
    # Not round in base-100, but relationally simple -> credited, not flagged.
    score = S.assess_simplicity([3, 6, 12, 24], chosen_base=100)
    assert score.simplicity_class is S.SimplicityClass.RELATIONAL_SIMPLICITY
    assert score.flagged is False


# --- Negative: representation-only simplicity is flagged, not credited ---------

def _base100_round_ugly_ratios():
    # Multiples of 100**3 (round in base 10/100) whose ratios are irrational-ish.
    ladders = [1000, 1414, 1732, 2236]  # ~ 1, sqrt2, sqrt3, sqrt5 (x1000)
    return [n * 1_000_000 for n in ladders]

def test_base100_roundness_is_flagged_representation_only():
    score = S.assess_simplicity(_base100_round_ugly_ratios(), chosen_base=100)
    assert score.simplicity_class is S.SimplicityClass.REPRESENTATION_ONLY
    assert score.flagged is True
    assert score.claim_class != ClaimClass.MATHEMATICAL_TRANSLATION.value


def test_representation_only_roundness_collapses_under_rerepresentation():
    values = _base100_round_ugly_ratios()
    score = S.assess_simplicity(values, chosen_base=100)
    # Round in base-100, but invariant (min over coprime bases) is far lower.
    assert score.representation_score >= S.REP_THRESHOLD
    assert score.invariant_score < score.representation_score
    # And the relations themselves are not simple.
    assert score.relational_score < S.REL_THRESHOLD


def test_refuse_representation_simplicity_as_meaning_raises():
    with pytest.raises(ClaimError):
        S.refuse_representation_simplicity_as_meaning()


def test_no_simplicity_for_unstructured_values():
    # Primes: not round in base-100, ratios not simple -> neither.
    score = S.assess_simplicity([17, 31, 53, 71], chosen_base=100)
    assert score.simplicity_class is S.SimplicityClass.NO_SIMPLICITY
    assert score.flagged is False


# --- Boundary / malformed -----------------------------------------------------

def test_single_value_refused():
    with pytest.raises(S.SimplicityError):
        S.assess_simplicity([5])


def test_non_finite_refused():
    with pytest.raises(S.SimplicityError):
        S.assess_simplicity([1.0, float("inf")])


def test_bad_base_refused():
    with pytest.raises(S.SimplicityError):
        S.assess_simplicity([2, 4], chosen_base=1)


def test_relational_needs_two_distinct_magnitudes():
    with pytest.raises(S.SimplicityError):
        S.relational_simplicity([5.0, 5.0])


# --- Determinism --------------------------------------------------------------

def test_assessment_is_deterministic():
    a = S.assess_simplicity([2, 4, 8, 16])
    b = S.assess_simplicity([2, 4, 8, 16])
    assert a == b


def test_report_declares_boundary():
    r = S.simplicity_report()
    assert r["source_vector_geographic_semantics"] == "NOT_CLAIMED"
    assert r["representation_only_is_credited"] is False
