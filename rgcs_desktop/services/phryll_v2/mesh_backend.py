"""Mesh backend: tessellates the generated cone shell and writes
binary STL and minimal 3MF directly — no external CAD dependency.

The mesh is built from the generated inner/outer profiles (crystal
envelope + clearance + wall), never from a reference mesh.
"""
from __future__ import annotations

import math
import struct
import zipfile
from pathlib import Path

import numpy as np

from rgcs_desktop.services.phryll_v2.cone_generator import ConeDesign


def tessellate_cone_shell(design: ConeDesign,
                          segments: int = 96) -> np.ndarray:
    """Watertight shell mesh as an (n_tri, 3, 3) float array.

    Surfaces: outer wall, inner wall, base annulus (z=0), top annulus
    (z=height). Vertices ring-by-ring along the generated profiles.
    """
    if segments < 12:
        raise ValueError("need at least 12 angular segments")
    inner = design.inner_profile
    outer = design.outer_profile
    angles = np.linspace(0.0, 2.0 * math.pi, segments, endpoint=False)
    cos, sin = np.cos(angles), np.sin(angles)

    def ring(r: float, z: float) -> np.ndarray:
        return np.stack([r * cos, r * sin, np.full(segments, z)], axis=1)

    triangles: list[np.ndarray] = []

    def lateral(profile, flip: bool) -> None:
        for a, b in zip(profile[:-1], profile[1:]):
            lo, hi = ring(a.r_mm, a.z_mm), ring(b.r_mm, b.z_mm)
            for i in range(segments):
                j = (i + 1) % segments
                t1 = np.stack([lo[i], lo[j], hi[i]])
                t2 = np.stack([lo[j], hi[j], hi[i]])
                if flip:  # inner wall faces inward
                    t1, t2 = t1[::-1], t2[::-1]
                triangles.append(t1)
                triangles.append(t2)

    def annulus(z: float, r_in: float, r_out: float, flip: bool) -> None:
        ri, ro = ring(r_in, z), ring(r_out, z)
        for i in range(segments):
            j = (i + 1) % segments
            t1 = np.stack([ri[i], ro[i], ro[j]])
            t2 = np.stack([ri[i], ro[j], ri[j]])
            if flip:
                t1, t2 = t1[::-1], t2[::-1]
            triangles.append(t1)
            triangles.append(t2)

    lateral(outer, flip=False)
    lateral(inner, flip=True)
    annulus(inner[0].z_mm, inner[0].r_mm, outer[0].r_mm, flip=True)
    annulus(inner[-1].z_mm, inner[-1].r_mm, outer[-1].r_mm, flip=False)
    return np.asarray(triangles, dtype=np.float64)


def write_binary_stl(triangles: np.ndarray, out_path: str | Path,
                     name: bytes = b"RGCS phryll v2 generated") -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    n = len(triangles)
    with out_path.open("wb") as fh:
        fh.write(name.ljust(80, b"\0")[:80])
        fh.write(struct.pack("<I", n))
        for tri in triangles:
            edge1 = tri[1] - tri[0]
            edge2 = tri[2] - tri[0]
            normal = np.cross(edge1, edge2)
            norm = np.linalg.norm(normal)
            normal = normal / norm if norm > 0 else np.zeros(3)
            fh.write(struct.pack("<3f", *normal))
            for vertex in tri:
                fh.write(struct.pack("<3f", *vertex))
            fh.write(b"\0\0")
    return out_path


