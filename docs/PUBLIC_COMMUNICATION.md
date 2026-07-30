# Public Communication Kit (Agent 12)

> **Reading note (R10.62).** The paragraph and pitches below were written
> for the v3 crystal programme and remain accurate for that lane. RGCS has
> since grown to five lanes. For current external wording use the
> **whole-programme summary** immediately below, and check anything you
> write against [CLAIM_BOUNDARIES](CLAIM_BOUNDARIES.md) and
> [BLOCKERS_B01_B07](BLOCKERS_B01_B07.md) — those two win over any
> promotional text, including this file.

## Whole-programme summary (current — use this first)

> RGCS is an evidence-governed research programme in resonant geometry.
> It spans crystal and resonator physics on a validated anisotropic
> FEM/piezoelectric stack, a typed coordinate and state-space framework,
> a coordinate/mapping workbench that turns numeric vectors into
> reproducible parse receipts and candidate map positions, and the
> provenance machinery that keeps all of it honest. Its organising
> discipline: lore proposes, mathematics translates, software attacks,
> evidence decides, provenance remains. Most physical claims in the
> programme have been refused or left unmeasured, and those null results
> are published beside the positive ones.

**The coordinate lane, stated exactly:**

> RGCS is a coordinate, mapping, signal, and provenance research
> workbench. It converts received or user-supplied numeric vectors into
> reproducible binary/octal parse receipts, candidate Earth-root
> positions, great-circle paths, and polygonal map regions. RGCS does not
> claim that anomalous sources, craft, crop formations, physical
> propulsion, or non-human communication are proven.

**The line to keep in every public description of the map lane:**

```text
The tool verifies geometry.
It does not verify that a candidate vertex is physically true.
```

## Never say

```text
the coordinate system is proven
physical craft are proven
Phryll is proven
Orion's Arm is a factual authority
crop circles validate the codec
RGCS has located anything
```

A projected point is a **candidate**, not a place. The projector retains
two free parameters at three anchors, and two admissible solutions put the
same vector on different continents — that contradiction is published, not
hidden, and any external description that omits it is inaccurate.

## v3 crystal-programme material (still accurate for that lane)

Copy-ready text for the repository page, release, and announcements.
Everything here obeys the classification policy: no unconfirmed claim is
presented as fact.

## Project summary — v3 crystal programme (one paragraph)

> RGCS is a reproducible research framework for studying acoustic and
> mechanical resonance in engineered quartz geometries. It pairs a typed,
> provenance-checked mathematics library (RSCS 1.0: 17 coordinate types,
> 23 operators, machine-enforced claim classification) with a crystal
> application (anisotropic elastodynamics, coupled modes, an optical
> probe layer), safety-bounded experiment schemas, and four manuscripts
> whose every number is generated from tested code. Its distinguishing
> discipline: a byte-frozen v2 baseline that v3 provably extends without
> change, and a falsification plan in which every hypothesis — several
> pre-registered as expected *nulls* — carries an observable, controls,
> and a failure condition. Nothing physical is claimed as confirmed.

## 30-second elevator pitch

> Research projects that draw on unconventional sources usually either
> launder them into "facts" or throw them away. RGCS does neither: it
> turns a historical crystal-practice corpus into typed mathematics,
> pre-registered experiments, and honest failure conditions — with a type
> system for epistemic status, so overclaiming literally doesn't compile.
> The physics is unconfirmed and says so on every page; the methodology
> is the product. If you build research software, the frozen-baseline +
> conservative-extension + claim-firewall pattern is worth stealing.

## GitHub About text (≤ 350 chars)

> Reproducible resonance-research framework: typed math library with
> machine-checked claim classification, anisotropic quartz modelling,
> safety-bounded experiment schemas, generated manuscripts, and a
> pre-registered falsification plan. No confirmed physical claims — by
> design, and enforced by the test suite.

## Repository description (one line)

> Typed, provenance-checked framework for resonance research in
> engineered quartz — models, experiment schemas, generated manuscripts,
> and a falsification plan; no unconfirmed claim presented as fact.

## Suggested tags

`reproducible-research` · `research-software` · `resonance` ·
`quartz` · `elastodynamics` · `coupled-oscillators` · `acousto-optics` ·
`falsification` · `pre-registration` · `provenance` · `python` ·
`pyside6` · `xelatex` · `metrology` · `open-science`

## Suggested release title

> **RGCS v3.0.0 — RSCS 1.0: typed coordinates, conservative extension,
> and a pre-registered falsification programme**

(rc: "RGCS v3.0.0-rc1 — release candidate" with the same subtitle.)

## Suggested release announcement

> **RGCS v3.0.0 is out.** Version 3 layers RSCS 1.0 — a typed
> coordinate/operator framework with machine-enforced claim
> classification — over the byte-frozen v2 baseline, and proves on every
> test run that nothing old changed (the Conservative Extension
> Property).
>
> Highlights:
> - The v2 scalar wave-speed *hypothesis* is resolved into an anisotropic
>   Christoffel model that recovers the scalar as its special case — the
>   old ±5 % uncertainty band turns out to be the physical X–Z spread.
> - An optical probe layer whose directional claims are pre-registered
>   **nulls**: unbiased passive quartz is reciprocal, and the project
>   says so before measuring.
> - A synchronized coil/laser timing architecture with one master clock,
>   a six-term phase budget, and a binding low-energy safety envelope.
> - Four manuscripts in which no number is hand-typed, a two-OS CI
>   matrix, and an independent adversarial QA whose findings (three real
>   defects) are documented before their fixes.
>
> Nothing physical is confirmed — the release says so honestly, and ships
> the observables, controls, and failure conditions that could change
> that. If the ideas are wrong, this framework is how we'll know.
>
> Checksums, provenance, and the full gate table: `release/`.

## DOI / archival readiness

- `CITATION.cff` is complete (cff 1.2.0, five-class abstract, ORCID slot
  available if desired).
- For a DOI: enable the Zenodo–GitHub integration before publishing the
  GitHub release (Zenodo archives the tag automatically and mints the
  DOI), then add the DOI badge + `identifiers:` block to CITATION.cff in
  a follow-up commit.
- The source zip in `release/` is self-contained and checksummed for
  archives that ingest artifacts directly.
