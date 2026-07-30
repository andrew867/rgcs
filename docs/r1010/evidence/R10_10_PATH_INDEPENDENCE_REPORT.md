# R10.10 Path-Independence Report (Phase 3)

**Result: PATH INDEPENDENCE FAILS — the transition/phase model is
incomplete, exactly as the spec's failure clause anticipates.**

## What was built

All 20 faces and 30 undirected adjacencies from the FROZEN V1 rigid
mesh; for every directed crossing the edge-induced permutation (shared
primal-edge vertices to themselves, unmatched to unmatched), its
parity, and its inverse (all 60 verified to invert exactly);
orientation states propagated from the Wilkes root (mesh face 0) along
a deterministic BFS.

## The finding

- **Every one of the 60 directed edge transitions is a reflection
  (parity −1).** This is intrinsic to the shared-edge crossing rule,
  not a data artifact.
- **All 12 dual 5-cycles (faces around a primal vertex) carry
  nontrivial holonomy with parity −1** — an odd number of reflections
  can never compose to the identity. 40/60 directed edges agree with
  the BFS assignment (the tree edges and coincidences); the rest
  witness the holonomy.
- Consequence: a single per-face orientation label CANNOT be globally
  consistent under edge-reflection transport on this graph. Any
  complete model needs an additional phase/parity rule (e.g. a spin
  structure / per-crossing sign convention) that the source has not
  yet provided. This is recorded as UNRESOLVED, not invented.
- Corroboration: the BFS assignment gives mesh face 12 orientation
  `012`, while the EXACT empirically recovered V1 convention is
  `102` — precisely one reflection apart.

## Data

`R10_10_FACE_ADJACENCY.csv`, `R10_10_DIRECTED_EDGE_TRANSFORMS.csv`,
`R10_10_FACE_ORIENTATION_ASSIGNMENTS.csv`, and the per-cycle holonomy
table inside `r1010.dual_graph.propagate()` output (all 12 cycles,
each length 5, each holonomy parity −1).
