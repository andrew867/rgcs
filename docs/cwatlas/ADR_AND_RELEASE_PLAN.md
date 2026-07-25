# Architecture Decision Record and Release Plan — R10.8.1 CW Atlas

**Phase:** T01 / P08 (Reconciliation and Data Authority)
**Repository head:** `2f49122` (v8.0.0, R15)
**Release target:** **v8.1.0**
**Status:** COMPLETE — documentation phase, no code.

This record freezes the design decisions, package layout, migration path,
terminal verdict, and rollback strategy for the R10.8.1 CW Atlas. Decisions are
recorded so the newest model does not silently rewrite history; superseded
options are kept as named alternatives, not deleted.

---

## ADR-1 — Package name is `cwatlas`

**Status:** ACCEPTED (frozen).

**Decision.** The CW Atlas and bidirectional geocoder ship as a new top-level
package `cwatlas`, additive alongside the existing `r13`/`r15` packages. Prior
releases are not reset and public history is not rewritten (carried from R15).

**Alternatives considered.**
- Extend an existing package (`r15`). *Rejected:* the atlas is a distinct
  product surface (map pin <-> vector) with its own claim boundary; folding it
  in would blur the firewall.
- A parallel toy package outside the repo. *Rejected:* violates the global
  execution contract (no parallel toy package).

**Consequences.** One import root, `cwatlas`; one schema directory,
`cwatlas/schemas/`; one receipts directory, `docs/cwatlas/receipts/`.

## ADR-2 — Pure-NumPy geodesy, no heavy geo stack at the core

**Status:** ACCEPTED (frozen).

**Decision.** The canonical geodesy (ellipsoid <-> ECEF, orientation,
plate-motion propagation) is implemented in pure NumPy + `hashlib`, deterministic
and dependency-light (`cwatlas/geodesy.py`, `frames.py`, `earth_frame.py`,
`mars_frame.py`). `pyproj`/`GeographicLib`/`FastAPI`/`MapLibre` from the
Architecture Spec map stack are **optional integration layers**, not core
dependencies.

**Rationale.** Clean-checkout reproducibility of receipts; no native-build
hazard; determinism testable now. The Architecture Spec says *prefer the
repository's existing stack* — the existing stack is pure-Python numeric.

**Consequences.** Every codec round-trip is reproducible in CI without a geo
toolchain. A UI/tile layer can be added later without touching the core.

## ADR-3 — Canonical vs. legacy separation is a hard firewall

**Status:** ACCEPTED (frozen).

**Decision.** The reversible **canonical** geocoder and the **legacy /
source-vector** hypothesis decoder are separate systems and never merge.

- Canonical: a *declared* coordinate -> versioned vector -> exact point
  (`CANONICAL_ROUND_TRIP`), within a declared quantization (invariant 3).
- Legacy: a source string -> zero, one, or many aliases with score and
  uncertainty (`LEGACY_ALIAS_CANDIDATE`), never a forced pin (invariant 4);
  or a region / heatmap / `REFUSAL` when calibration is missing.

**Consequences.** The reversible codec never proves what a source vector meant
(`claims.refuse_synthetic_codec_as_source_meaning`). Geographic labels and
known destinations stay sealed during transform selection (invariant 5).

## ADR-4 — Frame/epoch/root authorities are pinned by a registry

**Status:** ACCEPTED (frozen).

**Decision.** Every decode records exactly which body/frame/epoch/orientation/
ephemeris it used, by looking them up in a typed, versioned, hashed authority
registry (`cwatlas/authority.py`, P06), independent of the frame math. An
unregistered authority is refused; legacy versions are preserved side by side.

**Rationale.** Invariant 2 (every decode records frame, epoch, orientation,
software commit) and invariant 9 (no pin without a CRS + epoch receipt).

## ADR-5 — Synthetic-only public fixtures; private corpora stay out

**Status:** ACCEPTED (frozen).

**Decision.** Public tests and fixtures are synthetic (`cwatlas/privacy.py`,
P02). Private corpora load only through the ignored `CWATLAS_PRIVATE_DIR` path
and never enter version control, builds, logs, or exports (invariant 6, claim
boundary).

