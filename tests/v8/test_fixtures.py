"""R15 P06 — the fixture registry and its boundary conditions.

Focused: a boundary condition shifts the synthetic modal frequency as
modelled, and changing the support changes the modes. Negative: a
fixture-induced shift is a FIXTURE_EFFECT, not a signal, and the refusals
fire; a fixture id and a specimen id cannot swap; a missing preload blocks
a precision claim. Determinism: the same mount yields the same binding
hash, and a remount yields a distinct one.
"""

from __future__ import annotations

import json

import jsonschema
import pytest

from r15 import claims as C
from r15 import fixtures as F


# --- schema conformance ---------------------------------------------------

def _record_schema() -> dict:
    with open("r15/schemas/fixture_record.schema.json") as fh:
        return json.load(fh)


def _budget_schema() -> dict:
    with open("r15/schemas/error_budget.schema.json") as fh:
        return json.load(fh)


def test_every_registered_record_conforms_to_schema():
    schema = _record_schema()
    assert len(F.FIXTURE_REGISTRY) == 6
    for fid in F.FIXTURE_REGISTRY:
        jsonschema.validate(F.fixture(fid).as_record(), schema)


def test_registry_covers_the_six_mount_types():
    kinds = {F.fixture(fid).mount_type for fid in F.FIXTURE_REGISTRY}
    assert kinds == set(F.MountType)


def test_error_budget_conforms_to_schema():
    schema = _budget_schema()
    for fid in F.FIXTURE_REGISTRY:
        jsonschema.validate(F.fixture_error_budget(F.fixture(fid)), schema)


# --- focused: boundary conditions shift the synthetic modes ---------------

def test_boundary_condition_shifts_modal_frequency_as_modelled():
    free = F.modal_frequencies(F.BoundaryCondition.FREE)
    spring = F.modal_frequencies(F.BoundaryCondition.SPRING)
    fixed = F.modal_frequencies(F.BoundaryCondition.FIXED)
    # a stiffer end raises the fundamental: FREE < SPRING < FIXED
    assert free[0] < spring[0] < fixed[0]


def test_changing_support_changes_synthetic_modes():
    before = F.modal_frequencies(F.BoundaryCondition.FREE)
    after = F.modal_frequencies(F.BoundaryCondition.FIXED)
    assert before.shape == after.shape
    # every mode moves; the support change is not a no-op
    assert not (before == after).any()


def test_fixture_modal_shift_reports_a_nonzero_fractional_shift():
    shift = F.fixture_modal_shift(F.BoundaryCondition.FREE,
                                  F.BoundaryCondition.FIXED)
    assert shift.delta > 0.0
    assert shift.fractional_shift > 0.0


def test_fixture_change_is_booked_as_ordinary_boundary_work():
    ledger = F.fixture_change_ledger(F.BoundaryCondition.FREE,
                                     F.BoundaryCondition.FIXED)
    # the R13 energy ledger closes and asserts no new energy channel
    assert ledger["ledger"]["closes"] is True
    assert ledger["ledger"]["residual_is_new_energy"] is False


# --- negative: a fixture effect is not a signal ---------------------------

def test_fixture_shift_is_classified_as_a_fixture_effect():
    result = F.fixture_shift_is_ordinary(F.BoundaryCondition.SPRING,
                                         F.BoundaryCondition.FIXED)
    assert result["claim_class"] == C.ClaimClass.FIXTURE_EFFECT.value
    assert result["is_signal"] is False
    assert result["is_ordinary"] is True


def test_refuse_fixture_effect_as_signal_raises():
    with pytest.raises(F.FixtureError):
        F.refuse_fixture_effect_as_signal(0.05, "a specimen resonance")


def test_fixture_effect_is_an_ordinary_explanation_class_not_measurement():
    cls = C.ClaimClass.FIXTURE_EFFECT
    assert cls not in C.MEASUREMENT_CLASSES
    assert cls not in C.SOFTWARE_CLASSES


# --- negative: fixture and specimen ids cannot swap -----------------------

def test_a_specimen_id_cannot_be_used_as_a_fixture_id():
    with pytest.raises(F.FixtureError):
        F.check_fixture_id("SPX-001")


def test_a_fixture_id_cannot_be_used_as_a_specimen_id():
    with pytest.raises(F.FixtureError):
        F.check_specimen_id("FIX-CENTRE-CLAMP")


