"""Crystal mode and geometry model (Agent A07) + the provenance
records the pack requires (Agent A01 slice).

The purchased specimen exists only as a SELLER LISTING. Its
dimensions are claims, its material is a claim, and the model built
on them is SOURCE_CLAIM_PLUS_ANALYTIC_MODEL. The pre-arrival revision
is immutable; arrival measurements create a NEW revision and never
overwrite this one."""

from __future__ import annotations

import json
from fractions import Fraction

from .relations import hz

# --- the immutable pre-arrival record (from the pack's data file) ------------

PREARRIVAL = {
    "specimen_id": "SP-EBAY-137330949270-PREARRIVAL",
    "revision": 1,
    "status": "PREARRIVAL_UNVERIFIED",
    "listing": {"item_id": "137330949270", "seller": "vkgemsmart"},
    "claimed_geometry": {"length_mm": "77.8", "width_mm": "30.2",
                         "facets": 6, "mass_g": "68.0"},
    "material_claim": "Himalayan quartz",
    "evidence_class": "SOURCE_CLAIM_PLUS_ANALYTIC_MODEL",
    "warning": "Seller dimensions and material claims are not "
               "measurements.",
}

# Longitudinal velocity constant used by the pack's model. Provenance:
# the pack's own prearrival data file; consistent with an isotropic
# quartz longitudinal estimate. It is an ASSUMPTION for a specimen of
# unknown orientation (the elastic response of real quartz is
# orientation-dependent — v4 XRD contract).
V_LONG_M_S = Fraction("6310.812116")


class RevisionError(RuntimeError):
    pass


def prearrival_record() -> dict:
    """A deep copy; the constant is the authority and tests pin its
    immutability."""
    return json.loads(json.dumps(PREARRIVAL))


def screening_modes(length_mm=None, velocity_m_s=None) -> dict:
    """Level-0 1-D rod screening estimates (NOT a FEM solve):

      fixed-free  (quarter-wave): f = v / (4 L)
      free-free   (half-wave):    f = v / (2 L)

    plus crude shear and bending screens. Every number carries its
    model level and assumption list."""
    L = Fraction(str(length_mm)) if length_mm is not None else \
        Fraction(PREARRIVAL["claimed_geometry"]["length_mm"])
    v = Fraction(str(velocity_m_s)) if velocity_m_s is not None else \
        V_LONG_M_S
    L_m = L / 1000
    quarter = v / (4 * L_m)
    half = v / (2 * L_m)
    v_shear = v * Fraction("0.62")        # crude isotropic screen
    return {
        "model_level": "LEVEL0_1D_ROD_SCREENING",
        "assumptions": [
            "1-D rod, uniform cross-section (real: 6-facet tapered)",
            "isotropic longitudinal velocity (real quartz is "
            "anisotropic; orientation unknown, no XRD)",
            "free or fixed ideal ends (real: terminations + support)",
            "geometry is SELLER-PROVIDED, not measured",
        ],
        "longitudinal": {
            "quarter_wave_hz": quarter,
            "half_wave_hz": half,
        },
        "shear_screen": {"quarter_wave_hz": v_shear / (4 * L_m)},
        "bending_screen_note": "bending modes scale as t/L^2 and sit "
                               "far below the longitudinal family "
                               "for this aspect ratio; screened out "
                               "of the target band",
        "length_mm": L, "velocity_m_s": v,
    }


def target_errors() -> dict:
    """Errors of the screening modes against the registered targets —
    and the A01 correction record: the two percentage errors are the
    SAME number because both modes scale as v/L. Counting them twice
    would be double-counting one length/velocity ratio."""
    m = screening_modes()
    q = m["longitudinal"]["quarter_wave_hz"]
    h = m["longitudinal"]["half_wave_hz"]
    t1, t2 = hz("20480"), hz("40960")
    rel1 = (t1 - q) / t1
    rel2 = (t2 - h) / t2
    return {
        "quarter_vs_20480": {"model_hz": q, "target_hz": t1,
                             "abs_hz": t1 - q, "rel": rel1},
        "half_vs_40960": {"model_hz": h, "target_hz": t2,
                          "abs_hz": t2 - h, "rel": rel2},
        "correction_record": {
            "id": "FK-CORR-001",
            "statement": "the quarter-wave and half-wave percentage "
                         "errors are IDENTICAL by construction "
                         "(both modes are proportional to v/L); "
                         "they are one piece of evidence about one "
                         "length ratio, not two agreements",
            "verified_equal": rel1 == rel2,
        },
    }


def candidate_band(length_tol_mm="0.5", velocity_tol_frac="0.02",
                   support_shift_frac="0.005") -> dict:
    """A07 gate: produce a SEARCH BAND, not one magic frequency.
    Worst-case interval propagation of length, velocity, and support
    uncertainty through the quarter-wave estimate."""
    L = Fraction(PREARRIVAL["claimed_geometry"]["length_mm"])
    dL = Fraction(str(length_tol_mm))
    dv = Fraction(str(velocity_tol_frac))
    ds = Fraction(str(support_shift_frac))
    lo = (V_LONG_M_S * (1 - dv) / (4 * (L + dL) / 1000)) * (1 - ds)
    hi = (V_LONG_M_S * (1 + dv) / (4 * (L - dL) / 1000)) * (1 + ds)
    nom = V_LONG_M_S / (4 * L / 1000)
    return {"nominal_hz": nom, "band_lo_hz": lo, "band_hi_hz": hi,
            "band_width_hz": hi - lo,
            "uncertainty_sources": {
                "length_mm": str(dL), "velocity_frac": str(dv),
                "support_frac": str(ds)},
            "sweep_recommendation": "coarse sweep the full band, "
                                    "then fine sweep +/- 3 linewidths "
                                    "around any peak (campaigns 3-4)",
            "rule": "no magic best frequency: the model licenses a "
                    "band, and only a measurement licenses a number"}


def arrival_revision(measured_geometry: dict,
                     measurement_provenance: dict) -> dict:
    """A new revision from real measurements. Refuses without full
    provenance; NEVER mutates the pre-arrival record."""
    need = ("instrument", "operator", "timestamp")
    missing = [k for k in need if k not in measurement_provenance]
    if missing:
        raise RevisionError(f"measurement provenance missing "
                            f"{missing}; seller values cannot be "
                            "silently promoted (A24 attack)")
    rec = prearrival_record()
    return {**rec,
            "revision": rec["revision"] + 1,
            "status": "ARRIVED_MEASURED",
            "measured_geometry": dict(measured_geometry),
            "measurement_provenance": dict(measurement_provenance),
            "supersedes_revision": rec["revision"],
            "note": "the pre-arrival revision remains immutable; "
                    "this record supersedes without overwriting"}
