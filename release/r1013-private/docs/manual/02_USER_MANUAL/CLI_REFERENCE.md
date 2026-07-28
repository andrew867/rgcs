# CLI Reference


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Existing v8.0.0 command

```text
rgcs-v4
```

Existing subcommands include `devices`, `material`, `geometry`, `mesh`, `modes`, `sweep`, `piezo`, `optical`, `coil`, `diagnostics`, `refsystems`, `capabilities`, `proof-bundle`, `report`, and `verify-checksums`.

## Unified command (implemented)

```text
rgcs
```

The implementation must retain `rgcs-v4` as a compatibility entry point.

## General

```bash
rgcs --version
rgcs doctor
rgcs self-test
rgcs schema verify
rgcs examples verify
```

## Crystal records

```bash
rgcs crystal new FILE
rgcs crystal validate FILE
rgcs crystal inspect FILE
rgcs crystal migrate FILE --out NEW_FILE
rgcs crystal hash FILE
```

## Geometry and estimates

```bash
rgcs crystal geometry FILE
rgcs crystal density-check FILE
rgcs crystal estimate FILE --models LIST
rgcs crystal christoffel FILE --directions LIST
```

## Mesh and modes

```bash
rgcs crystal mesh FILE --clmax-mm FLOAT --out DIR
rgcs crystal modes FILE --mesh DIR --count INT --fixture NAME --out DIR
rgcs crystal converge FILE --levels 8,6,4 --count 24 --out DIR
rgcs crystal piezo FILE --condition open|short --count INT --out DIR
```

## Reports and bundles

```bash
rgcs crystal report FILE --from RESULT_DIR --out DIR
rgcs crystal bundle FILE --result RESULT_DIR --out BUNDLE_DIR
rgcs bundle verify BUNDLE_DIR
```

## Frequency registry

Note: a frequency-to-coordinate command is NOT shipped: it would assert the state-to-geometry bridge, which is underdetermined. The refusal is recorded in receipts/COMMAND_STATUS.json.

```bash
rgcs frequency list
rgcs frequency compare MODE_FILE --keys 4096,528,560
```

## Codec research

```bash
rgcs wire parse WIRE
rgcs wire explain WIRE
rgcs wire roundtrip WIRE
rgcs transition candidates WIRE --child C
rgcs mesh trace WIRE
```

Unknown transition cells must return a typed refusal.

## Output modes

Every command should support:

```text
--format human
--format json
--format csv
--quiet
--output PATH
```

Human output is for a normal user. JSON output is the stable automation interface.
