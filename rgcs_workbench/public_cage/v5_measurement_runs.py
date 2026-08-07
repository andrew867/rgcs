"""V5 one-variable-at-a-time measurement runs and the extended
witness layer.

Every run row names its parent, changes exactly one variable, and
uses its parent as the control. The V5 witness-layer extension adds
the ATR, THYR, s-SNOM, PTIR, and FTIR availability flags and the
surface-gap variable on top of the V4B contract; the V4B rule stands
unchanged: a witness is never a validation.
"""

from __future__ import annotations

from rgcs_workbench.public_cage import longitudinal_bridge as LB

RUN_CLAIM_STATUS = "SIMULATION_ESTIMATE"

#: V5 additions on top of the V4B witness-layer contract.
V5_WITNESS_EXTENSION_FIELDS = (
    "layer_type", "thickness_um", "surface_gap_um", "ATR_possible",
    "THYR_possible", "sSNOM_possible", "PTIR_possible",
    "same_field_control",
)


def witness_layer_v5(**overrides) -> dict:
    """A V4B-valid layer plus the V5 extension fields, defaults honest."""
    layer = {
        "layer_id": "DWL_V5_TEMPLATE", "sample_id": "NONE",
        "medium_type": "plant_surface_film",
        "epsilon_d_estimate": 1.0, "loss_tangent_estimate": 0.0,
        "surface_conductivity_estimate": 0.0,
        "water_film_state": "unknown",
        "molecular_fingerprint_status": "unknown",
        "mineral_particle_status": "unknown",
        "Raman_available": False, "SERS_possible": False,
        "FTIR_available": False, "time_since_event_days": "unknown",
        "control_sample_id": "NONE",
        "claim_status": "SIMULATION",
        # V5 extension
        "layer_type": "unknown", "thickness_um": 0.0,
        "surface_gap_um": 0.0, "ATR_possible": False,
        "THYR_possible": False, "sSNOM_possible": False,
        "PTIR_possible": False, "same_field_control": False,
    }
    unknown = set(overrides) - set(layer)
    if unknown:
        raise ValueError(f"unknown witness fields: {sorted(unknown)}")
    layer.update(overrides)
    problems = LB.validate_witness_layer(layer)
    if problems:
        raise ValueError(f"invalid V5 witness layer: {problems}")
    return layer


def run_row(*, run_id: str, parent_run_id: str | None,
            changed_variable: str, value) -> dict:
    """One run: the parent IS the control; the changed variable is
    named; the claim status is fixed."""
    return {"run_id": run_id,
            "parent_run_id": parent_run_id,
            "changed_variable": changed_variable,
            "value": value,
            "control_run": parent_run_id,
            "claim_status": RUN_CLAIM_STATUS}


def v5_run_sequence() -> list[dict]:
    """The V5 chain: baseline, then one variable per step."""
    rows = [run_row(run_id="RUN_V5_0001", parent_run_id=None,
                    changed_variable="baseline", value="no witness layer")]
    steps = (
        ("witness_layer_epsilon", 4.0 / 3.0),
        ("witness_layer_loss_tangent", 0.05),
        ("surface_gap_um", 2.0),
        ("quartz_optic_axis_orientation",
         "optic_axis_perpendicular_to_surface"),
        ("saw_bias_field_v_per_m", 1.0e4),
    )
    for index, (variable, value) in enumerate(steps, start=2):
        parent = rows[-1]["run_id"]
        rows.append(run_row(run_id=f"RUN_V5_{index:04d}",
                            parent_run_id=parent,
                            changed_variable=variable, value=value))
    return rows


def validate_run_sequence(rows) -> list[str]:
    problems: list[str] = []
    for index, row in enumerate(rows):
        if row["control_run"] != row["parent_run_id"]:
            problems.append(f"{row['run_id']} control is not its parent")
        if row["claim_status"] != RUN_CLAIM_STATUS:
            problems.append(f"{row['run_id']} has a non-simulation "
                            f"claim status")
        if index > 0 and row["parent_run_id"] != rows[index - 1]["run_id"]:
            problems.append(f"{row['run_id']} does not chain from the "
                            f"previous run")
    return problems


__all__ = ["RUN_CLAIM_STATUS", "V5_WITNESS_EXTENSION_FIELDS",
           "witness_layer_v5", "run_row", "v5_run_sequence",
           "validate_run_sequence"]
