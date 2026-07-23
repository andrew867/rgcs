# Release Process

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** The exact steps to ship a versioned release, including the count/metadata invariants and the current local-only verification constraint.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md), [TESTING.md](./TESTING.md)
**Related code / tests / schemas:** [../../tools/v4x_release_metadata.py](../../tools/v4x_release_metadata.py), [../../tools/r4_release_gate.py](../../tools/r4_release_gate.py), [../../tests/v4/test_v4x_release_metadata.py](../../tests/v4/test_v4x_release_metadata.py), [../../tests/v4/test_v4c_docs_closeout.py](../../tests/v4/test_v4c_docs_closeout.py), [../../docs/v4/RELEASE_METADATA.json](../../docs/v4/RELEASE_METADATA.json)
**Known limitations:** Hosted CI is unavailable — the free-tier GitHub Actions minutes are exhausted — so the verification of record is the full **local** suite on the exact release commit. Nothing in a release asserts a physical measurement.
**Next review trigger:** CI minutes become available again, or any change to the version-bump sites or the release tooling.

## Version-bump sites (all must agree)

Bump the version string in **every** one of these:

- [../../pyproject.toml](../../pyproject.toml)
- [../../CITATION.cff](../../CITATION.cff)
- [../../README.md](../../README.md)
- [../../CHANGELOG.md](../../CHANGELOG.md)
- the guard tests
  [../../tests/v4/test_v4c_docs_closeout.py](../../tests/v4/test_v4c_docs_closeout.py)
  and [../../tests/v4/test_v4x_release_metadata.py](../../tests/v4/test_v4x_release_metadata.py)

The guard tests fail the build if any site disagrees. This exists because a version or
count once lived only in prose and drifted; the count and version are now measured and
asserted.

## Steps

1. **Bump** the version in all sites above.
2. **Refresh the count/metadata:**
   ```
   ".venv/Scripts/python.exe" tools/v4x_release_metadata.py --refresh
   ```
   This runs the full suite, deselecting exactly
   `tests/regression/test_generator_determinism.py::test_generator_deterministic`
   (policy D-V3-04), and writes the measured count to
   `docs/v4/RELEASE_METADATA.json`. Every documented count site must match it.
3. **Regenerate the workbook and run the gate:**
   ```
   ".venv/Scripts/python.exe" tools/r4_release_gate.py --write
   ```
   Proceed only on verdict **`TAG_MAY_PROCEED`**.
4. **Run the firewall gate** (see [OPERATIONS_RUNBOOK.md](./OPERATIONS_RUNBOOK.md));
   `firewall.scan_committed(...)` must be clean.
5. **Revert regenerated frozen baselines.** The suite rewrites frozen files under
   `docs/v4/baseline/`; revert them so the release commit carries the canonical
   frozen copies, not run-local regenerations.
6. **Merge** the release branch into `main` with `--ff-only`.
7. **Tag** `vX.Y.Z` on the merge commit.
8. **Publish** with `gh release create vX.Y.Z` and the release notes.

## Verification of record

Because hosted CI cannot run, the authoritative evidence a release passed is the
**full local suite on the exact tagged commit**. Record the measured summary line in
`docs/v4/RELEASE_METADATA.json` (it captures passed/skipped/deselected counts and the
run time). Do not tag a commit whose local suite you have not run.

## What a release does not assert

A release ships code, documentation, and null/refusal results. It does **not** assert
any physical measurement, calibration, or hardware validation.

PHYSICAL_VALIDATION_NOT_CLAIMED
