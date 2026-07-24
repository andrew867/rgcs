# R13 Phase Receipt

```text
phase_id: 30
phase_title: Cross-Domain Transfer Benchmark
status: PREREGISTERED_NOT_RUN
start_commit: 8ae9574
end_commit: v7.0.0 (branch v630-r13)
files_added: r13/experiments.py, r13/preregister.py (shared across phases 25-30)
files_modified: none
tests_added: tests/v6/test_r13_experiments.py (shared prospective-registry suite, 17 tests)
focused_test_result: .venv/Scripts/python.exe -m pytest tests/v6/test_r13_experiments.py -q -> 17 passed
full_regression_result: 5638 passed, 8 skipped, 1 deselected, exit 0
source_hashes_used: build_meta source hash over SOURCE_ROOTS incl. r13
claim_classes_emitted: PROSPECTIVE_PREDICTION, ENGINEERING_CANDIDATE
private_files_read: false
```

## Work completed

Preregistered a benchmark for one complete certified path through at least
three domains. Registered in `r13/experiments.py`; the certified path is built
with `r13/bridgegraph.py` (coupling-graph search) over certificates including
the `r13/piezobridge.py` MECHANICAL->ELECTRICAL certificate. Sealed under
`r13/preregister.py`. Status `PREREGISTERED_NOT_RUN`.

- **The path:** at least three domains (e.g. atomistic / continuum ->
  mechanical -> electrical) connected by an end-to-end chain of coupling
  certificates.
- **Predicted signature / null / decision rule:** a transfer efficiency above
  the certificated null threshold, refuted otherwise.
- **Null model:** a no-coupling control with efficiency at the null threshold.

## Evidence and equations implemented

Certificate gating: every edge is a complete R12/R13 coupling certificate,
each `AWAITING_FALSIFICATION`. `path_claim_class` returns `ENGINEERING_CANDIDATE`
(the weakest link) and **never** a measurement class.
`refuse_path_as_measured` and `refuse_automatic_composition` block treating a
chain as measured or auto-composing certificates — a composite A->C needs its
own certificate. Power: the benchmark detects a planted transfer and nulls on
a no-coupling control.

## Negative results

A simulated path is not a measured transfer. A chain of certificates, each
awaiting falsification, is an engineering candidate — not evidence of
cross-domain transfer. `PHYSICAL_VALIDATION_NOT_CLAIMED`.

## Deviations from prompt

The prompt allows "measure or simulate" a complete path. Only the simulated
path is realizable here; the end-to-end path is at best an
`ENGINEERING_CANDIDATE` gated by certificates that are `AWAITING_FALSIFICATION`.
No measured transfer is claimed.

## Blocking inputs, when applicable

Execution (the measured path) is `BLOCKED_MISSING_INPUT` on a built bench: no
apparatus exists to run the certified chain end to end. The simulated path is
complete; the measurement is sealed and awaits data.

## Downstream impact

Composes the coupling-graph search (phase 6) and piezoelectric bridge
(phase 10) into a single benchmark whose claim class is pinned to the weakest
certificate, preventing any composite from being read as measured transfer.

## Reopening test

Unseal the preregistration and run the sealed analysis on real bench data;
reopen when a bench exists.

## Acceptance checklist

- [x] Benchmark registered and sealed; path built via `r13/bridgegraph.py`
  over `r13/piezobridge.py` and peer certificates.
- [x] `path_claim_class` returns `ENGINEERING_CANDIDATE`, never a measurement.
- [x] Path-as-measured and automatic composition both refused.
- [x] Planted transfer detected; no-coupling control nulls.
- [x] Focused suite passes (17 passed).
- [x] Claim classes `PROSPECTIVE_PREDICTION` / `ENGINEERING_CANDIDATE`; no
  physical validation claimed.
