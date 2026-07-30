"""R10.31 Agent 05/06 — crystal stack integration and the lunar root.

Two of Agent 05's open questions are pure arithmetic and are answered
here EXACTLY. The rest are hardware questions and are left open.

Q: "Can 4096 Hz and 13.1836 MHz be phase-locked with DDS/NCO hardware?"
A: YES, exactly. Both are integer multiples of 0.25 Hz --
   13183593.75 / 0.25 = 52734375 and 4096 / 0.25 = 16384, both integers.
   So one 0.25 Hz reference (equivalently a 1 Hz reference with a x4
   scaling) drives both with integer dividers. No fractional-N synthesis
   and no frequency error is required.

Q: "Does 13.1836 MHz excite any practical acoustic mode in Scale A?"
A: NO, not by harmonic coincidence. 13183593.75 / 4096 = 3218.6508...,
   not an integer. The nearest Scale A half-wave harmonics are
   3218 x 4096 = 13180928 Hz and 3219 x 4096 = 13185024 Hz; the law
   frequency misses the nearer of them by 1430.25 Hz. At quartz shear
   speed the half-wavelength is 0.144 mm against a 463.87 mm specimen,
   so it is an electronics-scale frequency, not a specimen-scale one.

CONSEQUENCE, stated plainly: on the arithmetic available,
13.18359375 MHz is a CONTROL/IF/LOCK-IN candidate, not a specimen drive
candidate. That is a negative result for the "crystal rings at the law
frequency" reading and it is reported as such.

Agent 06 lunar lane: registered, NOT asserted. No coordinate is sourced
in this run, so none is used.
"""

from __future__ import annotations

import math
from fractions import Fraction

F_OP = Fraction(54_000_000_000, 4096)      # 13183593.75 Hz, exact
SCALE_A_HZ = Fraction(4096)
SCALE_A_LENGTH_MM = 463.8671875
QUARTZ_SHEAR_M_S = 3800.0


def common_reference_hz() -> Fraction:
    """Largest frequency dividing BOTH exactly."""
    num = math.gcd(F_OP.numerator * SCALE_A_HZ.denominator,
                   SCALE_A_HZ.numerator * F_OP.denominator)
    return Fraction(num, F_OP.denominator * SCALE_A_HZ.denominator)


def phase_lock_report() -> dict:
    ref = common_reference_hz()
    a, b = F_OP / ref, SCALE_A_HZ / ref
    return {
        "f_op_hz": float(F_OP), "scale_a_hz": float(SCALE_A_HZ),
        "common_reference_hz": float(ref),
        "f_op_divider": int(a) if a.denominator == 1 else None,
        "scale_a_divider": int(b) if b.denominator == 1 else None,
        "both_integer_multiples": a.denominator == 1 and b.denominator == 1,
        "phase_lockable": a.denominator == 1 and b.denominator == 1,
        "method": "integer division from a single 0.25 Hz reference; no "
                  "fractional-N synthesis and no frequency error needed",
    }


def harmonic_coincidence_report() -> dict:
    n = F_OP / SCALE_A_HZ
    lo, hi = math.floor(n), math.ceil(n)
    f_lo, f_hi = lo * float(SCALE_A_HZ), hi * float(SCALE_A_HZ)
    miss = min(abs(float(F_OP) - f_lo), abs(float(F_OP) - f_hi))
    half_wave_mm = QUARTZ_SHEAR_M_S / (2 * float(F_OP)) * 1000.0
    return {
        "harmonic_index_required": float(n),
        "is_integer_harmonic": n.denominator == 1,
        "nearest_lower_mode_hz": f_lo, "nearest_upper_mode_hz": f_hi,
        "miss_hz": miss,
        "half_wavelength_mm": half_wave_mm,
        "specimen_length_mm": SCALE_A_LENGTH_MM,
        "half_wavelengths_in_specimen":
            SCALE_A_LENGTH_MM / half_wave_mm,
        "excites_scale_a_by_harmonic_coincidence": n.denominator == 1,
        "conclusion": "ELECTRONICS_SCALE_NOT_SPECIMEN_SCALE",
    }


