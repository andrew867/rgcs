# Anisotropy and the Christoffel Solver


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


For every unit direction \(\mathbf n\), build:

\[
\Gamma_{ik}=C_{ijkl}n_jn_l.
\]

Solve:

\[
\Gamma\mathbf p=\rho v^2\mathbf p.
\]

The eigenvectors are polarizations. The eigenvalues produce squared phase velocities.

## Output requirements

The solver must report:

- direction in crystal and body frames;
- branch identity;
- phase velocity;
- polarization;
- group velocity where calculated;
- source tensor version;
- orientation;
- numerical residual.

## Orientation uncertainty

When azimuth around the C-axis is unknown, sweep it. Do not choose the azimuth that best matches a preferred frequency after the calculation.
