"""P07 — the executable protocol engine and its runner.

Focused: a frozen protocol compiles and runs deterministically on
synthetic devices. Negative: a post-seal edit is detected, an unauthorized
configuration is refused, an unavailable capability fails before
acquisition, a measurement-class claim cap is refused. Determinism: same
seal + config + seed => byte-identical run.
"""

from __future__ import annotations

import json
import pathlib

import pytest

from r13 import serialize as r13_serialize
from r15 import claims as C
from r15 import protocol_runner as R
from r15 import protocols as P

_SCHEMA_DIR = pathlib.Path(__file__).resolve().parents[2] / "r15" / "schemas"


def _authorized_config(sealed, mode=R.ExecutionMode.SYNTHETIC, seed=20260724,
                       replay_frames=()):
    return R.RunConfig(
        specimen_id="SYN_SPEC", fixture_id="SYN_FIX", calibration_id="SYN_CAL",
        authorized_capabilities=frozenset(
            sealed.protocol.required_capabilities()),
        mode=mode, seed=seed, environment={"T_K": 300.0}, clock={"hz": 1.0},
        replay_frames=replay_frames)


# =======================================================================
# Focused: a frozen protocol compiles and runs on synthetic devices
# =======================================================================

def test_example_protocol_is_wellformed():
    proto = P.EXAMPLE_PROTOCOL
    assert proto.steps[0].kind is P.StepKind.ARM
    assert proto.steps[-1].kind is P.StepKind.RECORD
    assert len(proto.acquisition_steps()) == 2
    # every acquisition carries a maneuver
    assert all(s.maneuver is not None for s in proto.acquisition_steps())
    # claim cap is a software-reachable class, never a measurement class
    assert C.ClaimClass(proto.claim_cap) not in C.MEASUREMENT_CLASSES


def test_freeze_then_compile_and_run_synthetic():
    sealed = P.example_seal()
    assert sealed.verify()
    cfg = _authorized_config(sealed)
    run = R.execute(sealed, cfg, run_id="RUN1", epoch=1000)
    assert run.status == "SYNTHETIC_RUN_COMPLETE"
    assert run.claim_class == C.ClaimClass.SYNTHETIC_OBSERVATION.value
    assert run.protocol_seal == sealed.seal
    assert len(run.raw_artifacts) == 2


def test_dry_run_validates_without_acquiring():
    sealed = P.example_seal()
    cfg = _authorized_config(sealed)
    info = R.dry_run(sealed, cfg)
    assert info["compiles"] is True
    assert info["seal_verified"] is True
    assert info["n_acquisitions"] == 2


def test_compiled_plan_is_ordered():
    sealed = P.example_seal()
    plan = R.compile_plan(sealed, _authorized_config(sealed))
    assert [s.index for s in plan] == list(range(len(plan)))
    assert plan[0].kind == "ARM"


def test_all_maneuvers_are_representable():
    for m in P.Maneuver:
        step = P.ProtocolStep(0, P.StepKind.ACQUIRE, capability="X",
                              maneuver=m)
        assert step.maneuver is m


def test_records_match_their_schemas():
    import jsonschema
    proto_schema = json.loads(
        (_SCHEMA_DIR / "protocol_record.schema.json").read_text())
    run_schema = json.loads(
        (_SCHEMA_DIR / "experiment_run.schema.json").read_text())
    jsonschema.validate(P.EXAMPLE_PROTOCOL.to_record(), proto_schema)
    sealed = P.example_seal()
    run = R.execute(sealed, _authorized_config(sealed), run_id="RS", epoch=1)
    jsonschema.validate(run.to_record(), run_schema)


# =======================================================================
# Modes stay distinct
# =======================================================================

def test_real_mode_is_preregistered_not_run():
    sealed = P.example_seal()
    cfg = _authorized_config(sealed, mode=R.ExecutionMode.REAL)
    run = R.execute(sealed, cfg, run_id="RUNREAL", epoch=1000)
    assert run.status == "PREREGISTERED_NOT_RUN"
    assert run.raw_artifacts == ()
    assert run.steps_executed == 0


def test_fault_injection_stops_on_fault():
    sealed = P.example_seal()
    cfg = _authorized_config(sealed, mode=R.ExecutionMode.FAULT_INJECTION)
    run = R.execute(sealed, cfg, run_id="RUNF", epoch=1000)
    assert run.status == "FAULT_INJECTION_RUN_COMPLETE"
    assert run.stopped_by == "FAULT_DETECTED"
    assert run.raw_artifacts[0]["fault"] is True


