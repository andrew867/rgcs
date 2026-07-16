"""Canonical 110 mm crystal geometry + deterministic gmsh meshing
(Agent 05, RSCS2-G.1/G.2/G.5/G.6).

Two related configurations that MUST NOT be confused:

  * IDEAL N=7 ladder crystal: L = (v_L / (2 f_carrier)) / 7
      = (6310 m/s / (2*4096 Hz)) / 7 = 770.263671875/7 mm
      = 110.0376674107142857... mm
    Provenance: the frozen v2 defaults v_L = 6310 m/s (RGCS-M.10) and
    the 4096 Hz carrier; the half-wave ladder length split into N=7.
    The division is ARITHMETIC; it confers no physical claim.
  * NOMINAL real specimen: L = 110.000000 mm exactly.

Default proportions (documented, not invented): the wide/narrow
diameters scale the v2 reference specimen SP-Q154 (154 mm long,
40/30 mm across-vertices) to the canonical length:
  D_wide = L * 40/154,  D_narrow = L * 30/154.
Both diameters are explicit parameters recorded in every manifest.

Angles: female (receiver) 51.843 deg, male (transmitter) 60 deg,
face_slope convention, across_vertices diameters — all via the FROZEN
v2 helpers (`rgcs_core.geometry.crystal`: apothem_mm,
termination_height_mm, polygon_area_mm2; conventions RGCS-M.1..M.4).
The angle VALUES are Source claims (RG-16), as in v2.

Frames: body axis = +Z from the female (wide) apex at z=0 to the male
apex at z=L (the v2 x-axis convention maps x_v2 = z_body). The quartz
C-axis is aligned with +Z by default; other orientations via the Agent
04 Euler record. NO eye coordinate is assumed anywhere.

Meshing: gmsh as an EXTERNAL SUBPROCESS (DV4-006) on a generated
built-in-kernel .geo polyhedron; meshio (MIT) reads the .msh. STEP
export status: NOT_GENERATED — the built-in kernel cannot emit STEP; an
OCC-kernel path is documented but IMPLEMENTED_DOCUMENTED_UNTESTED per
DV4-013(4).
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import meshio
import numpy as np

from rgcs_core.geometry.crystal import (apothem_mm, polygon_area_mm2,
                                        termination_height_mm)

__all__ = ["CanonicalCrystal", "IDEAL_LENGTH_MM", "NOMINAL_LENGTH_MM",
           "build_crystal", "mesh_crystal", "mesh_quality",
           "analytic_volume_mm3"]

#: Ideal N=7 ladder length (mm): (6310/(2*4096)) m / 7, exact decimal.
IDEAL_LENGTH_MM = 770.263671875 / 7.0        # 110.0376674107142857...
NOMINAL_LENGTH_MM = 110.0

_SPQ154_WIDE_RATIO = 40.0 / 154.0
_SPQ154_NARROW_RATIO = 30.0 / 154.0


@dataclass(frozen=True)
class CanonicalCrystal:
    """Parametric canonical crystal record. Lengths/diameters in mm."""
    variant: str                       # "ideal_n7" | "nominal"
    length_mm: float
    wide_diameter_mm: float
    narrow_diameter_mm: float
    facets: int = 6
    female_angle_deg: float = 51.843   # face_slope, Source claim RG-16
    male_angle_deg: float = 60.0
    orientation_euler_zxz_deg: tuple = (0.0, 0.0, 0.0)   # C-axis = +Z

    @property
    def female_cap_height_mm(self) -> float:
        return termination_height_mm(
            apothem_mm(self.wide_diameter_mm, self.facets),
            self.female_angle_deg)

    @property
    def male_cap_height_mm(self) -> float:
        return termination_height_mm(
            apothem_mm(self.narrow_diameter_mm, self.facets),
            self.male_angle_deg)

    @property
    def shaft_length_mm(self) -> float:
        s = (self.length_mm - self.female_cap_height_mm
             - self.male_cap_height_mm)
        if s <= 0:
            raise ValueError("caps exceed total length")
        return s

    def record(self) -> dict:
        return {
            "variant": self.variant,
            "length_mm": repr(self.length_mm),
            "length_mm_float": self.length_mm,
            "wide_diameter_mm": self.wide_diameter_mm,
            "narrow_diameter_mm": self.narrow_diameter_mm,
            "diameter_policy": "SP-Q154 ratios 40/154 and 30/154 x L "
                               "(documented default; explicit parameters)",
            "facets": self.facets,
            "female_angle_deg": self.female_angle_deg,
            "male_angle_deg": self.male_angle_deg,
            "angle_mode": "face_slope",
            "diameter_mode": "across_vertices",
            "female_cap_height_mm": self.female_cap_height_mm,
            "male_cap_height_mm": self.male_cap_height_mm,
            "shaft_length_mm": self.shaft_length_mm,
            "frame": "body +Z from female apex (z=0) to male apex (z=L); "
                     "x_v2 == z_body; quartz C-axis default +Z",
            "orientation_euler_zxz_deg": list(self.orientation_euler_zxz_deg),
            "geometric_centre_z_mm": self.length_mm / 2.0,
            "rgcs_node_prior": "shaft midpoint prior per frozen "
                               "rgcs_core.geometry.nodes (RGCS-M.38/39); "
                               "measured node NOT supplied",
            "eye_coordinate": None,
            "region_annotations": {
                "electrode_candidates": "shaft facets 1 and 4 (opposed), "
                                        "z in [0.35L, 0.65L]",
                "coil_envelopes": "coaxial, centered z=0.3L and z=0.7L",
                "optical_entry": "lower shaft facet 1, z ~ 0.4L",
                "fixture_pads": "3-point cradle at z = 0.224L, 0.776L "
                                "(free-free flexural node stations)",
            },
        }


def build_crystal(variant: str = "ideal_n7",
                  wide_diameter_mm: float | None = None,
                  narrow_diameter_mm: float | None = None,
                  orientation=(0.0, 0.0, 0.0)) -> CanonicalCrystal:
    """The two canonical configurations (explicit, never confusable)."""
    if variant == "ideal_n7":
        length = IDEAL_LENGTH_MM
    elif variant == "nominal":
        length = NOMINAL_LENGTH_MM
    else:
        raise ValueError("variant must be 'ideal_n7' or 'nominal'")
    wd = wide_diameter_mm if wide_diameter_mm else length * _SPQ154_WIDE_RATIO
    nd = (narrow_diameter_mm if narrow_diameter_mm
          else length * _SPQ154_NARROW_RATIO)
    return CanonicalCrystal(variant, length, wd, nd,
                            orientation_euler_zxz_deg=tuple(orientation))


# --- geometry construction -------------------------------------------

def _ring(radius_mm: float, z_mm: float, facets: int) -> np.ndarray:
    ang = 2 * np.pi * np.arange(facets) / facets
    return np.stack([radius_mm * np.cos(ang), radius_mm * np.sin(ang),
                     np.full(facets, z_mm)], axis=1)


def _geo_text(c: CanonicalCrystal, clmax_mm: float) -> str:
    """Built-in-kernel .geo for the faceted body: two apexes, two hex
    rings, 6 cap triangles per cap, 6 planar shaft trapezoids."""
    n = c.facets
    rw = c.wide_diameter_mm / 2.0
    rn = c.narrow_diameter_mm / 2.0
    zf_ring = c.female_cap_height_mm
    zm_ring = c.length_mm - c.male_cap_height_mm
    pts = [(0.0, 0.0, 0.0), (0.0, 0.0, c.length_mm)]          # apexes 1,2
    pts += [tuple(p) for p in _ring(rw, zf_ring, n)]          # 3..3+n-1
    pts += [tuple(p) for p in _ring(rn, zm_ring, n)]          # 3+n..
    L = [f"Mesh.CharacteristicLengthMax = {clmax_mm};",
         "Mesh.CharacteristicLengthMin = 0.0;",
         "Mesh.Algorithm3D = 1;", "General.Verbosity = 2;"]
    for i, (x, y, z) in enumerate(pts, start=1):
        L.append(f"Point({i}) = {{{x:.12f}, {y:.12f}, {z:.12f}}};")
    fa, ma = 1, 2
    wr = [3 + i for i in range(n)]
    nr = [3 + n + i for i in range(n)]
    ln = {}
    lid = 0

    def line(a, b):
        nonlocal lid
        key = (a, b)
        if key in ln:
            return ln[key]
        if (b, a) in ln:
            return -ln[(b, a)]
        lid += 1
        L.append(f"Line({lid}) = {{{a}, {b}}};")
        ln[key] = lid
        return lid

    surf = 0
    loops = []

    def face(edges, group):
        nonlocal surf
        surf += 1
        L.append(f"Line Loop({surf + 1000}) = "
                 f"{{{', '.join(str(e) for e in edges)}}};")
        L.append(f"Plane Surface({surf}) = {{{surf + 1000}}};")
        loops.append(surf)
        groups.setdefault(group, []).append(surf)

    groups: dict = {}
    for i in range(n):
        j = (i + 1) % n
        # female cap triangle: apex -> wr[i] -> wr[j]
        face([line(fa, wr[i]), line(wr[i], wr[j]), line(wr[j], fa)],
             "cap_female")
        # male cap triangle: apex2 -> nr[j] -> nr[i]
        face([line(ma, nr[j]), line(nr[j], nr[i]), line(nr[i], ma)],
             "cap_male")
        # shaft trapezoid: wr[i]->wr[j]->nr[j]->nr[i]
        face([line(wr[i], wr[j]), line(wr[j], nr[j]),
              line(nr[j], nr[i]), line(nr[i], wr[i])], f"shaft_{i + 1}")
    L.append(f"Surface Loop(1) = {{{', '.join(str(s) for s in loops)}}};")
    L.append("Volume(1) = {1};")
    for gname, faces_ in groups.items():
        L.append(f'Physical Surface("{gname}") = '
                 f"{{{', '.join(str(s) for s in faces_)}}};")
    L.append('Physical Volume("crystal") = {1};')
    return "\n".join(L) + "\n"


def _gmsh_cmd() -> list[str]:
    """Command prefix for the gmsh CLI, run as a SEPARATE PROCESS
    (DV4-006 GPL boundary: file interchange only). The pip wheel ships
    a console script whose location varies: next to the interpreter in
    a venv (posix), or under Scripts/ for a plain Windows install
    (hosted CI). Plain scripts are invoked through this python so their
    `import gmsh` resolves."""
    import shutil as _shutil
    pydir = Path(sys.executable).parent
    for d in (pydir, pydir / "Scripts", pydir.parent / "Scripts",
              pydir / "bin"):
        exe = d / "gmsh.exe"
        if exe.exists():
            return [str(exe)]
        script = d / "gmsh"
        if script.exists():
            return [sys.executable, str(script)]
    found = _shutil.which("gmsh")
    if found:
        return [found]
    return ["gmsh"]     # PATH fallback (system install)


def mesh_crystal(c: CanonicalCrystal, clmax_mm: float,
                 workdir: str | Path, order: int = 1) -> dict:
    """Mesh via gmsh SUBPROCESS (DV4-006); returns nodes (m), tets,
    quality, manifest. Deterministic for fixed (geometry, clmax, gmsh
    version): element counts pinned in the manifest."""
    wd = Path(workdir)
    wd.mkdir(parents=True, exist_ok=True)
    geo = wd / f"{c.variant}_cl{clmax_mm:g}.geo"
    msh = geo.with_suffix(".msh")
    geo.write_text(_geo_text(c, clmax_mm), encoding="utf-8")
    cmd = _gmsh_cmd() + ["-3", str(geo), "-o", str(msh), "-format",
                         "msh2", "-order", str(order), "-v", "2"]
    run = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
    if run.returncode != 0 or not msh.exists():
        raise RuntimeError(f"gmsh failed: {run.stderr[-2000:]}")
    m = meshio.read(msh)
    tet_key = "tetra10" if order == 2 else "tetra"
    tets = None
    for cb in m.cells:
        if cb.type == tet_key:
            tets = cb.data
    if tets is None:
        raise RuntimeError("no tetrahedra in gmsh output")
    nodes_mm = m.points
    q = mesh_quality(nodes_mm, tets[:, :4])
    if q["n_inverted"] > 0:
        raise RuntimeError(f"{q['n_inverted']} inverted tets")
    manifest = {
        "geometry": c.record(),
        "clmax_mm": clmax_mm,
        "order": order,
        "gmsh_cmd": " ".join(cmd[1:]),
        "n_nodes": int(len(nodes_mm)),
        "n_tets": int(len(tets)),
        "quality": q,
        "mesh_volume_mm3": q["total_volume_mm3"],
        "analytic_volume_mm3": analytic_volume_mm3(c),
        "volume_rel_err": abs(q["total_volume_mm3"]
                              - analytic_volume_mm3(c))
        / analytic_volume_mm3(c),
        "nodes_sha256": _hash_arr(nodes_mm),
        "tets_sha256": _hash_arr(tets),
        "step_export_status": "NOT_GENERATED (built-in kernel; OCC path "
                              "IMPLEMENTED_DOCUMENTED_UNTESTED, DV4-013)",
    }
    (wd / f"{c.variant}_cl{clmax_mm:g}.manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8")
    return {"nodes_m": nodes_mm / 1000.0, "nodes_mm": nodes_mm,
            "tets": tets, "manifest": manifest, "msh_path": str(msh),
            "meshio": m}


def _hash_arr(a: np.ndarray) -> str:
    return hashlib.sha256(
        np.ascontiguousarray(np.round(np.asarray(a, dtype=float), 9))
        .tobytes()).hexdigest()


def mesh_quality(nodes_mm: np.ndarray, tets: np.ndarray) -> dict:
    """Per-tet signed volume (Jacobian sign), aspect (radius ratio),
    minimum dihedral angle, edge-length stats."""
    p = nodes_mm[tets]                       # (n,4,3)
    v0 = p[:, 1] - p[:, 0]
    v1 = p[:, 2] - p[:, 0]
    v2 = p[:, 3] - p[:, 0]
    vol = np.einsum("ij,ij->i", np.cross(v0, v1), v2) / 6.0
    edges = [p[:, a] - p[:, b] for a, b in
             ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))]
    elen = np.stack([np.linalg.norm(e, axis=1) for e in edges], axis=1)
    # inradius r = 3V/A_total; circumradius approx via longest edge bound
    areas = 0.5 * (
        np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 2] - p[:, 0]), axis=1)
        + np.linalg.norm(np.cross(p[:, 1] - p[:, 0], p[:, 3] - p[:, 0]), axis=1)
        + np.linalg.norm(np.cross(p[:, 2] - p[:, 0], p[:, 3] - p[:, 0]), axis=1)
        + np.linalg.norm(np.cross(p[:, 2] - p[:, 1], p[:, 3] - p[:, 1]), axis=1))
    r_in = 3.0 * np.abs(vol) / areas
    # normalized so a REGULAR tet scores exactly 1.0:
    # regular edge a has r_in = a/(2*sqrt(6))
    aspect = elen.max(axis=1) / (2.0 * np.sqrt(6.0) * r_in)
    # dihedral angles: between face normals sharing an edge
    faces = ((0, 1, 2), (0, 1, 3), (0, 2, 3), (1, 2, 3))
    normals = []
    for (a, b, cc) in faces:
        nrm = np.cross(p[:, b] - p[:, a], p[:, cc] - p[:, a])
        normals.append(nrm / np.linalg.norm(nrm, axis=1, keepdims=True))
    shared = (((0, 1)), ((0, 2)), ((0, 3)), ((1, 2)), ((1, 3)), ((2, 3)))
    dih = []
    for a, b in shared:
        cosang = np.clip(np.einsum("ij,ij->i", normals[a], normals[b]),
                         -1, 1)
        dih.append(np.degrees(np.pi - np.arccos(cosang)))
    dih = np.stack(dih, axis=1)
    return {
        "n_inverted": int(np.sum(vol <= 0)),
        "total_volume_mm3": float(np.sum(np.abs(vol))),
        "min_dihedral_deg": float(dih.min()),
        "max_aspect": float(aspect.max()),
        "mean_aspect": float(aspect.mean()),
        "edge_mm_min": float(elen.min()),
        "edge_mm_max": float(elen.max()),
    }


def analytic_volume_mm3(c: CanonicalCrystal) -> float:
    """Closed-form solid volume: two hex pyramids (A h / 3) + hex
    frustum h/3 (A1 + A2 + sqrt(A1 A2)); areas via the FROZEN
    polygon_area_mm2 (RGCS-M.1)."""
    a_w = polygon_area_mm2(c.wide_diameter_mm, c.facets)
    a_n = polygon_area_mm2(c.narrow_diameter_mm, c.facets)
    v_caps = (a_w * c.female_cap_height_mm + a_n * c.male_cap_height_mm) / 3.0
    v_shaft = c.shaft_length_mm / 3.0 * (a_w + a_n + math.sqrt(a_w * a_n))
    return v_caps + v_shaft
