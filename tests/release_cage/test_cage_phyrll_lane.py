"""MOD-004 Phyrll measurement lane -- the five spec tests."""

from __future__ import annotations

from rgcs_workbench.public_cage import phyrll_lane as PL


def _record(**overrides):
    record = {
        "voltage_v": 3.3,
        "current_a": 0.18,
        "temperature_c": 21.0,
        "magnetometer_response": {"x_ut": 0.1, "y_ut": 0.0, "z_ut": -0.2},
    }
    record.update(overrides)
    return record


def _plan(**overrides):
    plan = {
        "controls": list(PL.REQUIRED_SWEEP_CONTROLS),
        "baseline_recorded": True,
        "frequency_start_hz": 20000.0,
        "frequency_stop_hz": 21000.0,
    }
    plan.update(overrides)
    return plan


def test_1_protocol_refuses_force_output_fields():
    for banned in ("force_N", "thrust_n", "lift", "N_per_W"):
        problems = PL.validate_measurement_record(_record(**{banned: 1.0}))
        assert any("refused output field" in p for p in problems), banned
    assert PL.validate_measurement_record(_record()) == []


def test_2_protocol_records_the_four_required_channels():
    for channel in PL.REQUIRED_MEASUREMENT_FIELDS:
        record = _record()
        del record[channel]
        problems = PL.validate_measurement_record(record)
        assert any(channel in p for p in problems)


def test_3_each_sweep_includes_baseline_and_dummy_controls():
    assert PL.validate_sweep_plan(_plan()) == []
    assert any("baseline" in p for p in
               PL.validate_sweep_plan(_plan(baseline_recorded=False)))
    short = _plan(controls=["dummy crystal"])
    problems = PL.validate_sweep_plan(short)
    assert len(problems) == len(PL.REQUIRED_SWEEP_CONTROLS) - 1


def test_4_tuning_is_per_specimen_and_not_generalizable():
    result = PL.tuning_result("spec-uuid", 20481.5)
    assert result["scope"] == "THIS_SPECIMEN_ONLY"
    assert result["generalizable"] is False
    assert result["generalization_requires"] == "INDEPENDENT_REPLICATION"


def test_5_induced_energy_stays_measurement_derived():
    note = PL.induced_energy_note(0.0031)
    assert note["interpretation"] == "MEASUREMENT_DERIVED"
    assert note["anomalous_output_claimed"] is False


def test_sweep_plans_cannot_smuggle_force_fields():
    problems = PL.validate_sweep_plan(_plan(thrust=0.1))
    assert any("refused output field" in p for p in problems)
