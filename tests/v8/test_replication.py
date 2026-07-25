"""P24 — independent-replication receipts: the only path from a single-lab
UNEXPLAINED_INSTRUMENT_RESIDUAL up to a REPLICATED_ANOMALY. Focused, negative,
and determinism tests."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

from r13 import serialize
from r15 import claims as C
from r15 import replication as R

_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "r15" / "schemas"
_PROTOCOL = "a" * 64  # a frozen protocol hash the replicas followed


# --- fixtures -------------------------------------------------------------

def _origin():
    return R.LabIdentity(operator_id="op0", apparatus_id="rig0",
                         site_id="site0", specimen_id="spec0")


def _replica(n, *, operator=None, apparatus=None, site=None):
    return R.LabIdentity(
        operator_id=operator or f"op{n}",
        apparatus_id=apparatus or f"rig{n}",
        site_id=site or f"site{n}",
        specimen_id=f"spec{n}")


def _receipt(receipt_id, replica, *, outcome=R.ReplicationOutcome.CONFIRMS,
             residual=5.0, uncertainty=1.0, ran_firewall=True,
             survived=True, protocol=_PROTOCOL, origin=None,
             mode=R.ReplicationMode.SYNTHETIC):
    return R.ReplicationReceipt(
        receipt_id=receipt_id,
        origin=origin or _origin(),
        replica=replica,
        protocol_hash=protocol,
        mode=mode,
        residual_magnitude=residual,
        combined_uncertainty=uncertainty,
        ran_ordinary_explanation_firewall=ran_firewall,
        survived_ordinary_explanations=survived,
        outcome=outcome,
    )


def _bundle():
    return R.ReplicationBundle(
        residual_id="res1", protocol_hash=_PROTOCOL, origin=_origin(),
        epoch=1000, origin_residual_magnitude=5.0,
        origin_combined_uncertainty=1.0)


# --- focused: two independent confirmations reach REPLICATED_ANOMALY ------

def test_two_independent_confirmations_reach_replicated_anomaly():
    b = _bundle()
    b.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    b.add_receipt(_receipt("rcpt-B", _replica(2)), epoch=1002)
    v = b.verdict()
    assert v.claim_class is C.ClaimClass.REPLICATED_ANOMALY
    assert v.promoted is True
    assert v.independent_confirmations == 2
    assert set(v.confirming_receipt_ids) == {"rcpt-A", "rcpt-B"}


def test_replicated_anomaly_is_still_not_new_physics():
    # the promotion is a replicated *unexplained* effect, never phryll
    with pytest.raises(R.ReplicationError):
        R.refuse_residual_as_new_physics()
    with pytest.raises(C.ClaimError):
        R.refuse_phryll_detected()


# --- negative: single lab stays at the ceiling ---------------------------

def test_single_independent_confirmation_stays_unexplained():
    b = _bundle()
    b.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    v = b.verdict()
    assert v.claim_class is C.ClaimClass.UNEXPLAINED_INSTRUMENT_RESIDUAL
    assert v.promoted is False
    assert v.independent_confirmations == 1


def test_empty_bundle_stays_unexplained():
    v = _bundle().verdict()
    assert v.claim_class is R.RESIDUAL_CEILING
    assert v.independent_confirmations == 0


# --- negative: same-lab re-run is not independent ------------------------

def test_same_lab_rerun_does_not_count_as_second_replication():
    b = _bundle()
    # two confirmations that share a site (same lab) -> only one counts
    b.add_receipt(_receipt("rcpt-A", _replica(1, site="shared")), epoch=1001)
    b.add_receipt(_receipt("rcpt-B", _replica(2, site="shared")), epoch=1002)
    v = b.verdict()
    assert v.independent_confirmations == 1
    assert v.claim_class is R.RESIDUAL_CEILING


def test_rerun_of_origin_setup_is_not_independent_of_origin():
    # same operator/apparatus/site as the origin -> RERUN, not independent
    same = R.LabIdentity(operator_id="op0", apparatus_id="rig0",
                         site_id="site0")
    rcpt = _receipt("rcpt-A", same)
    assert rcpt.independence_level() is R.IndependenceLevel.RERUN
    assert rcpt.is_independent_of_origin() is False
    b = _bundle()
    b.add_receipt(rcpt, epoch=1001)
    assert b.verdict().claim_class is R.RESIDUAL_CEILING


def test_independence_levels_are_distinct():
    origin = _origin()
    rerun = R.LabIdentity("op0", "rig0", "site0")
    impl = R.LabIdentity("op0", "rigX", "site0")
    operator = R.LabIdentity("opX", "rigX", "site0")
    lab = R.LabIdentity("opX", "rigX", "siteX")
    assert R.independence_level(origin, rerun) is R.IndependenceLevel.RERUN
    assert R.independence_level(origin, impl) is \
        R.IndependenceLevel.INDEPENDENT_IMPLEMENTATION
    assert R.independence_level(origin, operator) is \
        R.IndependenceLevel.INDEPENDENT_OPERATOR
    assert R.independence_level(origin, lab) is \
        R.IndependenceLevel.INDEPENDENT_LABORATORY


def test_refuse_same_lab_as_independent_raises():
    with pytest.raises(R.ReplicationError):
        R.refuse_same_lab_as_independent(_origin(),
                                         R.LabIdentity("op0", "rig0", "site0"))


# --- negative: skipped-firewall replication rejected (confirmation bias) --

def test_skipped_firewall_confirmation_does_not_count():
    b = _bundle()
    b.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    # a "confirmation" that never ran the firewall
    b.add_receipt(_receipt("rcpt-B", _replica(2), ran_firewall=False),
                  epoch=1002)
    v = b.verdict()
    assert v.independent_confirmations == 1
    assert v.claim_class is R.RESIDUAL_CEILING


def test_firewall_not_survived_does_not_count():
    rcpt = _receipt("rcpt-A", _replica(1), survived=False)
    assert rcpt.passed_firewall() is False
    assert rcpt.is_valid_confirmation() is False


def test_residual_within_budget_is_not_a_confirmation():
    # a "CONFIRMS" whose residual does not exceed its own uncertainty
    rcpt = _receipt("rcpt-A", _replica(1), residual=0.5, uncertainty=1.0)
    assert rcpt.exceeds_uncertainty() is False
    assert rcpt.is_valid_confirmation() is False


def test_refuse_confirmation_bias_raises():
    rcpt = _receipt("rcpt-A", _replica(1), ran_firewall=False)
    with pytest.raises(R.ReplicationError):
        R.refuse_confirmation_bias(rcpt)


# --- negative: reanalysis is not replication -----------------------------

def test_reanalysis_is_not_replication():
    with pytest.raises(R.ReplicationError):
        R.refuse_reanalysis_as_replication()


def test_refuse_promotion_without_replication_raises():
    with pytest.raises(R.ReplicationError):
        R.refuse_promotion_without_replication(1)


# --- negative: mismatched protocol / wrong origin do not count -----------

def test_wrong_protocol_hash_does_not_count():
    b = _bundle()
    b.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    b.add_receipt(_receipt("rcpt-B", _replica(2), protocol="b" * 64),
                  epoch=1002)
    v = b.verdict()
    assert v.independent_confirmations == 1
    assert v.claim_class is R.RESIDUAL_CEILING


# --- synthetic replication differs from physical lab replication ----------

def test_synthetic_replication_is_not_physical():
    synthetic = _receipt("rcpt-A", _replica(1),
                         mode=R.ReplicationMode.SYNTHETIC)
    assert synthetic.is_physical_replication() is False
    assert synthetic.receipt_claim_class() is C.ClaimClass.SYNTHETIC_OBSERVATION
    # a structurally physical attempt would need REAL mode AND a raw artifact
    physical_shaped = R.ReplicationReceipt(
        receipt_id="rcpt-P", origin=_origin(), replica=_replica(1),
        protocol_hash=_PROTOCOL, mode=R.ReplicationMode.REAL,
        residual_magnitude=5.0, combined_uncertainty=1.0,
        ran_ordinary_explanation_firewall=True,
        survived_ordinary_explanations=True,
        outcome=R.ReplicationOutcome.CONFIRMS, has_raw_artifact=True)
    assert physical_shaped.is_physical_replication() is True
    assert synthetic.is_physical_replication() != \
        physical_shaped.is_physical_replication()


def test_all_four_modes_are_distinct_and_only_real_is_physical():
    assert R.ReplicationMode.REAL.is_physical is True
    for m in (R.ReplicationMode.REPLAY, R.ReplicationMode.SYNTHETIC,
              R.ReplicationMode.FAULT_INJECTION):
        assert m.is_physical is False
    assert len({m for m in R.ReplicationMode}) == 4


# --- failed and contradicting replications are preserved -----------------

def test_failed_and_contradicting_replications_are_recorded():
    b = _bundle()
    b.add_receipt(_receipt("rcpt-A", _replica(1),
                           outcome=R.ReplicationOutcome.FAILS_TO_CONFIRM,
                           residual=0.1), epoch=1001)
    b.add_receipt(_receipt("rcpt-B", _replica(2),
                           outcome=R.ReplicationOutcome.CONTRADICTS),
                  epoch=1002)
    v = b.verdict()
    assert v.total_receipts == 2
    assert v.failed_receipts == 1
    assert v.contradicting_receipts == 1
    assert v.independent_confirmations == 0
    assert v.claim_class is R.RESIDUAL_CEILING
    assert len(b) == 2


def test_failed_replication_lowers_status_from_replicated():
    # two confirmations promote; retracting one (leaving a failure) drops back
    b = _bundle()
    b.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    b.add_receipt(_receipt("rcpt-B", _replica(2)), epoch=1002)
    assert b.verdict().claim_class is C.ClaimClass.REPLICATED_ANOMALY
    b2 = _bundle()
    b2.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    b2.add_receipt(_receipt("rcpt-B", _replica(2),
                            outcome=R.ReplicationOutcome.FAILS_TO_CONFIRM,
                            residual=0.1), epoch=1002)
    assert b2.verdict().claim_class is R.RESIDUAL_CEILING


# --- the hash chain preserves the bundle ---------------------------------

def test_bundle_is_hash_chained_and_verifies():
    b = _bundle()
    b.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    b.add_receipt(_receipt("rcpt-B", _replica(2)), epoch=1002)
    assert b.verify() is True
    # genesis + two receipts
    assert len(b.records) == 3


def test_tampering_breaks_chain_verification():
    b = _bundle()
    b.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    b.add_receipt(_receipt("rcpt-B", _replica(2)), epoch=1002)
    records = list(b.records)
    victim = records[1]
    records[1] = serialize.Record(
        payload={"tampered": True}, claim_class=victim.claim_class,
        epoch=victim.epoch, prev_hash=victim.prev_hash,
        record_hash=victim.record_hash)
    assert serialize.verify_chain(tuple(records)) is False


# --- report claims nothing ------------------------------------------------

def test_report_claims_nothing():
    r = R.replication_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["has_phryll_detected_state"] is False
    assert r["residual_ceiling"] == "UNEXPLAINED_INSTRUMENT_RESIDUAL"
    assert r["replicated_class"] == "REPLICATED_ANOMALY"
    assert r["min_independent_replications"] == R.MIN_INDEPENDENT_REPLICATIONS


def test_verdict_is_versioned():
    b = _bundle()
    b.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    v = b.verdict()
    assert v.replication_version == R.REPLICATION_VERSION
    assert v.as_dict()["replication_version"] == R.REPLICATION_VERSION


# --- determinism ----------------------------------------------------------

def _build_bundle():
    b = R.ReplicationBundle(
        residual_id="res1", protocol_hash=_PROTOCOL, origin=_origin(),
        epoch=1000, origin_residual_magnitude=5.0,
        origin_combined_uncertainty=1.0)
    b.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    b.add_receipt(_receipt("rcpt-B", _replica(2)), epoch=1002)
    return b


def test_bundle_is_deterministic():
    a = _build_bundle()
    b = _build_bundle()
    assert a.tip_hash() == b.tip_hash()
    assert a.as_dict() == b.as_dict()
    assert json.dumps(a.verdict().as_dict(), sort_keys=True) == \
        json.dumps(b.verdict().as_dict(), sort_keys=True)


def test_confirmation_count_is_order_independent():
    b1 = _bundle()
    b1.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1001)
    b1.add_receipt(_receipt("rcpt-B", _replica(2)), epoch=1002)
    b2 = _bundle()
    b2.add_receipt(_receipt("rcpt-B", _replica(2)), epoch=1001)
    b2.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=1002)
    assert b1.independent_confirmations() == b2.independent_confirmations()


# --- input validation -----------------------------------------------------

def test_lab_identity_requires_ids():
    with pytest.raises(R.ReplicationError):
        R.LabIdentity(operator_id="", apparatus_id="rig", site_id="site")


def test_receipt_requires_protocol_hash():
    with pytest.raises(R.ReplicationError):
        _receipt("rcpt-A", _replica(1), protocol="")


def test_receipt_rejects_negative_residual():
    with pytest.raises(R.ReplicationError):
        _receipt("rcpt-A", _replica(1), residual=-1.0)


def test_bundle_needs_an_epoch():
    with pytest.raises(R.ReplicationError):
        R.ReplicationBundle(residual_id="res1", protocol_hash=_PROTOCOL,
                            origin=_origin(), epoch=None)


def test_add_receipt_needs_an_epoch():
    b = _bundle()
    with pytest.raises(R.ReplicationError):
        b.add_receipt(_receipt("rcpt-A", _replica(1)), epoch=None)


# --- schema conformance: the terminal receipt ----------------------------

def test_receipt_conforms_to_phase_receipt_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    schema = json.loads((_SCHEMA_DIR / "phase_receipt.schema.json")
                        .read_text(encoding="utf-8"))
    receipt = json.loads(
        (Path(__file__).resolve().parents[2] / "docs" / "v8" / "receipts"
         / "P24.json").read_text(encoding="utf-8"))
    jsonschema.validate(receipt, schema)
    assert receipt["phase_id"] == "P24"
    assert receipt["status"] == "COMPLETE"
