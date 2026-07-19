# RGCS Release and Disclosure Timeline

Assembled 2026-07-19 from git tags, the GitHub release list, and the
repository's own contemporaneous publication reports.

---

## ⚠ MATERIAL FINDING — the repository was PUBLIC for ~3.5 days

**This bears directly on the `PRIVATE_RC` decision and should be
reviewed with a registered patent agent before any further IP step.**

The repository is private *now*. It was not always. Two of its own
reports state the visibility explicitly:

- `docs/GITHUB_PUBLICATION_REPORT.md` (2026-07-15):
  > Visibility | **PUBLIC** (created private; flipped after release
  > verification)
- `docs/FINAL_PUBLICATION_REPORT.md` (2026-07-16):
  > **Public**: https://github.com/andrew867/rgcs — MIT detected

Corroborating evidence for the end of the public window: branch
protection with `enforce_admins` was verified working through v4.8.1
(2026-07-18 21:01Z). On a free GitHub plan that feature requires a
**public** repository. By the v4.9.0 gate check (2026-07-18 ~23:38Z)
the protection API returned:

```
HTTP 403: Upgrade to GitHub Pro or make this repository public
```

So the flip to private occurred between **2026-07-18 21:01Z and
23:38Z**.

### Releases published while public — 18 of them

| Tag | Published (UTC) |
|---|---|
| v3.0.0 | 2026-07-15 18:47 |
| v3.0.1 | 2026-07-16 04:43 |
| v4.0.0 | 2026-07-16 16:40 |
| v4.1.0-rc1 / v4.1.0 | 2026-07-16 21:15 / 21:17 |
| v4.1.1-rc1 / v4.1.1 | 2026-07-16 21:45 / 21:46 |
| v4.2.1 | 2026-07-17 02:11 |
| v4.3.0 | 2026-07-17 03:25 |
| v4.4.0 | 2026-07-17 21:18 |
| v4.5.0 | 2026-07-17 22:33 |
| v4.5.1 | 2026-07-17 23:38 |
| v4.5.2 | 2026-07-18 00:23 |
| v4.6.0 | 2026-07-18 10:59 |
| v4.7.0 | 2026-07-18 11:53 |
| v4.7.1 | 2026-07-18 15:40 |
| v4.8.0 | 2026-07-18 20:30 |
| v4.8.1 | 2026-07-18 21:01 |

Each carried full source archives under an **MIT licence**, plus
findings documents and the evidence workbook.

### What that means, stated carefully

I am not a lawyer and this is not legal advice. But the factual
position is:

- **The CSCP coordinate work, the PMWR multipath/worldline lane, the
  R3 root-space resolver, and the R4 radix/codec work were all
  publicly released**, with source, under MIT, for roughly 3.5 days.
- That includes the material underlying the proposed **coordinate
  manuscript** and the DDS-relevant content in `CSCP_FINDINGS.md`
  (the phase-closure result, §4 of that document).
- It does **not** include R6 (v4.9.0), R7 (v5.0.0) or R8.1 — those
  were released after the flip to private.

Consequences to raise with counsel:

1. **`FILE_THEN_PUBLISH` may be partly foreclosed** for anything
   disclosed in that window. Strict-novelty jurisdictions generally
   treat public disclosure as destroying novelty immediately. The US
   and Canada have limited inventor grace periods (commonly 12 months)
   which may still be open as of this writing — but conditions differ
   and this needs professional assessment, promptly.
2. **`DEFENSIVE_PUBLICATION` may have partly already occurred** for
   that same material. An MIT-licensed public GitHub release with
   dated tags is reasonable evidence of a dated public disclosure,
   though it is *not* an organised enabling disclosure prepared for a
   searcher — which is what a deliberate defensive publication is for.
3. **The `PRIVATE_RC` decision was made on an incomplete premise.**
   It was recorded (2026-07-18, `docs/v5/R7_PUBLICATION_DECISION.md`)
   on the reasoning that it "preserves both other paths." That
   reasoning is sound for R6/R7/R8.1 material. It is **not** sound for
   anything already disclosed in the public window, where the choice
   may have been made already by the earlier release.

