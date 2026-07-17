# Eye refinement V5 (Agent C02)

Coverage: **A07–A10**. Gates: **G07, G08**.
Status: **`NEAR_CONVENTIONAL_NODE_BUT_DISTINCT` — RESOLVED.**
Artifact: [`proof/C02/refinement_ladder_v5.json`](proof/C02/refinement_ladder_v5.json).
Reproduce: `python tools/v4x_eye_refinement_v5.py --budget 400`.
Companion: [V4X_EYE_SUBMM_REFINEMENT.md](V4X_EYE_SUBMM_REFINEMENT.md)
(the preliminary ladder).

## Headline

**The question is resolved, and the answer changed.**

For the first time the localization halfwidth (**1.803 mm**) is smaller
than the candidate-to-station separation (**6.298 mm**) — by a factor of
3.5. The two positions are numerically distinguishable, so the
comparison finally carries information.

**The conventional station does not explain the candidate.**

And a second finding, which matters as much: **the v4.1 canonical
candidate coordinate does not survive mesh refinement.** The candidate
converges to z ≈ 99.78 mm, not the recorded 102.240 mm.

Both results are **computational**, on an **ideal** geometry, with **no
experimental confirmation of anything**.

## The naming correction (V4X-D-011)

The v4.2.0 document called its work a **"sub-millimetre refinement"**.
Its mesh characteristic lengths were **8.0, 5.5, and 4.5 mm**.

That is not sub-millimetre resolution, and the title oversold the run
by roughly an order of magnitude. The v4.2.1 audit renames it what it
is: a **preliminary refinement ladder**. The previous record is
preserved unchanged — it is honest about its own numbers in the body
text, and only the framing was wrong.

## The question

Is the Eye candidate at (−0.295, −0.205, 102.240) mm distinct from the
nearest conventional station at (−0.447, 0.774, 106.018) mm — a
separation of **3.906 mm** with a localization halfwidth of 3.08 mm?

Exact coincidence means agreement within **1e-6 mm** (numerical
tolerance). **No proximity threshold is used, ever.** A separation of
3.906 mm is reported as 3.906 mm.

## The preliminary ladder (v4.2.0) and why it could not answer

| Level | clmax | centroid (mm) | spacing |
|---|---|---|---|
| coarse | 8.0 | (−0.256, 0.016, 102.288) | 6.896 |
| fine | 5.5 | (−0.060, 0.051, 102.307) | 4.972 |
| finer | 4.5 | (0.090, −0.321, 102.053) | 4.096 |

The halfwidth (4.096 mm) exceeded the separation (4.149 mm at that
level), so the comparison carried no information:
`INSUFFICIENT_RESOLUTION`. Its "sub-millimetre" title was wrong by an
order of magnitude (V4X-D-011).

## The V5 ladder (v4.2.1)

Global refinement, 8 elastic modes per level, on the ideal N=7 body:

| Level | spacing (mm) | centroid (mm) | d(v4.1 coord) | d(station) | f₁ (Hz) | dof |
|---|---|---|---|---|---|---|
| cl3.0 | 3.423 | (0.237, −0.010, 100.986) | 1.375 | 5.138 | 13772.75 | 5 394 |
| cl2.0 | 2.362 | (−0.053, −0.038, 99.989) | 2.270 | 6.096 | 13772.38 | 14 550 |
| **cl1.5** | **1.803** | **(−0.048, −0.020, 99.783)** | **2.476** | **6.298** | 13772.28 | 30 816 |

Convergence evidence:

- **Transverse converged.** (−0.053, −0.038) → (−0.048, −0.020): the
  last two levels agree to 0.02 mm, ~100× below the element spacing.
- **Axial converging.** Centroid shifts 1.039 mm → 0.207 mm — a 5×
  reduction per level. Geometric extrapolation puts the limit at
  z ≈ 99.73 mm.
- **Frequencies converged.** 13772.75 → 13772.38 → 13772.28 Hz
  (0.37 → 0.10 Hz).
- **Halfwidth 1.803 mm < separation 6.298 mm** — resolved by 3.5×.

## Verdict: NEAR_CONVENTIONAL_NODE_BUT_DISTINCT

Per the V4C-D-001 rule, `NEAR_..._BUT_DISTINCT` and `DISTINCT_FROM_...`
are **both scientifically distinct**; "near" is descriptive only. The
separation is reported at its exact value, 6.2976 mm, and exact
coincidence remains the 1e-6 mm numerical tolerance.

