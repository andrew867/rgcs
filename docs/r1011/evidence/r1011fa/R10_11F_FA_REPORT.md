# R10.11F + R10.11F-A Combined Report (2026-07-28)

**Verdict: `RGCS_R10_11F_YELLOW_EXACT_T_MESH_RECOVERED_NO_SINGLE_RATIO_LAW`**

The F-A override (operator retraction of the 627-step fitted operator,
verbatim in the pack) arrived mid-run and governs everything below.
Sections are separated per the report schema.

## 1. Independently reproduced coarse results (pre-override, kept)

- Pack reproduce script re-run clean in an isolated directory: root
  correspondence mean 3.5550° / RMS 3.6633°; level-2 stats identical to
  the pack receipt. Layer-2 mesh 162/480/320, Euler characteristic 2.
- Independent second path (this repo's own Kabsch construction from the
  recreational session, formalized): consistent within stated
  tolerances; the "T frame" reproduced from Wilkes+SAA clocking matches
  the frozen rigid frame to ~0.05 km.

## 2. Exact-T results computed BEFORE the retraction (now historical)

Run against the then-registered operators (627-step V1; flat-face
fitted candidate), the landmark edge inferences COLLAPSED: every
B0-matched apex edge missed Miami/San Juan by 305–1,268 km cross-track
(limit 150 km) — zero usable edges, ratio family unevaluable, all four
inferences rejected. The coarse suggestive ratios (6/5, 81/80, 10/9 at
0.02–0.5%) were artifacts of the regular unfitted solid; the null
base-rate analysis (9.4% per reading within 0.2% of some family member;
≥12 readings examined) independently shows they carry no significance.
These files are retained as the destruction record; the operators they
referenced are no longer active authority.

## 3. F-A override execution

- **627-step operator REVOKED** from active authority (verbatim
  retraction registered; archives remain immutable history only). The
  fitted flat-face node mesh is likewise excluded from the active
  target by the no-fitted-mesh rule. `CURRENT_T_PROJECTION_AUTHORITY.json`
  (v2) records both.
- **28-wire intake frozen** (sha256 b9f649ee…) and independently
  re-parsed: **27 exact E3 parses, 1 WIDTH_OVERFLOW on exactly
  `1687425419853`** — matching the pack. The overflow wire is untouched
  (the parser refuses; never truncates); the single-deletion file is
  imported as triage only.
- **Ratio authority updated**: 10/9 registered as source-approved
  primary; preregistered family + reciprocals preserved; bounded
  quadratic-irrational secondary class added.
- **π-equation frozen verbatim** with both `sq(r)` readings tested,
  prime-pair tokens (29|37, 89|37) and 33/35 registered, NO selection
  (underdetermined; awaiting the promised fields). One neutral
  observation recorded: under the sqrt reading with 33/35×29/37,
  √r = 6767 — 6.2% above Earth's mean radius in km; recorded, not
  interpreted.

## 4. Analytic ratio-driven compensation solve (the F-A core)

Construction: frozen analytic Wilkes/SAA frame; ratio-driven
shared-edge refinement with canonical orientation (lower global
ancestry key → higher; shared edges identical from both faces by
construction); split fraction q = r/(1+r); frozen anchors used ONLY as
post-law checks.

Result over the full family plus irrational secondaries, RMS over the
four non-codec-tension anchors (Stonehenge, Erie, Toronto, orange-A):

| law | q | anchor RMS |
|---|---|---|
| r = 1 | 0.5 | **13.902°** |
| 81/80 | 0.50311 | 13.911° |
| 10/9 (source primary) | 0.52632 | 14.100° |
| 9/8 | 0.52941 | 14.140° |
| best irrational | 0.55279 | (worse on 4-anchor RMS; 22.06° on all-5) |

**No law wins.** The global uniform edge-ratio law is nearly inert on
anchor residuals (±0.25° across the whole family) and r=1 is marginally
best; the source-approved 10/9 does not improve any frozen anchor.
Montréal (codec-level tension, 42–44° under every law) is reported
separately and dominates any all-5 statistic.

## 5. Standing interpretation (bounded)

The ~13.9° analytic-frame→target residual is exactly what the revoked
fitted warp existed to absorb. A GLOBAL per-edge ratio law cannot
absorb it under this canonical orientation. If the source's 10/9
compensation is real, it must act elsewhere: per-edge-class or
per-orientation laws (underdetermined — needs more source data), a
different canonical-direction rule, or inside the still-unresolved
mapping from segmented S6 states to geometry (the current addressing
still rides the demoted old-profile paths). That last possibility is
the standing suspicion: we may be compensating the wrong decode.

## 6. Unresolved

Full 64×8 transition table (12/512 cells); probe descendants P5/P6
(frozen, awaiting source); S6-state→geometry semantics; the π-equation
missing fields; per-edge-class ratio laws; Montréal decode model;
Erie-167 tension. Publication HOLD. No source-origin or physical
validation claimed.
