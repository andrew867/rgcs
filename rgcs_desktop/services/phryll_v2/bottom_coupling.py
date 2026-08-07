"""Crystal-bottom coupling model (PHRYLL_V2_COUPLING_UPDATE).

Coupling chain:

    crystal bottom
    -> open or lightly coupled gap
    -> flat pickup surface
    -> annular pickup ring

Rules: the crystal bottom is never overconstrained with solid plastic
(the cone stays open below the base aperture); O-rings are allowed as
compliant mounts — contact stabilizes the crystal without hard damping
of internal oscillation, the bottom coupling path stays exposed, and
O-ring material/diameter/compression/contact height are recorded.
"""
from __future__ import annotations

COUPLING_MODES = ("open", "lightly_coupled", "o_ring_mounted")

#: compression guidance for compliant (not hard-damping) mounting
O_RING_COMPRESSION_SOFT_MAX_PCT = 30.0
O_RING_COMPRESSION_MIN_PCT = 5.0


class CouplingError(ValueError):
    """A refused bottom-coupling configuration (with the reason)."""


def design_bottom_coupling(profile, settings: dict | None = None) -> dict:
    """Bottom-coupling record for a crystal profile.

    ``settings``: coupling_mode (default "open"), gap_mm (default 2.0),
    pickup_ring {od_mm, id_mm, thickness_mm} (derived from the base
    diameter when absent), o_ring {material, cord_diameter_mm, id_mm,
    compression_pct, contact_height_mm} when o_ring_mounted.
    """
    settings = dict(settings or {})
    mode = settings.get("coupling_mode", "open")
    if mode not in COUPLING_MODES:
        raise CouplingError(
            f"unknown coupling mode {mode!r} (supported: "
            f"{', '.join(COUPLING_MODES)}); a solid plastic bottom is "
            f"deliberately not a mode — the crystal bottom is never "
            f"overconstrained")
    gap = float(settings.get("gap_mm", 2.0))
    if gap < 0:
        raise CouplingError("gap must be >= 0")
    if mode == "open" and gap < 0.5:
        raise CouplingError(
            f"open coupling needs a real gap (>= 0.5 mm), got {gap} mm")

    base_d = max(profile.base_diameter_mm, profile.max_body_width_mm)
    ring = settings.get("pickup_ring") or {}
    ring_od = float(ring.get("od_mm", base_d + 6.0))
    ring_id = float(ring.get("id_mm", max(base_d - 8.0, base_d * 0.6)))
    ring_t = float(ring.get("thickness_mm", 2.0))
    if ring_id >= ring_od:
        raise CouplingError(f"pickup ring ID {ring_id} mm must be "
                            f"smaller than OD {ring_od} mm")

    out = {
        "coupling_chain": ["crystal bottom",
                           "open or lightly coupled gap",
                           "flat pickup surface",
                           "annular pickup ring"],
        "coupling_mode": mode,
        "gap_mm": gap,
        "bottom_aperture_open": True,
        "pickup_surface": "flat",
        "pickup_ring": {"od_mm": ring_od, "id_mm": ring_id,
                        "thickness_mm": ring_t},
        "note": "bottom coupling path preserved; no solid plastic "
                "under the crystal base",
    }

    o_ring = settings.get("o_ring")
    if mode == "o_ring_mounted" and not o_ring:
        raise CouplingError("o_ring_mounted needs an o_ring record "
                            "(material, cord_diameter_mm, id_mm, "
                            "compression_pct, contact_height_mm)")
    if o_ring:
        record = {
            "material": str(o_ring.get("material", "")),
            "cord_diameter_mm": float(o_ring.get("cord_diameter_mm", 0)),
            "id_mm": float(o_ring.get("id_mm", 0)),
            "compression_pct": float(o_ring.get("compression_pct", 0)),
            "contact_height_mm": float(o_ring.get("contact_height_mm",
                                                  0)),
        }
        for key in ("material", "cord_diameter_mm", "id_mm",
                    "compression_pct", "contact_height_mm"):
            if not record[key]:
                raise CouplingError(
                    f"o_ring.{key} must be recorded (compliant mounts "
                    f"are recorded, not assumed)")
        if record["compression_pct"] > O_RING_COMPRESSION_SOFT_MAX_PCT:
            raise CouplingError(
                f"O-ring compression {record['compression_pct']}% "
                f"exceeds {O_RING_COMPRESSION_SOFT_MAX_PCT}% — that is "
                f"hard damping, not a compliant mount")
        if record["compression_pct"] < O_RING_COMPRESSION_MIN_PCT:
            raise CouplingError(
                f"O-ring compression {record['compression_pct']}% "
                f"below {O_RING_COMPRESSION_MIN_PCT}% will not "
                f"stabilize the crystal")
        out["o_ring"] = record
    return out
