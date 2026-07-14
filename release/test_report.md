# RGCS v2 — Release Test Report

- report_id: test_report_release
- author: Sub-Agent 09 (Integration, Release, and Public Package)
- date: 2026-07-14
- package: rgcs-v2 2.0.0 (rgcs_core + rgcs_desktop)
- machine-readable results: `release/test_results.xml` (JUnit XML)
- companion: `release/test_report_core.md` (core-only report, Sub-Agent 04)
- environment: Linux x86_64; Python 3.11.15; numpy 2.4.4; scipy 1.17.1;
  pydantic 2.13.3; PySide6 6.11.1; pytest 9.1.1; hypothesis 6.156.6;
  `QT_QPA_PLATFORM=offscreen`

## Result summary

```yaml
command: QT_QPA_PLATFORM=offscreen python3 -m pytest --junitxml=release/test_results.xml
status: PASS
total: 227
passed: 227
failed: 0
errors: 0
skipped: 0
slow_marker: 1 passed (dataset regeneration, run separately with -m slow)
breakdown:
  unit: 118
  property: 17
  golden: 19
  regression: 50
  ui: 13
  integration: 10
```

## Delta vs QA baseline (203 tests, 2026-07-14 QA run)

24 tests added by the release-integration pass, all defect-driven:

- `tests/regression/test_qa_d04_coupling_map.py` (3): corrected coupling
  map |K| = 2πg reproduces the 2g frequency splitting and the beat node
  for a degenerate pair; real-symmetric coupling shown to split growth
  rates, not frequencies (the pre-correction failure mode, pinned); the
  old K = πg map now trips the pre-registered warning flag.
- `tests/unit/test_qa_hardening.py` (20): workspace corruption ×3 →
  `WorkspaceError`; corrupt db never archived as backup; backup restore
  round-trip; restore-without-backups error; CSV loader 7-case
  malformed-input matrix incl. NaN/inf rejection; manifest JSON error
  reporting ×2; coherence metric edge guards ×4; unified initial-phase
  estimator.
- `tests/unit/test_experiments_provenance.py` (+1): forbidden-vocabulary
  lint extended to `rgcs_desktop` (QA-D-11).

One pre-existing test updated for the corrected physics
(`test_coupling_consistency_k_equals_two_pi_g`, was `..._pi_g`), plus the
`coupling_rate_s` assertion in `test_two_mode_mixing_and_strong_coupling`.

## Determinism

The full suite was run three times during integration (before fixes: 203
green twice per QA; after fixes: 227 green on consecutive runs, including
the junit-producing run). No flaky tests observed; all randomness seeded.
