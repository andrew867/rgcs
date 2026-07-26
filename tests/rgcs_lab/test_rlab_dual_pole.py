"""Program locks — WS05 dual-pole machine: the critic can really block."""

import pytest

from rgcs_lab.authority.dual_pole_machine import (
    DualPoleMachine,
    EvidenceBinding,
    SchemaError,
)


def make_machine():
    m = DualPoleMachine()
    m.propose("C1", "the codec round-trips exactly",
              "IMPLEMENTED_SOFTWARE")
    return m


def test_full_loop_approval_requires_evidence():
    m = make_machine()
    m.attack("C1", "show me the tests")
    with pytest.raises(SchemaError, match="not independent evidence"):
        m.approve("C1", "sounds right to me")        # agreement != evidence
    m.bind_evidence("C1", EvidenceBinding(
        "TEST", "tests/rgcs_coordinate/test_rcw_codec_parity.py"))
    m.approve("C1", "round-trip locked by cited test")
    assert m.claim("C1").state.value == "APPROVED"


def test_blocked_never_jumps_to_approved():
    m = make_machine()
    m.attack("C1", "unsupported")
    m.block("C1", "no evidence bound")
    m.bind_evidence("C1", EvidenceBinding("TEST", "tests/x"))
    with pytest.raises(SchemaError, match="no path from BLOCKED"):
        m.approve("C1", "fixed now")
    m.revise("C1", "the codec round-trips exactly (see parity tests)",
             "bound the tests")
    m.resubmit("C1", "revised")
    m.approve("C1", "evidence now bound")
    assert m.claim("C1").state.value == "APPROVED"


def test_measurement_claims_need_receipts_not_citations():
    m = DualPoleMachine()
    m.propose("M1", "residual of 0.1 W observed", "MEASUREMENT")
    m.attack("M1", "protocol?")
    m.bind_evidence("M1", EvidenceBinding("CITATION", "doi:10/xyz"))
    with pytest.raises(SchemaError, match="RECEIPT"):
        m.approve("M1", "cited")
    m.bind_evidence("M1", EvidenceBinding(
        "RECEIPT", "docs/program/receipts/metasurface.json"))
    m.approve("M1", "receipt bound")


def test_ledger_is_append_only_and_complete():
    m = make_machine()
    m.attack("C1", "attack")
    m.block("C1", "block")
    ledger = m.receipt()["ledger"]
    assert [e["to_state"] for e in ledger] == \
        ["PROPOSED", "UNDER_ATTACK", "BLOCKED"]
    assert all(e["reason"] for e in ledger)
    assert m.receipt()["blocked"] == ["C1"]


def test_transitions_require_reasons_and_roles():
    m = make_machine()
    with pytest.raises(SchemaError, match="may not move"):
        m.resubmit("C1", "skip the critic")     # proposer can't self-attack
    m.attack("C1", "r")
    with pytest.raises(SchemaError, match="reason"):
        m.block("C1", "")
