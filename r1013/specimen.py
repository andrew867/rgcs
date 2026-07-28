"""R10.13 Phases 07-10 — crystal-specimen records for normal users.

Implements ``rgcs.crystal-specimen/1.0``: load, field-level validation
with repair steps, deterministic canonical serialization and hashing,
migration without in-place mutation, inspection, and conversion onto
the existing ``rscs2_core.crystal110`` geometry authority (the
geometry equations are NOT duplicated here).

Source claims live in ``source_claims`` and are never read as
measurements; measurements live in ``measurements``.
"""

from __future__ import annotations

import copy
import hashlib
import json
import math
from pathlib import Path

from r1013 import SPECIMEN_SCHEMA_VERSION
from r1013.errors import UserError

DIAMETER_MODES = ("across_vertices", "across_flats")
ANGLE_MODES = ("face_slope", "axis_to_face", "apex_included")
ORIENTATION_STATUS = ("known", "estimated", "assumed", "unknown")
HANDEDNESS = ("left", "right", "unknown", "not_applicable")

#: Densities (g/cm^3) for known material ids. alpha_quartz comes from
#: the frozen v3 constant (2649 kg/m^3, Bechmann/Auld handbook line).
KNOWN_MATERIALS = {"alpha_quartz": 2.649}

TEMPLATE = {
    "schema_version": SPECIMEN_SCHEMA_VERSION,
    "specimen_id": "my-crystal-001",
    "name": "My crystal",
    "description": "Replace every value with your own measurements.",
    "material": {"material_id": "alpha_quartz", "density_g_cm3": 2.65,
                 "handedness": "unknown"},
    "geometry": {"length_mm": None, "wide_diameter_mm": None,
                 "narrow_diameter_mm": None, "facets": 6,
                 "female_angle_deg": None, "male_angle_deg": None,
                 "diameter_mode": "across_vertices",
                 "angle_mode": "face_slope"},
    "orientation": {"status": "unknown"},
    "measurements": {"mass_g": None},
    "provenance": {"operator": "", "measurement_date": "",
                   "source_type": "measurement", "notes": ""},
}


# ----------------------------------------------------------- load/save
def load(path) -> dict:
    p = Path(path)
    if not p.is_file():
        raise UserError("RGCS-E001", f"No file at '{p}'.")
    try:
        rec = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as ex:
        raise UserError("RGCS-E002",
                        f"'{p.name}' is not valid JSON: {ex.msg} at "
                        f"line {ex.lineno}, column {ex.colno}.") from ex
    if not isinstance(rec, dict):
        raise UserError("RGCS-E002",
                        f"'{p.name}' must contain a JSON object, not "
                        f"{type(rec).__name__}.")
    return rec


def canonical_json(rec: dict) -> str:
    """Deterministic canonical serialization: sorted keys, fixed
    separators, no NaN, UTF-8-safe escapes."""
    return json.dumps(rec, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False)


def specimen_hash(rec: dict) -> str:
    return hashlib.sha256(canonical_json(rec).encode()).hexdigest()


# ---------------------------------------------------------- validation
def _num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) \
        and math.isfinite(v)


