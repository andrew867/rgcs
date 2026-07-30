"""Program locks — shared status schema and the Physics Truth Gate."""

import pytest

from rgcs_lab.authority import physics_truth_gate as gate
from rgcs_lab.common import status_schema as ss


def test_module_and_status_vocabulary():
    assert len(ss.MODULES) == 9
    assert ss.STATUSES == ("GREEN", "YELLOW", "RED")
    with pytest.raises(ss.SchemaError, match="unknown module"):
        ss.ModuleStatus("warpdrive", "GREEN", ("IMPLEMENTED_SOFTWARE",))
    with pytest.raises(ss.SchemaError, match="claim class"):
        ss.ModuleStatus("golay", "GREEN", ("TOTALLY_PROVEN",))


def test_badge_text_derives_from_schema():
    s = ss.ModuleStatus("golay", "GREEN",
                        (ss.ClaimClass.EXACT_ARITHMETIC.value,))
    assert s.badge_text() == "GOLAY: GREEN"


def test_banned_public_wording_refused_in_results():
    with pytest.raises(ss.SchemaError, match="banned public wording"):
        ss.ModuleStatus(
            "metasurface", "GREEN",
            (ss.ClaimClass.EXPLORATORY_MODEL.value,),
            result={"summary": "this is confirmed anti-gravity"})


def test_receipt_validation():
    good = {"module": "golay", "version": "0.1", "source_commit": "abc",
            "status": "GREEN", "claim_class": ["EXACT_ARITHMETIC"],
            "inputs": {}, "models": [], "result": {}, "tests": ["t"]}
    assert ss.validate_receipt(good)["valid"]
    for key in ss.REQUIRED_RECEIPT_KEYS:
        bad = dict(good)
        del bad[key]
        with pytest.raises(ss.SchemaError, match="missing required"):
            ss.validate_receipt(bad)
    assert ss.receipt_schema()["title"].startswith("RGCS")


def test_truth_gate_lists_are_complete():
    assert len(gate.IMPLEMENTABLE_EFFECTS) == 15
    assert len(gate.NEVER_PROMOTE) == 13
    assert len(gate.PROMOTION_PROTOCOL) == 9
    assert len(gate.ENERGY_LEDGER_FIELDS) == 12


def test_concept_boundaries_are_separate_and_conflation_refused():
    ids = [c.concept_id for c in gate.CONCEPT_BOUNDARIES]
    assert ids == ["PARAMETRIC_RESONANCE", "INTRINSIC_SPIN",
                   "TORSION", "QET"]
    # each declares its own energy boundary mentioning conservation-
    # relevant language, and its own evidence boundary
    for c in gate.CONCEPT_BOUNDARIES:
        assert c.energy_boundary and c.evidence_boundary
    with pytest.raises(gate.SchemaError, match="combined mechanism"):
        gate.refuse_concept_conflation("PARAMETRIC_RESONANCE", "TORSION")
    with pytest.raises(gate.SchemaError, match="combined mechanism"):
        gate.refuse_concept_conflation("INTRINSIC_SPIN", "QET")


def test_banned_claim_screen():
    hits = gate.screen_text_for_banned_claims(
        "our device shows that parametric resonance amplifies gravity")
    assert hits == ["parametric resonance amplifies gravity"]
    assert gate.screen_text_for_banned_claims(
        "parametric resonance transfers energy from the pump") == []


def test_energy_ledger_must_close():
    ledger = {f: 0.0 for f in gate.ENERGY_LEDGER_FIELDS}
    ledger.update({"input_electrical_power_w": 10.0,
                   "thermal_loss_w": 6.0, "ohmic_loss_w": 3.0,
                   "measured_mechanical_output_w": 0.9,
                   "unexplained_residual_w": 0.1,
                   "unexplained_residual_uncertainty_w": 0.05})
    report = gate.validate_energy_ledger(ledger)
    assert report["closes"]
    assert report["conclusion_ceiling"] == \
        "anomalous residual detected under protocol X"
    ledger["unexplained_residual_w"] = 2.0     # narrate a fake surplus
    with pytest.raises(gate.SchemaError, match="does not close"):
        gate.validate_energy_ledger(ledger)
    with pytest.raises(gate.SchemaError, match="missing mandatory"):
        gate.validate_energy_ledger({"input_electrical_power_w": 1.0})
