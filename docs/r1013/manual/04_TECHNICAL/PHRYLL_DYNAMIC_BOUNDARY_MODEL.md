# Phryll Dynamic-Boundary Research Model


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Status

This chapter preserves a source-provenance hypothesis and its conventional physical translation. It does not establish Phryll, free energy, propulsion, gravity modification, or multiverse transfer.

## Exact timing relationship

Carrier:

\[
f_c=4096\ \mathrm{Hz}.
\]

Nominal macrocycle:

\[
T_0=552\ \mathrm{ms}.
\]

Carrier cycles in the nominal interval:

\[
f_cT_0=2260.992=2260+\frac{124}{125}.
\]

The next integer closure is 2261 cycles:

\[
T_{\mathrm{closed}}=\frac{2261}{4096}=552.001953125\ \mathrm{ms}.
\]

Difference:

\[
\Delta t=1.953125\ \mu\mathrm{s}.
\]

Phase step:

\[
\Delta\phi=360^\circ/125=2.88^\circ.
\]

Define \(q\in\{0,\ldots,124\}\):

\[
\Delta t(q)=q(1.953125\ \mu\mathrm{s}),
\qquad
\Delta\phi(q)=q(2.88^\circ).
\]

## Dynamic boundary

Let \(g_q(t)\) be a timed gate applied to an optical or acoustic wavepacket envelope \(u(t)\).

Energy-weighted duty cycle:

\[
D_{\mathrm{eff}}(q)=
\frac{\int|u(t)|^2g_q(t)dt}{\int|u(t)|^2dt}.
\]

A time-dependent boundary may mix modes:

\[
a_m^{\mathrm{out}}=\sum_n\left(\alpha_{mn}a_n^{\mathrm{in}}+\beta_{mn}a_n^{\mathrm{in}\dagger}\right).
\]

The conventional energy ledger is:

\[
E_{\mathrm{before}}+W_{\mathrm{switch}}+E_{\mathrm{pump}}
=E_{\mathrm{after}}+E_{\mathrm{loss}}.
\]

## Testable observables

- transmitted and reflected optical energy;
- optical sidebands;
- acoustic sidebands;
- crystal ring-down;
- piezoelectric output;
- switching work;
- thermal change;
- mechanical mode redistribution;
- dependence on \(q\), pulse tail, and effective duty cycle.

## Source interpretation

The source model relates phase-controlled tail chopping to Phryll generation, environmental emission, and craft motion. That interpretation remains unverified and must not replace the energy ledger.
