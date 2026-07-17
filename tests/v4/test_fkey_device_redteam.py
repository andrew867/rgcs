"""v4.4 waves 3-4: boards, backends, safety FSM, bridge, and the A24
red-team attacks as executable tests."""

import pathlib
from fractions import Fraction

import pytest

from fkey_instrument import boards, contracts
from fkey_instrument.device import SafetyError, SimDevice
from fkey_instrument.optimizer import Bridge, candidate_families


# --- A14: boards ---------------------------------------------------------

def test_unknown_board_means_output_disabled():
    p = boards.board_profile("UNKNOWN")
    assert p["output_state"] == "OUTPUT_DISABLED"
    pc = boards.pin_conflicts("UNKNOWN", [22])
    assert pc["conflicts"] and not pc["allowed"]


def test_pin_conflict_detection():
    pc = boards.pin_conflicts("ESP32-2432S028R", [22, 27])
    assert pc["allowed"] == [22, 27]
    # display CS pin, boot-strap pin, input-only pin all conflict
    bad = boards.pin_conflicts("ESP32-2432S028R", [15, 0, 35])
    reasons = " ".join(c["reason"] for c in bad["conflicts"])
    assert len(bad["conflicts"]) == 3
    assert "peripheral" in reasons
    assert "boot-strap" in reasons
    assert "input-only" in reasons


def test_candidate_profiles_are_unverified():
    """A14 gate: community pin maps stay candidate until self-test."""
    for name in ("ESP32-2432S028R", "ESP32-2432S024C"):
        assert boards.board_profile(name)["verified"] is False
    assert boards.board_profile("SIMULATOR")["verified"] is True
    with pytest.raises(boards.BoardError):
        boards.board_profile("ESP32-MYSTERY")
    q = boards.questionnaire()
    assert "self-test" in q["rule"]


# --- A16: backends, exact timing ------------------------------------------

def test_ledc_realized_frequency_is_exact_rational():
    r = boards.LedcBackend().realize("4096", res_bits=10)
    assert isinstance(r["calculated_realized_hz"], Fraction)
    assert r["measured_realized_hz"] is None      # never asserted
    err = abs(float(r["quantization_error_hz"]))
    assert err < 0.5                              # sub-Hz at 4 kHz
    r2 = boards.LedcBackend().realize("20480", res_bits=10)
    assert abs(float(r2["quantization_error_hz"])) < 12.0


def test_rmt_and_dds_quantization():
    rmt = boards.RmtBackend().realize("4096")
    # 80 MHz / 4096 = 19531.25 ticks -> rounds; error small
    assert abs(float(rmt["quantization_error_hz"])) < 0.1
    dds = boards.DdsBackend().realize("20480")
    assert abs(float(dds["quantization_error_hz"])) < 0.01
    assert "jitter" in dds["note"]


def test_backend_refusals_not_fudges():
    r = boards.LedcBackend().realize("40000000", res_bits=10)
    assert r.get("refused")
    null = boards.NullBackend().realize("4096")
    assert null["calculated_realized_hz"] is None


def test_timing_report_for_the_two_key_frequencies():
    rep = boards.timing_report_4096_and_20480()
    assert "LEDC@4096Hz" in rep and "I2S_DDS@20480Hz" in rep
    for k, v in rep.items():
        if not v.get("refused"):
            assert "cycle_drift_60s" in v or \
                v["calculated_realized_hz"] is None


# --- A19: safety state machine ---------------------------------------------

def _good_recipe():
    return contracts.example_recipe("SYNTHETIC-SAFE", [
        {"label": "tone", "kind": "sine", "frequency_hz": "20480",
         "duration_s": 2.0, "duty": 0.5, "amplitude_frac": 0.3,
         "backend": "SIMULATOR"}])


def test_boot_lands_in_safe_off_with_output_off():
    d = SimDevice()
    assert d.state == "SAFE_OFF" and not d.output_on


def test_full_arm_start_run_cycle():
    d = SimDevice()
    b = Bridge(d)
    assert b.upload(_good_recipe())["loaded"]
    assert d.state == "RECIPE_VALID"
    out = b.arm_start_run()
    assert out["ok"]
    assert d.state == "SAFE_OFF" and not d.output_on
    logs = b.download_and_verify_logs()
    assert logs["chain"]["intact"] and logs["all_synthetic"]


