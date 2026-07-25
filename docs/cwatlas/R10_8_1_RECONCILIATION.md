# R10.8.1 Reconciliation — R10.8, R10.10, R14, R15 into the CW Atlas

**Phase:** T01 / P03 (Reconciliation and Data Authority)
**Repository head at reconciliation:** `2f49122` (v8.0.0, R15)
**Status:** COMPLETE — documentation phase, no code.

## Purpose

R10.8.1 (the CW Atlas and bidirectional geocoder, package `cwatlas`) does not
start from a blank page. Four prior requirement lines — **R10.8**, **R10.10**,
**R14**, and **R15** — carry coordinate, radio-frequency, materials, evidence,
and governance requirements that must be *reconciled* into R10.8.1, not
reopened and not silently dropped.

The rule for this phase (System Contract, and the phase prompt): merge prior
requirements **without reopening completed work** and **without silently
discarding contradictions**. Every prior requirement is given an explicit
disposition below:

- **CARRIED** — the requirement holds unchanged in R10.8.1 and is honoured by
  the current package or contract.
- **SUPERSEDED** — a later, stronger requirement replaces it; the older form is
  retained as named history, not overwritten.
- **CONTRADICTION-FLAGGED** — the requirement, if applied literally, would
  conflict with an R10.8.1 invariant. It is flagged here rather than resolved
  by fiat, and the conflicting claim is *not* adopted.

No disposition promotes any interpretation across the claim boundary. All
extraordinary interpretations remain `SOURCE_CLAIM`, `OPERATOR_HYPOTHESIS`, or
`MATHEMATICAL_TRANSLATION` (claims taxonomy, `cwatlas/claims.py`).

## Prior release context

| Line | Committed release | Substance (as recorded in git history / changelog) |
|------|-------------------|-----------------------------------------------------|
| R10.8 | `af93550`, `fc08e16` | Handshake, EMI, 13 MHz, the 1604/1644 cues; discipline to keep the private repo name out of public docs. |
| R10.10 | `af93e52` | Natural quartz, verified patent timeline, continuity of the materials lane. |
| R14 | (no standalone tag; interim research-delta line between R13 `v7.0.0` and R15 `v8.0.0`) | Coordinate/authority and evidence-ladder requirements folded forward into the R15 experimental infrastructure. |
| R15 | `2f49122`, `v8.0.0` | 36-phase experimental infrastructure; evidence ladder; REAL/REPLAY/SYNTHETIC/FAULT_INJECTION interfaces; `PHYSICAL_VALIDATION_NOT_CLAIMED`. |

## Reconciliation table

### R10.8 — handshake / EMI / RF cues / private-name discipline

| # | Prior R10.8 requirement | R10.8.1 disposition | Note |
|---|--------------------------|---------------------|------|
| 8.1 | The private repository name and private investigation particulars stay out of public docs. | **CARRIED** | Enforced by `cwatlas/privacy.py` (P02) and Contract invariant 6; public fixtures are synthetic. |
| 8.2 | 13 MHz / 1604 / 1644 handshake and EMI cues recorded as source material. | **CARRIED** | Retained as `SOURCE_CLAIM` research-archive context (Master Research Delta, RF lane). Not a coordinate authority; see P07 claim map. |
| 8.3 | Handshake/EMI framing treated as evidence of a mechanism. | **CONTRADICTION-FLAGGED** | R10.8.1 forbids promoting an RF cue to a physical mechanism (`PHYSICAL_VALIDATION_NOT_CLAIMED`). Kept as hypothesis, not adopted as fact. |

### R10.10 — natural quartz / patent timeline / continuity

| # | Prior R10.10 requirement | R10.8.1 disposition | Note |
|---|--------------------------|---------------------|------|
| 10.10.1 | Natural quartz materials lane preserved. | **CARRIED** | Materials lane referenced in the P07 dependency map as a supporting-source lane, claim-classed, not a coordinate input. |
| 10.10.2 | Patent timeline verified and retained. | **CARRIED** | Prior-art-literature class in P07; a patent is a document, never craft validation (`claims.refuse_patent_as_craft_validation`). |
| 10.10.3 | Patent timeline read as validating a craft programme. | **CONTRADICTION-FLAGGED** | Directly forbidden by the claim boundary. Flagged; not adopted. |

