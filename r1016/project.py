"""R10.16 — no-warp discrete projection search.

The projection chain is deliberately rigid:

    30-bit word -> frozen F5|Q22|S3 parse -> (face, path, shell)
                -> DISCRETE relabel (face offset, child order, endian)
                -> icosahedral cell centroid on the FROZEN mesh
                -> rigid frame rotation (+ optional discrete flips)
                -> lat/lon

Nothing here warps the mesh, fits a per-vector offset, or applies a
nonlinear correction. Every degree of freedom is a discrete choice
from a declared finite set, and the same choice applies to EVERY wire
in a model -- that is what makes the strict anchor gate meaningful.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from cwatlas.r1085a import final_projection as fp
from r12 import icosapacket as pk

EARTH_R_KM = 6371.0088

#: The four strict calibration anchors, keyed by their RESOLVED
#: SURFACE WORD -- not by the raw transport wire. Where a record
#: carries a canonical packet/candidate, that is the word which gets
#: projected; see r1016.surface_word. Montreal is the case that forced
#: this: raw 165879243 (payload octal 2174224) sits one symbol from
#: the old Cotswolds candidate and pulls Montreal into the British
#: cluster, while its canonical word 168500683 gives 3174224.
def _resolved_strict_anchors() -> dict:
    from r1016.surface_word import resolved_anchors
    return {str(v["surface_word"]): (name, v["lat"], v["lon"])
            for name, v in resolved_anchors().items()}


STRICT_ANCHORS = _resolved_strict_anchors()

#: The raw-wire keying, retained ONLY for explicitly labelled
#: RAW_TRANSPORT_WIRE_DIAGNOSTIC runs.
#: MONTREAL FULLY REMOVED (operator instruction, R10.18): BOTH the
#: raw/direct 165879243 and the bridge 168500683 are out of every
#: anchor set and every diagnostic. Do not reintroduce either.
RAW_TRANSPORT_ANCHORS = {
    "165876523": ("Stonehenge", 51.1789, -1.8262),
    "168930443": ("Toronto", 43.6532, -79.3832),
    "167849523": ("Erie", 42.1292, -80.0851),
}
STRICT_GATE_RMS_KM = 25.0


class ProjectError(ValueError):
    pass


@dataclass(frozen=True)
class RootVariant:
    """One discrete orientation/decode variant. No continuous knobs."""
    face_offset: int = 0          # 0..19
    child_order: str = "forward"  # forward | reversed
    bit_endian: str = "msb"       # msb | lsb (30-bit reversal)
    handedness: str = "right"     # right | mirrored (lon -> -lon)
    pole: str = "south_up"        # south_up | north_up
    context: str = "TRAINED"      # frame context id

    @property
    def id(self) -> str:
        return (f"F{self.face_offset:02d}/{self.child_order[:3]}/"
                f"{self.bit_endian}/{self.handedness[:3]}/"
                f"{self.pole[:5]}/{self.context}")


def reverse_bits30(word: int) -> int:
    return int(format(word & ((1 << 30) - 1), "030b")[::-1], 2)


def enumerate_variants(contexts=("TRAINED",)) -> list:
    out = []
    for ctx in contexts:
        for fo in range(20):
            for co in ("forward", "reversed"):
                for be in ("msb", "lsb"):
                    for hd in ("right", "mirrored"):
                        for po in ("south_up", "north_up"):
                            out.append(RootVariant(fo, co, be, hd, po,
                                                   ctx))
    return out


def _latlon_from_unit(p, variant: RootVariant) -> tuple[float, float]:
    lat, lon = fp._latlon(p)
    if variant.pole == "north_up":
        lat = -lat
        lon = lon + 180.0
    if variant.handedness == "mirrored":
        lon = -lon
    lon = ((lon + 180.0) % 360.0) - 180.0
    return lat, lon


def project(word: int, variant: RootVariant,
            rotation: np.ndarray) -> dict:
    """One word through one discrete variant. Rigid throughout."""
    w = reverse_bits30(word) if variant.bit_endian == "lsb" else word
    try:
        rec = pk.decode_record(w)
    except Exception as ex:
        raise ProjectError(f"frozen parser refused {w}: {ex}") from ex
    face = (int(rec["face"]) + variant.face_offset) % 20
    path = tuple(rec["path_levels"])
    if variant.child_order == "reversed":
        path = tuple(reversed(path))
    p_mesh = fp.cell_centroid_mesh(face, path)
    p_ground = np.asarray(rotation, float) @ np.asarray(p_mesh, float)
    lat, lon = _latlon_from_unit(p_ground, variant)
    return {"word": w, "f5": int(rec["face"]), "source_face": face,
            "q22_path": list(path), "s3": int(rec["shell"]),
            "octal": rec.get("octal"), "bits": rec.get("bits"),
            "lat": lat, "lon": lon}


def great_circle_km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    a = (math.sin((p2 - p1) / 2) ** 2
         + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2)
    return 2 * EARTH_R_KM * math.asin(min(1.0, math.sqrt(a)))


def anchor_rms(variant: RootVariant, rotation, view_words: dict
               ) -> dict:
    """Strict-anchor RMS for one (variant, view) model."""
    errs, rows = [], []
    for wire, (place, lat, lon) in STRICT_ANCHORS.items():
        word = view_words.get(wire)
        if word is None:
            rows.append({"wire": wire, "place": place,
                         "error_km": None,
                         "status": "NO_WORD_UNDER_THIS_VIEW"})
            continue
        try:
            r = project(word, variant, rotation)
        except ProjectError as ex:
            rows.append({"wire": wire, "place": place,
                         "error_km": None, "status": str(ex)[:80]})
            continue
        d = great_circle_km(r["lat"], r["lon"], lat, lon)
        errs.append(d)
        rows.append({"wire": wire, "place": place,
                     "lat": r["lat"], "lon": r["lon"],
                     "error_km": d, "status": "PROJECTED"})
    if not errs:
        return {"rms_km": None, "covered": 0, "rows": rows,
                "passes_gate": False}
    rms = math.sqrt(sum(e * e for e in errs) / len(errs))
    return {"rms_km": rms, "covered": len(errs), "rows": rows,
            "max_km": max(errs), "min_km": min(errs),
            "passes_gate": bool(rms <= STRICT_GATE_RMS_KM
                                and len(errs) == len(STRICT_ANCHORS))}
