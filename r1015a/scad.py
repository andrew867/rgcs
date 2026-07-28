"""R10.15A — reference-model (OpenSCAD) import and verification.

The v7 SCAD is imported under the existing reference-model authority
(alongside the R10.13 ``reference_models`` convention). When an
OpenSCAD executable is available the file is compiled to confirm it
renders; when it is not, the module reports STATIC INSPECTION ONLY and
never claims a render it did not perform.
"""

from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
from pathlib import Path

from r1015a import DESIGN_ID, ScaleAError

SCAD_PATH = Path(__file__).resolve().parent / "data" / \
    "vogel_parametric_crystal_models_v7_scaleA_4096Hz.scad"
JSON_PATH = Path(__file__).resolve().parent / "data" / \
    "scale_a_4096hz_463867_design.json"

#: Presets that must be present for this lane to be coherent.
REQUIRED_PRESETS = ("ScaleA_4096Hz_Shear_463p867mm_6sided",
                    "ScaleA_4096Hz_Longitudinal_695p801mm_6sided_Control")

#: Exact strings that must appear (the frozen numbers).
REQUIRED_EXACT = ("463.8671875", "695.80078125", "51.843", "4096")


def _text() -> str:
    if not SCAD_PATH.is_file():
        raise ScaleAError(f"reference model missing at {SCAD_PATH}")
    return SCAD_PATH.read_text(encoding="utf-8", errors="replace")


def delimiter_balance(text: str) -> dict:
    """Balance check that ignores delimiters inside strings/comments."""
    depth = {"(": 0, "[": 0, "{": 0}
    close = {")": "(", "]": "[", "}": "{"}
    i, n = 0, len(text)
    in_line = in_block = in_str = False
    while i < n:
        c = text[i]
        nxt = text[i + 1] if i + 1 < n else ""
        if in_line:
            if c == "\n":
                in_line = False
        elif in_block:
            if c == "*" and nxt == "/":
                in_block = False
                i += 1
        elif in_str:
            if c == "\\":
                i += 1
            elif c == '"':
                in_str = False
        elif c == "/" and nxt == "/":
            in_line = True
            i += 1
        elif c == "/" and nxt == "*":
            in_block = True
            i += 1
        elif c == '"':
            in_str = True
        elif c in depth:
            depth[c] += 1
        elif c in close:
            depth[close[c]] -= 1
            if depth[close[c]] < 0:
                return {"balanced": False,
                        "error": f"unmatched {c!r} at offset {i}"}
        i += 1
    bad = {k: v for k, v in depth.items() if v != 0}
    return {"balanced": not bad, "unclosed": bad}


def static_inspection() -> dict:
    """Everything checkable without an OpenSCAD binary."""
    text = _text()
    bal = delimiter_balance(text)
    presets = {p: (p in text) for p in REQUIRED_PRESETS}
    exact = {e: (e in text) for e in REQUIRED_EXACT}
    # non-ASCII scan: generated CAD must stay ASCII for toolchains
    non_ascii = sorted({ch for ch in text if ord(ch) > 127})
    em_dash = [ch for ch in non_ascii if ch in "–—"]
    modules = re.findall(r"^module\s+(\w+)", text, re.M)
    functions = re.findall(r"^function\s+(\w+)", text, re.M)
    return {
        "schema": "rgcs.r1015a.scad-inspection.v1",
        "path": str(SCAD_PATH),
        "sha256": hashlib.sha256(SCAD_PATH.read_bytes()).hexdigest(),
        "bytes": SCAD_PATH.stat().st_size,
        "lines": text.count("\n") + 1,
        "delimiter_balance": bal,
        "required_presets": presets,
        "all_presets_present": all(presets.values()),
        "required_exact_numbers": exact,
        "all_exact_present": all(exact.values()),
        "module_count": len(modules), "function_count": len(functions),
        "modules": modules[:40], "functions": functions[:40],
        "non_ascii_characters": non_ascii,
        "ascii_clean": not non_ascii,
        "em_or_en_dash_present": bool(em_dash),
        "design_id_present": DESIGN_ID in text
        or "ScaleA_4096Hz_Shear" in text,
        "verification_level": "STATIC_INSPECTION_ONLY",
    }


def openscad_available() -> str | None:
    return shutil.which("openscad") or shutil.which("OpenSCAD")