def write_3mf(triangles: np.ndarray, out_path: str | Path,
              title: str = "RGCS phryll v2 generated") -> Path:
    """Minimal single-object 3MF (deduplicated vertices)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    flat = np.round(triangles.reshape(-1, 3), 6)
    vertices, index = np.unique(flat, axis=0, return_inverse=True)
    faces = index.reshape(-1, 3)

    vert_xml = "".join(
        f'<vertex x="{v[0]}" y="{v[1]}" z="{v[2]}"/>' for v in vertices)
    face_xml = "".join(
        f'<triangle v1="{f[0]}" v2="{f[1]}" v3="{f[2]}"/>' for f in faces)
    model = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">'
        f'<metadata name="Title">{title}</metadata>'
        '<resources><object id="1" type="model"><mesh>'
        f'<vertices>{vert_xml}</vertices>'
        f'<triangles>{face_xml}</triangles>'
        '</mesh></object></resources>'
        '<build><item objectid="1"/></build></model>')
    content_types = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/'
        'content-types">'
        '<Default Extension="rels" ContentType="application/vnd.'
        'openxmlformats-package.relationships+xml"/>'
        '<Default Extension="model" ContentType="application/vnd.ms-'
        'package.3dmanufacturing-3dmodel+xml"/></Types>')
    rels = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<Relationships xmlns="http://schemas.openxmlformats.org/'
        'package/2006/relationships">'
        '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
        'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/'
        '3dmodel"/></Relationships>')
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("[Content_Types].xml", content_types)
        zf.writestr("_rels/.rels", rels)
        zf.writestr("3D/3dmodel.model", model)
    return out_path


def mesh_stats(triangles: np.ndarray) -> dict:
    flat = triangles.reshape(-1, 3)
    return {
        "n_triangles": int(len(triangles)),
        "bbox_min_mm": [float(x) for x in flat.min(axis=0)],
        "bbox_max_mm": [float(x) for x in flat.max(axis=0)],
        "height_mm": float(flat[:, 2].max() - flat[:, 2].min()),
        "max_diameter_mm": float(
            2.0 * np.max(np.hypot(flat[:, 0], flat[:, 1]))),
    }


def tessellate_coil_sleeve(design: ConeDesign, coil: dict,
                           segments: int = 72,
                           band_z_step_mm: float = 0.1) -> np.ndarray:
    """Cone shell with CONTINUOUS helical wire slots carved into the
    outer surface (both crossed coils), as displaced-surface mesh.

    In unrolled surface coordinates the phased helix
    theta(z) = s*2*pi*z/p + phi is a family of lines spaced one pitch
    apart in z; the outer-surface radius is pulled inward by the
    circular wire cross-section wherever a vertex sits within
    wire_d/2 (in z) of a groove centerline. Fine axial sampling inside
    the winding band resolves the slot walls.
    """
    inner = design.inner_profile
    outer = design.outer_profile
    height = design.generated_dimensions["height_mm"]
    paths = coil["paths"]
    spacing = coil["spacing"]
    wire_d = float(coil["wire"]["wire_diameter_mm"])
    pitch = float(spacing["groove_pitch_mm"])
    depth = float(spacing["groove_depth_mm"])
    band_lo = float(paths["band_bottom_mm"])
    band_hi = float(paths["band_top_mm"])

    def outer_r(z: float) -> float:
        zs = [p.z_mm for p in outer]
        rs = [p.r_mm for p in outer]
        return float(np.interp(z, zs, rs))

    def inner_r(z: float) -> float:
        zs = [p.z_mm for p in inner]
        rs = [p.r_mm for p in inner]
        return float(np.interp(z, zs, rs))

    # axial stations: coarse outside the band, fine inside it
    coarse = np.arange(0.0, height + 1e-9, 2.0)
    fine = np.arange(band_lo - wire_d, band_hi + wire_d, band_z_step_mm)
    z_list = np.unique(np.clip(np.concatenate(
        [coarse, fine, [height]]), 0.0, height))

    angles = np.linspace(0.0, 2.0 * math.pi, segments, endpoint=False)
    helices = [(1.0, float(paths["copper"]["phase_rad_at_z0"])),
               (-1.0, float(paths["silver"]["phase_rad_at_z0"]))]

    def groove_depth_at(theta: float, z: float) -> float:
        if not band_lo <= z <= band_hi:
            return 0.0
        best = 0.0
        for s, phi in helices:
            # groove centerlines pass angle theta at
            # z_line = s*(theta - phi)*p/(2*pi) + k*p; the axial
            # distance from this vertex to the nearest line:
            rel = (z - s * (theta - phi) * pitch
                   / (2 * math.pi)) % pitch
            dz = min(rel, pitch - rel)
            if dz < wire_d / 2:
                frac = math.sqrt(max(0.0, 1.0 - (2 * dz / wire_d) ** 2))
                best = max(best, depth * frac)
        return best

    # outer surface rings with groove displacement
    outer_rings = []
    for z in z_list:
        base_r = outer_r(z)
        ring = np.empty((segments, 3))
        for i, theta in enumerate(angles):
            r = base_r - groove_depth_at(theta, z)
            ring[i] = (r * math.cos(theta), r * math.sin(theta), z)
        outer_rings.append(ring)
    # inner surface: smooth, coarse stations only
    inner_rings = []
    for z in coarse if coarse[-1] == height else np.append(coarse, height):
        r = inner_r(z)
        ring = np.stack([r * np.cos(angles), r * np.sin(angles),
                         np.full(segments, z)], axis=1)
        inner_rings.append(ring)

    triangles: list[np.ndarray] = []

    def stitch(rings, flip: bool) -> None:
        for lo, hi in zip(rings[:-1], rings[1:]):
            for i in range(segments):
                j = (i + 1) % segments
                t1 = np.stack([lo[i], lo[j], hi[i]])
                t2 = np.stack([lo[j], hi[j], hi[i]])
                if flip:
                    t1, t2 = t1[::-1], t2[::-1]
                triangles.append(t1)
                triangles.append(t2)

    stitch(outer_rings, flip=False)
    stitch(inner_rings, flip=True)

    def annulus(z, r_in, r_out, flip):
        ri = np.stack([r_in * np.cos(angles), r_in * np.sin(angles),
                       np.full(segments, z)], axis=1)
        ro = np.stack([r_out * np.cos(angles), r_out * np.sin(angles),
                       np.full(segments, z)], axis=1)
        for i in range(segments):
            j = (i + 1) % segments
            t1 = np.stack([ri[i], ro[i], ro[j]])
            t2 = np.stack([ri[i], ro[j], ri[j]])
            if flip:
                t1, t2 = t1[::-1], t2[::-1]
            triangles.append(t1)
            triangles.append(t2)

    annulus(0.0, inner_r(0.0), outer_r(0.0), flip=True)
    annulus(height, inner_r(height), outer_r(height), flip=False)
    return np.asarray(triangles, dtype=np.float64)
