"""R10.12 Phases 13-18 — evidence-tiered transition engine.

Wraps the frozen source-known registry (twelve cells), the recomputed
affine envelopes (children 5/6), and the immutable probe workflow.
Unknown cells refuse with a typed error and the full candidate set —
never a guessed state.
"""

from __future__ import annotations

import hashlib

from r1011.affine_envelope import AffineEnvelopeError, envelope_lookup
from r1011.segmented_codec import T_SPARSE
from r1011 import gf2_affine as gf
from r1012.certificate import certify
from r1012.evidence import Tier


class TransitionError(ValueError):
    pass


def registry() -> dict:
    """Phase 13 — consolidated source-known registry."""
    out = {}
    for (state, child), nxt in sorted(T_SPARSE.items()):
        rec = {"output_state": nxt,
               "source_record": "R10.11C authority patch (2026-07-28), "
                                "verified on all four exact pairs",
               "hash": hashlib.sha256(
                   f"T[{state},{child}]={nxt}".encode()).hexdigest()[:16],
               "evidence_tier": Tier.SOURCE_KNOWN.value,
               "correction_status": "CURRENT"}
        out[f"({child},{state})"] = rec
    return {"schema": "rgcs.r1012.transition-registry.v1",
            "cell_count": len(out), "cells": out,
            "table_status": "12 of 512 cells known; remainder "
                            "UNDERDETERMINED"}


def lookup(child: int, state: int) -> dict:
    """Tiered lookup. SOURCE_KNOWN > consensus > underdetermined; other
    children refuse outright."""
    if not (0 <= state <= 63):
        raise TransitionError("state must be a six-bit value 0..63")
    if (state, child) in T_SPARSE:
        return {"child": child, "state": state,
                "output_state": T_SPARSE[(state, child)],
                "evidence_tier": Tier.SOURCE_KNOWN.value}
    try:
        env = envelope_lookup(state, child)
    except AffineEnvelopeError as ex:
        return {"child": child, "state": state,
                "evidence_tier": Tier.UNSUPPORTED.value,
                "refusal": str(ex)}
    if env["evidence_status"] == "AFFINE_FAMILY_CONDITIONAL_CONSENSUS":
        return {"child": child, "state": state,
                "conditional_output": env["conditional_output"],
                "evidence_tier": Tier.CONDITIONAL_CONSENSUS.value,
                "caveat": env["caveat"]}
    return {"child": child, "state": state,
            "possible_outputs": env["possible_outputs"],
            "evidence_tier": Tier.UNDERDETERMINED.value,
            "caveat": env["caveat"]}


def refine(wire, child: int) -> dict:
    """Refine a compact wire through T[., child]. Requires ALL THREE
    state cells to be SOURCE_KNOWN — anything less refuses (typed) and
    hands back the candidate machinery instead."""
    c = certify(wire)
    if c.depth != 0:
        raise TransitionError(
            f"refine expects a compact (depth-0) wire; {wire} has depth "
            f"{c.depth}")
    cells = [lookup(child, s) for s in c.states]
    if all(cell["evidence_tier"] == Tier.SOURCE_KNOWN.value
           for cell in cells):
        return {"wire": str(wire), "child": child,
                "refined_states": [cell["output_state"] for cell in cells],
                "evidence_tier": Tier.SOURCE_KNOWN.value}
    tiers = [cell["evidence_tier"] for cell in cells]
    raise TransitionError(
        f"refused: refinement of {wire} through child {child} needs "
        f"three SOURCE_KNOWN cells; got tiers {tiers}. Use "
        f"candidates() for the typed ambiguity instead.")


def candidates(wire, child: int) -> dict:
    """Full typed candidate set for an ambiguous refinement."""
    c = certify(wire)
    cells = [lookup(child, s) for s in c.states]
    if any(cell["evidence_tier"] == Tier.UNSUPPORTED.value
           for cell in cells):
        return {"wire": str(wire), "child": child,
                "evidence_tier": Tier.UNSUPPORTED.value,
                "refusal": next(cell["refusal"] for cell in cells
                                if "refusal" in cell)}
    outs = []
    for cell in cells:
        if "output_state" in cell:
            outs.append([cell["output_state"]])
        elif "conditional_output" in cell:
            outs.append([cell["conditional_output"]])
        else:
            outs.append(cell["possible_outputs"])
    n = 1
    for o in outs:
        n *= len(o)
    worst = max((cell["evidence_tier"] for cell in cells),
                key=lambda t: [Tier.SOURCE_KNOWN.value,
                               Tier.CONDITIONAL_CONSENSUS.value,
                               Tier.UNDERDETERMINED.value].index(t))
    return {"wire": str(wire), "child": child, "per_state_options": outs,
            "combination_count": n, "evidence_tier": worst,
            "note": "candidates are typed possibilities under the "
                    "restricted affine hypothesis; nothing is selected"}


def operator_family_receipts() -> dict:
    """Phase 15 — preserved R10.11E negative results (live re-check of
    the cheap ones; expensive ones referenced to frozen receipts)."""
    return {
        "no_shared_affine_core": gf.shared_linear_core()[
            "shared_matrix_count"] == 0,
        "frozen_receipt": "docs/r1011/evidence/"
                          "R10_11E_OPERATOR_FAMILY_REDUCTION.json",
        "highlights": ["0 conjugacy hits (720 bit perms)",
                       "0 bounded rot/xor/add fits",
                       "1024 relative operators, 34 cycle structures",
                       "16 equivalence classes per child",
                       "child-6 has fixed-point-free completions; "
                       "child-5 fixes 1-2 states"],
    }
