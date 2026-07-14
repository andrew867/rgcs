# V2 Baseline Audit — RGCS v2.0.0

Agent 01 deliverable. Audit date: 2026-07-14. Auditor: Claude Fable 5
(automated), directed by internal-docs/plans-v3 prompt pack.
Baseline commit: `f9fd2c2`, tag `v2.0.0`, branch `main`.

## 1. Source reconstruction

The two supplied archives (`rgcs-v2-part1.zip`, `rgcs-v2-part2.zip`) were
extracted into a clean scratch tree and compared file-by-file (SHA256)
against the repository working tree.

| Check | Result |
|---|---|
| Files in combined archives | 232 (excluding caches/egg-info) |
| Files in repository tree | 233 (the extra file is `.gitignore`) |
| Present in archive, missing in repo | 0 |
| Content hash mismatches | 0 |

**Verdict: the repository tree is a byte-identical reconstruction of the
frozen v2 source archives.** No duplicate or contradictory source tree
remains (the extraction scratch copy lives outside the repository).

## 2. Release checksum verification

`release/SHA256SUMS.txt` lists 929 entries; 919 refer to the Linux
PyInstaller build tree (`release/linux/…`), which is intentionally not in
the repository (`.gitignore: release/linux/`, per v2 release layout).
All 10 entries whose files are present were verified:

- `PROVENANCE.json`, `QA_REPORT.md`, `RELEASE_NOTES.md`,
  `example_workspace_bundle.zip`, `rgcs_v2.pdf`,
  `rgcs_v2_manuscript_source_bundle.zip`, `rgcs-v2-src-2.0.0.zip`,
  `test_report.md`, `test_report_core.md`, `test_results.xml`
  — **10/10 SHA256 match, 0 mismatches.**

## 3. Test suite reproduction

Environment: Windows 11, Python 3.13.2, numpy 2.5.1, scipy 1.18.0,
pydantic 2.13.4, PySide6 (current), in a fresh `.venv`.
Release environment (from `release/PROVENANCE.json`): Linux,
Python 3.11.15, numpy 2.4.4, scipy 1.17.1.

Result: **223 passed, 4 failed — 227 total, matching the release-notes
count of 227 tests.**

### Explained discrepancies (4)

| Test | Cause | Class |
|---|---|---|
| `tests/regression/test_generator_determinism.py::test_generator_deterministic` | One regenerated golden CSV (`case_e_coupled_oscillators.csv`) differs from the checked-in copy at a single low-order digit (byte 986744, `8` vs `6`). Golden data was generated on Linux/Py3.11/numpy 2.4.4; this run used Windows/Py3.13/numpy 2.5.1. Last-ulp floating-point drift across numpy/scipy versions and platform libm. | Environment drift |
| `tests/integration/test_vertical_slice.py::test_step_4_define_experiment_validated_manifest` | Specimen combo empty on Windows — workspace object listing affected by the same OS-path-separator behaviour class as V2-WIN-01 below. | v2 Windows portability defect |
| `tests/integration/test_vertical_slice.py::test_step_4b_ethics_gate_blocks_human_loading` | Downstream of the same defect (depends on step-4 state). | v2 Windows portability defect |
| `tests/integration/test_vertical_slice.py::test_step_7_reproducibility_bundle` | **V2-WIN-01:** `rgcs_desktop/services/bundle.py` builds zip arcnames with `str(p.relative_to(ws.root))` → backslashes on Windows. `ZipFile.writestr` normalizes stored member names to `/`, but `CHECKSUMS.json` keys keep `\`, so `verify_bundle` raises `KeyError` on Windows. Harmless on Linux (release platform). | v2 Windows portability defect |

The v2 release notes explicitly state the release was **built and verified
on Linux only** with no Windows binaries; these Windows failures are
consistent with that declared limitation, not with baseline corruption.
Per the freeze rule, v2 code is NOT patched; V2-WIN-01 is carried into the
v3 defect intake (see `V2_TO_V3_MIGRATION_MAP.md`, item MIG-CODE-07).

### Baseline environment defect found

**V2-PKG-01:** `rgcs_desktop` imports `yaml` (`viewers/model_editor.py:10`)
but `pyproject.toml` does not declare `pyyaml` in any dependency group.
The Linux release binary bundled it via PyInstaller, masking the gap.
Recorded for v3 packaging fix; v2 files remain frozen.

## 4. Release-notes claims verified in source

| Claim | Verification | Result |
|---|---|---|
| 61 registered equations | `docs/model_registry.yaml`: 61 model entries, no duplicate IDs (RGCS-M.1 … RGCS-M.61) | ✅ |
| 14 pre-registered hypotheses | `docs/ROADMAP_TO_FALSIFICATION.md`: H-01…H-14 plus sub-variants H-01a, H-06a, H-08b (17 table rows) | ✅ |
| 227 automated tests | 227 collected/executed (223+4) | ✅ |
| QA-D-03 fix (unified φ₀ estimator) | `rgcs_core/coherence/metrics.py:76 initial_phase_estimate` present | ✅ |
| QA-D-04 fix (anti-Hermitian coupling K = i·2πg) | `rgcs_core/coupled_modes/static.py:135-158` documents and implements \|K\| = 2πg with anti-Hermitian structure; regression test `tests/regression/test_qa_d04_coupling_map.py` passes | ✅ |
| QA-D-05 fix (WorkspaceError + backup restore) | `rgcs_desktop/workspaces/workspace.py:43 WorkspaceError`, `:193 restore_latest_backup` | ✅ |
| QA-D-01/02 bibliography fixes | `manuscript/references.bib` carries corrected gan2025 / koster2026 entries | ✅ (spot-checked) |

## 5. Classification census (model registry)

Established 24, Derived 20, Hypothesis 8, plus 9 entries with explicit
mixed/conditioned labels (e.g. "Established (geometry) / Hypothesis
(relevance H-06)"). All 61 carry a classification string; none is blank.

## 6. Freeze actions taken

1. Pristine baseline committed (`f9fd2c2`) and tagged **`v2.0.0`**.
2. v2 release artifacts moved to `archive/v2.0.0/release/` (git-tracked
   move; content unchanged, hashes re-verified after move). The top-level
   `release/` directory is reserved for v3 outputs.
3. Freeze rule in force: **no later agent may modify anything under
   `archive/v2.0.0/` or rewrite the `v2.0.0` tag.** v2 docs under `docs/`
   evolve in place for v3; their frozen v2 state is recoverable from the
   tag and from `archive/v2.0.0/release/rgcs-v2-src-2.0.0.zip`.

## 7. Acceptance gate (Agent 01)

| Criterion | Status |
|---|---|
| Baseline tests reproduce or discrepancy explained | ✅ 223/227; 4 explained above |
| All 61 v2 equations accounted for | ✅ |
| All 14 v2 hypotheses accounted for | ✅ (14 + 3 sub-variants) |
| P1 QA fixes verified in source | ✅ all five (QA-D-01…05) |
| No duplicate/contradictory source tree | ✅ |
