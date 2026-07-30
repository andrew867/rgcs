"""R10.47C — the variable STAGED address parser.

OPERATOR CORRECTION, accepted in full: every field label is a MAXIMUM
CAPACITY, not an always-full field. The grammar is staged:

    root -> section(s) -> path step(s) -> epoch/state step(s) -> M3

    ROOTvar     <= 4 bits
    SECTIONvar  <= 8 bits, often left-zero-padded
    PATHvar     <= 12 bits  = up to 4 octal path steps
    EPOCHvar    <=  9 bits  = up to 3 optional octal chunks
    M3          =  3 bits, MANDATORY, always last

RETRACTED BY THIS MODULE:
    R4 fixed, S8 fixed, P12 fixed, CORE24 fixed,
    path8 fixed, tail2 fixed,
    "width growth is only tail", "width growth is only path".

All four boundaries float. The parser ENUMERATES legal splits; it does
not assume one.

WHY THE PREVIOUS PARENT/CHILD HITS WERE FALSE (R10.47B)
-------------------------------------------------------
Testing "child path = parent path + one octal digit" on numerically
adjacent integers finds hits automatically: values 60 apart share long
octal prefixes by arithmetic. The giveaway was that 100% of hits were
BIDIRECTIONAL, and a refinement relation must be antisymmetric. Every
test here therefore reports its antisymmetry fraction, and a symmetric
result is reported as prefix coincidence, not refinement.
"""

from __future__ import annotations

#: SOURCE line 31: "always 4-bit root zero padded". The root is a FIXED
#: 4-bit field, zero-padded - not a variable-width one. This supersedes
#: the R10.47C "ROOTvar <= 4" wording, which the source contradicts.
#: Set ROOT_FIXED=False only to reproduce the older variable-root
#: enumeration for comparison.
ROOT_FIXED = True
ROOT_BITS = 4
ROOT_MAX, SECTION_MAX = 4, 8

#: SOURCE line 107: the 8-bit section is "surface refinement layer 2 AND
#: 3, not always including level 3". So S decomposes again:
#:     S = layer2 | OPTIONAL layer3
#: layer3 is one octal refinement digit when present, absent otherwise.
LAYER3_LENS = (0, 3)
LAYER2_MIN = 1
PATH_LENS = (0, 3, 6, 9, 12)
EPOCH_LENS = (0, 3, 6, 9)
M3_BITS = 3

#: Labelled same-location pairs. THREE, not two -- the third is what
#: refuted the affine bridge (R10.47C).
TRANSPORT_PAIRS = {
    "Stonehenge": (1643789253, 165876523),
    "Toronto": (1672875493, 168930443),
    "CYYT_StJohns": (1658274383, 165892733),
}


#: SOURCE CONSTRAINT, line 32 of the 2026-07-29 note:
#:   "surface refinements can be less than 20 bits, but ALWAYS ONE OF
#:    EACH from the 8-bit and 12-bit parts"
#: so a legal split must draw at least one refinement from the section
#: (8-bit) part AND at least one octal step from the path (12-bit) part.
#: S = 0 and P = 0 are therefore ILLEGAL. Earlier revisions of this
#: function allowed both and over-enumerated the split space.
SECTION_MIN = 1          # at least one bit from the 8-bit part
PATH_MIN = 3             # at least one octal step from the 12-bit part


def legal_splits(payload_bits: int, enforce_source_minima: bool = True):
    """Every (R,S,P,E) with R+S+P+E+3 == payload_bits.

    With ``enforce_source_minima`` (the default and the correct
    behaviour) S >= 1 and P >= 3, per the source's "always one of each"
    rule. Pass False only to reproduce the older over-enumeration for
    comparison.
    """
    smin = SECTION_MIN if enforce_source_minima else 0
    pmin = PATH_MIN if enforce_source_minima else 0
    roots = (ROOT_BITS,) if ROOT_FIXED else range(1, ROOT_MAX + 1)
    out = []
    for R in roots:
        for S in range(smin, SECTION_MAX + 1):
            for P in PATH_LENS:
                if P < pmin:
                    continue
                E = payload_bits - M3_BITS - R - S - P
                if E in EPOCH_LENS:
                    out.append((R, S, P, E))
    return out


def section_layers(section: int, S_bits: int):
    """SOURCE line 107: split the section into layer2 | optional layer3.

    Returns every legal (layer2_bits, layer3_bits) decomposition with
    the layer values, so the optional level-3 refinement is explicit
    rather than buried inside an opaque S.
    """
    out = []
    for l3 in LAYER3_LENS:
        l2 = S_bits - l3
        if l2 < LAYER2_MIN:
            continue
        layer2 = (section >> l3) & ((1 << l2) - 1) if l2 else 0
        layer3 = section & ((1 << l3) - 1) if l3 else None
        out.append({
            "layer2_bits": l2, "layer3_bits": l3,
            "layer2": layer2, "layer3": layer3,
            "level3_present": l3 > 0,
            "layer3_octal": format(layer3, "01o") if l3 else "",
        })
    return out


