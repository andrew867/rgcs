# Tutorial: Batch of Crystals


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Goal

Validate and estimate several specimens without mixing their provenance.

## Batch file

Use `examples/crystal_batch.csv`. Each row points to one JSON specimen file.

## Run

```bash
rgcs batch validate examples/crystal_batch.csv --out batch/validation
rgcs batch estimate examples/crystal_batch.csv --models axial-quarter,axial-half --out batch/estimates
```

## Rules

- Each result retains the specimen hash.
- A failed specimen does not disappear from the batch.
- Batch summary statistics do not replace individual reports.
- Do not select only the specimens nearest a frequency key after the run.
