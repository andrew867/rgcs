# Contributor Onboarding

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** How a new contributor sets up the environment and learns the project's rules before touching code.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [../../README.md](../../README.md), [../../SCIENTIFIC_BOUNDARIES.md](../../SCIENTIFIC_BOUNDARIES.md), [../../CONTRIBUTING.md](../../CONTRIBUTING.md)
**Related code / tests / schemas:** [../../r10/](../../r10/), [../../tests/](../../tests/), [../../pyproject.toml](../../pyproject.toml)
**Known limitations:** Nothing here has been physically measured; all hardware is deferred; hosted CI is unavailable (free-tier GitHub Actions minutes are exhausted), so every contributor is expected to run the full suite locally.
**Next review trigger:** A change to the dependency set, the supported Python version, or the entry-point reading list.

## 1. What this project is (read first)

RGCS is a computational research programme. Its default output is a **refusal** or a
**null result**, not a positive claim. Before writing code, read the README and
`SCIENTIFIC_BOUNDARIES.md` end to end. You must be able to state, in your own words:

- the difference between an **established claim** and a **source-derived claim**;
- why **physical validation is never claimed** anywhere in this repository;
- what the **public/private firewall** protects and why.

If any of those three are unclear, do not open a pull request yet.

## 2. Environment setup

The project runs on Windows with **PowerShell** and **Git Bash**. The virtual
environment's interpreter lives at `.venv/Scripts/python.exe`. That path contains
spaces on most checkouts, so **always quote it**.

```
git clone <repository-url> RGCS
cd RGCS
python -m venv .venv
".venv/Scripts/python.exe" -m pip install -e ".[dev]"
```

Do not place the working tree inside a cloud-synced folder that rewrites files under
you during a test run; the suite regenerates baseline artifacts and a sync race can
corrupt them.

## 3. Run the tests

```
".venv/Scripts/python.exe" -m pytest -q
```

At the v5.8.0 baseline the suite is roughly **3340 tests**. Tests are organized in
tranches: `tests/v52/` (R10), `tests/v51/`, and `tests/v4/`. Every test is written so
that it **can fail**; see [TESTING.md](./TESTING.md).

## 4. Understand the claim discipline

Every typed record carries an **evidence class** (for example `SOURCE_CLAIM`,
`DERIVED_MATHEMATICS`, `HISTORICAL_FACT`, `CONVENTIONAL_LITERATURE`,
`SOURCE_REQUIREMENT`). There is **no auto-promotion** between classes. Records may be
marked `publication_class = PRIVATE_ONLY`. Details in [DATA_MODEL.md](./DATA_MODEL.md).

## 5. The public/private firewall

The public repository must never leak private-repository content. Enforcement is
structural (`r10/firewall.py`) and content-based (`r10/claimfirewall.py`). Before you
commit, the firewall scan must be clean — see the gate step in
[OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md). Never add personal names, private
place names, private filesystem paths, the private repository's literal name, or raw
signal digits to any public file.

## 6. Where to go next

- [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md) — routine operations.
- [RELEASE_PROCESS.md](./RELEASE_PROCESS.md) — how a version ships.
- [NULLS_AND_FALSIFICATION.md](./NULLS_AND_FALSIFICATION.md) — the result philosophy.
- [EXPERIMENT_HANDBOOK.md](./EXPERIMENT_HANDBOOK.md) — the specimen protocols.

PHYSICAL_VALIDATION_NOT_CLAIMED
