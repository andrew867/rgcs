"""SAW convolver operator from US3833867 (V5).

The 1974 Sperry Rand acoustic-surface-wave convolver as a
source-bound operator: two oppositely propagating SAWs on a
piezoelectric surface, a semiconductor carrier-interaction layer,
interdigital bias and output electrodes, sum-frequency output
omega_3 = omega_1 + omega_2 with k_3 = k_1 - k_2. Signal-processing
patent, not craft validation (ledger P021).

The model refuses net gain as an operating target: bias is an
attenuation-control and carrier-drift field, and the source's
reported 6 dB/cm stays a SOURCE_REPORTED_EXAMPLE.
"""

from __future__ import annotations

import json
import pathlib

_HERE = pathlib.Path(__file__).resolve().parent


class GainTargetRefused(RuntimeError):
    """Raised when a run asks for net gain as its objective."""


def load_source_example() -> dict:
    seed = json.loads((_HERE / "v5_seed_data.json")
                      .read_text(encoding="utf-8"))
    return seed["saw_convolver_example"]


def sum_frequency_hz(f1_hz: float, f2_hz: float) -> float:
    """omega_3 = omega_1 + omega_2."""
    if f1_hz <= 0 or f2_hz <= 0:
        raise ValueError("input frequencies must be positive")
    return f1_hz + f2_hz


def output_wavevector(k1_per_m: float, k2_per_m: float) -> float:
    """k_3 = k_1 - k_2 for counter-propagating inputs."""
    return k1_per_m - k2_per_m


def convolver_operator(*, f1_hz: float, f2_hz: float,
                       launch_left: bool = True, launch_right: bool = True,
                       bias_field_v_per_m: float = 0.0,
                       desired_net_gain_db: float | None = None) -> dict:
    """One convolver configuration receipt.

    Bidirectional operation requires BOTH opposing launchers; the
    bias field is attenuation control, and requesting net gain as
    the objective raises rather than returns.
    """
    if desired_net_gain_db is not None:
        raise GainTargetRefused(
            "net gain is not an operating target; the source example's "
            "6 dB/cm remains SOURCE_REPORTED_EXAMPLE, and bias is "
            "modeled as attenuation control only")
    if not (launch_left and launch_right):
        raise ValueError("the convolver is bidirectional; both opposing "
                         "launchers are required")
    return {
        "output_sum_hz": sum_frequency_hz(f1_hz, f2_hz),
        "launchers": ("left", "right"),
        "bias_field_role": "ATTENUATION_CONTROL_AND_CARRIER_DRIFT",
        "bias_field_v_per_m": bias_field_v_per_m,
        "interaction": "COUNTERPROPAGATING_OVERLAP_REGION",
        "source": "US3833867",
        "label": "SOURCE_BOUND_OPERATOR",
        "claim": "SIGNAL_PROCESSING_OPERATOR_NOT_CRAFT_VALIDATION",
    }


__all__ = ["GainTargetRefused", "load_source_example",
           "sum_frequency_hz", "output_wavevector", "convolver_operator"]
