# Spiral-cone model (Agent G01)

Coverage: **S001–S011**. Gates: **G16, G17**.
Status: `REDUCED_ORDER_VALIDATED` (mathematics) /
`ENGINEERING_PROTOTYPE` (merit, exports).
Implementation: [`rscs2_core/spiral_cone.py`](../../rscs2_core/spiral_cone.py).

## Validated mathematics

| Quantity | Relation | Status |
|---|---|---|
| Logarithmic spiral | r(θ) = r₀ e^(−aθ) | DER |
| Curvature invariant | κ·r = 1/√(1+a²) | DER, checked numerically |
| Per-turn ratio | q_s = e^(−2πa) | DER |
| Stable focus | eigenvalues of [[−a,−1],[1,−a]] = −a ± i | DER, exact |
| Scale ratios | a = ln(ratio)/2π for φ, 2, e, 8 | DER |

`numeric_curvature_times_r()` differentiates the sampled spiral and
recovers the invariant — the analytic claim and the numerical one are
checked against each other rather than asserted.

## The pinched twisted cone (G17)

`spiral_cone_path(..., twist_pinch>0)` generates the geometry the
source actually describes: a twisted cone-tube, **pinched in the
middle, extending to a point** — not a generic cone. The twist adds an
azimuthal advance proportional to height; the pinch scales the radius.
`openscad_text()` carries the `pinch` parameter into the SCAD source.

## The cusp metric — audited (V4X-D-005)

`cusp_response_metric()` returns the fraction of |amplitude|²
concentrated within the innermost 10% radius, **arc-length weighted**.

### The audit premise was wrong, and the record is corrected here

The v4.2.1 audit was asked to investigate a suspected post-hoc
acceptance: *"the cusp test expected >5× and was changed after
observing ~1.44×."* **That is not what happened**, and the git history
settles it: the `5 *` threshold appears in exactly one commit
(`bcd27b2`, where the test was first written) and **has never been
modified**. The test still asserts >5× today.

What actually happened is worse and more interesting: **the metric was
broken, not the test.**

### The bug

The original metric summed |amplitude|² over path *samples*. But the
spiral is sampled uniformly in θ, and a logarithmic spiral crowds
θ-uniform samples near its centre. Measured on the standard fixture:

| Measure | Inner 10% radius |
|---|---|
| fraction of path **samples** | **69.5%** |
| fraction of path **arc length** | **9.3%** |

So the unweighted metric reported that a perfectly **uniform** field
had 69% of its energy concentrated at the cusp. That number was
measuring the sampling grid, not the geometry. The concentrated field
scored 0.999 and the uniform field 0.695 — a ratio of 1.438, which
failed the (correct) 5× expectation.

### The fix and its independent check

Arc-length weighting makes the metric measure the path:

| | concentrated | uniform | ratio |
|---|---|---|---|
| unweighted (buggy) | 0.9989 | 0.6945 | 1.438 |
| **arc-length weighted** | **0.9810** | **0.0928** | **10.576** |

The acceptance criterion is **not** the observed number. It is an
independent analytic control: a uniform field's concentration must
equal the **fraction of arc length** inside the inner radius, which is
0.0928. The weighted metric returns **0.0928**. The metric and the
geometry agree to four decimals, which is what justifies the metric —
not the fact that the test now passes.

`test_uniform_field_metric_equals_arclength_fraction` pins exactly
that, so the metric cannot silently regress to measuring its own
sampling.

### Consequence for the "singularity" reading

**ORPHAN-009 rejects the singularity claim on evidence**: the
concentration is **10.58×**, which is a real and useful focusing
effect — and it is *finite*. A singularity would diverge with
refinement. This does not. A geometric point of high curvature is not
a physical singularity.

## Mode overlap and merit

`mode_overlap()` is the normalized inner product Λ_ab — a real
quantity. `geometry_merit()` is Γ_s = cusp · |Λ| · log₁₀(1+Q) and is
**declared ENG**, with `note: carries no physical significance claim`.
It ranks designs. It predicts nothing.

## Controls (G20)

`archimedean_control()` supplies the matched non-logarithmic spiral.
The G01 rule is that a claim about the log spiral must beat a
*geometrically matched* control, not empty space. Mass-matched and
plain-cone controls come from the G02/G03 control set.

## Boundaries

- **No singularity claim.** The cusp is a geometric point of high
  curvature with a finite computed response.
- **No exotic field claim.** A converging spiral trajectory is a
  solution of a declared linear ODE (ORPHAN-008 translates the source
  "vortex" here).
- **51.843° is a cut/interface angle, not a spiral parameter.** The G01
  prompt is explicit; no tested spiral equation requires it, and it is
  not imported into the spiral mathematics.
- **Visual resemblance is not evidence.** A shape resembling a fossil,
  a shell, or a diagram is a shape.

## Fabrication

`openscad_text`, `dxf_polyline_text`, `stl_text_from_path` — see
[FABRICATION_CONTRACT.md](FABRICATION_CONTRACT.md) for validity
evidence. No spiral cone has been fabricated or measured.
