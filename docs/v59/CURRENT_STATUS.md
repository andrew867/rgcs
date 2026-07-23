# Current Status — RGCS v5.9.0 (candidate)

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** The state of the project at the v5.9.0 candidate, built on the v5.8.0 baseline.
**Last verified commit:** v5.8.0 baseline (branch v580-r10-10)
**Prerequisites:** [START_HERE.md](START_HERE.md)
**Related code / tests / schemas:** `r10/`, `tests/`, [../../CHANGELOG.md](../../CHANGELOG.md)
**Known limitations:** Test counts are the software gate only; nothing physical is measured or validated.
**Next review trigger:** Cutting v5.9.0, or acquiring any physical specimen or measured dataset.

## Where we are

v5.9.0 is the **R10.10 candidate**, developed from the **v5.8.0 baseline**.
At v5.8.0 the local suite held **~3340 passing tests** (one archived-environment
byte test deselected by policy D-V3-04); the R10.10 tranche adds more on top of
that baseline.

## Recent tranches

| Tranche | Release | Theme |
|---|---|---|
| R10.7 | v5.7.0 | Rooted interbody routing, phase-conjugate return, sky reconstruction |
| R10.8 | v5.8.0 | Handshake protocol, EMI survey, 13 MHz microcrystal, atomic-time, 1604/1644 cues |
| R10.10 | v5.9.0 (candidate) | Natural quartz, patent history, continuity handoff |

Each tranche adds r10 modules that **default to a refusal or a null**, plus the
firewalls that quarantine any dangerous source claim as UNSUPPORTED.

## What is measured

**Nothing.** The canonical evidence store holds records at derived, analytic,
source-claim, unsupported, simulation, geometry, synthetic and lore classes —
and **zero** at any physical class (`BENCH_MEASUREMENT`, `INDEPENDENT_REPLICATION`).
The software *cannot* emit a physical evidence class; that is enforced in code.
Hardware and future-data phases remain **deferred**. See
[../../SCIENTIFIC_BOUNDARIES.md](../../SCIENTIFIC_BOUNDARIES.md).

## Verification of record

**Hosted CI is unavailable** — the free-tier GitHub Actions minutes are
exhausted. The **full local suite, run on the exact release commit, is the
gate**. Restoring hosted CI is on the roadmap ([ROADMAP.md](ROADMAP.md)).

## Licensing

MIT throughout, unchanged. No relicensing in this tranche.

PHYSICAL_VALIDATION_NOT_CLAIMED
