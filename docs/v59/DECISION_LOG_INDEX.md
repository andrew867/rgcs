# Decision Log Index

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** Where the decision record lives, and the recurring lesson it teaches.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [START_HERE.md](START_HERE.md)
**Related code / tests / schemas:** [../../CHANGELOG.md](../../CHANGELOG.md), `docs/v52/`, `docs/v59/`
**Known limitations:** This is an index, not the decisions themselves; the linked records are authoritative.
**Next review trigger:** A new tranche findings document, or a reversed decision.

## The decision record

There is no single monolithic log. The decisions are distributed across:

- **[../../CHANGELOG.md](../../CHANGELOG.md)** — the release-by-release narrative:
  what each tranche added, what was refused, what stayed deferred.
- **Per-tranche findings (in `docs/v52/`)** — the detailed reasoning per research
  tranche:
  - `docs/v52/R9_FINDINGS.md`
  - `docs/v52/R10_FINDINGS.md`
  - `docs/v52/R10_1_FINDINGS.md`, `R10_2_FINDINGS.md`, `R10_3_FINDINGS.md`
  - `docs/v52/R10_6_FINDINGS.md`, `R10_7_FINDINGS.md`, `R10_8_FINDINGS.md`
  - Supporting receipts: `R10_GATE_ZERO_RECEIPT.md`, `R10_8_GATE_ZERO.md`,
    `R10_PUBLICATION_FIREWALL.md`, `R10_P06_BLOCKED.md`,
    `R10_2_CORPUS_IMPORT_RECEIPT.md`, `R10_INSTALL_PARITY.md`.
- **`docs/v59/`** — the v5.9 overview/reference set (this directory), the R10.10
  continuity and quartz records.

## The recurring lesson

Read across every findings document and one lesson repeats:

> **A green suite proves nothing.** Every null must first prove its **power** on
> **planted data** — if the method cannot detect a structure that *is* there, its
> failure to find one means nothing.

This is why nulls are published with their power demonstrations, why no result
auto-promotes to a stronger evidence class, and why hardware-dependent steps
carry explicit BLOCKED receipts rather than synthetic stand-ins.

## Related

- Evidence-class discipline: [ARCHITECTURE.md](ARCHITECTURE.md), [GLOSSARY.md](GLOSSARY.md)
- What remains unestablished: [../../SCIENTIFIC_BOUNDARIES.md](../../SCIENTIFIC_BOUNDARIES.md)

PHYSICAL_VALIDATION_NOT_CLAIMED
