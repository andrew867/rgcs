# Codex pytest teardown hang — investigation (2026-07-26)

## Reported symptom

Codex reported that all 11 focused test bodies reached 100% but pytest
hung during teardown/reporting on Windows. Flagged YELLOW pending
diagnosis.

## Environment used for this investigation

- Windows 11 Enterprise 10.0.26200, Python 3.13.2 (fresh venv at
  `%LOCALAPPDATA%\rgcs-int-venv`, outside OneDrive)
- pytest 9.x, hypothesis, numpy/scipy, fastapi/httpx/uvicorn, jsonschema
- Integration tree at `program/integration` (post-Codex merge), repo
  itself under a OneDrive-synced path (deliberately, to expose OneDrive
  file-lock interactions)

## Prescribed matrix — results

| # | Step | Result |
|---|---|---|
| 1 | `pytest tests/rgcs_lab -vv -s --setup-show` | 36 passed, exited normally, exit 0 (1.6 s) |
| 2 | `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest tests/rgcs_lab -q -p faulthandler` | 36 passed, exit 0 — no plugin-autoload dependency |
| 3 | One file at a time (all 9 files) | every file passed and exited normally |
| 4 | faulthandler enabled (pytest's built-in; no `-X dev` hang ever reached a dump) | no timeout ever triggered |
| 5 | Non-daemon thread inspection: in-process `pytest.main()` with an `atexit` thread dump | only `MainThread daemon=False` alive at interpreter exit — **no leaked threads** |
| 6 | FastAPI/HTTP/executor/multiprocessing/logging resources | TestClient-based API tests run in step 1–3; no lingering sockets or executors observed (thread dump above is the evidence) |
| 7 | `tmp_path` / OneDrive / cleanup | `-p no:cacheprovider` run also clean; suite passes with the repo under OneDrive; no `tmp_path` teardown stalls |
| 8 | Source tree vs installed wheel | wheel installed into a second clean venv outside the repo; every CLI module plus `rgcs-lab serve` ran and exited normally |
| 9 | With `pytest-qt` + `PySide6` installed (the repo dev extra and the usual Windows teardown-hang suspect) | 36 passed, exit 0 (2.7 s) |

Additionally the full repository suite (`pytest tests -q`) completes and
exits normally in this environment (see TEST_RECEIPT.json).

## Classification

**Environment (Codex harness), not a repository leak.**

- Repository exonerated: with the same test files, same OS family, and a
  clean interpreter, pytest exits normally under every prescribed
  variation, and the post-run thread dump shows no non-daemon thread
  other than MainThread. There is nothing in `tests/rgcs_lab` or the
  imported modules that can hold the process open here.
- The hang is therefore attributable to the reporting/teardown phase of
  the Codex agent's own sandboxed harness (its pytest wrapper, output
  piping, or process supervision), or to a plugin present only in that
  environment. It was not reproducible from the repository contents.
- Residual uncertainty: the exact Codex-side component was not observed
  directly (that environment is not available here), so the cause within
  the Codex harness remains unidentified — but the classification
  boundary (environment vs repository) is established by evidence.

## Status disposition

The YELLOW attached to "tests may hang on Windows" is lifted for this
repository: focused tests **complete normally** (the receipt-promotion
requirement). No pytest plugin was silenced, no timeout was added to
mask the symptom, and `pyproject.toml` pytest settings conceal nothing.
If a future harness reproduces a hang, re-run steps 1–5 above; step 5's
thread dump is the decisive discriminator between a repository leak and
harness supervision.
