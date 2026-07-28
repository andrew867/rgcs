# Python API Reference Contract


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


The exact module names must be reconciled with the target repository. The stable R10.13 user API should provide typed functions equivalent to:

```python
from rgcs import crystals

specimen = crystals.load_specimen("crystal.json")
validation = crystals.validate_specimen(specimen)
geometry = crystals.calculate_geometry(specimen)
estimates = crystals.estimate_frequencies(specimen, models=["axial-quarter", "axial-half"])
mesh = crystals.build_mesh(specimen, clmax_mm=6.0, output_dir="run/mesh")
modes = crystals.solve_elastic_modes(specimen, mesh=mesh, count=24, fixture="free")
report = crystals.build_report(specimen, modes, output_dir="run/report")
```

## Return contract

Every result object must include:

- schema version;
- evidence class;
- input hashes;
- warnings;
- status or typed refusal;
- deterministic serialization;
- provenance and correction state.

## Compatibility

Existing packages such as `rgcs_core`, `rscs_core`, `rscs2_core`, and `r15` remain importable according to the release policy. The new user API should wrap them rather than duplicate their mathematics.
