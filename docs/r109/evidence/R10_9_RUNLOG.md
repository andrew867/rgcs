# R10.9 Runlog (2026-07-27)

Executed sequence (private branch `program/r10-9-variable-depth` off
`program/integration @ 3af2496`; venv `%LOCALAPPDATA%/rgcs-int-venv`,
Python 3.13.2).

1. **Gate Zero** — repo truth confirmed: clean tree, tags ≤ v8.2.0,
   origin present, nothing pushed. Module inventory: frozen public
   parser `rgcs_coordinate.codecs.federation_terra_30`; R10.8.5A stack
   `cwatlas/r1082` (calibration freeze, Wilkes, SAA), `r1084`
   (recursive decode), `r1085a` (outer-in projection, shell profiles).
2. **Corpus arithmetic** — all pack expectations (octal renderings,
   F5/path/S3 for the five compact vectors) reproduce EXACTLY on the
   frozen parser, including direct Montréal `165879243`. Zero parser
   changes.
3. **History search** — subagent sweep of tree + all-refs git history,
   plus operator-archive scan (`internal-docs`, every plans-v5 zip,
   in-memory zip content grep): header list and its interpretation
   absent everywhere except the R10.9 pack; affine bridge and V1 found
   in the archived `RGCS_Earth_Alignment_Candidate_2026-07-26` zip;
   `167854923` blind receipt found NOWHERE (produced this run from the
   preserved V1 operator).
4. **V1 preservation** — archive extracted byte-for-byte to
   `docs/r109/earth_v1/`; V1 chain recovered: spherical midpoint
   subdivision, child map (2,1,0,3), corner order (1,0,2); EXACT on
   face 12 (Stonehenge + orange triplet to ~1e-14 vs archived values);
   face 19 approximate only (0.1–2.5°) — recorded as
   APPROXIMATE_CONVENTION_UNRESOLVED; V1 level-6 mesh: 0 reversals
   (archived claim reproduced).
5. **Implementation** — `r109/` package: authority registry (19
   entries, 8 evidence classes), typed address family, T10 dispatch +
   refusals, T11 bounded candidate registry (46), face/node
   arithmetic, shell semantics + marker firewall, vector registry V2,
   superseded-model ledger, header recovery, Earth V2 fitter.
6. **T11 enumeration** — 46 candidates × 2 training pairs: ZERO
   survivors; interleave stays UNRESOLVED; receipts written.
7. **Earth V2** — fit converged (868 steps, max residual 8.5e-7°);
   verification: 102 reversals (L5) / 361 (L6), area ratios to 47×,
   inverse non-invertible in folded patches (max 180°); V1↔V2 global
   displacement mean 0.257°; orange plane degraded ~1.25°; holdout
   under V1 (41.730, −80.834) and V2 (41.711, −81.338), never fitted.
8. **Focused tests** — `tests/r109`: 34 passed.
9. **Full repository suite** — same CI-mirroring deselection as the
   consolidation phase; result in `R10_9_TEST_RECEIPT.json`.
10. **Private registry/manuscript inputs** — updated in gitignored
    `internal-docs/provenance/` (2026-07-27 note); publication HOLD.
10b. **Sealed holdout intake (2026-07-27, mid-run)** — five raw wire
    values sealed with hashes BEFORE decoding
    (`R10_9_SEALED_HOLDOUT_INTAKE.json`, intake sha256 350c4ffb…);
    referenced external receipt file NOT FOUND on disk (recorded);
    pre-reveal prediction receipts under the frozen V1 and V2
    operators for the four decodable T10 vectors
    (`R10_9_PREREVEAL_PREDICTIONS.json`, digest fe6fcb83…); the
    T11-depth value `1687209343` gets NO prediction (interleave
    unresolved); pair relation with `168724343` NOT assumed;
    structural observation preserved: all five decimal terminals are
    3 while decoded S3 = {3,7,7,1} — marker firewall strengthened.
    Firewall tests forbid these values in T11 selection, V2 anchors,
    and registry fit sets.
11. Single evidence-rich commit on the private branch; no tag, no
    push, no release, no publication.
