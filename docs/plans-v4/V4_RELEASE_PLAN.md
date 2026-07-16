# V4 Release Plan

**Status:** PLANNING. Reuses the proven v3 release machinery
(`tools/build_v3_release.py` pattern → a `build_v4_release.py`,
GitHub+Zenodo, SHA256SUMS, PROVENANCE). Tags are immutable; v2/v3 never
rewritten.

## 1. Release ladder (partial releases ship value early)

| Tag | After | Contents | Gate |
|---|---|---|---|
| `v4.0.0-alpha0` | M2 | meshing toolkit (import/mesh/tags/manifests) | mesh determinism |
| `v4.0.0-alpha` | M3 | **CPU elastic solver + benchmarks (MVP)** | V.2/V.3/V.8 green |
| `v4.0.0-beta` | M4/M6 | crystal multiphysics + eye diagnostics | V.6/V.9 green; eye NULL-capable |
| `v4.0.0-rc` | M7 | validated (fork+cantilever) + inverse | V.4 + MAC + null-model |
| `v4.0.0` | M8 | full platform | full gate table GREEN |

Each pre-release is a real, installable, CPU-usable artifact — not a
placeholder.

## 2. Per-release procedure (mirrors v3)

1. green CI on main (3-OS CPU matrix + reference + optional GPU).
2. version-flip commit (pyproject, CITATION.cff, `__version__`s,
   release builder VERSION, release notes) → push → wait green.
3. build artifacts from the version commit (source zip w/o nested zips —
   the D-release-zip lesson: `release/*.zip` stays git-ignored),
   manuscripts bundle, sample projects bundle, PROVENANCE, SHA256SUMS.
4. tag `v4.x.y` (annotated) → push.
5. GitHub release with assets; verify sizes/checksums.
6. Zenodo auto-archives (integration already live) → DOI → CITATION.cff
   + README badge follow-up commit.

## 3. Release-gate table (v4.0.0)

Reuses the v3 12-gate structure, adds v4 rows: conservative-extension
anchors (V.6/V.9), mandatory benchmarks (V.2/V.3/V.4), GPU-status
honesty (no unearned benchmark claim), eye-diagnostic non-EST + NULL
capability, dataset-licence cleanliness, CPU-only-usable confirmation.
**Any red anchor or mandatory benchmark blocks the tag.**

## 4. What ships / what does not

- **Ships:** source, CPU-usable package, benchmarks, manuscripts,
  sample projects, provenance, checksums.
- **Ships experimental:** GPU backends (status-labelled), optional 4th
  reference system, wave-optics/EM integration contracts (not solvers).
- **Never ships:** a GPU speed claim without hardware; an eye result as
  EST; any high-power/human-exposure content; a dataset without a usable
  licence; a modified frozen artifact.

## 5. Known-limitations statement (every release)

Honest list, v3-style: no physical confirmation; GPU status per ladder;
staged fidelity (which levels are in); optional-dependency features;
byte-exact reproduction scoped to the reference environment
(tolerance-aware elsewhere). CPU authority and reproducibility are the
guarantees; performance and physics confirmation are not.
