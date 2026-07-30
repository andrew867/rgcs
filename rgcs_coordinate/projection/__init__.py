"""RCW projection profiles — honest candidate physical projection.

Body profiles are separate from codecs (authority lock). The only
registered profile today is ``earth-r1085a``, an adapter over the
repository's R10.8.5A outer-in gravity-shell projection layer
(``cwatlas.r1085a``). Its standing verdict is YELLOW:

    RGCS_R10_8_5A_YELLOW_PACKET_AUTHORITY_HELD_PROJECTION_UNDERDETERMINED

``project_coordinate`` therefore always reports
``UNDERDETERMINED`` overall, listing every assumption used, and labels
any placement it can compute as a training-calibrated
DERIVED_CANDIDATE — never a validated location. When the scientific
backend (numpy + cwatlas) is not installed, the profile reports
``PROFILE_BACKEND_UNAVAILABLE`` instead of degrading silently.
"""

from __future__ import annotations

from rgcs_coordinate.domain.claims import (
    ACTIVE_LONG_ORIGIN_EPOCH_REFERENCE,
    ClaimClass,
    trace_claims,
)

EARTH_R1085A = "earth-r1085a"

_PROFILES = {
    EARTH_R1085A: {
        "profile_id": EARTH_R1085A,
        "body": "Earth (Terra)",
        "frame": "South-Up, training-equality alignment over the sealed "
                 "R10.8.2 contexts (roll DOF undetermined)",
        "epoch_year": 2025.0,
        "long_origin_epoch_reference": ACTIVE_LONG_ORIGIN_EPOCH_REFERENCE,
        "ground_reference": "TERRA_SURFACE_SYNC_V1",
        "backend": "cwatlas.r1085a (repository scientific stack)",
        "status": "YELLOW_PROJECTION_UNDERDETERMINED",
        "verdict": "RGCS_R10_8_5A_YELLOW_PACKET_AUTHORITY_HELD_"
                   "PROJECTION_UNDERDETERMINED",
        "receipt": "docs/proofs/r1085a-outer-in-gravity-shell-projection/"
                   "TEST_RECEIPT.json",
    },
}


def list_body_profiles() -> list[dict]:
    return [dict(p) for p in _PROFILES.values()]


def _profile(profile_id: str) -> dict:
    if profile_id not in _PROFILES:
        raise KeyError(f"unsupported body profile {profile_id!r}; "
                       f"known: {sorted(_PROFILES)}")
    return dict(_PROFILES[profile_id])


def _assumptions() -> list[str]:
    return [
        "training alignment solved from the Stonehenge training "
        "equality only (2-DOF minimal rotation; roll UNDETERMINED)",
        "shell thicknesses: declared 3-member candidate family, none "
        "corpus-derived",
        "land-zero: average land height family {840 m, 797 m} along "
        "gravity vertical",
        "zeta convention: 2-member family (octree-Z, midband)",
        "magnetic family: declared tilted-dipole scalars; "
        "crust/IGRF members BLOCKED_MISSING_DATA",
        "epoch 2025.0; ground reference TERRA_SURFACE_SYNC_V1; "
        "long-origin epoch reference BA_130",
        "radial lane misfit >= 6.695 km (best declared config) open",
    ]


def project_coordinate(raw: int, profile: str = EARTH_R1085A) -> dict:
    """Candidate physical projection under a named profile.

    Always returns a typed result whose overall status is
    ``UNDERDETERMINED``; a computed placement, when the backend is
    available, is a training-calibrated DERIVED_CANDIDATE with every
    assumption listed.
    """
    meta = _profile(profile)
    base = {
        "raw_decimal": str(raw),
        "profile": meta,
        "assumptions": _assumptions(),
        "status": "UNDERDETERMINED",
        "claim_class": ClaimClass.UNDERDETERMINED.value,
        "claims": trace_claims(),
    }
    try:
        from cwatlas.r1085a import final_projection as fp
        from cwatlas.r1085a import magnetic_shell as ms
        from cwatlas.r1085a import shell_profile as sp
        from cwatlas.r1085a.land_zero import land_zero
    except ImportError as exc:
        base["backend"] = {
            "status": "PROFILE_BACKEND_UNAVAILABLE",
            "detail": f"scientific backend not importable ({exc}); "
                      f"structural decode remains fully available",
        }
        return base
    frame, align = fp.training_alignment(meta["epoch_year"])
    result = fp.forward(
        int(raw), frame, sp.profile("ATMOSPHERIC_LADDER_V1"),
        land_zero(), ms.member("GRAVITY_ONLY"),
        field_line_step_m=5000.0)
    base["backend"] = {"status": "OK", "training_alignment": align}
    base["candidate"] = {
        "claim_class": ClaimClass.DERIVED_CANDIDATE.value,
        "label": "TRAINING_CALIBRATED_CANDIDATE — not a validated "
                 "location; the frame was fitted to the training "
                 "equality",
        "latitude_deg": result.latitude_deg,
        "longitude_deg": result.longitude_deg,
        "height_above_land_zero_km": result.height_above_land_zero_km,
        "shell": result.shell_id,
        "zeta": result.zeta,
        "config": {
            "shell_profile": result.profile_id,
            "land_reference": result.land_reference_id,
            "zeta_convention": result.zeta_convention,
            "magnetic_member": result.magnetic_member_id,
            "radial_mode": result.radial_mode,
        },
        "uncertainty_note": (
            "one config of the declared 48-member sweep; see "
            "SWEEP_ROWS.json in the R10.8.5A receipt for the family "
            "spread"),
    }
    return base


def inverse_project(latitude_deg: float, longitude_deg: float,
                    height_above_land_zero_km: float,
                    profile: str = EARTH_R1085A) -> dict:
    """Candidate inverse encode under a named profile (same honesty)."""
    meta = _profile(profile)
    base = {
        "input": {"latitude_deg": latitude_deg,
                  "longitude_deg": longitude_deg,
                  "height_above_land_zero_km": height_above_land_zero_km},
        "profile": meta,
        "assumptions": _assumptions(),
        "status": "UNDERDETERMINED",
        "claim_class": ClaimClass.UNDERDETERMINED.value,
        "claims": trace_claims(),
    }
    try:
        from cwatlas.r1085a import final_projection as fp
        from cwatlas.r1085a import shell_profile as sp
    except ImportError as exc:
        base["backend"] = {
            "status": "PROFILE_BACKEND_UNAVAILABLE",
            "detail": f"scientific backend not importable ({exc})",
        }
        return base
    frame, _ = fp.training_alignment(meta["epoch_year"])
    inv = fp.inverse(latitude_deg, longitude_deg,
                     height_above_land_zero_km, frame,
                     sp.profile("ATMOSPHERIC_LADDER_V1"))
    base["backend"] = {"status": "OK"}
    base["candidate"] = {
        "claim_class": ClaimClass.DERIVED_CANDIDATE.value,
        "word": inv.word,
        "decimal": inv.decimal,
        "octal": inv.octal,
        "face": inv.face,
        "q22_path": list(inv.path_levels),
        "shell": inv.shell_id,
        "zeta": inv.zeta,
        "aliasing": inv.aliasing_note,
        "uniqueness": "NOT_PROVEN — aliasing is intrinsic to the "
                      "cell/shell quantization",
    }
    return base
