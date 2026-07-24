"""P44 — preregistration and blinding: seal the plan before the data."""

from __future__ import annotations

from dataclasses import replace

import pytest

from r13 import preregister as P


def _complete_prereg(**overrides) -> P.Preregistration:
    """A fully populated, well-formed preregistration for the tests."""
    base = dict(
        study_id="TEST_STUDY",
        hypothesis="treatment shifts the mean above the null band",
        predicted_signature="mean exceeds null by the preregistered margin",
        null_model="permuted labels preserving both marginals",
        decision_rule="declare support only if excess > 0.15 on held-out data",
        analysis_plan="freeze, reveal once, compute against four nulls",
        stopping_rule="fixed n = 160, no interim looks",
        power_on_planted="recovers a planted effect at zero residual",
        epoch_committed=20260724,
    )
    base.update(overrides)
    return P.Preregistration(**base)


# --- construction refusals (R10.6 lesson) ------------------------------

def test_empty_null_model_is_refused_at_construction():
    with pytest.raises(P.PreregisterError):
        _complete_prereg(null_model="")
    with pytest.raises(P.PreregisterError):
        _complete_prereg(null_model="   ")


def test_empty_decision_rule_is_refused_at_construction():
    with pytest.raises(P.PreregisterError):
        _complete_prereg(decision_rule="")
    with pytest.raises(P.PreregisterError):
        _complete_prereg(decision_rule="   ")


def test_a_complete_prereg_constructs_and_declares_prospective_prediction():
    prereg = _complete_prereg()
    assert prereg.claim_class == "PROSPECTIVE_PREDICTION"
    assert prereg.claim_class == P.PROSPECTIVE_PREDICTION


# --- sealing: deterministic and tamper-evident (POWER) -----------------

def test_seal_is_deterministic():
    prereg = _complete_prereg()
    assert P.seal(prereg) == P.seal(prereg)
    # Rebuilding an identical plan yields the identical seal.
    assert P.seal(prereg) == P.seal(_complete_prereg())


def test_seal_changes_when_the_hypothesis_changes():
    prereg = _complete_prereg()
    edited = replace(prereg, hypothesis="a different hypothesis entirely")
    assert P.seal(edited) != P.seal(prereg)


def test_seal_changes_when_the_analysis_plan_changes():
    prereg = _complete_prereg()
    edited = replace(prereg, analysis_plan="peek, then choose the test")
    assert P.seal(edited) != P.seal(prereg)


def test_seal_is_stable_across_epoch_only_when_epoch_is_unchanged():
    # The epoch is a sealed field passed in explicitly (no wall clock),
    # so two different committed epochs give two different seals, and the
    # same epoch always gives the same seal.
    a = _complete_prereg(epoch_committed=20260101)
    b = _complete_prereg(epoch_committed=20260102)
    assert P.seal(a) != P.seal(b)
    assert P.seal(a) == P.seal(_complete_prereg(epoch_committed=20260101))


# --- blinding ----------------------------------------------------------

def test_blinding_hides_assignment():
    labels = ("TREATMENT", "CONTROL", "TREATMENT", "CONTROL")
    salt = P.seal(_complete_prereg())
    blinding = P.blind_labels(labels, salt)
    # Codes are opaque and share nothing with the real condition names.
    assert P.blinding_hides_assignment(blinding)
    assert set(blinding.blinded_labels).isdisjoint(set(labels))
    # Structure survives: same condition -> same code, different -> different.
    assert blinding.blinded_labels[0] == blinding.blinded_labels[2]
    assert blinding.blinded_labels[0] != blinding.blinded_labels[1]


def test_blinding_is_deterministic():
    labels = ("A", "B", "A")
    salt = P.seal(_complete_prereg())
    assert P.blind_labels(labels, salt).blinded_labels == \
        P.blind_labels(labels, salt).blinded_labels


def test_unblind_requires_the_sealed_commitment():
    labels = ("TREATMENT", "CONTROL")
    salt = P.seal(_complete_prereg())
    blinding = P.blind_labels(labels, salt)
    # The correct sealed commitment reveals the true labels.
    assert P.unblind(salt, blinding) == labels
    # A wrong commitment reveals nothing.
    with pytest.raises(P.PreregisterError):
        P.unblind("not-the-commitment", blinding)
    with pytest.raises(P.PreregisterError):
        P.unblind("", blinding)


