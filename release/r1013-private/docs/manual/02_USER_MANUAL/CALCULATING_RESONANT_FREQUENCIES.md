# Calculating Resonant Frequencies


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## There is no single universal formula

Use the simplest model that answers the question, then move to a more complete model when needed.

## Quick axial quarter-wave estimate

\[
f_n = \frac{(2n-1)v}{4L_{\mathrm{eff}}}, \qquad n=1,2,3,\ldots
\]

Use this only when the boundary and mode resemble a quarter-wave path.

For a declared speed of 6310 m/s and length 77.8 mm:

\[
f_1 \approx \frac{6310}{4(0.0778)} \approx 20276.35\ \mathrm{Hz}.
\]

This is a screening estimate. It is not a full crystal mode.

## Quick axial half-wave estimate

\[
f_n = \frac{nv}{2L_{\mathrm{eff}}}.
\]

For the same example:

\[
f_1 \approx 40552.70\ \mathrm{Hz}.
\]

## Directional anisotropic estimate

For a direction vector \(\mathbf n\), solve:

\[
\Gamma_{ik}p_k = \rho v^2p_i,
\qquad
\Gamma_{ik}=C_{ijkl}n_jn_l.
\]

This returns three branches. Each branch can produce a path-frequency estimate. The result depends on crystal orientation.

Target command:

```bash
rgcs crystal christoffel my-crystal.json --directions body-z,body-x,body-y
```

## Full elastic FEM

The finite-element solver builds stiffness and mass matrices:

\[
K\mathbf u = \omega^2 M\mathbf u.
\]

Each non-rigid eigenpair gives:

\[
f=\frac{\omega}{2\pi}.
\]

The result includes a mode shape. It can distinguish axial, flexural, torsional, and mixed modes better than a one-dimensional formula.

## Piezoelectric solve

The coupled system adds electric potential and piezoelectric constitutive terms. Electrical boundary conditions such as open and short can shift the modes.

## Fixture effect

A calculated free-body mode and a clamped measured mode are different systems. Always include the fixture in the comparison.

## Convergence

Run at least three mesh sizes. A result should report:

- frequency change;
- mode-shape correlation;
- residual;
- degrees of freedom;
- solver tolerance;
- memory and runtime;
- whether mode ordering changed.

## Candidate frequency registry

A frequency key can be overlaid on the calculated spectrum. It does not become a mode because it was registered.

Use:

```bash
rgcs frequency compare modes.json --keys 4096,528,560,925,20480,32768
```

The output should show nearest modes and normalized distance without changing the solve.
