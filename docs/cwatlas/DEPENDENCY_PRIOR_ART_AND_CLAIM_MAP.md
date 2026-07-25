# Dependency, Prior-Art, and Claim Map — R10.8.1 CW Atlas

**Phase:** T01 / P07 (Reconciliation and Data Authority)
**Repository head:** `2f49122` (v8.0.0, R15)
**Status:** COMPLETE — documentation phase, no code.

## Purpose

Map the dependencies among the R10.8.1 lanes — **coordinate**, **RF**,
**plasmonic**, **crystal**, and **evidence** — so that no lane silently feeds a
claim into another, and classify every supporting source by its **claim class**.

Two independent rules govern this map:

1. **Dependency direction is one-way into the atlas, never out of it.** A
   coordinate result never depends on an RF, plasmonic, or crystal claim. The
   physics lanes are research-archive context; they inform *hypotheses*, never
   the reversible codec.
2. **Every source keeps its claim class.** A source cue is `SOURCE_CLAIM`, an
   operator idea is `OPERATOR_HYPOTHESIS`, an arithmetic re-expression is
   `MATHEMATICAL_TRANSLATION`, and outside literature is `PRIOR_ART_LITERATURE`.
   No class is promoted by proximity to another lane.

Claim classes referenced here are the taxonomy in `cwatlas/claims.py`
(`SOURCE_CLAIM`, `OPERATOR_HYPOTHESIS`, `MATHEMATICAL_TRANSLATION`,
`LEGACY_ALIAS_CANDIDATE`, `CANONICAL_ROUND_TRIP`, `CALIBRATED_MAPPING`,
`REFUSAL`), plus `PRIOR_ART_LITERATURE` for outside publications and patents.

## Lanes

| Lane | What it holds | Ships in `cwatlas`? |
|------|---------------|---------------------|
| **Coordinate** | Canonical geocoder (`CW-GEO-1`, `CW-HCM-ICO-1`), legacy candidate decoders, frame/epoch/root authorities. | Yes — the product. |
| **RF** | Handshake/EMI cues, 6.78/13/20.34/27.12 MHz families, dyadic 20.48/40.96 lane. | No — research-archive context only. |
| **Plasmonic** | Spoof surface-wave / metasurface field-shaping, Pearcey and space-time SPP analogues. | No — context only. |
| **Crystal** | Natural quartz, cavity loading, anisotropy, overtones, surface modes. | No — context only. |
| **Evidence** | Provenance receipts, holdout discipline, evidence ladder, uncertainty and search-space accounting. | Yes — governance around the coordinate lane. |

## Dependency map

```text
        PRIOR-ART LITERATURE (patents, papers)
                 |  (informs, never validates)
                 v
   RF lane     Plasmonic lane     Crystal lane      <-- research-archive context
      \             |                 /                  (SOURCE_CLAIM / hypothesis)
       \            |                /
        \           v               /
         +----> (hypotheses only) <-+
                     |
                     |  X  no dependency edge into the coordinate result
                     v
   ================ FIREWALL (claim boundary, cwatlas/claims.py) ================
                     |
                     v
             COORDINATE lane
        (CANONICAL_ROUND_TRIP / MATHEMATICAL_TRANSLATION / LEGACY_ALIAS_CANDIDATE)
                     |
                     v
             EVIDENCE lane
        (provenance receipt, uncertainty, holdout; REFUSAL when calibration missing)
```

Read the firewall literally: the physics lanes may *motivate* which legacy
codecs are worth trying, but a coordinate output's correctness never rests on
an RF, plasmonic, or crystal claim. The reversible codec is a math fact; the
candidate decoders return alias sets and uncertainties; the evidence lane
records provenance and refuses a pin without a CRS and epoch (invariant 9).

### Intra-coordinate dependencies

