# R6 Gate Zero Receipt (A00 / A01)

Programme: **RGCS v4.9 R6**. Baseline: **v4.8.1**.
Branch created: `v49-r6` from verified `origin/main`.

Nothing in the pack's `V48_1_BASELINE_SNAPSHOT.md` was trusted. Every
line below was reverified against the live repository and against
assets downloaded fresh from the release.

## Tag and branch identity

| Check | Result |
|---|---|
| `v4.8.1` dereferences to | `661d406e2bb6cb214bb39521076ddc20705b69b2` |
| tag object type | annotated (`git cat-file -t` → `tag`) |
| `main` | `661d406e…` |
| `origin/main` | `661d406e…` |
| `main == tag` | yes |
| post-tag commits on `main` | 0 |

The pack's claimed baseline commit matches. Note that `git rev-parse
v4.8.1` returns `b6af7475…`, the *annotated tag object*, not the
commit; the commit requires `v4.8.1^{commit}`. Comparing the raw
`rev-parse` output against a commit id would falsely report a
mismatch.

## Remote asset verification

All eleven published assets were downloaded and checked against the
published `SHA256SUMS.txt`:

```
rgcs-v4.8.1-source.zip              OK
rgcs-v4.8.1-proof-bundle.zip        OK
rgcs-v4.8.1-manuscripts.zip         OK
rgcs-v4.8.1-reference-systems.zip   OK
rgcs-v4.8.1-screenshots.zip         OK
rgcs-v4.8.1-example-workspace.zip   OK
rgcs-v4.8.1-test-report.txt         OK
PROVENANCE.json                     OK
RGCS-Workbench-4.8.1-…-portable.zip OK
RGCS-Workbench-4.8.1-…-Setup.exe    OK
RGCS_Master_Evidence_Workbook.xlsx  OK
```

## Binary provenance stamp

Extracted from the published portable ZIP
(`RGCSWorkbench/_internal/_build_stamp.json`):

```json
{
  "version": "4.8.1",
  "git_commit": "661d406e2bb6cb214bb39521076ddc20705b69b2",
  "source_hash": "dbe23fb4adf4b8fdc3aae809046fef7a13cb5ff6492a8c4d356a3c9c65bad19c",
  "built_at": "2026-07-18T20:50:14+00:00"
}
```

The stamped commit equals the tag commit. The v4.5.2 anti-stale
mechanism holds for this release.

## Published workbook

- 28 sheets, matching the reported count.
- `R4 Codec` sheet carries 18 columns including `negative_control` and
  `beats_any_baseline` — the v4.8.1 column-loss fix is present *in the
  published artifact*, not merely in source.
- `R4 Platforms` carries 20 columns including `open_gates` and
  `limitations`.

## Test count reconciliation

| Condition | Passed | Skipped |
|---|---|---|
| recorded in `RELEASE_METADATA.json` (CI, `dist/` absent) | 1219 | 6 |
| this machine, `dist/` present, pre-R6 | 1223 | 2 |

The delta is +4 passed / −4 skipped: four frozen-binary tests in
`tests/v4/test_v45_frozen.py` skip when `dist/` is absent and run when
it is present. The recorded metadata reconciles.

## Defect found during Gate Zero

**R6-D-001 — `tests/v49` was outside `testpaths`.**

`pyproject.toml` pinned `testpaths` to an explicit list ending at
`tests/v4`. A new `tests/v49` directory is collected when named
explicitly on the command line but is **silently skipped** by a bare
`pytest` run — which is what CI runs. Every R6 test would have passed
locally and never executed in CI.

Fixed by appending `"tests/v49"` to `testpaths`. Collection now
reports 1246 tests, of which 20 are R6.

This is the same failure family as the v4.8.1 workbook column loss: a
mechanism that reports success while silently covering less than it
appears to.

## Deviation from R4 release law: branch protection

R4 released with `enforce_admins` ON. That is **not currently
verifiable or enforceable**:

```
$ gh api repos/andrew867/rgcs/branches/main/protection
HTTP 403: Upgrade to GitHub Pro or make this repository public to
enable this feature.
```

The repository is now **private** on a plan without protected
branches. Consequences, stated plainly:

- step 5 of the R4 release procedure ("pass protected CI") cannot be
  *enforced* by the platform during R6;
- CI can still be run and its result verified before tagging, but that
  is operator discipline, not a technical gate;
- no claim of branch protection may appear in R6 release notes.

R6 substitutes an explicit pre-tag verification step: CI must be
observed green on the exact commit to be tagged, and the observation
recorded in the release receipt. This is weaker than `enforce_admins`
and is documented as weaker.

## Gate Zero verdict

**R4 is complete and remotely verified.** The boundary condition in
A00 ("if R4 is not complete and remotely verified, stop") is
satisfied. R6 proceeds on branch `v49-r6`.
