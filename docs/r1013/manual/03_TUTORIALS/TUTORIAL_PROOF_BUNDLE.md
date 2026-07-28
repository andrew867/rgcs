# Tutorial: Build and Verify a Proof Bundle


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Build

```bash
rgcs crystal bundle crystal.json --result runs/final --out proof/crystal-001
```

## Verify

```bash
rgcs bundle verify proof/crystal-001
```

## Expected contents

- specimen JSON and hash;
- material record;
- fixture and orientation records;
- mesh manifest and mesh hash;
- solver configuration;
- raw result files;
- convergence report;
- user report;
- software and environment receipt;
- `SHA256SUMS.txt`;
- evidence classification;
- limitations and refusals.

A proof bundle proves reproducibility and integrity. It does not prove that a physical prediction is correct.
