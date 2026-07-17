# V4X2 orphan register (O01)

Fixed ledger: **280** · orphans: **8** · total: **288**

Ideas that surfaced DURING this programme's execution — census discoveries, addendum structures not yet implemented, queued benchmarks. None deleted; each disposed.

| ID | Idea | Owner | Status | Disposition |
|---|---|---|---|---|
| ORPH2-001 | electrical trim primitives: narrow meanders and capacitive tuning fingers | R02 | ENGINEERING_PROTOTYPE | deferred_with_owner |
| ORPH2-002 | removable balancing pixels | R02 | ENGINEERING_PROTOTYPE | deferred_with_owner |
| ORPH2-003 | female-apex twin concentration (z ~ 4 mm) | Y03 | SOURCE_HYPOTHESIS | investigate |
| ORPH2-004 | mid-shaft symmetric D2 pair (z ~ 58 mm) | Y03 | SOURCE_HYPOTHESIS | investigate |
| ORPH2-005 | LOBPCG/AMG solver benchmark | Y02 | PROTOCOL_READY_HARDWARE_REQUIRED | queued |
| ORPH2-006 | filtration ordering on the coupled harmonic solve | Q04 | ENGINEERING_PROTOTYPE | deferred_with_owner |
| ORPH2-007 | angular-Nyquist aliasing in partial arrays | R11 | IMPLEMENTED_AND_TESTED | resolved_in_code |
| ORPH2-008 | claim-card versioning as a reusable mechanism | V02 | IMPLEMENTED_AND_TESTED | resolved_in_docs |

## Context and dispositions in full

### ORPH2-001 — electrical trim primitives: narrow meanders and capacitive tuning fingers

tuning addendum §2.1 lists ~10 sacrificial structures; design_trim implements the five mass-dominated ones. The two ELECTRICAL primitives change R/L/C rather than mass and need their own sensitivity model.

**Disposition:** deferred_with_owner: add electrical-zone primitives with impedance sensitivities (bvd.electrode_loading is the starting point)

### ORPH2-002 — removable balancing pixels

addendum §2.1: fine-grained balance correction cells distinct from frequency trim cells (they target the first moment, not f01).

**Disposition:** deferred_with_owner: balance-pixel groups whose target metric is group_balance_moment, not removal_df01_hz

### ORPH2-003 — female-apex twin concentration (z ~ 4 mm)

the unbiased census found a mirror strain-energy concentration near the female apex — never previously examined because every prior analysis selected nearest-to-candidate.

**Disposition:** investigate: is the twin's geometry-mirrored position exact under mesh refinement? symmetric twins would recast the apex feature as a tip-pair phenomenon

### ORPH2-004 — mid-shaft symmetric D2 pair (z ~ 58 mm)

second census discovery: a large symmetric pair in the D2 diagnostic mid-shaft.

**Disposition:** investigate: diagnostic-specific (D2-only) or physical? check against D1/D8 at matching quantiles

### ORPH2-005 — LOBPCG/AMG solver benchmark

named as the cheapest path below 1.5 mm spacing (Y012) but the actual two-solver benchmark on a controlled case has not run.

**Disposition:** queued: job manifest exists; needs a quiet machine window (memory contention invalidates the benchmark)

### ORPH2-006 — filtration ordering on the coupled harmonic solve

Q04's rgcs_application names the candidate; no RGCS solve has been restructured and no benefit measured.

**Disposition:** deferred_with_owner: apply apply_filtration to the harmonic_field coupling matrix and MEASURE the density change

### ORPH2-007 — angular-Nyquist aliasing in partial arrays

found while testing R11: with n partials, orders m and m+n are indistinguishable. Now reported in the API, but the design implication (choose n > 2*m_target) belongs in the composite-mode design rules.

**Disposition:** resolved_in_code: alias_band + alias_note in partial_resonator_array; design rule documented here

### ORPH2-008 — claim-card versioning as a reusable mechanism

the Eye claim card went v3->v4 during this programme when the census corrected the framing. The card mechanism (versioned claims + correction trail) should template any future public finding, not just the Eye.

**Disposition:** resolved_in_docs: EYE_CLAIM_CARD.md is the template; rule 3 (corrections are news) generalizes

