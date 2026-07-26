"""R10.8.5 corrective run — octal packet recovery (F5 | Q22 | S3).

Locked correction: the raw decimal integer converts to a fixed-width
binary packet FIRST; the spatial hierarchy is radix eight (8**12 = 2**36;
the nine-digit family uses the established 30-bit R12 grammar
F5 | Q22 | S3). The R10.8.4 decimal-triplet reading is REJECTED and kept
only as a receipted rejected candidate.

Reuses the existing R12 implementations verbatim (r12.icosapacket,
r12.icosarefine) — no new refinement operator is invented. The five R12
decode prerequisites are satisfied by the R10.8.2 sealed frame
(EARTH_ROOT_D_V1 + CALFREEZE per-family orientations); placements below
are labelled candidates under that freeze, never measurements.

Run:  python tools/r1085_octal_packet_recovery.py
"""

from __future__ import annotations

import itertools
import json
import math
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from r12 import icosapacket as pk                                  # noqa
from r12 import icosarefine as rf                                  # noqa
from cwatlas.icosahedron import classify_point                     # noqa
from cwatlas.r1082 import geocode_forward as gf                    # noqa
from cwatlas.r1082 import root_certificate as rc                   # noqa
from cwatlas.r1084 import cw_face_codebook as cb                   # noqa

OUT = ROOT / "docs" / "proofs" / "r1085-octal-packet-recovery"
R_KM = 6371.0
SH_LAT, SH_LON = 51.1789, -1.8262

NINE = ["165876523", "165877623", "165892743", "165892763", "165892783",
        "167829573"]
LONGER = ["1678523973", "1678295343", "16752349783", "16782953437"]

EXPECT_SH = {
    "bits": "001001111000110001001100101011",
    "octal": "1170611453",
    "face": 4, "shell": 3,
    "path_levels": (3, 3, 0, 1, 2, 0, 2, 1, 2, 1, 1),
    "octree_x": ("001010011", 83),
    "octree_y": ("001010000", 80),
    "octree_z": ("111001101", 461),
}


def octree_bits(word: int) -> dict:
    """Interpretation A: nine spatial octal digits -> per-axis bit paths."""
    o = format(word, "010o")
    spatial, shell = o[:9], int(o[9], 8)
    xb = "".join(format(int(d, 8), "03b")[0] for d in spatial)
    yb = "".join(format(int(d, 8), "03b")[1] for d in spatial)
    zb = "".join(format(int(d, 8), "03b")[2] for d in spatial)
    return {"spatial_octal": spatial, "shell_octal": shell,
            "X_bits": xb, "Y_bits": yb, "Z_bits": zb,
            "X": int(xb, 2), "Y": int(yb, 2), "Z": int(zb, 2),
            "note": "hierarchical octree bit paths, not completed global "
                    "Cartesian coordinates"}


def _unit(lat, lon):
    la, lo = math.radians(lat), math.radians(lon)
    return np.array([math.cos(la) * math.cos(lo),
                     math.cos(la) * math.sin(lo), math.sin(la)])


def _latlon(p):
    return (math.degrees(math.asin(max(-1, min(1, float(p[2]))))),
            math.degrees(math.atan2(float(p[1]), float(p[0]))))


def _gc(u, v):
    return R_KM * math.acos(max(-1.0, min(1.0, float(u @ v))))


def _in_tri(p, tri):
    m = np.column_stack(tri)
    try:
        w = np.linalg.solve(m, p)
    except np.linalg.LinAlgError:
        return False
    return bool(min(w) >= -1e-12)