**The implemented conventional model does not explain this candidate.**
That is the opposite of the v4.1 posture
(`UNCERTAINTY_OVERLAPS_CONVENTIONAL_NODE` — "may explain within
uncertainty"), and it is now resolved rather than merely open.

## The v4.1 coordinate does not survive refinement

This is the finding to read twice. The candidate's distance from the
recorded v4.1 coordinate **grows** monotonically as the mesh improves:
1.375 → 2.270 → **2.476 mm**. It is not converging on (−0.295, −0.205,
102.240); it is converging on **(−0.048, −0.020, 99.78)**.

The selection rule picks the strain-energy cluster *nearest the v4.1
coordinate*. At cl=1.5 the nearest cluster is 2.476 mm away — so at
this resolution **there is no cluster at z = 102.24**.

The honest reading: **the v4.1 candidate coordinate was
mesh-dependent.** It was obtained at ~4 mm spacing, where the
localization halfwidth exceeded the very distances being discussed.

The canonical record is **preserved unchanged** (G07) — it is a
faithful record of what that computation produced. What changes is its
interpretation: it is a resolution-limited coordinate, not the
converged one. The candidate was never moved onto the comparator, and
the comparator was never moved onto the candidate.

## Resource limit — an honest stop

`cl=1.25` was **not attempted**. Measured cost at cl=1.5: **~13.9 GB
resident** and ~14 min on a 31.6 GB machine with 4.5 GB free. The
calibrated projection for cl=1.25 (69 471 dof) is **~45 GB** —
infeasible here, so the run stopped and said so rather than thrashing.

A memory guard now refuses a level that would leave < 6 GB free, and
the ladder writes results after **every** level so an infeasible level
cannot destroy the completed ones.

**Correction to the earlier estimate.** The first resource estimate
projected 0.29 GB at cl=1.25 using the textbook nnz(LU) ~ dof^1.5 rule.
That is a 2-D result; 3-D tetrahedral factors grow ~dof², and the
estimate was wrong by roughly 150×. It was corrected against the
measurement, not before it.

## Queued-compute package

To go below ~1.5 mm on this problem, one of:

1. **Iterative eigensolver** — LOBPCG with an AMG preconditioner,
   avoiding the LU factor entirely. Memory becomes O(dof) instead of
   O(dof²). This is the cheapest real path.
2. **Nested local refinement** — a gmsh size field around the
   candidate, station, and junction, holding the global body coarse.
   Keeps dof low but entangles the convergence rate with the size
   field's shape, so the uniform ladder above should remain the
   headline.
3. **Larger machine** — cl=1.25 needs ≳48 GB; cl=1.0 needs ≳150 GB.

Exact reproduction: `python tools/v4x_eye_resource_estimate.py` then
`python tools/v4x_eye_refinement_v5.py --deep`.

## Preserved regardless of outcome (G07)

- Candidate: (−0.295, −0.205, 102.240) mm
- Station: (−0.447, 0.774, 106.018) mm
- Separation: **3.906 mm** — exact, never absorbed into a threshold
- Halfwidth: 3.08 mm · convergence shift: 0.353 mm · cloud RMS:
  0.032 mm · tolerance: 1e-6 mm

## What is NOT claimed

- **No experimental confirmation.** Nothing here was measured. This is
  a computation on an ideal geometry.
- **Not "the Eye is real".** A resolvable strain-energy cluster in a
  model is a property of the model. Whether any physical crystal does
  anything at that coordinate is untested and untestable without the
  hardware in [METROLOGY_PROTOCOL.md](METROLOGY_PROTOCOL.md).
- **Single mode, single orientation.** The first elastic mode of an
  ideal body with an assumed C-axis. No specimen has been XRD-oriented
  (see [XRD_ORIENTATION_CONTRACT.md](XRD_ORIENTATION_CONTRACT.md)), and
  the elastic model is orientation-dependent.
- **Still converging.** The 0.207 mm final shift is small relative to
  the 6.298 mm separation but is not zero.

## Preserved regardless of outcome (G07)

- Candidate: (−0.295, −0.205, 102.240) mm
- Station: (−0.447, 0.774, 106.018) mm
- Separation: **3.906 mm** — exact, never absorbed into a threshold
- Halfwidth: 3.08 mm · convergence shift: 0.353 mm · cloud RMS:
  0.032 mm · tolerance: 1e-6 mm

The candidate has **not** been moved onto the comparator, and the
comparator has not been moved onto the candidate.

## D9/D10 driven diagnostics (A09)

Complex driven response via `fem.harmonic_field` at the first elastic
mode: mean phase coherence **0.773**, **4** phase singularities on the
interpolated x–z plane. These are properties of the computed field,
reported as such, and are not evidence for the candidate.

The realness guards in `eye.phase_coherence_field` and
`phase_singularities_on_plane` were changed from an absolute
`np.allclose(w.imag, 0)` to a relative test (`max|Im w| < 1e-12 ×
scale`). The absolute form rejected genuine complex driven responses at
small amplitude — a solver-scale artifact, not physics.

## Frequency sensitivity (A10)

`frequency_sensitivity_map` evaluated at candidate, station, and
midpoint. A derived sensitivity of modal frequency to coordinate
perturbation; it carries no claim about which location is preferred.

## Honest bottom line

The Eye question is **open**, and this programme has not closed it. It
is not a blocker on releasing the rest of the work — it is a result:
the resolution ran out before the question did.

## Appended: the independent census (Y03, emergent programme)

The account above used nearest-to-candidate selection. The unbiased
full-domain census (`tools/v4x2_eye_census.py`,
[`proof/C02/independent_census.json`](proof/C02/independent_census.json))
corrects one framing and adds structure:

- **One apex feature, two estimates.** The v4.1 (z = 102.24 mm) and V5
  (z = 99.78 mm) coordinates are 2.53 mm apart; the census shows a
  single persistent male-apex concentration whose centroid estimate
  moves from ~102 mm (coarse) toward ~99.8 mm (fine). "The v4.1
  coordinate does not survive refinement" conflated the estimate with
  the feature — the FEATURE survives; the ESTIMATE was
  resolution-dependent.
- **The station comparison stands** (5.1–6.7 mm across meshes and
  diagnostics, halfwidth ~1.8 mm at the finest level).
- **The feature has a family**: a mirror concentration near the female
  apex (z ≈ 4 mm) and a symmetric mid-shaft D2 pair (z ≈ 58 mm). Any
  unique-point narrative must contend with this symmetry.
- **No mode switch**: the first elastic eigenspace tracks across
  meshes with principal angles < 2.7° (MAC/subspace, not index).

Current wording of record: see
[EYE_CLAIM_CARD.md](EYE_CLAIM_CARD.md), card **v4**.
