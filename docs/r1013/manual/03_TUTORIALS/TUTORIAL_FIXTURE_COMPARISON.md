# Tutorial: Fixture Comparison


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Goal

Compare a free specimen, a three-point cradle, and a center clamp.

## Run three declared fixtures

```bash
rgcs crystal modes crystal.json --fixture fixtures/free.json --out runs/free
rgcs crystal modes crystal.json --fixture fixtures/three_point.json --out runs/three-point
rgcs crystal modes crystal.json --fixture fixtures/center_clamp.json --out runs/center-clamp
```

## Compare

```bash
rgcs compare fixtures runs/free runs/three-point runs/center-clamp --out runs/fixture-comparison
```

The report should show frequency shift, mode-shape change, and new fixture-local modes.
