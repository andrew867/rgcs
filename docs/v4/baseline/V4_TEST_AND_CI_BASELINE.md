# V4 Test and CI Baseline (Agent B0)

## Local (LOCAL evidence — never claimed as hosted)

At baseline commit `2fed8fd`, before any completion-programme code:

- `pytest -q --deselect tests/regression/test_generator_determinism.py::test_generator_deterministic`
  → **471 passed, 1 deselected** (106.9 s, Windows/Py3.13). The
  deselected node is the v3 archived-environment byte-equality test
  (D-V3-04 policy; hosted CI deselects the same node).
- B0 scanner tests add 5 (tests/v4/test_v4c_baseline.py, 5 passed).

Static per-directory function counts: `V4_BASELINE_TEST_MATRIX.json`.

## Hosted CI (GitHub API evidence)

Run `29516325600` at head `2fed8fd`: **conclusion success** — 10 jobs
(portable ubuntu/windows/macos × py3.11/3.13, pinned reference,
v4-demo × 3 OS). This is the A1/A3 gate baseline: everything green
before completion-programme changes.

## Gate A1 status: PASS

Existing tests pass before v4-completion changes; the only dirty path
is untracked generated `release/v4/` assets (preserved, not absorbed).
