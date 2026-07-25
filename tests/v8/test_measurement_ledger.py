"""P10 — immutable, append-only, hash-chained measurement ledger.

Focused: appends verify and the chain holds. Negative: tampering a past
record breaks the chain, a missing-binding observation is capped below E4,
and an external pointer rejects wrong bytes. Determinism: same inputs give
identical hashes and content addresses.
"""

from __future__ import annotations

import numpy as np
import pytest

from r13 import serialize
from r15 import claims
from r15 import measurement_ledger as ML


# --- helpers ------------------------------------------------------------

FULL = claims.EvidenceBindings(
    instrument=True, calibration=True, specimen=True, fixture=True,
    protocol=True, clock=True, environment=True, raw_artifact=True,
    uncertainty=True)


def _built_ledger():
    led = ML.MeasurementLedger()
    led.append_run("run-1", ML.AcquisitionMode.SYNTHETIC, "proto-1", epoch=10)
    raw = ML.Artifact.from_bytes(
        "raw-1", "run-1", ML.ArtifactKind.RAW, "application/octet-stream",
        b"\x01\x02\x03\x04", "instr-1", "cal-1")
    led.append_artifact(raw, epoch=11)
    return led, raw


# --- focused: append + verify_chain holds -------------------------------

def test_appends_grow_the_ledger_and_verify():
    led, _ = _built_ledger()
    assert len(led) == 2
    assert led.verify() is True
    assert led.verify_report()["verified"] is True


def test_empty_ledger_verifies_trivially():
    led = ML.MeasurementLedger()
    assert led.verify() is True
    assert len(led) == 0


def test_tip_hash_advances_and_links():
    led, _ = _built_ledger()
    # the second record's back-link is the first record's hash
    assert led.records[1].prev_hash == led.records[0].record_hash
    assert led.tip_hash() == led.records[-1].record_hash


def test_raw_artifact_is_content_addressed():
    data = b"raw-bytes-payload"
    art = ML.Artifact.from_bytes(
        "a", "r", ML.ArtifactKind.RAW, "application/octet-stream",
        data, "i", "c")
    assert art.content_hash == ML.sha256_hex(data)
    assert art.bytes == len(data)
    assert art.verify(data) is True
    assert art.immutable is True


def test_artifact_manifest_conforms_to_schema_shape():
    _, raw = _built_ledger()
    m = raw.to_manifest()
    for key in ("artifact_id", "run_id", "kind", "media_type", "hash",
                "bytes", "instrument_id", "calibration_id", "immutable"):
        assert key in m
    assert m["immutable"] is True


def test_derivation_links_fit_to_exact_source_and_code():
    deriv = ML.Derivation(
        output_artifact_id="fit-1", input_artifact_ids=("raw-1",),
        software="rgcs.fit", software_version="9.9.9",
        parameters={"model": "lorentzian"})
    m = deriv.to_manifest()
    assert m["input_artifact_ids"] == ["raw-1"]
    assert m["software"] == "rgcs.fit"
    assert m["software_version"] == "9.9.9"


# --- negative: tampering a PAST record breaks the chain -----------------

def test_mutating_a_past_record_breaks_verification_downstream():
    led, _ = _built_ledger()
    led.append_receipt({"status": "COMPLETE"}, epoch=12)
    assert led.verify() is True

    recs = list(led.records)
    victim = recs[0]  # tamper the earliest record's payload
    recs[0] = serialize.Record(
        payload={"entry_kind": "RUN", "body": {"run_id": "EVIL"}},
        claim_class=victim.claim_class, epoch=victim.epoch,
        prev_hash=victim.prev_hash, record_hash=victim.record_hash)
    assert serialize.verify_chain(tuple(recs)) is False
    report = serialize.verify_chain_report(tuple(recs))
    assert report["verified"] is False


def test_raw_artifact_is_immutable_and_rehashes_differently_on_change():
    art = ML.Artifact.from_bytes(
        "a", "r", ML.ArtifactKind.RAW, "application/octet-stream",
        b"original", "i", "c")
    # frozen dataclass: cannot mutate in place
    with pytest.raises(Exception):
        art.content_hash = "0" * 64  # type: ignore[misc]
    # any different content addresses differently
    other = ML.Artifact.from_bytes(
        "a", "r", ML.ArtifactKind.RAW, "application/octet-stream",
        b"original!", "i", "c")
    assert other.content_hash != art.content_hash
    assert art.verify(b"tampered") is False


def test_immutable_false_is_refused():
    with pytest.raises(ML.LedgerError):
        ML.Artifact("a", "r", ML.ArtifactKind.RAW, "m", "h", 1, "i", "c",
                    immutable=False)


