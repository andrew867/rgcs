"""R15 P02 — measurement provenance: artifacts, lineage, and binding caps.

Focused tests plus the required negatives: one-byte changes alter hashes,
derived data require source artifacts, replay reproduces deterministically,
and a missing clock or calibration caps evidence below a physical
measurement. Nothing here is measured.
"""

from __future__ import annotations

import jsonschema
import pytest

from r15 import artifacts as A
from r15 import claims as C
from r15 import provenance as P


# --- schema fixtures -----------------------------------------------------

import json
from pathlib import Path

_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "r15" / "schemas"


def _schema(name: str) -> dict:
    return json.loads((_SCHEMA_DIR / name).read_text(encoding="utf-8"))


def _artifacts(seed_a: int = 1, seed_b: int = 2):
    a1 = A.synthetic_artifact(
        artifact_id="ART_01", run_id="RUN_T", instrument_id="INSTR_SYNTH",
        calibration_id="CAL_SELFTEST", seed=seed_a, n_bytes=128)
    a2 = A.synthetic_artifact(
        artifact_id="ART_02", run_id="RUN_T", instrument_id="INSTR_SYNTH",
        calibration_id="CAL_SELFTEST", seed=seed_b, n_bytes=128)
    return a1, a2


def _obs(artifacts, **overrides):
    kw = dict(
        observation_id="OBS_T", run_id="RUN_T", quantity="amplitude",
        value=1.25, units="V",
        uncertainty={"type": "standard", "value": 0.01, "units": "V", "k": 1},
        artifacts=artifacts, instrument_id="INSTR_SYNTH",
        calibration_id="CAL_SELFTEST", specimen_id="SPEC_SYNTH",
        fixture_id="FIX_SYNTH", protocol_id="PROTO_SYNTH",
        environment_id="ENV_SYNTH", start_epoch=1000, end_epoch=1001)
    kw.update(overrides)
    return P.build_observation(**kw)


# --- artifacts: immutability and content hashing -------------------------

def test_artifact_manifest_conforms_to_schema():
    a1, _ = _artifacts()
    jsonschema.validate(a1.to_manifest(), _schema("measurement_artifact.schema.json"))


def test_manifest_is_immutable_flag_true():
    a1, _ = _artifacts()
    assert a1.to_manifest()["immutable"] is True


def test_empty_artifact_is_refused():
    with pytest.raises(A.ArtifactError):
        A.MeasurementArtifact(
            artifact_id="X", run_id="R", kind=A.ArtifactKind.RAW_TRACE,
            media_type="application/octet-stream", raw=b"",
            instrument_id="I", calibration_id="C")


def test_missing_binding_on_artifact_is_refused():
    with pytest.raises(A.ArtifactError):
        A.MeasurementArtifact(
            artifact_id="X", run_id="R", kind=A.ArtifactKind.RAW_TRACE,
            media_type="application/octet-stream", raw=b"abc",
            instrument_id="", calibration_id="C")


def test_one_byte_change_alters_artifact_hash():
    a1, _ = _artifacts()
    tampered = A.fault_injected(a1, byte_index=0)
    assert tampered.content_hash != a1.content_hash
    assert tampered.size_bytes == a1.size_bytes  # same length, one byte flipped


def test_identical_bytes_hash_identically():
    a1, _ = _artifacts()
    replay = a1.replay()
    assert replay.content_hash == a1.content_hash


def test_replay_does_not_mutate_original():
    a1, _ = _artifacts()
    original = a1.content_hash
    _ = a1.replay()
    assert a1.verify(original)  # original bytes still intact


def test_synthetic_artifact_is_not_physical():
    a1, _ = _artifacts()
    assert a1.is_physical is False
    assert a1.mode in A.SOFTWARE_MODES


def test_synthetic_acquisition_is_deterministic():
    a, _ = _artifacts()
    b = A.synthetic_artifact(
        artifact_id="ART_01", run_id="RUN_T", instrument_id="INSTR_SYNTH",
        calibration_id="CAL_SELFTEST", seed=1, n_bytes=128)
    assert a.content_hash == b.content_hash


def test_refuse_mutation_raises():
    with pytest.raises(A.ArtifactError):
        A.refuse_mutation()


# --- observation: schema, lineage, and requiring sources -----------------

def test_observation_record_conforms_to_schema():
    a1, a2 = _artifacts()
    rec = _obs((a1, a2))
    jsonschema.validate(rec.to_record(), _schema("observation_record.schema.json"))


def test_derived_data_require_source_artifacts():
    with pytest.raises(P.ProvenanceError):
        _obs(())  # no artifacts


