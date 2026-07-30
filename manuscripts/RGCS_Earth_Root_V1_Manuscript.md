# A Candidate Hierarchical Earth-Root Coordinate System: Structure, Projection, and Its Limits

**RGCS V1 Technical Manuscript**
Author: Andrew Green · Lane: `r1053` · Status: V1 operational, not physically validated

---

## Abstract

We describe RGCS V1, a research workbench that parses a family of compact decimal
words as hierarchical recursive surface addresses and projects them onto Earth under
a declared candidate law. The structural layer is exact: a 30-bit word admits two
verified field decompositions, its octal rendering partitions a labelled corpus into
two geographically coherent branches with no crossovers, and every source-stated
grammar constraint is enforced by test. The projection layer is not. We show by
direct rank measurement that a scale-invariant 3×3 projective map fitted to three
anchors retains two free parameters, that consequently a zero anchor residual is
guaranteed by construction and carries no information, and that two members of the
same admissible family place one word 5122 km apart — on different continents. We
report one positive result on the refinement ratio, one refutation of a
rotation-only law, and a residual-scale observation reported together with a null
that substantially deflates it. We enumerate seven open blockers and identify the
single input that would make the projection falsifiable: two additional
independently sourced hard anchors.

---

## 1. Claim classes

Results in this programme are typed before they are stated.

| class | meaning |
|---|---|
| `EXACT_ARITHMETIC` | reproducible bit arithmetic; verifiable by re-execution |
| `TRAINING_EQUALITY` | agreement that exists because it was fitted; **not evidence** |
| `PROJECTION_UNDERDETERMINED` | output of a law with free parameters remaining |
| `CANDIDATE_NOT_LOCATED_TARGET` | a projected point, not a place |
| `STRUCTURAL_PARSE_EXACT` | the wire decomposition is exact and reversible |

The distinction that does the most work here is the second. Much of the apparent
progress in coordinate reconstruction consists of quantities that agree because they
were constructed to agree. Section 4 makes that failure mode measurable rather than
rhetorical.

---

## 2. The wire and its structure

### 2.1 Two exact cuts

A direct RGCS word is a 30-bit integer presented in decimal. Its leading `16` is an
artifact of decimal rendering, not a field; stripping it produces a value that is no
longer 30 bits and no longer addresses anything. Two cuts of the same word are used:

```
diagnostic:  R4 | S8  | P12 | tail      (4 + 8 + 12 + 6 = 30)
geometric:   F5 | Q22 | S3              (5 + 22 + 3     = 30)
```

Both are exact and reversible. Neither is privileged. The diagnostic cut yields a
path label `PATH7 = S8₈ ‖ P12₈`; the geometric cut supplies a face index, eleven
two-bit refinement symbols, and a check digit.

For six labelled words the diagnostic decomposition is verified exactly:

| vector | R4 | S8₈ | P12₈ | PATH7 | branch |
|---|---|---|---|---|---|
| `165876523` Stonehenge | 2 | 170 | 6114 | `1706114` | 117 |
| `165892743` Orange A | 2 | 170 | 6512 | `1706512` | 117 |
| `165892763` Orange B | 2 | 170 | 6512 | `1706512` | 117 |
| `165892783` Orange C | 2 | 170 | 6512 | `1706512` | 117 |
| `167849523` Erie | 2 | 200 | 2270 | `2002270` | 120 |
| `168930443` Toronto | 2 | 204 | 3262 | `2043262` | 120 |

The orange triplet shares `PATH7` identically and differs only in the tail. This is
the signature of a same-cell family, and it is independently visible in their mutual
extent (§6.2).

### 2.2 The check digit is not geometry

`S3` is the mandatory terminal check/shell digit. It is excluded from the geometric
kernel, and this is enforced behaviourally rather than asserted: eight words differing
only in `S3` are shown to land in the identical cell. An earlier result reporting
structured angular spacing among sundial-like features was retracted when it was
traced to including this check digit in an angle computation.

### 2.3 The branch partition

The leading three octal symbols partition the labelled corpus:

```
117 → Britain          120 → North America
```

with no observed crossovers. This is the strongest structural result in the
programme, and it was obtained by following an operator instruction to convert to
octal before looking for structure — a reminder that the representation in which a
pattern is sought determines whether it can be seen. An earlier "structured decimal
third digit" claim in the same corpus proved to be a range artifact of the decimal
presentation.

### 2.4 Staged grammar

The fixed-field reading is demoted to a maximum-envelope diagnostic. The active
grammar is staged with floating boundaries:

```
root → section(s) → path step(s) → epoch/state step(s) → M3
```

with `root` fixed at 4 zero-padded bits, `section ≤ 8`, `path ≤ 12`, optional 3-bit
epoch chunks, and a mandatory terminal `M3`. Source constraints require at least one
unit drawn from the section and at least one octal step from the path. Enforcing
these reduces the legal split space to 9, 6, 3 and 1 for widths 27, 30, 33 and 36
bits respectively — a 62 % reduction against the unconstrained enumeration.

