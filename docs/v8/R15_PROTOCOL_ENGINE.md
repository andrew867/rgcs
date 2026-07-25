# R15 P07 — Executable Protocol Engine

**Tranche:** T3 Experimental Execution &nbsp;·&nbsp; **Status:** COMPLETE
&nbsp;·&nbsp; **Depends on:** the R15 claim taxonomy (`r15/claims.py`) and the
R13 authorities it reuses (`r13/serialize.py`, `r13/preregister.py`,
`r13/experiments.py`).

P07 turns a preregistered procedure into a **frozen, hash-sealed,
executable protocol** and a **runner** that compiles and executes it
deterministically against synthetic devices. No apparatus is operated; no
physical measurement is produced or claimed.

## What P07 adds

| Module | What it is |
|---|---|
| `r15/protocols.py` | The typed `Protocol` (matching `protocol_record.schema.json`): id, version, hypotheses, controls, randomization, blinding, ordered steps, stop conditions, analysis plan, and a **claim cap**. Freezing (`freeze`) seals it under a deterministic SHA-256 hash. |
| `r15/protocol_runner.py` | The runner: `compile_plan` verifies the seal and authorizes every capability *before* acquisition; `execute` runs the plan, producing an `ExperimentRun` (matching `experiment_run.schema.json`); `dry_run` validates without acquiring. |

## The step vocabulary

A protocol is an ordered tuple of `ProtocolStep`s. The lifecycle kinds
(`StepKind`) are fixed and run in order:

```
ARM → BIND_CALIBRATION → BIND_SPECIMEN → BIND_FIXTURE → ACQUIRE → RECORD
```

Every step names the **capability** it binds to; an `ACQUIRE` step also
carries a **maneuver** (`Maneuver`) and its setpoints, each with a
tolerance band and unit. The maneuvers cover the pack's list:

`SWEEP` · `FIXED_TONE` · `PULSE` · `RINGDOWN` · `ENVIRONMENTAL_SOAK` ·
`REMOUNT` · `REVERSAL` · `SHAM`

Stop conditions (`StopCondition` / `StopKind`) — `MAX_ACQUISITIONS`,
`MAX_STEPS`, `THRESHOLD_EXCEEDED`, `FAULT_DETECTED` — are part of the plan,
so a run's length is fixed before the run, not chosen once data are in view.

## Freezing before execution

`freeze(protocol, epoch=…)` records a SHA-256 seal over the protocol's
canonical serialization, reusing `r13.serialize.content_hash` so there is
one canonicalisation authority, not two. The seal is deterministic (the
same plan always seals identically) and tamper-evident:

- `SealedProtocol.verify()` recomputes the hash from the carried plan; an
  edited plan no longer matches its seal.
- `refuse_edit_after_seal(sealed, proposed)` raises when a proposed plan
  differs from the frozen one — **an edit is a new version with a new seal,
  never a silent replacement of the old.**
- `compile_plan` refuses to run against a broken seal.

The example protocol also carries a `preregistration_hash` — the seal of
the R13 worked preregistration (`r13.preregister.example_seal`) — and takes
its hypothesis from the R13 experiment registry, so it *binds to* those
authorities rather than restating them.

## The four execution modes (kept distinct)

| Mode | Behaviour | Status | Claim class |
|---|---|---|---|
| `REAL` | **Not run** — no apparatus exists here | `PREREGISTERED_NOT_RUN` | `PREREGISTERED_NOT_RUN` |
| `SYNTHETIC` | Seeded deterministic simulator | `SYNTHETIC_RUN_COMPLETE` | `SYNTHETIC_OBSERVATION` |
| `REPLAY` | Re-emits caller-supplied recorded frames | `REPLAY_RUN_COMPLETE` | `SYNTHETIC_OBSERVATION` |
| `FAULT_INJECTION` | Deterministically injects a fault; stops on the fault condition | `FAULT_INJECTION_RUN_COMPLETE` | `SYNTHETIC_OBSERVATION` |

A synthetic reading is a pure function of *(plan seal, step index, config
seed)*: the same inputs always yield the same numbers, so a run is
reproducible and the run's content hash is stable across runs.

## The refusal paths

- **Broken seal** → `compile_plan` / `execute` refuse (`RunnerError`).
- **Unauthorized configuration / unavailable capability** → refused *before*
  acquisition (`compile_plan`).
- **Missing calibration** on a calibration-requiring step → refused.
- **Claim cap at a measurement class** → refused at construction
  (`Protocol._validate_claim_cap`) — no plan turns a synthetic run into a
  physical measurement.
- **Synthetic run read as a measurement** → `refuse_synthetic_as_measurement`
  (delegates to the claim taxonomy's standing refusal).
- **Frozen prediction read as a result** → `refuse_prediction_as_measurement`.

## What P07 does NOT establish

P07 measures nothing. Freezing hashes a plan; it does not operate an
apparatus. A `SYNTHETIC` / `REPLAY` run yields a `SYNTHETIC_OBSERVATION`,
reproducible from the seed and **never** a `PHYSICAL_MEASUREMENT`. A `REAL`
run is not performed at all — it is recorded as `PREREGISTERED_NOT_RUN` with
no artifacts. The strongest class reachable here is a synthetic observation;
the measurement classes exist in the taxonomy only so the ladder stays
honest about what is still missing.

**Claim cap:** `SYNTHETIC_OBSERVATION`.
**Verdicts:** `EXECUTABLE_PROTOCOL_FROZEN_NO_PHYSICAL_RUN`
(`protocols`) and
`PROTOCOL_COMPILED_AND_RUN_SYNTHETIC_NO_PHYSICAL_MEASUREMENT` (`runner`).

`PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Tests

`tests/v8/test_protocols.py` — 31 tests: focused (a frozen protocol compiles
and runs deterministically on synthetic devices; records validate against
their schemas), modes-distinct (REAL is not run, fault injection stops on
its fault, replay re-emits frames), stop conditions terminate correctly,
determinism (same seal + config + seed ⇒ byte-identical run), and the
negative/refusal paths (post-seal edit detected, unauthorized config and
unavailable capability refused before acquisition, measurement-class claim
cap refused, synthetic run not readable as a measurement).