### R14 — interim coordinate/authority + evidence-ladder delta

| # | Prior R14 requirement | R10.8.1 disposition | Note |
|---|-----------------------|---------------------|------|
| 14.1 | Coordinate vectors kept as separate source families (12-digit, nine-digit, variable-length). | **CARRIED** | Master Research Delta coordinate lane; codec families `CW-TRIPLET9-1`, `CW-BASE100-1`, etc. (Architecture Spec). |
| 14.2 | Every address carries body, frame, epoch, shell, residual, uncertainty, provenance. | **CARRIED** | Canonical-address requirement (Architecture Spec); frame/epoch authorities pinned by the P06 registry. |
| 14.3 | Evidence ladder caps unbound observations below physical measurement. | **SUPERSEDED** | Subsumed by R15's fuller evidence ladder; R14's form retained as the earlier named realization, not overwritten. |
| 14.4 | Any single interim "best" interpretation is pinned as the answer. | **CONTRADICTION-FLAGGED** | Conflicts with invariant 4 (legacy decoder may return zero/one/many aliases, never a forced pin). Flagged; not adopted. |

### R15 — experimental infrastructure / evidence ladder / no physical claim

| # | Prior R15 requirement | R10.8.1 disposition | Note |
|---|-----------------------|---------------------|------|
| 15.1 | `PHYSICAL_VALIDATION_NOT_CLAIMED` on every lane. | **CARRIED** | Terminal verdict of R10.8.1; every `*_report()` in `cwatlas` re-asserts it. |
| 15.2 | Typed governance core (claim ladder + forbidden promotions). | **CARRIED** | Reimplemented for the atlas in `cwatlas/claims.py`; the seven forbidden promotions are preserved. |
| 15.3 | REAL/REPLAY/SYNTHETIC/FAULT_INJECTION interface discipline; no physical acquisition. | **CARRIED** | R10.8.1 uses synthetic fixtures only; no-purchase / no-acquisition rule holds. |
| 15.4 | Strongest unreplicated residual stays `UNEXPLAINED_INSTRUMENT_RESIDUAL`; no detection state. | **CARRIED** | No `..._DETECTED` state exists in the atlas; source-vector geographic semantics stay `NOT_CLAIMED`. |
| 15.5 | Additive only — no prior work reset, no public history rewritten. | **CARRIED** | R10.8.1 adds the `cwatlas` package alongside prior releases; nothing prior is deleted. |

## Contradictions carried forward (not resolved by fiat)

The three CONTRADICTION-FLAGGED items (8.3, 10.10.3, 14.4) are **recorded, not
adopted**. Each would, if applied literally, breach an R10.8.1 invariant:

- 8.3 and 10.10.3 would promote a source cue / patent to a physical or craft
  claim — forbidden by the claim boundary and `PHYSICAL_VALIDATION_NOT_CLAIMED`.
- 14.4 would force a single pin from a legacy vector — forbidden by invariant 4.

They remain visible so a later phase (or a prospective calibration challenge)
can revisit them with evidence, rather than having them quietly disappear.

## Unresolved questions

- Whether R14's evidence-ladder wording differs materially from R15's in any
  edge case not covered by 14.3 (tracked; no coordinate impact).
- Whether any R10.8 RF cue ever earns a coordinate-authority role. Answer today:
  no; it stays an RF-lane source. See P07.

## Verdict

```text
R10_8_1_RECONCILIATION_COMPLETE_NO_COMPLETED_WORK_REOPENED
CONTRADICTIONS_FLAGGED_NOT_SILENTLY_DISCARDED
SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
PHYSICAL_VALIDATION_NOT_CLAIMED
```
