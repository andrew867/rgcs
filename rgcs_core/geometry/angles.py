"""Angle-provenance audit arithmetic (RG-16; numerology containment).

Units: degrees. These are Established arithmetic identities auditing
Source claims; no physical inference is made or permitted (RG-16: the
manuscript must not claim golden-ratio equality — the mismatch is
quantified and nonzero).
"""

from __future__ import annotations

import math
from typing import Any

from ..provenance import classified, classification_string

__all__ = ["GOLDEN_RATIO", "angle_audit"]

GOLDEN_RATIO = (1.0 + math.sqrt(5.0)) / 2.0   # 1.618033988749895


@classified("Established", sources=("RG-16",),
            note="arithmetic auditing Source claims; the proposed angle is "
                 "Source claim; no physical inference")
def angle_audit(proposed_angle_deg: float = 51.843) -> dict[str, Any]:
    """Audit the proposed termination angle against candidate identities
    (RG-16). Golden: atan(sqrt(phi)) = 51.8272923730 deg;
    delta vs 51.843 deg = -0.015708 deg (G-11)."""
    if not math.isfinite(proposed_angle_deg):
        raise ValueError("proposed_angle_deg must be finite")
    atan_sqrt_phi = math.degrees(math.atan(math.sqrt(GOLDEN_RATIO)))
    return {
        "proposed_angle_deg": proposed_angle_deg,
        "atan_sqrt_phi_deg": atan_sqrt_phi,
        "delta_atan_sqrt_phi_deg": atan_sqrt_phi - proposed_angle_deg,
        "sexagesimal_51_51_51_deg": 51.0 + 51.0 / 60.0 + 51.0 / 3600.0,
        "atan_4_over_pi_deg": math.degrees(math.atan(4.0 / math.pi)),
        "heptagon_360_over_7_deg": 360.0 / 7.0,
        "classification": classification_string(angle_audit),
    }