# --- negative: missing bindings cap the observation below physical ------

def test_missing_binding_caps_observation_below_physical():
    led = ML.MeasurementLedger()
    partial = claims.EvidenceBindings(instrument=True, calibration=True)
    entry = led.append_observation(
        "obs-1", "run-1", ("raw-1",), "an-1", "freq", 1.0, "Hz",
        {"type": "combined", "value": 0.1},
        partial, claims.ClaimClass.PHYSICAL_MEASUREMENT,
        claims.EvidenceLevel.E4, epoch=20)
    assert entry.granted_class != "PHYSICAL_MEASUREMENT"
    assert entry.granted_class == claims.MAX_SOFTWARE_CLASS.value
    # evidence cannot reach E4 without full bindings
    granted = claims.EvidenceLevel[entry.granted_evidence]
    assert granted.value < claims.EvidenceLevel.E4.value


def test_cap_helper_leaves_full_bindings_untouched():
    assert ML.cap_class_for_bindings(
        claims.ClaimClass.MODEL_PREDICTION, FULL) is \
        claims.ClaimClass.MODEL_PREDICTION
    # missing bindings collapse a measurement class to the software ceiling
    empty = claims.EvidenceBindings()
    assert ML.cap_class_for_bindings(
        claims.ClaimClass.PHYSICAL_MEASUREMENT, empty) is \
        claims.MAX_SOFTWARE_CLASS


def test_ledger_records_only_the_capped_class():
    led = ML.MeasurementLedger()
    partial = claims.EvidenceBindings(instrument=True)
    entry = led.append_observation(
        "obs-2", "run-1", ("raw-1",), "an-1", "freq", 1.0, "Hz",
        {"type": "combined", "value": 0.1},
        partial, claims.ClaimClass.INDEPENDENT_REPLICATION,
        claims.EvidenceLevel.E7, epoch=21)
    body = entry.record.payload["body"]
    assert body["claim_class"] != "INDEPENDENT_REPLICATION"
    assert body["bindings_complete"] is False
    assert "specimen" in body["missing_bindings"]


# --- negative: external pointers are hash-verified ----------------------

def test_external_pointer_verifies_correct_bytes_only():
    data = b"y" * 2048
    ptr = ML.ExternalArtifactPointer(
        "ext-1", "run-1", ML.ArtifactKind.RAW, "application/octet-stream",
        "file:///store/ext-1.bin", ML.sha256_hex(data), len(data), "i", "c")
    assert ptr.verify(data) is True
    assert ptr.verify(data + b"z") is False          # wrong size + hash
    assert ptr.verify(b"y" * 2048 + b"") is True      # identical bytes
    wrong = bytearray(data)
    wrong[0] ^= 0xFF
    assert ptr.verify(bytes(wrong)) is False          # same size, wrong hash


def test_derivation_requires_source_and_software():
    with pytest.raises(ML.LedgerError):
        ML.Derivation("out", (), "sw", "1.0")
    with pytest.raises(ML.LedgerError):
        ML.Derivation("out", ("in",), "", "1.0")


# --- determinism: same inputs => same hashes ----------------------------

def test_same_inputs_give_identical_content_addresses():
    a = np.arange(32, dtype=np.float64).reshape(4, 8)
    b = np.arange(32, dtype=np.float64).reshape(4, 8)
    assert ML.array_bytes(a) == ML.array_bytes(b)
    assert ML.sha256_hex(ML.array_bytes(a)) == ML.sha256_hex(ML.array_bytes(b))


def test_two_ledgers_same_inputs_same_record_hashes():
    def build():
        led = ML.MeasurementLedger()
        led.append_run("run-1", ML.AcquisitionMode.SYNTHETIC, "p", epoch=10)
        art = ML.Artifact.from_bytes(
            "raw-1", "run-1", ML.ArtifactKind.RAW, "application/octet-stream",
            b"deterministic", "i", "c")
        led.append_artifact(art, epoch=11)
        led.append_receipt({"status": "COMPLETE"}, epoch=12)
        return [r.record_hash for r in led.records]

    assert build() == build()


def test_report_measures_nothing_and_detects_tamper():
    r = ML.measurement_ledger_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["chain_verifies"] is True
    assert r["tamper_detected"] is True
    assert r["external_pointer_verifies"] is True
    assert r["external_pointer_rejects_wrong_bytes"] is True
    assert r["observation_capped_below_physical"] is True
    assert r["verdict"] == ML.VERDICT


def test_report_epoch_is_passed_in_never_wallclock():
    r = ML.measurement_ledger_report()
    assert r["epochs_passed_in_never_wallclock"] is True
