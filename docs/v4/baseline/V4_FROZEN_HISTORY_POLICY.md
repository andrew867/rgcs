# V4 Frozen History Policy (Agent B0)

Binding on every workstream of the completion programme.

1. Tags `v2.0.0`, `v3.0.0`, `v3.0.0-rc1`, `v3.0.1`, `v4.0.0-alpha`,
   `v4.0.0-rc1`, `v4.0.0` are immutable. No retag, no force-push, no
   deletion, no asset replacement. Tree hashes recorded in
   `V4_FROZEN_ARTIFACT_CHECKSUMS.json` are the comparison anchors.
2. `archive/v2.0.0/` never changes:
   `git diff --stat 715486b HEAD -- archive/v2.0.0` must stay empty
   (checked by `tools/qa_audit_v4.py` and again by Q1).
3. Frozen registries (RGCS-M.*, RSCS-C.*, RSCS-O.*) and published v3
   equations never change meaning. `rscs2_core/registry/
   rscs2_registry.yaml` is append-only.
4. The published v4.0.0 proof bundle semantics (verdict
   CONVENTIONAL_NODE_FOUND) may be EXPANDED with new NOT_APPLICABLE
   records and additional diagnostics, never silently altered; any
   verdict change must come from the engine with full evidence.
5. FEM authority commits `9165594`, `7962817`, `3fcb0d7` (all verified
   reachable) define the validated mass/stiffness forms; changes
   adjacent to `rscs2_core/fem.py` require re-running
   `tests/v4/test_rscs2_solver.py` and the mass-patch audit before
   commit.
6. Prior Zenodo records (10.5281/zenodo.21387946/47) are never edited
   by this programme.
7. Release assets for this programme are NEW (`v4.1.0-rc1`, `v4.1.0`,
   DV4C-002); they never overwrite v4.0.0 assets.
