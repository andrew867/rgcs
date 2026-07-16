# Reproduction

One deterministic command (from the repo root, venv active):

    python -m rscs2_core.proofbundle

Regenerates this bundle at ./proof_bundle_110mm (pass an argument for
a different output directory; `--fast` uses coarser meshes for smoke
testing). Seed 20260716; gmsh meshes are deterministic (hashes in
geometry/geometry_hashes.json must match). Copied hardware-dependent
artifacts (acceleration/, benchmarks/tuning_fork.csv) come from the
committed evidence tree and are listed in PROVENANCE.json.
Verify integrity: sha256sum -c SHA256SUMS.txt
