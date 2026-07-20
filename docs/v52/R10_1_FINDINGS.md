# RGCS R10.1 — Coordinate Space Closure: Findings

**Status:** `SOFTWARE_VERIFIED_PHYSICAL_UNTESTED`
**Baseline:** v5.3.0 (`4b75543`)
**Evidence class:** `DERIVED_MATHEMATICS`
**No physical measurement was performed by this project.**

---

## Gate Zero: the pack's checkpoint was stale

The pack's `CHECKPOINT.md` was written before the previous programme
finished, and two entries no longer hold:

| Checkpoint says | Actual |
|---|---|
| "v5.3.0 was not tagged" | **Tagged** at `4b75543`, released, CI green on that exact commit |
| "clean-clone 2709 passed" | **2710** — a regression test was added afterwards |

Reconciled against repository truth, per the pack's own instruction not
to discard completed work. Rules Q00/Q01 were already satisfied: the tag
waited for exact-commit CI, which is what the outage forced and what the
release contract requires.

---

## Q02 — the inverse packaging defect, closed

`consciousness_lane` shipped in the wheel and sdist, appeared in
`top_level.txt`, and was importable after `pip install` — while sitting
**outside** `SOURCE_ROOTS`, so changing it could not invalidate a frozen
dist. This is the mirror of R8-D-006 ("hashed but not shipped"), and it
is recorded as **R10-D-004**.

The operator's standing decision resolves it: *a publicly shipped
package must be hashed unless it is removed from every public artifact.*
It ships, so it is now hashed.

Both directions are now asserted, and the two lists must be **exactly
equal** — so neither can drift again in either direction.

---

## Q14 — "twenty regions" does not specify a topology

An icosahedron has 20 faces and 12 vertices. Its dual, the dodecahedron,
has 12 faces and 20 vertices. **Both readings give twenty regions:**

| Reading | Regions |
|---|---|
| icosahedron **faces** | 20 |
| dodecahedron **vertices** | 20 |
| icosahedron vertices | 12 |
| dodecahedron faces | 12 |

This is not cosmetic relabelling. Twenty icosahedral faces meet three at
a vertex and share edges with three neighbours; twenty dodecahedral
vertices meet three faces and have three edge-neighbours. **The adjacency
graphs differ**, so neighbour queries, gate semantics, and any address
encoding "next region" differ too.

Both are implemented; neither is assumed. `Address` records which is in
use, and the ambiguity has teeth: region 15 is valid among 20 faces and
**invalid** among 12 vertices.

---

## Q15 — the address arithmetic is exact, and it is a fit

```
4096³ == 8¹² == 2³⁶ == 68,719,476,736
```

Twelve levels of one-to-eight refinement is exactly **36 bits**, exactly
**three 12-bit words**. From a mean Earth radius of 6371.0088 km, twelve
levels reaches **1.5554 km**.

### But twelve was chosen, not discovered

| Levels | Linear scale |
|---|---|
| 11 | 3.11 km |
| **12** | **1.56 km** |
| 13 | 0.78 km |

Twelve levels was selected *because* it reaches kilometre scale, and
kilometre scale was the target. Whichever level count matched the desired
resolution would have been adopted. That is a parameter **fitted to a
known answer**, and `address_provenance()` returns
`status: RETROSPECTIVE_FIT` rather than presenting it as a prediction.

**What would make it evidence:** fixing the topology, level count and
orientation in advance, then testing them against an observable they were
not fitted to — and reporting the result whichever way it came out.

### On the elegance

`8¹² == 2³⁶ == 4096³` is true and tidy. Tidiness is not evidence. *Any*
power-of-two refinement produces identities like this at every level;
they are a property of the radix, not a discovery about Earth.

---

## Q17 — precision is not created by unit conversion

The candidate shell is quoted as **2500 statute miles**. The statute mile
has been exactly 1609.344 m since 1959, so the conversion is exact:

```
2500 statute miles = 100584/25 km = 4023.36 km  (exactly)
```

**And reporting that figure would be dishonest.** The exactness belongs
to the *definition of the mile*, not to the measurement. "2500" is a
round nominal figure carrying about **two** significant figures; 4023.36
implies six.

