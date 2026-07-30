# Crystal Geometry Model


> Documentation status: R10.13 IMPLEMENTED release documentation (verified against the repository; see receipts/COMMAND_STATUS.json).
>
> Repository state observed during drafting: public RGCS v8.0.0, Python 3.11+, existing console commands `rgcs-v4` and `rgcs-workbook`, and desktop command `rgcs-workbench`.
>
> The custom-specimen commands are implemented in this release by the unified `rgcs` command (r1013.cli) and every documented command is executed by the doc-execution test suite. Two documented items were NOT shipped and carry typed reasons in receipts/COMMAND_STATUS.json: `rgcs frequency coordinate` (refused: would assert the underdetermined state-to-geometry bridge) and the desktop New Specimen wizard (deferred; CLI workflow is the supported path).
>
> All resonance outputs are estimates, analytic results, numerical simulations, synthetic observations, or physical measurements according to their evidence label. A computed frequency is not a measured resonance.


## Regular faceted model

Inputs:

- total length \(L\);
- wide diameter \(D_w\);
- narrow diameter \(D_n\);
- facet count \(N\);
- female and male termination angles;
- diameter and angle conventions.

For across-vertices diameter, polygon area is:

\[
A=\frac{N}{8}D^2\sin\left(\frac{2\pi}{N}\right).
\]

For across-flats diameter:

\[
A=N\left(\frac{D}{2}\right)^2\tan\left(\frac{\pi}{N}\right).
\]

The apothem for across-vertices diameter is:

\[
r_a=\frac{D}{2}\cos\left(\frac{\pi}{N}\right).
\]

The default face-slope cap height is:

\[
h=r_a\tan\alpha.
\]

The shaft length is:

\[
h_s=L-h_f-h_m.
\]

The model refuses \(h_s\le0\).

## Volume

The tapered shaft is a frustum:

\[
V_s=\frac{h_s}{3}\left(A_w+A_n+\sqrt{A_wA_n}\right).
\]

Add both termination pyramids:

\[
V=V_s+\frac{A_wh_f}{3}+\frac{A_nh_m}{3}.
\]

## Mass consistency

\[
m=\rho V.
\]

The density inverse may scale diameters to match a measured mass. This is a diagnostic. It does not replace direct diameter measurements.

## Irregular geometry

Use an imported mesh when facet irregularity is significant. The import audit must verify units, closure, manifold status, volume, orientation, and scale.
