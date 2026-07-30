"""R10.8.5A §8 — FinalLocalProjection: the corrected forward/inverse chain.

Forward:  decimal transmission number
          -> frozen F5|Q22|S3 packet parse (r12, reused verbatim)
          -> hierarchical terminal cell (addresses, never coordinates)
          -> GroundTimeFrame (epoch + ground reference + alignment)
          -> magnetically corrected gravity-shell boundaries
          -> outer-in shell address along a gravity-field line
          -> conventional latitude/longitude ONLY as the final output.

Inverse:  chosen conventional location -> the same chain reversed,
          reproducing the original packet or reporting explicit
          aliasing (the terminal cell and shell registers quantize; any
          point in the same cell/shell maps to the same word — that is
          aliasing, and it is reported, not hidden).

Hierarchical X/Y/Z indices are NEVER accepted as latitude, longitude,
Cartesian coordinates, kilometres or decimal altitude; the typed
:class:`HierarchicalAddress` and its refusals enforce that at the API.

The current run concerns the Federation/Terra codec only: wire radix
and packet layout are civilization-specific, the hierarchical spatial
semantics are canonical, the body projection is Terra-specific, and
lat/lon rendering is the last step — the four layers are kept separate.

``SOURCE_ORIGIN_VALIDATED: no``. The Stonehenge word is a hard
TRAINING equality: satisfying it is calibration, never validation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from r12 import icosapacket as pk
from r12 import icosarefine as rf

from cwatlas.claims import ClaimError
from cwatlas.r1082 import geocode_forward as gf
from cwatlas.r1085a import gravity_field_line as gfl
from cwatlas.r1085a import magnetic_shell as ms
from cwatlas.r1085a import outer_in_radial as oir
from cwatlas.r1085a.ground_time_frame import (
    GroundTimeFrame,
    minimal_rotation,
    rotation_angle_deg,
)
from cwatlas.r1085a.land_zero import LandZeroReference, land_zero
from cwatlas.r1085a.shell_profile import ShellProfile

# Training anchor (hard TRAINING equality — calibration input only).
TRAINING_WORD = 165876523
TRAINING_NAME = "STONEHENGE"
TRAINING_LAT_DEG = 51.1789
TRAINING_LON_DEG = -1.8262

#: Conventional geoid potential constant (IERS W0, m^2/s^2) and a mean
#: surface gravity — used only to construct the average-land-height
#: equipotential (geoid level lifted by the mean land elevation).
W0_GEOID_M2_S2 = 62636851.7
G_MEAN_M_S2 = 9.7976

GROUND_REFERENCE_ID = "TERRA_SURFACE_SYNC_V1"

CODEC_LAYERS = {
    "wire": "FEDERATION_TERRA_DECIMAL_TRANSMISSION_V1 (radix 10 display "
            "of a 30-bit word; civilization-specific)",
    "packet": "F5|Q22|S3 (r12.icosapacket, frozen, reused verbatim)",
    "spatial": "canonical hierarchical icosahedral address (civilization-"
               "independent claim, carried not validated)",
    "body": "Terra outer-in gravity-shell projection (this module)",
    "rendering": "conventional latitude/longitude, FINAL output only",
}


# --- typed hierarchical address (never coordinates) --------------------

@dataclass(frozen=True)
class HierarchicalAddress:
    """The parsed packet as an address. Indices are register values.

    Any attempt to read them as geographic or Cartesian coordinates is
    refused by the named methods below rather than failing silently.
    """

    word: int
    face: int
    path_levels: tuple[int, ...]
    shell: int
    octree_x: int
    octree_y: int
    octree_z: int

    def as_latitude(self) -> None:
        refuse_indices_as_coordinates("latitude")

    def as_longitude(self) -> None:
        refuse_indices_as_coordinates("longitude")

    def as_cartesian_km(self) -> None:
        refuse_indices_as_coordinates("Cartesian kilometres")

    def as_altitude(self) -> None:
        refuse_indices_as_coordinates("decimal altitude")


def refuse_indices_as_coordinates(what: str = "coordinates") -> None:
    raise ClaimError(
        f"refused: hierarchical X/Y/Z indices are addresses in a "
        f"recursive non-Cartesian hierarchy, not {what}. Conventional "
        f"coordinates exist only after the full body, shell, gravity, "
        f"magnetic, time and ground-reference transform "
        f"(FinalLocalProjection.forward).")


def parse_address(word: int) -> HierarchicalAddress:
    """Frozen parser, verbatim; plus the octree register split."""
    face, path, shell = pk.decode(word)
    o = format(word, "010o")
    spatial = o[:9]
    xb = "".join(format(int(d, 8), "03b")[0] for d in spatial)
    yb = "".join(format(int(d, 8), "03b")[1] for d in spatial)
    zb = "".join(format(int(d, 8), "03b")[2] for d in spatial)
    return HierarchicalAddress(
        word=word, face=face,
        path_levels=tuple(pk.path_levels(path)), shell=shell,
        octree_x=int(xb, 2), octree_y=int(yb, 2), octree_z=int(zb, 2))


# --- lateral geometry (r12 frozen mesh; sealed orientations) -----------

def _unit(lat_deg: float, lon_deg: float) -> np.ndarray:
    la, lo = math.radians(lat_deg), math.radians(lon_deg)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo), math.sin(la)])


def _latlon(p: np.ndarray) -> tuple[float, float]:
    p = np.asarray(p, dtype=float)
    p = p / np.linalg.norm(p)
    return (math.degrees(math.asin(float(np.clip(p[2], -1, 1)))),
            math.degrees(math.atan2(float(p[1]), float(p[0]))))


def cell_centroid_mesh(face: int, path_levels: tuple[int, ...]) -> np.ndarray:
    tri = rf.cell_triangle(face, path_levels)
    c = sum(np.asarray(v, dtype=float) for v in tri)
    return c / np.linalg.norm(c)


def cell_vertices_mesh(face: int,
                       path_levels: tuple[int, ...]) -> list[np.ndarray]:
    return [np.asarray(v, dtype=float)
            for v in rf.cell_triangle(face, path_levels)]


def sealed_contexts() -> dict[str, np.ndarray]:
    """The sealed R10.8.2 orientation family, reused exactly as frozen."""
    fp = gf.load_frozen_profile()
    base = gf._frozen_orientation(fp)
    by_fam = gf._frozen_orientation_by_family(fp)
    out = {"BASE": np.asarray(base, dtype=float)}
    for fam in gf._frozen_family_names(fp):
        out[fam] = np.asarray(by_fam.get(fam, base), dtype=float)
    return out


def _frame(rotation: np.ndarray, mode: str, epoch_year: float,
           undetermined: tuple[str, ...] = (),
           note: str = "") -> GroundTimeFrame:
    return GroundTimeFrame(
        epoch_year=float(epoch_year),
        ground_reference_id=GROUND_REFERENCE_ID,
        alignment_mode=mode,
        rotation=tuple(map(tuple, np.asarray(rotation, dtype=float))),
        rotational_phase_deg=0.0,
        south_up=True,
        undetermined_dof=undetermined,
        training_note=note)


def sealed_frame(context: str, epoch_year: float) -> GroundTimeFrame:
    ctx = sealed_contexts()
    if context not in ctx:
        raise ClaimError(f"unknown sealed context {context!r}; "
                         f"declared: {sorted(ctx)}")
    return _frame(ctx[context], "SEALED_R1082", epoch_year)


def training_alignment(epoch_year: float) -> tuple[GroundTimeFrame, dict]:
    """Solve the training-equality frame from the Stonehenge word ONLY.

    Pre-declared rule (fixed before any result is seen): among the
    sealed contexts, the one whose decoded training-cell direction
    needs the SMALLEST minimal rotation onto the training anchor is the
    calibration context; the minimal rotation is composed on top of its
    sealed orientation. The roll about the aligned axis is left
    UNDETERMINED and recorded. All contexts' angles are returned so the
    choice is auditable.
    """
    addr = parse_address(TRAINING_WORD)
    centroid = cell_centroid_mesh(addr.face, addr.path_levels)
    target = _unit(TRAINING_LAT_DEG, TRAINING_LON_DEG)
    angles = {}
    for name, orient in sealed_contexts().items():
        d = orient @ centroid
        angles[name] = rotation_angle_deg(
            minimal_rotation(d, target))
    chosen = min(sorted(angles), key=lambda k: angles[k])
    orient = sealed_contexts()[chosen]
    correction = minimal_rotation(orient @ centroid, target)
    frame = _frame(
        correction @ orient, "TRAINING_EQUALITY_R1085A", epoch_year,
        undetermined=("ROLL_ABOUT_TRAINING_ANCHOR_AXIS",),
        note=(f"minimal rotation {angles[chosen]:.4f} deg composed on "
              f"sealed context {chosen}; solved from the Stonehenge "
              f"training word only, then sealed."))
    receipt = {
        "rule": "smallest minimal-rotation sealed context, declared "
                "before results were seen",
        "context_angles_deg": {k: round(v, 4) for k, v in angles.items()},
        "chosen_context": chosen,
        "correction_angle_deg": round(angles[chosen], 4),
        "undetermined_dof": ["ROLL_ABOUT_TRAINING_ANCHOR_AXIS"],
    }
    return frame, receipt


# --- radial geometry ---------------------------------------------------

def land_zero_potential(ref: LandZeroReference) -> float:
    """W level of the average-land-height surface: geoid W0 lifted by
    the mean land elevation (potential decreases upward by ~g*h)."""
    return W0_GEOID_M2_S2 - G_MEAN_M_S2 * ref.mean_land_elevation_m


def land_zero_radius_m(direction: np.ndarray, ref: LandZeroReference,
                       epoch_year: float) -> float:
    """Radius along ``direction`` of the land-zero equipotential."""
    u = np.asarray(direction, dtype=float)
    u = u / np.linalg.norm(u)
    w_target = land_zero_potential(ref)

    def f(r: float) -> float:
        return gfl.potential_w(r * u, epoch_year) - w_target

    lo, hi = 6.30e6, 6.45e6
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        raise ClaimError("land-zero surface not bracketed near the "
                         "Earth surface; the potential model is being "
                         "used outside its regime")
    for _ in range(60):
        mid = 0.5 * (lo + hi)
        fm = f(mid)
        if flo * fm <= 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return 0.5 * (lo + hi)


# --- the forward projection --------------------------------------------

@dataclass(frozen=True)
class ProjectionResult:
    """One fully-declared forward projection of one word."""

    word: int
    frame_mode: str
    profile_id: str
    zeta_convention: str
    land_reference_id: str
    magnetic_member_id: str
    epoch_year: float
    shell_id: int
    zeta: float
    d_in_km: float
    outer_boundary_radius_km: float
    magnetic_deformation_m: float
    field_line_deviation_m: float
    point_ecef_m: tuple[float, float, float]
    latitude_deg: float
    longitude_deg: float
    height_above_land_zero_km: float
    radial_mode: str


def forward(word: int, frame: GroundTimeFrame, profile: ShellProfile,
            land_ref: LandZeroReference,
            magnetic: ms.MagneticShellCorrection,
            zeta_convention: str = "ZETA_FROM_OCTREE_Z_V1",
            field_line_step_m: float = 2000.0) -> ProjectionResult:
    """The corrected outer-in projection. Lat/lon appear only at the end.

    No argument of this function is per-vector: the same frame,
    profile, land reference and magnetic member apply to every word
    (``no free per-vector offsets`` is structural, not aspirational).
    """
    addr = parse_address(word)
    epoch = frame.epoch_year

    # lateral: hierarchical cell -> Earth direction (still an address
    # direction, not a coordinate, until the radial lane resolves)
    direction = frame.to_earth(
        cell_centroid_mesh(addr.face, addr.path_levels))

    # radial registers -> outer-in distances (pure stack arithmetic)
    zeta = oir.zeta_under(zeta_convention, addr.octree_z)
    radial = oir.decode(addr.shell, zeta, profile, epoch)

    # gravity + magnetic geometry: land-zero surface, outer operational
    # boundary (magnetically deformed), inward field line
    r_land0 = land_zero_radius_m(direction, land_ref, epoch)
    r_outer_nominal = r_land0 + radial.stack_height_km * 1000.0
    r_outer = ms.boundary_radius_m(direction, epoch, r_outer_nominal,
                                   magnetic)
    start = r_outer * direction / np.linalg.norm(direction)
    line = gfl.integrate_inward(start, epoch, radial.d_in_km * 1000.0,
                                step_m=field_line_step_m)
    point = np.asarray(line.end_m)
    lat, lon = _latlon(point)
    return ProjectionResult(
        word=word,
        frame_mode=frame.alignment_mode,
        profile_id=profile.profile_id,
        zeta_convention=zeta_convention,
        land_reference_id=land_ref.reference_id,
        magnetic_member_id=magnetic.member_id,
        epoch_year=epoch,
        shell_id=addr.shell,
        zeta=zeta,
        d_in_km=radial.d_in_km,
        outer_boundary_radius_km=r_outer / 1000.0,
        magnetic_deformation_m=r_outer - r_outer_nominal,
        field_line_deviation_m=line.lateral_deviation_m,
        point_ecef_m=tuple(map(float, point)),
        latitude_deg=lat,
        longitude_deg=lon,
        height_above_land_zero_km=radial.height_above_land_zero_km,
        radial_mode=radial.radial_mode)


def forward_with_operator_correction(
        word: int, active_shell: int, frame: GroundTimeFrame,
        profile: ShellProfile, land_ref: LandZeroReference,
        magnetic: ms.MagneticShellCorrection,
        zeta_convention: str = "ZETA_FROM_OCTREE_Z_V1",
        field_line_step_m: float = 2000.0) -> ProjectionResult:
    """Forward projection under a REGISTERED operator data correction.

    This is not a per-vector offset: the only corrections it will apply
    are the ones registered in :mod:`cwatlas.r1085a.orange_slice`
    (currently the middle orange-slice vector's shell, raw 3 ->
    active 7, ``OPERATOR_CORRECTION_TRANSCRIPTION_OR_PACKET_ERROR``).
    Any other (word, shell) pair is refused. The raw parse is left in
    provenance untouched.
    """
    from cwatlas.r1085a import orange_slice as osl
    registered = {(int(r.vector), r.active_shell)
                  for r in osl.rows() if r.corrected}
    if (word, active_shell) not in registered:
        raise ClaimError(
            f"refused: no registered operator correction maps word "
            f"{word} to shell {active_shell}. Corrections live in "
            f"cwatlas.r1085a.orange_slice with provenance; ad-hoc shell "
            f"overrides are per-vector offsets and are banned.")
    addr = parse_address(word)
    epoch = frame.epoch_year
    direction = frame.to_earth(
        cell_centroid_mesh(addr.face, addr.path_levels))
    zeta = oir.zeta_under(zeta_convention, addr.octree_z)
    radial = oir.decode(active_shell, zeta, profile, epoch)
    r_land0 = land_zero_radius_m(direction, land_ref, epoch)
    r_outer_nominal = r_land0 + radial.stack_height_km * 1000.0
    r_outer = ms.boundary_radius_m(direction, epoch, r_outer_nominal,
                                   magnetic)
    start = r_outer * direction / np.linalg.norm(direction)
    line = gfl.integrate_inward(start, epoch, radial.d_in_km * 1000.0,
                                step_m=field_line_step_m)
    point = np.asarray(line.end_m)
    lat, lon = _latlon(point)
    return ProjectionResult(
        word=word, frame_mode=frame.alignment_mode,
        profile_id=profile.profile_id, zeta_convention=zeta_convention,
        land_reference_id=land_ref.reference_id,
        magnetic_member_id=magnetic.member_id, epoch_year=epoch,
        shell_id=active_shell, zeta=zeta, d_in_km=radial.d_in_km,
        outer_boundary_radius_km=r_outer / 1000.0,
        magnetic_deformation_m=r_outer - r_outer_nominal,
        field_line_deviation_m=line.lateral_deviation_m,
        point_ecef_m=tuple(map(float, point)),
        latitude_deg=lat, longitude_deg=lon,
        height_above_land_zero_km=radial.height_above_land_zero_km,
        radial_mode=radial.radial_mode)


def surface_distance_km(lat1: float, lon1: float,
                        lat2: float, lon2: float) -> float:
    u, v = _unit(lat1, lon1), _unit(lat2, lon2)
    return 6371.0 * math.acos(float(np.clip(np.dot(u, v), -1.0, 1.0)))


def cell_contains(frame: GroundTimeFrame, addr: HierarchicalAddress,
                  lat_deg: float, lon_deg: float) -> bool:
    """Gnomonic containment of a surface point in the terminal cell."""
    p_mesh = frame.to_mesh(_unit(lat_deg, lon_deg))
    tri = cell_vertices_mesh(addr.face, addr.path_levels)
    m = np.column_stack(tri)
    try:
        w = np.linalg.solve(m, p_mesh)
    except np.linalg.LinAlgError:
        return False
    return bool(min(w) >= -1e-12)


# --- the inverse projection --------------------------------------------

def _classify_face_mesh(p_mesh: np.ndarray) -> int:
    best, best_w = None, -np.inf
    for f in range(20):
        tri = [np.asarray(v, dtype=float) for v in rf.face_triangle(f)]
        m = np.column_stack(tri)
        try:
            w = np.linalg.solve(m, p_mesh)
        except np.linalg.LinAlgError:
            continue
        if min(w) > best_w:
            best, best_w = f, float(min(w))
    if best is None:
        raise ClaimError("point classifies to no r12 face")
    return best


def _descend(face: int, p_mesh: np.ndarray,
             levels: int = 11) -> tuple[int, ...]:
    tri = [np.asarray(v, dtype=float) for v in rf.face_triangle(face)]
    path = []
    for _ in range(levels):
        kids = rf._subdivide(tri)
        best, best_w = 0, -np.inf
        for i, kid in enumerate(kids):
            m = np.column_stack([np.asarray(v, dtype=float) for v in kid])
            try:
                w = np.linalg.solve(m, p_mesh)
            except np.linalg.LinAlgError:
                continue
            if min(w) > best_w:
                best, best_w = i, float(min(w))
        path.append(best)
        tri = kids[best]
    return tuple(path)


@dataclass(frozen=True)
class InverseResult:
    """Location -> word, with aliasing made explicit."""

    latitude_deg: float
    longitude_deg: float
    height_above_land_zero_km: float
    face: int
    path_levels: tuple[int, ...]
    shell_id: int
    zeta: float
    word: int
    octal: str
    decimal: str
    aliasing_note: str


def inverse(lat_deg: float, lon_deg: float,
            height_above_land_zero_km: float,
            frame: GroundTimeFrame, profile: ShellProfile) -> InverseResult:
    """Chosen conventional location -> hierarchical address -> word.

    The shell register comes from the height above land-zero under the
    declared profile; zeta is the in-shell fraction. Aliasing is
    intrinsic: the word stores face+path+shell only, so every point of
    the terminal cell and shell band yields the same word.
    """
    epoch = frame.epoch_year
    p_mesh = frame.to_mesh(_unit(lat_deg, lon_deg))
    face = _classify_face_mesh(p_mesh)
    path = _descend(face, p_mesh)

    h = float(height_above_land_zero_km)
    shell_id, zeta = None, None
    for s in profile.bands:
        lo = profile.inner_stack_below_km(s.shell_id, epoch)
        hi = lo + s.thickness_km(epoch)
        if lo <= h < hi or (s.shell_id == 8 and abs(h - hi) < 1e-9):
            shell_id = s.shell_id
            zeta = (h - lo) / (hi - lo)
            break
    if shell_id is None:
        raise ClaimError(
            f"height {h} km above land-zero is outside the operational "
            f"stack (0..{profile.stack_height_km(epoch)} km under "
            f"{profile.profile_id}); shells 0..2 below the land-zero "
            f"surface are not addressable by this codec.")
    if shell_id == 8:
        raise ClaimError(
            "refused: the S3 register is 3 bits (shells 0..7); shell 8 "
            "is not encodable. The 8 <-> 0 closure is stored as source "
            "ontology and never auto-applied (cwatlas.shells invariant "
            "8); opting in would be a declared step, not a silent one.")
    word = pk.encode(face, path, shell_id)
    return InverseResult(
        latitude_deg=lat_deg, longitude_deg=lon_deg,
        height_above_land_zero_km=h,
        face=face, path_levels=path, shell_id=shell_id,
        zeta=float(zeta), word=word,
        octal=format(word, "010o"), decimal=str(word),
        aliasing_note=(
            "the word stores face, 11 path levels and a 3-bit shell "
            "register only: every point of the same terminal cell and "
            "shell band encodes to this same word (explicit aliasing; "
            "the in-shell zeta and octree split are NOT independently "
            "settable by the encoder)."))
