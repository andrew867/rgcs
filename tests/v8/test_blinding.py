"""R15 P09 — blind operator mode: masking, gated unblind, broken-blind cost.

Focused tests (the blind hides the assignment; unblinding requires the
sealed commitment, a locked dataset, and an authorized role), negative
tests (unblind before lock refused, wrong commitment rejected, analyst has
no authority, exploratory cannot be relabelled confirmatory), and a
determinism check.
"""

from __future__ import annotations

import pytest

from r13 import preregister as _prereg
from r15 import blinding as B


# -- fixtures -----------------------------------------------------------

def _commitment() -> str:
    return B.EXAMPLE_COMMITMENT


def _session(mode=B.StudyMode.CONFIRMATORY) -> B.BlindOperatorSession:
    return B.BlindOperatorSession(
        study_id="TEST_STUDY",
        mode=mode,
        sealed_commitment=_commitment(),
        assignments=B.example_assignments(),
    )


# -- focused: the operator sees no assignment ---------------------------

def test_operator_packet_contains_no_assignment():
    session = _session()
    packets = session.operator_packets()
    for packet, assignment in zip(packets, session.assignments):
        assert B.packet_hides_assignment(packet, assignment)
        # no code equals any real value
        for code in packet.all_codes():
            assert code not in assignment.real_values()


def test_ui_payload_is_free_of_assignment():
    session = _session()
    packet = session.operator_packets()[0]
    payload = B.ui_payload(packet)
    assert payload["blinded"] is True
    assert "condition_label" not in payload
    assert not B.payload_leaks_assignment(payload, session.assignments[0])


def test_blinding_hides_assignment_property():
    bl = B.blind(("CONDITION_A", "CONDITION_B", "CONDITION_A"), _commitment())
    assert B.blinding_hides_assignment(bl)
    # structure is preserved: two units in one condition share a code
    assert bl.blinded_labels[0] == bl.blinded_labels[2]
    assert bl.blinded_labels[0] != bl.blinded_labels[1]


# -- focused: unblind requires the sealed commitment, lock, authority ---

def test_authorized_unblind_after_lock_reveals_labels():
    session = _session()
    session.operator_packets()
    session.lock({"samples": [1, 2, 3]}, epoch=1000)
    result = session.unblind(B.Role.CUSTODIAN, _commitment(), epoch=1001)
    assert result["revealed_labels"] == list(session.condition_labels())
    assert session.stage is B.Stage.UNBLINDED


def test_unblind_requires_the_sealed_commitment():
    bl = B.blind(("CONDITION_A", "CONDITION_B"), _commitment())
    # the true commitment lifts the blind
    assert B.unblind(_commitment(), bl) == ("CONDITION_A", "CONDITION_B")


def test_unblinder_role_is_authorized():
    session = _session()
    session.lock({"samples": [1]}, epoch=1)
    result = session.unblind(B.Role.UNBLINDER, _commitment(), epoch=2)
    assert result["by_role"] == "UNBLINDER"


# -- negative: unblind before the data are locked is refused ------------

def test_unblind_before_lock_is_refused():
    session = _session()
    session.operator_packets()
    assert not session.is_locked
    with pytest.raises(B.BlindingError):
        session.unblind(B.Role.CUSTODIAN, _commitment(), epoch=1)


def test_refuse_unblind_before_lock_direct():
    session = _session()
    with pytest.raises(B.BlindingError):
        B.refuse_unblind_before_lock(session)


# -- negative: a wrong / tampered commitment reveals nothing ------------

def test_tampered_commitment_is_rejected():
    session = _session()
    session.lock({"samples": [1]}, epoch=1)
    with pytest.raises(B.BlindingError):
        session.unblind(B.Role.CUSTODIAN, _commitment() + "deadbeef", epoch=2)


def test_wrong_commitment_on_raw_unblind_rejected():
    bl = B.blind(("CONDITION_A", "CONDITION_B"), _commitment())
    with pytest.raises(B.BlindingError):
        B.unblind("not-the-sealed-commitment", bl)


def test_empty_commitment_rejected():
    bl = B.blind(("CONDITION_A", "CONDITION_B"), _commitment())
    with pytest.raises(B.BlindingError):
        B.unblind("", bl)


# -- negative: an analyst (or operator/auditor) has no authority --------

@pytest.mark.parametrize("role", [B.Role.ANALYST, B.Role.OPERATOR,
                                  B.Role.AUDITOR])
def test_unauthorized_roles_cannot_unblind(role):
    session = _session()
    session.lock({"samples": [1]}, epoch=1)
    with pytest.raises(B.BlindingError):
        session.unblind(role, _commitment(), epoch=2)


def test_only_custodian_and_unblinder_are_authorized():
    assert B.UNBLIND_AUTHORIZED_ROLES == frozenset(
        {B.Role.CUSTODIAN, B.Role.UNBLINDER})
    B.refuse_unauthorized_unblind(B.Role.CUSTODIAN)  # does not raise
    B.refuse_unauthorized_unblind(B.Role.UNBLINDER)  # does not raise


