# Migration Guide


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## From canonical-only v8.0.0 workflows

The current CLI accepts `ideal_n7` and `nominal`. R10.13 adds custom specimen files.

Canonical workflows remain valid:

```bash
rgcs-v4 geometry nominal
rgcs-v4 modes nominal --n 12
```

Equivalent target workflow:

```bash
rgcs crystal export-canonical nominal --out nominal.json
rgcs crystal modes nominal.json --count 12
```

The exported file must reproduce the canonical geometry exactly.

## Historical codec profiles

Old monolithic packet profiles remain historical compatibility records. They cannot become the default parser for the active segmented family.

## Proof bundles

Never migrate a proof bundle in place. Create a new bundle and preserve the old one.
