"""R10.11 unified compact/refined codec search (grammar families A-F).

Three exact same-location pairs constrain the search; NO old field
boundary (F5/Q22/S3, header width, root-face position, low-bit shell)
is assumed. Every family is finite and declared BEFORE evaluation;
every rejection is recorded; no location names appear in any decision
path (pairs arrive as opaque integer tuples).

Families (from 02_MATHEMATICS/UNIFIED_VARIABLE_DEPTH_CODEC_SPEC.md):

A. Whole-number binary/octal, finite boundaries: the refined word's
   natural binary width exceeds the compact word's by exactly 3 bits
   on every pair, so the exhaustive contiguous test is: delete 3
   consecutive bits at every offset (and 1 octal digit at every
   offset); parent equality is integer equality.
B. Decimal hierarchy first: clip k leading decimal digits
   (k in 0..3) as a typed header field, then run the family-A tests
   on the payloads; header agreement is recorded, not assumed.
C. Prefix-as-path: nested typed digits star|Sol|body ("1","6","5|7")
   with the remainder as payload; structural agreement of the typed
   digits across each pair is the gate.
D. Width-based octal refinement: one extra decimal digit <-> one
   3-bit node selection — realized by the A/B deletion tests at
   natural widths (widths recorded exactly, never forced to 30/33).
E. Morton/XYZ interleaves: pad compact to 3L bits and refined to
   3(L+1); split into 3-bit levels; parent removal = drop last level;
   compare level sequences under axis permutation (6), level-order
   reversal (2), per-level Gray decode (2), pad mode (2) = 48
   combos; plus FAM-E-SCATTER: delete ANY 3 (possibly non-adjacent)
   bit positions of the refined word — all C(31,3) subsets per pair —
   and intersect the surviving position-sets across pairs.
F. Finite reversible transducers keyed by declared state: bounded in
   this phase to the identity transducer (any non-trivial machine
   space is unbounded and would be silent grammar-widening; recorded
   as such).
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass


def _bits(n: int, width: int | None = None) -> str:
    b = format(n, "b")
    return b if width is None else b.zfill(width)


def _gray_decode(v: int) -> int:
    out = 0
    while v:
        out ^= v
        v >>= 1
    return out


@dataclass(frozen=True)
class FamilyResult:
    family: str
    candidate: str
    per_pair: tuple            # tuple of dicts
    survives: bool
    rejection: str = ""


def family_a(pairs) -> list[FamilyResult]:
    out = []
    # contiguous 3-bit deletion, per offset (offset counted from MSB
    # of the refined natural-width word)
    max_off = max(len(_bits(r)) for _, r in pairs)
    for off in range(max_off):
        rows, ok = [], True
        for c, r in pairs:
            rb = _bits(r)
            if off + 3 > len(rb):
                rows.append({"pair": (c, r), "hit": False,
                             "why": "offset beyond word"})
                ok = False
                continue
            cand = int(rb[:off] + rb[off + 3:], 2)
            hit = cand == c
            rows.append({"pair": (c, r), "hit": hit,
                         "child_bits": rb[off:off + 3]})
            ok = ok and hit
        out.append(FamilyResult(
            "A", f"A_BITDEL_off{off}", tuple(rows), ok,
            "" if ok else "not all pairs align at this offset"))
    # single octal-digit deletion
    for k in range(11):
        rows, ok = [], True
        for c, r in pairs:
            ro = format(r, "o")
            if k >= len(ro):
                rows.append({"pair": (c, r), "hit": False,
                             "why": "digit index beyond word"})
                ok = False
                continue
            cand = int(ro[:k] + ro[k + 1:], 8)
            hit = cand == c
            rows.append({"pair": (c, r), "hit": hit, "child_digit": ro[k]})
            ok = ok and hit
        out.append(FamilyResult(
            "A", f"A_OCTDEL_pos{k}", tuple(rows), ok,
            "" if ok else "not all pairs align at this octal position"))
    return out


def family_b(pairs) -> list[FamilyResult]:
    out = []
    for k in (1, 2, 3):
        # typed header = first k decimal digits (recorded, compared)
        clipped = []
        for c, r in pairs:
            cs, rs = str(c), str(r)
            clipped.append(((cs[:k], int(cs[k:] or "0")),
                            (rs[:k], int(rs[k:] or "0")), (c, r)))
        header_match = all(ch == rh for (ch, _), (rh, _), _ in clipped)
        for off in range(30):
            rows, ok = [], True
            for (ch, cp), (rh, rp), pair in clipped:
                rb = _bits(rp)
                if len(rb) - len(_bits(cp)) != 3 or off + 3 > len(rb):
                    rows.append({"pair": pair, "hit": False,
                                 "why": "payload widths not 3 bits apart "
                                        "or offset out of range"})
                    ok = False
                    continue
                cand = int(rb[:off] + rb[off + 3:], 2)
                hit = cand == cp
                rows.append({"pair": pair, "hit": hit,
                             "headers": (ch, rh)})
                ok = ok and hit
            ok = ok and header_match
            out.append(FamilyResult(
                "B", f"B_CLIP{k}_BITDEL_off{off}", tuple(rows), ok,
                "" if ok else ("header fields differ within a pair"
                               if not header_match else
                               "payload alignment failed")))
    return out


def family_c(pairs) -> list[FamilyResult]:
    rows, ok = [], True
    for c, r in pairs:
        cs, rs = str(c), str(r)
        typed_c = (cs[0], cs[1], cs[2])
        typed_r = (rs[0], rs[1], rs[2])
        match = typed_c == typed_r and typed_c[:2] == ("1", "6") \
            and typed_c[2] in ("5", "7")
        rows.append({"pair": (c, r), "typed_compact": typed_c,
                     "typed_refined": typed_r, "hit": match})
        ok = ok and match
    return [FamilyResult(
        "C", "C_STAR_SOL_BODY_TYPED", tuple(rows), ok,
        "" if ok else "typed star|Sol|body digits do not agree across "
                      "pair members / not in {165,167} form")]


def family_e(pairs) -> list[FamilyResult]:
    out = []
    for pad_natural in (True, False):
        for perm in itertools.permutations(range(3)):
            for rev in (False, True):
                for gray in (False, True):
                    rows, ok = [], True
                    for c, r in pairs:
                        if pad_natural:
                            cl = (len(_bits(c)) + 2) // 3
                            rl = (len(_bits(r)) + 2) // 3
                        else:
                            cl, rl = 10, 11
                        if rl != cl + 1:
                            rows.append({"pair": (c, r), "hit": False,
                                         "why": "level counts not L,L+1"})
                            ok = False
                            continue
                        cb = _bits(c, 3 * cl)
                        rb = _bits(r, 3 * rl)
                        clv = [cb[i:i + 3] for i in range(0, 3 * cl, 3)]
                        rlv = [rb[i:i + 3] for i in range(0, 3 * rl, 3)]
                        if rev:
                            rlv = rlv[::-1]
                        parent = rlv[:-1]

                        def xf(sym):
                            v = int(sym, 2)
                            if gray:
                                v = _gray_decode(v)
                            b = format(v, "03b")
                            return "".join(b[perm[i]] for i in range(3))
                        hit = [xf(s) for s in parent] == clv
                        rows.append({"pair": (c, r), "hit": hit})
                        ok = ok and hit
                    out.append(FamilyResult(
                        "E",
                        f"E_LVL_{'nat' if pad_natural else '30_33'}_"
                        f"perm{''.join(map(str, perm))}_"
                        f"{'rev' if rev else 'fwd'}_"
                        f"{'gray' if gray else 'bin'}",
                        tuple(rows), ok,
                        "" if ok else "level sequences differ"))
    return out


def family_e_scatter(pairs) -> FamilyResult:
    """Delete ANY 3 bit positions (MSB-indexed in the padded-31 frame)
    of each refined word; intersect surviving position-sets."""
    common = None
    per_pair = []
    for c, r in pairs:
        rb = _bits(r, 31)
        hits = set()
        for combo in itertools.combinations(range(31), 3):
            cand = int("".join(ch for i, ch in enumerate(rb)
                               if i not in combo), 2)
            if cand == c:
                hits.add(combo)
        per_pair.append({"pair": (c, r), "hit_count": len(hits)})
        common = hits if common is None else (common & hits)
    ok = bool(common)
    return FamilyResult(
        "E", "E_SCATTER_DEL3", tuple(per_pair), ok,
        "" if ok else "no common 3-bit deletion position-set across all "
                      "pairs",)


def family_f(pairs) -> list[FamilyResult]:
    return [FamilyResult(
        "F", "F_IDENTITY_TRANSDUCER", tuple(
            {"pair": p, "hit": False} for p in pairs), False,
        "identity transducer reduces to family A (already failed); "
        "non-trivial machine spaces are unbounded and are NOT searched "
        "(that would silently widen the grammar)")]


def evaluate(pairs) -> dict:
    results: list[FamilyResult] = []
    results += family_a(pairs)
    results += family_b(pairs)
    results += family_c(pairs)
    results += family_e(pairs)
    results.append(family_e_scatter(pairs))
    results += family_f(pairs)
    survivors = [r for r in results if r.survives]
    return {
        "schema": "rgcs.r1011.codec-search.v1",
        "pair_count": len(pairs),
        "candidate_count": len(results),
        "survivor_count": len(survivors),
        "survivors": [r.candidate for r in survivors],
        "results": [{
            "family": r.family, "candidate": r.candidate,
            "survives": r.survives, "rejection": r.rejection,
            "per_pair": [
                {k: v for k, v in row.items() if k != "pair"} | {
                    "compact": row["pair"][0], "refined": row["pair"][1]}
                for row in r.per_pair],
        } for r in results],
        "status": ("UNIFIED_CODEC_CANDIDATE" if len(survivors) == 1
                   else "FINITE_ALIASES" if len(survivors) > 1
                   else "TESTED_GRAMMAR_INCOMPLETE_ZERO_SURVIVORS"),
    }
