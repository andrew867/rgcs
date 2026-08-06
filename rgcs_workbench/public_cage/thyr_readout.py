"""THz Hyper-Raman quartz readout lane (V5).

THYR is a diagnostic readout protocol for phonon/polariton families
that may be weak or invisible in linear IR and Raman measurements:
an intense sub-picosecond THz pulse plus a femtosecond optical pulse
undergo four-wave mixing in alpha-SiO2; sidebands appear around the
optical second harmonic; the time-domain signal Fourier-transforms
into the excitation spectrum (Rubano et al., ledger P026).

THYR is a readout lane. It is not a drive lane and it is not a
claim of RGCS success.
"""

from __future__ import annotations

import json
import pathlib

_HERE = pathlib.Path(__file__).resolve().parent

ROLE = "READOUT_LANE_NOT_DRIVE_VALIDATION"


def sidebands(omega_l: float, omega_t: float) -> dict:
    """First-order sidebands omega_s,a = 2 omega_L -/+ omega_T."""
    if omega_l <= 0 or omega_t <= 0:
        raise ValueError("frequencies must be positive")
    return {"stokes": 2.0 * omega_l - omega_t,
            "anti_stokes": 2.0 * omega_l + omega_t,
            "around": "OPTICAL_SECOND_HARMONIC",
            "role": ROLE,
            "label": "SOURCE_REPORTED_MECHANISM"}


def source_resonances_thz() -> list[float]:
    seed = json.loads((_HERE / "v5_seed_data.json")
                      .read_text(encoding="utf-8"))
    return list(seed["thyr_resonances_thz"])


def unresolved_feature() -> dict:
    """The source's 9 to 10 THz moving polariton-like feature stays
    recorded as unresolved; resolution requires new measurement."""
    seed = json.loads((_HERE / "v5_seed_data.json")
                      .read_text(encoding="utf-8"))
    return {"range_thz": seed["thyr_unresolved_feature_thz"],
            "status": "UNRESOLVED_IN_SOURCE",
            "resolution_requires": "NEW_MEASUREMENT",
            "role": ROLE}


__all__ = ["ROLE", "sidebands", "source_resonances_thz",
           "unresolved_feature"]
