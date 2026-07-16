# V4 Source Hierarchy and Licence Policy (Agent M1)

## Hierarchy (gate B4; machine rank in `provenance_v4.SOURCE_RANK`)

peer-reviewed primary > internal RGCS authority / linked v3 >
peer-reviewed theory > review > preprint > author manuscript >
commentary > public preview / software docs > unresolved topic >
independent theory essay / historical > subtitle-transcript.

`resolve_precedence([...])` returns the ranking winner; Toyoda primary
outranks the News & Views commentary mechanically (tested).

## Access statuses in use (DV4C-003)

- `FULL_TEXT_LOCAL` — file present, real SHA-256 (only SRC-V4-00, the
  pack itself, at programme start).
- `METADATA_ONLY_NOT_LOCALLY_SUPPLIED` — the pack requires the source
  but no file was supplied; sha256 null (never guessed); citation
  status marked WEB_VERIFIED / UNVERIFIED_RECALLED / TOPIC_ONLY.
- `ACCESS_RESTRICTED_PREVIEW_ONLY` — News & Views
  10.1038/s41563-026-02641-3, as mandated (gate H10).
- Upgrade path: `provenance_v4.ingest_file` computes real hashes and
  flips status when files arrive; same-filename/different-content is
  refused (source-diff rule).

## Licence policy (gate B3)

- No source PDF ships in any release asset. `release_filter()` scans
  staged files against every registered restricted filename (v4 AND
  frozen v3 registries) and is run by Q1/R1 before packaging.
- Citations and checksums are always shippable; contents are not.
- The pack zip is internal (gitignored) and never shipped.
- Open-access preprints (e.g. arXiv 2506.07051 for Toyoda) may be
  ingested later; until a licence check is recorded at ingest they are
  treated as local-analysis-only.
