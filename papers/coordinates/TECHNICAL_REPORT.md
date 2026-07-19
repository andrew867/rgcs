# Relational Root-Space Coordinates — Technical Report

**Document type: technical report. Not a research paper.**

That classification is the report's first result. An adversarial
prior-art review found six of the framework's seven components to be
textbook, and recommended against research-paper submission on the
grounds that a referee would recognise their own standard material.
This document records the design and states plainly what is and is
not a contribution.

---

## 1. What the framework is

A typed, certificate-carrying coordinate object for phase-referenced
systems, with three properties:

1. the unresolved integer **alias set is retained as data** rather
   than collapsed to a point estimate;
2. the **frame-transform chain propagates uncertainty** as a
   first-class citizen;
3. **insufficiency of evidence is a typed output value** — not an
   exception, not a NaN, not a sentence in a limitations section.

Implementation: `r3/root_space.py`, `r3/address.py`, `r3/atlas.py`,
`r6/mailbox.py`, `r6/navigation.py`, `r7/clocklink.py`,
`r8/framemem.py`.

## 2. Component-by-component prior art

| # | Component | Verdict | Prior art |
|---|---|---|---|
| 1 | Root aliasing; dual-carrier thinning | **textbook, three times over** | Teunissen LAMBDA (1995); Melbourne–Wübbena wide-lane (1985); synthetic-wavelength interferometry; robust-CRT sub-Nyquist |
| 2 | Typed root certificates | partially covered | **IVOA STC 1.33** (near-direct hit); PhysFrame (ICSE 2021); certifying algorithms (McConnell 2011); PTB DCC; PROV-O |
| 3 | Recursive barycentric frames | textbook | IAU 2000/2006; SPICE; astropy; TEMPO2 |
| 4 | Exact radix addressing | **vacuous** | it is arithmetic; "refused as compression" is the absence of a claim |
| 5 | Emission coordinates | textbook | Coll–Ferrando–Morales (2006); Rovelli (2002); bifurcation gating already published |
| 6 | Relativity validation | not a novelty claim | see §4 |
| 7 | Refusal semantics | possibly novel as framing | "rhetoric with a type signature" |

**Component 4 should be deleted from any external version.** Presenting
4096 = 2¹² as a verified result signals an inability to distinguish a
result from a definition, and invites a referee to re-read components
1–3 in that light.

On component 1: the alias count of 4097 candidates per second at
4096 Hz is 2·(4096/2)·1 + 1. Presenting 2N+1 as a finding is
presenting a definition as a discovery.

## 3. The honest residual

> A typed, certificate-carrying coordinate object in which the alias
> set is retained, the frame chain propagates uncertainty, and
> insufficiency is a typed value.

Three caveats, all load-bearing:

- **Each leg is individually prior art.** LAMBDA keeps a candidate
  set. GUM propagates uncertainty. Result types make failure
  first-class. The claim can only ever be about the composition.
- **The composition's value is unproven.** There is no case on record
  where the integrated object caught an error the separate tools
  miss. PhysFrame is the bar: frames as types, evaluated on 180 real
  projects, 154 true-positive inconsistencies found.
- **A framework that has not caught anything is a design document.**
  That is the accurate description of this one today.

### The one piece worth keeping

**The uncertainty-carrying frame chain.** SPICE, astropy and ROS tf2
verifiably do not propagate covariance through a frame chain, and
tf2's omission is a long-standing, explicitly acknowledged
limitation. That is a real unmet engineering need.

It required a fix before it could be claimed at all — see §5.

## 4. Validation status — corrected

An earlier version of this work claimed validation "against two
published measurements." **That claim is withdrawn.**

- **Pound–Rebka.** The 2.45×10⁻¹⁵ figure is the theoretical
  *prediction* gh/c² for the ~22.5 m Jefferson tower. Verified
  directly: 9.80665 × 22.5 / c² = 2.4551×10⁻¹⁵. Comparing our
  2.4551×10⁻¹⁵ against it compares the formula with itself. The
  *measured* value was ≈ (2.57 ± 0.26)×10⁻¹⁵, agreeing to ~10%, and
  that 10% is the actual empirical constraint.
- **GPS.** The third digit of +38.44 vs +38.5 µs/day is a modelling
  convention (assumed orbit radius, eccentricity handling), not a
  measured quantity.

What these establish: the machinery reproduces standard formulae
correctly. That is worth stating and is not validation against
measurement.

## 5. Defect corrected during this work

**R8-D-002 — quadrature accumulation contradicted the covariance
field.** `FrameGraph.total_uncertainty_m` added link uncertainties in
quadrature, which assumes independence. A frame chain typically
shares an ephemeris, a time scale and a calibration across several
transforms, so errors are correlated and quadrature *understates* the
total. Meanwhile the certificate carried a covariance field — the
object claimed to track correlation and then discarded it.

Fixed: uniform pairwise-correlation form, reducing to quadrature at
ρ = 0 and linear addition at ρ = 1, with `worst_case_uncertainty_m()`
as the bound. For a 9-link chain at 2 m per link, quadrature reports
6.0 m against a fully-correlated 18.0 m — understating by 3×.

Note this had to be fixed *before* the frame chain could be offered as
the surviving contribution, since quadrature-only accumulation would
have reproduced rather than fixed the state of the art.

## 6. Evidence status

The coordinate/root thread emits `ANALYTIC_MODEL`,
`DERIVED_ARITHMETIC` and `NUMERICAL_SIMULATION`. It has never emitted
`SYNTHETIC_RUN` or any physical class.

The strongest claim any root certificate can carry is a **bounded
relational root lock**, and even that is demonstrated on synthetic
channels only. `ABSOLUTE_VACUUM_ROOT_UNSUPPORTED` and
`NONLOCAL_REFERENCE_FRAME_UNSUPPORTED` are standing statuses emitted
on every certificate by construction — not conclusions awaiting data.

## 7. Recommended disposition

- **This document**: internal technical report. Preserves the work,
  establishes a date, claims nothing unsupportable.
- **If the code is packaged and documented**: a software paper (JOSS,
  SoftwareX, or *Astronomy & Computing*) on the uncertainty-carrying
  frame chain specifically — with the refusal semantics and typed
  certificates presented as *design decisions*, which is their correct
  epistemic status.
- **Not** *Phys. Rev. D*, *Class. Quantum Grav.*, *J. Geodesy*, or
  *GPS Solutions*.

Before any external version: **engage IVOA STC 1.33 head-on**. It is
the closest structural match to the certificate, and a referee from
the virtual-observatory world will reject on that basis alone if it
goes uncited. **ISO 19111 / OGC Abstract Topic 2** was not checked at
all and should be.

## 8. Disclosure

The material underlying this report (CSCP v4.6.0, PMWR v4.7.0, R3
v4.7.1) was **publicly released under MIT** between 2026-07-18 10:59Z
and 15:40Z, while the repository was public. See
`docs/v51/RGCS_RELEASE_AND_DISCLOSURE_TIMELINE.md`. This bears on any
IP decision and is not addressed by the later `PRIVATE_RC` record.
