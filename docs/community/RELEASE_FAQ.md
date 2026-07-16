# Release FAQ — v3.0.0 (community edition)

Release-specific questions. Project-level questions (what is RGCS,
what's "the eye", why five labels, etc.): the root
[`FAQ.md`](../../FAQ.md).

**What exactly did v3.0.0 confirm?**
Nothing physical — deliberately and explicitly. It confirmed *software
and mathematical* properties: 378 tests, three-OS CI, and the
Conservative Extension Property (v3 provably reproduces the frozen v2
results wherever they overlap). Physical hypotheses H-01..H-30 are
pre-registered and await bench execution.

**Where do I download it, and how do I verify what I got?**
The GitHub release (v3.0.0) carries a source zip, a manuscripts bundle,
a sample-experiments bundle, four standalone PDFs, `SHA256SUMS.txt`,
and `PROVENANCE.json`. Verify: `sha256sum -c SHA256SUMS.txt`. The
source zip is byte-identical to the `v3.0.0` git tag archive.

**Is there a DOI?**
Zenodo integration is enabled; the DOI is minted from this release's
Zenodo record and will be added to `CITATION.cff` and the README in a
follow-up commit when issued. Until then, cite via `CITATION.cff`
(GitHub's "Cite this repository" button).

**Which platforms are supported?**
Linux, Windows, macOS × Python 3.11/3.13 (the CI matrix). One known
platform nuance, documented: byte-exact regeneration of the golden
datasets requires the archived v2 build environment; every platform
verifies numerical equivalence to the printed precision instead.

**Can I run the experiments? What do I need?**
Yes — that's the point of the community-validation phase.
`docs/BENCH_HARDWARE.md` lists the bench (mostly standard audio/optics/
test gear; the specimens are the specialty item), and
`docs/LAB_MANUAL.md` + `docs/MEASUREMENT_PROTOCOL.md` are the runbooks.
Hard safety envelope: ≤ 30 V, ≤ 3 A, ≤ 5 mJ/pulse, laser class ≤ 3R,
dummy-load-first, **no human exposure of any kind**.

**What if I run a branch and find nothing?**
Then you've produced exactly what several rows *predict* (H-21/H-23
are pre-registered nulls) — or a first-class negative result for the
others. Both get registered with your name on the contribution. This
project treats a clean null as a success of method.

**What if I find an effect?**
It faces the pre-registered controls and the ARTIFACT category before
anything else. If it survives: it gets registered at its honest class
(a single campaign never upgrades a Hypothesis to Established), and
replication is the next step. Please open an issue keyed to the claim
id with your run manifests.

**Why should software people care about a quartz project?**
The reusable part is the discipline: claim classification as a type
system, frozen baselines + conservative-extension tests, equation-level
provenance with forbidden-transfer clauses, generated-numbers-only
documents. `DESIGN_PHILOSOPHY.md` is the transferable read.

**Is v3 stable? Will the math change under me?**
The mathematics is frozen (registries are append-only; ids are never
renumbered). Software evolves by conservative extension only —
the same guarantee v3 gave v2. Roadmaps:
`docs/CONTRIBUTOR_ROADMAP.md` (what you can pick up) and
`docs/MODELLING_ROADMAP.md` (next software generation).

**Who's behind it, and who paid for it?**
Andrew Green, independent; self-funded; no institutional affiliation,
no sponsor, no product. MIT license — including the parts that would
be embarrassing to get wrong, which is rather the point of publishing
them.
