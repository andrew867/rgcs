# Run log — Agent M1 (source ingestion + equation provenance)

- Base commit: `5fa9099`. Mode: DV4C-004 sequential in-place.
- Owned paths: `sources/registry/`, `docs/v4/provenance/`,
  `rscs2_core/provenance_v4.py`, `tests/v4/test_v4c_provenance.py`,
  `docs/v4/runlogs/M1-*`.

## Delivered

- `v4_source_registry.yaml`: 20 records (SRC-V4-00..19). Only the
  pack itself is FULL_TEXT_LOCAL (sha256
  cc54f1a0...a21c5b); Toyoda/Schlauderer/Afanasiev citations
  WEB_VERIFIED (2026-07-16 search); News & Views mandated
  ACCESS_RESTRICTED_PREVIEW_ONLY; topic-only entries carry no invented
  metadata (DV4C-003, no guessed hashes).
- `v4_equation_ledger.yaml`: 15 initial equations with locators,
  adaptation types, units checks, ceilings, forbidden transfers
  (agents append theirs at implementation commits).
- `rscs2_core/provenance_v4.py`: loaders + ceiling enforcement
  (`check_classification`), hierarchy resolver, exclusion matrix
  (`check_transfer`, `quartz_mechanism_allowed`), lawful-release
  filter (v4 + frozen v3 filenames), provenance linter,
  ingest/source-diff tool.
- Docs: adaptation matrix, exclusion matrix, hierarchy/licence
  policy, source-lore index.

## Tests

`pytest tests/v4/test_v4c_provenance.py` → **11 passed** (registry
shape, ledger-ceiling audit, laundering blocks, hierarchy, forbidden
transfers, quartz exclusions, release filter incl. live audit of the
shipped proof bundle, linter, ingest+diff refusal, frozen-v3 check).

## Defect found during implementation

Ledger entry EQ-012 initially cited topic-only SRC-V4-14 while
claiming CORE_VALIDATED; the ceiling test failed mechanically;
re-sourced to the EST standard form. Recorded here as evidence the
enforcement bites (severity P1-at-birth, fixed pre-commit, regression
is the permanent ledger audit test).

## Gates

B1 PASS (all LOCAL sources hashed; absent files carry null, policy
DV4C-003). B2 PASS for the initial ledger. B3 PASS (filter + live
audit). B4 PASS (mechanical precedence). B5 PASS (ceilings tested).
