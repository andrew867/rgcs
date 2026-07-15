# Contributing to RGCS / RSCS

Thank you for considering a contribution. This project has an unusual
discipline layer on top of ordinary open-source practice; the rules below
exist so that contributions cannot accidentally weaken the scientific
guarantees. They are checked by the test suite, not just by review.

## The three inviolables

1. **The frozen baseline is immutable.** Nothing under `archive/v2.0.0/`
   changes; the tag `v2.0.0` is never rewritten; the 61 frozen equations
   (`RGCS-M.1..61`, `docs/model_registry.yaml`) are never redefined.
   `git diff 715486b HEAD -- archive/v2.0.0` must stay empty.
2. **Every claim carries a classification.** Public functions in
   `rgcs_core` need the `@classified(...)` decorator (Established /
   Derived / Hypothesis / Source claim); RSCS operators need
   `@rscs_classified` with a registry id. Tests fail otherwise.
3. **New mathematics goes through governance.** A new RSCS coordinate or
   operator requires: an append to `docs/RSCS_NOTATION_LEDGER.md` §4, a
   `DECISION_LOG.md` entry, a row in
   `rscs_core/registry/rscs_registry.yaml` (units, class, provenance,
   tests), and at least one machine test — *before first use*. The
   registry is append-only: ids are never renumbered or reused.

## Ground rules

- **Conservative extension:** if your code generalizes a frozen v2
  result, add a regression test showing it reproduces the v2 numbers on
  the v2 domain (rtol 1e-9 / atol 1e-12; see
  `tests/regression/test_rscs_conservative_extension.py` for the pattern).
- **Coupling sign convention is frozen:** anti-Hermitian `K = i·2πg`
  (DECISION_LOG D3-007). A PR introducing any other convention will be
  declined regardless of code quality.
- **Safety envelope is a ceiling** (D7-003): no schema, preset, doc, or
  example may describe operation above 30 V / 3 A / 5 mJ per pulse /
  laser class 3R / 5 mW, and nothing may describe human exposure.
- **No number is hand-typed in a manuscript.** Extend
  `tools/make_v3_artifacts.py` instead.
- **Fail loud.** Invalid inputs raise; NaN/inf never propagate; unknown
  schema versions are errors, not guesses.

## Practical workflow

```bash
python3 -m pip install -e ".[desktop,dev]"
python3 -m pytest -q          # expect 376 passed, 1 documented failure
                              # (golden byte-equality, Linux-reference-only)
python experiments/schemas/validate.py
python tools/generate_optical_comparison.py --check
```

- Branch from `main`; keep PRs to one coherent change.
- Match the surrounding code style (PEP 8-ish, ~79 columns, docstrings
  that state units and classification).
- Update `CHANGELOG.md` and, if your change touches claims or registries,
  the relevant register (`CLAIM_REGISTER.md`, `TRACEABILITY_MATRIX.md`).
- CI runs Linux + Windows × Python 3.11/3.13; both must pass.

## What contributions are most welcome

- Running the bench campaigns (H-20..H-30) and reporting results —
  **negative results are first-class contributions** and go in
  `docs/NEGATIVE_RESULTS.md`.
- T2 desktop panels over the existing tested headless services.
- FEA import scripts consuming `rgcs_core.fea_export` documents.
- Portability reports from platforms we haven't run.
- Documentation clarity fixes (this file included).

## What will be declined

- Class upgrades without registered experimental evidence.
- Physical-conclusion transfer by analogy from the source papers
  (the `forbidden_transfer` column of
  `references/equation_provenance.yaml` is binding).
- Anything presenting a Hypothesis or Source claim as fact, anywhere.