def test_replay_mode_reemits_frames():
    sealed = P.example_seal()
    frames = ({"samples": [1.0, 2.0], "note": "frame0"},
              {"samples": [3.0, 4.0], "note": "frame1"})
    cfg = _authorized_config(sealed, mode=R.ExecutionMode.REPLAY,
                             replay_frames=frames)
    run = R.execute(sealed, cfg, run_id="RUNR", epoch=1000)
    assert run.status == "REPLAY_RUN_COMPLETE"
    assert run.raw_artifacts[0]["note"] == "frame0"


def test_replay_without_frames_is_refused():
    sealed = P.example_seal()
    cfg = _authorized_config(sealed, mode=R.ExecutionMode.REPLAY,
                             replay_frames=())
    with pytest.raises(R.RunnerError):
        R.execute(sealed, cfg, run_id="RUNR2", epoch=1000)


# =======================================================================
# Stop conditions terminate correctly
# =======================================================================

def test_max_acquisitions_terminates_run():
    sealed = P.example_seal()
    run = R.execute(sealed, _authorized_config(sealed), run_id="RUNS",
                    epoch=1)
    # the protocol has two acquisitions and a MAX_ACQUISITIONS limit of 2
    assert run.stopped_by == "MAX_ACQUISITIONS"
    assert len(run.raw_artifacts) == 2


def test_max_acquisitions_limit_of_one_stops_early():
    base = P.EXAMPLE_PROTOCOL
    proto = P.Protocol(
        protocol_id=base.protocol_id, version="1.0.1",
        hypotheses=base.hypotheses, controls=base.controls,
        randomization=base.randomization, blinding=base.blinding,
        steps=base.steps,
        stop_conditions=(P.StopCondition("one", P.StopKind.MAX_ACQUISITIONS,
                                         1.0),),
        analysis_plan=base.analysis_plan, claim_cap=base.claim_cap)
    sealed = P.freeze(proto, epoch=1)
    run = R.execute(sealed, _authorized_config(sealed), run_id="RUN1A",
                    epoch=1)
    assert run.stopped_by == "MAX_ACQUISITIONS"
    assert len(run.raw_artifacts) == 1


# =======================================================================
# Determinism
# =======================================================================

def test_same_seed_gives_identical_run():
    sealed = P.example_seal()
    cfg = _authorized_config(sealed, seed=42)
    a = R.execute(sealed, cfg, run_id="D", epoch=1000)
    b = R.execute(sealed, cfg, run_id="D", epoch=1000)
    assert a.run_hash() == b.run_hash()
    assert a.raw_artifacts == b.raw_artifacts


def test_different_seed_changes_readings():
    sealed = P.example_seal()
    a = R.execute(sealed, _authorized_config(sealed, seed=1), run_id="D",
                  epoch=1000)
    b = R.execute(sealed, _authorized_config(sealed, seed=2), run_id="D",
                  epoch=1000)
    assert a.raw_artifacts != b.raw_artifacts


def test_freeze_is_deterministic():
    assert P.compile_hash(P.EXAMPLE_PROTOCOL) == \
        P.compile_hash(P.EXAMPLE_PROTOCOL)
    assert P.example_seal().seal == P.example_seal().seal


# =======================================================================
# Negative: edits, unauthorized configs, unavailable capabilities, caps
# =======================================================================

def test_edit_after_seal_creates_a_new_hash():
    sealed = P.example_seal()
    edited = P.Protocol(
        protocol_id=P.EXAMPLE_PROTOCOL.protocol_id, version="2.0.0",
        hypotheses=P.EXAMPLE_PROTOCOL.hypotheses,
        controls=P.EXAMPLE_PROTOCOL.controls,
        randomization=P.EXAMPLE_PROTOCOL.randomization,
        blinding=P.EXAMPLE_PROTOCOL.blinding, steps=P.EXAMPLE_PROTOCOL.steps,
        stop_conditions=P.EXAMPLE_PROTOCOL.stop_conditions,
        analysis_plan=P.EXAMPLE_PROTOCOL.analysis_plan,
        claim_cap=P.EXAMPLE_PROTOCOL.claim_cap)
    assert P.compile_hash(edited) != sealed.seal
    with pytest.raises(P.ProtocolError):
        P.refuse_edit_after_seal(sealed, edited)