def stack_roles() -> list:
    """Which layer 13.18359375 MHz can and cannot be, on arithmetic."""
    return [
        {"role": "CONTROL_IF_OR_LOCK_IN_REFERENCE", "supported": True,
         "basis": "exact integer relation to a 0.25 Hz reference shared "
                  "with the 4096 Hz mechanical lane",
         "status": "ARITHMETICALLY_CONSISTENT_NOT_MEASURED"},
        {"role": "APERTURE_STEP_CLOCK", "supported": True,
         "basis": "the same reference can clock the 35-position 2,2,2,1 "
                  "stepping; 35 and 7 are integer divisors",
         "status": "ARITHMETICALLY_CONSISTENT_NOT_MEASURED"},
        {"role": "SPECIMEN_ACOUSTIC_DRIVE", "supported": False,
         "basis": "not an integer harmonic of 4096 Hz; misses the nearest "
                  "Scale A mode by 1430.25 Hz; half-wavelength 0.144 mm "
                  "against a 463.87 mm specimen",
         "status": "NEGATIVE_RESULT"},
        {"role": "94_GHZ_CARRIER", "supported": False,
         "basis": "would require a new geometry, a new eigenproblem and "
                  "holdout criteria; never assumed from a frequency "
                  "coincidence (standing R10.15A rule)",
         "status": "REFUSED_WITHOUT_NEW_EIGENPROBLEM"},
    ]


#: Agent 06. REGISTERED, not asserted; no coordinate is sourced here.
LUNAR_ROOT_LANE = [
    {"item": "Apollo 11 LRRR", "role": "lunar local-system root candidate",
     "coordinate_sourced": False,
     "state": "REQUIRES_PRIMARY_SOURCE_NOT_VERIFIED_IN_THIS_RUN"},
    {"item": "Apollo 11/14 corner-cube arrays",
     "role": "fused-silica/quartz retroreflector apparatus",
     "coordinate_sourced": False,
     "state": "REQUIRES_PRIMARY_SOURCE_NOT_VERIFIED_IN_THIS_RUN",
     "note": "material relevance to the quartz lane is a SOURCE CLAIM, "
             "not a demonstrated connection"},
    {"item": "Apollo 15 / Lunokhod reflectors",
     "role": "additional lunar anchor candidates",
     "coordinate_sourced": False,
     "state": "REQUIRES_PRIMARY_SOURCE_NOT_VERIFIED_IN_THIS_RUN"},
    {"item": "retroreflection as phase/range/time/root marker",
     "role": "apparatus framing", "coordinate_sourced": False,
     "state": "REGISTERED_NO_SOURCE_VALIDATION_CLAIMED"},
]

#: 40 GHz attestation. The one thing that would turn the frequency law
#: from arithmetic into evidence.
ATTESTATION_40GHZ = {
    "constant": "F_LO = 40 GHz",
    "role_in_law": "local oscillator in F_op = (94 GHz - F_LO)/4096",
    "attested_in_source_notes": False,
    "attested_in_literature_this_run": False,
    "web_research_authorized": False,
    "status": "UNATTESTED_FITTED_CONSTANT",
    "consequence": "the frequency law remains EXACT ARITHMETIC with one "
                   "free parameter; it is not evidence until 40 GHz is "
                   "independently attested",
    "what_would_settle_it": "a primary source stating a 40 GHz LO (or any "
                            "specific LO) in a 94 GHz metasurface or "
                            "millimetre-wave down-conversion chain",
}


def report() -> dict:
    return {
        "schema": "rgcs.r1031.crystal-stack.v1",
        "phase_lock": phase_lock_report(),
        "harmonic_coincidence": harmonic_coincidence_report(),
        "stack_roles": stack_roles(),
        "lunar_root_lane": LUNAR_ROOT_LANE,
        "attestation_40ghz": ATTESTATION_40GHZ,
        "external_facts_asserted": 0,
        "physical_validation_claimed": False,
        "verdicts": {
            "crystal": "R10_31_CRYSTAL_FREQUENCY_STACK_UPDATED",
            "lunar": "R10_31_LUNAR_ROOT_QUARTZ_RETROREFLECTOR_LANE_READY",
            "attestation": "R10_31_40GHZ_ATTESTATION_ASSESSED",
        },
    }
