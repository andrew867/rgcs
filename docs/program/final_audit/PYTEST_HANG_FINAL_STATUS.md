# Pytest Hang Final Status

Date: 2026-07-26

Audit worktree: `audit-worktree`

Base commit: `b84e6eb4608b55b951270e07d3af3ffb08f96a61`

## Final Status

Closed: no repository pytest teardown hang was reproduced.

Current classification:

```text
NO_REPOSITORY_PYTEST_TEARDOWN_HANG_FOUND
DEFAULT_WINDOWS_TEMP_ROOT_ACL_PROBLEM_FOUND
```

## Evidence

The default `tests\rgcs_lab` run exited instead of hanging:

```text
python -m pytest tests\rgcs_lab -q
52 passed, 3 errors in 8.70s
EXIT_CODE=1
ELAPSED_SECONDS=10.96
```

The three errors were all setup-time `tmp_path` failures:

```text
PermissionError: [WinError 5] Access is denied:
'C:\Users\andrew\AppData\Local\Temp\pytest-of-andrew'
```

The same suite passes when pytest is given a writable temp root inside the
fresh audit worktree:

```text
python -m pytest tests\rgcs_lab -q --basetemp .pytest-basetemp
55 passed in 3.16s
EXIT_CODE=0
ELAPSED_SECONDS=4.209
```

The same suite also passes with plugin autoload disabled and only
`faulthandler` loaded:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests\rgcs_lab -q -p faulthandler --basetemp .pytest-basetemp-noplugins
55 passed in 2.62s
EXIT_CODE=0
ELAPSED_SECONDS=3.333
```

## Relationship To Prior Investigation

The integration branch already contained
`docs/program/integration/CODEX_PYTEST_HANG_INVESTIGATION.md`, which reported
that a clean Windows environment ran `tests\rgcs_lab` normally and classified
the original Codex-side hang as harness-specific rather than a repository leak.

This fresh audit worktree independently confirms the important boundary:

- no hang was reproduced;
- with a writable `--basetemp`, the test suite exits cleanly;
- with plugin autoload disabled, the test suite exits cleanly;
- the present failing condition is an ACL denial on pytest's default temp root.

## Disposition

No repository code change is indicated for a teardown hang.

Operational workaround for this machine:

```bash
python -m pytest tests\rgcs_lab -q --basetemp .pytest-basetemp
```

Recommended local cleanup outside this audit:

```text
repair or remove the inaccessible C:\Users\andrew\AppData\Local\Temp\pytest-of-andrew tree
```

