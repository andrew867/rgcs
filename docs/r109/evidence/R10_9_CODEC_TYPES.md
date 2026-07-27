# R10.9 Codec Types (Phase 3)

Typed boundaries per the spec; names follow repository conventions.

| Type | Module | Purpose |
|---|---|---|
| `SolGroup` | `r109.types` | source-reported group/member codes (16, 16-5 Terra, 16-7 Luna); constructor refuses any evidence class other than SOURCE_REPORTED; no wire encoding invented |
| `DecimalTerminalMarker` | `r109.types` | last decimal digit + source-reported meaning; firewalled from binary S3 |
| `WireAddress` | `r109.types` | raw value with exact decimal/binary/octal renderings, octal depth, provenance id; no truncation anywhere |
| `CompactAddress` | `r109.types` | T10 fields F5 / 11-symbol Q22 path / S3; validates ranges |
| `RefinedAddress` | `r109.types` | T11 candidate decode: source face, parent path, ONE 8-way child (end of path, before shell/epoch), shell, epoch, parent link, alias id |
| `ShellSemantics`, `CrustalBandProfile`, `OrbitClass` | `r109.types` / `r109.shell_semantics` | shell 3 crustal band with variable depth; shell 7 orbit class |
| `AuthorityEntry` | `r109.authority` | machine-readable locks with evidence classes and supersedes links |
| `VectorRecord` | `r109.registry` | registry V2 rows with fit permissions and firewalls |
| `T11Candidate` | `r109.t11_candidates` | one declared candidate transform: permutation, extraction, child position, inverse, parent reduction, assumptions |
| `HeaderAlias` | `r109.header_recovery` | UNRESOLVED primary-list alias with exact binary renderings |

## Dispatch and refusals (`r109.codec`)

- `classify()`: depth 10 + 30-bit range → T10; depth 11 → T11; anything
  else refused (never truncated).
- `decode_compact()`/`encode_compact()`: thin typed wrappers over the
  FROZEN public parser `rgcs_coordinate.codecs.federation_terra_30` —
  no reimplementation.
- Permanent refusals (all test-enforced): decimal-triplet XYZ; 30-bit
  truncation of long values; the superseded general affine bridge;
  modulo-20 promotion of reserved faces; literal physical F5=23;
  post-reveal retuning (registry fit permissions + holdout lock).

## Receipts

Every registry row renders its wire facts; T10 traces are frozen in
`R10_9_T10_TRACE_FIXTURES.json`; T11 evaluation receipts in
`R10_9_PARENT_CHILD_CONTAINMENT.json` / `R10_9_T11_CANDIDATES.csv`.
