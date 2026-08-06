"""SAW geometry guard from US4023124 (V5).

1974-priority Philips interdigital geometry as a design guard:
half-wavelength overlap spacing, quarter-wavelength electrode width
and gap inside the overlap envelope, eighth-wavelength strips and
gaps outside it at odd multiples of lambda/4, length-weighted
aperture for wavefront correction. Geometry patent, not craft
validation (ledger P022).

Every lambda-derived feature must be tied to a material velocity and
a frequency; a bare wavelength with no material is refused.
Wavefront-correction fields stay separate from active drive fields,
and length-weighted and uniform apertures never mix in one guard.
"""

from __future__ import annotations

APERTURE_MODES = ("uniform", "length_weighted")


def lambda_saw_m(v_saw_m_per_s: float, f_saw_hz: float) -> float:
    """lambda = v / f; both inputs are required and positive."""
    if v_saw_m_per_s <= 0 or f_saw_hz <= 0:
        raise ValueError("lambda-derived features must be tied to a "
                         "material velocity and a frequency")
    return v_saw_m_per_s / f_saw_hz


def quarter_wave_m(v_saw_m_per_s: float, f_saw_hz: float) -> float:
    return lambda_saw_m(v_saw_m_per_s, f_saw_hz) / 4.0


def eighth_wave_m(v_saw_m_per_s: float, f_saw_hz: float) -> float:
    return lambda_saw_m(v_saw_m_per_s, f_saw_hz) / 8.0


def overlap_electrode_geometry(v_saw_m_per_s: float,
                               f_saw_hz: float) -> dict:
    lam = lambda_saw_m(v_saw_m_per_s, f_saw_hz)
    return {"effective_spacing_m": lam / 2.0,
            "electrode_width_m": lam / 4.0,
            "electrode_gap_m": lam / 4.0,
            "region": "OVERLAP_ENVELOPE",
            "role": "ACTIVE_DRIVE",
            "source": "US4023124",
            "label": "SOURCE_REPORTED_GEOMETRY"}


def correction_strip_geometry(v_saw_m_per_s: float, f_saw_hz: float,
                              spacing_multiple: int = 1) -> dict:
    """Strips outside the overlap envelope at an ODD multiple of
    lambda/4; even multiples are refused."""
    if spacing_multiple % 2 != 1:
        raise ValueError("strip spacing must be an odd multiple of "
                         "lambda/4")
    lam = lambda_saw_m(v_saw_m_per_s, f_saw_hz)
    return {"effective_spacing_m": spacing_multiple * lam / 4.0,
            "strip_width_m": lam / 8.0,
            "strip_gap_m": lam / 8.0,
            "region": "OUTSIDE_OVERLAP_ENVELOPE",
            "role": "WAVEFRONT_CORRECTION",
            "source": "US4023124",
            "label": "SOURCE_REPORTED_GEOMETRY"}


def aperture_guard(mode: str) -> dict:
    """One aperture mode per guard; mixing is a design error."""
    if mode not in APERTURE_MODES:
        raise ValueError(f"aperture mode must be one of {APERTURE_MODES}, "
                         f"never a mixture")
    return {"aperture_mode": mode,
            "wavefront_correction_separate_from_drive": True,
            "label": "DESIGN_GUARD"}


__all__ = ["APERTURE_MODES", "lambda_saw_m", "quarter_wave_m",
           "eighth_wave_m", "overlap_electrode_geometry",
           "correction_strip_geometry", "aperture_guard"]