def validate(rec: dict) -> dict:
    """Field-level validation. Returns {ok, errors, warnings}; every
    error has a stable code, plain message, and repair step."""
    errors, warnings = [], []

    def err(code, msg, field):
        errors.append(UserError(code, msg, field).record())

    if rec.get("schema_version") != SPECIMEN_SCHEMA_VERSION:
        err("RGCS-E003",
            f"schema_version is {rec.get('schema_version')!r}; expected "
            f"'{SPECIMEN_SCHEMA_VERSION}'.", "schema_version")
    for f in ("specimen_id", "name"):
        v = rec.get(f)
        if not isinstance(v, str) or not v.strip():
            err("RGCS-E004", f"'{f}' must be a non-empty text value.", f)

    mat = rec.get("material")
    if not isinstance(mat, dict) or not mat.get("material_id"):
        err("RGCS-E004", "material.material_id is required (for quartz "
            "use 'alpha_quartz').", "material.material_id")
        mat = {}
    dens = mat.get("density_g_cm3")
    if dens is not None and (not _num(dens) or dens <= 0):
        err("RGCS-E005", f"material.density_g_cm3 is {dens!r}; it must "
            "be a positive number in g/cm3 (quartz is near 2.65) or "
            "null if unknown.", "material.density_g_cm3")
    hand = mat.get("handedness")
    if hand is not None and hand not in HANDEDNESS:
        err("RGCS-E006", f"material.handedness {hand!r} is not one of "
            f"{HANDEDNESS}.", "material.handedness")
    mid = mat.get("material_id")
    if mid and mid not in KNOWN_MATERIALS:
        warnings.append(
            f"material_id '{mid}' has no built-in material record; "
            "anisotropic calculations will refuse (only "
            f"{sorted(KNOWN_MATERIALS)} ship with this release).")

    geo = rec.get("geometry")
    if not isinstance(geo, dict):
        err("RGCS-E004", "geometry section is required.", "geometry")
        geo = {}
    for f in ("length_mm", "wide_diameter_mm"):
        v = geo.get(f)
        if v is None:
            err("RGCS-E004", f"geometry.{f} is required. Measure it in "
                "millimetres.", f"geometry.{f}")
        elif not _num(v) or v <= 0:
            err("RGCS-E005", f"geometry.{f} is {v!r}; it must be a "
                "positive number of millimetres.", f"geometry.{f}")
    nd = geo.get("narrow_diameter_mm")
    if nd is not None and (not _num(nd) or nd <= 0):
        err("RGCS-E005", f"geometry.narrow_diameter_mm is {nd!r}; use a "
            "positive number of millimetres, or null if not measured.",
            "geometry.narrow_diameter_mm")
    facets = geo.get("facets")
    if not isinstance(facets, int) or isinstance(facets, bool) or facets < 3:
        err("RGCS-E005", f"geometry.facets is {facets!r}; it must be a "
            "whole number of 3 or more (natural quartz is 6).",
            "geometry.facets")
    for f in ("female_angle_deg", "male_angle_deg"):
        v = geo.get(f)
        if v is not None and (not _num(v) or not (0 < v < 180)):
            err("RGCS-E005", f"geometry.{f} is {v!r}; use degrees "
                "strictly between 0 and 180, or null if not measured.",
                f"geometry.{f}")
    if geo.get("diameter_mode") not in DIAMETER_MODES:
        err("RGCS-E006", f"geometry.diameter_mode is "
            f"{geo.get('diameter_mode')!r}.", "geometry.diameter_mode")
    if geo.get("angle_mode") not in ANGLE_MODES:
        err("RGCS-E006", f"geometry.angle_mode is "
            f"{geo.get('angle_mode')!r}.", "geometry.angle_mode")

    wd = geo.get("wide_diameter_mm")
    if _num(wd) and _num(nd) and nd > wd:
        err("RGCS-E007", f"narrow_diameter_mm ({nd}) is larger than "
            f"wide_diameter_mm ({wd}); the names are probably swapped.",
            "geometry.narrow_diameter_mm")
    L = geo.get("length_mm")
    if (_num(L) and _num(wd) and geo.get("facets") == 6
            and _num(geo.get("female_angle_deg"))
            and _num(geo.get("male_angle_deg"))
            and geo.get("angle_mode") == "face_slope"
            and errors == []):
        # cap-height feasibility via the FROZEN v2 helpers
        from rgcs_core.geometry.crystal import (apothem_mm,
                                                termination_height_mm)
        mode = geo.get("diameter_mode", "across_vertices")
        hf = termination_height_mm(
            apothem_mm(wd, geo["facets"], mode), geo["female_angle_deg"])
        hm = termination_height_mm(
            apothem_mm(nd if _num(nd) else wd, geo["facets"], mode),
            geo["male_angle_deg"])
        if hf + hm >= L:
            err("RGCS-E007", "The two termination caps "
                f"({hf:.2f} mm + {hm:.2f} mm) meet or exceed the total "
                f"length ({L} mm); there is no prism left. Re-check the "
                "length and the angle convention.", "geometry.length_mm")

    ori = rec.get("orientation")
    if ori is not None:
        if not isinstance(ori, dict) or \
                ori.get("status") not in ORIENTATION_STATUS:
            err("RGCS-E006", "orientation.status must be one of "
                f"{ORIENTATION_STATUS}.", "orientation.status")
        else:
            eul = ori.get("euler_zxz_deg")
            if eul is not None and (not isinstance(eul, list)
                                    or len(eul) != 3
                                    or not all(_num(x) for x in eul)):
                err("RGCS-E005", "orientation.euler_zxz_deg must be "
                    "three numbers in degrees.",
                    "orientation.euler_zxz_deg")
            if ori.get("status") in ("known", "estimated") and \
                    ori.get("euler_zxz_deg") is None:
                err("RGCS-E004", "orientation.status is "
                    f"'{ori['status']}' but euler_zxz_deg is missing.",
                    "orientation.euler_zxz_deg")
            if ori.get("status") in ("assumed", "unknown"):
                warnings.append(
                    "Orientation is not measured; anisotropic results "
                    "will carry an orientation-unknown warning and an "
                    "ensemble spread instead of a single line.")

    meas = rec.get("measurements")
    if meas is not None and not isinstance(meas, dict):
        err("RGCS-E004", "measurements must be an object.",
            "measurements")
    sc = rec.get("source_claims")
    if sc is not None:
        if not isinstance(sc, list) or \
                not all(isinstance(x, dict) for x in sc):
            err("RGCS-E004", "source_claims must be a list of objects.",
                "source_claims")
        else:
            for i, claim in enumerate(sc):
                for k in claim:
                    if k in ("mass_g", "length_mm", "frequency_hz"):
                        warnings.append(
                            f"source_claims[{i}].{k}: a source claim is "
                            "never used as a measurement; move it to "
                            "'measurements' only if you measured it.")
    if isinstance(meas, dict) and meas.get("mass_g") is None:
        warnings.append("No mass_g measurement: the density consistency "
                        "check will be skipped.")
    if nd is None:
        warnings.append("narrow_diameter_mm is null: quick estimates "
                        "work, but a full mesh needs both diameters.")

    return {"ok": not errors, "errors": errors, "warnings": warnings,
            "specimen_hash": specimen_hash(rec) if not errors else None}


