# E09 — Staged physical bench execution and measurement release

Coverage: **E018–E020, E022, E023, E026, E027**.
Status: **`PROTOCOL_READY_HARDWARE_REQUIRED`** — no stage executed.

## Staging order (dependencies, not preferences)

| Stage | Requires |
|---|---|
| 1. Apparatus characterization | instruments calibrated |
| 2. Ordinary-artifact budget measured | stage 1 |
| 3. Acoustic (E01) | stages 1–2 |
| 4. Impedance / BVD (E02, E08) | stages 1–2 |
| 5. Coil / field (E03) | stages 1–2 + interlocks |
| 6. Material comparison (E04) | stages 3–5 + metrology |
| 7. Water (E05) | stages 1–5 |
| 8. Human loading (E06) | **ethics approval** |
| 9. Operator state (E07) | stage 8 complete |
| 10. Prospective precision family | fabricated specimens |

Stage 2 gates everything. Until the ordinary artifacts are *measured*
(not just predicted), no residual means anything.

## Escalation gates

Each stage requires: preregistration filed, calibration current,
controls present, safety gate passed, and the previous stage's report
accepted. A stage cannot be skipped because its result is expected.

## Abort criteria

- Any safety envelope exceeded → immediate stop.
- Calibration expired mid-session → session void.
- Control missing → run void, not "control-free pilot data".
- Blind broken before lock → data unusable for the preregistered
  outcome.

## Data lock points

Raw files hashed at capture. Analysis version recorded. Blind decoded
**only after** the analysis is locked. Deviations logged as deviations,
not silently absorbed into the method.

## Null preservation (G48)

Every executed run produces a record, including the ones that find
nothing. **A null result is not a failed project**, and no run may be
deleted for being uninteresting. Chain of custody, raw hashes,
calibration, controls, and deviations are audited — the audit assumes
the most likely error is the experimenter, because it is.

## Boundaries

- **Do not fabricate runs. Do not call synthetic data measured.**
- Do not proceed past a safety or ethics gate.
- For unavailable hardware, finish the protocol-ready artifacts and
  return `PROTOCOL_READY_HARDWARE_REQUIRED` — which is the honest
  status of **all ten stages** today.

## Current state

Zero stages executed. Zero runs. Zero measured data points anywhere in
the RGCS v4.2 programme.
