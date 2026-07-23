# Glossary

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** The core vocabulary of evidence classes, nulls, firewalls, and refusal tokens.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** none
**Related code / tests / schemas:** `r10/firewall.py`, `r10/claimfirewall.py`, [../../SCIENTIFIC_BOUNDARIES.md](../../SCIENTIFIC_BOUNDARIES.md)
**Known limitations:** Definitions summarize the enforced meaning; the code and boundaries docs are authoritative.
**Next review trigger:** A new evidence class or refusal token entering the codebase.

## Evidence and provenance

- **Evidence class** — the typed label on every result stating how strongly it is
  supported (e.g. derived arithmetic, analytic model, simulation, source claim,
  bench measurement). The store currently holds **zero** at any physical class.
- **SOURCE_CLAIM** — a claim asserted by the source material; recorded, not endorsed.
- **DERIVED_MATHEMATICS** — a result that follows by arithmetic/algebra from stated inputs.
- **HISTORICAL_FACT** — an independently checkable fact about the world (e.g. a dated patent).
- **SOURCE_REQUIREMENT** — a claim that *would need* a source to resolve, flagged
  as source-required rather than assumed true or false.
- **Tier-A source** — a highest-confidence, independently verifiable source.

## Nulls and statistics

- **Null / matched null** — the default result: no effect found. A **matched null**
  is credible only because the same code detects **planted** structure.
- **Power** — the demonstrated ability of a method to detect a real effect when one
  is present (shown on planted data before a null is trusted).
- **Look-elsewhere** — the correction for having searched many hypotheses; inflates
  a raw p-value (e.g. a coincidence reported at look-elsewhere p=1.0).
- **Refusal** — a first-class typed output: the honest answer when a claim cannot be
  proved, measured, or implemented.

## Firewalls and boundaries

- **Publication firewall** (`r10/firewall.py`) — keeps private source material out
  of the public tree.
- **Claim firewall** (`r10/claimfirewall.py`) — quarantines dangerous claims as
  UNSUPPORTED; no group-targeted biology, medicine, accusation, or financial action.
- **Public/private boundary** — the public repository carries software, math, and
  nulls; the private repository holds the raw source sessions and quarantined claims.

## Refusal tokens

- **PHYSICAL_VALIDATION_NOT_CLAIMED** — no physical measurement or validation is asserted.
- **NO_DECODER_IDENTIFIED** — no decoding scheme was found that beats chance.
- **NO_BETTER_THAN_CHANCE** — a candidate result is statistically indistinguishable from chance.
- **BLOCKED_NO_SPECIMENS** — an experiment is blocked for want of physical specimens.

## Continuity

- **Bus-factor-zero** — the risk that project knowledge is not recoverable if the
  sole maintainer stops; the continuity docs exist to reduce it. See
  [CONTINUITY_HANDOFF.md](CONTINUITY_HANDOFF.md).

PHYSICAL_VALIDATION_NOT_CLAIMED
