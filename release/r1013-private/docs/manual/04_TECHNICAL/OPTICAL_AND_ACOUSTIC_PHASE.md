# Optical and Acoustic Phase


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


Quartz can act as a resonator, transducer, phase reference, birefringent medium, acousto-optic medium, and nonlinear optical medium in different devices.

## Phase state

A coherent component can be represented by:

\[
\mathcal X=(\omega,\mathbf k,\phi,t_0,\mathrm{domain},\mathrm{path},\Sigma).
\]

A received residual is:

\[
\delta\phi=\phi_{\mathrm{received}}-\phi_{\mathrm{ideal}}.
\]

Separate residual contributions from synthesis, clock, path, medium, motion, transducer, fixture, and noise.

## Acousto-optic modulation

A traveling strain field changes refractive index and can create a moving optical grating. Phase and timing determine diffraction and pulse gating.

The 1970 research lead identifies resonant self-pulsing acousto-optic quartz modulation and variable delay as prior-art areas that require formal verification in the repository bibliography.
