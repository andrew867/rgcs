# Reproducibility Audit — v3 (Agent 10)

**Date:** 2026-07-15. Platform: Windows 11, Python 3.13, numpy per
VERSIONS.json. The v2 audit is retained unchanged.

| Artifact | Regeneration | Result |
|---|---|---|
| Full test suite | `pytest -q` | 376 passed / 1 inherited (NR3-001) |
| RSCS registry consistency | fresh cross-resolution script | 40 ids, all modules resolve, all tested |
| CEP battery | live `run_all_cep()` | all_ok = True |
| `docs/generated/OPTICAL_MECHANISM_COMPARISON.md` | `--check` | byte-identical |
| Manuscript tables + macros | re-run `make_v3_artifacts.py` | byte-identical |
| Manuscript figures (PDF) | re-run | **DIFFER (CreationDate metadata) -> D-V3-02** |
| Experiment schemas | `validate.py` | 12/12 OK |
| Vertical slice (workspace->bundle) | in suite | 10/10 on Windows (first time; V2-WIN-01 fixed) |
| Corrupted-input behavior | fuzz (garbage/unknown-schema JSON) | all loud failures, no silent accepts |

Known non-portable artifact: golden CSV byte-equality (NR3-001) --
tolerance-checked semantics pass everywhere; byte-exactness only on the
Linux reference platform (deselected in Windows CI with justification).
Linux legs of CI are defined but not executed in this environment (gap
recorded in QA_REPORT_V3 section 4).
