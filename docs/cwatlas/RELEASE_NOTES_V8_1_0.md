# RGCS v8.1.0 - R10.8.1 CW Atlas and Bidirectional Geocoder

**Release date:** 2026-07-25
**Predecessor:** v8.0.0 (R15)
**Final verdict:** RGCS_R10_8_1_GREEN_CW_ATLAS_READY / CANONICAL_ROUND_TRIP_VERIFIED / LEGACY_ALIAS_SET_PIPELINE_VERIFIED / SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED / PHYSICAL_VALIDATION_NOT_CLAIMED

R10.8.1 adds the `cwatlas` package: a 64-phase CW Atlas across 8 tranches
(data authority, coordinate frames + globe engine, canonical + legacy codecs,
icosahedral addressing, map->vector, vector->map, evidence/holdouts, and
publication/release). Two firewalled systems: a reversible canonical geocoder
(CW-GEO-1 + CW-HCM-ICO, exact round-trip) and a source-vector hypothesis
decoder that returns an alias set / region / heatmap / refusal and never a
forced pin. Earth (WGS84/ITRF) and Mars (IAU) frames; sealed-anchor
calibration and a prospective known-destination challenge as the only path to
a calibrated mapping; search-space accounting, MDL + multiple-comparison
scoring, and a selection-bias firewall. A cw-atlas CLI + service and GeoJSON/
KML/CSV/JSON/CW-URI interchange. Pure numpy; the browser UI is a spec over the
tested backend. See docs/cwatlas/R10_8_1_MANUSCRIPT.md and
docs/cwatlas/receipts/.

Non-claims: a source vector does NOT identify a real location; no site is
decoded from the vector family; a close arithmetic match is not intent; the
coordinate system controls nothing physical. Additive; no history rewritten.

# expect: 7392 passed (1 archived-environment byte test deselected by policy D-V3-04)
