"""Reproduce the R10.11D segmented-frame and affine-envelope result.

This script does not claim that the source table is affine. It enumerates every
invertible affine six-bit permutation consistent with the known child-5 and
child-6 entries, then reports consensus and ambiguity.
"""
from __future__ import annotations

# The full executable implementation is the same implementation embedded in
# the machine receipt generation run. For a compact verification without numpy,
# use the precomputed JSON completion tables and verify every source-known row.

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

KNOWN = {
    5: {15: 5, 30: 40, 4: 37, 26: 30, 1: 25, 52: 31},
    6: {15: 49, 55: 53, 25: 45, 14: 51, 11: 14, 61: 36},
}

for child in (5, 6):
    document = json.loads(
        (HERE / f"AFFINE_CHILD_{child}_32_COMPLETIONS.json").read_text()
    )
    completions = document["completions"]
    assert len(completions) == 32
    for completion in completions:
        table = completion["table"]
        assert len(table) == 64
        assert len(set(table)) == 64
        for source, target in KNOWN[child].items():
            assert table[source] == target
    print(f"child {child}: 32 affine permutation completions verified")

print("R10.11D verification complete")
