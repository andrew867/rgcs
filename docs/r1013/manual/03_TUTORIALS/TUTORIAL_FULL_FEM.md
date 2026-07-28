# Tutorial: Full Three-Dimensional FEM


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Goal

Calculate the first 24 elastic modes of a complete regular-faceted specimen.

## Prepare complete data

Use `examples/crystal_complete.json`. Replace the example values with measured values.

## Validate

```bash
rgcs crystal validate examples/crystal_complete.json --model fem-elastic
```

## Build a coarse mesh

```bash
rgcs crystal mesh examples/crystal_complete.json --clmax-mm 8 --out tutorial/fem/cl8
```

## Solve

```bash
rgcs crystal modes examples/crystal_complete.json --mesh tutorial/fem/cl8 --count 24 --fixture free --out tutorial/fem/modes-cl8
```

## Refine

Repeat at 6 mm and 4 mm. Then:

```bash
rgcs crystal convergence tutorial/fem/modes-cl8 tutorial/fem/modes-cl6 tutorial/fem/modes-cl4 --out tutorial/fem/convergence
```

## Pass condition

The pass condition must be declared before the final run. Example:

- frequency change below 1 percent for the modes of interest;
- mode-shape correlation above 0.95;
- residual below the solver threshold;
- no invalid or inverted elements.

A mode that fails convergence remains provisional.
