# Quartz-Growth Patent and Industry History

**Authority:** RGCS R10.10 / v5.9.0 (candidate)
**Scope:** the verified postwar synthetic-quartz patent timeline and the refusal it exists to make.
**Last verified commit:** v5.8.0 baseline (branch `v580-r10-10`).
**Prerequisites:** [SCIENTIFIC_BOUNDARIES](../../SCIENTIFIC_BOUNDARIES.md), [NATURAL_VS_SYNTHETIC_QUARTZ](NATURAL_VS_SYNTHETIC_QUARTZ.md).
**Related code / tests / schemas:** [`r10/quartzhistory.py`](../../r10/quartzhistory.py), [`tests/v52/test_r10_quartzhistory.py`](../../tests/v52/test_r10_quartzhistory.py); schema `CrystalGrowthPatent`.
**Known limitations:** dates and patent numbers are transcribed from the source pack's primary-record research (`source_quality = PRIMARY_RECORD_SECONDHAND`) — sourced, not independently re-verified against a patent office in this environment. Nothing here is measured.
**Next review trigger:** any correction to a patent date, or new primary-record verification.

---

## What is verified

There was intense postwar industrial effort to grow oscillator-grade
quartz, and it ran through Brush Development, Clevite, and Bell
Laboratories — companies with deep electronics and defense/ordnance
business. The timeline, ordered by each record's milestone date:

| Date | Record | Note |
|---|---|---|
| 1948-12-30 | Bell CIP (Buehler) | earlier continuation-in-part, later abandoned |
| 1949-05-21 | Brush Development | hydrothermal quartz priority |
| 1950-03-06 | Brush UK filing | |
| 1950-04-11 | Sobek & Hale (Clevite) application | |
| 1952-04-28 | Buehler (Bell Labs) application | |
| 1952-11-05 | GB682203A | hydrothermal seeded quartz, alkali carbonate/bicarbonate |
| 1954-04-13 | US2675303A (Clevite) | oscillator-grade synthetic quartz; growth depends on exact seed position/orientation |
| 1957-03-12 | US2785058A (Bell) | natural **or** synthetic seed; growth along the main axis, ~38° minor-rhombohedral cut |
| 1962 | US3051558A (Clevite) | filed 1956 |

Industry context: Cleveland Graphite Bronze bought Brush in 1952 for
$7M and adopted the Clevite name; by 1959 over a third of Clevite sales
were electronics including ordnance; second-harmonic generation was first
seen in quartz in 1961.

## The three verdicts

- `POSTWAR_QUARTZ_INDUSTRIAL_TIMELINE_VERIFIED`
- `DEFENSE_COMPANY_OVERLAP_VERIFIED`
- **`CLASSIFIED_TECHNOLOGY_LINK_NOT_ESTABLISHED`**

## The refusal (this is the point)

The overlap between quartz growers and defense contractors is **real and
ordinary**. Firms that make oscillators also make ordnance because
oscillators go in radios and radios go in weapons. That adjacency is
industrial history, **not** provenance, and it does **not** establish a
classified, suppressed, or extraterrestrial lineage behind the
technology. `refuse_classified_link()` and `refuse_chronology_as_causation()`
enforce this in code: chronological order is not causation, and corporate
proximity is not a hidden inheritance.

`PHYSICAL_VALIDATION_NOT_CLAIMED`