### 2.5 Refusal as a design commitment

Records exceeding 30 bits are **refused, never truncated**. Seven such records
(34–41 bits) are gated. The affine transport bridge that would translate them,
`y = (923x + 550585316) mod 2³⁰`, was refuted at R10.47C: a third labelled pair
missed by 484,856,892, and enumerating the complete 32-member `(A,B)` family that
fits the first two pairs, zero members reproduce the third. Two points cannot
over-determine an affine modulo 2³⁰; the earlier "2 of 2 exact" was the minimum
needed to *define* the map, never a test of it. This is the same error, in a simpler
setting, as the projector under-determination of §4.

---

## 3. The Earth frame

Following the SPICE separation — a reference frame is an ordered orthonormal triple
*with a center*, a coordinate system locates points within it, and both plus an epoch
are required for state data — RGCS emits typed certificates rather than bare
coordinates.

The declared V1 frame is:

```
R_E = (O_COM, ẑ_rot, u_Wilkes, u_SAA(t,s), H_SouthUp)
```

with Earth centre of mass as origin, the mean rotation axis displayed South-Up, a
Wilkes Land gravity-anomaly centroid **candidate** as fixed angular root, and the
South Atlantic Anomaly field minimum as a dynamic phase hand evaluated at the encoded
shell radius `r_s = R_E + h_s`. The level-3 datum is mean sea level.

Epoch is **gated, not removed**: structural decoding proceeds without a solved
calendar, but dynamic projection — the SAA phase hand, moving body frames,
barycentric contexts — requires it, and public receipts require declared epoch
metadata regardless.

---

## 4. The projection, and why it is not yet a test

### 4.1 The law

```
u   = kernel(F5, Q22)     source_face = (F5 + 14) mod 20,
                          11 × 4-way spherical refinement at split t
lat/lon = normalize(A u)
```

### 4.2 The rank argument

`A` is used projectively and is therefore scale-invariant: nine entries, **eight free
parameters**. Each anchor contributes the two independent equations of
`e × (A u) = 0`. Three anchors give **six constraints**.

Direct measurement of the constraint matrix gives rank **6** and null-space dimension
**3** — one dimension of overall scale plus **two genuinely free directions**.

Three consequences follow, and all three are asserted as tests:

1. **Every member of the family fits every anchor exactly.** The reported anchor
   residual is 0.000000 km. This is arithmetic.
2. **The family moves non-anchor words without bound.** Perturbing `A` within the
   null space while holding all anchors exact to sub-metre displaces `165879243` by
   40 km, then 87 km, then past 1000 km as the perturbation grows.
3. **Four anchors would not help.** Four gives eight constraints against eight
   parameters — exactly determined, still guaranteed to fit. **Five** is the threshold
   at which the system first becomes over-determined and therefore falsifiable.

A collinearity subtlety is worth recording: `e × (Au) = 0` is satisfied by both `u`
and `−u`, so a large perturbation can send an anchor to its antipode while remaining
formally exact. Resolving that sign is part of the pinning rule.

### 4.3 The recorded pinning

Because two parameters are free, V1 records a rule rather than leaving them implicit:

```
V1_PINNING = MIN_FROBENIUS_NORM_EXACT_FIT_SIGN_FIXED_POSITIVE_ORIENTATION
```

This makes V1 reproducible. It does not make it correct.

### 4.4 The continent disagreement

Under the recorded pinning, all four V1 words project into southern England —
consistent with their shared octal branch `117` and shared source face 18. Under the
operator-supplied member of the same family, the orange triplet agrees to within
~200 km but `165879243` is placed **5122 km away in Quebec**.

| vector | V1-pinned | operator-supplied | gap |
|---|---|---|---|
| `165879243` | 50.849, −0.902 | 45.842, −72.679 | **5121.7 km** |
| `165892743` | 51.275, −1.889 | 50.687, 0.457 | 176.7 km |
| `165892763` | 51.286, −1.920 | 50.675, 0.505 | 182.8 km |
| `165892783` | 51.392, −2.248 | 50.628, 0.667 | 220.9 km |

Both fit all three anchors to machine precision. **The law cannot choose between
them, and one contradicts the branch partition.** This is the sharpest statement of
the problem available: the disagreement is not a numerical nuisance but a question
about which continent a word addresses, and it becomes decidable the moment a fourth
and fifth anchor exist.

---

## 5. What was established about the ratio

Two projection-layer results are positive.

**The source ratio wins.** Scanning all 20 face offsets, depths 9–11, and
`t ∈ {10/19, 1/2, 9/19}`, the value `t = 10/19` is the best-performing split at every
setting. This is weak — it is a comparison among three candidates — but it is a
prediction the source made and the geometry honoured.

