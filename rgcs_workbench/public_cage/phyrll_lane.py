"""MOD-004 Phyrll generator measurement lane -- public schema only.

Validates low-power measurement plans and records: what a record must
contain (voltage, current, temperature, magnetometer), what a plan
must contain (baseline and dummy controls for every sweep), and what
the lane refuses outright (any force output field). The research
arithmetic stays in rgcs_phyrll_v06/v07 behind their own firewalls.

This module does measurement-plan validation. It does not claim
force output or anomalous energy. Bench measurement remains pending.
"""

from __future__ import annotations

STATUS = "BENCH_PROTOCOL"

#: Output fields the public lane refuses to carry at all. The refusal
#: list is field names, not physics: the lane has no force column.
REFUSED_OUTPUT_FIELDS = (
    "force_n", "force_newtons", "thrust_n", "thrust", "lift_n", "lift",
    "n_per_w", "newtons_per_watt", "specific_force",
)

#: Every measurement record must log at least these channels.
REQUIRED_MEASUREMENT_FIELDS = (
    "voltage_v", "current_a", "temperature_c", "magnetometer_response",
)

#: Controls a sweep plan must include (spec pack list).
REQUIRED_SWEEP_CONTROLS = (
    "dummy crystal", "empty fixture", "coil-only run",
    "resistive dummy load", "magnetometer background", "thermal blank",
    "mechanical vibration blank", "orientation reversal",
)


def validate_measurement_record(record: dict) -> list[str]:
    problems: list[str] = []
    for key in record:
        if str(key).strip().lower() in REFUSED_OUTPUT_FIELDS:
            problems.append(f"refused output field '{key}': the public "
                            f"lane records no force quantity")
    problems.extend(
        f"measurement record missing required channel '{field}'"
        for field in REQUIRED_MEASUREMENT_FIELDS if field not in record)
    return problems


def validate_sweep_plan(plan: dict) -> list[str]:
    """A sweep without baseline and dummy controls is not a protocol."""
    controls = {str(c).strip().lower() for c in plan.get("controls", ())}
    problems = [f"sweep plan missing control '{control}'"
                for control in REQUIRED_SWEEP_CONTROLS
                if control not in controls]
    if not plan.get("baseline_recorded"):
        problems.append("sweep plan must record a baseline before the "
                        "driven runs")
    for key in plan:
        if str(key).strip().lower() in REFUSED_OUTPUT_FIELDS:
            problems.append(f"refused output field '{key}' in sweep plan")
    return problems


def tuning_result(specimen_id: str, tuned_frequency_hz: float) -> dict:
    """Tuning is per specimen. Generalization needs replication."""
    return {"specimen_id": specimen_id,
            "tuned_frequency_hz": tuned_frequency_hz,
            "scope": "THIS_SPECIMEN_ONLY",
            "generalizable": False,
            "generalization_requires": "INDEPENDENT_REPLICATION"}


def induced_energy_note(joules_measured: float) -> dict:
    """Measured joules stay measurement-derived, never anomalous."""
    return {"joules_measured": joules_measured,
            "interpretation": "MEASUREMENT_DERIVED",
            "anomalous_output_claimed": False}


__all__ = ["STATUS", "REFUSED_OUTPUT_FIELDS",
           "REQUIRED_MEASUREMENT_FIELDS", "REQUIRED_SWEEP_CONTROLS",
           "validate_measurement_record", "validate_sweep_plan",
           "tuning_result", "induced_energy_note"]
