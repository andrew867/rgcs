# Tutorial: Quick Estimate


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Goal

Calculate quarter-wave and half-wave screening frequencies for a 77.8 mm specimen.

## Create the file

Copy `examples/crystal_minimum.json` to `my-crystal.json`.

## Validate

```bash
rgcs crystal validate my-crystal.json
```

## Run

```bash
rgcs crystal estimate my-crystal.json --models axial-quarter,axial-half --wave-speed-m-s 6310
```

## Verify by hand

Convert length:

\[
77.8\ \mathrm{mm}=0.0778\ \mathrm{m}.
\]

Quarter-wave:

\[
f=6310/(4\times0.0778)=20276.35\ \mathrm{Hz}.
\]

Half-wave:

\[
f=6310/(2\times0.0778)=40552.70\ \mathrm{Hz}.
\]

## Interpret

These two numbers are not competing truths. They correspond to different boundary assumptions. The software must print the assumption beside each number.
