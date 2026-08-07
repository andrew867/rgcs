"""Eye alignment solver.

The coil crossing plane must land on the exact Eye coordinate —
NOT the cone midpoint, crystal midpoint, body midpoint, STL midpoint,
or holder midpoint (unless one happens to equal the Eye).

Crossed-coil model: copper wound clockwise, silver counter-clockwise,
same pitch p. With angular positions

    theta_cu(z) = +2*pi*z/p + phi_cu
    theta_ag(z) = -2*pi*z/p + phi_ag

the paths cross where theta_cu == theta_ag (mod 2*pi), i.e. every
p/2 along z. Phasing the helices shifts the crossing ladder so one
crossing lands exactly on z_eye.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


class EyeAlignmentError(ValueError):
    pass


@dataclass
class EyeAlignmentReport:
    z_eye_mm: float
    z_cross_mm: float
    alignment_error_mm: float
    tolerance_mm: float
    ok: bool

    def to_json(self) -> dict:
        return {"z_eye_mm": self.z_eye_mm,
                "z_cross_mm": self.z_cross_mm,
                "alignment_error_mm": self.alignment_error_mm,
                "tolerance_mm": self.tolerance_mm,
                "pass": self.ok}


def default_eye_tolerance_mm(eye_uncertainty_mm: float) -> float:
    return max(0.25, 2.0 * float(eye_uncertainty_mm))


def compute_eye_alignment(z_eye_mm: float, z_cross_mm: float,
                          tolerance_mm: float) -> EyeAlignmentReport:
    if tolerance_mm <= 0:
        raise EyeAlignmentError("tolerance must be > 0")
    error = abs(float(z_cross_mm) - float(z_eye_mm))
    return EyeAlignmentReport(
        z_eye_mm=float(z_eye_mm), z_cross_mm=float(z_cross_mm),
        alignment_error_mm=error, tolerance_mm=float(tolerance_mm),
        ok=error <= tolerance_mm)


def solve_helix_phase_for_eye(z_eye_mm: float, pitch_mm: float,
                              handedness: str = "clockwise") -> float:
    """Helix phase (radians at z=0) placing a crossing at z_eye.

    For the symmetric crossed pair we phase each helix so both have
    angular position 0 at z = z_eye: phi = -s * 2*pi*z_eye/pitch with
    s = +1 clockwise, -1 counter-clockwise. Then theta_cu(z_eye) =
    theta_ag(z_eye) = 0 — an exact crossing on the Eye plane.
    """
    if pitch_mm <= 0:
        raise EyeAlignmentError("pitch must be > 0")
    if handedness not in ("clockwise", "counter_clockwise"):
        raise EyeAlignmentError(f"unknown handedness {handedness!r}")
    sign = 1.0 if handedness == "clockwise" else -1.0
    phase = -sign * 2.0 * math.pi * float(z_eye_mm) / float(pitch_mm)
    # normalize to [0, 2*pi)
    return phase % (2.0 * math.pi)


def crossing_ladder(z_eye_mm: float, pitch_mm: float, length_mm: float,
                    max_crossings: int = 512) -> list[float]:
    """All crossing planes in [0, length] for the phased crossed pair:
    z_eye + k * pitch/2. One rung is exactly z_eye by construction."""
    if pitch_mm <= 0 or length_mm <= 0:
        raise EyeAlignmentError("pitch and length must be > 0")
    half = pitch_mm / 2.0
    k_min = math.ceil((0.0 - z_eye_mm) / half - 1e-12)
    rungs = []
    k = k_min
    while len(rungs) < max_crossings:
        z = z_eye_mm + k * half
        if z > length_mm + 1e-12:
            break
        if z >= -1e-12:
            rungs.append(round(z, 9))
        k += 1
    return rungs
