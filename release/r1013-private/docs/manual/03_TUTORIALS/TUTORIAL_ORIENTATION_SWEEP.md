# Tutorial: Orientation Sweep


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Goal

Quantify how unknown lattice orientation changes the candidate modes.

## Define the ensemble

```bash
rgcs orientation plan crystal.json --beta 0:15:5 --gamma 0:330:30 --out orientation-plan.json
```

The exact syntax is a target interface. The plan must record every orientation before execution.

## Run

```bash
rgcs crystal modes crystal.json --orientation-plan orientation-plan.json --count 12 --clmax-mm 8 --out runs/orientation
```

## Read the result

Report a distribution for each tracked mode. Do not report only the orientation that places a mode nearest a preferred key.
