# R10.11 No-Fold Report

| Operator | Reversals | Params | Anchor max residual | Status |
|---|---|---|---|---|
| V1 Gaussian RBF | 0 (L6) | 627 warp steps | 0.0° | preserved historical calibrated profile |
| V2 direct-Montréal RBF | 361 (L6) | 868 steps | 0.0° (incl. Montréal) | preserved FAILED diagnostic; never promoted |
| Regular spherical midpoint | 0 | 0 | 16.55° | control |
| Param-Slerp (t=0.6515) | 0 | 1 | 15.33° | control (traversal-curved; not source-matched) |
| Möbius | 0 | 6 | 4.49° | control (global conformal; not source-matched) |
| Snyder-style equal-area approx | 0 | 0 | 16.85° | control (labelled approximation, not full ISEA) |
| **FLAT_FACE_NODE_CURVATURE (new)** | **0 (L5+L6)** | **24** | **4e-05°** | **source-matched candidate; convex; exact inverse** |

The new candidate meets every analytical no-fold condition of the
spec (convex base node set, positive child orientation, shared-edge
identity, single-valued outward lift, star-shaped shell) and fits the
three declared anchors essentially exactly with 26× fewer parameters
than V1's step count — with zero folds where V2's exact-anchor RBF
folded 361 times.

**Montréal remains excluded from the fit** (residual 45.93° if
evaluated): with its old-profile path 0.257° from Stonehenge's cell,
NO per-face smooth model can satisfy it — the tension lives in the
codec/decode layer (see the CYYT contradiction), not in map curvature.
V1 is NOT replaced in this phase: the new candidate becomes the
source-profile CANDIDATE alongside V1 pending codec resolution, since
its anchor semantics still depend on the demoted old structural
profile's paths.
