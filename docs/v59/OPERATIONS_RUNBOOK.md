# Operations Runbook

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** Routine, repeatable operations — running tests, refreshing metadata, regenerating the workbook, running the firewall gate, cutting a release, restoring an archive.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [CONTRIBUTOR_ONBOARDING.md](./CONTRIBUTOR_ONBOARDING.md)
**Related code / tests / schemas:** [../../tools/v4x_release_metadata.py](../../tools/v4x_release_metadata.py), [../../tools/r4_release_gate.py](../../tools/r4_release_gate.py), [../../r10/firewall.py](../../r10/firewall.py), [../../docs/v4/RELEASE_METADATA.json](../../docs/v4/RELEASE_METADATA.json)
**Known limitations:** No apparatus and no measurements are involved in any operation here; hosted CI is unavailable, so the verification of record is always the local suite; operations assume Windows + PowerShell / Git Bash.
**Next review trigger:** A change to any tool invocation, the metadata schema, or the firewall policy.

All commands assume the quoted interpreter `.venv/Scripts/python.exe` (the path
contains spaces).

## Run the full test suite

```
".venv/Scripts/python.exe" -m pytest -q
```

This is the verification of record. See [TESTING.md](./TESTING.md).

## Refresh the release metadata / test count

```
".venv/Scripts/python.exe" tools/v4x_release_metadata.py --refresh
```

This runs the **full** suite, deselecting exactly
`tests/regression/test_generator_determinism.py::test_generator_deterministic`
(policy D-V3-04 — a byte-equality test that needs the archived build environment),
and writes the measured count to `docs/v4/RELEASE_METADATA.json`. Every documented
count site must then agree; the guard tests
[../../tests/v4/test_v4x_release_metadata.py](../../tests/v4/test_v4x_release_metadata.py)
and [../../tests/v4/test_v4c_docs_closeout.py](../../tests/v4/test_v4c_docs_closeout.py)
enforce this.

## Regenerate the workbook and run the release gate

```
".venv/Scripts/python.exe" tools/r4_release_gate.py --write
```

`--write` regenerates the workbook and then verifies the gate. A releasable state
reports the verdict **`TAG_MAY_PROCEED`**; otherwise it reports `REFUSE_TAG` and you
stop.

## Run the firewall gate (must be clean before any commit)

```
".venv/Scripts/python.exe" - <<'PY'
from pathlib import Path
from r10 import firewall
findings = firewall.scan_committed(Path("."))
print("CLEAN" if not findings else findings)
PY
```

`scan_committed` must return no findings. `firewall.enforce(...)` additionally checks
the working tree and (optionally) git history. Content-level claim checks live in
`r10/claimfirewall.py`. If the scan reports a leak, remove the offending content — do
not add it to the allowlist without an explicit policy decision.

## Cut a release

Follow [RELEASE_PROCESS.md](./RELEASE_PROCESS.md). In short: bump the version in all
sites, refresh metadata, regenerate the workbook, confirm `TAG_MAY_PROCEED`, revert
regenerated frozen baseline files, merge `--ff-only` to `main`, tag, and publish.

## Restore an archive

Release builds and frozen baselines are archived. To restore, check out the archived
artifact set for the target tag and re-run the suite on that commit; the suite
regenerates derived artifacts. Never hand-edit a restored baseline — regenerate it.

## Common hazards

- **Quote the interpreter path** — the space breaks unquoted invocations.
- **Regenerated frozen baselines** under `docs/v4/baseline/` are rewritten by the
  suite and must be **reverted** before committing a release.
- **Cloud-sync races** can corrupt artifacts mid-run; let a run finish before syncing.

PHYSICAL_VALIDATION_NOT_CLAIMED
