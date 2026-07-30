"""R10.12 Phases 08+09+16 — golden 28-wire registry, legacy migration,
child-column coverage audit and source query queue."""

from __future__ import annotations

import hashlib
import json
from importlib import resources
from pathlib import Path

from r1012.certificate import certify
from r1012.evidence import Tier

_DATA = Path(__file__).resolve().parent / "data"


def golden28() -> dict:
    """The corrected, versioned 28-wire fixture (A2 batch v2)."""
    return json.loads((_DATA / "golden28_v2.json").read_text(encoding="utf-8"))


def verify_corpus() -> dict:
    """Parse + round-trip every golden wire; verify batch hash."""
    g = golden28()
    wires = g["wires"]
    h = hashlib.sha256(json.dumps(wires).encode()).hexdigest()
    rows, failures = [], 0
    for w in wires:
        try:
            c = certify(w)
            rows.append({"wire": w, "ok": True, "e3": c.e3,
                         "depth": c.depth, "terminal": c.terminal,
                         "children": list(c.child_path)})
        except Exception as ex:                              # typed refusals
            rows.append({"wire": w, "ok": False, "error": str(ex)[:80]})
            failures += 1
    # legacy segmented-family wires (anchors etc.) migrate through the
    # SAME canonical parser — never the monolithic profile
    legacy = ["165876523", "1643789253", "168930443", "1672875493",
              "165892733", "1658274383", "165823973", "1658729343",
              "165879243", "167849523", "167854923", "165892323",
              "168724343", "165872943", "165829473", "165872393",
              "165652893", "165879633", "165778933"]
    legacy_rows = []
    for w in legacy:
        try:
            c = certify(w)
            legacy_rows.append({"wire": w, "ok": True, "e3": c.e3,
                                "depth": c.depth})
        except Exception as ex:
            legacy_rows.append({"wire": w, "ok": False,
                                "error": str(ex)[:80]})
    return {
        "schema": "rgcs.r1012.corpus-verify.v1",
        "golden_batch_sha256": h,
        "expected_sha256": g["intake_v2_sha256"],
        "hash_match": h == g["intake_v2_sha256"],
        "golden_total": len(wires),
        "golden_parsed": sum(1 for r in rows if r["ok"]),
        "golden_failures": failures,
        "legacy_total": len(legacy),
        "legacy_parsed": sum(1 for r in legacy_rows if r["ok"]),
        "rows": rows, "legacy_rows": legacy_rows,
        "correction_ledger_note": "1687425419853 lives only in the "
                                  "correction ledger (COR-03)",
    }


def child_coverage() -> dict:
    """Phase 16 — what the corrected batch adds structurally.

    A transition cell needs a same-location compact/refined EQUALITY;
    a child symbol alone infers nothing. This audit counts coverage and
    emits the query queue of decisive pairings."""
    g = golden28()
    seen = {}
    queue = []
    for w in g["wires"]:
        try:
            c = certify(w)
        except Exception:
            continue
        for ch in c.child_path:
            seen.setdefault(ch, []).append(w)
        if c.depth >= 1:
            queue.append({
                "wire": w, "children": list(c.child_path),
                "becomes_decisive_if": "a same-location compact parent "
                                       "(or deeper refined descendant) is "
                                       "declared by the source",
                "new_columns_it_would_touch": sorted(
                    set(c.child_path) - {5, 6})})
    known_columns = {5, 6}
    return {
        "schema": "rgcs.r1012.child-coverage.v1",
        "child_symbol_occurrences": {str(k): len(v)
                                     for k, v in sorted(seen.items())},
        "columns_with_source_known_cells": sorted(known_columns),
        "columns_touched_by_new_batch_without_transitions":
            sorted(set(seen) - known_columns),
        "transition_inference_rule": "NEVER from a child symbol alone",
        "query_queue": queue,
    }
