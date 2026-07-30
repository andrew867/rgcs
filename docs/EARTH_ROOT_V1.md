# RGCS V1 Earth Root — Final Specification

```text
SPEC_STATUS:        V1_CANDIDATE_LOCKED
PHYSICAL_STATUS:    NOT_VALIDATED
PUBLICATION_STATUS: RELEASE_ALLOWED_WITH_BOUNDARY
```

> RGCS V1 is a coordinate/research workbench with a candidate Earth-root projection. It can parse and emit structured vector receipts, reproduce the V1 calibration artifacts, and classify residuals under declared cell-scale and operational-envelope hypotheses. It does not prove physical craft, alien sources, crop-circle authorship, Phryll propulsion, or metric engineering.

---

## 1. Frame-first principle

The NAIF/SPICE frame model makes a separation RGCS had been eliding, and it is the
organising idea of this spec:

- a **reference frame** is an ordered set of three orthogonal unit-length direction
  vectors, and it has an associated **center**;
- a **coordinate system** is the mechanism used to locate points *within* that frame;
- state and pointing data require knowing **both**, plus an **epoch** whenever the
  frame is time-dependent.

A compact RGCS vector is therefore **not** a naked latitude/longitude. It expands into
a typed *address certificate*. This is implemented in
[`r1053/certificate.py`](../r1053/certificate.py) — `frame_manifest()` and
`address_certificate()` — so that no coordinate leaves the system without the frame it
was expressed in.

---

## 2. Earth root D_V1

```
R_E = (O_COM, ẑ_rot, u_Wilkes, u_SAA(t,s), H_SouthUp)
```

| element | value | role |
|---|---|---|
| `O_COM` | Earth centre of mass | frame center |
| `ẑ_rot` | mean rotation axis | primary axis |
| `H_SouthUp` | South-Up display | viewed externally above Antarctica, positive rotation is clockwise |
| `u_Wilkes` | Wilkes Land gravity-anomaly centroid **candidate** | fixed angular root |
| `u_SAA(t,s)` | South Atlantic Anomaly field minimum | dynamic phase hand |
| datum | mean sea level | level-3 reference |

`u_Wilkes` is a **candidate**, not a confirmed root. It is recorded as a declared
frame element so that a competing root can be tested against the same certificates.

---

## 3. Dynamic phase hand

The shell determines the radius at which the SAA phase hand is evaluated:

```
r_s      = R_E + h_s
r_SAA(t,s) = argmin_{|r| = r_s} |B(r, t)|
```

No separate altitude field is missing for this layer. The address already supplies
body, shell, epoch, and therefore the magnetic evaluation surface. This is the one
place in V1 where **epoch is not optional** — see
[Frames, Epochs and Galactic Directions](FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md).

---

## 4. Projection stages

```
wire codec → canonical hierarchical address → body-specific projection → conventional display
```

The final lat/lon is a **projection artifact**. The native RGCS object is:

```
body + frame + epoch + root + ordered path + shell/state + local coordinate + uncertainty
```

Concretely, the V1 law is:

```
direct RGCS-30 word
  → F5 | Q22 | S3
  → source_face = (F5 + 14) % 20
  → 11 × 4-way spherical refinement at split t = 10/19
  → lat/lon = normalize(A u)
```

---

## 5. The pinning problem — stated, not hidden

`A` is used projectively, so it is scale-invariant: **9 entries, 8 free parameters**.
Each anchor contributes the two independent equations of `e × (A u) = 0`.

| quantity | value |
|---|---|
| fit anchors | 3 (Stonehenge, Erie, Toronto) |
| constraints | 6 |
| free parameters | 8 |
| constraint-matrix rank | **6** (measured, not assumed) |
| null-space dimension | 3 |
| genuinely free directions | **2** |
| anchors needed to over-determine | **5** |

**Anchor residuals are 0.000000 km, and that is not evidence.** It is guaranteed by
construction. Perturbing `A` inside the null space keeps every anchor exact to
sub-metre while a non-anchor word walks past 1000 km — this is asserted as a test, not
a claim (`test_the_free_family_really_does_move_a_non_anchor_word`).

V1 therefore **records a pinning rule** rather than leaving the two parameters implicit:

```
V1_PINNING = MIN_FROBENIUS_NORM_EXACT_FIT_SIGN_FIXED_POSITIVE_ORIENTATION
```

This makes V1 reproducible. It does **not** make it correct.

---

## 6. Nonlinear projection is required

A rigid regular icosahedron was excluded: the Wilkes-rooted regular midpoint model
missed Stonehenge by about **6.82°** in the earlier audit. WGS84/ellipsoid
compensation is mandatory for precision but cannot alone explain that gap.

Independently, a **rotation-only** law was tested and refuted. A rotation has 3
parameters against 6 constraints and would have been testable immediately. Scanned
across all 20 face offsets, depths 9–11, and `t ∈ {10/19, 1/2, 9/19}`, the best
achievable anchor RMS is **451.6 km**. The projection must remain face-dependent and
nonlinear.

One positive from that scan: **`t = 10/19` is the best-performing split of the three
tested, at every depth and every offset.** The source ratio beats the midpoint.

---

## 7. The branch conflict (V1-B03)

The leading three octal symbols partition the labelled corpus with no crossovers:

```
117 = British branch      120 = North American branch
```

Under the recorded V1 pinning, all four V1 words land in **southern England**, which
is what branch 117 predicts. The operator-supplied member agrees for the orange
triplet to within ~200 km but sends `165879243` **5122 km** to Quebec.

Both members fit all three anchors to machine precision. **The law cannot choose
between them, and one contradicts the branch partition.** This is a decidable
question the moment a 4th and 5th anchor exist.

---

## 8. V1 blockers retained

| id | blocker |
|---|---|
| B01 | pinning irreproducibility |
| B02 | three hard anchors cannot test a free projective law |
| B03 | branch-117 Britain-vs-Quebec conflict |
| B04 | 15 km cell-scale n=1 |
| B05 | no coastline / water-acceptance layer |
| B06 | Saint-Frédéric is a proxy **and** an observer location |
| B07 | no transport bridge |

See also: [Variable Codec Spec](VARIABLE_LENGTH_CODEC.md) ·
[15 km Field Envelope Model](15KM_CELL_FIELD_ENVELOPE_MODEL.md) ·
[Frames and Epochs](FRAMES_EPOCHS_AND_GALACTIC_DIRECTIONS.md)