**Recommended action: treat the pre-v4.9.0 corpus as already
disclosed until a patent agent says otherwise, and date the grace
period from 2026-07-15.**

---

## Full release history

| Date (UTC) | Tag | Programme | Visibility at release |
|---|---|---|---|
| 2026-07-15 18:17 | — | repository created | private |
| 2026-07-15 18:47 | v3.0.0 | RSCS 1.0 typed coordinates | **public** |
| 2026-07-16 04:43 | v3.0.1 | archival / Zenodo-DOI trigger | **public** |
| 2026-07-16 16:40 | v4.0.0 | RSCS 2.0 | **public** |
| 2026-07-16 21:17 | v4.1.0 | capability-aware multiphysics | **public** |
| 2026-07-16 21:46 | v4.1.1 | documentation patch | **public** |
| 2026-07-17 02:11 | v4.2.1 | master research expansion | **public** |
| 2026-07-17 03:25 | v4.3.0 | emergent resonator | **public** |
| 2026-07-17 21:18 | v4.4.0 | frequency-key instrument | **public** |
| 2026-07-17 22:33 | v4.5.0 | Windows workbench | **public** |
| 2026-07-17 23:38 | v4.5.1 | launch fix | **public** |
| 2026-07-18 00:23 | v4.5.2 | clean rebuild, valid binaries | **public** |
| 2026-07-18 10:59 | v4.6.0 | **CSCP — coordinates, nulls, DDS closure** | **public** |
| 2026-07-18 11:53 | v4.7.0 | **PMWR — phase memory, worldline recovery** | **public** |
| 2026-07-18 15:40 | v4.7.1 | **R3 — root-space resolver, atlas** | **public** |
| 2026-07-18 20:30 | v4.8.0 | R4 — radix, codec, platforms | **public** |
| 2026-07-18 21:01 | v4.8.1 | workbook column-loss fix | **public** |
| — | — | **visibility flipped to private** | — |
| 2026-07-18 23:38 | v4.9.0 | R6 — witness memory, mailbox, grid | private |
| 2026-07-19 02:55 | v5.0.0 | R7 — CW null, metric refusal, clock link | private |
| pending | v5.1.0 | R8.1 — papers, audit, measurement | private |

## Disclosure status by proposed paper

| Paper | Underlying material | Disclosure status |
|---|---|---|
| **DDS closure** | `CSCP_FINDINGS.md` §4, v4.6.0 | **publicly disclosed 2026-07-18** — the phase-closure result and the binary-clock recovery were in the public release. The R8.1 generalisation (theorem, continuous/sampled discrepancy) is **not** disclosed. |
| **Null calibration** | case studies span v4.6 (metric), v4.9 (blind detector), v5.0 (forced prefix) | **partially disclosed** — the circular-metric case was public in v4.6.0; the blind-detector and forced-prefix cases were not. |
| **Coordinate report** | CSCP, PMWR, R3 | **publicly disclosed** — all three were public releases. |

## Non-disclosures (for completeness)

- No Zenodo DOI was ever minted. `.zenodo.json` and
  `docs/ZENODO_METADATA.md` were staged; `FINAL_PUBLICATION_REPORT.md`
  records "**no DOI invented**" and the step remained a human action.
- No preprint, conference submission, or journal submission has been
  made.
- No manuscript has been sent to any third party.
- The R8.1 work (this branch, `v51-r8`) has never been public.

## Provenance of this document

Tags and dates from `git for-each-ref` and `gh release list`.
Visibility from the repository's own contemporaneous reports plus the
branch-protection API behaviour recorded in
`docs/v4/R6_GATE_ZERO_RECEIPT.md`. **The exact moment of the
visibility flip is inferred, not logged** — GitHub does not expose
historical visibility through the API, and the operator should confirm
it from their own account audit log, which does record it.
