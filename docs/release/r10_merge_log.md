# R10 Public Consolidation Merge Log

Baseline `main`: `8077e04395b04464ad57d99a4b6b49e6b72a2e60`

Release-control inventory/filter commit: `2cb48397f9a9de031ceebdf2c576bb100b32ba52`

No worktree was deleted, no push was performed, and no tag was created during consolidation.

## Public Engineering Lane

The source branch `claude/rgcs-r10-62-terminal-vertex-4aca40` was **not merged**. Its 37-commit delta contains both public engineering work and private decode/privacy lanes. A clean branch, `release/r10-public-engineering`, was created from `main`; only these audited commits were replayed:

| Source commit | Replayed commit | Scope |
|---|---|---|
| `35312e29c8db1b164975991b1df07a8c8653cd47` | `20d9588` | R10.71 public Phyrll/Terra v0.6 |
| `4e762851d083c31238f582b4b29497943a1a0407` | `47977a8` | R10.72 public engineering v0.7 |
| `a10a3bb11a1c05fd6f7676a97ac12b3417d877ec` | `64b2ab4` | composed loading and phase-lag sweep |
| `710e5947c80ea7a2299dc0a40fd63a4262891e39` | `24af887` | R10.73 authority bench-drive specification |

The replay exposed an import dependency on an unapproved R10.70 package. Commit `561d00f80b79fc0b45f39410d6811055578163d5` retained the bounded subtraction-control API locally, removed the mixed-lane dependency, and expanded the existing filter to content scanning over every required term.

Focused command:

```text
python -m pytest tests/test_miami_bermuda_calibration.py tests/test_phyrll_v06_annular_proxy.py tests/test_phyrll_v06_coefficients.py tests/test_phyrll_v06_resonance.py tests/test_phyrll_v06_ring37.py tests/test_terra_public_release_filter.py tests/test_phyrll_v07_engineering.py tests/test_phyrll_v07_composed_sweep.py tests/test_phyrll_v07_bench_drive.py tests/v51/test_r8_source_coverage.py tests/release/test_r10_public_release.py -q --basetemp build/pytest-r1071-r1073-postmerge
```

Pre-merge: **155 passed** in 10.434 seconds. Post-merge: **155 passed** in 12.108 seconds.

Merged with `--no-ff` at `dd298d6d471c1b8810aca0c2d0f48234a24aefc5`.

## R10.74 ARDK Lane

`rcw-public-workbench` contained one public delta, source commit `dfab636c4bf5e165103d7ebc72a693ef828b9987`. Registry conflicts were resolved by keeping every consolidated package/test root and adding `rgcs_ardk`. The R10.74 numerical and test-environment fixes were retained.

Focused command:

```text
python -m pytest rgcs_ardk/tests tests/v51/test_r8_source_coverage.py tests/v6/test_r13_floquet.py -q --basetemp build/pytest-r1074-merge
```

The first invocation reached 68 passed and then reported three setup errors because the ignored `build` parent did not exist. After creating that writable parent, the identical command passed: **71 passed** in 3.188 seconds.

Merged with `--no-ff` at `f2034069adccdf6cf7620d42dab240337b7723ac`.

## Not Merged

- `claude/rgcs-r10-62-terminal-vertex-4aca40`: quarantine; mixed public/private delta.
- `release-safety-snapshot-20260803-2105`: retained as an immutable safety pointer.
- `program/r10-9-variable-depth`, `program/r10-10-face-orientation`, `program/r10-11-flat-face-codec`: private research lanes.
- Historical branches already contained in the Phase 0 `main`: no delta to merge.
- Every branch in `r10_review_queue.md`: unresolved review status.
