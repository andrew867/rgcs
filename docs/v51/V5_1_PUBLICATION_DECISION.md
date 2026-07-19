# v5.1.0 Publication Decision Record

**Decision: `PUBLIC_OPEN_COMMONS`**

| Field | Value |
|---|---|
| Path | `PUBLIC_OPEN_COMMONS` |
| Authorized by | Andrew Green (repository owner), in writing |
| Authorization token | `OPEN_COMMONS_PUBLICATION_AUTHORIZED` |
| Date | 2026-07-19 |
| Supersedes | `PRIVATE_RC` (recorded 2026-07-18, `docs/v5/R7_PUBLICATION_DECISION.md`) |
| Licence | MIT, unchanged — no relicensing |

## Authorized

- final public technical report;
- publication of the complete open reference implementation;
- public release of reproducible software, schemas, tests, negative
  results, prior-art corrections and provenance archives that are
  safe to publish;
- transition of the repository to public visibility after every
  release gate is green;
- a GitHub v5.1.0 release;
- the Humanity Commons Charter and the anti-enclosure intent document,
  the latter marked as policy draft pending legal review;
- publication under the repository's existing applicable licences.

## Explicitly not authorized

False physical claims · removal of evidence labels · rewriting failed
results · medical claims · human or animal testing · release of
secrets or personal data · destructive history edits · broad patent
claims to basic mathematics · silent relicensing of previously
released code.

## Why this supersedes PRIVATE_RC rather than contradicting it

`PRIVATE_RC` was recorded on the reasoning that it preserved both
other paths. That reasoning was sound for R6, R7 and R8.1 material,
which had never been public.

It was **not** sound for anything already disclosed: v3.0.0 through
v4.8.1 were published under MIT between 2026-07-15 and 2026-07-18,
covering CSCP, PMWR, R3 and R4. For that material the choice had
substantially been made by the earlier release.

The owner was shown that finding and has decided, knowingly, that the
foundation should be common infrastructure rather than a patent
position. That is a legitimate decision for the owner to make, and it
is recorded here as knowing rather than inadvertent.

## Standing legal caveat

This decision does not constitute legal advice and does not close the
IP question. `PATENT_NON_ASSERTION_INTENT.md` remains **intent, not a
covenant**, and its checklist for counsel stands — in particular
confirming the true visibility-flip timestamp from the account audit
log, and determining which subject matter was first disclosed
privately in R6/R7/R8.1 versus in the earlier public window.

Publishing does not remove the need for that triage; it changes what
the triage is about.

## Safety verification performed before authorization took effect

- secret scan: no API keys, tokens or credentials in tracked files;
- personal data: the only email is the author's own published contact
  address, already public since v3.0.0;
- `internal-docs/` is gitignored and untracked — no prompt packs are
  published;
- `source_claims/` is untracked — no third-party corpus is published
  in this release;
- no private filesystem paths in tracked files.

## Excluded at the owner's instruction

Personal provenance material unrelated to the scientific record was
excluded from every artifact in this release at the owner's explicit
direction. No file, reference or index entry was created for it.

## Gate

Public visibility flips only after every release gate is green and
the release is verified by download. If the flip cannot be performed
by tooling, the release completes privately and the visibility change
is left as the sole human action, with exact steps supplied.