def test_no_auto_arm_and_no_arm_without_recipe():
    d = SimDevice()
    with pytest.raises(SafetyError):
        d.request_arm()


def test_arm_expiry_faults_and_latches():
    t = [0.0]
    d = SimDevice(clock=lambda: t[0])
    d.load_recipe(_good_recipe(), contracts.validate_recipe)
    lease = d.request_arm(ttl_s=10.0)
    t[0] = 11.0                        # expire the lease
    out = d.start(lease["token"])
    assert not out["started"]
    assert d.state == "FAULT_LATCHED" and not d.output_on
    # latched: cannot load a recipe until acknowledged
    with pytest.raises(SafetyError):
        d.request_arm()
    d.acknowledge_faults()
    assert d.state == "SAFE_OFF"


def test_wrong_token_faults():
    d = SimDevice()
    d.load_recipe(_good_recipe(), contracts.validate_recipe)
    d.request_arm()
    out = d.start("not-the-token")
    assert not out["started"] and d.state == "FAULT_LATCHED"


def test_invalid_recipe_faults_before_output():
    d = SimDevice()
    bad = _good_recipe()
    bad["limits"]["max_continuous_s"] = 999
    r = d.load_recipe(bad, contracts.validate_recipe)
    assert not r["loaded"]
    assert d.state == "FAULT_LATCHED" and not d.output_on


def test_overtemp_and_estop_force_output_off():
    d = SimDevice()
    d.load_recipe(_good_recipe(), contracts.validate_recipe)
    lease = d.request_arm()
    d.start(lease["token"])
    assert d.output_on
    d.fault("OVERTEMP", "65C")
    assert not d.output_on and d.state == "FAULT_LATCHED"
    d.acknowledge_faults()
    d2 = SimDevice()
    d2.emergency_stop()
    assert d2.state == "FAULT_LATCHED" and not d2.output_on


def test_reset_lands_output_off():
    """A15 gate: watchdog/brownout/reset leaves the output off."""
    d = SimDevice()
    d.load_recipe(_good_recipe(), contracts.validate_recipe)
    lease = d.request_arm()
    d.start(lease["token"])
    assert d.output_on
    d.simulate_reset()
    assert d.state == "SAFE_OFF" and not d.output_on
    assert d.recipe is None            # no auto-resume of authority


def test_recipe_timeout_faults_midrun():
    d = SimDevice()
    rec = contracts.example_recipe("SYNTHETIC-LONG", [
        {"label": "a", "kind": "sine", "frequency_hz": "4096",
         "duration_s": 20.0, "amplitude_frac": 0.3,
         "backend": "SIMULATOR"},
        {"label": "b", "kind": "sine", "frequency_hz": "4096",
         "duration_s": 15.0, "amplitude_frac": 0.3,
         "backend": "SIMULATOR"}])
    rec["limits"]["max_continuous_s"] = 30
    # schema passes (30 <= 60, each segment fine) but the device
    # enforces the running total against the limit
    r = contracts.validate_recipe(rec)
    assert not r["valid"]              # 35 > 30 caught at validation
    # tighten to pass validation, then device-level timeout on a
    # sabotaged copy
    rec["segments"][1]["duration_s"] = 5.0
    d.load_recipe(rec, contracts.validate_recipe)
    d.recipe["segments"][1]["duration_s"] = 25.0     # sabotage
    lease = d.request_arm()
    d.start(lease["token"])
    out = d.run_segments()
    assert not out["completed"]
    assert d.state == "FAULT_LATCHED" and not d.output_on


def test_pin_conflict_faults_on_load():
    d = SimDevice(profile="ESP32-2432S028R")
    rec = _good_recipe()
    rec["device_requirements"]["output_pins"] = [15]   # display CS
    r = d.load_recipe(rec, contracts.validate_recipe)
    assert not r["loaded"] and d.state == "FAULT_LATCHED"


# --- A24 red-team attacks ---------------------------------------------------

