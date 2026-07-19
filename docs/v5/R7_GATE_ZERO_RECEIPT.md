# R7 Gate Zero Receipt (A00 / A01)

Programme: **RGCS v5.0 R7**. Baseline: **v4.9.0**.
Branch created: `v50-r7` from verified `origin/main`.

The pack's own baseline block was not trusted. Every line below was
reverified against the live repository.

## Identity

| Check | Result |
|---|---|
| `v4.9.0` dereferences to | `7847c2e34e186abe88b70868a062c2a063040405` |
| `origin/main` | `7847c2e…` |
| `main == tag` | yes |
| post-tag commits on `main` | 0 |
| working tree at branch point | clean |
| published release assets | 12 |
| repository visibility | **private** |

The pack's claimed baseline commit matches.

## Branch protection

Still unavailable, as recorded in the R6 receipt. The repository is
private on a plan without protected branches, so
`enforce_admins` cannot be verified or enforced. CI is triggered via a
pull request and observed green on the exact commit before tagging.
That is operator discipline, not a platform gate, and R7 inherits the
same documented deviation.

## Test baseline

The v4.9.0 recorded figure is 1840 passed with `dist/` absent. R7 adds
`tests/v50` to `testpaths` in the same commit that creates the
directory — the R6-D-001 defect (a new test directory silently
excluded from CI) is not repeated.

## Publication gate

R7 introduces a gate that did not exist in earlier programmes: no
public disclosure without a signed decision record. The decision is
recorded in `docs/v5/R7_PUBLICATION_DECISION.md` as **`PRIVATE_RC`**,
the only reversible path. The release agent will emit the private
token.

## Gate Zero verdict

**v4.9.0 is complete and remotely verified.** R7 proceeds on branch
`v50-r7`, privately.
