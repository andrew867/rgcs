"""R10.12 Phases 25-30 — E3 envelope, Ba-130 authority, shells,
ellipsoid realization, gravity-vertical refusal, body separation."""

from __future__ import annotations

import math

from r1012.evidence import Tier

E3_ENVELOPE = {
    "source_reported": "two bits relate to shell and epoch",
    "arithmetic": "a THREE-bit aligned field is required by the octal "
                  "frame (R10.11D width proof)",
    "internal_subdivision": "UNRESOLVED — E3 is NOT a fully decoded "
                            "epoch field",
    "observed_values": [2, 3, 4, 6],
    "evidence_tier": Tier.CONDITIONAL_CONSENSUS.value,
}

EPOCH_AUTHORITY = {
    "long_origin": "Ba-130 (sole authority for the active solve)",
    "fine_phase": "Cs-133 permitted only for downstream fine phase",
    "evidence_tier": Tier.SOURCE_KNOWN.value,
}


class ShellEpochError(ValueError):
    pass


def shell_report(extracted_shell_context: dict | None = None) -> dict:
    """Phase 27 — shell-relative coordinates via the declared candidate
    profiles; outer-in vs inner-out closure delegated to the existing
    verified machinery. No shell reduces to a trailing decimal digit."""
    from r109.shell_semantics import (candidate_profile_ids,
                                      outer_in_inner_out_agreement)
    checks = {pid: outer_in_inner_out_agreement(pid)["all_close"]
              for pid in candidate_profile_ids()}
    return {"profiles": checks, "all_close": all(checks.values()),
            "firewall": "decimal terminal marker != binary field != "
                        "physical shell semantics (unchanged)",
            "evidence_tier": Tier.CONDITIONAL_COMPLETION.value}


def ellipsoid_realize(lat_deg: float, lon_deg: float,
                      height_m: float = 0.0) -> dict:
    """Phase 28 — exact WGS84 realization (direction -> ellipsoid point
    via the repository geodesy core). SEPARATE from any angular mesh
    compensation."""
    from cwatlas.geodesy import geodetic_to_ecef
    x, y, z = geodetic_to_ecef(lat_deg, lon_deg, height_m)
    return {"lat_deg": lat_deg, "lon_deg": lon_deg, "height_m": height_m,
            "ecef_m": [x, y, z],
            "note": "ellipsoid realization only; no mesh compensation "
                    "is implied", "evidence_tier": Tier.SOURCE_KNOWN.value}


def gravity_vertical(lat_deg: float, lon_deg: float,
                     allow_geocentric_substitute: bool = False) -> dict:
    """Phase 29 — typed interface. Physical field data is absent, so
    this refuses unless the caller EXPLICITLY requests the geocentric
    substitute."""
    if not allow_geocentric_substitute:
        raise ShellEpochError(
            "refused: no physical gravity-field data is loaded; a "
            "geocentric radial substitute exists but must be requested "
            "explicitly (allow_geocentric_substitute=True)")
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return {"direction_unit": [math.cos(la) * math.cos(lo),
                               math.cos(la) * math.sin(lo), math.sin(la)],
            "model_status": "GEOCENTRIC_SUBSTITUTE_EXPLICITLY_REQUESTED",
            "evidence_tier": Tier.CONDITIONAL_COMPLETION.value}


BODY_TERMINAL_SEPARATION = {
    "rule": "Terra/Luna, shell, and terminal semantics are never "
            "inferred from one another",
    "standing_tension": "167-prefix Luna wording vs Earth-labelled Erie "
                        "record 167849523 — UNRESOLVED, preserved",
    "evidence_tier": Tier.UNDERDETERMINED.value,
}