**Rotation-only is refuted.** A rotation has three parameters against six
constraints and would have been immediately testable. Its best achievable anchor RMS
across the same scan is **451.6 km**. The free projective form is therefore forced,
not chosen for convenience — the under-determination of §4 is a consequence of the
data, not a modelling preference.

---

## 6. The residual scale

### 6.1 The cell-scale relation

At icosahedral subdivision depth `d` with `R = 6371.0 km`:

```
N_d = 20 · 4^d       A_d = 4πR²/N_d       e_d = √(4A_d/√3)
```

giving `e₉ = 14.989 km`, `e₁₀ = 7.495 km`, `e₁₁ = 3.747 km`. The observed
Drummondville residual against the city label is 15.684 km:

```
15.684 / 14.989 = 1.046
```

one depth-9 cell edge, within 4.6 %.

### 6.2 The null

The depth ladder is geometric with ratio 2, so a tolerance band covers a fixed
fraction of log space, `log₂((1+τ)/(1−τ))`. Against a uniform draw below 60 km:

| τ | P(random residual reads as cell-scale) |
|---:|---:|
| ±30 % | **0.881** |
| ±10 % | 0.294 |
| **±5 %** | **0.147** |
| ±2 % | 0.059 |

**At the ±30 % tolerance under which the observation was first stated, nearly nine
residuals in ten qualify.** The observation survives at ±5 %, where the coincidence
rate is 0.147. That is interesting and it is not a result: it is one observation
against a six-rung ladder. The orange triplet's 16.184 km extent (r = 1.080) is a
second instance, but three points from one `PATH7` family in one neighbourhood are
not three independent words.

### 6.3 The label hypothesis

A separate reading, from a hard-SF engineering prior rather than from RGCS geometry,
notes that a 30 km field-interaction envelope implies a 15 km radius. The two
readings converge numerically without supporting each other. Together they motivate
an operating rule:

```
CITY_NAME  ≠ EXACT TARGET
CITY_NAME  = nearest human-readable regional label
PROJECTED  = operational cell / envelope centre / object-position candidate
```

This is a falsifiable hypothesis about what a coordinate is *for*: it predicts that
projected points should land approximately one cell-width from human labels, on open
terrain. The Drummondville point is 4.939 km from Saint-Eugène in farm country, and
15.684 km WSW of the city centre. One instance is consistent with the rule and does
not establish it.

A category caution applies to the associated witness location: Rue Saint-Frédéric is
where an observer stood, not where an object was over ground. Scoring a projected
object position against an observer position is a category difference, not a residual.

---

## 7. Blockers

| id | severity | statement | clears when |
|---|---|---|---|
| B01 | structural | operator coordinates not reproducible from the stated law; gaps 177–5122 km | pinning recorded upstream, or 4th+5th anchor |
| B02 | structural | three anchors cannot test a free projective law | ≥5 independently sourced hard anchors |
| B03 | structural | `165879243` is branch-117 with a Quebec label | independent coordinate, or demonstrated crossover |
| B04 | evidential | cell-scale reading is n = 1 against a six-rung ladder | ≥3 independent words at the declared relation |
| B05 | operational | no coastline dataset; water acceptance cannot score | dataset present **and** B01/B02 cleared |
| B06 | operational | Saint-Frédéric is a proxy and an observer location | exact civic geocode; observer/object distinction settled |
| B07 | structural | no transport bridge; affine refuted | bridge reproducing all three labelled pairs |

---

## 8. Validation plan

The programme's next steps are ordered by what they would decide, not by effort.

1. **Two additional independently sourced hard anchors.** At five, `A` becomes
   over-determined, the anchor residual becomes informative for the first time, and
   the B01/B03 continent disagreement resolves itself. Nothing else in this list
   compares.
2. **Three independent words at the declared cell-scale relation**, scored without
   retuning, to clear B04.
3. **A coastline dataset**, to activate the water-acceptance criterion. The source
   states that decodes usually land in water; Earth is ~71 % water, so a correct
   decode set must **exceed** that baseline, not merely meet it.
4. **An independent coordinate for `165879243`**, which would settle B03 outright
   whichever way it fell.
5. **A transport bridge reproducing all three labelled pairs**, to open the
   wide-envelope lane.

Until (1) is satisfied, no projected point in this system is a located target, and
every artifact the workbench emits says so.

---

## 9. Boundary

> RGCS V1 is a coordinate/research workbench with a candidate Earth-root projection. It can parse and emit structured vector receipts, reproduce the V1 calibration artifacts, and classify residuals under declared cell-scale and operational-envelope hypotheses. It does not prove physical craft, alien sources, crop-circle authorship, Phryll propulsion, or metric engineering.

Hard-SF and provenance material — Orion's Arm, crop-glyph observations, witness
reports — appears in this programme as a source of distinctions and testable
suggestions. None of it is used as evidence. If every such reference were removed, no
verdict and no blocker in this manuscript would change.
