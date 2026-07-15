"""FEA export contract (RGCS v3, Agent 08; scoped by crystal application
section 8).

Exports the anisotropic material card (full alpha-quartz Voigt stiffness in
SI + density, from Agent 05) and the specimen geometry parameters as a
neutral, solver-agnostic JSON document with a sha256 self-checksum. This is
a CONTRACT, not a mesh: any FEA pipeline (CalculiX/Elmer/COMSOL import
scripts) consumes the JSON; meshing stays outside this repository.

Classification: the material card is Established handbook input (D5-002);
the export format itself is engineering. JSON uses null-not-NaN (v2 rule).
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

from .anisotropy import (ALPHA_QUARTZ_C_GPA, ALPHA_QUARTZ_DENSITY_KG_M3,
                         alpha_quartz_stiffness_pa)
from .provenance import classified

__all__ = ["FEA_CONTRACT_VERSION", "material_card", "fea_export",
           "write_fea_export", "verify_fea_export"]

FEA_CONTRACT_VERSION = "1.0"


@classified("Established", sources=("D5-002", "Bechmann 1958"),
            note="alpha-quartz anisotropic material card in SI (Pa, kg/m^3) "
                 "for FEA; orientation must be supplied by the consumer")
def material_card() -> dict[str, Any]:
    """The alpha-quartz FEA material card (SI units)."""
    return {
        "material": "alpha-quartz",
        "symmetry_class": "trigonal-32",
        "stiffness_voigt_pa": [[float(v) for v in row]
                               for row in alpha_quartz_stiffness_pa()],
        "stiffness_voigt_gpa": [[float(v) for v in row]
                                for row in ALPHA_QUARTZ_C_GPA],
        "density_kg_m3": ALPHA_QUARTZ_DENSITY_KG_M3,
        "source": "Bechmann 1958 / Auld AFWS (D5-002; closes v2 D-19a)",
        "classification": "Established",
    }


def _require_geometry(geometry: dict[str, Any]) -> dict[str, Any]:
    required = ("length_mm", "diameter_wide_mm", "diameter_narrow_mm",
                "facet_count")
    for key in required:
        if key not in geometry:
            raise ValueError(f"geometry missing required field {key!r}")
        v = geometry[key]
        if not (isinstance(v, (int, float)) and math.isfinite(v) and v > 0):
            raise ValueError(f"geometry field {key!r} must be positive and "
                             f"finite")
    return dict(geometry)


@classified("Derived", sources=("RGCS_CRYSTAL_APPLICATION.md section 8",),
            note="solver-agnostic FEA export document: material card + "
                 "geometry + orientation + provenance; NOT a mesh")
def fea_export(specimen_id: str, geometry: dict[str, Any],
               orientation_deg: dict[str, float] | None = None,
               notes: str = "") -> dict[str, Any]:
    """Build the FEA export document for one specimen.

    ``geometry`` follows the v2 specimen schema fields (length_mm,
    diameter_wide_mm, diameter_narrow_mm, facet_count, ...).
    ``orientation_deg`` is the measured crystallographic orientation
    (Euler z-x-z; None = orientation UNKNOWN, in which case any FEA result
    inherits the v2 scalar +/-5% wave-speed band instead of the
    anisotropic model -- the model-selection rule of crystal application
    section 7)."""
    if not specimen_id or not isinstance(specimen_id, str):
        raise ValueError("specimen_id must be a non-empty string")
    geo = _require_geometry(geometry)
    if orientation_deg is not None:
        for axis in ("z1_deg", "x_deg", "z2_deg"):
            v = orientation_deg.get(axis)
            if not (isinstance(v, (int, float)) and math.isfinite(v)):
                raise ValueError(f"orientation_deg needs finite {axis!r}")
    doc = {
        "fea_contract_version": FEA_CONTRACT_VERSION,
        "specimen_id": specimen_id,
        "material": material_card(),
        "geometry": geo,
        "orientation_euler_zxz_deg": orientation_deg,
        "orientation_known": orientation_deg is not None,
        "model_selection_note": (
            "orientation measured: use anisotropic Christoffel model "
            "(RSCS-O.17)" if orientation_deg is not None else
            "orientation UNKNOWN: results carry the v2 scalar v_L +/-5% "
            "band (RGCS-M.10); do not present anisotropic precision"),
        "notes": notes,
    }
    payload = json.dumps(doc, sort_keys=True).encode("utf-8")
    doc["sha256"] = hashlib.sha256(payload).hexdigest()
    return doc


@classified("Derived", sources=("RGCS_CRYSTAL_APPLICATION.md section 8",),
            note="write + self-checksum; verify_fea_export round-trips")
def write_fea_export(doc: dict[str, Any], path: str | Path) -> Path:
    """Write an FEA export document as canonical JSON."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=2, sort_keys=True),
                 encoding="utf-8")
    return p


@classified("Derived", sources=(),
            note="recomputes the embedded sha256 over the document minus "
                 "its checksum field")
def verify_fea_export(path: str | Path) -> bool:
    """True iff the file's embedded sha256 matches its content."""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    stated = doc.pop("sha256", None)
    payload = json.dumps(doc, sort_keys=True).encode("utf-8")
    return stated == hashlib.sha256(payload).hexdigest()