---

## Package layout (frozen)

```text
cwatlas/
  __init__.py            # package intro + the standing invariants
  claims.py              # claim taxonomy + forbidden promotions (governance core)
  privacy.py             # private/public corpus boundary (P02)
  authority.py           # frame/epoch/root authority registry (P06)
  geodesy.py             # pure-NumPy ellipsoid/ECEF geodesy
  frames.py              # ITRS/ITRF realizations, epoch, plate motion (P10)
  earth_frame.py         # Earth body-fixed root + orientation profiles (P11)
  mars_frame.py          # Mars IAU body-fixed convention
  shells.py              # shell-state ontology (8<->0 as source ontology, invariant 8)
  schemas/               # JSON schemas (frame_epoch, cw_vector, codec_result, ...)
docs/cwatlas/
  R10_8_1_RECONCILIATION.md            # P03
  DEPENDENCY_PRIOR_ART_AND_CLAIM_MAP.md# P07
  ADR_AND_RELEASE_PLAN.md              # P08 (this file)
  fixtures/                            # synthetic fixtures
  receipts/                            # per-phase terminal receipts
tests/cwatlas/                         # deterministic unit/property/negative tests
```

## Migration path

- **Additive.** `cwatlas` is new; no existing module is modified or removed.
  R10.8, R10.10, R14, R15 requirements are reconciled per the P03 table
  (CARRIED / SUPERSEDED / CONTRADICTION-FLAGGED), never reopened.
- **Versioned interpretations.** Legacy codecs (`CW-SHELL9-LEGACY`) and legacy
  frame realizations (ITRF2008/2014/2020) are retained as named versions, not
  overwritten. The authority registry keys on `(type, id, version)`.
- **Schema evolution.** Schema changes are additive and versioned; the
  `frame_epoch.schema.json` required set is a compatibility contract for
  FRAME/EPOCH certificates.
- **No data migration.** No production coordinate data exists to migrate; the
  atlas operates on declared inputs and synthetic fixtures.

## Release plan — v8.1.0

**Target:** `v8.1.0` (minor bump over v8.0.0 / R15; additive, no breaking
change).

Release gate (all must hold):

1. Focused tests green: `tests/cwatlas/test_authority.py` and the full
   `tests/cwatlas` suite.
2. Broad regression: prior suites do not regress.
3. Clean-checkout reproducibility of every `docs/cwatlas/receipts/*.json`.
4. Privacy scan clean: no private paths/identities, synthetic fixtures only.
5. Every `*_report()` asserts `PHYSICAL_VALIDATION_NOT_CLAIMED` and
   `SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED`.
6. CHANGELOG entry and release notes for v8.1.0.

Publication follows the repository's standing rule: **release is prepared
locally; pushing to any public remote requires explicit operator
authorization** (carried from the R7/R13/R15 release discipline). This ADR does
not authorize a push.

## Rollback strategy

- **Scope.** `cwatlas` is additive and isolated; rolling it back removes the
  package and its docs/receipts without touching prior releases.
- **Mechanism.** Revert the R10.8.1 commits (or `git revert` the merge of
  `r1081-cwatlas`); prior tags `v8.0.0`, `v7.0.0`, ... remain valid and
  buildable.
- **Data safety.** No private data is committed, so rollback carries no
  disclosure risk. Synthetic fixtures are the only shipped data.
- **Partial rollback.** Individual phases are receipt-isolated; a single phase
  can be reverted by removing its module/test/receipt without cascading, except
  where a dependency edge in P07 requires the predecessor (e.g. authority
  registry underpins decode receipts).

## Terminal verdict

```text
RGCS_R10_8_1_GREEN_CW_ATLAS_READY
CANONICAL_ROUND_TRIP_VERIFIED
SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
PHYSICAL_VALIDATION_NOT_CLAIMED
```

## Unresolved questions

- Whether the optional FastAPI/MapLibre UI layer ships in v8.1.0 or a later
  minor. Decision deferred; core is UI-independent by ADR-2.
- Final CHANGELOG wording for v8.1.0 (release-authoring phase, not this ADR).
