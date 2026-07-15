# Public Communication Kit (Agent 12)

Copy-ready text for the repository page, release, and announcements.
Everything here obeys the classification policy: no unconfirmed claim is
presented as fact.

## Project summary (one paragraph)

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
