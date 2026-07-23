# RGCS R10.10 — Natural Quartz, Patent Timeline, Continuity: Findings

**Status:** `SOFTWARE_VERIFIED` · `PHYSICAL_VALIDATION_NOT_CLAIMED`
**Baseline:** v5.8.0 (`3fca1e5`)
**Evidence class:** `DERIVED_MATHEMATICS`, `HISTORICAL_FACT`, conventional literature, and typed source records.
**Hardware:** deferred. **No apparatus built, no specimen measured, no crystal driven.**

---

## Gate Zero

Baseline v5.8.0 / `3fca1e5`, tree clean, 3340 tests. Firewall committed
gate CLEAN. Private repository: 0 remotes, outside the public worktree.
See [R10_10_GATE_ZERO.md](R10_10_GATE_ZERO.md).

## Verified history, and the refusal (P01/P02)

**Module:** [`r10/quartzhistory.py`](../../r10/quartzhistory.py)

The postwar synthetic-quartz patent timeline (Brush 1949 priority,
Clevite's US2675303A 1954, Bell's US2785058A 1957, Clevite buying Brush in
1952, first SHG in quartz 1961) is transcribed from primary-record
research and ordered by milestone date. Verdicts:
`POSTWAR_QUARTZ_INDUSTRIAL_TIMELINE_VERIFIED` and
`DEFENSE_COMPANY_OVERLAP_VERIFIED` — **and**
`CLASSIFIED_TECHNOLOGY_LINK_NOT_ESTABLISHED`. Corporate/defense adjacency
is ordinary industrial history, not a hidden lineage;
`refuse_classified_link()` and `refuse_chronology_as_causation()` enforce
it. Dates are `HISTORICAL_FACT` as sourced, not independently re-verified
against a patent office here. See
[QUARTZ_PATENT_HISTORY.md](../v59/QUARTZ_PATENT_HISTORY.md).

## Natural quartz: source-required, experimentally unresolved (P03, P06)

**Modules:** [`r10/naturalsource.py`](../../r10/naturalsource.py),
[`r10/natsynth.py`](../../r10/natsynth.py),
[`r10/specimen.py`](../../r10/specimen.py),
[`r10/characterize.py`](../../r10/characterize.py)

The private source hypothesis — natural geological quartz is *required*
because its growth history is part of the function — stays private. The
public translation is exactly one thing: **geological growth history is an
independent experimental variable**, verdict
`SOURCE_REQUIRED_EXPERIMENTALLY_UNRESOLVED`.
`refuse_publish_consciousness_as_materials_science()` blocks publishing
the interpretation as science. **Synthetic quartz, fused silica, and glass
are mandatory controls** (dropping one is refused). The matched protocol is
blinded and preregistered, matched on geometry/handedness/mass/`c`-axis/
fixture, with dummies, a label-shuffle null (power proven on a planted
effect), and multiplicity correction; any measured difference is
attributed to **ordinary differentiators first** (`refuse_exotic_explanation`).
A specimen's origin is `VERIFIED` only with a **chain of custody** — a
seller label is not provenance — and material class needs measurement, not
a label. Real specimens: `BLOCKED_NO_SPECIMENS`. See
[NATURAL_VS_SYNTHETIC_QUARTZ.md](../v59/NATURAL_VS_SYNTHETIC_QUARTZ.md).

## CW codec V2, coordinate binding, nonlinear inverse (P07–P09)

- **[`r10/cwcodec2.py`](../../r10/cwcodec2.py)** — 40-bit packed decimal
  (minimal: 2³⁹ < 10¹²), a 4-bit header + 36-bit octal path, **null
  windows** that keep unknown digits NULL until a padding rule is supplied,
  and a collision audit. It carries forward `NO_DECODER_IDENTIFIED`: a
  reversible codec relocates information but cannot create it, so a clean
  round-trip is necessary but never sufficient. No retrofit.
- **[`r10/codecbind.py`](../../r10/codecbind.py)** — a codec output is a
  number, not a coordinate. Binding it requires a **frame and epoch**
  (refused otherwise), a non-zero **uncertainty**, and **preregistration**;
  a post-hoc binding is retrofit and refused.
- **[`r10/nlinverse.py`](../../r10/nlinverse.py)** — nonlinear inverse
  estimation that **detects non-identifiability** (rank-deficient Jacobian
  → `NON_IDENTIFIABLE`, refuses a point estimate) and calibrates its
  uncertainty by a coverage test. Tight-looking fits can be unidentifiable.

## Nonlinear optics: an honest negative (P10)

**Module:** [`r10/nlo.py`](../../r10/nlo.py)

Quartz (class 32) is non-centrosymmetric and was the first material where
second-harmonic generation was seen (1961), with `d11 ≈ 0.3 pm/V`. But
bulk quartz is **not birefringently phase-matchable** for SHG — its
birefringence (~0.009) is too small to offset dispersion — so the process
is weak and non-phase-matched: `NOT_PHASE_MATCHABLE_IN_BULK_QUARTZ`.
`refuse_efficient_shg_claim()` refuses any claim of usable SHG from bulk
quartz. See [NONLINEAR_OPTICS.md](../v59/NONLINEAR_OPTICS.md).

## Continuity: bus-factor-zero (P13–P16)

**Module:** [`r10/continuity.py`](../../r10/continuity.py)

A deterministic content-hashed **manifest** (same tree → same manifest; a
missing canonical file is an error), an **export/restore** verification
loop that names every missing or altered file (`RESTORE_VERIFIED` /
`RESTORE_INCOMPLETE`), and a clean-room **successor drill** enumerating
what a stranger must do from the repositories and docs alone. See
[CONTINUITY_HANDOFF.md](../v59/CONTINUITY_HANDOFF.md) and
[DISASTER_RECOVERY.md](../v59/DISASTER_RECOVERY.md).

## Documentation (P11, P12)

The required public documentation set is delivered under
[`docs/v59/`](../v59/) (30 documents), each carrying authority, scope, last
verified commit, prerequisites, related code/tests/schemas, known
limitations, and a next-review trigger; the top-level `README.md` and
`SCIENTIFIC_BOUNDARIES.md` remain authoritative for their sections. See
[DOC_SET_STATUS.md](../v59/DOC_SET_STATUS.md) for the full map.

---

## What R10.10 does not claim

- No apparatus, no specimen measured, no crystal driven, no signal emitted.
- Natural quartz is **source-required but experimentally unresolved**;
  synthetic quartz is a **mandatory control**; no natural-superiority or
  consciousness claim is published.
- Verified corporate/defense history does **not** establish a classified
  or extraterrestrial technology lineage.
- The CW vectors are **not decoded** (a reversible codec cannot create
  content); no codec output is a coordinate without a frame, epoch, and
  uncertainty.
- Bulk quartz SHG is weak and not phase-matched; no efficient-SHG claim.
- No private name, locality, raw source text, or CW vector digit enters
  the public tree; the private interpretation stays private.

## Not executed (deferred / blocked)

- **The matched experiment (P06):** no specimens — `BLOCKED_NO_SPECIMENS`;
  no bench, no measurement.
- **Characterization (P05):** every result is a measurement *request*;
  nothing measured.
- **Hosted CI:** the free-tier GitHub Actions minutes are exhausted; the
  verification of record is the full local suite on the exact release
  commit.

`PHYSICAL_VALIDATION_NOT_CLAIMED`
