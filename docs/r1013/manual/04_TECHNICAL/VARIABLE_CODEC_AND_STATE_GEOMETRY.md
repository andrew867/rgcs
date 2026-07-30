# Variable Codec and State Geometry


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Corrected variable form

There is no one-bit extension field. Refinement can be added on the left or right of the fixed core:

\[
C_{L,3}^{d_L}
\mid E_3
\mid S_{\mathrm{tor},6}
\mid S_{\mathrm{pol},6}
\mid S_{\mathrm{rad},6}
\mid C_{R,3}^{d_R}.
\]

The decimal transport envelope is:

```text
16 | packed payload | terminal
```

Legal payload width:

\[
W=21+3(d_L+d_R).
\]

The parser chooses the smallest legal width that contains the payload. It then enumerates all legal left and right splits.

## State meaning

The three S6 states are source-reported as:

- toroidal phase;
- poloidal phase;
- radial phase.

The radial phase is not a linear \(s/63\) distance. The active hypothesis uses a nonlinear sundial table with 15 degrees per hour-like phase unit.

## Recursive operators

Left refinement:

\[
\mathcal R_L(c):(L,\mathbf s,R)\rightarrow(L\oplus_Lc,T_c^L(\mathbf s),R).
\]

Right refinement:

\[
\mathcal R_R(c):(L,\mathbf s,R)\rightarrow(L,T_c^R(\mathbf s),R\oplus_Rc).
\]

Left and right operations are not assumed to commute.

## State-dependent edge law

The base odds ratio is source-approved as 10/9, modified by state, child, edge, and refinement side:

\[
r_e=\frac{10}{9}M(\phi_{\mathrm{tor}},\phi_{\mathrm{pol}},\phi_{\mathrm{rad}},c,e,\sigma).
\]

Convert odds to an edge fraction:

\[
t_e=\frac{r_e}{1+r_e}.
\]

Generate the shared node analytically by spherical interpolation or the declared body-space equivalent.

A global 10/9 law was not recovered. Only the state-dependent base-ratio model remains active.

## Training corpus

The corrected 19-wire response is intended to encode eight compact/refined pairs and one three-depth same-point chain. The solver must recover the partition. It must use every wire exactly once and must not request the same relationship again before exhausting the exact-cover search.
