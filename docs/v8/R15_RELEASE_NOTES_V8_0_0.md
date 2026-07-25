# RGCS v8.0.0 - R15 Experimental Phase Infrastructure

**Release date:** 2026-07-25
**Predecessor:** v7.0.0 (R13)
**Final verdict:** `R15_GREEN_EXPERIMENTAL_INFRASTRUCTURE_READY_NO_PHYSICAL_CLAIMS_ADVANCED`

R15 adds the `r15/` package: 36 phases across 8 tranches (33 modules, 11 JSON
schemas, 36 terminal receipts) turning the R13 architecture into an
instrument-ready, calibration-bound, uncertainty-aware experimental platform.
Every hardware-facing lane ships REAL/REPLAY/SYNTHETIC/FAULT_INJECTION modes,
an error budget, protocols, tests, and docs; only physical acquisition is
blocked (no-purchase rule). The evidence ladder (E0-E7) caps any observation
missing a binding below a physical measurement; the strongest unreplicated
residual is UNEXPLAINED_INSTRUMENT_RESIDUAL, and there is no PHRYLL_DETECTED
state. See docs/v8/R15_FINDINGS.md and docs/v8/R15_NON_CLAIMS.md.

Additive: no prior work reset, no public history rewritten.
PHYSICAL_VALIDATION_NOT_CLAIMED.

# expect: 6533 passed (1 archived-environment byte test deselected by policy D-V3-04)
