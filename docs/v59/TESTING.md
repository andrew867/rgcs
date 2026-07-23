# Testing

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** The testing philosophy and layout — why every test must be able to fail, and what null-power and refusal tests guarantee.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [CONTRIBUTOR_ONBOARDING.md](./CONTRIBUTOR_ONBOARDING.md), [NULLS_AND_FALSIFICATION.md](./NULLS_AND_FALSIFICATION.md)
**Related code / tests / schemas:** [../../tests/v52/](../../tests/v52/), [../../tests/v51/](../../tests/v51/), [../../tests/v4/](../../tests/v4/), [../../docs/v4/RELEASE_METADATA.json](../../docs/v4/RELEASE_METADATA.json)
**Known limitations:** Tests exercise computation only — no measurement, no hardware, no physical validation. Hosted CI is unavailable, so the local run is the verification of record.
**Next review trigger:** A new module lands, or the null-power / refusal test contract changes.

## Core principle: every test must be able to fail

A test that cannot fail proves nothing. Each module therefore ships:

1. **Focused tests** for its own behavior;
2. a **null-power test** — a planted signal is injected and the pipeline is required
   to **recover** it, proving the method has power to detect a real effect;
3. a **refusal test** — the module is required to **refuse** to emit a positive claim
   under the conditions where it should (missing custody, unpreregistered endpoint,
   promotion across evidence classes, and so on).

The **default output of a module is a refusal or a null.** A positive result is the
exception and must survive both the null-power test (the method can see a signal) and
the refusal test (the method declines when it should).

## Layout

Tests are organized in tranches:

- [../../tests/v52/](../../tests/v52/) — R10 modules (`test_r10_*.py`).
- [../../tests/v51/](../../tests/v51/) — prior tranche.
- [../../tests/v4/](../../tests/v4/) — v4 tranche, including the release guard tests.

## Running

```
".venv/Scripts/python.exe" -m pytest -q
```

Quote the interpreter path (it contains spaces). At the v5.8.0 baseline the suite is
roughly **3340 tests**. The measured summary is written to
`docs/v4/RELEASE_METADATA.json` by the metadata tool; see
[RELEASE_PROCESS.md](./RELEASE_PROCESS.md).

## Deselected node

The metadata refresh deselects exactly
`tests/regression/test_generator_determinism.py::test_generator_deterministic`
(policy D-V3-04): it is a byte-equality test that requires the archived build
environment, and hosted CI deselects the same node id. It is deselected only for the
metadata count run — a normal `pytest -q` still collects it.

## Writing a new test

- Make it capable of failing — assert a specific outcome, not a tautology.
- If the module can emit a positive claim, add a **null-power** test that plants a
  known effect and requires recovery, and a **refusal** test for the decline path.
- Never assert a physical measurement; assert computational behavior only.

PHYSICAL_VALIDATION_NOT_CLAIMED
