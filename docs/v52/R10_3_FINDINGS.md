# RGCS R10.3 — Toroidal Source, Density, Nodes, Quadrature: Findings

**Status:** `SOFTWARE_VERIFIED` · `PHYSICAL_VALIDATION_NOT_CLAIMED`
**Baseline:** v5.4.1 (`a76174b`)
**Evidence class:** `DERIVED_MATHEMATICS` and typed source records.
**Hardware:** deferred. **No apparatus has been built or measured.**

---

## Gate Zero

Repository truth at v5.4.1 / `a76174b`, tree clean, clean-clone 2867,
both package lists equal. Private corpus: no remote, outside the public
worktree, firewall zero findings. Nothing to reconcile.

## Scope, stated plainly

This is a 24-phase pack about a nine-"density" ontology, a toroidal-Source
cosmology, geographic "node/gateway" sites, and a coil apparatus. Most of
it is lore, and the pack's own hard rules — which match this project's
standing discipline — forbid promoting any of it to physical evidence.

**What went public: five typed engines, each built around the firewall
that keeps its subject honest.** The operator hypothesis delta, the
source transcripts, and any named-site intuition stay in the private
repository. No real person is named or classified; no gateway, stargate,
Phryll, gravity, or instantaneous-transfer status is asserted.

---

## The headline: named sites do not beat chance (P08/P13)

**Module:** [`r10/nodes.py`](../../r10/nodes.py)

"Do these special sites form a Platonic solid on the globe?" is a
look-elsewhere trap, and quantifying the trap is the contribution. To fit
N sites to a polyhedron you get to choose the polyhedron (five families,
4–20 vertices), its orientation (3 continuous degrees of freedom), which
vertex each site maps to, and how much coordinate slop counts as "near".
**With that much freedom a handful of points fits *something* almost
always** — so a small residual is not evidence.

`alignment_pvalue()` runs the identical best-fit search on the real sites
and on many random site sets, and reports the fraction of random sets
that fit at least as well:

| Sites | Best residual | Null median | p | Verdict |
|---|---|---|---|---|
| 4 random | 13.5° | 13.5° | 0.51 | NO_BETTER_THAN_CHANCE |
| 8 random | 17.2° | 18.2° | 0.24 | NO_BETTER_THAN_CHANCE |
| 8 on an exact cube | 5.9° | 18.2° | **0.003** | TIGHTER_THAN_CHANCE |

The machine has **power** — a genuine cube scores p = 0.003 — and it
returns the honest null on random points. This is the CW
`EXPLAINED_BY_CONSTRUCTION` result again, in geography: alignment is only
evidence if it beats the same search on random sites, and small point
sets do not.

The public registry holds **public heritage coordinates only** (Giza,
Chichén Itzá). Antarctica and the Bahamas "crystal sphere" narrative have
no established coordinate and are held `LOCATION_UNKNOWN` — a status the
module refuses to overwrite without a cited authority. **Only two public
sites are located, which is too few to test a polyhedron at all**, and the
module says so rather than padding the set. Gateway and stargate statuses
are pinned `UNSUPPORTED` and cannot be set positive.

---

## Density is not dimension (P02/P03)

**Module:** [`r10/density.py`](../../r10/density.py)

The nine-step "density" ladder is a source ontology, and the first thing
the module enforces is the confusion most likely to occur: **source
"density" is not mathematical dimension and not mass density.** "Density
4" is the source's phrase for "time and free will", not a 4-space and not
kg/m³. `refuse_dimension_conflation()` raises on it.

**Only two numbers are supplied:** the light-body fraction is 0.5 at step
6 and the Source endpoint is step 9. Everything else is honest about its
support:

| Steps | Light fraction |
|---|---|
| 1–5 | **UNSUPPLIED** — no anchor below 6, so any number is extrapolation from one point. Refused. |
| 6 | 0.500 (anchored) |
| 7 | 0.67 ± 0.12 (model-derived band) |
| 8 | 0.82 ± 0.09 (model-derived band) |
| 9 | 1.000 (anchored) |

The band is the spread of three monotone models pinned to the two
anchors — genuine model disagreement, not a decorative error bar.
`light_fraction_point()` refuses to hand out a bare number where only a
band exists.

---

## Quadrature polarity, and four poles are not four charges (P15/P17)

**Module:** [`r10/polarity.py`](../../r10/polarity.py)

Four spatial channels at 0/90/180/270° with signed currents. Ideal
sinusoidal quadrature produces a genuine constant-magnitude rotating
field — mean magnitude 2A, **relative ripple 3×10⁻¹⁶**, sweeping the full
circle. The balanced sign patterns sum to exactly zero current
(`Fraction`-exact).

**The firewall:** four spatial poles do **not** imply four charge
polarities. Charge has two signs; the four poles are coil positions that
make a rotating field from ordinary AC. `refuse_four_charge_polarities()`
raises on the conflation.

The six-pole comparison is quantitative and clean:

| Scheme | THD | Field directions | Verdict |
|---|---|---|---|
| True six-phase | ~0 | 720 | rotates |
| Dual three-phase | ~0 | 720 | **identical to six-phase** |
| Alternating triads | 0.31 | ~7 | **steps, does not rotate** |

Six-phase and dual-three-phase trace the identical locus (they are the
same drive rewritten); alternating triads step the field in discrete
jumps. No coil was built; every report is `DERIVED_MATHEMATICS`,
`measured_here: nothing`.

---

## The torus is geometry; the cosmology is not entailed (P04–P07)

**Module:** [`r10/toroid.py`](../../r10/toroid.py)

A torus is ordinary geometry — exact area, volume, winding, and a
hierarchical CW toroidal address (parent-domain prepend, two angle
fields, mandatory frame/epoch). The "Source zero-point" is the origin: a
hole, geometrically central and physically empty.

Two firewalls carry the module:

- **Toroidal EM is not spacetime torsion.** A coil makes an ordinary
  magnetic field; GR torsion is a property of a connection. Same Latin
  root, nothing else. `refuse_torsion_conflation()`.
- **No channel beats light.** "Broadcast outside ordinary time" gets a
  causality firewall: `CONVENTIONAL_DELAYED` (a real mechanism, finite
  latency) and `SHARED_STATE` (real, but transmits no information faster
  than light) are supported; `NONLOCAL_TRANSFER` is `UNSUPPORTED`. A
  claimed 0-second latency over 1 AU (light floor 499 s) returns
  `PHYSICALLY_IMPOSSIBLE`.

Sign conventions for Earth rotation, equatorial circulation, coil
rotation, crystal axis, and handedness are fixed as ±1 so any simulation
or bench can reverse them unambiguously.

---

## What R10.3 does not claim

- No apparatus built, no field measured, no crystal driven.
- No site is a node, gateway, or stargate; those statuses are
  `UNSUPPORTED`, and no `LOCATION_UNKNOWN` site was assigned a coordinate.
- No instantaneous transfer, gravity modification, Phryll detection, or
  dimensional gateway.
- The density ladder is a `SOURCE_CLAIM`, not a physical or biological
  fact. Toroidal cosmology is a picture the geometry does not entail.
- No real person is named, characterised, or classified; no private
  transcript, intuition, path, or named-site row appears in the public
  repository.

## Not executed

P01, P06 (channel modelling beyond the causality firewall), P09–P12
(operator-specific site tests — run privately with the public engine),
P14, P16, P18–P23. The apparatus phases (P16, P21) remain deferred
hardware. The operator-specific node hypotheses are tested in the private
repository with `r10/nodes.py` and their rows stay private.
