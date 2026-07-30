# R10.9 Header Table Recovery (Phase 2)

**Status: `NOT_RECOVERED_FROM_HISTORY` — explicit alias set returned;
no labels invented.**

## What was searched (2026-07-27)

| Scope | Method | Result |
|---|---|---|
| Integration repo working tree | `git grep` (spaced/unspaced variants of `3,5,6,7,8,9,10,12,15`) | pack references only |
| Full git history, all refs | `git log -S` pickaxe + `git grep` over `--all` | nothing |
| Sibling `RGCS` checkout | same | nothing |
| Operator archives `internal-docs/` (incl. every `plans-v5` zip, extracted in memory and scanned) | recursive grep + zip content scan | list appears ONLY in the R10.9 prompt pack |
| Frequency list `5,7,24,27,28,48,54,57,64,75,97` | same sweep | R10.9 pack only |
| Affine bridge constants `923`/`550585316`/`168500683` | same sweep | R10.9 pack + `plans-v5/EARTH_ALIGNMENT_CANDIDATE.json` + `EXACT_ARITHMETIC_TESTS.json` (the archived V1 candidate, where the bridge is native) |

Conclusion: no archived binary interpretation of the primary header
list exists anywhere in project history available to this run. The
"recover and reproduce exactly" requirement is therefore **not
satisfiable from history**; per the spec, an explicit alias set is
returned instead (`r109.header_recovery.alias_set`), giving exact
binary renderings at 4/5/6-bit widths with semantics marked UNKNOWN
and evidence class UNRESOLVED.

## Quarantine

The frequency-channel/key list is typed in
`r109.header_recovery.FREQUENCY_KEY_LIST` and
`assert_not_header()` refuses any of its members entering header
parsing (tested).

## Chronology

- 2026-07-26 — federation-group/node-23 provenance recorded in the
  private operator area (gitignored `internal-docs/`), including "the
  federation group lives in the transport header; exact numeric group
  ID unknown".
- 2026-07-27 — R10.9 pack names the primary historical header list
  `3,5,6,7,8,9,10,12,15` and the group codes `16`, `16-5`, `16-7`
  (source-reported). This is the FIRST appearance of the list in any
  material available to this repository.

## What would change this status

An operator-supplied archived artifact (session log, earlier registry,
manuscript draft) containing the original binary interpretation. Until
then, header semantics remain UNRESOLVED aliases and the group codes
remain typed SOURCE_REPORTED values with no invented wire encoding.