def test_mounting_refuses_a_fixture_id_in_the_specimen_slot():
    fx = F.fixture("FIX-CENTRE-CLAMP")
    with pytest.raises(F.FixtureError):
        F.mount(fx, "FIX-OTHER", 0)


def test_a_record_with_a_specimen_shaped_id_is_refused_at_construction():
    with pytest.raises(F.FixtureError):
        F.FixtureRecord(
            fixture_id="SPX-999",
            mount_type=F.MountType.SYNTHETIC,
            contact_points=(F.ContactPoint("c", (0.0, 0.0, 0.0),
                                           F.BoundaryCondition.SPRING, 1.0),),
            preload=F.Preload(clamp_force_n=1.0),
            materials=("x",))


# --- negative: a missing preload blocks precision claims ------------------

def test_missing_preload_blocks_a_precision_claim():
    fx = F.fixture("FIX-SUSPENSION")  # preload clamp force is None
    assert fx.preload.is_known is False
    assert F.precision_claim_supported(fx) is False
    with pytest.raises(F.FixtureError):
        F.assert_precision_claim(fx)


def test_recorded_preload_supports_a_precision_claim():
    fx = F.fixture("FIX-CENTRE-CLAMP")  # preload clamp force recorded
    assert fx.preload.is_known is True
    assert F.precision_claim_supported(fx) is True
    F.assert_precision_claim(fx)  # does not raise


def test_error_budget_flags_whether_the_preload_is_known():
    known = F.fixture_error_budget(F.fixture("FIX-CENTRE-CLAMP"))
    unknown = F.fixture_error_budget(F.fixture("FIX-SUSPENSION"))
    assert known["preload_known"] is True
    assert unknown["preload_known"] is False


# --- remounting is a new binding ------------------------------------------

def test_remounting_generates_a_distinct_run_binding():
    fx = F.fixture("FIX-CENTRE-CLAMP")
    first = F.mount(fx, "SPX-042", 0)
    again = F.remount(fx, first)
    assert again.mount_index == first.mount_index + 1
    assert again.binding_hash != first.binding_hash
    assert again.binding_id != first.binding_id
    # same specimen, same fixture, different mount
    assert again.specimen_id == first.specimen_id
    assert again.fixture_id == first.fixture_id


def test_remount_must_use_the_same_fixture():
    fx = F.fixture("FIX-CENTRE-CLAMP")
    other = F.fixture("FIX-THREE-POINT")
    first = F.mount(fx, "SPX-042", 0)
    with pytest.raises(F.FixtureError):
        F.remount(other, first)


# --- determinism ----------------------------------------------------------

def test_binding_hash_is_deterministic():
    fx = F.fixture("FIX-ELASTOMER")
    a = F.mount(fx, "SPX-777", 2)
    b = F.mount(fx, "SPX-777", 2)
    assert a.binding_hash == b.binding_hash
    assert a.binding_id == b.binding_id


def test_modal_frequencies_are_deterministic():
    a = F.modal_frequencies(F.BoundaryCondition.SPRING)
    b = F.modal_frequencies(F.BoundaryCondition.SPRING)
    assert (a == b).all()


def test_content_hash_is_deterministic():
    fx = F.fixture("FIX-ADHESIVE")
    assert fx.content_hash() == F.fixture("FIX-ADHESIVE").content_hash()


# --- plans ----------------------------------------------------------------

def test_reversal_plan_alternates_reversal_and_is_not_executed():
    plan = F.reversal_plan(F.fixture("FIX-THREE-POINT"), n_remounts=4)
    assert plan["executed"] is False
    reversals = [s["reversal_deg"] for s in plan["steps"]]
    assert reversals == [0.0, 180.0, 0.0, 180.0]


def test_sensor_permutation_plan_is_deterministic_and_capped():
    plan = F.sensor_permutation_plan(("s1", "s2", "s3"), max_permutations=4)
    assert plan["n_permutations"] == 4
    assert plan["permutations"][0] == ["s1", "s2", "s3"]
    assert plan["executed"] is False


def test_sensor_permutation_plan_refuses_duplicate_labels():
    with pytest.raises(F.FixtureError):
        F.sensor_permutation_plan(("s1", "s1"))


# --- report claims nothing ------------------------------------------------

def test_report_claims_nothing_measured():
    r = F.fixtures_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == C.ClaimClass.SYNTHETIC_FIXTURE.value
    assert r["id_namespaces"]["can_swap"] is False
    assert r["verdict"] == F.VERDICT
