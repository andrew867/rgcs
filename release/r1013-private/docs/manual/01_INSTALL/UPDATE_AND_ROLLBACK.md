# Update and Roll Back


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Before an update

1. Export specimen files and run configurations.
2. Record the installed version.
3. Verify existing proof bundles.
4. Read the migration guide.

## Update a source checkout

```bash
git fetch --tags
git checkout <approved-tag-or-commit>
python -m pip install -e '.[desktop,workbook]'
```

## Roll back

Install the exact prior wheel or check out the prior tag. Do not edit old proof bundles. A bundle belongs to the software version that created it.

## Schema migration

The command:

```bash
rgcs crystal migrate old.json --out migrated.json
```

must create a new file. It must preserve the old file and write a migration receipt.
