"""R10.15 — multi-rate architecture (R10.15 physics override).

The device has SEVERAL distinct rates and they must not be conflated:

  f_master  4096 Hz   master phase and switching reference
  f_mod       16 Hz   candidate traveling-pattern modulation
  f_gap       32 Hz   gap passage rate      (2 omitted x 16)
  f_active   528 Hz   active passage rate   (33 active x 16)
  f_passage  560 Hz   total passage rate    (35 cells x 16)
  f_SW       DERIVED  the electromagnetic surface-wave carrier

f_SW IS NOT 4096 Hz. It is not any of the drive rates. It must be
obtained from the unit-cell and annular eigenvalue problems in
``impedance.py`` and ``eigenmodes.py``. Asking this module for f_SW
raises: the value has to be solved for, and 4096 Hz may only be
supplied as one explicitly labelled controlled candidate.

The exact integer relationships below are DERIVED arithmetic on
source-provenance inputs; they carry no physical warrant on their own.
"""

from __future__ import annotations

from fractions import Fraction

from rgcs_surface_wave.evidence import ClaimClass
from rgcs_surface_wave.geometry import C0

F_MASTER_HZ = 4096
F_MOD_HZ = 16
CELLS = 35
ACTIVE = 33
OMITTED = 2
PHASE_STATES = 125


class RateError(ValueError):
    pass


def architecture() -> dict:
    """Exact multi-rate table, regenerated from the definitions."""
    f_passage = CELLS * F_MOD_HZ
    f_active = ACTIVE * F_MOD_HZ
    f_gap = OMITTED * F_MOD_HZ
    if f_passage != f_active + f_gap:
        raise RateError("passage rates do not sum")            # pragma: no cover
    carrier_period = Fraction(1, F_MASTER_HZ)
    step = carrier_period / PHASE_STATES
    return {
        "schema": "rgcs.r1015.rate-architecture.v1",
        "f_master_hz": F_MASTER_HZ,
        "f_master_role": "phase and switching reference ONLY; not the "
                         "electromagnetic carrier",
        "f_mod_hz": F_MOD_HZ,
        "f_passage_total_hz": f_passage,
        "f_passage_active_hz": f_active,
        "f_passage_gap_hz": f_gap,
        "master_per_modulation_cycle": F_MASTER_HZ / F_MOD_HZ,
        "phase_states": PHASE_STATES,
        "phase_step_deg": 360.0 / PHASE_STATES,
        "timing_step_us": float(step * 1_000_000),
        "timing_step_exact_s": [step.numerator, step.denominator],
        "phase_states_tile_one_carrier_period":
            step * PHASE_STATES == carrier_period,
        "f_surface_wave_hz": None,
        "f_surface_wave_status": "DERIVED_REQUIRED",
        "f_surface_wave_note": "solve the unit-cell and annular "
                               "eigenvalue problems; do not assume "
                               "4096 Hz",
        "claim_class": ClaimClass.DERIVED.value,
        "inputs_claim_class": ClaimClass.SOURCE_PROVENANCE.value,
    }


def surface_wave_frequency():
    """f_SW is never available from the rate table."""
    raise RateError(
        "refused: the electromagnetic surface-wave carrier f_SW is not "
        "a drive rate and cannot be read off this table. Solve "
        "eigenmodes.annular_modes() (or impedance.unit_cell_dispersion) "
        "and pass the result explicitly. To test the source-suggested "
        "value, call controlled_candidate(4096.0), which labels it as a "
        "candidate under test rather than a derived carrier.")


def controlled_candidate(f_hz: float, label: str = "source_suggested") -> dict:
    """Register a carrier value as an explicit controlled candidate."""
    if not (f_hz > 0):
        raise RateError("candidate frequency must be positive")
    return {"f_candidate_hz": float(f_hz), "label": label,
            "status": "CONTROLLED_CANDIDATE_UNDER_TEST",
            "claim_class": ClaimClass.HYPOTHESIS.value,
            "free_space_wavelength_m": C0 / f_hz,
            "note": "registered for falsification, not adopted as f_SW"}


def scale_separation(f_sw_hz: float, q_factor: float,
                     f_mod_hz: float = F_MOD_HZ) -> dict:
    """Can the modulation actually resolve sidebands on this mode?

    Space-time modulation produces sidebands at f_SW +- n*f_mod. They
    are spectrally distinct only if the modulation offset exceeds the
    resonance half-linewidth f_SW/(2Q). Otherwise every sideband lies
    inside the same resonance and the system is in the QUASI-STATIC
    regime, where the nonreciprocity mechanism does not engage.
    """
    if f_sw_hz <= 0 or q_factor <= 0:
        raise RateError("f_sw and Q must be positive")
    linewidth = f_sw_hz / q_factor
    half = 0.5 * linewidth
    resolved = f_mod_hz > half
    q_required = f_sw_hz / (2.0 * f_mod_hz)
    return {
        "f_sw_hz": f_sw_hz, "q_factor": q_factor,
        "f_mod_hz": f_mod_hz,
        "ratio_f_sw_over_f_mod": f_sw_hz / f_mod_hz,
        "linewidth_hz": linewidth,
        "half_linewidth_hz": half,
        "sidebands_resolved": bool(resolved),
        "q_required_to_resolve": q_required,
        "regime": ("SIDEBAND_RESOLVED" if resolved
                   else "QUASI_STATIC_UNRESOLVED"),
        "consequence": (
            "sidebands are spectrally distinct; space-time coupling can "
            "be evaluated on separated lines"
            if resolved else
            "all sidebands fall inside one resonance linewidth: the "
            "modulation is adiabatic with respect to the mode, and no "
            "nonreciprocal space-time gap opens. Any force is the "
            "ordinary quasi-static reaction, not a modulation effect"),
        "claim_class": ClaimClass.DERIVED.value,
    }