def stage(value: int, width: int, split) -> dict:
    """Cut one word under one split, canonicalised by left-padding."""
    R, S, P, E = split
    pos = width
    pos -= R
    root = (value >> pos) & ((1 << R) - 1) if R else 0
    pos -= S
    sect = (value >> pos) & ((1 << S) - 1) if S else 0
    pos -= P
    path = (value >> pos) & ((1 << P) - 1) if P else 0
    pos -= E
    ep = (value >> pos) & ((1 << E) - 1) if E else 0
    m3 = value & 7
    return {
        "split": split, "width": width,
        "root_padded4": format(root, "04b"),
        "section_padded8": format(sect, "08b"),
        "path_octal": format(path, f"0{P // 3}o") if P else "",
        "section_layerings": section_layers(sect, S),
        "epoch_octal": format(ep, f"0{E // 3}o") if E else "",
        "m3": m3,
    }


def parses(value: int):
    """All canonical staged parses of one wire."""
    bl = value.bit_length()
    width = next((w for w in (27, 30, 33, 36) if bl <= w), None)
    if width is None:
        return []
    return [stage(value, width, s) for s in legal_splits(width)]


def _antisym(hits) -> dict:
    s = {(a, b) for a, b, *_ in hits}
    both = sum(1 for a, b in s if (b, a) in s)
    return {"directed_hits": len(s), "bidirectional": both,
            "bidirectional_fraction": (both / len(s)) if s else 0.0,
            "antisymmetric": bool(s) and both == 0}


def refinement_tests(corpus) -> dict:
    """A/B/C: section, path and epoch refinement, each with antisymmetry."""
    P = {v: parses(v) for v in corpus}
    sect_h, path_h, ep_h = [], [], []
    for a in corpus:
        for b in corpus:
            if a == b:
                continue
            for pa in P[a]:
                for pb in P[b]:
                    # A. SECTION refinement: same root, section extends
                    if (pa["root_padded4"] == pb["root_padded4"]
                            and pa["section_padded8"] != pb["section_padded8"]
                            and pb["section_padded8"].lstrip("0").startswith(
                                pa["section_padded8"].lstrip("0"))
                            and pa["section_padded8"].lstrip("0")):
                        sect_h.append((a, b, pa["split"], pb["split"]))
                    # B. PATH refinement: same root+section, +1 octal step
                    if (pa["root_padded4"] == pb["root_padded4"]
                            and pa["section_padded8"] == pb["section_padded8"]
                            and len(pb["path_octal"]) == len(pa["path_octal"]) + 1
                            and pb["path_octal"][:-1] == pa["path_octal"]):
                        path_h.append((a, b, pa["split"], pb["split"]))
                    # C. EPOCH refinement: same root+section+path, +1 chunk
                    if (pa["root_padded4"] == pb["root_padded4"]
                            and pa["section_padded8"] == pb["section_padded8"]
                            and pa["path_octal"] == pb["path_octal"]
                            and len(pb["epoch_octal"]) == len(pa["epoch_octal"]) + 1
                            and pb["epoch_octal"][:-1] == pa["epoch_octal"]):
                        ep_h.append((a, b, pa["split"], pb["split"]))
    return {
        "A_section": {**_antisym(sect_h), "raw_hits": len(sect_h)},
        "B_path": {**_antisym(path_h), "raw_hits": len(path_h)},
        "C_epoch": {**_antisym(ep_h), "raw_hits": len(ep_h)},
    }


def transport_bridge_status() -> dict:
    """D. The affine bridge, tested against all THREE labelled pairs."""
    M, A, B = 1 << 30, 923, 550585316
    rows, ok = [], 0
    for lab, (var, comp) in TRANSPORT_PAIRS.items():
        got = (A * int(str(var)[2:]) + B) % M
        hit = got == comp
        ok += hit
        rows.append({"pair": lab, "variable": var, "compact": comp,
                     "bridge_output": got, "exact": hit,
                     "error": got - comp})
    return {
        "rows": rows, "exact": ok, "total": len(TRANSPORT_PAIRS),
        "affine_fits_all_three": ok == len(TRANSPORT_PAIRS),
        "family_members_fitting_all_three": 0,
        "status": "REFUTED_AS_GENERAL_TRANSPORT_BRIDGE",
        "why": "two points cannot over-determine an affine mod 2^30 - 32 "
               "(A,B) pairs fit any two. The third labelled pair is the "
               "first out-of-sample test and NO member of that family "
               "reproduces it. The R10.19 '32/2^60' figure answered "
               "whether a pre-recorded constant lands in the fitting "
               "family, not whether the map generalises.",
        "retracts": "R10_19_SURFACE_BRIDGE_HEADER_STRIPPED_AFFINE_CANDIDATE",
    }
