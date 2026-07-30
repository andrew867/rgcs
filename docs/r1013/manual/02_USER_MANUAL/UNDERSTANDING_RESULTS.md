# Understanding Results


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Read the evidence class first

A frequency without an evidence class is incomplete.

Common classes:

- `SOURCE_CLAIM`: copied from a source record.
- `DERIVED_ARITHMETIC`: exact or approximate arithmetic on declared inputs.
- `ANALYTIC_MODEL`: result of a closed-form or low-order model.
- `NUMERICAL_SIMULATION`: result of FEM or another numerical solver.
- `SYNTHETIC_RUN`: generated test data.
- `BENCH_MEASUREMENT`: data acquired from a physical instrument with required metadata.
- `INDEPENDENT_REPLICATION`: a qualifying independent repeat.
- `UNSUPPORTED`: the requested conclusion is not supported.
- `UNDERDETERMINED`: several results remain possible.
- `REVOKED` or `HISTORICAL_ONLY`: preserved history that cannot become active.

## Mode table fields

A useful mode table includes:

- mode index;
- frequency;
- rigid-body flag;
- residual;
- mode family classification;
- dominant displacement direction;
- effective mass or participation;
- mesh level;
- fixture;
- orientation;
- confidence and warnings.

## Rigid modes

A free three-dimensional body has near-zero rigid translations and rotations. Do not confuse them with elastic resonances.

## Mode ordering

Modes may cross or exchange order as the mesh, fixture, or orientation changes. Match modes by shape, not only by list index.

## Precision

Six decimal places do not create six-decimal physical accuracy. Report numerical precision separately from input and model uncertainty.

## A null result can pass

The correct result may be:

- no mode near the candidate key;
- no directional asymmetry;
- no change beyond uncertainty;
- insufficient input;
- model family falsified.

RGCS treats an honest null as a successful scientific result.