def verify_render(out_stl: str | Path | None = None,
                  timeout_s: int = 900) -> dict:
    """Compile with OpenSCAD when present; otherwise report honestly."""
    exe = openscad_available()
    base = static_inspection()
    if not exe:
        base.update({
            "openscad_available": False,
            "render_attempted": False,
            "render_claimed": False,
            "note": "OpenSCAD is not installed in this environment, so "
                    "this file is STATIC-INSPECTED ONLY. F5/F6 render "
                    "and STL export must be performed where OpenSCAD "
                    "is available before it is treated as "
                    "render-verified.",
        })
        return base
    out = Path(out_stl or (SCAD_PATH.with_suffix(".stl")))
    run = subprocess.run([exe, "-o", str(out), str(SCAD_PATH)],
                         capture_output=True, text=True,
                         timeout=timeout_s)
    ok = run.returncode == 0 and out.is_file() and out.stat().st_size > 0
    base.update({
        "openscad_available": True, "openscad_path": exe,
        "render_attempted": True, "render_claimed": bool(ok),
        "returncode": run.returncode,
        "stderr_tail": (run.stderr or "")[-2000:],
        "output_stl": str(out) if ok else None,
        "output_bytes": out.stat().st_size if ok else 0,
        "verification_level": ("RENDER_VERIFIED" if ok
                               else "RENDER_FAILED"),
    })
    return base


def design_json() -> dict:
    import json
    if not JSON_PATH.is_file():
        raise ScaleAError(f"design JSON missing at {JSON_PATH}")
    return json.loads(JSON_PATH.read_text(encoding="utf-8"))


def validate_design_json(doc: dict | None = None) -> dict:
    """Schema + cross-check of the supplied JSON against derived
    geometry. Any disagreement is an error, not a rounding note."""
    from r1015a.design import ScaleAGeometry, half_wave_proxy
    d = doc if doc is not None else design_json()
    errors, checks = [], {}
    required = ("schema", "design_id", "status", "target_frequency_hz",
                "working_phase_velocity_m_s",
                "effective_half_wave_path_mm",
                "nominal_tip_to_tip_length_mm", "facets",
                "rx_face_slope_deg", "tx_face_slope_deg",
                "angle_mode", "diameter_mode", "nonclaims",
                "required_unresolved_inputs")
    for k in required:
        if k not in d:
            errors.append(f"missing required field {k!r}")
    if d.get("design_id") != DESIGN_ID:
        errors.append(f"design_id must be {DESIGN_ID!r}")
    if not errors:
        proxy = half_wave_proxy("shear_proxy",
                                d["target_frequency_hz"])
        checks["half_wave_path"] = abs(
            proxy["length_mm"] - d["effective_half_wave_path_mm"])
        geo = ScaleAGeometry(
            length_mm=d["nominal_tip_to_tip_length_mm"],
            facets=d["facets"],
            length_to_avg_diameter=d["length_to_average_diameter"],
            wide_to_narrow_ratio=d["wide_to_narrow_ratio"],
            rx_face_slope_deg=d["rx_face_slope_deg"],
            tx_face_slope_deg=d["tx_face_slope_deg"],
            angle_mode=d["angle_mode"],
            diameter_mode=d["diameter_mode"])
        for key, got in (("wide_diameter_mm", geo.wide_diameter_mm),
                         ("narrow_diameter_mm", geo.narrow_diameter_mm),
                         ("rx_cap_height_mm", geo.rx_cap_height_mm),
                         ("tx_cap_height_mm", geo.tx_cap_height_mm),
                         ("shaft_height_mm", geo.shaft_height_mm),
                         ("idealized_volume_cm3", geo.volume_cm3),
                         ("idealized_mass_g_at_2p65", geo.mass_g())):
            if key in d:
                checks[key] = abs(got - d[key])
        worst = max(checks.values()) if checks else 0.0
        if worst > 1e-6:
            errors.append(
                f"derived geometry disagrees with the supplied JSON by "
                f"{worst:.3e} mm/cm3/g; the JSON is not reproducible "
                "from its own declared inputs")
    if d.get("status") != "GEOMETRY_AND_HALF_WAVE_PROXY_ONLY":
        errors.append("status must remain "
                      "GEOMETRY_AND_HALF_WAVE_PROXY_ONLY")
    return {"ok": not errors, "errors": errors,
            "cross_check_max_deviation": max(checks.values())
            if checks else None,
            "cross_checks": checks,
            "nonclaim_count": len(d.get("nonclaims", [])),
            "unresolved_input_count": len(
                d.get("required_unresolved_inputs", []))}
