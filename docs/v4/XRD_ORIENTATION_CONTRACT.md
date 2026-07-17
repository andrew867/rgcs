# XRD orientation contract (Agent C05)

Coverage: **G001–G030** (orientation). Status: `INTERFACE_ONLY`.
Implementation: `rscs2_core.metrology.xrd_orientation_interface`.

## The rule

**Crystallographic axes may not be inferred from visual facets.**

This is the C05 boundary, and it is enforced in code:
`xrd_orientation_interface()` returns `INTERFACE_ONLY` with
`c_axis_deg: None` unless a real scan is supplied.

## Why a facet is not an axis

A facet normal is a geometric fact about the shape in front of you. A
c-axis is a crystallographic fact about the lattice inside it. For a
naturally terminated crystal the two are related — but quartz can be
**cut at any angle to its axes**, and every specimen in this programme
is a cut, polished, seller-supplied body of unknown provenance.

Inferring the c-axis from the visible six-fold symmetry of a cut wand
assumes the conclusion. The anisotropic elastic model is orientation-
dependent (the whole point of the v3 Christoffel work), so a wrong
axis assignment propagates silently into every modal frequency.

Since the elastic model **is** orientation-dependent, an assumed
orientation would make every downstream frequency an assumption
wearing a measurement's clothes.

## What the interface declares

```
input:  2-theta/omega scan + reference quartz calibration
output: c-axis and lateral-axis orientation with uncertainty
```

With a real scan (`two_theta_deg`, `intensity`, `calibration_id`) the
function returns the measured dominant peak and tags the record `MEAS`.
It does **not** assign the peak to a lattice plane: that requires the
reference pattern, and the function returns the measurement only.

Malformed scans raise rather than returning a guess.

## Current status

No XRD data exists in this programme. Every specimen's orientation is
therefore **unknown**, and the ideal-geometry models assume a declared
orientation which is stated as an assumption in each result envelope
rather than as a property of the specimen.

## What would close this

A 2-theta/omega scan per specimen against a reference quartz standard,
with the calibration id recorded. Requires XRD hardware access
(`PROTOCOL_READY_HARDWARE_REQUIRED`) — a human-only action.