def require_valid(rec: dict) -> None:
    v = validate(rec)
    if not v["ok"]:
        e = v["errors"][0]
        raise UserError(e["code"], e["message"], e["field"])


# ----------------------------------------------------------- migration
def migrate(rec: dict) -> dict:
    """Return a NEW record at the current schema version. The input is
    never mutated. Older/looser records get fields normalized and a
    migration note appended to provenance."""
    out = copy.deepcopy(rec)
    notes = []
    if out.get("schema_version") != SPECIMEN_SCHEMA_VERSION:
        notes.append(f"schema_version {out.get('schema_version')!r} -> "
                     f"{SPECIMEN_SCHEMA_VERSION}")
        out["schema_version"] = SPECIMEN_SCHEMA_VERSION
    geo = out.setdefault("geometry", {})
    for legacy, current in (("length", "length_mm"),
                            ("wide_diameter", "wide_diameter_mm"),
                            ("narrow_diameter", "narrow_diameter_mm")):
        if legacy in geo and current not in geo:
            geo[current] = geo.pop(legacy)
            notes.append(f"geometry.{legacy} -> {current} (assumed mm)")
    geo.setdefault("diameter_mode", "across_vertices")
    geo.setdefault("angle_mode", "face_slope")
    geo.setdefault("facets", 6)
    out.setdefault("orientation", {"status": "unknown"})
    if notes:
        prov = out.setdefault("provenance", {})
        prov["migration"] = (prov.get("migration", []) + notes)
    return out


# ---------------------------------------------------------- inspection
def inspect(rec: dict) -> dict:
    v = validate(rec)
    geo = rec.get("geometry", {})
    summary = {
        "specimen_id": rec.get("specimen_id"),
        "name": rec.get("name"),
        "material": rec.get("material", {}).get("material_id"),
        "length_mm": geo.get("length_mm"),
        "wide_diameter_mm": geo.get("wide_diameter_mm"),
        "narrow_diameter_mm": geo.get("narrow_diameter_mm"),
        "facets": geo.get("facets"),
        "orientation_status": (rec.get("orientation") or {}).get(
            "status", "unknown"),
        "valid": v["ok"],
        "error_count": len(v["errors"]),
        "warning_count": len(v["warnings"]),
        "specimen_hash": v["specimen_hash"],
        "ready_for": readiness(rec),
    }
    return summary


