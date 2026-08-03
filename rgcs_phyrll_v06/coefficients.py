"""Exact coefficient spine, v0.6. Everything here is ``Fraction`` exact.

The v0.6 correction note's central instruction: do NOT force every number
into the force law. The supplied coefficients divide into at least three
role families, and each entry below is a typed hypothesis with a claim
tag, never a silently promoted law.

    A. force/coupling      -- 47/63, 27/93 = 9/31, 311
    B. ring/crystal geometry -- 631/732, 57.3 = 573/10
    C. coordinate/geodesic calibration -- 236805/142

29.7, 142/897, 297634, 47 and 23 remain candidate order/scale/diagnostic
values (UNRESOLVED) until a simulation or source clarification assigns
them.
"""

from __future__ import annotations

import math
from fractions import Fraction as F

# ------------------------------------------------------------- family A
#: Operator-reported target efficiency figure. SOURCE_PROVENANCE.
ETA_F_SOURCE = F(673, 10)

#: 27/93 in source spelling; Fraction reduces it. EXACT_ARITHMETIC.
Q_RAW = F(27, 93)
Q = F(9, 31)

SIGMA = F(47, 63)
APERTURE_A = F(311, 1)

#: The v0.5/v0.6 exact derivation: sigma * q * (A - q).
ETA_F_CALC = SIGMA * Q * (APERTURE_A - Q)

# ------------------------------------------------------------- family B
GEOMETRY_CG = F(631, 732)
#: 57.3 as an exact fraction -- the source's degrees-per-radian shorthand.
DEG_PER_RAD_SRC = F(573, 10)

THETA_TILT_CANDIDATE_DEG = GEOMETRY_CG * DEG_PER_RAD_SRC

# ------------------------------------------------------------- family C
SMALL_RATIO = F(142, 897)
STATE47_CANDIDATE = F(297, 1) * SMALL_RATIO
SMALL_ANGLE_CANDIDATE_DEG = SMALL_RATIO * DEG_PER_RAD_SRC
MIAMI_BERMUDA_CANDIDATE_KM = F(236805, 142)


def eta_identity_holds() -> bool:
    """The must-pass identity: sigma*q*(A-q) == 64672/961 == 67.3 (1 dp)."""
    return (Q_RAW == Q and ETA_F_CALC == F(64672, 961)
            and round(float(ETA_F_CALC), 1) == 67.3)


def theta_readings_cg() -> dict:
    """All three declared angle readings of c_g = 631/732.

    They are different numbers, so at most one reading can be the intended
    one; none is selected here.
    """
    cg = float(GEOMETRY_CG)
    return {
        "acos_deg": math.degrees(math.acos(cg)),
        "asin_deg": math.degrees(math.asin(cg)),
        "times_57p3_deg": float(THETA_TILT_CANDIDATE_DEG),
        "readings_are_distinct": True,
        "selected": None,
        "claim": "UNRESOLVED",
    }


def coefficient_table() -> list:
    """Every coefficient, typed and claim-tagged. The deliverable."""
    def row(name, value, role, claim, note=""):
        return {"name": name, "exact": str(value),
                "decimal": float(value), "role": role, "claim": claim,
                "note": note}

    return [
        row("eta_F_source", ETA_F_SOURCE, "A_force_coupling",
            "SOURCE_PROVENANCE", "operator-reported 67.3 target"),
        row("q = 27/93", Q, "A_force_coupling", "EXACT_ARITHMETIC",
            "reduces to 9/31; reduction asserted by test"),
        row("sigma = 47/63", SIGMA, "A_force_coupling", "EXACT_ARITHMETIC"),
        row("A = 311", APERTURE_A, "A_force_coupling", "SOURCE_PROVENANCE"),
        row("eta_F_calc", ETA_F_CALC, "A_force_coupling",
            "EXACT_ARITHMETIC",
            "sigma*q*(A-q) = 64672/961; rounds to 67.3, NOT equal to 673/10"),
        row("c_g = 631/732", GEOMETRY_CG, "B_geometry", "SOURCE_PROVENANCE"),
        row("57.3 = 573/10", DEG_PER_RAD_SRC, "B_geometry",
            "SOURCE_PROVENANCE", "degrees-per-radian shorthand, not 180/pi"),
        row("theta_tilt = c_g*57.3", THETA_TILT_CANDIDATE_DEG, "B_geometry",
            "MODEL_OUTPUT", "one of three inequivalent angle readings"),
        row("142/897", SMALL_RATIO, "C_calibration", "UNRESOLVED"),
        row("state47 = 297*(142/897)", STATE47_CANDIDATE, "C_calibration",
            "UNRESOLVED", "candidate only; 47 is not promoted to a state"),
        row("small_angle = (142/897)*57.3", SMALL_ANGLE_CANDIDATE_DEG,
            "C_calibration", "UNRESOLVED"),
        row("miami_bermuda = 236805/142", MIAMI_BERMUDA_CANDIDATE_KM,
            "C_calibration", "MODEL_OUTPUT",
            "compared against the Bermuda metrics in rgcs_terra_release"),
    ]


def eta_source_vs_calc() -> dict:
    """The source figure and the derivation are NOT the same number.

    673/10 = 67.3 exactly; 64672/961 = 67.2966... They agree only after
    rounding to one decimal place. Recording the exact gap prevents the
    rounded agreement being quietly upgraded to an identity.
    """
    gap = ETA_F_SOURCE - ETA_F_CALC
    return {"eta_source": str(ETA_F_SOURCE), "eta_calc": str(ETA_F_CALC),
            "exact_gap": str(gap), "gap_decimal": float(gap),
            "identical": ETA_F_SOURCE == ETA_F_CALC,
            "agree_at_1dp": round(float(ETA_F_CALC), 1)
            == round(float(ETA_F_SOURCE), 1),
            "claim": "EXACT_ARITHMETIC"}


__all__ = ["ETA_F_SOURCE", "Q_RAW", "Q", "SIGMA", "APERTURE_A",
           "ETA_F_CALC", "GEOMETRY_CG", "DEG_PER_RAD_SRC",
           "THETA_TILT_CANDIDATE_DEG", "SMALL_RATIO", "STATE47_CANDIDATE",
           "SMALL_ANGLE_CANDIDATE_DEG", "MIAMI_BERMUDA_CANDIDATE_KM",
           "eta_identity_holds", "theta_readings_cg", "coefficient_table",
           "eta_source_vs_calc"]
