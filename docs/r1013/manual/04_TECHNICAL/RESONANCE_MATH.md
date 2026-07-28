# Resonance Mathematics


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## One-dimensional screening

Quarter-wave:

\[
f_n=\frac{(2n-1)v}{4L}.
\]

Half-wave:

\[
f_n=\frac{nv}{2L}.
\]

Closed path:

\[
f_n=\frac{nv}{L_{\mathrm{path}}}.
\]

These formulas need a declared path, speed, and boundary model.

## Anisotropic plane waves

\[
\det\left(C_{ijkl}n_jn_l-\rho v^2\delta_{ik}\right)=0.
\]

The three eigenvalues produce three phase velocities. Group velocity may not align with the phase normal.

## Finite-element eigenproblem

\[
K\mathbf u=\omega^2M\mathbf u.
\]

For piezoelectric coupling, use the block electromechanical system and declared open, short, or finite-load boundary.

## Damping and Q

A lossless eigenproblem predicts frequencies and mode shapes. It does not predict measured Q unless damping is modeled or fitted.

A measured Q may be estimated by:

\[
Q=\frac{f_0}{\Delta f_{-3\mathrm{dB}}}.
\]

## Frequency uncertainty

For a simple length model:

\[
\left(\frac{\sigma_f}{f}\right)^2\approx
\left(\frac{\sigma_v}{v}\right)^2+
\left(\frac{\sigma_L}{L}\right)^2.
\]

Full models require sampling geometry, material, orientation, fixture, and numerical uncertainty.