def containment(word: int) -> dict:
    """Cell containment of Stonehenge under the sealed frame, for every
    finite context: 5 codebooks (source-face -> mesh-face) x sealed family
    orientations. R12's frozen face numbering and child order are used
    as-is (its own guard forbids re-orienting the mesh)."""
    face_src, path, shell = pk.decode(word)
    fp = gf.load_frozen_profile()
    base = gf._frozen_orientation(fp)
    by_fam = gf._frozen_orientation_by_family(fp)
    # r12 froze its own icosahedron (r11.earthface); same geometry as the
    # cwatlas mesh but a different face numbering. Bridge explicitly.
    from cwatlas.icosahedron import build_icosahedron
    cw = build_icosahedron()

    def _key(tri):
        return tuple(sorted(tuple(np.round(v, 9)) for v in tri))
    cwk = {_key([cw.vertices[i] for i in cw.faces[f]]): f
           for f in range(20)}
    r12_to_cw = [cwk[_key(rf.face_triangle(f))] for f in range(20)]
    cw_to_r12 = {c: r for r, c in enumerate(r12_to_cw)}
    cert = rc.resolve(2025.0, 3).to_earth_root_profile_dict()
    wl, wo = cert["fixed_anchor"]["centroid_deg"]
    sl, so = cert["dynamic_zero"]["minimum_deg"]
    sh = _unit(SH_LAT, SH_LON)
    rows = []
    for fam in gf._frozen_family_names(fp):
        orient = by_fam.get(fam, base)
        w_m = orient.T @ _unit(wl, wo)
        s_m = orient.T @ _unit(sl, so)
        root_face = int(classify_point(cw, w_m))
        books = cb.build_codebooks(root_face, s_m)
        sh_m = orient.T @ sh
        for book, order in books.items():
            mesh_face = order[face_src]          # cwatlas numbering
            r12_face = cw_to_r12[mesh_face]      # r12 frozen numbering
            levels = pk.path_levels(path)
            tri = rf.face_triangle(r12_face)
            first_excl = None
            if not _in_tri(sh_m, tri):
                first_excl = 0
            else:
                cur = tri
                for n, d in enumerate(levels, start=1):
                    cur = rf._subdivide(cur)[d]
                    if first_excl is None and not _in_tri(sh_m, cur):
                        first_excl = n
            cell = rf.cell_triangle(r12_face, levels)
            verts_e = [orient @ v for v in cell]
            cen = sum(verts_e)
            cen = cen / np.linalg.norm(cen)
            dmin = min(_gc(sh, v / np.linalg.norm(v)) for v in verts_e)
            dmin = min(dmin, _gc(sh, cen))
            rows.append({
                "family": fam, "codebook": book,
                "source_face": face_src, "mesh_face": mesh_face,
                "root_face": root_face,
                "contained": first_excl is None,
                "first_excluding_level": first_excl,
                "cell_centroid_latlon": _latlon(cen),
                "approx_min_distance_km": round(dmin, 2),
            })
    return {"rows": rows,
            "contained_any": any(r["contained"] for r in rows),
            "best": min(rows, key=lambda r: r["approx_min_distance_km"])}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # ---- 1. exact packet verification (independent of the prompt text) --
    n = 165876523
    rec = pk.decode_record(n)
    checks = {
        "bits": rec["bits"] == EXPECT_SH["bits"],
        "octal": rec["octal"] == EXPECT_SH["octal"],
        "face": rec["face"] == EXPECT_SH["face"],
        "shell": rec["shell"] == EXPECT_SH["shell"],
        "path_levels": tuple(rec["path_levels"]) == EXPECT_SH["path_levels"],
        "round_trip": rec["round_trip"] and rec["octal_round_trip"],
    }
    ob = octree_bits(n)
    checks["octree"] = (
        (ob["X_bits"], ob["X"]) == EXPECT_SH["octree_x"]
        and (ob["Y_bits"], ob["Y"]) == EXPECT_SH["octree_y"]
        and (ob["Z_bits"], ob["Z"]) == EXPECT_SH["octree_z"])
    q22_note = (
        "prompt's printed Q22 bit string '1110001100010011001010' is "
        "off by one bit position; the correct middle-22 window is "
        f"'{rec['path_bits']}', whose quaternary pairs are exactly the "
        "claimed path (3,3,0,1,2,0,2,1,2,1,1). Values verified "
        "independently; typo recorded, not propagated.")
    print("packet checks:", checks)

    # ---- 2. nine-digit family packets + orange slice in octal domain ----
    packets = {}
    for v in NINE:
        r = pk.decode_record(int(v))
        r["octree"] = octree_bits(int(v))
        packets[v] = r
    orange = ["165892743", "165892763", "165892783"]
    slice_rows = {v: {"octal": packets[v]["octal"],
                      "face": packets[v]["face"],
                      "path": packets[v]["path"],
                      "shell": packets[v]["shell"]} for v in orange}
    shells = [packets[v]["shell"] for v in orange]
    faces = [packets[v]["face"] for v in orange]
    paths = [packets[v]["path"] for v in orange]
    common = 0
    for cs in zip(*paths):
        if len(set(cs)) == 1:
            common += 1
        else:
            break
    slice_finding = {
        "faces": faces, "shells": shells,
        "common_path_prefix_levels": common,
        "path_suffixes": [p[common:] for p in paths],
        "reading": (
            "under the octal grammar the +20-decimal steps change the low "
            "bits: shells are {" + ",".join(map(str, sorted(set(shells))))
            + "} and the paths share only the first "
            f"{common} of 11 levels. The clean single-axis line that the "
            "decimal domain shows does NOT survive the binary/octal "
            "conversion — an exact structural discriminant between the "
            "two readings, reported as-is."),
    }
    print("orange slice (octal):", slice_finding["faces"],
          slice_finding["shells"], "common prefix", common)

    # ---- 3. Stonehenge containment under the sealed freeze --------------
    cont = containment(n)
    print("containment: any =", cont["contained_any"],
          "best =", cont["best"]["approx_min_distance_km"], "km",
          "(", cont["best"]["codebook"], cont["best"]["family"], ")")

    # ---- 4. family separation -------------------------------------------
    fam_sep = {}
    for v in LONGER:
        bits = int(v).bit_length()
        fam_sep[v] = {
            "decimal_digits": len(v), "bits_needed": bits,
            "fits_30_bit_grammar": bits <= 30,
            "status": "BLOCKED_BY_MISSING_INPUT",
            "note": "outside the nine-digit/30-bit family; no exact "
                    "version bridge to a 36/40-bit grammar is proven, so "
                    "it is NOT decoded here (families kept separate as "
                    "locked).",
        }
    print("longer vectors:", {v: fam_sep[v]["bits_needed"]
                              for v in LONGER})

    (OUT / "PACKET_RECEIPT.json").write_text(json.dumps({
        "grammar": "F5|Q22|S3 (r12.icosapacket, reused verbatim)",
        "radix_identity": {"8**12": 8 ** 12, "2**36": 2 ** 36,
                           "4096**3": 4096 ** 3,
                           "equal": 8 ** 12 == 2 ** 36 == 4096 ** 3},
        "stonehenge_checks": checks,
        "q22_print_typo_note": q22_note,
        "stonehenge_record": {k: (list(v) if isinstance(v, tuple) else v)
                              for k, v in packets["165876523"].items()},
        "nine_digit_packets": {v: {"octal": packets[v]["octal"],
                                   "face": packets[v]["face"],
                                   "path": packets[v]["path"],
                                   "shell": packets[v]["shell"],
                                   "octree": packets[v]["octree"]}
                               for v in NINE},
        "orange_slice_octal": {"packets": slice_rows,
                               "finding": slice_finding},
        "family_separation": fam_sep,
        "claims": {"SOURCE_ORIGIN_VALIDATED": "no",
                   "status": "GRAMMAR_EXACT; placements are candidates "
                             "under the R10.8.2 freeze only"},
    }, indent=1, default=str) + "\n", encoding="utf-8")

    (OUT / "CONTAINMENT_REPORT.md").write_text(
        f"""# Stonehenge containment — octal packet decode (R10.8.5)

Word `165876523` = `F5|Q22|S3` -> source face 4, quaternary path
(3,3,0,1,2,0,2,1,2,1,1), shell 3 (body-relative surface shell by the
locked semantics — NOT inferred from any decimal digit). Cell geometry:
R12 frozen midpoint 4-way subdivision (`r12.icosarefine.cell_triangle`),
level-11 cell edge ~ {7054 / 2048:.2f} km. Face context: source-face 4
mapped through the five declared codebooks; Earth orientation: sealed
CALFREEZE per-family rotations. {len(cont['rows'])} finite contexts.

* contained in the final level-11 cell: **{cont['contained_any']}**
  ({sum(1 for r in cont['rows'] if r['contained'])} of
  {len(cont['rows'])} contexts)
* best context: codebook {cont['best']['codebook']}, family
  {cont['best']['family']}, mesh face {cont['best']['mesh_face']},
  first excluding level {cont['best']['first_excluding_level']},
  approx. min distance {cont['best']['approx_min_distance_km']} km
* full rows in PACKET_RECEIPT-adjacent JSON below.

```json
{json.dumps(cont['rows'], indent=1)}
```

Shell 3 declares surface compatibility, so the radial lane is consistent
by construction under this candidate.

SOURCE_ORIGIN_VALIDATED: no
""", encoding="utf-8")

    (OUT / "RUNLOG.md").write_text(
        "# R10.8.5 runlog\n\n```\npython tools/r1085_octal_packet_recovery"
        ".py\npython -m pytest tests/cwatlas/r1085/ -q\n```\n\nReuses "
        "r12.icosapacket / r12.icosarefine verbatim (no new operator). "
        "R10.8.4 decimal-triplet decoder demoted to REJECTED candidate in "
        "cwatlas/r1082/decoder_candidates.py; its code is retained as the "
        "rejected-experiment receipt.\n", encoding="utf-8")
    print("receipts written to", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