# --- the four forbidden retrofits --------------------------------------

def test_refuse_hypothesis_change_after_seal_raises():
    sealed = _complete_prereg()
    P.seal(sealed)
    retrofitted = replace(sealed, hypothesis="the result we happened to get")
    with pytest.raises(P.PreregisterError):
        P.refuse_hypothesis_change_after_seal(sealed, retrofitted)


def test_an_unchanged_hypothesis_after_seal_is_allowed():
    sealed = _complete_prereg()
    out = P.refuse_hypothesis_change_after_seal(sealed, sealed)
    assert out["allowed"] is True
    assert out["changed_fields"] == []


def test_refuse_result_without_prereg_raises():
    with pytest.raises(P.PreregisterError):
        P.refuse_result_without_prereg(None)
    with pytest.raises(P.PreregisterError):
        P.refuse_result_without_prereg("a-commitment-never-sealed")
    # A genuinely sealed commitment is accepted (no raise).
    commitment = P.seal(_complete_prereg(study_id="SEALED_FOR_RESULT"))
    P.refuse_result_without_prereg(commitment)


def test_refuse_optional_stopping_raises_without_a_stopping_rule():
    with pytest.raises(P.PreregisterError):
        P.refuse_optional_stopping()
    no_rule = _complete_prereg(study_id="NO_STOP", stopping_rule="")
    with pytest.raises(P.PreregisterError):
        P.refuse_optional_stopping(no_rule)
    # A preregistered stopping rule makes the sequential stop legitimate.
    out = P.refuse_optional_stopping(_complete_prereg())
    assert out["allowed"] is True
    assert out["has_preregistered_stopping_rule"] is True


def test_refuse_prediction_as_result_raises():
    with pytest.raises(P.PreregisterError):
        P.refuse_prediction_as_result()


def test_all_four_refusals_raise():
    sealed = _complete_prereg()
    retrofitted = replace(sealed, hypothesis="post-hoc hypothesis")
    for call in (
        lambda: P.refuse_hypothesis_change_after_seal(sealed, retrofitted),
        lambda: P.refuse_result_without_prereg(None),
        lambda: P.refuse_optional_stopping(),
        lambda: P.refuse_prediction_as_result(),
    ):
        with pytest.raises(P.PreregisterError):
            call()


# --- power discipline --------------------------------------------------

def test_requires_power_on_planted_data_flags_a_missing_declaration():
    missing = _complete_prereg(study_id="NO_POWER", power_on_planted="")
    flagged = P.requires_power_on_planted_data(missing)
    assert flagged["flagged"] is True
    assert flagged["declares_power_on_planted"] is False
    present = P.requires_power_on_planted_data(_complete_prereg())
    assert present["flagged"] is False
    assert present["declares_power_on_planted"] is True


# --- validation checklist ----------------------------------------------

def test_validate_passes_a_complete_prereg():
    out = P.validate(_complete_prereg())
    assert out["complete"] is True
    assert out["missing"] == []
    assert all(out["checklist"].values())


def test_validate_fails_a_prereg_missing_a_stopping_rule():
    out = P.validate(_complete_prereg(stopping_rule=""))
    assert out["complete"] is False
    assert "has_stopping_rule" in out["missing"]


def test_validate_fails_a_prereg_missing_the_power_declaration():
    out = P.validate(_complete_prereg(power_on_planted=""))
    assert out["complete"] is False
    assert "has_power_declaration" in out["missing"]


# --- the report --------------------------------------------------------

def test_report_verdict_and_measures_nothing():
    r = P.preregister_report()
    assert r["verdict"] == "PREREGISTRATION_AND_BLINDING_SEALED"
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["claim_class"] == "PROSPECTIVE_PREDICTION"
    assert r["seal_is_deterministic"] is True
    assert r["blinding"]["hides_assignment"] is True
    assert len(r["refusals"]) == 4


def test_import_surface():
    from r13 import preregister  # noqa: F401
    assert hasattr(preregister, "Preregistration")
    assert hasattr(preregister, "seal")