def test_editing_the_carried_protocol_breaks_the_seal():
    # A SealedProtocol whose carried plan does not hash to its seal is
    # detected by verify() and refused at compile time.
    sealed = P.example_seal()
    tampered = P.SealedProtocol(
        protocol=P.Protocol(
            protocol_id="TAMPERED", version="9.9.9",
            hypotheses=("x",), controls=(), randomization={}, blinding={},
            steps=P.EXAMPLE_PROTOCOL.steps,
            stop_conditions=P.EXAMPLE_PROTOCOL.stop_conditions,
            analysis_plan={}, claim_cap=P.EXAMPLE_PROTOCOL.claim_cap),
        seal=sealed.seal, sealed_epoch=1)
    assert tampered.verify() is False
    with pytest.raises(R.RunnerError):
        R.compile_plan(tampered, _authorized_config(sealed))


def test_unauthorized_configuration_is_refused():
    sealed = P.example_seal()
    cfg = R.RunConfig(
        specimen_id="s", fixture_id="f", calibration_id="c",
        authorized_capabilities=frozenset({"SIGNAL_SOURCE"}),  # missing rest
        mode=R.ExecutionMode.SYNTHETIC, seed=1)
    with pytest.raises(R.RunnerError):
        R.compile_plan(sealed, cfg)


def test_unavailable_capability_fails_before_acquisition():
    sealed = P.example_seal()
    cfg = R.RunConfig(
        specimen_id="s", fixture_id="f", calibration_id="c",
        authorized_capabilities=frozenset(),  # nothing authorized
        mode=R.ExecutionMode.SYNTHETIC, seed=1)
    with pytest.raises(R.RunnerError):
        R.execute(sealed, cfg, run_id="U", epoch=1)


def test_missing_calibration_is_refused():
    sealed = P.example_seal()
    cfg = R.RunConfig(
        specimen_id="s", fixture_id="f", calibration_id="   ",
        authorized_capabilities=frozenset(
            sealed.protocol.required_capabilities()),
        mode=R.ExecutionMode.SYNTHETIC, seed=1)
    with pytest.raises(R.RunnerError):
        R.compile_plan(sealed, cfg)


def test_measurement_class_claim_cap_is_refused():
    with pytest.raises(P.ProtocolError):
        P.Protocol(
            protocol_id="BAD", version="1.0.0", hypotheses=("h",),
            controls=(), randomization={}, blinding={},
            steps=(P.ProtocolStep(0, P.StepKind.RECORD, capability="LOG"),),
            stop_conditions=(), analysis_plan={},
            claim_cap=C.ClaimClass.PHYSICAL_MEASUREMENT.value)


def test_acquisition_without_maneuver_is_refused():
    with pytest.raises(P.ProtocolError):
        P.ProtocolStep(0, P.StepKind.ACQUIRE, capability="X")


def test_nonacquisition_with_maneuver_is_refused():
    with pytest.raises(P.ProtocolError):
        P.ProtocolStep(0, P.StepKind.ARM, capability="X",
                       maneuver=P.Maneuver.SWEEP)


def test_empty_protocol_is_refused():
    with pytest.raises(P.ProtocolError):
        P.Protocol(
            protocol_id="E", version="1.0.0", hypotheses=("h",), controls=(),
            randomization={}, blinding={}, steps=(), stop_conditions=(),
            analysis_plan={},
            claim_cap=C.ClaimClass.SYNTHETIC_OBSERVATION.value)


def test_synthetic_run_cannot_be_read_as_measurement():
    sealed = P.example_seal()
    run = R.execute(sealed, _authorized_config(sealed), run_id="M", epoch=1)
    with pytest.raises(C.ClaimError):
        R.refuse_synthetic_as_measurement(run)


def test_prediction_is_not_a_measurement():
    with pytest.raises(P.ProtocolError):
        P.refuse_prediction_as_measurement()


def test_run_unauthorized_refusal_names_the_rule():
    with pytest.raises(R.RunnerError):
        R.refuse_run_unauthorized()


# =======================================================================
# Reports claim nothing physical
# =======================================================================

@pytest.mark.parametrize("report", [
    P.protocols_report, R.protocol_runner_report])
def test_reports_claim_nothing_physical(report):
    r = report()
    assert r["measured_here"] == "nothing"
    assert r["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert "verdict" in r and "claim_class" in r


def test_runner_report_is_deterministic_and_real_is_unrun():
    r = R.protocol_runner_report()
    assert r["determinism_same_seed"] is True
    assert r["real_run_is_not_run"] is True
    assert r["real_run_n_artifacts"] == 0


def test_protocol_bound_to_r13_authorities():
    # the example reuses R13's preregistration seal and experiment registry
    r = P.protocols_report()
    assert r["bound_to_r13_preregistration"] is not None
    assert isinstance(r["bound_to_r13_preregistration"], str)