def readiness(rec: dict) -> dict:
    """What each model can run with the data present (Phase 09)."""
    geo = rec.get("geometry", {})
    have_L = _num(geo.get("length_mm"))
    have_wd = _num(geo.get("wide_diameter_mm"))
    have_nd = _num(geo.get("narrow_diameter_mm"))
    have_angles = _num(geo.get("female_angle_deg")) and \
        _num(geo.get("male_angle_deg"))
    return {
        "quick_estimate": bool(have_L),
        "christoffel": True,      # material-level, needs no geometry
        "geometry_report": bool(have_L and have_wd),
        "mesh_and_modes": bool(have_L and have_wd and have_nd
                               and have_angles),
        "missing_for_mesh": [f for f, ok in (
            ("length_mm", have_L), ("wide_diameter_mm", have_wd),
            ("narrow_diameter_mm", have_nd),
            ("female_angle_deg and male_angle_deg", have_angles))
            if not ok],
    }


# ------------------------------------------- geometry authority bridge
def to_crystal(rec: dict):
    """Convert a valid, mesh-ready specimen onto the EXISTING
    rscs2_core.crystal110.CanonicalCrystal (no equation duplication).
    Refuses (typed) when required values are null."""
    require_valid(rec)
    geo = rec["geometry"]
    miss = readiness(rec)["missing_for_mesh"]
    if miss:
        raise UserError("RGCS-E008",
                        "This calculation needs the full shape. Still "
                        "missing: " + ", ".join(miss) + ".")
    if geo.get("diameter_mode") == "across_flats":
        # convert to across_vertices via the frozen apothem relation:
        # apothem = R*cos(pi/n) -> D_vertices = D_flats / cos(pi/n)
        k = math.cos(math.pi / geo["facets"])
        wd, nd = geo["wide_diameter_mm"] / k, geo["narrow_diameter_mm"] / k
    else:
        wd, nd = geo["wide_diameter_mm"], geo["narrow_diameter_mm"]
    if geo.get("angle_mode") != "face_slope":
        raise UserError("RGCS-E013",
                        f"angle_mode '{geo['angle_mode']}' is recorded "
                        "but automatic conversion to face_slope is not "
                        "provided in this release; re-express the "
                        "angles as face_slope (see "
                        "MEASURING_YOUR_CRYSTAL).")
    from rscs2_core.crystal110 import CanonicalCrystal
    eul = tuple((rec.get("orientation") or {}).get(
        "euler_zxz_deg") or (0.0, 0.0, 0.0))
    return CanonicalCrystal(
        variant=f"specimen_{rec['specimen_id']}",
        length_mm=geo["length_mm"], wide_diameter_mm=wd,
        narrow_diameter_mm=nd, facets=geo["facets"],
        female_angle_deg=geo["female_angle_deg"],
        male_angle_deg=geo["male_angle_deg"],
        orientation_euler_zxz_deg=eul)


def geometry_report(rec: dict) -> dict:
    c = to_crystal(rec)
    from rscs2_core.crystal110 import analytic_volume_mm3
    vol = analytic_volume_mm3(c)
    return {"specimen_id": rec["specimen_id"],
            "crystal_record": c.record(),
            "analytic_volume_mm3": vol,
            "evidence_class": "ANALYTIC",
            "note": "computed from the recorded dimensions with the "
                    "frozen v2 geometry conventions; not a measurement"}


def density_check(rec: dict, tolerance_pct: float = 3.0) -> dict:
    """Measured mass vs analytic volume vs declared density."""
    require_valid(rec)
    mass = (rec.get("measurements") or {}).get("mass_g")
    if not _num(mass) or mass <= 0:
        raise UserError("RGCS-E008", "density-check needs "
                        "measurements.mass_g (grams).")
    vol_mm3 = geometry_report(rec)["analytic_volume_mm3"]
    implied = mass / (vol_mm3 / 1000.0)          # g/cm3
    declared = (rec.get("material") or {}).get("density_g_cm3")
    out = {"mass_g": mass, "analytic_volume_mm3": vol_mm3,
           "implied_density_g_cm3": implied,
           "declared_density_g_cm3": declared,
           "evidence_class": "ANALYTIC"}
    if declared:
        dev = 100.0 * (implied - declared) / declared
        out["deviation_pct"] = dev
        out["consistent"] = abs(dev) <= tolerance_pct
        if not out["consistent"]:
            out["error"] = UserError(
                "RGCS-E009",
                f"Implied density {implied:.3f} g/cm3 differs from the "
                f"declared {declared} g/cm3 by {dev:+.1f}% (tolerance "
                f"{tolerance_pct}%).").record()
    else:
        out["consistent"] = None
        out["note"] = "no declared density; nothing to compare against"
    return out
