# Zenodo Metadata (Agent 15)

Human-readable record of the archival metadata. The machine copy the
GitHub–Zenodo integration reads is **`.zenodo.json` at the repo root**
(keep the two in sync; the JSON wins). Sequence and post-DOI steps:
`docs/DOI_RELEASE_GUIDE.md`. **No DOI appears anywhere until Zenodo
issues one.**

| Field | Value |
|---|---|
| Title | RGCS v3.0.0 / RSCS 1.0 — Resonant Geometry Computational System: typed coordinates, conservative extension, and a pre-registered falsification programme |
| Upload type | Software |
| Authors | Green, Andrew (independent researcher; me@andrewgreen.ca) |
| Affiliations | none (independent) |
| Version | 3.0.0 |
| License | MIT |
| Language | English |
| Funding | none — self-funded independent research |
| Communities | suggested after record creation: *open-science*, *reproducible-research* (join requests are per-community and post-hoc) |
| Keywords | reproducible research; research software; resonance; quartz; elastodynamics; coupled oscillators; acousto-optics; falsification; pre-registration; provenance; claim classification; metrology; open science |
| Related identifiers | `isSupplementTo` → https://github.com/andrew867/rgcs · `isIdenticalTo` → the v3.0.0 release URL |

## Abstract (as archived)

RGCS is a reproducible research framework for studying acoustic and
mechanical resonance in engineered quartz geometries. It pairs a typed,
provenance-checked mathematics library (RSCS 1.0: 17 coordinate types,
23 operators, machine-enforced claim classification) with a crystal
application (anisotropic Christoffel elastodynamics, coupled modes, an
optical probe layer), safety-bounded experiment schemas, a complete
laboratory validation plan, and four manuscripts whose every number is
generated from tested code. Its distinguishing discipline: a
byte-frozen v2 baseline that v3 provably extends without change (the
Conservative Extension Property, machine-tested on every run), and a
falsification plan in which every hypothesis — several pre-registered
as expected *nulls* — carries an observable, controls, and a failure
condition. **No physical hypothesis of the programme has been
experimentally confirmed**, and the software states this on every
claim-bearing surface. The strongest current result is methodological:
a demonstration that unconventional source material can be preserved
faithfully and tested honestly without becoming evidence by repetition.

## Software description (Zenodo "additional notes")

Source release only: cross-platform-tested source
(ubuntu/windows/macos × Python 3.11/3.13 CI, all green at the release
lineage), 13 JSON experiment schemas with validated examples, four
XeLaTeX manuscripts with per-manuscript checksums and build docs, and a
provenance manifest. Checksums: `SHA256SUMS.txt` in the release. The
frozen v2.0.0 baseline ships inside the repository (`archive/v2.0.0/`).

## References (archived record references section)

The six adapted-mathematics sources and two handbook sources cited in
`references/references.bib` and `manuscripts/common/handbooks.bib`
(Sohn/Orsel/Bahl; Cheng et al.; Lapointe/Coia/Vallée; Wang et al.;
Zhang/Zhan/Gong/Niu; Chao/Yam/Vivien/Dagens; Bechmann 1958; Auld 1973)
— each used for *mathematics only*, with binding forbidden-transfer
clauses recorded in `references/equation_provenance.yaml`.

## Post-DOI follow-up commit (checklist)

1. `CITATION.cff`: add `identifiers:` block with the version DOI.
2. README: DOI badge under the title.
3. `docs/GITHUB_PUBLICATION_REPORT.md`: DOI status row updated.
