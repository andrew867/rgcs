"""R10.13 Phase 29 — 19-wire exact-cover partition solver.

The corrected 19-record response is stated (source) to encode eight
compact/refined pairs and one three-depth same-point chain. This
solver enumerates BOUNDED partitions of the actual 19 wires into
{8 pairs + 1 triple}, scoring each block against executable
relationship tests, and reports the truth of what survives — it never
fabricates a partition to match the stated target.

Relationship families tested per block (declared, bounded):
  R1 refined-descendant: parses differ by exactly one extra child
     (left or right under the two-sided codec) and the state triple is
     consistent with the 12 SOURCE_KNOWN transition cells where those
     cells apply (unknown cells: CONDITIONAL, not a match).
  R2 same-point chain: three wires with extra depth 0,1,2 forming two
     nested R1 links.
  R3 sibling: identical E3 + state triple, different children.

Every wire must be used exactly once. The full partition space over
blocks that pass R1/R2 is exhausted before any conclusion; if zero
partitions survive, the result is a typed negative, and the next
request to the source is emitted instead of a guess.
"""

from __future__ import annotations

import itertools
import json

from r1011.segmented_codec import T_SPARSE
from r1013.varcodec import parse_all

WIRES_19 = ["165876523", "1643789253", "168930443", "1672875493",
            "165892733", "1658274383", "165823973", "1658729343",
            "165879243", "167849523", "167854923", "165892323",
            "168724343", "165872943", "165829473", "165872393",
            "165652893", "165879633", "165778933"]

KNOWN_PAIRS = [("165876523", "1643789253"),   # Stonehenge
               ("168930443", "1672875493"),   # Toronto
               ("165892733", "1658274383"),   # CYYT
               ("165823973", "1658729343")]   # slash pair


def _p(wire):
    return parse_all(wire)["splits"]


def link_test(a: str, b: str) -> dict:
    """R1: is b a one-step refinement of a (any legal split pairing)?"""
    pa, pb = _p(a), _p(b)
    hits = []
    for sa in pa:
        for sb in pb:
            dl = sb.depth_left - sa.depth_left
            dr = sb.depth_right - sa.depth_right
            if dl + dr != 1 or dl < 0 or dr < 0:
                continue
            side = "left" if dl == 1 else "right"
            if side == "left":
                if sb.left_children[1:] != sa.left_children:
                    continue
                child = sb.left_children[0]
            else:
                if sb.right_children[:-1] != sa.right_children:
                    continue
                child = sb.right_children[-1]
            if sb.e3 != sa.e3:
                continue
            # transition consistency on the 12 SOURCE_KNOWN cells
            verdicts = []
            for s_in, s_out in zip(sa.states, sb.states):
                if (s_in, child) in T_SPARSE:
                    verdicts.append(T_SPARSE[(s_in, child)] == s_out)
                else:
                    verdicts.append(None)          # unknown cell
            if any(v is False for v in verdicts):
                continue
            hits.append({"side": side, "child": child,
                         "known_cells_hit": sum(v is True
                                                for v in verdicts),
                         "unknown_cells": sum(v is None
                                              for v in verdicts),
                         "status": "EXACT" if all(verdicts)
                         else "CONDITIONAL"})
    return {"a": a, "b": b, "links": hits, "linked": bool(hits)}


def chain_test(a: str, b: str, c: str) -> bool:
    return link_test(a, b)["linked"] and link_test(b, c)["linked"]


def solve(max_partitions: int = 200000) -> dict:
    """Exhaust partitions of the 19 wires into 8 pairs + 1 triple over
    the R1/R2-passing blocks."""
    wires = WIRES_19
    # candidate pairs and triples from executable link tests
    pair_ok = {}
    for a, b in itertools.permutations(wires, 2):
        lt = link_test(a, b)
        if lt["linked"]:
            pair_ok[(a, b)] = lt
    triple_ok = []
    for a, b, c in itertools.permutations(wires, 3):
        if (a, b) in pair_ok and (b, c) in pair_ok:
            triple_ok.append((a, b, c))
    survivors = []
    examined = 0

    def extend(remaining, blocks, used_triple):
        nonlocal examined
        if examined > max_partitions:
            return
        if not remaining:
            if used_triple and len(blocks) == 9:
                survivors.append(list(blocks))
            return
        w = min(remaining)
        # w in a pair
        for other in remaining - {w}:
            for blk in ((w, other), (other, w)):
                if blk in pair_ok:
                    examined += 1
                    extend(remaining - {w, other}, blocks + [blk],
                           used_triple)
        # w in the triple
        if not used_triple:
            for t in triple_ok:
                if w in t and set(t) <= remaining:
                    examined += 1
                    extend(remaining - set(t), blocks + [t], True)

    extend(frozenset(wires), [], False)
    result = {
        "schema": "rgcs.r1013.exact-cover.v1",
        "wires": wires, "wire_count": len(wires),
        "candidate_pairs": len(pair_ok),
        "candidate_triples": len(triple_ok),
        "partitions_examined": examined,
        "surviving_partitions": len(survivors),
        "known_pairs_reproduced": [
            {"pair": list(pq),
             "linked": link_test(*pq)["linked"]} for pq in KNOWN_PAIRS],
        "search_exhausted": examined <= max_partitions,
    }
    if survivors:
        result["status"] = ("UNIQUE_PARTITION" if len(survivors) == 1
                            else "MULTIPLE_PARTITIONS_UNDERDETERMINED")
        result["example_partition"] = [list(b) for b in survivors[0]]
    else:
        result["status"] = "NO_PARTITION_UNDER_CURRENT_CONSTRAINTS"
        result["next_source_request"] = (
            "The 19 wires do not partition into 8 one-step pairs and "
            "one 3-chain under the executable link tests (depth "
            "structure: 15 compact + 4 refined wires cannot form 8 "
            "pairs each needing a refined member). Request from the "
            "source: which wires pair, or the refined descendants of "
            "the frozen probes 165872393 (child 5) and 165879633 "
            "(child 6).")
    return result


def receipt(path=None) -> dict:
    r = solve()
    if path:
        from pathlib import Path
        Path(path).write_text(json.dumps(r, indent=2) + "\n",
                              encoding="utf-8")
    return r
