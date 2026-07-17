# Butterworth-Van Dyke extraction (Agent C06)

Coverage: **A14, A15**. Gate: **G13** (synthetic recovery and
identifiability). Status: `REDUCED_ORDER_VALIDATED`.
Implementation: [`rscs2_core/bvd.py`](../../rscs2_core/bvd.py).

## The circuit

    Z(w) = Z_C0 || (R1 + jwL1 + 1/(jwC1))

    fs      = 1 / (2 pi sqrt(L1 C1))
    fp      = fs sqrt(1 + C1/C0)
    Q       = 2 pi fs L1 / R1
    k_eff^2 = (fp^2 - fs^2) / fp^2        (IEEE-176 form)

The `k_eff²` convention matches the frozen v4 piezo module, so the two
cannot silently disagree.

## Synthetic recovery (G13)

Round-trip against a designed circuit (fs = 10 kHz):

| Parameter | Truth | Recovered |
|---|---|---|
| fs | 10000.00 Hz | 10000.00 Hz |
| fp | 10024.97 Hz | 10025.00 Hz |

C0 comes from the high-frequency capacitive asymptote, C1 from
`C0((fp/fs)² − 1)`, L1 from fs, R1 from |Z| at series resonance.

## Identifiability is reported, not assumed

`extract_bvd()` returns `INSUFFICIENT_RESOLUTION` when fs or fp is not
resolved inside the sweep band — it does not extrapolate.

`fit_uncertainty()` goes further and reports when a fit that *looks*
successful is not trustworthy:

- fs/fp are quantized by the frequency grid → `u_fs = df/2`, and that
  uncertainty propagates into `k_eff²` analytically.
- If `fp − fs` spans fewer than 4 grid steps, the fit is
  **non-identifiable** and exact parameters must not be reported.
- If |Z|min sits at or below the noise floor, R1 (and therefore Q) is
  unconstrained.

Verified: the same circuit sampled on a 25-point grid correctly
returns non-identifiable with the reason
`fp-fs = 33.333 Hz spans fewer than 4 grid steps (16.667 Hz)`.

**Reporting a Q of 125663.7 from a sweep that cannot resolve the peak
would be false precision, not a measurement.**

## Multi-branch: unmodelled structure is named

The C06 boundary: *do not fit a single branch to a multimode spectrum
and call the residual structure noise*.

`fit_multibranch()` detects every dip, ranks by depth, models up to
`max_branches`, and **reports the rest explicitly** in
`unmodelled_dips_hz`. `single_branch_adequate` is only true when
exactly one dip exists. Residual structure is never relabelled noise.

## Open-short-load calibration

`osl_correct()` de-embeds the fixture through the standard three-term
error model:

    Z_dut = Z_ref (Z_m − Z_s)(Z_o − Z_l) / ((Z_o − Z_m)(Z_l − Z_s))

Verified to recover the DUT exactly from ideal standards. Degenerate
standards raise rather than returning a silently wrong de-embedding.

Fixture impedance is an ordinary channel; an uncalibrated fixture
produces "resonances" that belong to the jig
(see [APPARATUS_DIGITAL_TWIN.md](APPARATUS_DIGITAL_TWIN.md)).

## Electrode loading

`electrode_loading()` scales C0 by the coverage fraction and applies a
first-order Rayleigh mass-loading pull,
`f/f0 = sqrt(m/(m+dm))` — declared as an estimate, not a calibration.

## SPICE export

`to_spice()` emits a subcircuit for the apparatus simulation. The
header states it is a fitted reduced-order model, **not** a measured
device, so the label travels with the file.

## Status boundary

Every number in this module currently comes from a **synthetic**
sweep. No impedance analyser has been connected to any specimen. The
pipeline is validated on planted fixtures; measurement awaits hardware
(`PROTOCOL_READY_HARDWARE_REQUIRED` at the campaign level, E02/E08).