| Depends on | Provides | Mechanism |
|------------|----------|-----------|
| Frame/epoch/root **authority registry** (P06, `cwatlas/authority.py`) | Every decode | Pins exactly which body/frame/epoch/orientation/ephemeris a decode used (invariant 2); refuses unregistered authorities. |
| **Privacy boundary** (P02, `cwatlas/privacy.py`) | Every lane | Keeps private corpora out of public artifacts; public fixtures synthetic. |
| **Claim taxonomy** (`cwatlas/claims.py`) | Every lane | Types every result; blocks the forbidden promotions. |
| Canonical codec | Legacy decoders | Provides the reversible reference; a legacy alias is never merged into the canonical round-trip. |

## Source classification

| Source (lane) | Claim class | Rationale |
|---------------|-------------|-----------|
| Operator-reported source vector strings (coordinate) | `SOURCE_CLAIM` | Reported by a source; yields alias sets or refusals, never a decoded destination. |
| "This legacy string decodes to site X" (coordinate) | `OPERATOR_HYPOTHESIS` | Operator proposal; requires a prospective known-destination challenge to advance. |
| Arithmetic re-expression of a legacy string by a codec (coordinate) | `MATHEMATICAL_TRANSLATION` | Codec output; asserts no meaning. Strongest class reachable for a source vector without evidence. |
| Alias among a candidate set (coordinate) | `LEGACY_ALIAS_CANDIDATE` | One admissible decode with a score/uncertainty; never forced to one pin. |
| 13 MHz / 1604 / 1644 handshake and EMI cues (RF) | `SOURCE_CLAIM` | Reported cue; not a coordinate authority. |
| 6.78 MHz base and 20.34/27.12 MHz 3:4 pair; 20.48/40.96 dyadic lane (RF) | `MATHEMATICAL_TRANSLATION` | Ratio arithmetic on declared frequencies; no mechanism claimed. |
| m=2 counter-rotating pattern -> 1.695 MHz / ~60.55 microtesla (RF) | `OPERATOR_HYPOTHESIS` | Model-derived correspondence, not a measurement. |
| Spoof surface-wave / metasurface framing (plasmonic) | `PRIOR_ART_LITERATURE` | Established physics; a field-shaping analogue, not gravity evidence. |
| Pearcey / space-time SPP papers (plasmonic) | `PRIOR_ART_LITERATURE` | Conventional field-shaping analogues; explicitly not gravity evidence. |
| Natural quartz, cavity loading, anisotropy, overtones (crystal) | `SOURCE_CLAIM` + `PRIOR_ART_LITERATURE` | Materials-lane context requiring coupled Maxwell-electroelastic models to say anything quantitative. |
| Electrokinetic patents and review (crystal / prior art) | `PRIOR_ART_LITERATURE` | A patent is a document, not validation of a craft programme (`claims.refuse_patent_as_craft_validation`). |
| Provenance receipts, holdout results (evidence) | `CANONICAL_ROUND_TRIP` / `REFUSAL` | Verified codec properties or explicit declines; never a source-meaning claim. |

## Forbidden cross-lane promotions (all refused)

- An RF cue -> a coordinate authority. **Refused.** RF stays research context.
- A close arithmetic match (any lane) -> intended encoding. **Refused**
  (`claims.refuse_close_match_as_intent`).
- A plasmonic/crystal analogue -> physical validation of the coordinate system.
  **Refused** (`PHYSICAL_VALIDATION_NOT_CLAIMED`).
- A patent -> craft-programme validation. **Refused**
  (`claims.refuse_patent_as_craft_validation`).
- A source vector -> a real geographic/extraterrestrial location. **Refused**
  (`claims.refuse_source_as_geographic`).

## Unresolved questions

- Whether any RF frequency family can ever be a *calibration anchor* for a
  legacy codec. Today: no; it would require a prospective known-destination
  challenge, and even then advances only that codec's class, not the RF lane's.
- Whether crystal-lane models will ever be quantitative enough to enter the
  dependency graph. Today: no edge; context only.

## Verdict

```text
DEPENDENCY_MAP_ONE_WAY_INTO_COORDINATE_LANE
ALL_SOURCES_CLAIM_CLASSED_NO_CROSS_LANE_PROMOTION
SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED
PHYSICAL_VALIDATION_NOT_CLAIMED
```