def test_attack_arithmetic_confused_with_generation():
    """The optimizer must give zero expected amplitude to arithmetic
    coincidences and to sine 'harmonics' — tested in the wave-1 file;
    here we verify the RELATION language cannot upgrade either."""
    from fkey_instrument.relations import classify_scale, hz
    r = classify_scale(hz("8"), 2560, hz("20480"))
    assert r.primary_class == "PHASE_CLOSURE_ONLY"
    assert "not a spectral generation mechanism" in r.note


def test_attack_seller_dimension_cannot_become_measured():
    from fkey_instrument.crystal_mode import (RevisionError,
                                              arrival_revision)
    with pytest.raises(RevisionError):
        arrival_revision({"length_mm": "77.8"}, {})


def test_attack_ui_cannot_arm_without_authority():
    d = SimDevice()
    d.load_recipe(_good_recipe(), contracts.validate_recipe)
    # start without arm
    with pytest.raises(SafetyError):
        d.start("anything")
    # arm token single-use
    lease = d.request_arm()
    d.start(lease["token"])
    d.stop()
    with pytest.raises(SafetyError):
        d.start(lease["token"])        # replay refused (state)


def test_attack_network_loss_cannot_leave_output_on():
    """Wi-Fi loss is a fault path in firmware; in the twin, any
    fault during RUNNING kills the output."""
    d = SimDevice()
    d.load_recipe(_good_recipe(), contracts.validate_recipe)
    lease = d.request_arm()
    d.start(lease["token"])
    d.fault("WATCHDOG", "network task starved")
    assert not d.output_on


def test_attack_alias_cannot_fake_a_20k_peak():
    from fkey_instrument.spectrum import nyquist_check
    a = nyquist_check(40960.0, 48000.0)
    assert a["aliased"] and "artifact" in a["note"]


def test_attack_synthetic_label_leakage():
    """Every device log event, sweep, campaign and recipe id carries
    SYNTHETIC; stripping it from a recipe id is visible."""
    d = SimDevice()
    b = Bridge(d)
    fam = candidate_families()[0]
    rec = b.compile_recipe(fam)
    assert rec["recipe_id"].startswith("SYNTHETIC")
    assert rec["evidence_class"] == "SYNTHETIC_INSTRUMENT_RUN"
    b.upload(rec)
    assert all(e["synthetic"] for e in d.log)
    assert "SYNTHETIC" in d.status()["banner"]


def test_attack_double_counted_octave_errors():
    from fkey_instrument.crystal_mode import target_errors
    e = target_errors()
    assert e["correction_record"]["verified_equal"]
    assert "not two agreements" in \
        e["correction_record"]["statement"]


def test_attack_timing_overflow_rejected():
    r = contracts.validate_recipe(contracts.example_recipe(
        "SYNTHETIC-NAN", [
            {"label": "t", "kind": "sine",
             "frequency_hz": "4096",
             "duration_s": float("inf")}]))
    assert not r["valid"]


def test_attack_free_form_frequency_cannot_bypass_limits():
    """A18 gate: everything reaches the device as a validated recipe;
    there is no other input path on the SimDevice API."""
    d = SimDevice()
    api = [m for m in dir(d) if not m.startswith("_")]
    assert "load_recipe" in api
    assert not any("set_frequency" in m or "direct" in m
                   for m in api)


def test_attack_missing_amplitude_is_refused_not_defaulted():
    """A segment without amplitude_frac must be rejected — a default
    amplitude on an actuation instrument is the wrong answer by
    construction."""
    rec = contracts.example_recipe("SYNTHETIC-NOAMP", [
        {"label": "t", "kind": "sine", "frequency_hz": "4096",
         "duration_s": 1.0}])
    out = contracts.validate_recipe(rec)
    assert not out["valid"]
    assert any("amplitude_frac" in e for e in out["errors"])


def test_fk_coverage_bidirectional():
    """A02: forward (requirement -> artifact) and reverse (module ->
    requirement) orphan checks, release-blocking."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "cov", pathlib.Path(__file__).resolve().parents[2]
        / "tools/v44_coverage.py")
    cov = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cov)
    rep = cov.evaluate()
    assert rep["all_passed"], rep["failures"]
    assert rep["total_requirements"] >= 35
