"""R10.16b — profile-specific semantic layering (operator correction).

The first search forced every payload into the FROZEN F5|Q22|S3 split:
5 face bits, 22 path bits (11 levels x 2), 3 shell bits. That is one
semantic profile among many, and treating it as the only one was an
unrecorded assumption.

Under the corrected hypothesis the octal payload IS the recursive
address, and a profile-specific semantic layer decides how much of the
bit string becomes face, refinement, shell, epoch, body or route
state. So the split itself is enumerated:

    [ offset ][ face_bits ][ n_levels x level_bits ][ trailing state ]

Everything stays rigid and discrete: no warp, no fitted operator, no
per-vector freedom. The same profile applies to every wire in a model.

THE FAST EXACT FILTER. Pairwise angular separations between decoded
directions are invariant under every rotation. If a profile's decoded
angle-set does not match the claimed angle-set, then NO rotation --
discrete or continuous -- can align it, and the profile is rejected
without testing a single orientation. That turns an otherwise
intractable search into a cheap exact one.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np

from cwatlas.r1085a import final_projection as fp
from r12 import icosarefine as rf
from r1016.project import STRICT_ANCHORS
from r1016.salvage import _unit, optimal_rotation

#: The frozen mesh refines each triangle into 4 children, so a level
#: index must be 2 bits. Deeper octal (3-bit) reads are recorded as
#: unsupported by this mesh rather than silently folded mod 4.
LEVEL_BITS = 2
MAX_LEVELS = 12
MIN_LEVELS = 3


@dataclass(frozen=True)
class SemanticProfile:
    offset: int         # leading bits skipped (epoch/body/route)
    face_bits: int      # bits that select the source face
    n_levels: int       # refinement levels consumed

    @property
    def id(self) -> str:
        return (f"O{self.offset:02d}/FB{self.face_bits}/"
                f"L{self.n_levels:02d}")

    @property
    def bits_needed(self) -> int:
        return self.offset + self.face_bits + self.n_levels * LEVEL_BITS

    def decode(self, value: int, total_bits: int):
        """(face, path_levels) or None if the value cannot supply them."""
        if total_bits < self.bits_needed:
            return None
        b = format(value, f"0{total_bits}b")
        i = self.offset
        face = int(b[i:i + self.face_bits], 2) % 20
        i += self.face_bits
        levels = []
        for _ in range(self.n_levels):
            levels.append(int(b[i:i + LEVEL_BITS], 2))
            i += LEVEL_BITS
        return face, tuple(levels)


def all_profiles(max_offset: int = 24, max_skip: int = 6) -> list:
    """Both families: binary-split and octal-digit."""
    return enumerate_profiles(max_offset) + enumerate_octal_profiles(max_skip)


def enumerate_profiles(max_offset: int = 16) -> list:
    out = []
    for off in range(max_offset + 1):
        for fb in (4, 5, 6):
            for nl in range(MIN_LEVELS, MAX_LEVELS + 1):
                out.append(SemanticProfile(off, fb, nl))
    return out



# ------------------------------------------------------------------
# Octal-digit profile family: the reading closest to "the octal
# payload IS the recursive address". Each OCTAL DIGIT is one level of
# the recursive path. The frozen mesh refines 4-ways, so an 8-valued
# digit is folded by a DECLARED rule (mod 4, or high two bits); both
# rules are enumerated rather than one being chosen silently.
# ------------------------------------------------------------------

FOLD_RULES = {"mod4": lambda d: d % 4, "hi2": lambda d: d >> 1}


@dataclass(frozen=True)
class OctalDigitProfile:
    face_digits: int      # leading octal digits that select the face
    n_levels: int         # octal digits consumed as path levels
    fold: str             # mod4 | hi2
    skip: int = 0         # leading digits treated as epoch/body/route

    @property
    def id(self) -> str:
        return (f"OCT/S{self.skip}/FD{self.face_digits}/"
                f"L{self.n_levels:02d}/{self.fold}")

    def decode(self, value: int, _total_bits=None):
        digits = [int(c) for c in format(value, "o")]
        need = self.skip + self.face_digits + self.n_levels
        if len(digits) < need:
            return None
        i = self.skip
        face_val = 0
        for d in digits[i:i + self.face_digits]:
            face_val = face_val * 8 + d
        i += self.face_digits
        face = face_val % 20
        f = FOLD_RULES[self.fold]
        levels = tuple(f(d) for d in digits[i:i + self.n_levels])
        return face, levels


def enumerate_octal_profiles(max_skip: int = 6) -> list:
    out = []
    for skip in range(max_skip + 1):
        for fd in (1, 2):
            for nl in range(MIN_LEVELS, MAX_LEVELS + 1):
                for fold in FOLD_RULES:
                    out.append(OctalDigitProfile(fd, nl, fold, skip))
    return out


def _pairwise(dirs) -> list:
    return [math.degrees(math.acos(min(1.0, max(-1.0, float(
        np.dot(dirs[i], dirs[j]))))))
        for i, j in itertools.combinations(range(len(dirs)), 2)]


def claimed_directions():
    return [_unit(lat, lon) for _w, (_p, lat, lon)
            in STRICT_ANCHORS.items()]


def profile_shape_error(profile: SemanticProfile, words: dict) -> dict:
    """Rotation-invariant shape mismatch for one profile.

    Returns the worst pairwise-angle discrepancy. This is a NECESSARY
    condition: a profile that fails it cannot be rescued by any
    rotation whatsoever.
    """
    dirs, wires = [], []
    for wire in STRICT_ANCHORS:
        w = words.get(wire)
        if w is None:
            return {"profile": profile.id, "status": "NO_WORD"}
        dec = profile.decode(w, max(30, int(w).bit_length()))
        if dec is None:
            return {"profile": profile.id, "status": "TOO_FEW_BITS"}
        face, levels = dec
        try:
            dirs.append(np.asarray(
                fp.cell_centroid_mesh(face, levels), float))
        except Exception as ex:
            return {"profile": profile.id, "status": f"MESH:{ex}"[:40]}
        wires.append(wire)
    if len(dirs) < len(STRICT_ANCHORS):
        return {"profile": profile.id, "status": "INCOMPLETE"}
    dec_ang = _pairwise(dirs)
    cl_ang = _pairwise(claimed_directions())
    diffs = [abs(a - b) for a, b in zip(dec_ang, cl_ang)]
    return {"profile": profile.id, "status": "SHAPED",
            "profile_obj": profile,
            "decoded_angles_deg": dec_ang,
            "claimed_angles_deg": cl_ang,
            "max_angle_error_deg": max(diffs),
            "mean_angle_error_deg": sum(diffs) / len(diffs),
            "dirs": dirs}


def best_rotation_rms_km(shape: dict) -> float:
    """Given a shape-compatible profile, the optimal rigid rotation."""
    from r1016.project import great_circle_km
    dirs = shape["dirs"]
    targ = claimed_directions()
    R = optimal_rotation(dirs, targ)
    errs = []
    for d, (_w, (_p, lat, lon)) in zip(dirs, STRICT_ANCHORS.items()):
        la, lo = fp._latlon(R @ d)
        errs.append(great_circle_km(la, lo, lat, lon))
    return math.sqrt(sum(e * e for e in errs) / len(errs))


def search(words_by_view: dict, shape_tolerance_deg: float = 8.0,
           max_offset: int = 16) -> dict:
    """Exhaust semantic profiles under the exact rotation-invariant
    filter, then rotation-fit only the survivors."""
    profiles = all_profiles(max_offset)
    shaped, viable = [], []
    for view, words in words_by_view.items():
        for p in profiles:
            s = profile_shape_error(p, words)
            if s.get("status") != "SHAPED":
                continue
            s["view"] = view
            shaped.append({k: v for k, v in s.items()
                           if k not in ("dirs", "profile_obj")})
            if s["max_angle_error_deg"] <= shape_tolerance_deg:
                s["rotation_rms_km"] = best_rotation_rms_km(s)
                viable.append({k: v for k, v in s.items()
                               if k != "dirs"})
    shaped.sort(key=lambda d: d["max_angle_error_deg"])
    viable.sort(key=lambda d: d["rotation_rms_km"])
    return {
        "schema": "rgcs.r1016b.semantic-profile-search.v1",
        "profiles_per_view": len(profiles),
        "profiles_evaluated": len(shaped),
        "shape_tolerance_deg": shape_tolerance_deg,
        "shape_compatible": len(viable),
        "best_shape_error_deg": (shaped[0]["max_angle_error_deg"]
                                 if shaped else None),
        "best_shape": shaped[0] if shaped else None,
        "best_rotation_rms_km": (viable[0]["rotation_rms_km"]
                                 if viable else None),
        "survivors_25km": [v for v in viable
                           if v["rotation_rms_km"] <= 25.0],
        "top_shapes": shaped[:15],
        "top_viable": viable[:15],
    }
