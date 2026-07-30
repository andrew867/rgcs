"""Program locks — WS04 memory spec and WS08 prediction registry."""

import pytest

from rgcs_lab.authority import memory_spec as ms
from rgcs_lab.authority.prediction_registry import (
    FrozenPrediction,
    MeasurementRecord,
    PredictionRegistry,
    SchemaError,
)


# --- WS04 --------------------------------------------------------------

def test_summary_without_provenance_refused():
    with pytest.raises(ms.SchemaError, match="without provenance"):
        ms.MemoryNode("s1", ms.NodeKind.SUMMARY,
                      ms.MemoryAuthority.PUBLIC, "summary text")
    node = ms.MemoryNode("s1", ms.NodeKind.SUMMARY,
                         ms.MemoryAuthority.PUBLIC, "summary",
                         children=("r1", "r2"), resolution_level=1)
    assert node.children == ("r1", "r2")


def _arm(budget=1000):
    return {"recall_at_10": 0.5, "mrr": 0.4,
            "provenance_depth_hit": 0.9, "latency_ms": 12.0,
            "budget_tokens": budget}


def _report(**over):
    rep = {"arms": {a: _arm() for a in ms.BENCHMARK_ARMS},
           "ablations": {a: {"run": True} for a in ms.MANDATORY_ABLATIONS},
           "corpus_authority": "PUBLIC"}
    rep.update(over)
    return rep


def test_benchmark_report_gates():
    ok = ms.validate_benchmark_report(_report())
    assert ok["valid"] and "not consciousness" in ok["non_claim"]
    bad = _report()
    del bad["arms"]["hybrid"]
    with pytest.raises(ms.SchemaError, match="missing arms"):
        ms.validate_benchmark_report(bad)
    bad = _report()
    bad["arms"]["vector"] = _arm(budget=99999)
    with pytest.raises(ms.SchemaError, match="unequal or undeclared"):
        ms.validate_benchmark_report(bad)
    with pytest.raises(ms.SchemaError, match="PUBLIC"):
        ms.validate_benchmark_report(
            _report(corpus_authority="PRIVATE_OPERATOR"))
    bad = _report()
    del bad["ablations"]["no_symbolic_reranker"]
    with pytest.raises(ms.SchemaError, match="mandatory ablations"):
        ms.validate_benchmark_report(bad)


# --- WS08 --------------------------------------------------------------

def _prediction(pid="P1"):
    return FrozenPrediction(
        prediction_id=pid,
        hypothesis="lattice mode splitting under schedule S",
        observable="beat frequency",
        predicted_value="12.5 Hz",
        uncertainty="+/- 0.3 Hz",
        apparatus="bench rig A, rev 3",
        analysis_plan="notebook nb-7, frozen",
        controls=("sham", "detuned"),
        freeze_commit="abc1234",
        blind_label="BLIND-01")


def test_freeze_digest_and_tamper_evidence():
    reg = PredictionRegistry()
    p = _prediction()
    digest = reg.freeze(p)
    assert p.verify() and digest == p.digest
    st = reg.status("P1")
    assert st["outcome"] == "PENDING"
    assert st["claim_class"] == "PROSPECTIVE_PREDICTION"
    assert "not evidence before measurement" in st["non_claims"][0]


def test_controls_must_freeze_with_prediction():
    with pytest.raises(SchemaError, match="required control"):
        FrozenPrediction(
            prediction_id="P2", hypothesis="h", observable="o",
            predicted_value="1 Hz", uncertainty="0.1 Hz",
            apparatus="a", analysis_plan="n", controls=("sham",),
            freeze_commit="abc", blind_label="B")


def test_measurement_binds_to_digest_and_never_edits_freeze():
    reg = PredictionRegistry()
    p = _prediction()
    reg.freeze(p)
    with pytest.raises(SchemaError, match="different prediction digest"):
        reg.attach_measurement("P1", MeasurementRecord(
            prediction_digest="0" * 64, measured_value="12.4 Hz",
            measurement_uncertainty="0.2 Hz",
            instrument_calibration_ref="cal-9",
            analysis_notebook_sha256="f" * 64, outcome="HIT"))
    reg.attach_measurement("P1", MeasurementRecord(
        prediction_digest=p.digest, measured_value="12.4 Hz",
        measurement_uncertainty="0.2 Hz",
        instrument_calibration_ref="cal-9",
        analysis_notebook_sha256="f" * 64, outcome="HIT"))
    st = reg.status("P1")
    assert st["outcome"] == "HIT"
    assert st["claim_class"] == "MEASUREMENT"
    assert "does not establish the proposed mechanism" in \
        st["non_claims"][1]
    with pytest.raises(SchemaError, match="append-only"):
        reg.attach_measurement("P1", MeasurementRecord(
            prediction_digest=p.digest, measured_value="12.6 Hz",
            measurement_uncertainty="0.2 Hz",
            instrument_calibration_ref="cal-9",
            analysis_notebook_sha256="f" * 64, outcome="MISS"))


def test_classified_outcome_requires_calibration_and_notebook_hash():
    with pytest.raises(SchemaError, match="calibration"):
        MeasurementRecord(prediction_digest="d", measured_value="1",
                          measurement_uncertainty="0.1",
                          instrument_calibration_ref="",
                          analysis_notebook_sha256="", outcome="HIT")
