# Codex Numerical Audit

Date: 2026-07-26

Audit worktree: `audit-worktree`

Audit branch: `program/codex-numerical-audit`

Base commit: `b84e6eb4608b55b951270e07d3af3ffb08f96a61`

Scope: independent post-merge verification of Codex-owned numerical cores,
receipts, CLI behavior, installed-wheel behavior, and Windows pytest teardown
status. This audit did not run in the completed implementation branches.

## Summary

Verdict: PASS with one environment caveat.

The numerical core checks passed for Golay correction, quaternion algebra,
memory benchmark determinism and equal budgets, dual-pole transitions, lattice
Hermiticity/convergence/energy accounting, metasurface passivity/SI units, CLI
receipts, and installed-wheel imports/CLI. The pytest hang is closed as not
reproduced. A separate default-temp-root ACL issue remains on this machine:
pytest cannot read `C:\Users\andrew\AppData\Local\Temp\pytest-of-andrew`.
With `--basetemp` inside the audit worktree, `tests\rgcs_lab` passes normally.

## Independent Numerical Checks

An independent inline Python verifier exercised merged APIs directly:

- `rgcs_lab.golay`
- `rgcs_lab.frames`
- `rgcs_lab.memory`
- `rgcs_lab.dual_pole`
- `rgcs_lab.authority.dual_pole_machine`
- `rgcs_lab.lattice`
- `rgcs_lab.metasurface`
- `rgcs_lab.cli`

Result: 178 assertions passed, 0 failed.

## Findings

### Golay

Status: PASS.

Verified selected 12-bit blocks `0`, `1`, `0x123`, `0xA5A`, and `0xFFF`.
For each block, no-error decode and every single-bit flip across the 24-bit
codeword decoded back to the original value. Representative two-bit and
three-bit masks decoded correctly. The 36-bit transport receipt for
`165876523` with flips `[0, 1, 2]` was GREEN and round-tripped exactly. A
four-bit corruption boundary check reported non-round-trip behavior rather
than silently returning wrong data.

### Quaternion

Status: PASS.

Verified 90-degree X/Y/Z rotations, near-zero and near-pi axis-angle cases,
orthogonal rotation matrices, determinant near `1`, inverse round trips,
norm preservation, noncommutative composition, and `q` / `-q` sign-alias matrix
equivalence. Frame receipt round-trip error was below `1e-12`.

### Memory Benchmark

Status: PASS.

Two consecutive benchmark runs over `examples/rgcs_lab/memory` with `top_k=2`
produced identical result objects. Every model declared the same equal-budget
fields: same corpus, `top_k=2`, and no generation. The complete proposed
system avoided stale memory in the test corpus.

### Dual-Pole

Status: PASS.

The text audit blocked `resonance gain proves excess energy`. The bounded
YELLOW example in `examples/rgcs_lab/claim_yellow.json` remained YELLOW and
did not bypass the critic. The deterministic `DualPoleMachine` refused critic
approval without evidence, then approved only after a typed evidence binding.

### Lattice

Status: PASS.

The 64-state Hamiltonian with directed phase and a defect had Hermitian
residual `0.0`. Lossless integration showed small energy drift:

- coarse `dt_s=0.01`, 100 steps: `2.777655883079433e-11`
- fine `dt_s=0.005`, 200 steps: `8.683054275593349e-13`

The final norm converged across those two runs within `1e-8`. Damped runs
reduced stored norm and increased dissipated ledger mass. The resonance label
does not use excess-energy wording.

### Metasurface

Status: PASS / YELLOW lane preserved.

The reduced-order spoof-SPP sweep remained YELLOW. Power ledger units are `W`;
model units include `H/m`, `F/m`, `ohm/m`, `S/m`, `Hz`, and `W`. Transmitted
power stayed within input power, and numerical residual was `0.0`. The receipt
explicitly warns that the electromagnetic reduced-order model does not compute
gravity or gravity coupling.

### CLI Receipts

Status: PASS.

In-process CLI calls returned exit code `0` for:

- `golay demo --random-flips 3`
- `frames example earth-south-up`
- `memory benchmark examples/rgcs_lab/memory --top-k 2`
- `dual-pole audit examples/rgcs_lab/claim_yellow.json`
- `lattice run --steps 10`
- `metasurface sweep --points 3`

The direct installed `rgcs-lab.exe golay demo --random-flips 3` wrapper also
returned exit code `0` from `C:\tmp`.

### Installed Wheel

Status: PASS with environment note.

Built wheel:

- file: `C:\tmp\rgcs-audit-wheel\rgcs-8.2.0-py3-none-any.whl`
- SHA256: `13449f569be9faee0bc264f00031bb6fc7f06553ce3f46670fd47f18b7bedc46`

Installed into `C:\tmp\rgcs-audit-installed`. Because this user environment
contains older editable RGCS path hooks, installed-wheel import checks forced
the wheel target to the front of `sys.path` and filtered stale editable RGCS
entries. After ACL normalization on the temp install tree, installed imports
resolved from `C:\tmp\rgcs-audit-installed\rgcs_lab\__init__.py`.

Installed checks passed for:

- `rgcs_lab.cli doctor`
- `rgcs_lab.cli golay demo --random-flips 3`
- `rgcs_lab.lattice.simulate(LatticeConfig(steps=10))`
- `C:\tmp\rgcs-audit-installed\bin\rgcs-lab.exe golay demo --random-flips 3`

## Pytest Status

Default temp root run:

```text
python -m pytest tests\rgcs_lab -q
52 passed, 3 errors in 8.70s
EXIT_CODE=1
ELAPSED_SECONDS=10.96
```

Errors were all setup-time `PermissionError: [WinError 5] Access is denied:
'C:\Users\andrew\AppData\Local\Temp\pytest-of-andrew'` for tests using
`tmp_path`.

Writable basetemp run:

```text
python -m pytest tests\rgcs_lab -q --basetemp .pytest-basetemp
55 passed in 3.16s
EXIT_CODE=0
ELAPSED_SECONDS=4.209
```

No-plugin writable basetemp run:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests\rgcs_lab -q -p faulthandler --basetemp .pytest-basetemp-noplugins
55 passed in 2.62s
EXIT_CODE=0
ELAPSED_SECONDS=3.333
```

Conclusion: no pytest teardown hang is reproducible in the fresh audit
worktree. The current Windows issue is an ACL problem in pytest's default temp
root, not a repository teardown leak.

