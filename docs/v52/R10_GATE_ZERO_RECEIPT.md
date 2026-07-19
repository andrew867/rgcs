# R9.2 / R10 — Gate Zero Receipt (P00)

**Date:** 2026-07-19
**Baseline tag:** `v5.2.1`
**Baseline commit:** `8cadec2`
**Branch:** `main` (fast-forwarded from `v52-r9`)
**Repository visibility:** PUBLIC

---

## Branch reconciliation

The pack refers to an operator-reported `v52-r9` branch. That branch was
completed, merged fast-forward into `main`, tagged, and released:

| Tag | Commit | CI | Note |
|---|---|---|---|
| `v5.2.0` | `f40f4a8` | **red** | packaging guard could not collect without setuptools (R9-D-020) |
| `v5.2.1` | `8cadec2` | **green, 10/10** | current baseline |

`v5.2.0` is immutable and stays as cut. `v5.2.1` supersedes it and says
why in its own release notes rather than replacing it quietly.

## Test baseline

```bash
git clone https://github.com/andrew867/rgcs && cd rgcs
pip install -e ".[dev]"
pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic
# 2564 passed, 11 skipped, 1 deselected
```

Clean-clone count is authoritative. A full working copy reports more
(2569) because several tests need optional untracked content.

## Working tree

Clean. No untracked files, no uncommitted changes, no active worktrees.
The tree is reconstructible from the tag without guessing, so P00's stop
condition does not trigger.

## Inherited defects — status at Gate Zero

The pack's P01–P04 target defects inherited from R9. Most were closed
during the R9 closeout, before this pack was read:

| Phase | Subject | Status entering R10 |
|---|---|---|
| P01 | generator determinism | **Not a defect.** See below. |
| P02 | neutrino rate normalisation | **Closed** (R9-D-018), anchored to Borexino; ~10× correction applied |
| P03 | packaging / provenance parity | **Partly closed** (R9-D-003/004/020); wheel and sdist parity still to do |
| P04 | inferential-test power | **Closed** (R9-D-007/008/009); register audit reports 5 of 8 tests live |

### P01 — the determinism "failure" is not a defect

`test_generator_deterministic` requires the archived v2.0.0 build
environment (Python 3.11.15, numpy 2.4.4, scipy 1.17.1 and its libm),
and hosted CI **deliberately deselects that exact node id** under policy
D-V3-04. Its portable sibling `test_generator_numerically_equivalent`
runs on every platform and passes.

Running it on Python 3.13.2 with current numpy/scipy produces last-digit
drift, which is the documented and expected outcome. There is no
nondeterminism to root-cause; the test is doing what it was designed to
do. **P01 should be re-scoped to confirming that documentation, rather
than hunting a bug that does not exist.**

## Privacy boundary

Public-tree scan for prohibited personal terms: **clean** (0 hits across
`r6`–`r9`, `docs/`, `README.md`, `CHANGELOG.md`).

CW vectors are referenced only as originating from the omega region, at
region granularity, and no analysis step depends on provenance.

## Blocking gap: private source root is absent

`RGCS_PRIVATE_SOURCE_ROOT` is **unset**, and no default private root
exists on this machine.

This gates:

- **P05** (`144.000` source-frame ontology) — the pack requires the
  source frame with its timestamp, URL, screenshot hash, and visible
  unit/context. Without it, `144.000` cannot be typed, and the pack's own
  rule is to treat it as an untyped decimal until metadata proves a unit.
  The locale-separator reading (`144.000` = 144 000) cannot be excluded
  either.
- **P06/P07** partially — the five CW vectors are already present in the
  public tree as anonymised fixtures, so the exact-arithmetic and
  codebook work can proceed; only source-corpus context is unavailable.

No private material has been copied into the repository, and none will
be. This gap is recorded rather than worked around.
