"""P26 — the ESP32 / embedded experiment runner twin.

Focused tests (the twin executes a recipe deterministically; fail-off
triggers on a lost heartbeat and on over-temp; the hash-chained log
verifies), negative/refusal tests (an out-of-range output is refused; a run
without an arm lease is refused; a twin run is not a hardware run; a real
deployment is BLOCKED_MISSING_INPUT), and determinism and schema-conformance
tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

try:
    import jsonschema
except ImportError:  # pragma: no cover
    jsonschema = None

from r15 import claims as C
from r15 import embedded_runner as E

_SCHEMA_DIR = Path(__file__).resolve().parents[2] / "r15" / "schemas"


# --- FOCUSED: the twin executes a recipe deterministically ----------------

def test_twin_runs_recipe_to_completion():
    recipe = E.example_recipe()
    run = E.run_recipe(recipe, run_id="R", seed=0, epoch=1000)
    assert run.status == "TWIN_RUN_COMPLETE"
    assert run.stopped_by == "RECIPE_COMPLETE"
    assert len(run.raw_artifacts) == len(recipe.segments)
    assert run.claim_class == C.ClaimClass.SYNTHETIC_OBSERVATION.value


def test_twin_run_is_deterministic_same_inputs():
    recipe = E.example_recipe()
    a = E.run_recipe(recipe, run_id="R", seed=7, epoch=1000)
    b = E.run_recipe(recipe, run_id="R", seed=7, epoch=1000)
    assert a.run_hash() == b.run_hash()
    assert a.raw_artifacts == b.raw_artifacts


def test_different_seed_changes_realized_setpoints():
    recipe = E.example_recipe()
    a = E.run_recipe(recipe, run_id="R", seed=1, epoch=1000)
    b = E.run_recipe(recipe, run_id="R", seed=2, epoch=1000)
    assert a.run_hash() != b.run_hash()


def test_recipe_compile_hash_is_stable_and_content_addressed():
    r1 = E.example_recipe()
    r2 = E.example_recipe()
    assert r1.compile_hash() == r2.compile_hash()
    bigger = E.EmbeddedRecipe(
        recipe_id="OTHER", segments=r1.segments, limits=r1.limits)
    assert bigger.compile_hash() != r1.compile_hash()


# --- FOCUSED: fail-off on a lost heartbeat --------------------------------

def test_lost_heartbeat_fails_off():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    lease = ctrl.request_arm(0, ttl_ticks=10)
    ctrl.start(lease["token"], 0)
    assert ctrl.output_on is True
    fired = ctrl.check_watchdog(ctrl.limits.watchdog_timeout_ticks + 1)
    assert fired is True
    assert ctrl.output_on is False
    assert ctrl.state is E.EmbeddedState.FAULT_LATCHED
    assert ctrl.faults[-1]["cause"] == E.FaultCause.HEARTBEAT_LOST.value


def test_heartbeat_within_window_keeps_running():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    lease = ctrl.request_arm(0, ttl_ticks=10)
    ctrl.start(lease["token"], 0)
    ctrl.heartbeat(ctrl.limits.watchdog_timeout_ticks)   # refresh in time
    fired = ctrl.check_watchdog(ctrl.limits.watchdog_timeout_ticks + 1)
    assert fired is False
    assert ctrl.output_on is True
    assert ctrl.state is E.EmbeddedState.RUNNING


# --- FOCUSED: over-temperature interlock ----------------------------------

def test_overtemp_fails_off():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    lease = ctrl.request_arm(0, ttl_ticks=10)
    ctrl.start(lease["token"], 0)
    tripped = ctrl.report_temperature(ctrl.limits.max_temp_c + 1.0, epoch=1)
    assert tripped is True
    assert ctrl.output_on is False
    assert ctrl.state is E.EmbeddedState.FAULT_LATCHED
    assert ctrl.faults[-1]["cause"] == E.FaultCause.OVERTEMP.value


# --- FOCUSED: output off at boot, only RUNNING can be on ------------------

def test_output_off_at_boot():
    ctrl = E.EmbeddedController(boot_epoch=0)
    assert ctrl.output_on is False
    assert ctrl.state is E.EmbeddedState.SAFE_OFF


def test_output_only_on_in_running():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    assert ctrl.output_on is False           # RECIPE_VALID, still off
    lease = ctrl.request_arm(0, ttl_ticks=10)
    assert ctrl.output_on is False           # ARMED, still off
    ctrl.start(lease["token"], 0)
    assert ctrl.output_on is True            # RUNNING, now on
    ctrl.stop(1)
    assert ctrl.output_on is False           # back to SAFE_OFF


# --- FOCUSED: the hash-chained log verifies -------------------------------

def test_hash_chained_log_verifies():
    recipe = E.example_recipe()
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(recipe, 0)
    lease = ctrl.request_arm(0, ttl_ticks=10)
    ctrl.start(lease["token"], 0)
    ctrl.stop(1)
    v = ctrl.verify_log_chain()
    assert v["intact"] is True
    assert v["n"] == len(ctrl.log)


def test_tampered_log_is_detected():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    assert ctrl.verify_log_chain()["intact"] is True
    ctrl.log[2]["payload"] = {"tampered": True}
    v = ctrl.verify_log_chain()
    assert v["intact"] is False
    assert v["broken_at"] == 2


# --- FOCUSED: faults latch until acknowledged while off -------------------

def test_faults_latch_and_clear_only_by_acknowledgement():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    lease = ctrl.request_arm(0, ttl_ticks=10)
    ctrl.start(lease["token"], 0)
    ctrl.emergency_stop(1)
    assert ctrl.state is E.EmbeddedState.FAULT_LATCHED
    assert ctrl.output_on is False
    res = ctrl.acknowledge_faults(2)
    assert res["cleared"] >= 1
    assert ctrl.state is E.EmbeddedState.SAFE_OFF


# --- NEGATIVE: out-of-range output refused --------------------------------

def test_out_of_range_command_refused_and_faults():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    lease = ctrl.request_arm(0, ttl_ticks=10)
    ctrl.start(lease["token"], 0)
    over = E.OutputSetpoint(frequency_hz=1e9, amplitude=0.2, duty=0.25)
    with pytest.raises(E.UnsafeOutputError):
        ctrl.command_output(over, epoch=1)
    assert ctrl.output_on is False
    assert ctrl.state is E.EmbeddedState.FAULT_LATCHED


def test_refuse_unsafe_output_names_the_violations():
    limits = E.SafetyLimits()
    over = E.OutputSetpoint(frequency_hz=1.0, amplitude=99.0, duty=0.9)
    with pytest.raises(E.UnsafeOutputError):
        E.refuse_unsafe_output(over, limits)


def test_in_bounds_output_is_accepted():
    limits = E.SafetyLimits()
    ok = E.OutputSetpoint(frequency_hz=10_000.0, amplitude=0.3, duty=0.3)
    assert limits.violations(ok) == []
    E.refuse_unsafe_output(ok, limits)       # does not raise


def test_out_of_band_recipe_faults_at_load_not_half_loaded():
    bad = E.EmbeddedRecipe(
        recipe_id="BAD",
        segments=(E.RecipeSegment(
            "hot", E.OutputSetpoint(1e9, 5.0, 0.99), 3),),
        limits=E.SafetyLimits())
    assert bad.validate()["valid"] is False
    ctrl = E.EmbeddedController(boot_epoch=0)
    res = ctrl.load_recipe(bad, 0)
    assert res["loaded"] is False
    assert ctrl.state is E.EmbeddedState.FAULT_LATCHED
    assert ctrl.recipe is None


def test_recipe_over_max_continuous_is_invalid():
    long = E.EmbeddedRecipe(
        recipe_id="LONG",
        segments=(E.RecipeSegment(
            "hold", E.OutputSetpoint(1_000.0, 0.2, 0.25), 1000),),
        limits=E.SafetyLimits())
    result = long.validate()
    assert result["valid"] is False
    assert any("continuous" in e for e in result["errors"])


# --- NEGATIVE: run without an arm lease refused ---------------------------

def test_start_without_arm_lease_refused():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    with pytest.raises(E.ArmLeaseError):
        ctrl.start("no-such-token", 0)       # never armed


def test_arm_requested_without_valid_recipe_refused():
    ctrl = E.EmbeddedController(boot_epoch=0)
    with pytest.raises(E.ArmLeaseError):
        ctrl.request_arm(0)                  # in SAFE_OFF, no recipe


def test_expired_lease_refused_and_faults():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    lease = ctrl.request_arm(0, ttl_ticks=2)
    with pytest.raises(E.ArmLeaseError):
        ctrl.start(lease["token"], epoch=10)  # past expiry
    assert ctrl.state is E.EmbeddedState.FAULT_LATCHED


def test_wrong_token_refused_and_faults():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    ctrl.request_arm(0, ttl_ticks=10)
    with pytest.raises(E.ArmLeaseError):
        ctrl.start("wrong-token", 0)
    assert ctrl.state is E.EmbeddedState.FAULT_LATCHED


def test_refuse_run_without_arm_lease_helper():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    with pytest.raises(E.ArmLeaseError):
        E.refuse_run_without_arm_lease(ctrl)  # only RECIPE_VALID, not ARMED
    lease = ctrl.request_arm(0, ttl_ticks=10)
    E.refuse_run_without_arm_lease(ctrl)      # ARMED with a lease: no raise
    assert lease["token"]


def test_arm_lease_is_single_use():
    ctrl = E.EmbeddedController(boot_epoch=0)
    ctrl.load_recipe(E.example_recipe(), 0)
    lease = ctrl.request_arm(0, ttl_ticks=10)
    ctrl.start(lease["token"], 0)
    assert ctrl.arm is None                   # consumed on start


# --- NEGATIVE: a twin run is not a hardware run ---------------------------

def test_twin_run_is_not_a_hardware_run():
    run = E.run_recipe(E.example_recipe(), run_id="R", seed=0, epoch=1000)
    with pytest.raises(E.TwinAsHardwareError):
        E.refuse_twin_as_hardware_run(run)


def test_twin_run_never_carries_a_measurement_class():
    run = E.run_recipe(E.example_recipe(), run_id="R", seed=0, epoch=1000)
    assert run.claim_class not in {c.value for c in C.MEASUREMENT_CLASSES}
    assert run.claim_class == C.ClaimClass.SYNTHETIC_OBSERVATION.value


# --- NEGATIVE: a real deployment is BLOCKED_MISSING_INPUT -----------------

def test_real_mode_run_is_blocked_no_board():
    run = E.run_recipe(E.example_recipe(), run_id="R", seed=0, epoch=1000,
                       mode=E.RunMode.REAL)
    assert run.status == "BLOCKED_MISSING_INPUT"
    assert run.raw_artifacts == ()
    assert run.stopped_by == "NO_BOARD_TO_FLASH"


def test_deploy_to_board_is_blocked():
    res = E.deploy_to_board(E.example_recipe())
    assert res["deployed"] is False
    assert res["status"] == "BLOCKED_MISSING_INPUT"
    assert res["measured_here"] == "nothing"


def test_self_test_reports_no_firmware_no_board():
    st = E.EmbeddedController(boot_epoch=0).self_test()
    assert st["firmware_compiled"] is False
    assert st["board_flashed"] is False


# --- FAULT_INJECTION mode stays distinct ----------------------------------

def test_fault_injection_stops_on_over_range():
    run = E.run_recipe(E.example_recipe(), run_id="F", seed=0, epoch=1000,
                       mode=E.RunMode.FAULT_INJECTION)
    assert run.stopped_by == "FAULT_INJECTED_OVER_RANGE"
    assert run.status == "FAULT_INJECTION_RUN_COMPLETE"
    assert run.claim_class == C.ClaimClass.SYNTHETIC_OBSERVATION.value
    assert run.raw_artifacts[0]["fault"] is True


def test_replay_reproduces_supplied_frames():
    recipe = E.example_recipe()
    frames = tuple({"segment_index": i, "replayed": True}
                   for i in range(len(recipe.segments)))
    run = E.run_recipe(recipe, run_id="RP", seed=0, epoch=1000,
                       mode=E.RunMode.REPLAY, replay_frames=frames)
    assert run.status == "REPLAY_RUN_COMPLETE"
    assert all(a["replayed"] for a in run.raw_artifacts)


# --- the report claims nothing --------------------------------------------

def test_report_claims_nothing_measured():
    rep = E.embedded_runner_report()
    assert rep["measured_here"] == "nothing"
    assert rep["physical_validation"] == "PHYSICAL_VALIDATION_NOT_CLAIMED"
    assert rep["firmware_compiled"] is False
    assert rep["board_flashed"] is False
    assert rep["determinism_same_seed"] is True
    assert rep["watchdog_fires_on_lost_heartbeat"] is True
    assert rep["output_off_after_watchdog"] is True
    assert rep["real_deploy_is_blocked"] is True
    assert rep["claim_class"] == C.ClaimClass.SYNTHETIC_OBSERVATION.value


def test_run_record_conforms_to_experiment_run_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    schema = json.loads((_SCHEMA_DIR / "experiment_run.schema.json")
                        .read_text(encoding="utf-8"))
    run = E.run_recipe(E.example_recipe(), run_id="R", seed=0, epoch=1000)
    jsonschema.validate(run.to_record(), schema)


# --- the terminal receipt conforms to the phase-receipt schema ------------

def test_receipt_conforms_to_phase_receipt_schema():
    if jsonschema is None:  # pragma: no cover
        pytest.skip("jsonschema not installed")
    schema = json.loads((_SCHEMA_DIR / "phase_receipt.schema.json")
                        .read_text(encoding="utf-8"))
    receipt = json.loads(
        (Path(__file__).resolve().parents[2] / "docs" / "v8" / "receipts"
         / "P26.json").read_text(encoding="utf-8"))
    jsonschema.validate(receipt, schema)
    assert receipt["phase_id"] == "P26"
    assert receipt["status"] == "COMPLETE"
    assert receipt["commit"] is None