| | |
|---|---|
| Exact conversion | 4023.36 km |
| **Honestly reportable** | **4000 km** |

`Shell` tracks significant figures through the conversion and refuses to
report more than it was given. A control test confirms the rounding
really tracks the declared precision rather than being a hardcoded
string — a shell declared to five significant figures reports 4023.4 km.

---

## Firewalls

- **An address is a label, not a position.** `Address` requires `frame`
  and `epoch` with no defaults, plus an uncertainty.
- **Graph adjacency is not spacetime geometry.**
  `refuse_metric_promotion()` states that a shortcut through the
  partition is a property of the construction, and that promoting it
  would require a mechanism, a stress-energy budget, and a measurement —
  none of which exists.

---

## What this is, and is not

**Is:** a well-defined synthetic addressing scheme over a sphere, with
exact arithmetic, explicit frames and epochs, honest precision tracking,
and reusable infrastructure.

**Is not:** evidence that Earth has twenty regions, that a polyhedral
partition is physically privileged, that gates or nodes exist, or that
anything about the scheme constrains physics. **A partition is a choice
of bookkeeping.**

---

## Q19 — the estimator works, and its failures are confident

**Module:** [`r10/inverse.py`](../../r10/inverse.py)

Moment-based recovery of a tetrahedron's vertices from points sampled
uniformly inside it, with the algebra derived rather than cited. The
constants 20 and 60 fall out of `Cov(W) = (4I−J)/80` and the collapse of
the third central moment (the cross terms each carry a factor `Σcᵢ = 0`);
both are checked in `Fraction`.

Recovery is clean N^(−1/2): 11.3% at N=100, 1.2% at 10k, 0.22% at 300k.
Below ~300 points the method is unusable, which is reported rather than
omitted.

### The result that matters: the errors are biases, not noise

| Broken assumption | Error | Diagnostics catch it? |
|---|---|---|
| Non-uniform density (α=2) | **25.5%** | **No** |
| Non-uniform density (α=4) | 45.8% | No |
| Rotation 22.5° | **19.6%** | **No** |
| Translation drift ≈ 1 scale | **95.2%** | **No** |
| Density against one face | — | Yes |
| Shell inside the insphere | — | Yes |

At α=2 the error is 25.1% / 25.6% / 25.5% at N = 10⁴ / 10⁵ / 10⁶.
**More data makes the wrong answer more precise.** Three of six broken
assumptions produce confident wrong answers with healthy-looking
diagnostics.

### Two constructive non-identifiability results

**Second moments never identify a tetrahedron.** `M = S^(1/2) R S^(−1/2)`
preserves mean, covariance *and* volume while changing the shape. Three
familiar summary statistics agreeing is not identification — which is
exactly why the third moment is required.

**Shell-confined observations are non-identifiable outright.** Two
tetrahedra with volume ratio 1.42 share an insphere; shell samples from
them agree to 1e-9, while an independent control differs. Tetrahedra have
12 degrees of freedom and spheres have 4, so the equivalence class is an
**8-parameter family**. This is impossibility, not difficulty.

### What it does not license

Classed `LITERATURE_REPRODUCTION`. Per the pack's own firewall, *a
tetrahedral inverse estimator is not proof that the hidden object is
tetrahedral*. The estimator does reject a box, a Gaussian and a square
pyramid — so "it returns a tetrahedron for anything" is false — but those
alternatives were hand-chosen from an unbounded model space, and the
failure modes it does **not** detect are precisely the pack's conditions:
non-uniform density, shell support, and motion.

The 2018 prior art could not be fetched in this environment. Nothing is
attributed to it, and `inverse_report()["prior_art"]["verified"]` is
`False`.

---

## Still open

- Q06, Q07, Q09–Q12, Q16, Q18, Q20–Q23 not executed.
- Q04 (`144.000`) remains **blocked** — no source frame exists, and the
  pack forbids fabricating metadata for it.
- **R10-D-002** still open: `tests/v4` rewrites tracked JSON files, which
  cost the v5.3.0 release one red CI run.
