# Blockers B01–B07

These are the open problems that stand between RGCS V1 and a validated Earth
projector. They are stated here in full and are **not** softened anywhere else in the
documentation. If any public claim in this project appears to contradict one of these,
the blocker wins.

Every one of these is asserted by a test. `test_blockers_are_listed_and_the_structural_ones_named`
fails if a blocker loses its detail or its clearing condition.

---

## B01 — Pinning irreproducibility

**Severity:** STRUCTURAL

The operator-supplied projected coordinates are **not derivable** from the V1 law as
stated. `A` is a scale-invariant 3×3 matrix used projectively — 9 entries, 8 free
parameters — fitted against 6 constraints from 3 anchors. A 2-dimensional family of
matrices remains free, and every member fits all three anchors to machine precision.

Measured gap between this repository's recorded pinning and the operator-supplied
member, for the four V1 targets:

| vector | V1-pinned | operator-supplied | gap |
|---|---|---|---|
| `165879243` | 50.849, −0.902 | 45.842, −72.679 | **5121.7 km** |
| `165892743` | 51.275, −1.889 | 50.687, 0.457 | 176.7 km |
| `165892763` | 51.286, −1.920 | 50.675, 0.505 | 182.8 km |
| `165892783` | 51.392, −2.248 | 50.628, 0.667 | 220.9 km |

The two members **disagree about which continent `165879243` addresses**, and the law
cannot choose between them. This repository's pinning is the one that agrees with the
octal branch partition, landing all four words in southern England — but that is a
consistency argument, not a proof.

**Clears when:** a pinning rule is recorded upstream, **or** a 4th and 5th independent
anchor arrive.

---

## B02 — Three anchors cannot test a free projective law

**Severity:** STRUCTURAL

| quantity | value |
|---|---|
| fit anchors | 3 |
| constraints | 6 |
| free parameters | 8 |
| constraint-matrix rank | **6** (measured) |
| genuinely free directions | **2** |
| anchors needed to over-determine | **5** |

**The reported anchor residual is 0.000000 km, and that is not evidence.** It is
guaranteed by construction. Perturbing `A` inside the null space holds every anchor
exact to sub-metre while a non-anchor word walks 40 km → 87 km → past 1000 km.

A rotation-only law *would* have been testable at three anchors — 3 parameters against
6 constraints. It was scanned across all 20 face offsets, depths 9–11, and
`t ∈ {10/19, 1/2, 9/19}`, and its best achievable anchor RMS is **451.6 km**. So the
free projective form, and this blocker with it, is forced by the data rather than
chosen for convenience.

**Four anchors would not help.** Four gives 8 constraints against 8 parameters —
exactly determined, still guaranteed to fit. **Five** is the threshold at which the
system first becomes over-determined and therefore falsifiable.

**Clears when:** ≥5 independently sourced hard anchors.

---

## B03 — Branch-117 Britain-vs-Quebec conflict

**Severity:** STRUCTURAL

The leading three octal symbols partition the labelled corpus with no observed
crossovers:

```
117 = British branch        120 = North American branch
```

`165879243` has octal `1170616713` — **branch 117** — while its active working label
is *Drummondville / Saint-Eugène*, in Quebec. It also shares source face 18 with the
orange triplet, which projects to southern England ~5,500 km away.

Relabelling the vector from Montréal to Drummondville **did not resolve this**. It
replaced one North American label the branch rejects with another the branch rejects
identically. The conflict carried over from R10.44 B002 is unchanged.

**Clears when:** an independent coordinate for `165879243`, **or** a demonstrated
crossover that breaks the partition.

---

## B04 — Cell-scale reading is n = 1

**Severity:** EVIDENTIAL

The Drummondville residual is 15.684 km and the depth-9 equal-area cell edge is
14.989 km, giving **1.046 cell edges**. The observation is real; its weight is not
what it first appears.

The depth ladder is geometric with ratio 2, so a tolerance band covers a fixed
fraction of log space:

| tolerance | P(random residual < 60 km reads as cell-scale) |
|---:|---:|
| ±30 % | **0.881** |
| ±10 % | 0.294 |
| **±5 %** | **0.147** |
| ±2 % | 0.059 |

**At the ±30 % tolerance the observation was first stated with, nearly nine residuals
in ten qualify.** It survives at ±5 %, where the coincidence rate is 0.147. That is
interesting, and it is **one observation against a six-rung ladder**.

The orange triplet's 16.184 km extent (r = 1.080) is a second instance but **not
independent** — three points from one `PATH7` family in one neighbourhood.

**Clears when:** ≥3 independent hard-labelled words land at the declared
cell-scale/envelope relationship without retuning.

---

## B05 — Coastline / water acceptance not wired

**Severity:** OPERATIONAL

The source states that decodes usually land in oceans or bodies of water. That is the
only decode check available that needs no labelled anchor — once coordinates exist it
scores every decode at once, and a majority-land result would falsify a projector no
anchor test could reach.

It cannot run. There is no coastline dataset in this environment, and the criterion
refuses to approximate a land/water call by eye. It also needs coordinates from a
projector that is not yet determined.

**Earth is ~71 % water, so a correct decode set must *exceed* that baseline, not
merely meet it.** Landing at or below 71 % is not support.

**Clears when:** a coastline dataset is present **and** B01/B02 are cleared.

---

## B06 — Saint-Frédéric is a proxy *and* an observer location

**Severity:** OPERATIONAL

The coordinate `45.883, −72.486` is supplied as a proxy pending an exact civic point.
More importantly, Rue Saint-Frédéric is where a **witness stood** in 2015 — not where
an object was over ground.

Scoring a projected object position against an observer position is a **category
difference, not a residual**. The row is reported for completeness and is not treated
as a hit.

**Clears when:** an exact civic geocode is supplied **and** the observer/object
distinction is settled.

---

## B07 — No transport bridge

**Severity:** STRUCTURAL

Seven wide-envelope records (34–41 bits) cannot enter the 30-bit direct lane. They are
**refused, never truncated** — truncating would manufacture a false address.

The bridge that would translate them, the header-stripped affine
`y = (923x + 550585316) mod 2³⁰`, was **refuted** at R10.47C. A third labelled pair
(`1658274383 → 165892733`) was the first out-of-sample test and missed by
484,856,892. Enumerating the complete 32-member `(A,B)` family that fits the first two
pairs, **zero** members reproduce the third.

Two points cannot over-determine an affine modulo 2³⁰ — the earlier "2 of 2 exact" was
the minimum needed to *define* the map, never a test of it. This is the same error, in
a simpler setting, as B02.

**Clears when:** a bridge reproducing all three labelled pairs.

---

## Summary

| id | severity | clears when |
|---|---|---|
| B01 | structural | pinning recorded upstream, or 4th+5th anchor |
| B02 | structural | ≥5 independently sourced hard anchors |
| B03 | structural | independent coordinate, or demonstrated crossover |
| B04 | evidential | ≥3 independent words at the declared relation |
| B05 | operational | coastline dataset **and** B01/B02 cleared |
| B06 | operational | exact civic geocode; observer/object distinction settled |
| B07 | structural | bridge reproducing all three labelled pairs |

**The single highest-value input is two more independently sourced hard anchors.** At
five, `A` becomes over-determined, the anchor residual becomes informative for the
first time, and B01/B03 resolve themselves. Nothing else on this list compares.
