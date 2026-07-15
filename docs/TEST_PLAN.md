# RGCS v2 — Test Plan

**Author:** Sub-Agent 09. **Date:** 2026-07-14.
**Current status:** 227/227 passing (`QT_QPA_PLATFORM=offscreen python3 -m
pytest`); machine-readable results in `release/test_results.xml`.

## 1. Suite structure

| Directory | Count | Purpose |
|---|---|---|
| `tests/unit` | 118 | Function-level contracts per core module + desktop services; provenance/classification lint; forbidden-vocabulary lint over `rgcs_core` **and** `rgcs_desktop` (QA-D-11); malformed-input handling; QA hardening suite (workspace corruption + restore, CSV/JSON loaders, metric edge guards) |
| `tests/property` | 17 | Hypothesis-based invariants: spectrum monotonicity, eigenvalue interlacing, circular-statistic bounds, shear-scalar invariances |
| `tests/golden` | 19 | Ledger Part E golden values recomputed live and compared exactly (Table 1 of the manuscript) |
| `tests/regression` | 50 | Every expected value of the golden coherence manifest recomputed from CSVs; generator determinism; performance guards; QA-D-04 coupling-map regression (2g splitting, growth-vs-frequency discrimination, old-map flag) |
| `tests/ui` | 13 | Offscreen smoke tests: every panel constructs, badges render, gates wire |
| `tests/integration` | 10 | `test_vertical_slice.py`: workspace → import → spectrum → experiment → job → results → bundle (quality gate 6); ethics gate |

## 2. How to run

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest             # full suite
python3 -m pytest tests/unit tests/property tests/golden tests/regression  # core-only
python3 -m pytest -m slow                               # dataset regeneration
python3 -m pytest --junitxml=release/test_results.xml   # machine-readable
```

Markers: `slow` (long-running dataset regeneration), `benchmark`
(non-gating performance checks).

## 3. Test design rules

1. Golden/expected values are **read from data files**
   (`golden_coherence/manifest.json`), never hard-coded in test bodies.
2. Randomized tests are seeded; property tests pin Hypothesis profiles.
3. Every defect fix ships with a regression test named after the defect
   (e.g. `test_qa_d04_coupling_map.py`, `test_qa_hardening.py`).
4. UI tests run headless (`QT_QPA_PLATFORM=offscreen`) and assert
   construction + wiring, not pixels.
5. Error-path coverage is mandatory for user-facing loaders: empty,
   header-only, binary, ragged, non-numeric, non-finite inputs must all
   raise a `ValueError` whose message a non-developer can act on.

## 4. Gate mapping

| Quality gate | Covering tests |
|---|---|
| 1 workbook parity | golden + unit (ported formulas); spreadsheet-only markings in `INCONSISTENCY_REGISTER.md` addendum |
| 2 generated numerics | regeneration byte-diff (QA procedure), `tools/` determinism tests |
| 3 suites pass | all of §1 |
| 4/5 classification & hypotheses | provenance lint tests; manuscript Table 9 |
| 6 desktop workflow | `tests/integration/test_vertical_slice.py` |
| 7 no forbidden claims | vocabulary lint (core + desktop) |
| 8 manuscript | `latexmk` log audit + page inspection (release checklist) |
| 9 artifacts | checksum/provenance scripts + bundle round-trip tests |

## 5. Known non-gating risks (tracked)

- QA-D-14: job cancellation is SIGTERM without SIGKILL escalation; shared
  progress queue could in principle wedge under mid-`put` termination.
  Verified clean in adversarial runs; documented limitation.
- QA-D-20/22/24/25: default-parameter and API-doc mismatches, blocking-call
  hygiene in one widget path — cosmetic, registered in DEFECT_REGISTER.md.

## v3 Agent 08 addendum

New gates: `tests/unit/test_rgcs_platform.py` (FEA contract round-trip +
tamper detection; crystal DB round-trip + migration failure modes; HG
persistence H-15/H-17/H-19 now machine-tested; provenance graph
determinism; waveform preview; V2-WIN-01 regression guard). CI matrix
(Linux+Windows x Py3.11/3.13) runs schema validation and generated-doc
freshness as gate steps; NR3-001 byte-equality is deselected on Windows
with documented justification (`.github/workflows/ci.yml`).
