# The 15 km Residual — Cell Scale and Field Envelope Model

```text
STATUS:    PROMOTED_V1_HYPOTHESIS
NOT_PROOF: TRUE
BLOCKER:   V1-B04 (n = 1)
```

The 15 km offset is not one thing. It has **two independent interpretations that
converge numerically**. They do not prove each other, and they are documented
separately for that reason.

---

## 1. RGCS cell-scale derivation

At icosahedral 4-way subdivision depth `d`, with mean Earth radius `R = 6371.0 km`:

```
N_d = 20 · 4^d                    cells
A_d = 4πR² / N_d                  area per cell
e_d = √(4 A_d / √3)               equal-area equilateral edge proxy
```

Computed by `r1053.kernel.cell_edge_km`:

| depth | cells | cell area (km²) | edge proxy (km) |
|---:|---:|---:|---:|
| 7 | 327,680 | 1556.593 | 59.957 |
| 8 | 1,310,720 | 389.148 | 29.978 |
| **9** | **5,242,880** | **97.287** | **14.989** |
| 10 | 20,971,520 | 24.322 | 7.495 |
| 11 | 83,886,080 | 6.080 | 3.747 |
| 12 | 335,544,320 | 1.520 | 1.874 |

Observed Drummondville residual:

```
15.684 km / 14.989 km ≈ 1.046
```

**The residual is one depth-9 cell edge, with +4.6 % deviation.**

---

## 2. Field-envelope analogue

The Orion's Arm plasma-magnet page gives a 30 km magnetic interaction envelope for a
small plasma magnet. **As a hard-SF design prior only:**

```
30 km diameter → 15 km radius
```

This suggests a separate operational reading:

```
coordinate pin    = field-envelope centre candidate
human place label = nearest recognisable witness/city label
15 km             = stand-off / local operational radius
```

**This is not evidence of a real plasma magnet in RGCS.** It is an engineering-scale
convergence, and Orion's Arm is a collective hard-science-fiction worldbuilding
project, not a factual source. See
[OA Convergence Ledger](OA_CONVERGENCE_LEDGER.md).

---

## 3. The label rule

The two readings converge on the same operating rule:

```
CITY_NAME  ≠ EXACT TARGET
CITY_NAME  = nearest human-readable regional label
PROJECTED  = operational cell / field-envelope centre / object-position candidate
```

If you were operating something aerial, quiet, large, and unadvertised, you would not
pin the town hall. You would pick somewhere near enough to a named place for
reference, far enough from population density, flat and open, with road access but not
downtown. That is a *hypothesis about what a coordinate is for*, and it is testable:
it predicts that projected points should repeatedly land one cell-width from human
labels, on open terrain.

### Scoring bands

| distance | band |
|---|---|
| 0–5 km | `LOCAL_HIT` |
| 5–15 km | `SAME_CELL_OR_NEAR_FIELD_RADIUS` |
| 15–25 km | `ADJACENT_CELL / FIELD_ENVELOPE_EDGE` |
| 25–75 km | `REGIONAL_CORRIDOR` |
| 75–200 km | `COARSE_V1_CORRIDOR` |
| > 200 km | `WEAK_OR_FAIL_PENDING_SEMANTICS` |

---

## 4. The Drummondville measurement

Projected point `45.8418969, −72.6788251`:

| reference | distance | bearing | band | cell scale |
|---|---|---|---|---|
| Saint-Eugène | **4.939 km** | 019° | `LOCAL_HIT` | — |
| Rue Saint-Frédéric proxy | 15.615 km | 253° WSW | adjacent-cell | depth 9, r = 1.042 |
| Drummondville city | 15.684 km | 254° WSW | adjacent-cell | depth 9, r = 1.046 |

Saint-Eugène's official toponymy coordinate is under 5 km from the projected point.
Saint-Edmond-de-Grantham and Saint-Guillaume lie in the same rural corridor. The
projected point is farm country WSW of the city, not downtown.

**Rue Saint-Frédéric is where a 2015 witness stood, not where an object was over
ground.** Scoring a projected object position against an observer location is a
category difference, not a residual — this is blocker B06, and it is why that row is
reported but not treated as a hit.

---

## 5. Null caution — read this before quoting the result

The depth ladder is **geometric with ratio 2**, so a loose tolerance tiles the whole
range. The fraction of log-space a ±tol band covers is `log₂((1+tol)/(1−tol))`.

Measured by `r1053.residuals.cell_scale_null_sweep` against a uniform draw below 60 km:

| tolerance | P(random residual looks cell-scale) | analytic |
|---:|---:|---:|
| ±30 % | **0.881** | 0.893 |
| ±20 % | 0.588 | 0.585 |
| ±10 % | 0.294 | 0.290 |
| **±5 %** | **0.147** | 0.144 |
| ±2 % | 0.059 | 0.058 |

**At the ±30 % tolerance the observation was first stated with, nearly nine residuals
in ten qualify.** That framing carries no information.

The observed deviation is **0.046**, so it survives at ±5 %, where the coincidence
rate is **0.147**. That is genuinely interesting — and it is still **one observation
against a six-rung ladder**.

```
Drummondville:         n = 1 independent word
Orange triplet extent: 16.184 km, r = 1.080 — related support, NOT independent
                       (three points from one neighbourhood, one PATH7 family)
```

**V1-B04 clears only after at least three independent hard-labelled words land at the
declared cell-scale/envelope relationship without retuning.**
