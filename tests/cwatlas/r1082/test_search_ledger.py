"""P27 — search-space and description-length ledger.

The freedom is counted (families, continuous angle, Wilkes/epoch/codec
alternatives, total selection bits), the degrees of freedom are compared against
the 2 sealed anchors and surfaced honestly, F1/F3 indistinguishability is
counted, per-candidate description length is produced, and determinism holds.
"""

from __future__ import annotations

import math

import pytest

from cwatlas.r1082 import claims, search_ledger as S, spatialization


def test_family_count_and_indistinguishability():
    ledger = S.build_ledger()
    assert ledger.family_count == spatialization.FAMILY_COUNT == 4
    # F1 and F3 collapse at the default root -> fewer distinguishable families.
    assert ledger.distinguishable_families == 3
    assert ledger.distinguishable_families < ledger.family_count


def test_continuous_parameter_is_the_orientation_angle():
    ledger = S.build_ledger()
    assert ledger.continuous_params == S.CONTINUOUS_PARAMS_PER_FAMILY == 1
    assert ledger.continuous_bits() == pytest.approx(
        math.log2(S.ANGLE_RANGE_DEG / S.ANGLE_QUANTISATION_DEG))


def test_selection_bits_counted():
    ledger = S.build_ledger()
    expected_discrete = (math.log2(ledger.family_count)
                         + math.log2(ledger.wilkes_candidates)
                         + math.log2(ledger.epoch_profiles))
    assert ledger.discrete_selection_bits() == pytest.approx(expected_discrete)
    assert ledger.total_selection_bits() == pytest.approx(
        ledger.discrete_selection_bits() + ledger.continuous_bits())
    assert ledger.total_selection_bits() > 0.0


def test_degrees_of_freedom_at_least_sealed_anchors():
    ledger = S.build_ledger()
    dof = ledger.dof_vs_anchors()
    assert dof["sealed_anchors"] == S.SEALED_ANCHORS == 2
    assert dof["degrees_of_freedom"] >= dof["sealed_anchors"]
    # The weakness of the constraint is surfaced honestly, not hidden.
    assert dof["dof_at_least_anchors"] is True
    assert dof["constraint_is_weak"] is True
    assert "weakly constrained" in dof["note"]


def test_per_candidate_description_length():
    ledger = S.build_ledger()
    desc = S.describe_candidate("CAND_1", ledger)
    payload = spatialization.ROUTE_TOKENS * math.log2(spatialization.TOKEN_BASE)
    assert desc.route_payload_bits == pytest.approx(payload)
    assert desc.description_length_bits == pytest.approx(
        ledger.total_selection_bits() + payload)
    assert S.description_length_bits(ledger) == pytest.approx(
        desc.description_length_bits)


def test_constraint_accounting_separates_the_four_kinds():
    acc = S.constraint_accounting()
    assert set(acc) == {
        "exact_arithmetic", "calibration_fit", "holdout_prediction",
        "destination_catalogue_proximity"}
    assert acc["exact_arithmetic"]["fitted_freedom_bits"] == 0.0
    assert acc["calibration_fit"]["sealed_anchors"] == S.SEALED_ANCHORS
    assert acc["destination_catalogue_proximity"]["rewarded"] is False


def test_ledger_deterministic():
    a = S.build_ledger().to_dict()
    b = S.build_ledger().to_dict()
    assert a == b


def test_candidate_not_measured_raises():
    with pytest.raises(claims.R1082ClaimError):
        S.refuse_candidate_as_measured()


def test_report_governance_fields():
    r = S.search_ledger_report()
    assert r["phase_id"] == "P27"
    assert r["tranche"] == "T07"
    assert r["sealed_anchors"] == 2
    assert r["dof_at_least_anchors"] is True
    assert r["constraint_is_weak"] is True
    assert r["famous_place_proximity_rewarded"] is False
    assert len(r["negative_results"]) >= 1
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["physical_effects"] == "PHYSICAL_EFFECTS_NOT_CLAIMED"
    assert r["source_origin"] == "SOURCE_ORIGIN_NOT_VALIDATED"
    assert r["verdict"]
