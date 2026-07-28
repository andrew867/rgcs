"""R10.11D — restricted affine transition-table envelope.

The imported artifacts (``docs/r1011/evidence/r1011d/``) describe, for
child columns 5 and 6, the 32 affine-permutation completions each that
are consistent with the twelve source-known cells, with 32/64 rows
invariant across every completion. This is a **restricted falsifiable
hypothesis** — NEVER the recovered source table. Unknown rows outside
the consensus stay UNDERDETERMINED; children 0,1,2,3,4,7 have NO
entries and are never filled.

High-information probes (await a supplied refined descendant, which
selects or falsifies the affine completion — nothing is assumed):

    165872393 child 5: position-1 output 5;  pos2 XOR pos3 = 58
    165879633 child 6: position-1 output 49; pos2 XOR pos3 = 48

Firewalls: no geography, no lunar-reveal table selection, no invented
cells.
"""

from __future__ import annotations

import csv
from pathlib import Path

from r1011.segmented_codec import T_SPARSE

EV = Path(__file__).resolve().parents[1] / "docs" / "r1011" / "evidence" / \
    "r1011d"

HYPOTHESIS_STATUS = ("RESTRICTED_AFFINE_FALSIFIABLE_HYPOTHESIS — not the "
                     "recovered source table; child columns 5 and 6 only; "
                     "32 completions each; falsified by any mismatching "
                     "supplied refined descendant")

PROBES = {
    (165872393, 5): {"position_1_output": 5, "pos2_xor_pos3": 58},
    (165879633, 6): {"position_1_output": 49, "pos2_xor_pos3": 48},
}


class AffineEnvelopeError(ValueError):
    pass


def load_consensus() -> dict:
    rows = {}
    with open(EV / "AFFINE_CONSENSUS_TABLE.csv", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            key = (int(r["child"]), int(r["input_state"]))
            rows[key] = r
    return rows


def envelope_lookup(state: int, child: int) -> dict:
    """Typed lookup honoring every firewall."""
    if child not in (5, 6):
        raise AffineEnvelopeError(
            f"child {child}: no affine envelope exists (children "
            f"0,1,2,3,4,7 have no entries and are never invented)")
    rows = load_consensus()
    r = rows[(child, state)]
    status = r["evidence_status"]
    out = {"child": child, "state": state, "evidence_status": status,
           "hypothesis": HYPOTHESIS_STATUS}
    if status == "SOURCE_KNOWN":
        out["output"] = int(r["source_known_output"])
        assert T_SPARSE[(state, child)] == out["output"]
    elif status == "AFFINE_FAMILY_CONDITIONAL_CONSENSUS":
        out["conditional_output"] = int(r["consensus_output"])
        out["caveat"] = ("identical under all 32 completions but still "
                         "CONDITIONAL on the affine hypothesis")
    else:
        out["possible_outputs"] = [int(x) for x in
                                   r["possible_outputs"].split()]
        out["caveat"] = "UNDERDETERMINED (32 possibilities)"
    return out
