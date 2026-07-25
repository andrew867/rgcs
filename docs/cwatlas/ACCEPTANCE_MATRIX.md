# R10.8.1 CW Atlas — Acceptance Matrix

Maps the System Contract's non-negotiable invariants and the pack's product
targets to the modules and tests that satisfy them. All under the `cwatlas`
package with tests in `tests/cwatlas/`.

## System Contract invariants

| # | Invariant | Enforced by | Verified by |
|---|---|---|---|
| 1 | Raw bytes/strings immutable | `ingest`, `source_registry`, `provenance_ledger` | test_ingest, test_source_registry, test_provenance_ledger |
| 2 | Every decode records codec/version/frame/epoch/orientation/shell/commit | `canonical`, `authority`, `audit_bundle` | test_canonical, test_authority, test_audit_bundle |
| 3 | Canonical codec round-trips exactly within quantization | `codec_geo1`, `localize`, `address_to_vector`, `ico_vector` | test_codec_geo1, test_localize, test_address_to_vector, test_ico_vector |
| 4 | Legacy decoder may return 0/1/many aliases; never a forced pin | `codec_registry`, `decode_legacy`, `alias_regions`, `vector_to_pin_ux` | test_codec_registry, test_decode_legacy, test_alias_regions |
| 5 | Geographic labels sealed during transform selection/scoring | `calibration`, `holdout` | test_calibration, test_holdout |
| 6 | Public fixtures synthetic; private vectors outside VC | `privacy`, `export_separation` | test_privacy, test_export_separation |
| 7 | Declared geodetic/geocentric (Earth) / IAU (Mars) convention | `geodesy`, `frames`, `mars_frame` | test_geodesy, test_frames, test_mars_frame |
| 8 | `8<->0` shell closure stored as source ontology, not auto-applied | `shells`, `radial` | test_shells, test_radial |
| 9 | No map pin without CRS + epoch receipt | `map_to_address`, `claims.refuse_pin_without_crs_epoch` | test_map_to_address, test_claims |
| 10 | Extraordinary interpretations stay SOURCE/HYPOTHESIS/MATH until evidence | `claims`, `challenge`, `simplicity` | test_claims, test_challenge, test_simplicity |

## Product targets

| Target | Module(s) | Verified by |
|---|---|---|
| Map/globe click -> versioned CW vector | `map_to_address` -> `address_to_vector` / `ico_vector` | test_map_to_address, test_address_to_vector |
| Canonical vector -> exact map pin | `decode_canonical` | test_decode_canonical |
| Legacy/source vector -> candidates/regions/heatmaps/refusal | `decode_legacy`, `alias_regions`, `vector_to_pin_ux` | test_decode_legacy, test_alias_regions, test_vector_to_pin_ux |
| Earth + Mars frames | `earth_frame`, `mars_frame`, `portability` | test_*_frame, test_portability |
| 20-face icosahedral + recursive 8-way path | `icosahedron`, `subdivision`, `addressing`, `localize` | test_icosahedron, test_addressing, test_localize |
| Codec plugins (GEO-1/PACK40/PACK38/BASE100/TRIPLET9/SHELL9) | `codec_*`, `codec_registry` | test_codec_* |
| Body-relative shell states | `shells`, `radial` | test_shells, test_radial |
| Sealed calibration + prospective challenge | `calibration`, `challenge`, `holdout` | test_calibration, test_challenge, test_holdout |
| Private/public separation | `privacy`, `export_separation` | test_privacy, test_export_separation |
| Receipts, uncertainty, search-space accounting | `audit_bundle`, `uncertainty`, `search_space` | test_audit_bundle, test_uncertainty, test_search_space |
| Export GeoJSON/KML/JSON/CSV/URI | `io_geo`, `share`, `interchange` | test_io_geo, test_share, test_interchange |
| Backend API + CLI | `service`, `cli` | test_service, test_cli |
| Browser UI (MapLibre/Cesium/offline) | UI specs (P58/P59/P60) over the service API | spec — frontend outside pytest gate |

## Status

63 engine phases (P01–P63) COMPLETE with module + tests + receipt; 859
cwatlas tests pass. Browser frontend is spec-level over the tested backend.
`SOURCE_VECTOR_GEOGRAPHIC_SEMANTICS_NOT_CLAIMED`; `PHYSICAL_VALIDATION_NOT_CLAIMED`.
