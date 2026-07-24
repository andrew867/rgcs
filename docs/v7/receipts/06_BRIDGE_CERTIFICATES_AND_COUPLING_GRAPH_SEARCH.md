# R13 Phase Receipt

```text
phase_id: 06
phase_title: Bridge Certificates and Coupling-Graph Search
status: COMPLETE
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/bridgegraph.py, tests/v6/test_r13_bridgegraph.py
files_modified: none
tests_added: 15
focused_test_result: 15 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS (incl. r13); references hashed by srcregistry
claim_classes_emitted: ENGINEERING_CANDIDATE
private_files_read: false
```

## Work completed

Provided machinery that permits new cross-domain hypotheses without automatic
equivalence. Verdict **`COUPLING_GRAPH_SEARCH_CERTIFICATE_GATED`**. The module
builds a directed graph (`CouplingGraph`) whose edges are R12 coupling
certificates: an edge from source to target exists only when a complete
certificate — all nine declarations present — licenses that directed pair. An
incomplete certificate is refused as an edge (`add_edge`), and a missing edge
yields `None`, never a guess. Two refusals hold —
`refuse_automatic_composition` and `refuse_path_as_measured`.

## Evidence and equations implemented

`search_candidate_bridges` enumerates the domain pairs that could bridge a
source to a target (the direct pair and every one-intermediate pair), returning
each as a `CandidateBridge` fixed at `REQUIRES_CERTIFICATE`. Composition is not
free: `path_claim_class` caps any chain of complete certificates at
`ENGINEERING_CANDIDATE` (weakest link, never a measurement class), and a
multi-edge `Path` carries `REQUIRES_END_TO_END_CERTIFICATE`.

## Negative results

A certificate edge is a licence to model one transfer awaiting a falsifying
measurement that has not been performed — not evidence that any cross-domain
coupling exists. Certificates do not compose:
`refuse_automatic_composition` (consistent with
`r12.bridge.refuse_chained_transfer`) enforces that A→B and B→C do not license
A→C — a routed A..C chain still needs its own end-to-end certificate. A
candidate bridge is a hypothesis to go certify, not an established coupling.
Nothing was measured.

## Deviations from prompt

None.

## Blocking inputs, when applicable

None — software/architecture phase.

## Downstream impact

The certificate-gated graph is the transfer authority for every cross-domain
phase: the piezo→BVD bridge (10), the cross-domain transfer benchmark (30),
and the cross-domain red team (43) all route through it.

## Reopening test

Re-run `tests/v6/test_r13_bridgegraph.py`; reopen if the verdict string
changes, if an incomplete certificate is accepted as an edge, if
`path_claim_class` exceeds `ENGINEERING_CANDIDATE`, or if either refusal stops
raising.

## Acceptance checklist
- [x] focused tests pass
- [x] receipt written
- [x] claim classes recorded
- [x] no private files read
- [x] PHYSICAL_VALIDATION_NOT_CLAIMED
