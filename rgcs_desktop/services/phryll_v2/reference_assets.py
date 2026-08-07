"""Reference asset registry and measurement tools.

CC-SA reference assets are style/size-family references ONLY. This
module loads the packaged registry (with prior mesh-decode seed data),
measures STL files directly when they are present, and compares a
reference cone profile against a generated custom profile — advisory
output; the generated geometry is always primary.
"""
from __future__ import annotations

import json
import math
import struct
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import numpy as np

from rgcs_desktop.services.phryll_v2.crystal_profile import (
    CrystalProfile, interpolate_crystal_radius)

REGISTRY_FILE = (Path(__file__).resolve().parents[2] / "data"
                 / "phryll_v2_reference_registry.json")


class ReferenceError(ValueError):
    pass


@dataclass
class MeshBounds:
    n_triangles: int
    min_mm: tuple[float, float, float]
    max_mm: tuple[float, float, float]

    @property
    def size_mm(self) -> tuple[float, float, float]:
        return tuple(hi - lo for lo, hi in zip(self.min_mm, self.max_mm))


@lru_cache(maxsize=1)
def _registry() -> dict:
    return json.loads(REGISTRY_FILE.read_text(encoding="utf-8"))


def load_reference_manifest() -> list[dict]:
    """All registered reference assets (id, file, role, license)."""
    return list(_registry()["assets"])


def source_profiles() -> list[dict]:
    """Source cone profiles, M2_TEXT and M2_MESH deliberately separate."""
    return list(_registry()["source_profiles"])


def source_profile_by_id(profile_id: str) -> dict:
    for profile in source_profiles():
        if profile["profile_id"] == profile_id:
            return profile
    raise ReferenceError(f"unknown source profile {profile_id!r}")


def cone_profile_fits() -> list[dict]:
    """Prior mesh-decode cone fits (seed data)."""
    return list(_registry()["cone_profile_fits"])


def load_stl_triangles(path: str | Path) -> np.ndarray:
    """Read binary or ASCII STL into (n, 3, 3) vertices."""
    path = Path(path)
    data = path.read_bytes()
    if len(data) < 84:
        raise ReferenceError(f"{path.name}: too small to be an STL")
    n = struct.unpack("<I", data[80:84])[0]
    if len(data) == 84 + n * 50:            # binary layout matches
        tris = np.frombuffer(data[84:], dtype=np.uint8)
        tris = tris.reshape(n, 50)[:, 12:48].copy()
        return tris.view("<f4").reshape(n, 3, 3).astype(np.float64)
    text = data.decode("ascii", errors="ignore")
    if "vertex" not in text:
        raise ReferenceError(f"{path.name}: neither binary nor ASCII STL")
    values = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("vertex"):
            values.append([float(v) for v in line.split()[1:4]])
    if len(values) % 3:
        raise ReferenceError(f"{path.name}: vertex count not divisible "
                             f"by 3")
    return np.asarray(values).reshape(-1, 3, 3)


def measure_stl_bounds(path: str | Path) -> MeshBounds:
    tris = load_stl_triangles(path)
    flat = tris.reshape(-1, 3)
    return MeshBounds(n_triangles=len(tris),
                      min_mm=tuple(float(v) for v in flat.min(axis=0)),
                      max_mm=tuple(float(v) for v in flat.max(axis=0)))


def measure_cone_profile(path: str | Path, n_stations: int = 14) -> list[dict]:
    """Radial profile of a cone-like mesh: per z-station max radius
    about the bbox center axis. Direct measurement when the asset file
    is present (seed data covers the absent case)."""
    tris = load_stl_triangles(path)
    flat = tris.reshape(-1, 3)
    z_lo, z_hi = flat[:, 2].min(), flat[:, 2].max()
    cx = (flat[:, 0].min() + flat[:, 0].max()) / 2
    cy = (flat[:, 1].min() + flat[:, 1].max()) / 2
    radii = np.hypot(flat[:, 0] - cx, flat[:, 1] - cy)
    stations = []
    for i in range(n_stations):
        z0 = z_lo + (z_hi - z_lo) * i / n_stations
        z1 = z_lo + (z_hi - z_lo) * (i + 1) / n_stations
        mask = (flat[:, 2] >= z0) & (flat[:, 2] < z1)
        if mask.any():
            stations.append({"z_mm": float((z0 + z1) / 2 - z_lo),
                             "outer_r_mm": float(radii[mask].max())})
    return stations


def compare_reference_to_custom(profile_id: str,
                                crystal: CrystalProfile,
                                desired_clearance_mm: float) -> dict:
    """Advisory: would this stock reference family clear the crystal?

        reference_inner_radius(z) >= r_crystal(z) + desired_clearance

    Uses the registered top/base inner diameters as a linear profile
    over the reference height. Never a design command.
    """
    ref = source_profile_by_id(profile_id)
    top_d = ref.get("top_inner_d_mm")
    base_d = ref.get("base_inner_d_mm")
    height = ref.get("height_mm")
    if not (top_d and base_d and height):
        return {"profile_id": profile_id, "comparable": False,
                "reason": "registered profile has no inner cone "
                          "dimensions", "advisory": True}
    overlap = min(float(height), crystal.length_mm)
    failures = []
    min_margin = math.inf
    for i in range(25):
        z = overlap * i / 24
        ref_r = (float(base_d)
                 + (float(top_d) - float(base_d)) * (z / float(height))) / 2
        need = interpolate_crystal_radius(crystal, z) \
            + desired_clearance_mm
        margin = ref_r - need
        min_margin = min(min_margin, margin)
        if margin < 0:
            failures.append(f"z={z:.1f} mm: short by {-margin:.2f} mm")
    return {"profile_id": profile_id, "comparable": True,
            "fits": not failures, "min_margin_mm": round(min_margin, 3),
            "overlap_mm": overlap, "failures": failures[:5],
            "advisory": True,
            "note": "reference compatibility is advisory; the generated "
                    "custom cone is primary"}