# -- emergency unblinding is logged and downgrades evidence -------------

def test_emergency_unblind_is_logged_and_downgrades_evidence():
    session = _session()
    before = session.evidence_level_for("RUN_0001")
    assert before is B.BLINDED_EVIDENCE_LEVEL
    record = session.emergency_unblind(
        B.Role.UNBLINDER, _commitment(), reason="safety stop", epoch=5)
    assert record["logged"] is True
    assert record["downgraded"] is True
    assert record["evidence_after"] == B.BROKEN_BLIND_EVIDENCE_LEVEL.name
    # the disclosure is recorded on the session
    assert len(session.disclosures) == 1
    assert session.disclosures[0].kind == "EMERGENCY"
    # and the run's evidence has fallen
    after = session.evidence_level_for("RUN_0001")
    assert after is B.BROKEN_BLIND_EVIDENCE_LEVEL
    assert after.value < before.value


def test_emergency_unblind_needs_authority():
    session = _session()
    with pytest.raises(B.BlindingError):
        session.emergency_unblind(B.Role.OPERATOR, _commitment(),
                                  reason="x", epoch=1)


def test_accidental_disclosure_is_logged_and_downgrades():
    session = _session()
    session.record_accidental_disclosure(
        "RUN_0001", reason="operator glimpsed the label", epoch=3,
        by_role=B.Role.OPERATOR)
    assert session.disclosures[0].kind == "ACCIDENTAL"
    assert session.evidence_level_for("RUN_0001") is \
        B.BROKEN_BLIND_EVIDENCE_LEVEL
    # an untouched run keeps the blinded level
    assert session.evidence_level_for("RUN_0002") is B.BLINDED_EVIDENCE_LEVEL


# -- exploratory runs cannot be relabelled confirmatory -----------------

def test_exploratory_cannot_be_relabelled_confirmatory():
    session = _session(mode=B.StudyMode.EXPLORATORY)
    with pytest.raises(B.BlindingError):
        session.relabel_mode(B.StudyMode.CONFIRMATORY)


def test_confirmatory_can_be_downgraded_to_exploratory():
    session = _session(mode=B.StudyMode.CONFIRMATORY)
    session.relabel_mode(B.StudyMode.EXPLORATORY)
    assert session.mode is B.StudyMode.EXPLORATORY


def test_refuse_relabel_confirmatory_direct():
    with pytest.raises(B.BlindingError):
        B.refuse_relabel_confirmatory(B.StudyMode.EXPLORATORY,
                                      B.StudyMode.CONFIRMATORY)
    # the reverse is allowed
    B.refuse_relabel_confirmatory(B.StudyMode.CONFIRMATORY,
                                  B.StudyMode.EXPLORATORY)


# -- determinism --------------------------------------------------------

def test_codes_are_deterministic():
    a = B.operator_packet(B.example_assignments()[0], _commitment(),
                          B.StudyMode.CONFIRMATORY)
    b = B.operator_packet(B.example_assignments()[0], _commitment(),
                          B.StudyMode.CONFIRMATORY)
    assert a == b
    assert a.all_codes() == b.all_codes()


def test_data_lock_is_deterministic_and_content_bound():
    lock1 = B.lock_data({"x": 1, "y": [2, 3]}, epoch=10)
    lock2 = B.lock_data({"y": [2, 3], "x": 1}, epoch=10)  # key order flipped
    assert lock1.data_hash == lock2.data_hash
    assert lock1.matches({"x": 1, "y": [2, 3]})
    assert not lock1.matches({"x": 1, "y": [2, 4]})


def test_report_is_deterministic_and_claims_nothing():
    r1 = B.blinding_report()
    r2 = B.blinding_report()
    assert r1 == r2
    assert r1["measured_here"] == "nothing"
    assert r1["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r1["claim_class"] == "SOFTWARE_IMPLEMENTED"
    assert r1["verdict"] == "BLIND_OPERATOR_MODE_ENFORCED"
    # the report's own self-checks all hold
    assert r1["operator_packet_hides_assignment"] is True
    assert r1["ui_payload_free_of_assignment"] is True
    assert r1["peek_before_lock_refused"] is True
    assert r1["analyst_unblind_refused"] is True
    assert r1["wrong_commitment_refused"] is True
    assert r1["authorized_unblind_succeeded"] is True
    assert r1["exploratory_to_confirmatory_refused"] is True
    assert r1["emergency_unblind_logged"] is True
    assert r1["emergency_downgrades_evidence"] is True


def test_report_uses_only_r13_and_r15_claims_no_sibling_phases():
    # the sealed commitment is a genuine R13 preregistration seal
    assert B.EXAMPLE_COMMITMENT == _prereg.seal(_prereg.EXAMPLE_PREREG)
