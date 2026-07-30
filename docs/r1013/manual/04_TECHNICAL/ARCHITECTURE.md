# Architecture


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Layers

```text
user input
  -> specimen schema
  -> validation and provenance
  -> geometry model
  -> material and orientation model
  -> low-order estimate or mesh
  -> elastic or piezoelectric solver
  -> uncertainty and convergence
  -> evidence classification
  -> report and proof bundle
```

Research extensions add:

```text
phase and frequency registry
  -> dynamic boundary timing
  -> aperture geometry
  -> optical and acoustic mode redistribution
  -> measured or simulated observables
```

Coordinate research adds:

```text
decimal transport envelope
  -> two-sided octal refinement
  -> E3 and three S6 states
  -> state transitions
  -> state-dependent analytic edge law
  -> topology and body realization
```

## Separation rules

- Geometry is separate from material.
- Material is separate from orientation.
- Orientation is separate from fixture.
- Topology is separate from node positions.
- Angular mesh compensation is separate from ellipsoid realization.
- A source hypothesis is separate from its physical translation.
- A model output is separate from a physical measurement.
