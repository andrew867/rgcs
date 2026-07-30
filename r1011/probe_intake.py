"""R10.11E — deterministic probe intake and scoring (append-only).

Candidate descendant sets for the two frozen probes are generated and
HASHED before any source answer exists. Registration of a received
descendant freezes it verbatim without scoring; scoring is a separate
step that reads only the pre-hashed candidate sets. A regenerated
candidate set is a new version, never a replacement.

CLI:
    python -m r1011.probe_intake freeze
    python -m r1011.probe_intake register --probe P5 --raw-wire 16... \
        --source-note "..." --observed-at 2026-07-28T...
    python -m r1011.probe_intake score --receipt <id>
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from r1011 import e3_frame as e3
from r1011 import gf2_affine as gf

EV = Path(__file__).resolve().parents[1] / "docs" / "r1011" / "evidence"
LEDGER = EV / "R10_11E_PROBE_LEDGER.jsonl"

PROBES = {
    "P5": {"compact_wire": 165872393, "states": (15, 23, 39), "child": 5,
           "required_output1": 5, "required_xor23": 58},
    "P6": {"compact_wire": 165879633, "states": (15, 34, 59), "child": 6,
           "required_output1": 49, "required_xor23": 48},
}


def candidate_set(probe_id: str) -> dict:
    p = PROBES[probe_id]
    comps = gf.reconstruct(p["child"])
    compact = e3.parse(p["compact_wire"])
    assert compact.states == p["states"]
    cands = []
    for c in comps:
        s1 = c["table"][p["states"][0]]
        s2 = c["table"][p["states"][1]]
        s3 = c["table"][p["states"][2]]
        assert s1 == p["required_output1"]
        assert (s2 ^ s3) == p["required_xor23"]
        wire = e3.encode(e3.E3Parse(
            wire=0, e3=compact.e3, states=(s1, s2, s3),
            children=(p["child"],), terminal=compact.terminal,
            payload_bits=24))
        cands.append({"completion_id": c["id"], "refined_states": [s1, s2, s3],
                      "candidate_wire": wire})
    wires = [c["candidate_wire"] for c in cands]
    return {
        "schema": "rgcs.r1011e.probe-candidates.v1",
        "probe": probe_id, **{k: (list(v) if isinstance(v, tuple) else v)
                              for k, v in PROBES[probe_id].items()},
        "e3": compact.e3, "terminal": compact.terminal,
        "candidates": cands,
        "distinct_wires": len(set(wires)),
        "wire_collisions": len(wires) - len(set(wires)),
        "information_accounting": {
            "raw_observed_output_bits": 18,
            "already_known_bits": "output state 1 (6 bits) is a "
                                  "SOURCE_KNOWN cell",
            "new_table_cells_observed": 2,
            "new_table_cell_bits": 12,
            "affine_completion_index_entropy_bits": 5,
            "invariant_check": f"s2 XOR s3 == {PROBES[probe_id]['required_xor23']} "
                               "under every completion (independent test)",
            "note": "one descendant supplies two previously unknown "
                    "six-bit cells (12 bits of table content) while at "
                    "most 5 bits are needed to index a completion — the "
                    "surplus is the falsification power",
        },
    }


def freeze() -> dict:
    out = {}
    for pid in PROBES:
        cs = candidate_set(pid)
        body = json.dumps(cs, indent=2, sort_keys=True)
        digest = hashlib.sha256(body.encode()).hexdigest()
        cs["candidate_set_sha256"] = digest
        path = EV / f"R10_11E_PROBE_{pid}_CANDIDATES.json"
        path.write_text(json.dumps(cs, indent=2) + "\n", encoding="utf-8")
        out[pid] = digest
    return out


def register(probe: str, raw_wire: int, source_note: str,
             observed_at: str) -> dict:
    """Append-only registration; NO scoring, NO selection."""
    entry = {
        "action": "REGISTER", "probe": probe, "raw_wire": raw_wire,
        "source_note": source_note, "observed_at": observed_at,
        "receipt_id": hashlib.sha256(
            f"{probe}:{raw_wire}:{observed_at}".encode()).hexdigest()[:16],
    }
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry) + "\n")
    return entry


def score(receipt_id: str) -> dict:
    entries = [json.loads(l) for l in open(LEDGER, encoding="utf-8")]
    reg = next(e for e in entries
               if e.get("receipt_id") == receipt_id
               and e["action"] == "REGISTER")
    pid = reg["probe"]
    cs = json.loads((EV / f"R10_11E_PROBE_{pid}_CANDIDATES.json")
                    .read_text(encoding="utf-8"))
    p = PROBES[pid]
    parsed = e3.parse(int(reg["raw_wire"]))
    s1, s2, s3 = parsed.states
    matched = [c["completion_id"] for c in cs["candidates"]
               if tuple(c["refined_states"]) == (s1, s2, s3)]
    verdict = ("SELECTS_COMPLETIONS" if matched
               else "FALSIFIES_AFFINE_FAMILY_FOR_THIS_PROBE")
    result = {
        "action": "SCORE", "receipt_id": receipt_id, "probe": pid,
        "candidate_set_sha256": cs["candidate_set_sha256"],
        "parse": {"e3": parsed.e3, "states": list(parsed.states),
                  "children": list(parsed.children),
                  "terminal": parsed.terminal},
        "output1_matches_source_known": s1 == p["required_output1"],
        "xor_invariant_holds": (s2 ^ s3) == p["required_xor23"],
        "matched_completion_ids": matched,
        "verdict": verdict,
        "note": "source-known cells and the E3 frame are untouched by "
                "any outcome; a falsification kills only the affine "
                "hypothesis for this child column",
    }
    with open(LEDGER, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(result) + "\n")
    return result


def main() -> int:
    ap = argparse.ArgumentParser(prog="r1011.probe_intake")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("freeze")
    r = sub.add_parser("register")
    r.add_argument("--probe", required=True, choices=list(PROBES))
    r.add_argument("--raw-wire", required=True, type=int)
    r.add_argument("--source-note", required=True)
    r.add_argument("--observed-at", required=True)
    s = sub.add_parser("score")
    s.add_argument("--receipt", required=True)
    a = ap.parse_args()
    if a.cmd == "freeze":
        print(json.dumps(freeze(), indent=2))
    elif a.cmd == "register":
        print(json.dumps(register(a.probe, a.raw_wire, a.source_note,
                                  a.observed_at), indent=2))
    else:
        print(json.dumps(score(a.receipt), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
