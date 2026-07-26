"""Trace serialization — RecursiveDecodeTrace -> JSON-safe dict (§5.1)."""

from __future__ import annotations

from fractions import Fraction

from cwatlas.r1084.cw_hedron_state import RecursiveDecodeTrace


def _safe(o):
    if isinstance(o, Fraction):
        return {"num": o.numerator, "den": o.denominator,
                "float": float(o)}
    if isinstance(o, dict):
        return {k: _safe(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_safe(v) for v in o]
    return o


def trace_to_dict(t: RecursiveDecodeTrace) -> dict:
    r = t.region
    return _safe({
        "raw": t.raw,
        "frame": {
            "family": t.frame.family, "codebook": t.frame.codebook,
            "source_face_id": t.frame.source_face.value,
            "mesh_face_id": t.frame.mesh_face.value,
            "vertex_order": t.frame.vertex_order,
            "profile_id": t.frame.profile_id,
        },
        "compensation": t.compensation,
        "levels": t.levels,
        "final_region": None if r is None else {
            "surface_polygon_latlon": r.polygon_latlon,
            "surface_corners_chart": r.surface.corners,
            "surface_orientation": r.surface.orientation,
            "radial_interval_km": (float(r.radial.interval.r_min),
                                   float(r.radial.interval.r_max)),
            "radial_root_profile": r.radial.root_profile,
            "uncertainty": {
                "surface_max_radius_km":
                    r.uncertainty.surface_max_radius_km,
                "radial_thickness_km": r.uncertainty.radial_thickness_km,
                "effective_3d_scale_km":
                    r.uncertainty.effective_3d_scale_km,
                "axis_depths": r.uncertainty.axis_depths,
                "partial_level_axes": r.uncertainty.partial_level_axes,
            },
        },
        "representative": None if t.representative is None else {
            "lat_deg": t.representative.lat_deg,
            "lon_deg": t.representative.lon_deg,
            "height_km_interval": t.representative.height_km_interval,
            "label": t.representative.label,
        },
        "claims": {"SOURCE_ORIGIN_VALIDATED": "no",
                   "PHYSICAL_ANOMALOUS_GRAVITY_VALIDATED": "no"},
    })