def test_record_carries_every_source_hash():
    a1, a2 = _artifacts()
    rec = _obs((a1, a2))
    assert rec.source_artifact_hashes == (a1.content_hash, a2.content_hash)
    assert rec.to_record()["derivation_graph"][0]["hash"] == a1.content_hash


def test_lineage_verifies_for_untampered_artifacts():
    a1, a2 = _artifacts()
    rec = _obs((a1, a2))
    assert P.verify_lineage(rec, (a1, a2)) is True


def test_tamper_of_any_artifact_breaks_lineage():
    a1, a2 = _artifacts()
    rec = _obs((a1, a2))
    tampered = A.fault_injected(a2, byte_index=3)
    assert P.verify_lineage(rec, (a1, tampered)) is False


def test_tamper_of_first_artifact_breaks_lineage():
    a1, a2 = _artifacts()
    rec = _obs((a1, a2))
    tampered = A.fault_injected(a1, byte_index=0)
    assert P.verify_lineage(rec, (tampered, a2)) is False


# --- binding caps --------------------------------------------------------

def test_fully_bound_synthetic_is_not_physical():
    a1, a2 = _artifacts()
    rec = _obs((a1, a2))
    assert rec.claim_class is C.ClaimClass.SYNTHETIC_OBSERVATION
    assert rec.is_physical is False
    assert rec.evidence.value < C.EvidenceLevel.E4.value


def test_missing_clock_caps_evidence_below_physical():
    a1, a2 = _artifacts()
    rec = _obs((a1, a2), start_epoch=None, end_epoch=None)
    assert "clock" in rec.missing_bindings
    assert rec.evidence.value < C.EvidenceLevel.E4.value
    assert rec.claim_class not in C.MEASUREMENT_CLASSES


def test_missing_calibration_caps_evidence_below_physical():
    a1, a2 = _artifacts()
    rec = _obs((a1, a2), calibration_id=None)
    assert "calibration" in rec.missing_bindings
    assert rec.evidence.value < C.EvidenceLevel.E4.value
    assert rec.claim_class not in C.MEASUREMENT_CLASSES


def test_classify_incomplete_bindings_caps_below_physical():
    partial = C.EvidenceBindings(instrument=True)  # everything else missing
    cls, ev = P.classify_observation(A.AcquisitionMode.SYNTHETIC, partial)
    assert cls not in C.MEASUREMENT_CLASSES
    assert ev.value < C.EvidenceLevel.E4.value


def test_classify_real_complete_would_be_physical_in_principle():
    # The ladder stays honest: a REAL, fully-bound acquisition is the only
    # path to a physical measurement -- and no REAL device exists here.
    full = C.EvidenceBindings(
        instrument=True, calibration=True, specimen=True, fixture=True,
        protocol=True, clock=True, environment=True, raw_artifact=True,
        uncertainty=True)
    cls, ev = P.classify_observation(A.AcquisitionMode.REAL, full)
    assert cls is C.ClaimClass.PHYSICAL_MEASUREMENT
    assert ev is C.EvidenceLevel.E4


def test_no_record_built_here_is_physical():
    a1, a2 = _artifacts()
    rec = _obs((a1, a2))
    with pytest.raises(C.ClaimError):
        P.refuse_synthetic_observation_as_physical(rec)


# --- determinism / replay ------------------------------------------------

def test_replay_reproduces_observation_deterministically():
    a1, a2 = _artifacts()
    rec1 = _obs((a1, a2))
    rec2 = _obs((a1.replay(), a2.replay()))
    assert rec1.lineage_hash == rec2.lineage_hash
    assert rec1.to_record() == rec2.to_record()


def test_lineage_hash_is_stable_across_builds():
    a1, a2 = _artifacts()
    assert _obs((a1, a2)).lineage_hash == _obs((a1, a2)).lineage_hash


def test_wallclock_timestamp_is_refused():
    from r13 import serialize as S
    with pytest.raises(S.SerializeError):
        S.refuse_wallclock_timestamp(reads_clock=True)


# --- reports claim nothing ----------------------------------------------

def test_artifacts_report_claims_nothing():
    r = A.artifacts_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["artifact_is_physical"] is False
    assert r["one_byte_change_alters_hash"] is True
    assert r["replay_reproduces_hash"] is True


def test_provenance_report_claims_nothing():
    r = P.provenance_report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert r["fully_bound_is_physical"] is False
    assert r["fully_bound_claim_class"] == "SYNTHETIC_OBSERVATION"
    assert r["missing_clock_capped_below_physical"] is True
    assert r["lineage_verifies"] is True
    assert "clock" in r["missing_clock_bindings"]
