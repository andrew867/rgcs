# T02 — Arisaka source-stack audit

Coverage: **C007–C011**. Lane: **quarantined**.
Sources: Arisaka decks, local, `SRC` tier, **not redistributed**.

## Audit posture

These are **presentation claims from a source deck**. They are not
settled neuroscience and this audit does not treat them as such. Each
is recorded with what it says, what established work it overlaps, what
is genuinely novel as a hypothesis, and what would falsify it.

Source claims are retained at `SRC`/`HYP` **without endorsement and
without mockery**. The corpus is `LOCAL_ANALYSIS_ONLY`; no source text
is reproduced here.

## Claim-by-claim

### C007 — "space is time" (`SOURCE_HYPOTHESIS`, SRC)

A source statement. No operational definition with units is supplied,
so there is nothing to compute. Established overlap: time-of-flight
reconstruction genuinely does convert signal timing into spatial
structure — which is a signal-processing fact, not an identity of space
and time. Retained with page-level provenance; not endorsed.

### C008 — MePMoS (`ENGINEERING_PROTOTYPE`, ENG)

Treated as a proposed architecture. **Falsified if** it fails its own
stated engineering benchmark. No consciousness claim attaches.

### C009 — Neural Holographic Tomography (`ENGINEERING_PROTOTYPE`)

Established overlap: tomographic reconstruction is standard. **Falsified
if** reconstruction fails on synthetic phantoms — the ordinary test any
tomography method must pass.

### C010 — Holographic Ring Attractor Lattice (`REDUCED_ORDER_VALIDATED`)

**This one has a real model**, implemented by the v4.2.1 audit:
`ring_attractor()`. A continuous ring attractor with local excitation,
global inhibition, and a saturating transfer function forms a localized
bump that **persists after the input is removed** and tracks the input
direction.

That persistence is the property the deck calls "holographic memory".
Established overlap: ring attractors are standard computational
neuroscience (head-direction cells, and the *Drosophila* ellipsoid body
where the bump has been directly imaged).

Two honest notes:

1. The saturation is load-bearing. With a bare ReLU the network only
   decays or diverges (rates ~1e7 by k_exc=8), so a "persistent bump"
   would be a knife-edge artifact of the gain rather than an attractor.
2. **Implementing a ring attractor and naming it after the deck does
   not make the deck correct.** It demonstrates that *this component*
   of the proposal corresponds to a known, working mechanism. The word
   "holographic" adds nothing the attractor dynamics do not already do.

**Falsified if** the bump fails to form or fails to persist under the
declared noise level.

### C011 — Q-HAL, BFFT, CAIRO, TERESA (`ENGINEERING_PROTOTYPE`)

Proposed software components. Each is falsified by failing its own
declared software benchmark. They are engineering artifacts; none is a
brain model, and none is evidence of consciousness (G39).

## Comparison with established work

Predictive processing, ring attractors, grid cells, neural fields,
tomography, phase coding, replay, and memory consolidation all cover
territory the deck also covers. Where the deck overlaps them, the
established work is the citation. Where it exceeds them, it is a
hypothesis.

## Boundaries

- **Do not identify public presentation claims as settled
  neuroscience.**
- **Do not present any of this as conscious-AI proof.**
- No "overwhelming evidence" wording appears in this audit, because no
  overwhelming evidence exists.
